# MAESTRO M0

MAESTRO M0 is the deterministic core spine for the project: a structured
atomic-op score description becomes a `music21` score, exports MIDI, and renders
WAV audio through FluidSynth when available.

There is no natural-language LLM layer in M0. The LLM parser comes later; this
milestone proves `ops -> score -> sound`.

## Install

```sh
cd maestro
python3 -m pip install --user "music21<9"
```

Install FluidSynth if your machine has Homebrew:

```sh
brew install fluidsynth
```

Add a General MIDI SoundFont under `soundfonts/`. See
`soundfonts/README.md` for the documented source used for this seed.

## Run

```sh
cd maestro
python3 maestro.py render scores/demo.txt
```

Outputs:

- `out/demo.mid`
- `out/demo.wav` when `fluidsynth` and a `.sf2` file are available

If FluidSynth is unavailable, M0 still writes the MIDI file and prints the render
step it skipped.

Manual render:

```sh
fluidsynth -ni soundfonts/YourSoundFont.sf2 out/demo.mid -F out/demo.wav -r 44100
```

## Atomic Ops

Text score files are line-based `op(...)` commands. JSON is also accepted as a
list of `{ "op": "...", "args": [...] }` objects.

- `set_tempo(bpm)`
- `set_meter(n, d)`
- `anacrusis(beats)` enables pickup measure `0`
- `part(name, instrument)`
- `add_note(part, measure, beat, pitch, dur)`
- `stack_chord(part, measure, beat, root, quality, dur="half")`

Measures are 1-based. Measure `0` is reserved for the anacrusis. Beats are
1-based inside each measure. Durations can be numbers in quarter lengths or
names: `whole`, `half`, `quarter`, `eighth`, `16th`.

Supported chord qualities: `maj`, `min`, `dim`, `aug`, `sus2`, `sus4`, `maj7`,
`dom7`, `min7`.

## Demo

`scores/demo.txt` reproduces the Chairman's seed example:

- 4/4 with a weak-beat pickup
- Violin I enters and lands on a half-note `A4`
- harmony stacks an A major triad, then extends it to A major 7
- cello anchors the root
- the phrase continues for multiple bars so it sounds musical

## Next

- **M0.5:** LLM natural-language to atomic ops, with schema validation.
- **M1:** per-measure editing plus save/load of structured score JSON.
- **M2:** MusicXML/Verovio notation view for live score inspection.
