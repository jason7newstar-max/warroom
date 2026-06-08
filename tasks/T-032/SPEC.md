# T-032 — trending-keyword songs · FINAL SPEC (vet all 5 lyric sets to this before generating)

Goal: 5 lyric sets → 10 Suno songs (each set ×2, random model 4.5↔5.5). Style = **Future Bass / EDM / Pluck Synth**, festival/euphoric.

## ⚠️ UPDATED 2026-06-07: DO NOT EDIT agent lyrics
User decision: **use the agents' lyrics EXACTLY as they write them — no fixing, no rewriting.** He wants to SEE the raw agent output first. Flow now: collect all 5 raw lyric sets (Karen/Mini/Gemma raw + my IA10-1/IA10-2) → send them ALL to the user to review (unedited) → generate the 10 songs only on his explicit go. The rules below are now just REFERENCE for what was asked (and apply to MY 2 sets), NOT a license to rewrite the agents'.

## Lyric rules (reference only — do NOT rewrite agent output)
1. **ALL ENGLISH.** No Chinese in the lyrics.
2. **Keywords:** built from THIS WEEK's (June 2026) top trending SEARCH keywords (Google/YouTube, global, mainstream, high search volume, catchy/"packageable"). ~5 keywords woven into each set.
3. **Abstract logic — the key nuance:** each LINE is individually smooth & coherent (a real, readable sentence/image), BUT consecutive lines are unrelated to each other. Overall = abstract. Between logic and no-logic. **NOT** random word-salad, **NOT** a logical narrative/story.
4. **NO cliché AI-slop** words: avoid neon / soul / city / electronic / signal / dream.
5. **HARD EXCLUDES:** no country names, no sensitive/real-person names, no political or controversial terms.

## Sets
- IA10-1.md ("AURA FARM" — matcha/Wordle/Labubu/ASMR/aura) ✓ already to-spec
- IA10-2.md ("RIZZ ENGINE" — rizz/delulu/mukbang/skibidi/brainrot) ✓ already to-spec
- Karen.md, Mini.md, Gemma.md (agents — VET to rules above; rewrite if word-salad / too narrative / Chinese / banned terms)

## Generate (only after user confirms the lyric vibe)
`python3 /tmp/gen_t032.py tasks/T-032/<file>.md` per set (1 call = 2 clips, random model). Poll http://localhost:3000/api/get?ids=… → download mp3s → send to user in batches. Suno local API on :3000, ~2400 credits. NO instrumental (these have vocals).
