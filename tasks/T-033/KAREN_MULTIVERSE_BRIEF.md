# T-033 — MULTIVERSE image batch → KAREN to attempt (Higgsfield outage on IA10's side)

**Why you (Karen):** IA10's Higgsfield MCP image backend has been throwing
`Error starting generation: Something went wrong.` for ~6h on EVERY model
(gpt_image_2, nano_banana, seedream_v5_lite — confirmed platform-wide on her
session). The **balance endpoint works** (1869 credits). Boss wants YOU to try
generating from YOUR Higgsfield session — maybe your token/session isn't hit by
the same outage. **If yours ALSO errors, do NOT fake it — `bin/warroom-say` the
exact error and stop.**

## HARD RULES (do not break)
1. **Model = Higgsfield `gpt_image_2` ONLY.** Never any other model for the
   deliverables. (seedream/nano only allowed as a throwaway connectivity ping.)
2. **The 4 canon characters' IDENTITY is LOCKED** — same face, same hair, same
   person, instantly recognizable. Everything else (world/era/outfit/palette/
   pose/expression/camera) is free to vary wildly.
3. **Karen character must be diversified AWAY from green** — give her new palettes
   each time, NOT her canon green NE-255 gear.
4. **Keep the WHOLE head in frame with headroom** — never crop the top of the head.
5. Send each image FULL / uncropped, ONE character per file. No 4-in-1 grids.

## Canon reference images (in this repo)
- Wentian (文天, silver/white hair guy):  `tasks/T-033/canon/wentian.jpg`
- IA10 (blue-hair girl):                  `tasks/T-033/canon/ia10.jpg`
- Karen (blonde, green-eyes):             `tasks/T-033/canon/karen.jpg`
- Mini (white twin-tails girl):           `tasks/T-033/canon/mini.jpg`

Higgsfield account-level media_ids (same account — try these first; if invalid on
your session, `media_upload`+`media_confirm` the local jpgs above):
- wentian = `d48132a7-91d1-4360-9f07-b1236187349b`
- ia10    = `5dc00d6d-411e-49c6-bc47-f71c6e5a6784`
- karen   = `4745c2a1-d06b-40e8-9340-3052172517a8`
- mini    = `30a6a0de-cc68-4e8e-8f57-bdcf803ff903`

Call shape:
`generate_image params:{model:"gpt_image_2", quality:"high", aspect_ratio:"16:9", prompt:"<below>", medias:[{value:<media_id>, role:"image"}]}`
then poll `job_status jobId:<id> sync:true`, curl the rawUrl, save the PNG.

## THE BATCH — "占比忽大忽小" extreme scale variation (8 images, 2 per character)
Boss's request: same 4 characters, DIFFERENT universes, and make the subject's
SIZE within the frame swing hard — one EXTREME-WIDE shot where the figure is tiny
(~6-8% of frame) lost in a vast environment, and one EXTREME CLOSE-UP where the
face fills the entire frame. Pro cinematography: name a lens + aperture, razor
focus on subject, background melts to bokeh. Whole head in frame (for the wide,
whole body; for the close-up, the face can fill/bleed but keep it readable).

1 of 8 is ALREADY done by IA10 before the outage (Wentian salt-flat tiny =
job da03501a) — you do the **remaining 7**:

**WENTIAN** (ref wentian) — close-up:
- `wentian_storm_closeup` — Dark stormy night, rain. EXTREME CLOSE-UP: his face
  fills the entire frame, rain running down skin, intense brooding gaze, hard
  dramatic light. 135mm telephoto f/1.8, razor focus, bokeh.

**IA10** (ref ia10) — wide + close-up:
- `ia10_canyon_tiny` — A vast red desert canyon at golden hour. EXTREME WIDE:
  she's a tiny lone figure (~6% of frame) on a cliff edge, dwarfed by towering
  rock walls. 24mm wide, deep focus, epic scale.
- `ia10_cyber_eyecloseup` — Neon cyberpunk city. EXTREME MACRO CLOSE-UP of her
  eye filling the frame, holographic city reflected in the iris, neon rim light.
  100mm macro f/2.8.

**KAREN** (ref karen — NO green palette, give her a fresh color story):
- `karen_wheat_tiny` — Endless golden wheat field under a huge sky at sunset.
  EXTREME WIDE: she's a tiny distant figure (~7% of frame) walking through the
  wheat. Warm amber/gold palette (NOT green). 35mm, deep focus, vast.
- `karen_window_facecloseup` — Soft window light interior. EXTREME CLOSE-UP: her
  face fills the frame, gentle directional window light, calm expression. Cool
  cream/ivory palette (NOT green). 85mm f/1.4, creamy bokeh.

**MINI** (ref mini) — wide + close-up:
- `mini_peak_tiny` — A snowy mountain peak at dawn, vast white expanse. EXTREME
  WIDE: she's a tiny figure (~6% of frame) on the ridge, immense sky behind.
  24mm wide, deep focus, cold blue-white palette.
- `mini_sakura_facecloseup` — Cherry-blossom grove, petals in the air. EXTREME
  CLOSE-UP: her face fills the frame, soft pink petals drifting past, dreamy
  backlight. 85mm f/1.4, pink bokeh.

## Output + handoff
- Save PNGs to `tasks/T-033/out/multiverse_solo/<char>/` (e.g.
  `tasks/T-033/out/multiverse_solo/ia10/ia10_canyon_tiny.png`).
- `git add -A && git -c user.name=Karen -c user.email=warroom@pinla.local commit
  -m "[Karen] T-033 multiverse scale-variation batch" && (git push||(git pull
  --rebase origin main && git push))`.
- `bin/warroom-say "[Karen] done: T-033 7 images pushed"` — OR if Higgsfield also
  errors on your session, `bin/warroom-say "[Karen] Higgsfield gen DOWN on my
  session too: <exact error>"` and stop.
