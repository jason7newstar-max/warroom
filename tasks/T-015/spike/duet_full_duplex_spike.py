#!/usr/bin/env python3
"""Headless CoreAudio full-duplex spike for Apogee Duet 2 via PortAudio."""

from __future__ import annotations

import argparse
import math
import re
import sys
import wave
from datetime import datetime
from pathlib import Path

import numpy as np
import sounddevice as sd


DEFAULT_DEVICE_RE = r"apogee|duet"
DEFAULT_SECONDS = 3.0
DEFAULT_RATE = 44100
DEFAULT_TONE_HZ = 440.0
DEFAULT_VOLUME = 0.08


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List CoreAudio devices and run a short full-duplex playback+record test."
    )
    parser.add_argument("--device-regex", default=DEFAULT_DEVICE_RE)
    parser.add_argument("--input-regex", default=None)
    parser.add_argument("--output-regex", default=None)
    parser.add_argument("--seconds", type=float, default=DEFAULT_SECONDS)
    parser.add_argument("--samplerate", type=int, default=DEFAULT_RATE)
    parser.add_argument("--tone-hz", type=float, default=DEFAULT_TONE_HZ)
    parser.add_argument("--volume", type=float, default=DEFAULT_VOLUME)
    parser.add_argument("--channels", type=int, default=1, help="Input channels to record.")
    parser.add_argument("--out", default=None, help="Output WAV path.")
    parser.add_argument("--list-only", action="store_true")
    return parser.parse_args()


def print_devices(devices: list[dict]) -> None:
    print("CoreAudio/PortAudio devices:")
    for idx, dev in enumerate(devices):
        print(
            f"  {idx}: {dev['name']} "
            f"({dev['max_input_channels']} in, {dev['max_output_channels']} out, "
            f"default_sr={dev['default_samplerate']:.0f})"
        )


def find_device(devices: list[dict], pattern: str, *, needs_input: bool, needs_output: bool) -> int | None:
    regex = re.compile(pattern, re.IGNORECASE)
    for idx, dev in enumerate(devices):
        if not regex.search(dev["name"]):
            continue
        if needs_input and dev["max_input_channels"] < 1:
            continue
        if needs_output and dev["max_output_channels"] < 1:
            continue
        return idx
    return None


def make_tone(seconds: float, samplerate: int, frequency: float, volume: float) -> np.ndarray:
    frames = int(math.ceil(seconds * samplerate))
    t = np.arange(frames, dtype=np.float32) / float(samplerate)
    mono = (np.sin(2.0 * np.pi * frequency * t) * volume).astype(np.float32)
    return np.column_stack([mono, mono])


def write_wav(path: Path, samples: np.ndarray, samplerate: int) -> None:
    clipped = np.clip(samples, -1.0, 1.0)
    pcm16 = (clipped * np.iinfo(np.int16).max).astype("<i2")
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(samples.shape[1] if samples.ndim > 1 else 1)
        wav.setsampwidth(2)
        wav.setframerate(samplerate)
        wav.writeframes(pcm16.tobytes())


def main() -> int:
    args = parse_args()
    devices = list(sd.query_devices())
    print_devices(devices)

    if args.list_only:
        return 0

    if args.input_regex or args.output_regex:
        in_re = args.input_regex or args.device_regex
        out_re = args.output_regex or args.device_regex
        input_device = find_device(devices, in_re, needs_input=True, needs_output=False)
        output_device = find_device(devices, out_re, needs_input=False, needs_output=True)
    else:
        duplex_device = find_device(devices, args.device_regex, needs_input=True, needs_output=True)
        input_device = output_device = duplex_device

    if input_device is None or output_device is None:
        print(
            "\nFAIL: could not find matching input/output device. "
            f"Default target regex was {args.device_regex!r}."
        )
        print("Check that the Apogee Duet 2 is connected, powered, and visible in Audio MIDI Setup.")
        return 2

    input_name = devices[input_device]["name"]
    output_name = devices[output_device]["name"]
    input_channels = min(args.channels, int(devices[input_device]["max_input_channels"]))
    if input_channels < 1:
        print("FAIL: selected input device has no input channels.")
        return 2

    print(f"\nUsing input device {input_device}: {input_name}")
    print(f"Using output device {output_device}: {output_name}")
    print(f"Running {args.seconds:.1f}s full-duplex test at {args.samplerate} Hz...")

    backing = make_tone(args.seconds, args.samplerate, args.tone_hz, args.volume)
    recording = sd.playrec(
        backing,
        samplerate=args.samplerate,
        channels=input_channels,
        dtype="float32",
        device=(input_device, output_device),
        blocking=True,
    )

    out_path = Path(args.out) if args.out else Path(
        f"duet_full_duplex_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    )
    write_wav(out_path, recording, args.samplerate)

    peak = float(np.max(np.abs(recording))) if recording.size else 0.0
    rms = float(np.sqrt(np.mean(np.square(recording)))) if recording.size else 0.0
    print(f"PASS: wrote {out_path}")
    print(f"Input peak={peak:.6f}, rms={rms:.6f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
