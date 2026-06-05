#!/usr/bin/env python3
"""MAESTRO M0: deterministic atomic ops -> music21 Score -> MIDI/WAV."""

from __future__ import annotations

import argparse
import ast
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from music21 import chord, instrument, meter, metadata, note, stream, tempo


ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "out"
DEFAULT_SOUNDFONT_DIR = ROOT / "soundfonts"

DURATIONS = {
    "whole": 4.0,
    "half": 2.0,
    "quarter": 1.0,
    "eighth": 0.5,
    "16th": 0.25,
}

CHORD_INTERVALS = {
    "maj": [0, 4, 7],
    "major": [0, 4, 7],
    "min": [0, 3, 7],
    "minor": [0, 3, 7],
    "dim": [0, 3, 6],
    "aug": [0, 4, 8],
    "sus2": [0, 2, 7],
    "sus4": [0, 5, 7],
    "maj7": [0, 4, 7, 11],
    "major7": [0, 4, 7, 11],
    "dom7": [0, 4, 7, 10],
    "7": [0, 4, 7, 10],
    "min7": [0, 3, 7, 10],
    "minor7": [0, 3, 7, 10],
}


class MaestroError(Exception):
    pass


class Builder:
    def __init__(self) -> None:
        self.score = stream.Score()
        self.score.metadata = metadata.Metadata()
        self.score.metadata.title = "MAESTRO M0 demo"
        self.parts: Dict[str, stream.Part] = {}
        self.time_signature = meter.TimeSignature("4/4")
        self.pickup_beats = 0.0

    def set_tempo(self, bpm: Any) -> None:
        mark = tempo.MetronomeMark(number=float(bpm))
        if len(self.score.getElementsByClass(tempo.MetronomeMark)) == 0:
            self.score.insert(0, mark)
        else:
            self.score.insert(0, mark)

    def set_meter(self, n: Any, d: Any) -> None:
        self.time_signature = meter.TimeSignature(f"{int(n)}/{int(d)}")
        self.score.insert(0, self.time_signature)
        for part_obj in self.parts.values():
            part_obj.insert(0, self.time_signature)

    def anacrusis(self, beats: Any = 1) -> None:
        self.pickup_beats = float(beats)

    def part(self, name: Any, instr: Any = "Piano") -> None:
        part_name = str(name)
        if part_name in self.parts:
            raise MaestroError(f"part already exists: {part_name}")
        part_obj = stream.Part(id=_safe_id(part_name))
        part_obj.partName = part_name
        part_obj.insert(0, _instrument(str(instr)))
        part_obj.insert(0, self.time_signature)
        self.parts[part_name] = part_obj
        self.score.append(part_obj)

    def add_note(self, part_name: Any, measure: Any, beat: Any, pitch: Any, dur: Any) -> None:
        n = note.Note(str(pitch))
        n.quarterLength = _duration(dur)
        self._insert(str(part_name), int(measure), float(beat), n)

    def stack_chord(
        self,
        part_name: Any,
        measure: Any,
        beat: Any,
        root: Any,
        quality: Any,
        dur: Any = "half",
    ) -> None:
        pitches = _chord_pitches(str(root), str(quality))
        c = chord.Chord(pitches)
        c.quarterLength = _duration(dur)
        self._insert(str(part_name), int(measure), float(beat), c)

    def _insert(self, part_name: str, measure: int, beat: float, element: Any) -> None:
        if part_name not in self.parts:
            raise MaestroError(f"unknown part: {part_name}")
        if beat < 1:
            raise MaestroError(f"beat is 1-based; got {beat}")
        offset = self._offset(measure, beat)
        self.parts[part_name].insert(offset, element)

    def _offset(self, measure: int, beat: float) -> float:
        bar = float(self.time_signature.barDuration.quarterLength)
        if measure == 0:
            if self.pickup_beats <= 0:
                raise MaestroError("measure 0 requires anacrusis(beats)")
            if beat > self.pickup_beats:
                raise MaestroError("pickup beat exceeds anacrusis length")
            return beat - 1
        return self.pickup_beats + ((measure - 1) * bar) + (beat - 1)


def _safe_id(name: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in name).strip("_") or "part"


def _instrument(name: str) -> instrument.Instrument:
    classes = {cls.__name__.lower(): cls for cls in instrument.Instrument.__subclasses__()}
    key = name.replace(" ", "").lower()
    for cls in instrument.Instrument.__subclasses__():
        if cls.__name__.lower() == key:
            return cls()
    try:
        return instrument.fromString(name)
    except Exception:
        return instrument.Piano()


def _duration(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().lower()
    if text in DURATIONS:
        return DURATIONS[text]
    try:
        return float(text)
    except ValueError as exc:
        raise MaestroError(f"unknown duration: {value}") from exc


def _chord_pitches(root: str, quality: str) -> List[str]:
    q = quality.lower()
    if q not in CHORD_INTERVALS:
        raise MaestroError(f"unknown chord quality: {quality}")
    root_name = root if any(ch.isdigit() for ch in root) else f"{root}4"
    base = note.Note(root_name)
    out = []
    for semitones in CHORD_INTERVALS[q]:
        n = base.transpose(semitones)
        out.append(n.nameWithOctave)
    return out


def parse_score(path: Path) -> List[Dict[str, Any]]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text())
        if isinstance(data, dict):
            data = data.get("ops", [])
        if not isinstance(data, list):
            raise MaestroError("JSON score must be a list or an object with an ops list")
        return [_normalize_json_op(item) for item in data]
    return list(_parse_text_ops(path.read_text().splitlines()))


def _normalize_json_op(item: Any) -> Dict[str, Any]:
    if not isinstance(item, dict) or "op" not in item:
        raise MaestroError(f"bad JSON op: {item!r}")
    args = item.get("args")
    if args is None:
        args = {k: v for k, v in item.items() if k != "op"}
    return {"op": item["op"], "args": args}


def _parse_text_ops(lines: Iterable[str]) -> Iterable[Dict[str, Any]]:
    for line_no, raw in enumerate(lines, 1):
        line = _strip_comment(raw).strip()
        if not line:
            continue
        if not line.endswith(")") or "(" not in line:
            raise MaestroError(f"line {line_no}: expected op(...), got {raw!r}")
        op, rest = line.split("(", 1)
        args_text = rest[:-1].strip()
        try:
            args = ast.literal_eval(f"({args_text},)" if args_text and "," not in args_text else f"({args_text})")
        except Exception as exc:
            raise MaestroError(f"line {line_no}: could not parse arguments") from exc
        if args_text == "":
            args = ()
        if not isinstance(args, tuple):
            args = (args,)
        yield {"op": op.strip(), "args": list(args)}


def _strip_comment(raw: str) -> str:
    quote: Optional[str] = None
    escaped = False
    for index, ch in enumerate(raw):
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if quote:
            if ch == quote:
                quote = None
            continue
        if ch in {"'", '"'}:
            quote = ch
            continue
        if ch == "#":
            return raw[:index]
    return raw


def build_score(ops: Iterable[Dict[str, Any]]) -> stream.Score:
    builder = Builder()
    dispatch = {
        "set_tempo": builder.set_tempo,
        "set_meter": builder.set_meter,
        "part": builder.part,
        "add_note": builder.add_note,
        "stack_chord": builder.stack_chord,
        "anacrusis": builder.anacrusis,
    }
    for index, op in enumerate(ops, 1):
        name = str(op["op"])
        if name not in dispatch:
            raise MaestroError(f"op {index}: unknown operation {name}")
        args = op.get("args", [])
        try:
            if isinstance(args, dict):
                dispatch[name](**args)
            else:
                dispatch[name](*args)
        except TypeError as exc:
            raise MaestroError(f"op {index} {name}: wrong arguments") from exc
    if not builder.parts:
        raise MaestroError("score has no parts")
    return builder.score


def find_soundfont() -> Optional[Path]:
    for candidate in sorted(DEFAULT_SOUNDFONT_DIR.rglob("*.sf2")):
        return candidate
    return None


def render(score_path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    ops = parse_score(score_path)
    score = build_score(ops)
    midi_path = out_dir / "demo.mid"
    wav_path = out_dir / "demo.wav"
    score.write("midi", fp=str(midi_path))
    print(f"wrote {midi_path}")

    fluidsynth = shutil.which("fluidsynth")
    soundfont = find_soundfont()
    if not fluidsynth:
        print("skipped WAV: fluidsynth binary not found", file=sys.stderr)
        return
    if not soundfont:
        print("skipped WAV: no .sf2 soundfont found in maestro/soundfonts", file=sys.stderr)
        return
    cmd = [fluidsynth, "-ni", str(soundfont), str(midi_path), "-F", str(wav_path), "-r", "44100"]
    subprocess.run(cmd, check=True)
    print(f"wrote {wav_path}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="MAESTRO M0 atomic-op renderer")
    sub = parser.add_subparsers(dest="command", required=True)
    render_parser = sub.add_parser("render", help="render a score file to MIDI and WAV when possible")
    render_parser.add_argument("score", type=Path, help="score file, e.g. scores/demo.txt")
    render_parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output directory")
    args = parser.parse_args(argv)

    try:
        if args.command == "render":
            score_path = args.score
            if not score_path.is_absolute():
                score_path = ROOT / score_path
            out_dir = args.out if args.out.is_absolute() else ROOT / args.out
            render(score_path, out_dir)
            return 0
    except (MaestroError, subprocess.CalledProcessError) as exc:
        print(f"maestro: {exc}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
