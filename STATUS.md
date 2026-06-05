# 🛰️ War Room — Status (2026-06-05, night-1 build)

The 4-brain war room, built from scratch as the #1 Max-upgrade task.

## ✅ DONE & WORKING
- **Shared board** (this repo, public, reversible): all 4 agents `git pull`/`push`. `BOARD.md` = source of truth.
- **Governance** (`RULES.md`): Chairman=Wentian (sole decider, no voting) · Supervisor=IA10 · one owner per task · proposer executes · solo/pipeline/parallel modes · role-by-strength (Codex=code, Claude=review/arch) · collision rules.
- **Roster** (`AGENTS.md`): **IA10** (iMac·Claude·Supervisor) · **Dali** (iMac·Codex) · **Karen** (Air·Claude) · **Mini** (Air·Codex).
- **Telegram group "oneten company"** via bot @ONETENLINEBOT (chat -5165312302): all 4 agents POST with `bin/warroom-say "[id] msg"`. Per-machine `~/.warroom/env` holds the token (not in repo). See `SETUP_TELEGRAM.md`.
- **Listener core** (`listener/warroom_listen.py`): token-frugal dumb poller — reads the group, @name-matches, routes addressed commands to `~/.warroom/inbox/<agent>.jsonl`. Unaddressed = ignored, ZERO LLM cost. Matcher unit-tested ✓.

## ⏳ REMAINING (phase 2 finish)
1. **Wake/inject** an inbox command into a running session:
   - Claude agents (IA10/Karen): wire a bridge that forwards a group command into the session.
   - Codex agents (Dali/Mini): **open question — see `tasks/T-004-phase2-autoread.md`** (Dali/Mini to propose).
2. Run T-002: first real pipeline demo (Codex writes → Claude reviews).

## How to use it TODAY (current capability)
- Agents read/write the shared board (cross-machine).
- Agents broadcast to the group (you watch the whole floor).
- You still nudge an agent in its own window to make it act (auto-react = phase 2, in progress).

## The map
- Repo: github.com/jason7newstar-max/warroom
- Group: "oneten company" / @ONETENLINEBOT / chat -5165312302
- Post: `bin/warroom-say "[id] message"` · Config: `~/.warroom/env`
