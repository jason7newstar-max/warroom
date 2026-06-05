#!/usr/bin/env python3
"""MAESTRO M0.5 — natural language -> atomic ops -> score -> sound.

Plain language ("写四小节 D 大调,小提琴主旋律,大提琴垫低音,中间叠个属七和弦")
is translated by an LLM (Groq Llama) into MAESTRO's deterministic atomic ops,
which the M0 engine (maestro.py) turns into a music21 score, MIDI, and audio.

The LLM ONLY emits atomic ops; the music itself stays deterministic + editable.

Usage:
    python3 maestro_nl.py "your description in any language" [--name out_basename]

Reads GROQ_API_KEY from ~/.hermes/.env (same place voice-stt uses).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCORES = ROOT / "scores"
OUT = ROOT / "out"
HERMES_ENV = Path.home() / ".hermes" / ".env"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"

VALID_OPS = {"set_tempo", "set_meter", "anacrusis", "part", "add_note", "stack_chord"}

SYSTEM_PROMPT = """You are MAESTRO's composition compiler. You translate a musician's
free-form description (any language) into MAESTRO atomic-op commands. You output ONLY
op lines — no prose, no markdown, no code fences, no comments.

THE ONLY ALLOWED OPS (one per line, Python-literal args, strings double-quoted):
  set_tempo(bpm)                               e.g. set_tempo(96)
  set_meter(n, d)                              e.g. set_meter(4, 4)
  anacrusis(beats)                             optional pickup; then use measure 0
  part("Name", "Instrument")                   declare a part BEFORE adding notes to it
  add_note("Part", measure, beat, "Pitch", "dur")
  stack_chord("Part", measure, beat, "Root", "quality", "dur")

RULES:
- Measures are 1-based (measure 0 only if you called anacrusis). Beats are 1-based.
- Pitch = note name + octave, e.g. "A4", "C#5", "Eb3". Root for chords e.g. "A3".
- dur is one of: "whole","half","quarter","eighth","16th".
- chord quality is one of: maj, min, dim, aug, sus2, sus4, maj7, dom7, min7.
- Instruments (music21 names): Violin, Viola, Violoncello, Contrabass, StringInstrument,
  Flute, Oboe, Clarinet, Bassoon, Trumpet, Horn, Trombone, Piano, Harp, Timpani.
- Always: first set_tempo, then set_meter, (optional anacrusis), then declare every
  part() once, THEN add_note/stack_chord. Never add to an undeclared part.
- Write REAL, musical material that fits the request: melody + harmony + bass,
  sensible voice-leading, multiple bars so it breathes. Respect key, meter, mood,
  instrument and bar-count the user asks for. If unspecified, choose tastefully.

EXAMPLE (request: "two bars in A major, violin melody, cello bass, an A major7 in the middle"):
set_tempo(88)
set_meter(4, 4)
part("Violin", "Violin")
part("Harmony", "StringInstrument")
part("Cello", "Violoncello")
add_note("Violin", 1, 1, "A4", "half")
stack_chord("Harmony", 1, 1, "A3", "maj7", "half")
add_note("Cello", 1, 1, "A2", "half")
add_note("Violin", 1, 3, "C#5", "quarter")
add_note("Violin", 1, 4, "E5", "quarter")
stack_chord("Harmony", 1, 3, "E3", "dom7", "half")
add_note("Cello", 1, 3, "E2", "half")
add_note("Violin", 2, 1, "A4", "whole")
stack_chord("Harmony", 2, 1, "A3", "maj", "whole")
add_note("Cello", 2, 1, "A2", "whole")

Output ONLY the op lines for the user's request."""


def load_groq_key() -> str:
    if not HERMES_ENV.exists():
        sys.exit(f"maestro_nl: {HERMES_ENV} not found (need GROQ_API_KEY)")
    for line in HERMES_ENV.read_text().splitlines():
        if line.startswith("GROQ_API_KEY="):
            return line.split("=", 1)[1].strip()
    sys.exit("maestro_nl: GROQ_API_KEY not in ~/.hermes/.env")


def call_groq(key: str, description: str) -> str:
    body = json.dumps({
        "model": MODEL,
        "temperature": 0.4,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": description},
        ],
    }).encode()
    req = urllib.request.Request(
        GROQ_URL, data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "maestro-nl/0.5",  # Groq WAF 403s urllib's default UA
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"]


OP_LINE = re.compile(r'^\s*(set_tempo|set_meter|anacrusis|part|add_note|stack_chord)\s*\(.*\)\s*$')


def sanitize(raw: str) -> str:
    """Keep only valid-looking op lines; drop prose / fences."""
    lines = []
    for ln in raw.splitlines():
        s = ln.strip().strip("`")
        if OP_LINE.match(s):
            lines.append(s)
    if not lines:
        sys.exit("maestro_nl: model returned no valid ops:\n" + raw)
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="MAESTRO M0.5 natural-language -> music")
    ap.add_argument("description", help="plain-language description of the music")
    ap.add_argument("--name", default="nl", help="output basename (default: nl)")
    args = ap.parse_args()

    key = load_groq_key()
    print("→ asking Groq Llama to compile your words into a score…", file=sys.stderr)
    ops = sanitize(call_groq(key, args.description))

    SCORES.mkdir(exist_ok=True)
    score_path = SCORES / f"{args.name}.txt"
    score_path.write_text(f"# generated from: {args.description}\n{ops}")
    print("\n===== generated atomic ops =====")
    print(ops)
    print(f"(saved → {score_path})\n")

    print("===== rendering via maestro.py =====", file=sys.stderr)
    rc = subprocess.call([sys.executable, str(ROOT / "maestro.py"), "render", str(score_path)])
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
