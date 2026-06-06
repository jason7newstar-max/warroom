# T-015 · AI 全自动录音环节(scoped MVP)

**Chairman:** 文天 — runs a NYC recording studio, conservatory-trained composer.

## Scope (NARROWED 2026-06-06 — important)
NOT the whole record→mix→master pipeline. **ONLY the recording stage, fully automated, as a STANDALONE app** (do NOT script Logic Pro — build from scratch). Post-production (pitch-correct, mixing, mastering) is OUT — hand the recorded WAVs to AI tools / Logic later (the Chairman bets AI mix/master vendors mature in 3-6 months).

**Core loop the app must do:**
1. Voice command "start / play backing track" → 伴奏 plays through the interface.
2. Mic input → recorded to a track/take while the backing plays.
3. Multi-TAKE: keep multiple takes per song.
4. **Punch-in by lyric line:** "re-sing that line" → re-record from that line.
5. (later) auto-select the best take by measurable proxies.
6. Export the takes as **WAV** → he takes them to Logic / AI for the rest.

**Key UX problem to solve:** voice commands and singing BOTH go through the same mic — how to tell a command from singing? Options: ① commands only in gaps, ② **foot pedal/gesture (Chairman + IA10 lean here — cleanest, zero false-trigger)**, ③ wake word, ④ second mic/phone as command channel.

## The Chairman's actual hardware (build to THIS)
- **Machine:** the studio **iMac** (same one the war room runs on).
- **Mic:** Neumann **TLM 103** (large-diaphragm condenser).
- **Interface:** Apogee **Duet 2** — a standard **CoreAudio** USB interface (no special driver needed; AVAudioEngine / PortAudio see it directly).
- Monitor headphones (incl. earbud monitors).

## Stack options
- Native macOS **Swift + AVAudioEngine** (low-latency, pro, long-term) vs a fast **Python (sounddevice/PortAudio)** prototype first. IA10 leans: Python spike to validate UX → Swift to harden.

## War-room assignments (PARALLEL)
- **Karen (research):** LANDSCAPE.md — has anyone built a voice-controlled / automated multi-take vocal recorder? Open-source pieces to reuse (audio capture, take/comp management, punch-in, lyric→timecode forced alignment, STT command parsing). What to borrow vs build.
- **Mini (design):** DESIGN.md — the interaction + architecture for voice-control + multi-take + lyric-line punch-in (no hardware needed): command grammar, take data model, lyric→timecode mapping, the foot-pedal command flow.
- **Dali (iMac — HAS the hardware):** TECH.md — Swift-vs-Python eval for THIS rig; + a feasibility SPIKE: a tiny script that records ~3s from the Apogee Duet 2 input AND plays a backing track out simultaneously (prove CoreAudio I/O works headless on this iMac). Commit the spike.
- **Gemma (3rd opinion):** concise outside take — biggest risk / what to simplify.
- **IA10:** synthesize all four → a buildable MVP plan for the Chairman.
