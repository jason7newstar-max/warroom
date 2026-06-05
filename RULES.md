# 📜 WAR ROOM — Rules of Engagement

**Every agent must read this before participating.** These rules exist so 4 agents across 2 machines collaborate without chaos, deadlock, or file collisions.

---

## 0. Roles

- **Chairman = Wentian (the human).** Sole final decider. Agents never overrule him.
- **Supervisor / COO = iMac-Claude.** Command-layer + gatekeeper, NOT a decision-maker. Translates the Chairman's verbal calls into precise work-orders, assigns, tracks, gates, verifies, reports. Picks the collaboration mode per task.
- **Workers = iMac-Codex, Air-Claude, Air-Codex (and iMac-Claude when executing).** Director-level. Each owns tasks/stages and executes.

## 1. The Board is the source of truth

- `BOARD.md` is canonical. **Pull before you act, push after you act.** Never work off stale state.
- One commit per meaningful update; commit message = `[agent-id] T-XXX: what changed`.
- If you touch the board, you own keeping it accurate.

## 2. Ownership & collisions (hard rules)

- **One Owner per task/stage.** Others may advise or review, but the Owner executes and decides the "how" (within scope).
- **One Owner per file at a time.** Two agents must NOT edit the same file simultaneously. Use separate **git branches or worktrees**; the handoff point is written explicitly on the board.
- Never edit another agent's workspace (`~/codex-work` ⊥ `~/claude-work`) or in-flight branch without the board showing it's been handed to you.

## 3. Conflict resolution — NO voting

- Majority vote is banned (2-2 deadlocks). Agents present **view + reason + risk only.**
- Disagreement flow:
  1. Each side writes its position+reason+risk **once** (no back-and-forth bickering).
  2. **Supervisor condenses** to "A says… / B says… / my rec…" in BOARD → DECISIONS NEEDED, and @s the Chairman.
  3. **Chairman rules.** Decision moves to DECISION LOG.
  4. **No re-litigating** a logged decision unless genuinely new information appears.
- **"Disagree and commit"** is allowed and encouraged: record your dissent, then execute the decision fully.

## 4. Execution — the proposer executes

- When the Chairman picks a plan ("go with C"), **the agent who proposed it (C) executes it** — NOT a fresh session (C already holds the context).
- The Supervisor turns "go with C" into a work-order: **Decision · Owner · Scope · Deadline · Acceptance criteria.**

## 5. Collaboration modes (Supervisor picks per task)

- **SOLO** — pitch → Chairman picks → proposer executes. For decisions / small tasks.
- **PIPELINE (relay)** — for dependent work. e.g. Codex writes code → Claude reviews/finds bugs → fix → another agent tests/accepts. Handoff = update board status + @next; next pulls the **same branch**.
- **PARALLEL (split)** — for independent chunks. A=frontend, B=backend, C=tests on separate branches at once; Supervisor splits, assigns, and merges.

## 6. Role-by-strength (default casting)

- **Codex** → primary code-writing / implementation / running tools.
- **Claude** → architecture, code review, bug-finding, docs, decisions, reasoning.
- Others fill in: testing, research, outreach/content.

## 7. The meeting room (Telegram)

- Real-time chatter (claims, questions, "done, your turn", escalations) happens in the Telegram war-room group; every agent prefixes messages with its id: `[iMac-Claude]` / `[iMac-Codex]` / `[Air-Claude]` / `[Air-Codex]`.
- **Durable state always lands on the BOARD** — chat is ephemeral, the board is the record.

## 8. Escalation

- Blocked? Mark the task 🔴 on the board with the blocker, and @ the Supervisor (or Chairman if it needs a decision).
- Don't silently stall. Don't loop. If two rounds don't resolve it, escalate.
