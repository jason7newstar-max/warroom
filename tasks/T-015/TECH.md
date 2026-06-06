# T-015 TECH · Audio I/O Stack Spike

## Rig Target

- Studio iMac, macOS CoreAudio.
- Neumann TLM 103 into Apogee Duet 2.
- App scope: standalone multi-take vocal recorder. It must play a backing track while recording mic input, keep WAV takes, and later support foot-pedal/voice commands and lyric-line punch-in.

## Swift AVAudioEngine vs Python sounddevice

### Swift + AVAudioEngine

Best long-term production stack for this rig.

- Direct fit for CoreAudio hardware, low-latency monitoring, aggregate devices, Audio Unit effects, sandbox permissions, MIDI/foot-pedal integration, and a polished macOS UI.
- Better for a studio operator app that must survive long sessions, reconnect devices, show meters/waveforms, and keep audio timing stable.
- More upfront cost: UI, file/session model, waveform/timeline, and command input all need native implementation.

Risk: slower iteration while the interaction model is still unresolved. Punch-in by lyric line and command gating need UX proof before native hardening.

### Python + sounddevice/PortAudio

Best MVP/prototype stack for this task.

- PortAudio exposes macOS CoreAudio devices directly; good enough to validate Duet input/output, full-duplex playback+record, take file writing, and rough pedal/keyboard command flows.
- Fast iteration for the unknowns: command grammar, take naming, pre-roll, punch-in timing, lyric line mapping, and audio export layout.
- Easy to run headless from this iMac for feasibility checks.

Risk: not the final pro app stack. GUI polish, device hotplug, permissions UX, latency tuning, and native pedal support are weaker than Swift.

## Recommendation

Build the MVP in Python first, then port the proven recorder core to Swift.

MVP stack:

- Python 3 + `sounddevice` for CoreAudio full-duplex I/O.
- WAV export via standard-library `wave` or `soundfile` later.
- Foot pedal first for command gating. Voice commands can be added only inside pedal-held command mode or explicit gaps, avoiding false triggers while singing.
- Data model: project folder -> song -> backing file -> takes as timestamped WAVs -> JSON metadata with sample rate, device names, lyric line, start/end sample offsets.

Swift migration target:

- `AVAudioEngine` for playback+record graph.
- `AVAudioFile`/CAF or WAV export.
- Native pedal/MIDI/HID event handling.
- Timeline UI for takes and lyric-line punch-in.

## Spike Result on 2026-06-06

PortAudio/CoreAudio is working on this iMac, but the Apogee Duet 2 is **not currently visible** to CoreAudio.

Observed devices from `sounddevice.query_devices()`:

- `Hue Sync Audio` - 8 input / 4 output
- `BlackHole 2ch` - 2 input / 2 output
- `iMac Microphone` - 1 input / 0 output
- `iMac Speakers` - 0 input / 2 output

`system_profiler SPAudioDataType` also did not list an Apogee/Duet device, and USB profiler search found no Apogee/Duet entry.

Control check: the same script successfully ran a 1-second full-duplex test with `iMac Microphone` as input and `iMac Speakers` as output, proving the Python + sounddevice + PortAudio path can simultaneously record and play through CoreAudio on this iMac.

Conclusion: the submitted spike script is ready to prove the Duet path, but the actual Duet 2 full-duplex test did **not** pass today because the interface is not connected, powered, or enumerated by macOS. Once the Duet appears in Audio MIDI Setup/CoreAudio, rerun:

```bash
cd /Users/pinnyc/codex-work/warroom/tasks/T-015/spike
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python duet_full_duplex_spike.py
```

Expected pass condition: the script finds an Apogee/Duet device with input and output channels, plays a low test tone for ~3 seconds, records simultaneously from the Duet input, writes a WAV, and prints measured input peak/RMS.
