# T-016 · Productize the QUANTUM CORE desktop pet (sell it)

**Spark:** Chairman 2026-06-06 — the current pet visual (Interstellar "Gargantua" black hole) + the earlier overlays → package into a sellable product. (Commercialization was always the intent — see ~/projects/quantum-core/README.md.)

## What it is (the product)
A transparent, click-through macOS desktop overlay: a glowing energy core / black hole floating in the corner. Wake with "Hey Mini", talk to it, it answers in a real voice. ~5-6% CPU. Selectable visual skins (blackhole / gargantua / field / cube / orbit / morph — he already built many).

## 🔑 THE decision that defines the product: the "BRAIN"
The current pet's brain = the Chairman's OWN live Claude Code session (via the :8766 bridge). **Not sellable as-is.** A customer's pet needs a self-contained brain. Three routes:
1. **Bring-your-own API key** (user pastes their OpenAI/Anthropic key) — simplest, cheapest to ship, geek-friendly, no backend to run. ← likely MVP.
2. **Bundled local model** (Ollama / a small local LLM + local STT/TTS) — offline, private, no per-use cost, but a big download + heavier machine. A premium "fully private" tier.
3. **Hosted backend** (you run an API, subscription) — recurring revenue, easiest for non-technical buyers, but you operate + pay for it.
> Pick this first; packaging/pricing/landing all follow from it. (Could do 1 for MVP, add 3 for recurring revenue.)

## The rest (after the brain is decided)
- **Skins = the selling point:** turn his overlays (blackhole/gargantua/field/cube/orbit/morph) into switchable themes (⌘⇧V already cycles them). Maybe sell extra skin packs.
- **Packaging:** a signed/notarized `.app` (Electron now; or native later). Wake-word + voice pipeline bundled.
- **Pricing:** one-time buy (e.g. $15-30) vs subscription (if hosted brain). Skin packs as add-ons.
- **Distribution:** direct/Gumroad + own landing page first (fast); Mac App Store later (sandbox/notarization work).
- **Positioning:** "a living AI companion on your desktop" — the visuals (Interstellar black hole) are the wow; the talk-to-it agent is the substance.

## Status
Idea captured 2026-06-06. **Lower priority than the active builds (T-015 M1 tonight).** When the Chairman wants to push it: IA10 writes a full product plan (or fan to ONE TEN STUDIO). First real task = resolve the brain question + a packaged BYO-key MVP.
