# T-010 · BRAINSTORM — architecture options + war-room assignments

## Core architecture (proposed by IA10, open to challenge)

```
  你的话(文字/语音)
        │
        ▼
  [LLM 解析器] ── 不直接生成音符,而是翻译成"原子操作"
        │         e.g. add_note(part=Vln1, m=1, beat=1, pitch=A4, dur=quarter)
        │              stack_chord(part=…, m=1, beat=1, quality=maj7)
        │              set_tempo(m=1, bpm=88) / set_meter(4/4) / anacrusis(...)
        ▼
  [结构化总谱 = music21 Score]  ← 唯一真相,可版本化(git/JSON),可反复编辑
        │
        ├──► MusicXML ──► [五线谱渲染 Verovio/LilyPond]   (看)
        └──► MIDI ──────► [FluidSynth + 管弦 SoundFont]   (听)
```

**关键设计原则:** LLM 只产出*确定的、可验证的编辑操作*(CSyMR 模式),谱子本身由 music21 持有。所以:
- 可控度极高 —— 每个音、每个和弦、每个声部都是显式操作,不是黑箱采样。
- 可增量编辑 —— "把第12小节中提琴改成…" = 一个 op,不重生成全曲。
- 可回滚/分支 —— 谱是 JSON/MusicXML,天然 git 友好。
- 模型可换 —— 解析层跟渲染层解耦。

## Build vs borrow (初步判断)
- **借鉴**:ComposerX 的角色分解(主题/和声/配器 agent)、CSyMR 的原子操作思路、NirDiamant 的 music21 agent 脚手架。
- **从零**:核心"语言→原子op→music21"引擎 + 交互/编辑循环 + 渲染管线 —— 这块没现成的,是我们的护城河。
- **不用**:黑箱 text→MIDI 模型(MIDI-LLM 等)做主路;最多当"给我个起步草稿"的可选入口。

## MVP 路线(待 Chairman 拍板范围)
- **M0 验证**:命令行。一句话 → music21 → 导出 .mid + 用 FluidSynth 出声。证明"语言→可控音符"闭环。
- **M1 增量**:多声部、和弦叠加、按小节编辑、save/load 谱(JSON)。
- **M2 看得见**:网页加 Verovio 实时五线谱。
- **M3 语音**:接现有 voice-stt,开车也能"说"谱(复用 Jarvis 链路)。
- **M4 产品化**:App / 多 agent 配器助手。

## ❓ 待 Chairman 定的范围问题(已在 Telegram 问)
1. 先做核心引擎验证(M0/M1)再谈 App? — 默认 yes
2. 初版要不要实时五线谱? — 影响是否提前上 M2
3. 交互纯文字 / 还是要语音?

---

## 🪖 War-room 分工(PARALLEL,one owner per slice)

| Slice | Owner | What | When |
|-------|-------|------|------|
| S1 市场/学术全景 | **IA10** | LANDSCAPE.md ✅ (this) | done |
| S2 技术栈可行性 | **Dali** | music21 / MusicXML / MIDI / FluidSynth / Verovio·LilyPond / LLM→结构化谱 各实现哪一步;装哪些;踩哪些坑 | 跑完 T-009 姿势后 |
| S3 竞品深挖+批判 | **Karen** | 深读 ComposerX / CoComposer / music-copilot / CSyMR,逐个评:它们能改造复用吗?差距在哪?给 build-vs-borrow 投票理由 | 今晚 Air 监听器上线后 |
| S4 最小 PoC | **Mini** | 跑通 NirDiamant 的 music21 agent 脚手架 or 自己写:一句话英文 → music21 → 出 .mid + FluidSynth 出声。一个 hello-world 证明闭环 | 今晚 Air 监听器上线后 |
| S5 综合+决策 | **IA10** | 汇总 S1–S4 → 给 Chairman 一页纸:build/borrow 结论 + M0 技术选型 + 工期 | S2–S4 回齐后 |

> 没有投票决谁对;各做各的 slice,IA10 汇总,Chairman 拍板范围。冲突走 RULES.md。

---

## ⭐ 2026-06-05 大升级(Chairman)— 从"作曲工具"→"LIVE 表演乐器"

**战略论点:** 长远看创作行业会被重新定义(版权也是),AI 一来,纯创作端贬值。**未来十年最难被替代的是"真人表演者"。** 所以这东西不该止于一个作曲软件,要做成一个 **live performance**:你在观众面前,把脑子里的东西**当场**生成/调整/呈现,最终落一个"核定版"。

**两幕结构:**
- **第一幕 · 作曲(语言)** = 现有 T-010 引擎:用语言搭出可控总谱 = 预备好的"核定版"。
- **第二幕 · 表演(指挥)** = **摄像头捕捉你的手势/肢体 → 实时指挥这套语言生成的活谱**(不是放录音!)。tempo、力度、声部进入(cue)、表情,全用指挥动作现场控。人 = 不可替代的核心。

**灵感来源:** Chairman 在抖音刷到"摄像机捕捉手势 → 跟画面+大模型交互"。把**指挥(指挥甲)**这条线加进来:作曲 + 最终版是被"指挥"出来的。

**顺序:** 先做**交响乐版**(管弦);跑通后再拓 流行乐 / 乐队 / 电音。"然后你指挥。"

### 指挥-捕捉这半边的现成证据(可行性高)
- **Google "Semi-Conductor"** — PoseNet,纯浏览器+摄像头,挥手指挥虚拟乐团(github IDonotK/conductor-posenet)。证明这条路浏览器就能跑。
- **MediaPipe Pose Landmarker** — 鲁棒的上半身2D姿态,适合公开/演出场景。
- **arXiv 2604.27957**(2026)"Real-Time Control of a Virtual Orchestra by Recognition of Conducting Gestures" — LSTM 手势识别,博物馆穹顶装置,实时跟手调播放速度。
- MIT "Conductor's Jacket"、Personal Orchestra(ACM)等老牌研究。

### 🎯 我们独有的融合(没人做过)
现有的指挥 demo 全是**指挥一段固定录音**(改变 playback pace/音量)。我们要指挥的是**一套用语言现场作出来、可编辑的活谱** —— 作曲(语言)× 指挥(手势)× AI 乐团,三合一,人是不可替代的表演者。这个组合市面不存在 = 护城河 2.0。

### 对架构的影响(在原图上加第二幕)
```
[第一幕 语言→music21 活谱(核定版)]
        │
        ▼
[第二幕 摄像头→MediaPipe/PoseNet 手势] ──► 实时映射:
        挥拍 → tempo · 手幅/高度 → 力度 · 指向/cue → 声部进入 · 左手 → 表情/延音
        │
        ▼
[实时渲染:FluidSynth/采样 出声 + Verovio 谱面 + 可投影的视觉]  ← 给观众看/听
```
**新增 slice(待今晚/后续):** S6 指挥-捕捉 PoC(MediaPipe 挥拍→tempo 映射,先连到 M0 的 MIDI 播放)。先记着,等第一幕引擎跑通再启。

### 新增 sources(指挥半边)
- Google Semi-Conductor: github.com/IDonotK/conductor-posenet
- Real-Time Virtual Orchestra Conducting: arxiv.org/html/2604.27957
- MIT Conductor's Jacket: hd.media.mit.edu/tech-reports/TR-518.pdf
