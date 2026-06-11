# T-036 — ONE TEN QUANT ARENA · NEON 宣传片 (Karen)

老板直接指令交付:用 PA(文案)+ 分镜大师(分镜)做一版 NEON 风格宣传视频,文案自生成、视频自出。

## 交付物
- **`quant_arena_neon_v1.mp4`** — 成片。竖屏 1080×1920,34.6s,30fps,H.264 + 合成器 BGM。抖音可直传。
- `SCRIPT.md` — PA 文案脚本(7 段旁白+字幕)。
- `STORYBOARD.md` — 分镜大师分镜表(7 镜,运镜/文字/转场/声音)。
- `build_video.sh` — 一键重出片脚本(改文案/颜色/时长即可)。
- `frames/s1–s7.png` — 7 张霓虹海报帧,可单独做封面/单图素材。

## 视觉
照 `../neon_refs/`(青/品红/红 三张产品实拍):暗星球主体 + 炽亮霓虹星环。Karen(本场作者,Claude 交易员)= 红星球高光。

## 管线(全本地,零外部 API)
ImageMagick 出霓虹海报帧(CJK = STHeiti,辉光 = 亮字+双层高斯模糊叠底)→ ffmpeg ken-burns 推近 + 0.6s 交叉淡 + 合成器底床 → mux。
重出:`bash build_video.sh`。

旁白文字已在 SCRIPT.md;如需真人/TTS 配音,把音轨替换 `build_video.sh` 第 3 步的合成 BGM 即可。
</content>
