# PHANTOM Native — low-latency monitor engine (JUCE)

The C++ path to **"feels-zero" latency** monitoring with effects (the Python software
monitor in `../recorder/studio_ui/` is fine for review but sits at ~20 ms because of
the Python/PortAudio path). A native JUCE callback at a **64-sample buffer** runs the
CLA-stage vocal chain in real time — roughly **3–7 ms round trip**, the same league as
Logic. (Note: literally-zero latency + effects is physically impossible without onboard
DSP hardware like a UA Apollo — see the chat. This gets as close as software can.)

## Chain (Source/Main.cpp · CLAStageMonitor)
HPF 90 Hz → Compressor (−22 dB, 4:1, 3/80 ms) → de-mud −2 dB @350 → presence +3 dB @4k
→ air +3.5 dB @8k → +3 dB makeup → stage reverb. Mirrors the Python `_cla_stage()`.

## Build (macOS — needs CMake + Xcode command-line tools)
```bash
cd tasks/T-015/phantom-native
cmake -B build -G Xcode           # first run fetches JUCE (~1–2 min)
cmake --build build --config Release
./build/PhantomNative_artefacts/Release/PhantomNative
```
It opens the **Duet** in/out at a 64-sample buffer and monitors your voice through the
chain. Open the Duet's hardware monitor OFF while testing this (avoid double monitoring).

## Status (2026-06-07)
**Scaffold** — written, not yet compiled on this machine. Next: build, confirm it runs
at 64 samples without dropouts, tune the chain by ear, then expose params + wrap with the
PHANTOM UI (the web UI can drive it, or port the UI to a JUCE plugin/standalone). This is
the multi-day "PHANTOM as a real product" track; the Python UI stays for record/mix/review.
