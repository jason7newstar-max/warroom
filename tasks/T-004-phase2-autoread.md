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
_(Dali: write here)_

### Mini's proposal:
_(Mini: write here)_
