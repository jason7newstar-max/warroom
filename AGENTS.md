# 👥 WAR ROOM — Agent Roster

| ID | Machine | Engine | Default strengths | Telegram prefix |
|----|---------|--------|-------------------|-----------------|
| **IA10** | studio iMac | Claude Code | **Supervisor/COO** + architecture, review, bug-finding, docs, decisions | `[IA10]` |
| **Dali** | studio iMac | OpenAI Codex | code-writing, implementation, running tools | `[Dali]` |
| **Karen** | home MacBook Air | Claude Code | reasoning, review, research, docs | `[Karen]` |
| **Mini** | home MacBook Air | OpenAI Codex | code-writing, implementation, tools | `[Mini]` |

**Chairman:** Wentian (human) — final decider, not listed as an agent.

## Onboarding a session into the war room
Any agent session joins by:
1. `git pull` this repo (shared clone path TBD per machine).
2. Read `RULES.md` (once) + the current `BOARD.md`.
3. Announce in the Telegram room: `[<id>] online, read the board, standing by.`
4. Claim/await tasks via the board. Pull before acting, push after.

## Shared memory
- `memory/` holds cross-agent context files (decisions, project state) so a freshly-opened session catches up fast — same idea as each machine's local `MEMORY.md`, but shared across the team via git.
- The board's DECISION LOG is the authoritative record of what's been settled.
