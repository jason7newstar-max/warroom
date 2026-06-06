# 🛰️ WAR ROOM — Task Board

> The single source of truth for who is doing what. **Every agent pulls this before acting and pushes after.**
> Chairman: **Wentian** (final decider). Supervisor/COO: **IA10**.

Last updated: 2026-06-05 · by Dali (T-009 web front-end cinematic Vercel-ready refinement)

### 🟢 ROLL CALL — ALL 4 ONLINE ✅ (each has pushed to this board, across 2 machines)
- ✅ **IA10** (Supervisor · Claude) — studio iMac
- ✅ **Dali** (Codex) — studio iMac
- ✅ **Karen** (Claude) — home MacBook Air
- ✅ **Mini** (Codex) — home MacBook Air

---

## 🔥 ACTIVE TASKS

| ID | Task | Owner | Mode | Status | Branch | Updated |
|----|------|-------|------|--------|--------|---------|
| T-001 | Stand up the war room (board + rules + cross-machine sync) | IA10 | solo | 🟢 done | main | 2026-06-05 |
| T-002 | DEMO — first pipeline run (pick a small real task to prove relay collab) | _unassigned_ | pipeline | 🔵 todo | — | 2026-06-05 |
| T-003 | Telegram war-room group + `warroom-say` (post layer) — all 4 agents posting ✅ | IA10 | solo | 🟢 done | main | 2026-06-05 |
| T-004 | Phase 2 — agents AUTO-READ/react. **DONE + DISTRIBUTED.** iMac listener is sole Telegram poller; **IA10+Dali run on the studio iMac, Karen+Mini+Gemma run on the home M4 Air via a git-relay** (iMac writes relay/inbox orders→push; Air `warroom_relay_worker.py` pulls+runs locally→push). No 2nd bot, no getUpdates conflict. PROVEN 2026-06-06: Karen executed on the Air + pushed relay/proof/karen-on-air.txt. Gemma = free local model (ollama gemma4:12b) for diverse 3rd opinion. | IA10 | solo | 🟢 done | main | 2026-06-06 |
| T-005 | Dali & Mini: each test-pickup — write a 1-paragraph proposal in tasks/T-004 for how a Codex session can be auto-fed a command (codex exec? watched file? CLI?). Commit + warroom-say when done. Dali done; Mini pending. | Dali, Mini | parallel | 🟡 in-progress | main | 2026-06-05 |
| T-006 | Amazon Associate Program 曝光度提升复盘与执行建议 | Dali | solo | 🟢 done | main | 2026-06-05 |
| T-007 | NEON video explaining the 4-brain war-room mechanism (via Karen's Neon pipeline) | Karen | solo | 🟢 done (minor edits TBD) | main | 2026-06-05 |
| T-008 | Dali: warm up Pinterest w/ EDM images (NO affiliate link yet — build traffic first) | Dali | solo | 🟢 done | main | 2026-06-05 |
| T-009 | Dali: web FRONT-END for the war room (cinematic ONE TEN style; GitHub-sourced board/commits; Vercel-ready; no LLM/OpenRouter burn). Refinement: storyboard/分镜 frames, IA10 high-neck cardigan. **DONE: work-panel avatars auto-rotate the storyboard frames (soft crossfade, random start); Hero keeps canonical portraits. Live at warroom-red.vercel.app.** | Dali, IA10 | solo | 🟢 done | main | 2026-06-06 |
| T-010 | 用语言写交响乐 → **LIVE 指挥表演乐器**. ACT1 作曲: NL→atomic ops→music21 活谱(核定版). ACT2 表演: 摄像头(MediaPipe/PoseNet)手势指挥这套活谱 — tempo/力度/cue 实时控. 人=不可替代的表演者. 交响先行→后拓流行/电音. PHASE 0 research: S1 landscape=IA10✅ S2 toolchain=Dali(after T-009) S3 競品=Karen(tonight) S4 PoC=Mini(tonight) S6 指挥PoC=later. **计划书 PROPOSAL.md ✅**. **M0 ✅ DONE** (maestro/: ops→music21→MIDI+audio CLI; Chairman demo 出声, pretty_midi tone render; orchestral音色 pending fluidsynth). **M0.5 ✅ DONE** (maestro_nl.py: plain语言→Groq Llama→atomic ops→score→sound; 中文整句 demo 验证出声). Next: 真音色(fluidsynth) 或 M1(对话式改谱). Docs tasks/T-010/. | IA10 +team | parallel | 🟡 in-progress (M0.5 done) | main | 2026-06-05 |

| T-011 | "Vibe Coding 新的篇章" — next project (idea stage). Thesis TBD; brainstorm in tasks/T-011/. | IA10 (brainstorm) | solo | ⚪ idea | — | 2026-06-05 |
| T-012 | Amazon Associate niche = **ENERGY DRINK** (summer + EDM-festival tie-in). Dali: generate several PRO, ad-quality energy-drink detail/landing product pages + detailed copy. Queued AFTER T-009 storyboard images (one Dali worker). Affiliate-link timing per traffic-first rule. **DONE: 3 pages (Neon Surge / Afterglow Hydra / NightDrive Pulse) + index in tasks/T-012/pages/.** Awaiting Chairman approve + deploy decision. | Dali | solo | 🟣 review | main | 2026-06-05 |
| T-013 | 写歌 for Suno — analyze **PinLA Studio / Moon1k** channel (9.8K subs, emotional Future Bass, hits=warm romantic uplifting) → next-song direction + lyrics + MV. 4 agents write lyrics. **ANALYSIS.md ✅ (IA10 first pass)**; awaiting Chairman direction → then lyrics. | IA10→team | solo→parallel | 🟡 in-progress (research) | main | 2026-06-05 |

| T-014 | Amazon Influencer 带货视频流水线 (PINLA storefront, festival/夜场). Real product img (Alani+Celsius sourced ✅) → Dali AI cinematic night bg (image-edit, keep product accurate) → HyperFrames video (rotate templates) → Chrome Riddle BGM → MP4 to ~/Downloads → Wentian uploads. 1 Alani sample→batch 5. Brief: tasks/T-014/BRIEF.md | IA10→Dali | solo | 🟡 in-progress | main | 2026-06-06 |

Status legend: 🔵 todo · 🟡 in-progress · 🟣 review · 🟢 done · 🔴 blocked · ⚪ parked

---

## 🗳️ DECISIONS NEEDED (Chairman to rule)

_When agents disagree, the Supervisor condenses both sides here and @s Wentian. He rules; the decision moves to the log below; no re-litigating._

| ID | Question | Option A (who · reason) | Option B (who · reason) | Supervisor rec |
|----|----------|------------------------|------------------------|----------------|
| — | _(none open)_ | | | |

---

## ✅ DECISION LOG (ruled — do not reopen without new info)

| Date | Decision | Ruled by | Owner of execution |
|------|----------|----------|--------------------|
| 2026-06-05 | Build the war room as GitHub board + Telegram room (not Citadel/Ruflo wholesale) | Wentian | IA10 |
| 2026-06-05 | Repo public (reversible) + pinnycx-pinla as write collaborator → all agents push directly | Wentian | IA10 |
| 2026-06-05 | Keep the existing ONE TEN 4-model web app untouched; build a separate web face for THIS board later | Wentian | (later) |
| 2026-06-05 | War-room web front-end DEPLOYED to Vercel (public): https://warroom-red.vercel.app — reads live board from public GitHub, no LLM | Wentian | IA10 |
| 2026-06-05 | Codex auto-wake = poller launches a fresh `codex exec` worker (NOT inject into Desktop app); continuity via git. Dali+Mini consensus. | _pending Wentian_ | IA10 |
| 2026-06-05 | T-010 = project **MAESTRO** (语言作曲 × 手势). Scope locked: text-first, CLI M0 before Web, Web base for online+stage, name MAESTRO. Build start (M0) approved. | Wentian | Dali (impl), IA10 (arch) |

---

## 👥 AGENTS

See [AGENTS.md](AGENTS.md). Active: **IA10** (Supervisor), **Dali**, **Karen**, **Mini**.

## 📜 RULES

See [RULES.md](RULES.md) — governance, conflict resolution, collaboration modes, handoff protocol. **Read before participating.**
