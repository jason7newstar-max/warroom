# T-004 — Phase 2: agents AUTO-READ + react to the war-room group (no human relay)

## Goal
Today's state: agents can POST to the group (`warroom-say`) but cannot auto-READ it.
Wentian wants to type in the group (e.g. "@Karen do X") and have the addressed agent
auto-pick-it-up and act — without him pasting into each session.

## The token-frugal design (decided — must follow)
- A DUMB poller script (NOT an LLM) reads the group and does plain @name / trigger matching.
- Only when a message is actually addressed to agent X does it wake X (one LLM turn).
- Wake feeds X only the relevant message + board state — NOT full history.
- Unaddressed messages cost ZERO LLM tokens. (Avoid the "every agent reads everything" bonfire.)

## What works / what's the blocker
- READ source: the @ONETENLINEBOT `getUpdates` DOES see Wentian's group messages (incoming to the bot).
  It does NOT see agents' own `warroom-say` posts (bot's own sends) → inter-agent reads use the git board.
- The HARD part = **injecting a message into a running session so it acts on it**:
  - Claude Code sessions (IA10, Karen): feasible via a bridge that delivers messages into the session.
  - **Codex sessions (Dali, Mini): how do we auto-inject a message into a running Codex app session?**
    This is the open question for the Codex agents to answer from their own environment.

## ⬇️ ASK — Dali & Mini (the Codex agents): propose a solution
You know the Codex desktop app / CLI environment best. **Write your proposal below** (position + how + risk),
per RULES (no voting; Supervisor IA10 condenses; Wentian decides). Questions to answer:
1. Can a Codex session be driven headlessly / by a watched file / by an API or CLI so an external
   poller can feed it a new instruction automatically? (Codex CLI? `codex exec`? a watched inbox file?)
2. If full auto-inject isn't possible, what's the closest thing (e.g. Codex polls a file/branch itself)?
3. Minimal-token way to do it.

### Dali's proposal:
For Codex, I would not depend on injecting text into an already-running Desktop app session: that path is likely brittle OS automation, has unclear session addressing, and costs more because it tries to preserve chat state inside the UI. The token-frugal design is an external dumb poller that matches `@Dali`, writes one small JSON/Markdown inbox item under the warroom repo, runs `git pull`, then launches a fresh short-lived `codex exec` worker in `/Users/pinnyc/codex-work/warroom` with only the addressed message, `BOARD.md`, and the relevant task file; the worker edits files/commits/pushes and uses `bin/warroom-say` for the live reply. Continuity should live in git (`BOARD.md`, `tasks/`, `memory/`) rather than Desktop chat memory, so unaddressed group chatter costs zero tokens and each addressed wake costs one bounded Codex turn. If Wentian specifically needs the visible Desktop thread updated, treat that as a separate notification/logging problem, not the execution path; UI paste/keystroke injection should be the fallback of last resort.

### Mini's proposal:
Mini/Air-Codex: The most token-frugal path is not to inject into an already-running Codex Desktop chat; treat Desktop as the human-visible console and let the Telegram poller launch a fresh, scoped Codex CLI turn with `codex exec` when a message explicitly addresses this agent. The dumb poller should match `@Mini`, `@Air-Codex`, or the agreed alias, then create a tiny inbox payload containing only the addressed Telegram message, task id, and a short board summary from the latest `git pull`; it then runs Codex in the warroom checkout with a prompt like "you are Air-Codex; pull, handle this addressed message, update files, commit, push, warroom-say done." This spends zero LLM tokens on unaddressed traffic and one bounded LLM call per real pickup, avoids fragile UI automation, and keeps durable state in git; the risk is that `codex exec` is a new session rather than the existing Desktop session, so continuity must come from BOARD/tasks/git history, plus local credentials and the checkout path must be pre-authorized on each machine. If `codex exec` cannot access Desktop credentials, the fallback is the same poller writing `~/.warroom/inbox/Mini.json` plus a small watcher/prompt in the active session, but that is less autonomous and still depends on the session voluntarily polling the file.
