# T-010 — 用语言写交响乐 · LANDSCAPE (first pass)

**Owner of this survey:** IA10 (Supervisor) · 2026-06-05
**The ask (Chairman, classically-trained composer):** NOT a Suno-style one-shot generator. A **tool/app where natural language is the precise control layer for composing an orchestral score** — "第1小节, 速度X, 弱起, 小提琴拉某音, 叠三和弦再叠七和弦…" → structured score → MIDI/MusicXML → notation + playback. **Incremental, editable, version-able, high control over instrument/harmony/rhythm/arrangement.** Long-term project.

---

## The 4 buckets of prior art

### 1. Black-box Text → symbolic MIDI (powerful, but NOT controllable the way he wants)
- **MIDI-LLM** — NeurIPS AI4Music '25. Text→multitrack MIDI by expanding an LLM's vocab with MIDI tokens. FAD 0.173 / CLAP 22.1, 3–14× realtime. Code: github.com/slSeanWU/MIDI-LLM. → SOTA quality, but you *prompt-and-pray*; no per-measure/per-note surgical control.
- **Text2midi** — earlier baseline (FAD 0.818). 
- **MuseCoco** ("Music Composition Copilot") — text→symbolic MIDI via extracted musical attributes.
- **XMusic** — multimodal symbolic gen, emotion control.
- **ISMIR 2025** — symbolic music from NL prompts using an LLM-enhanced dataset.
> Verdict: these are **generators**, not **instruments for a composer**. Wrong paradigm for him — black box, low controllability. Useful only as a *starting-sketch* option.

### 2. Multi-agent composition (mirrors the 总谱→配器 workflow — but one-shot)
- **ComposerX** (arXiv 2404.18081) — leader / melody / harmony / instrument / reviewer / **arrangement** agents → outputs **ABC notation**. Literally encodes the classical workflow as agents.
- **CoComposer** (arXiv 2509.00132) — 5 agents on the traditional composition workflow; tested GPT-4o / DeepSeek-V3 / Gemini-2.5-Flash.
> Verdict: **closest to his mental model** (motive→harmony→orchestration as roles). BUT they run once from a prompt; not an interactive, editable, "change measure 12's viola" loop. We can *steal the role decomposition*, drop the one-shot framing.

### 3. NL "copilots" that edit notes (closest to his interaction, wrong scope)
- **music-copilot** (github TommyX12/music-copilot) — FL Studio piano-roll script; GPT **creates/edits notes via natural language**. This is the nearest existing thing to "用语言改谱". But piano-roll/DAW-bound, pop-oriented, not orchestral-score-grade.
- **Ableton Copilot MCP**, **Soundverse Agent** — conversational controllers over a DAW/platform. NL → DAW actions. Again: production tools, not score-native composer tools.
- Microsoft Copilot×Suno — just routes to Suno (black box).

### 4. The build-from-scratch toolchain (all open-source, mature)
- **music21** (MIT, MIT-born) — the spine: in-memory score model, **MusicXML + MIDI export**, transposition, chord/harmony objects, analysis. Perfect target representation.
- **LangGraph + music21 agent** — NirDiamant/GenAI_Agents has a working `music_compositor_agent` notebook (NL → music21) to crib from.
- **ABC notation** — compact, LLM-friendly text format (ComposerX uses it); good intermediate.
- **FluidSynth + orchestral SoundFont (.sf2)** — free audio rendering of MIDI.
- **VexFlow** (web, JS) / **LilyPond** (engraving) / **Verovio** (MusicXML→SVG in browser) — notation display.
- **CSyMR** (arXiv 2601.11556) — ReAct controller + **deterministic music21 operators**, decomposing queries into *atomic, verifiable* score operations. → This is the pattern for our "language → structured edit op" core.

---

## 🎯 The gap = his opportunity
Nobody is doing the **composer-grade, score-native, INCREMENTAL, language-as-precise-control** tool:
- Generators (bucket 1) = no control.
- Multi-agent (bucket 2) = right workflow, but one-shot, not editable.
- Copilots (bucket 3) = right interaction, but DAW/pop, not orchestral-score thinking.
- The toolchain (bucket 4) = all the parts exist, **unassembled** for this purpose.

His differentiator: a trained composer's mental model (motive-first, then orchestration, explicit harmony stacking 三和弦→七和弦, anacrusis, voice-leading) exposed as a **persistent, editable score you drive in language** — "borrow the role-decomposition from ComposerX, the atomic-verifiable-ops from CSyMR, the score model from music21, render with Verovio+FluidSynth." That assembly doesn't exist as a product.

## Sources
- MIDI-LLM: arxiv.org/html/2511.03942v1 · github.com/slSeanWU/MIDI-LLM
- ComposerX: arxiv.org/pdf/2404.18081
- CoComposer: arxiv.org/html/2509.00132v1
- CSyMR: arxiv.org/pdf/2601.11556
- music-copilot: github.com/TommyX12/music-copilot
- LangGraph+music21: github.com/NirDiamant/GenAI_Agents (music_compositor_agent_langgraph)
- ISMIR2025: ismir2025program.ismir.net/poster_32.html
