#!/usr/bin/env python3
"""ONE TEN M1 standalone multi-take vocal recorder.

Full-duplex CoreAudio path:
  output = backing track only
  input = microphone take capture

No software monitoring is performed; the singer should monitor through the
interface hardware mix.
"""

from __future__ import annotations

import argparse
import json
import math
import queue
import re
import select
import sys
import termios
import threading
import time
import tty
import wave
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import sounddevice as sd
import soundfile as sf

try:
    import rtmidi
except Exception:  # pragma: no cover - optional at runtime
    rtmidi = None


DUET_RE = re.compile(r"apogee|duet", re.IGNORECASE)
DEFAULT_SESSIONS_DIR = Path(__file__).resolve().parent / "sessions"
DEFAULT_TEST_DIR = Path(__file__).resolve().parent / "test_assets"


@dataclass
class Intent:
    name: str
    source: str
    raw: str


@dataclass
class DeviceSelection:
    input_device: int | None
    output_device: int | None
    input_name: str
    output_name: str
    samplerate: int
    reason: str


class LevelMeter:
    def __init__(self) -> None:
        self.peak = 0.0
        self.rms = 0.0
        self._lock = threading.Lock()

    def update(self, samples: np.ndarray) -> None:
        if samples.size == 0:
            return
        peak = float(np.max(np.abs(samples)))
        rms = float(np.sqrt(np.mean(np.square(samples))))
        with self._lock:
            self.peak = peak
            self.rms = rms

    def snapshot(self) -> tuple[float, float]:
        with self._lock:
            return self.peak, self.rms


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ONE TEN M1 full-duplex vocal recorder")
    parser.add_argument("--backing", help="Backing track: WAV/AIFF/MP3 as supported by libsndfile")
    parser.add_argument("--lyrics", help="Optional lyrics .txt, one lyric line per line")
    parser.add_argument("--song", help="Session song folder name; defaults to backing stem")
    parser.add_argument("--sessions-dir", type=Path, default=DEFAULT_SESSIONS_DIR)
    parser.add_argument("--samplerate", type=int, help="Override backing/device samplerate")
    parser.add_argument("--input-device", type=int, help="PortAudio input device index")
    parser.add_argument("--output-device", type=int, help="PortAudio output device index")
    parser.add_argument("--list-devices", action="store_true")
    parser.add_argument("--no-midi", action="store_true", help="Disable MIDI listener")
    parser.add_argument("--self-test", action="store_true", help="Generate a tone and record a 4s test take")
    parser.add_argument("--seconds", type=float, default=4.0, help="Self-test take duration")
    return parser.parse_args()


def print_devices() -> None:
    print("CoreAudio/PortAudio devices:")
    for idx, dev in enumerate(sd.query_devices()):
        print(
            f"  {idx}: {dev['name']} "
            f"({dev['max_input_channels']} in, {dev['max_output_channels']} out, "
            f"default_sr={dev['default_samplerate']:.0f})"
        )


def device_name(index: int | None, kind: str) -> str:
    if index is None:
        return f"default {kind}"
    return str(sd.query_devices(index)["name"])


def find_duet_device_pair() -> tuple[int, int] | None:
    devices = list(sd.query_devices())
    duplex = None
    input_only = None
    output_only = None
    for idx, dev in enumerate(devices):
        if not DUET_RE.search(str(dev["name"])):
            continue
        has_in = int(dev["max_input_channels"]) > 0
        has_out = int(dev["max_output_channels"]) > 0
        if has_in and has_out:
            duplex = idx
            break
        if has_in and input_only is None:
            input_only = idx
        if has_out and output_only is None:
            output_only = idx
    if duplex is not None:
        return duplex, duplex
    if input_only is not None and output_only is not None:
        return input_only, output_only
    return None


def choose_devices(args: argparse.Namespace, requested_rate: int | None) -> DeviceSelection:
    if args.input_device is not None or args.output_device is not None:
        in_dev = args.input_device
        out_dev = args.output_device
        rate_device = in_dev if in_dev is not None else out_dev
        rate = requested_rate or int(sd.query_devices(rate_device)["default_samplerate"])
        return DeviceSelection(
            in_dev,
            out_dev,
            device_name(in_dev, "input"),
            device_name(out_dev, "output"),
            rate,
            "manual device override",
        )

    duet = find_duet_device_pair()
    if duet:
        in_dev, out_dev = duet
        rate = requested_rate or int(sd.query_devices(in_dev)["default_samplerate"])
        return DeviceSelection(
            in_dev,
            out_dev,
            device_name(in_dev, "input"),
            device_name(out_dev, "output"),
            rate,
            "auto-detected Apogee Duet 2",
        )

    defaults = sd.default.device
    in_dev = int(defaults[0]) if defaults and defaults[0] is not None and defaults[0] >= 0 else None
    out_dev = int(defaults[1]) if defaults and defaults[1] is not None and defaults[1] >= 0 else None
    rate_source = in_dev if in_dev is not None else out_dev
    rate = requested_rate or (int(sd.query_devices(rate_source)["default_samplerate"]) if rate_source is not None else 44100)
    return DeviceSelection(
        in_dev,
        out_dev,
        device_name(in_dev, "input"),
        device_name(out_dev, "output"),
        rate,
        "Duet not found; using default/built-in CoreAudio devices",
    )


def load_audio(path: Path, samplerate: int | None) -> tuple[np.ndarray, int]:
    data, file_rate = sf.read(str(path), always_2d=True, dtype="float32")
    rate = samplerate or file_rate
    if rate != file_rate:
        raise ValueError(
            f"Backing samplerate is {file_rate} Hz but requested {rate} Hz. "
            "For M1, export/convert the backing to the target samplerate first."
        )
    return data, rate


def fit_output_channels(backing: np.ndarray, channels: int) -> np.ndarray:
    if backing.shape[1] == channels:
        return backing
    if channels == 1:
        return np.mean(backing, axis=1, keepdims=True).astype("float32")
    mono = np.mean(backing, axis=1, keepdims=True)
    return np.repeat(mono, channels, axis=1).astype("float32")


def sanitize_song_name(name: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", name.strip()).strip("._-")
    return safe or "song"


def write_wav(path: Path, samples: np.ndarray, samplerate: int) -> None:
    clipped = np.clip(samples, -1.0, 1.0)
    pcm16 = (clipped * np.iinfo(np.int16).max).astype("<i2")
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(samples.shape[1] if samples.ndim > 1 else 1)
        wav.setsampwidth(2)
        wav.setframerate(samplerate)
        wav.writeframes(pcm16.tobytes())


def next_take_number(song_dir: Path) -> int:
    nums = []
    for path in song_dir.glob("take_*.json"):
        match = re.match(r"take_(\d+)_", path.name)
        if match:
            nums.append(int(match.group(1)))
    return max(nums, default=0) + 1


def make_metadata(
    *,
    take_number: int,
    wav_path: Path,
    backing_path: Path,
    lyrics_path: Path | None,
    started_at: str,
    duration: float,
    devices: DeviceSelection,
    input_channels: int,
    frames: int,
) -> dict[str, Any]:
    return {
        "take": take_number,
        "wav_file": wav_path.name,
        "backing_file": str(backing_path),
        "lyrics_file": str(lyrics_path) if lyrics_path else None,
        "device": {
            "input": devices.input_name,
            "output": devices.output_name,
            "input_device_index": devices.input_device,
            "output_device_index": devices.output_device,
            "selection": devices.reason,
        },
        "samplerate": devices.samplerate,
        "input_channels": input_channels,
        "frames": frames,
        "duration": duration,
        "started_at": started_at,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "software_monitoring": False,
    }


def save_take(
    song_dir: Path,
    take_number: int,
    samples: np.ndarray,
    backing_path: Path,
    lyrics_path: Path | None,
    started_at: str,
    devices: DeviceSelection,
    input_channels: int,
) -> tuple[Path, Path, dict[str, Any]]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = f"take_{take_number:03d}_{timestamp}"
    wav_path = song_dir / f"{stem}.wav"
    json_path = song_dir / f"{stem}.json"
    duration = float(len(samples) / devices.samplerate) if devices.samplerate else 0.0
    write_wav(wav_path, samples, devices.samplerate)
    metadata = make_metadata(
        take_number=take_number,
        wav_path=wav_path,
        backing_path=backing_path,
        lyrics_path=lyrics_path,
        started_at=started_at,
        duration=duration,
        devices=devices,
        input_channels=input_channels,
        frames=len(samples),
    )
    json_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return wav_path, json_path, metadata


class MidiListener:
    """Maps MIDI note/CC events to recorder intents."""

    def __init__(self, intents: "queue.Queue[Intent]") -> None:
        self.intents = intents
        self._midi_in = None
        self._stop = threading.Event()

    def start(self) -> bool:
        if rtmidi is None:
            print("MIDI: python-rtmidi unavailable; keyboard controls still active.")
            return False
        midi_in = rtmidi.MidiIn()
        ports = midi_in.get_ports()
        if not ports:
            print("MIDI: no input ports found; keyboard controls still active.")
            return False
        midi_in.open_port(0)
        midi_in.set_callback(self._callback)
        self._midi_in = midi_in
        print(f"MIDI: listening on {ports[0]}")
        return True

    def close(self) -> None:
        self._stop.set()
        if self._midi_in is not None:
            self._midi_in.close_port()

    def _callback(self, event: tuple[list[int], float], _data: Any = None) -> None:
        msg, _delta = event
        if not msg:
            return
        status = msg[0] & 0xF0
        data1 = msg[1] if len(msg) > 1 else 0
        data2 = msg[2] if len(msg) > 2 else 0
        intent = None
        if status == 0x90 and data2 > 0:
            intent = {
                60: "toggle",
                61: "new_take",
                62: "play_last",
                63: "quit",
            }.get(data1)
        elif status == 0xB0 and data2 > 0:
            intent = {
                20: "toggle",
                21: "new_take",
                22: "play_last",
                23: "quit",
            }.get(data1)
        if intent:
            self.intents.put(Intent(intent, "midi", f"{msg}"))


class RawTerminal:
    def __enter__(self) -> "RawTerminal":
        self.fd = sys.stdin.fileno()
        self.old = termios.tcgetattr(self.fd)
        tty.setcbreak(self.fd)
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)


def poll_keyboard(intents: "queue.Queue[Intent]") -> None:
    while select.select([sys.stdin], [], [], 0)[0]:
        char = sys.stdin.read(1).lower()
        mapping = {
            " ": "toggle",
            "n": "new_take",
            "p": "play_last",
            "q": "quit",
        }
        if char in mapping:
            intents.put(Intent(mapping[char], "keyboard", repr(char)))


class RecorderApp:
    def __init__(
        self,
        backing: np.ndarray,
        backing_path: Path,
        lyrics_path: Path | None,
        song_dir: Path,
        devices: DeviceSelection,
    ) -> None:
        self.backing = backing
        self.backing_path = backing_path
        self.lyrics_path = lyrics_path
        self.song_dir = song_dir
        self.devices = devices
        self.intents: queue.Queue[Intent] = queue.Queue()
        self.state = "IDLE"
        self.take_count = next_take_number(song_dir) - 1
        self.meter = LevelMeter()
        self.last_wav: Path | None = None
        self.last_json: Path | None = None
        self.quit_requested = False

    def record_take(self, max_seconds: float | None = None) -> tuple[Path, Path, dict[str, Any]]:
        output_channels = min(2, int(sd.query_devices(self.devices.output_device)["max_output_channels"])) if self.devices.output_device is not None else 2
        input_channels = min(1, int(sd.query_devices(self.devices.input_device)["max_input_channels"])) if self.devices.input_device is not None else 1
        backing = fit_output_channels(self.backing, output_channels)
        if max_seconds is not None:
            max_frames = min(len(backing), int(max_seconds * self.devices.samplerate))
            backing = backing[:max_frames]
        return self._record_playrec(backing, input_channels, allow_stop=max_seconds is None)

    def _record_playrec(
        self,
        backing: np.ndarray,
        input_channels: int,
        *,
        allow_stop: bool,
    ) -> tuple[Path, Path, dict[str, Any]]:
        started_at = datetime.now(timezone.utc).isoformat()
        self.state = "RECORDING"
        self._render_status()
        samples = sd.playrec(
            backing,
            samplerate=self.devices.samplerate,
            channels=input_channels,
            dtype="float32",
            device=(self.devices.input_device, self.devices.output_device),
            blocking=False,
        )
        start = time.monotonic()
        duration = len(backing) / float(self.devices.samplerate)
        stop_early = False
        while True:
            elapsed = time.monotonic() - start
            frames_done = min(len(samples), max(0, int(elapsed * self.devices.samplerate)))
            if frames_done > 0:
                window_start = max(0, frames_done - int(0.25 * self.devices.samplerate))
                self.meter.update(samples[window_start:frames_done])
            if allow_stop:
                poll_keyboard(self.intents)
                try:
                    intent = self.intents.get_nowait()
                except queue.Empty:
                    intent = None
                if intent and intent.name in {"toggle", "quit"}:
                    if intent.name == "quit":
                        self.quit_requested = True
                    stop_early = True
                    sd.stop()
                    break
            self._render_status()
            if elapsed >= duration:
                sd.wait()
                break
            time.sleep(0.05)
        if stop_early:
            frames_done = min(len(samples), max(0, int((time.monotonic() - start) * self.devices.samplerate)))
            samples = samples[:frames_done]
        self.meter.update(samples)
        take_number = next_take_number(self.song_dir)
        wav_path, json_path, metadata = save_take(
            self.song_dir,
            take_number,
            samples,
            self.backing_path,
            self.lyrics_path,
            started_at,
            self.devices,
            input_channels,
        )
        self.take_count = take_number
        self.last_wav = wav_path
        self.last_json = json_path
        self.state = "IDLE"
        self._render_status(final=True)
        print(f"\nSaved take {take_number:03d}: {wav_path}")
        print(f"Sidecar: {json_path}")
        return wav_path, json_path, metadata

    def play_last(self) -> None:
        if not self.last_wav:
            print("\nNo last take to play.")
            return
        data, rate = sf.read(str(self.last_wav), always_2d=True, dtype="float32")
        self.state = "PLAY_LAST"
        self._render_status()
        sd.play(data, samplerate=rate, device=self.devices.output_device, blocking=True)
        self.state = "IDLE"

    def run_interactive(self, use_midi: bool) -> None:
        midi = MidiListener(self.intents) if use_midi else None
        if midi:
            midi.start()
        print("Keys: space=start/stop  n=new take  p=play last  q=quit")
        print("MIDI: note 60/CC20=start-stop, note 61/CC21=new take, note 62/CC22=play last, note 63/CC23=quit")
        self._render_status()
        try:
            with RawTerminal():
                while True:
                    poll_keyboard(self.intents)
                    try:
                        intent = self.intents.get(timeout=0.1)
                    except queue.Empty:
                        self._render_status()
                        continue
                    if intent.name == "toggle":
                        self.record_take()
                        if self.quit_requested:
                            break
                    elif intent.name == "new_take":
                        print("\nNew take armed. Press space/pedal to start.")
                    elif intent.name == "play_last":
                        self.play_last()
                    elif intent.name == "quit":
                        break
        finally:
            if midi:
                midi.close()
            print("\nRecorder stopped.")

    def _render_status(self, final: bool = False) -> None:
        peak, rms = self.meter.snapshot()
        width = 24
        filled = min(width, int(peak * width * 4))
        bar = "#" * filled + "-" * (width - filled)
        end = "\n" if final else "\r"
        print(
            f"STATE={self.state:<10} takes={self.take_count:<3} "
            f"input peak={peak:0.4f} rms={rms:0.4f} [{bar}]",
            end=end,
            flush=True,
        )


def generate_test_backing(path: Path, seconds: float = 4.0, samplerate: int = 44100) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = int(seconds * samplerate)
    t = np.arange(frames, dtype=np.float32) / samplerate
    tone = 0.08 * np.sin(2.0 * np.pi * 220.0 * t)
    pulse = 0.035 * np.sin(2.0 * np.pi * 440.0 * t) * (np.sin(2.0 * np.pi * 1.0 * t) > 0)
    stereo = np.column_stack([tone, tone + pulse]).astype("float32")
    sf.write(str(path), stereo, samplerate)


def run_self_test(args: argparse.Namespace) -> int:
    backing_path = DEFAULT_TEST_DIR / "m1_test_backing.wav"
    lyrics_path = DEFAULT_TEST_DIR / "m1_test_lyrics.txt"
    generate_test_backing(backing_path, seconds=max(args.seconds, 4.0))
    lyrics_path.write_text("Test line one\nTest line two\n", encoding="utf-8")
    backing, rate = load_audio(backing_path, args.samplerate)
    devices = choose_devices(args, rate)
    song_dir = args.sessions_dir / "m1_self_test"
    song_dir.mkdir(parents=True, exist_ok=True)
    print(f"Device selection: {devices.reason}")
    print(f"Input: {devices.input_name}")
    print(f"Output: {devices.output_name}")
    app = RecorderApp(backing, backing_path, lyrics_path, song_dir, devices)
    wav_path, json_path, metadata = app.record_take(max_seconds=args.seconds)
    print("SELF-TEST PASS")
    print(f"WAV={wav_path}")
    print(f"JSON={json_path}")
    print(f"duration={metadata['duration']:.3f}s samplerate={metadata['samplerate']}")
    return 0


def main() -> int:
    args = parse_args()
    if args.list_devices:
        print_devices()
        return 0
    if args.self_test:
        return run_self_test(args)
    if not args.backing:
        print("ERROR: --backing is required unless --self-test or --list-devices is used.", file=sys.stderr)
        return 2

    backing_path = Path(args.backing).expanduser().resolve()
    lyrics_path = Path(args.lyrics).expanduser().resolve() if args.lyrics else None
    backing, rate = load_audio(backing_path, args.samplerate)
    devices = choose_devices(args, rate)
    song_name = sanitize_song_name(args.song or backing_path.stem)
    song_dir = args.sessions_dir / song_name
    song_dir.mkdir(parents=True, exist_ok=True)

    if lyrics_path and lyrics_path.exists():
        lyric_count = len([line for line in lyrics_path.read_text(encoding="utf-8").splitlines() if line.strip()])
        print(f"Loaded lyrics: {lyric_count} lines from {lyrics_path}")
    elif lyrics_path:
        print(f"WARNING: lyrics file not found: {lyrics_path}")

    print(f"Device selection: {devices.reason}")
    print(f"Input: {devices.input_name}")
    print(f"Output: {devices.output_name}")
    print(f"Session: {song_dir}")
    app = RecorderApp(backing, backing_path, lyrics_path, song_dir, devices)
    app.run_interactive(use_midi=not args.no_midi)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
