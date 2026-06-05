# T-009 — Dali: web front-end for the war room (reads the board, NO OpenRouter burn)

**Owner:** Dali (iMac · Codex)  ·  **From:** Wentian (via Supervisor IA10)

## Goal
A web "command center" page (ONE TEN style) that is the FACE of this war room.
It DISPLAYS the real state from this board — it does NOT call any LLM/OpenRouter
(that's what made the old 4-model ONE TEN web app burn money). The real work is done
by the 4 actual agents; the web just shows it.

## What it shows
- The 4 brains (IA10·Dali·Karen·Mini) with live status (idle / working).
- The live BOARD: active tasks, owners, status, recent decisions (read from BOARD.md / git).
- Recent war-room activity (the agents' posts / commits).
- On-brand ONE TEN aesthetic (reuse the look of the existing card-fan / 4-avatar page).

## How (token-frugal, no LLM in the web)
- Static or lightweight front-end that reads `BOARD.md` + git log (e.g. a small reader that
  parses the markdown board + `git log`), refreshed on a poll. No model calls.
- Keep the EXISTING ONE TEN 4-model web app untouched (separate page).

## Notes
- Build it inside the warroom repo under `web/`. Coordinate with IA10 (Supervisor) on the data shape (how to expose the board to the web).
- This is a SHELL-first build: get the layout + live board reading working, polish after.
- Big task — plan it properly; deliver in stages.

## 2026-06-05 · Dali refinement
- Elevated `web/public/` toward the cinematic ONE TEN design language: deep-space starfield, elegant serif hero, wide-tracked micro-labels, premium dark translucent panels, and a more composed 4-brain status fan.
- Made the deployed static front-end fetch public GitHub data directly: raw `BOARD.md` plus repo commits from the GitHub API. `/api/state` remains as a GitHub-first local dev fallback.
- Confirmed no LLM/OpenRouter calls; the web face only reads board/commit state.
