#!/usr/bin/env python3
"""T-015 · P1 — post-record processing chain (the "unmanned mix" step).

Takes a recorded vocal take WAV and runs it through a Pedalboard effects chain
(high-pass / EQ -> Compressor -> make-up Gain -> Reverb). Critically, it can host
BOTH Pedalboard's built-in DSP AND any external VST3 / AU plugin (FabFilter,
Waves, Logic stock, etc.) via `pedalboard.load_plugin` — so the unmanned studio
mixes with the engineer's OWN plugins, no new infrastructure. VST3/AU are the
universal standards; nothing to "emulate."

Usage:
  python3 process_chain.py take.wav                          # built-in default chain
  python3 process_chain.py take.wav -o take_mixed.wav
  python3 process_chain.py take.wav \
      --plugin "/Library/Audio/Plug-Ins/VST3/FabFilter Pro-C 2.vst3" \
      --plugin "/Library/Audio/Plug-Ins/Components/ValhallaRoom.component"
"""
from __future__ import annotations

import argparse
from pathlib import Path

from pedalboard import Pedalboard, HighpassFilter, Compressor, Gain, Reverb, load_plugin
from pedalboard.io import AudioFile


def build_default_chain() -> Pedalboard:
    """A safe, musical vocal chain from Pedalboard's built-in DSP.
    Tune any stage, or swap a stage for a load_plugin() instance below.
    This is the P2 hook: later, an AI step sets these numbers per-source
    (the "PinLA AUTO" idea) instead of fixed defaults."""
    return Pedalboard([
        HighpassFilter(cutoff_frequency_hz=80),                       # clear low rumble
        Compressor(threshold_db=-18, ratio=3.0, attack_ms=5, release_ms=120),
        Gain(gain_db=2.0),                                            # make-up gain
        Reverb(room_size=0.25, wet_level=0.12, dry_level=0.88, width=0.9),
    ])


def load_external(path: str):
    """Load the engineer's OWN VST3/AU plugin. Inspect/tune params with:
        p = load_external(path); print(p.parameters.keys())
        p.threshold_db = -20   # set like attributes
    """
    return load_plugin(path)


def process(in_wav: str, out_wav: str, board: Pedalboard) -> None:
    with AudioFile(in_wav) as f:
        audio = f.read(f.frames)
        sr = f.samplerate
    processed = board(audio, sr)
    with AudioFile(out_wav, "w", sr, num_channels=processed.shape[0]) as f:
        f.write(processed)
    print(f"✓ {in_wav} -> {out_wav}  ({sr} Hz)")


def main() -> None:
    ap = argparse.ArgumentParser(description="P1 post-record mix chain")
    ap.add_argument("input", help="recorded take WAV")
    ap.add_argument("-o", "--output", help="output WAV (default: <input>_mixed.wav)")
    ap.add_argument("--plugin", action="append", default=[],
                    help="VST3/AU plugin path to insert (repeatable). "
                         "If any are given, they REPLACE the built-in default chain.")
    args = ap.parse_args()

    out = args.output or f"{Path(args.input).with_suffix('')}_mixed.wav"
    board = Pedalboard([load_external(p) for p in args.plugin]) if args.plugin \
        else build_default_chain()
    process(args.input, out, board)


if __name__ == "__main__":
    main()
