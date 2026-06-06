# T-015 · LANDSCAPE — voice/pedal-controlled multi-take vocal recorder

**Author:** Karen (research) · 2026-06-06
**Question:** Has anyone built a voice/foot-pedal-controlled, automated MULTI-TAKE vocal recorder? What open-source pieces can we BORROW vs what must we BUILD?

---

## TL;DR
- **No one has built exactly this.** Hands-free, voice/pedal-driven, lyric-line punch-in multi-take *vocal* recorder is a genuine gap. Adjacent pieces all exist and are mature.
- The hard parts are **solved problems individually**: audio I/O (PortAudio/AVAudioEngine), take/comp data models (DAW prior art), lyric→timecode forced alignment (WhisperX / MFA), and STT command parsing (Whisper + grammar/wake-word).
- **Borrow** the four engines (capture, alignment, STT, foot-pedal HID). **Build** the glue: the take/comp data model, the command grammar/state machine, and the lyric-punch-in orchestration. That glue *is* the product — nothing off-the-shelf does it.

---

## 1. Has anyone built it? (prior art / competitors)

| Thing | Hands-free? | Multi-take? | Lyric punch-in? | Notes |
|---|---|---|---|---|
| **DAWs** (Logic, Pro Tools, Reaper, Ardour) | ❌ engineer-driven | ✅ takes/comp/loop-record | ❌ (region/time, not lyric) | The gold standard for take *management*; all assume a human at the keys. Reaper/Ardour are scriptable. |
| **Reaper** (ReaScript/Lua/Python) | partial (scriptable) | ✅ best take-comp model in any DAW | ❌ | Closest "borrowable" comp model; could in theory be driven headless, but Brief says **build from scratch, don't script a DAW**. |
| **Ardour** (open-source DAW, C++) | ❌ | ✅ playlists = takes | ❌ | GPL; useful as a *reference design* for take/playlist data model. |
| **Singing/karaoke apps** (Smule, Yousician, Vocaler, Riyaz) | ❌ tap-driven | partial | lyric *display* synced, not punch-in | They align lyrics for scrolling/scoring — proves lyric→timecode is productized, but recording is single-take, no hands-free re-sing. |
| **Voice-controlled DAW research** (e.g. "Voice-controlled audio editing", academic + a11y projects) | ✅ voice | varies | ❌ | Exists in accessibility space (blind producers). Command-driven editing, not automated multi-take vocal capture. |
| **Foot-pedal punch-in** (guitarist loopers: Boss RC, SooperLooper) | ✅ pedal | loop layers | ❌ | Proves the **pedal = clean command channel** instinct (Brief option ②). SooperLooper is open-source (GPL) and pedal-driven — good UX reference. |
| **AI vocal-take selection** (LANDR, iZotope, Vocal comp AI in newer Pro Tools) | ❌ | ✅ | ❌ | Post-pro "pick best take" exists but is OUT of our scope (Brief: hand WAVs off later). |

**Verdict:** the *components* are everywhere; the *integration* — sing hands-free, manage takes by voice/pedal, re-sing a specific lyric line — has **no direct open-source competitor**. That's our wedge.

---

## 2. Reusable OPEN-SOURCE pieces

### A. Audio capture + simultaneous playback (record-while-playing)
The core of the Brief: backing track plays out **while** mic records in. This is full-duplex I/O.

- **Python — `sounddevice`** (PortAudio binding, MIT). `sd.Stream` / `sd.OutputStream`+`InputStream` gives simultaneous in/out on one CoreAudio device. Cleanest for the spike. Pairs with `soundfile` (libsndfile) for WAV write. **← recommended for the Python prototype.**
- **Python — `pyaudio`** (PortAudio, MIT) — older, clunkier callbacks; prefer sounddevice.
- **PortAudio** (C, MIT) under both — battle-tested, sees the Apogee Duet 2 as a standard CoreAudio device (no driver needed, per Brief).
- **Swift — `AVAudioEngine`** (Apple, native) — low-latency, `AVAudioPlayerNode` (backing) + input tap (mic) on one engine, sample-accurate. **← for the hardened Swift build.** `AVAudioRecorder` is too high-level; use the engine + manual buffer write to WAV.
- **JUCE** (C++, GPL/commercial) — if cross-platform ever matters; overkill for a Mac-only studio tool.

**Latency note:** monitoring (singer hears themself + backing) wants round-trip < ~10–12 ms. AVAudioEngine + Duet 2 handles this; Python/PortAudio is fine for *capture timing* but software monitoring may be borderline — **let the singer monitor through the Duet 2's own zero-latency hardware mix** and avoid SW monitoring entirely. (Flag for Dali's spike.)

### B. Take / comp / punch-in data model
**No off-the-shelf library** — this is DAW-internal. Borrow the *design*, build the code.

- **Reaper take/comp model** + **Ardour playlists** = the reference designs to copy. Concepts to lift: a *Song* has N *Takes*; each Take = a WAV + per-line segment markers; a *Comp* = an ordered list of (line → chosen take) pointers. Non-destructive: punch-in writes a **new** take/segment, never overwrites.
- **Punch-in** itself is trivial mechanically: stop playback, seek to line's start timecode, pre-roll a beat, arm record, drop in. The intelligence is **knowing the line's timecode** → that's forced alignment (§C).
- Build on plain WAV + a JSON/SQLite sidecar (song → takes → line-segments). No library needed; this is ours to own.

### C. Lyric → timecode forced alignment (the punch-in enabler)
"Re-sing *that line*" requires mapping each lyric line to a (start, end) in the backing/vocal. Two mature open-source routes:

- **WhisperX** (BSD-ish / MIT-ish, Max Bain) — Whisper ASR + **wav2vec2 forced alignment** → **word-level timestamps**. Works on sung vocals reasonably; you can also align a **known lyric transcript** to audio. Fast, GPU-optional, Python. **← recommended** — modern, word-level, easy install, aligns *given* text (we already have the lyrics).
- **Montreal Forced Aligner (MFA)** (MIT, Kaldi-based) — the academic gold standard for text↔audio phoneme alignment. More accurate phoneme boundaries, but heavier (Kaldi, pronunciation dictionaries, conda). Better if we need phoneme-level or non-English precision. **← fallback / precision option.**
- **aeneas** (AGPL, readbeyond) — lightweight text-to-audio sync (designed for audiobooks/lyrics). Less robust on singing but trivial to run; a quick-start option.
- **Practical approach:** align lyrics to the **backing track's guide/reference** (or a first scratch take) once → cache line timecodes → every punch-in just seeks. Re-align only when needed. Singing pitch/vibrato hurts ASR; aligning the *first full take* (where we know the words) is more reliable than aligning blind.

### D. STT / voice command parsing
Separating **commands** from **singing** through one mic is the key UX risk (Brief). Pieces:

- **openai-whisper / faster-whisper** (MIT) — high-accuracy STT for parsing spoken commands ("start", "re-sing the chorus", "next take"). `faster-whisper` (CTranslate2) is realtime-capable on the iMac.
- **Vosk** (Apache-2.0, Kaldi) — **offline, streaming, low-latency**, supports a **constrained grammar/vocabulary** (you can restrict it to your command words → far fewer false hits). **← best for live command channel** if we go voice (not pedal).
- **openWakeWord** (Apache-2.0) / **Picovoice Porcupine** (free tier) — wake-word ("Hey Studio…") to gate commands (Brief option ③).
- **Pedal route (Brief's lean, option ②):** no STT needed for control at all — a USB/MIDI foot pedal is a **HID/MIDI event**. Read via `python-rtmidi`/`mido` (MIDI pedals) or `hidapi`/`pynput` (USB HID pedals like the cheap "FootSwitch"/PageFlip/AirTurn). **Zero false-trigger, zero latency, zero mic contention** — this is the right primary control. Use STT only for *labeling*/optional convenience.

**Recommendation on the UX problem:** **foot pedal = primary command channel** (transport: arm/punch/stop/next-take), **Whisper/Vosk = optional secondary** for richer spoken commands during gaps. This dodges the command-vs-singing collision entirely and matches Chairman + IA10's lean.

---

## 3. BORROW vs BUILD

### ✅ BORROW (don't reinvent)
1. **Audio I/O** — `sounddevice`/PortAudio (Python spike) → `AVAudioEngine` (Swift harden). Full-duplex record+play.
2. **WAV write** — `soundfile`/libsndfile (Py) / AVAudioFile (Swift).
3. **Forced alignment** — **WhisperX** primary, **MFA** for precision, aeneas for a fast start.
4. **STT** — **faster-whisper** (rich commands) and/or **Vosk** (constrained grammar, streaming).
5. **Foot-pedal input** — `mido`/`python-rtmidi` (MIDI) or `hidapi`/`pynput` (USB HID).
6. **Take-model *design*** — copy Reaper/Ardour's take/playlist/comp concepts.
7. **Loop/punch UX reference** — SooperLooper (pedal-driven, GPL) for interaction feel.

### 🔨 BUILD (this is the product — nothing does it)
1. **Take/comp data model** — Song → Takes → per-lyric-line segments; non-destructive comp pointers. Plain WAV + JSON/SQLite sidecar.
2. **Command grammar + state machine** — `IDLE → PLAYING → RECORDING → PUNCH-IN(line) → REVIEW`; map pedal/voice events to transitions.
3. **Lyric-line punch-in orchestration** — line→timecode lookup, pre-roll, seek, arm, drop-in, write new segment. The "re-sing that line" loop.
4. **The hands-free control layer** — pedal-first event router + optional gap-gated voice, so commands never collide with singing.
5. **WAV export** — flatten chosen comp / dump raw takes for handoff to Logic/AI.

### Explicitly OUT (per Brief)
- Pitch correction, mixing, mastering, AI "best-take" auto-select (later/hand-off).
- Scripting Logic Pro / any DAW — build standalone.

---

## 4. Recommended path (research view, feeds IA10 synth)
1. **Python spike** (Dali): `sounddevice` full-duplex — play backing + record mic on the Duet 2, write WAV. Proves CoreAudio I/O headless. (already his task)
2. **Pedal as primary control**; Whisper/Vosk as optional secondary — kills the mic-collision risk.
3. **WhisperX** to pre-align the lyrics once per song → cache line timecodes → punch-in is just seek+arm.
4. **Own the take/comp model** (copy Reaper's concepts) — that + the punch-in loop is the defensible product.
5. Port hot paths to **AVAudioEngine/Swift** once UX is validated.

**Biggest reuse win:** alignment + capture are free and mature. **Biggest build (and the moat):** the multi-take/lyric-punch-in state machine and data model — no open-source project does hands-free automated vocal multi-take. We're not competing with a DAW; we're building the thing a DAW makes you do by hand.
