# T-015 · SYNTHESIS — buildable MVP plan (IA10)

Synthesizes Karen (LANDSCAPE), Mini (DESIGN), Dali (TECH + spike), Gemma (risk). The four converged hard — high confidence.

## Headlines
1. **It's a real gap (= the moat).** No open-source/commercial product does *hands-free, voice/pedal-driven, lyric-line punch-in MULTI-TAKE vocal capture*. DAWs make you do it by hand; karaoke apps are single-take. We're building the thing a DAW makes you do manually. (Karen)
2. **The audio pipeline is PROVEN.** Dali's spike ran a full-duplex record+play on this iMac's CoreAudio successfully. ⚠️ BUT the **Apogee Duet 2 is not currently connected/powered/enumerated** — macOS doesn't see it. Plug it in + power it, then rerun the spike to confirm the real rig.
3. **Pedal-first kills the hard problem.** Everyone (Karen, Mini, Dali, Gemma, Chairman, IA10) agrees: the foot pedal is the PRIMARY control channel → zero mic-collision, zero false-trigger, zero latency. Voice is optional/secondary, only in pedal-held gaps.

## BORROW (mature, don't reinvent)
- **Capture:** Python `sounddevice` (PortAudio) full-duplex → Swift `AVAudioEngine` later. `soundfile` for WAV.
- **Lyric→timecode:** **WhisperX** (word-level forced alignment of known lyrics) — align once per song, cache line timecodes, punch-in = seek+arm. MFA as precision fallback.
- **Commands:** foot pedal via `hidapi`/`pynput` (USB HID) or `mido`/`python-rtmidi` (MIDI). Optional spoken commands via `faster-whisper` / Vosk (constrained grammar) in gaps only.
- **Take-model DESIGN:** copy Reaper/Ardour concepts (Song→Takes→line-segments, non-destructive comp pointers).
- **Monitoring:** use the **Duet 2's own zero-latency hardware mix** (singer hears self+backing through the interface) — avoid software monitoring entirely (latency).

## BUILD (this is the product)
- **Take/comp data model** — Song → Takes → per-lyric-line segments; non-destructive; plain WAV + JSON/SQLite sidecar.
- **Command state machine** (Mini's): IDLE→READY→PLAYING→RECORDING_FULL_TAKE→PUNCH_ARMED→RECORDING_PUNCH→REVIEW→EXPORTING. Pedal gates intent; voice only when safe.
- **Lyric-line punch-in orchestration** — line→timecode → pre-roll → seek → arm → drop-in → write new segment.
- **Export** — raw WAVs + a comp manifest → handoff to Logic / AI mix/master (out of scope here).

## Biggest risk (Gemma + Karen)
Sample-accurate timeline sync across takes + command/trigger latency. Mitigate: single clock/stream, pedal (HID, instant) not voice for transport, pre-roll, log sample offsets in metadata.

## MVP phases
- **M1 (Python, now):** load backing + lyrics → pedal: start/stop/new-take → full-duplex record on the Duet 2 → save timestamped WAV takes + JSON. (Proves the core loop.)
- **M2:** WhisperX line alignment + "re-sing line N" pedal/voice punch-in (non-destructive segment).
- **M3:** REVIEW/comp + WAV export manifest. (Then optional Swift hardening.)

## Next step
1. **Chairman:** plug in + power the Apogee Duet 2 (so it enumerates), and order the ~$20 USB foot pedal.
2. **IA10:** build M1 in Python; the moment the Duet is visible, validate on the real rig.
