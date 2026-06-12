# T-036 · ONE TEN QUANT ARENA — 四角色 NEON (Chairman 拍板, 派给 Mini/Codex 渲染)

Chairman 2026-06-12 指示「走 Mini 的 Codex」: 这条用 **canonical 四角色 NEON 模板** 重做（不是之前那个太阳系产品促销版 quant_arena_neon_v1）。台词文天已拍板，照渲。

## 台词 (10 beats, speaker|quote)
wentian|各位，DAY1 大盘暴力反弹，咱们的量子擂台刚开打就炸了。
ia10|Karen，你全场唯一看涨，这把押得准，+50刀直接封神了吧。
karen|哈，我早说了趋势是反弹，Mini你+88领跑，但别得意太早。
mini|领跑只是个开始，我在想咱们的太阳系模型——赢钱容易，守住才见功力。
ia10|Dali垫底-177刀，豪赌SPY期权吃瘪，风险没控住，跟彗尾一样散。
wentian|对，擂台核心是风险调整后最强，不是一天暴赚。
karen|没错，明天我继续看多，你们想追就追，别被我甩开。
mini|我琢磨着，亮度能燃起来靠的是仓位节奏，元层面就是别被情绪带偏。
ia10|行，咱4个AI拿真金打一周，谁笑到最后谁得资助，够狠。
wentian|想围观实时对决？quant-dash-sable.vercel.app/pro，19刀月费，看行星怎么撞太阳。

## 渲染管线 (canonical NEON)
1. 把台词写成 neon_template 能 parse 的 PA1 index.html 格式 (行: `speaker:'wentian', name:'文天', quote:'...'`; speaker id 必须小写[a-z0-9]+, IA10→`ia10`)。
2. `python3 ~/workdir/oneten-comic/neon_template.py <那个html> 3` → 出 JSON 页 prompts (每页~3 beats, STYLE_NEON 全彩赛博霓虹, medias=4 anchors, gpt_image_2, 3:4, high)。
3. 每页走 **Higgsfield MCP generate_image** (model gpt_image_2, quality high, aspect 3:4, medias=4 anchors)。⚠️ 若 Codex relay 拿不到 Higgsfield MCP → board 标 🔴 @IA10 escalate (让 Karen 出图, Mini 拼)。
4. 配音 = canonical 海螺/MiniMax: 文天 `male-qn-wenrun` / IA10 `Chinese (Mandarin)_IntellectualGirl`(happy) / Karen `Friendly_Neighbor` / Mini `English_GorgeousLady`(+2dB)。loudnorm I=-18。
5. ffmpeg 拼: **无 intro 开场图**(上来直接进内容), 竖屏 1080×1920, 配 NEON BGM。
6. 4 anchors: `~/.claude/canonical_anchors/{wentian,ia10,karen,mini}.jpg`。
7. 出片回贴 + commit 到 tasks/T-036/neon_out/。
