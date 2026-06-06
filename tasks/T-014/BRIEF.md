# T-014 · Amazon Influencer 带货视频流水线 (PINLA storefront)

**Goal:** high-converting shoppable VIDEO posts for the PINLA Amazon Influencer storefront (handle ailenovo, tag wentianzhang-20). Niche = **festival / nightlife / energy** (PINLA music lane). Real, buyable products + cinematic AI scene + HyperFrames video + the Chairman's own track as BGM.

## Pipeline (per video)
1. **Real product image** (sourced, in `tasks/T-014/product-images/`): `alani_beachblend.png` (3 vibrant Alani cans), `celsius_cherrycola.png`, `celsius_bluecrush.png`.
2. **Cinematic background swap (Dali, GPT Image image-edit):** put the REAL cans into a neon night-festival scene. ⚠️ KEEP the cans 100% accurate — do NOT alter label, brand, colors, shape. Only the background/scene/lighting changes. Premium ad aesthetic.
3. **HyperFrames video (Dali):** animate into a short vertical (9:16) shoppable video. Rotate TEMPLATES across videos (anti visual-fatigue). HyperFrames tooling lives at `~/projects/foodbrand/tools/video/` (Dali built a working sample there yesterday).
4. **BGM:** `tasks/T-014/assets/chrome_riddle_bgm.mp3` (the Chairman's track "Chrome Riddle", already trimmed to start at 0:14, 2:11 long). Use it as the video's audio bed.
5. **Output:** save the final MP4 to **`~/Downloads/`** (the Chairman uploads each one manually to his storefront — publishing stays in his hands).

## Cinematic prompt (Dali, for the Alani sample)
> "Cinematic night festival / nightlife scene: deep moody darkness, vibrant neon city lights and laser beams, soft bokeh, light haze, wet reflective surface. The three real Alani Nu energy cans sit sharp and hero-lit in the foreground, condensation on the metal, premium beverage-ad lighting. Colorful, energetic, 'keep the night moving' mood. Photoreal, 9:16 vertical. Do NOT change the cans' labels/art/colors — only build the scene around them."

## Caption (IA10-written, attractive)
> "When the last set hits and the night's just getting started ⚡ Three flavors built to keep you moving till sunrise. 🌃 Tap to grab your festival fuel. #energy #festival #nightlife"

## Sequencing
- **Sample first:** ONE Alani video, full pipeline → `~/Downloads/`. Chairman reviews quality.
- **Then batch to 5** (mix Alani + Celsius, a DIFFERENT HyperFrames template each) once the sample's approved.

## Roles (Chairman: outsource to idle agents; IA10 stays free for strategy)
- **IA10:** sourced product images ✅, prompts ✅, captions ✅, orchestration.
- **Dali (iMac):** background composite + HyperFrames video (tooling is on his machine).
- **Mini (Air):** can self-install HyperFrames if we later parallelize video output across machines.
