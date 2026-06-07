# T-028 · Plugin hosting + PinLA Studio own plugins (extends T-015 AI recording studio)

Spark: Chairman 2026-06-06 — after recording, how do we plug mixing/reverb plugins into our system? Can we be compatible with existing third-party plugins? And release PinLA-branded plugins (Compressor, Reverb…)?

## 1. Hosting existing plugins — SOLVED, you already have the tool
- **Pedalboard** (Spotify's Python lib) — already used for Kontakt/MAESTRO ([[project_maestro]]). It **loads any VST3 / AU plugin** (`pedalboard.load_plugin()`) and runs audio through it. So: recorded take → Pedalboard chain (Compressor → Reverb → EQ) using ANY existing third-party plugin (FabFilter, Waves, Logic's stock, etc.). Fits the T-015 Python pipeline directly — no new infra.
- **No "emulation" needed.** VST3 + AU ARE the universal standards. Support those two and every existing plugin just works (AU = Logic-native, since Chairman is on Logic). JUCE is the alternative host if we ever go C++/native.

## 2. Building PinLA Studio's OWN plugins
- Build in **JUCE** (industry-standard C++ framework): one codebase → exports **VST3 + AU + AAX + standalone**, works in every DAW.
- Compressor + Reverb = well-understood DSP; JUCE ships `juce::dsp::Compressor` + reverb algorithms to start from. Brand the UI as PinLA Studio.
- Distribute on own site / Gumroad / plugin marketplaces.

## 3. ⚠️ Honest strategic note — the differentiator
The plugin market is SATURATED (FabFilter, Waves, etc.). A generic PinLA compressor/reverb won't stand out on merit alone. **Lead with the AI / self-driving angle** — the unmanned-studio philosophy as a plugin: a compressor/reverb that **sets itself** (analyzes the source, dials its own settings). "PinLA AUTO" line. That's novel, on-brand, and ties the whole [[project_ai_recording_studio]] thesis into a sellable product.

## Phasing
- **P1 (this week, fits T-015):** host existing plugins via Pedalboard — recorded take auto-runs through a configurable Compressor→Reverb→EQ chain.
- **P2 (bigger, later):** first PinLA-branded JUCE plugin — and make it the AI auto-set one, not a me-too.
