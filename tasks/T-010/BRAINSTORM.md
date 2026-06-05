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
