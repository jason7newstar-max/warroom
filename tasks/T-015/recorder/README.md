# T-015 M1 Recorder

Standalone Python multi-take vocal recorder for the ONE TEN vocal booth loop.

M1 scope only:

- Load one backing track (`.wav`, `.aiff`, `.mp3` if local libsndfile supports MP3).
- Optionally load a lyrics `.txt` file with one lyric line per line.
- Play backing out while recording mic in through CoreAudio via `sounddevice`.
- Save every take non-destructively as WAV plus JSON sidecar.
- Keyboard and MIDI foot-pedal controls.
- No software monitoring. Monitor voice/backing through the Apogee Duet hardware mix.

## Setup

```bash
cd /Users/pinnyc/codex-work/warroom/tasks/T-015/recorder
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

List devices:

```bash
.venv/bin/python recorder.py --list-devices
```

Run a session:

```bash
.venv/bin/python recorder.py \
  --backing /path/to/backing.wav \
  --lyrics /path/to/lyrics.txt \
  --song my_song
```

Takes are written to:

```text
tasks/T-015/recorder/sessions/<song>/take_<NN>_<timestamp>.wav
tasks/T-015/recorder/sessions/<song>/take_<NN>_<timestamp>.json
```

The JSON sidecar includes take number, input/output device names, samplerate, duration, `started_at`, frame count, input channels, backing file, lyrics file, and `software_monitoring=false`.

## Device Behavior

The app auto-detects an Apogee Duet 2 when CoreAudio exposes a device name containing `Apogee` or `Duet`.

Selection order:

1. Manual `--input-device` / `--output-device`, if supplied.
2. Auto-detected Apogee/Duet device or split Apogee input/output pair.
3. Default CoreAudio input/output, usually the built-in iMac microphone and speakers when the Duet is unplugged.

This means it is testable now on the built-in device and will auto-use the Duet 2 once plugged in, powered, and visible in Audio MIDI Setup.

## Keyboard / USB-HID Pedal Map

A USB-HID foot pedal that emits one of these keystrokes drops in directly:

| Key | Intent |
|---|---|
| `space` | start/stop recording the current take |
| `n` | arm a new take |
| `p` | play last take |
| `q` | quit |

## MIDI Footswitch Map

Requires `python-rtmidi`. The app opens the first available MIDI input port.

| MIDI event | Intent |
|---|---|
| Note 60 or CC 20 value > 0 | start/stop recording |
| Note 61 or CC 21 value > 0 | new take |
| Note 62 or CC 22 value > 0 | play last take |
| Note 63 or CC 23 value > 0 | quit |

Disable MIDI:

```bash
.venv/bin/python recorder.py --backing /path/to/backing.wav --no-midi
```

## Built-In Device End-to-End Test

This generates a short backing tone, records about 4 seconds through the current default input while playing the tone to the default output, then prints the WAV and JSON paths:

```bash
.venv/bin/python recorder.py --self-test --seconds 4
```

Expected result:

```text
SELF-TEST PASS
WAV=.../sessions/m1_self_test/take_001_YYYYMMDD_HHMMSS.wav
JSON=.../sessions/m1_self_test/take_001_YYYYMMDD_HHMMSS.json
duration=...
```
