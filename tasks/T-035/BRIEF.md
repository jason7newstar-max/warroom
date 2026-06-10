# T-035 — JARVIS MISSION-CONTROL CONSOLE (Iron-Man HUD) + Hue hooks

**Owner: Dali (Codex, iMac).** Chairman: Wentian. Supervisor: IA10.
IA10 handles the **Hue local bridge** separately (needs hardware); YOU build the **front-end console**.

## What this is
A full-screen JARVIS-style mission-control UI for the ONE TEN war room — the central
"command console" Wentian talks to. Think **Iron Man HUD**: holographic, glowing,
translucent "透视屏" (see-through) panels, floating **Liquid Glass** windows, light/scan-line
ambience. It shows live ops at a glance and is the canvas the Hue lights will sync to.

We already have a first JARVIS dashboard (PINLA COMMAND): live at
https://jarvis-dashboard-five-peach.vercel.app , source `~/projects/jarvis-dashboard/index.html`
(single file). **Build the upgraded version** — you may start from that file's data wiring,
but the visual language should level up to the Iron-Man HUD spec below.

## Visual spec (the look)
- **Iron-Man / Tony Stark HUD**: dark space-charcoal bg, cyan/gold accent glow, thin
  circular gauges, radial tick rings, scanning sweep lines, subtle grid + particle haze.
- **Liquid Glass floating windows**: frosted translucent panels (backdrop-blur, soft inner
  glow, 1px luminous border, rounded), that *float* (gentle parallax/drift on mouse), can
  overlap, with a faint refraction highlight. This is the signature element — nail it.
- **透视屏 see-through displays**: panels you can faintly see the background through; layered depth.
- Motion: everything breathes — gauges animate, numbers tick, panels drift, a soft holographic
  flicker. 60fps, GPU-friendly (CSS transforms + canvas, no heavy libs).

## Content / panels (data)
- **Central voice core**: a glowing reactive orb/arc-reactor in the middle = the voice-interaction
  focus (ties to the Quantum Core voice agent later). It should pulse/react (for now to a fake
  audio level; IA10 will wire real mic FFT). Leave a clean hook: a JS function `setCoreLevel(0..1)`
  and `setCoreState('idle'|'listening'|'speaking'|'working')`.
- **Progress rings**: overall ops progress + a few key metrics as radial gauges.
- **Task cards**: card-shaped panels listing live tasks / things-to-do — pull from the war-room
  board. Source = the public GitHub `BOARD.md` (parse the ACTIVE TASKS table) and/or the
  tasks/ folder. Show id, title, status chip (🟡/🟢/🟣/⚪), owner. No LLM / no OpenRouter burn.
- **Activity/log stream**: recent commits (GitHub API, public repo jason7newstar-max/warroom)
  scrolling like a telemetry feed.
- Clock / system status line.

## Hue integration (DO NOT build the bridge — just expose hooks)
IA10 builds a local service that drives Philips Hue via the Entertainment API (screen-color +
audio sync). All YOU need to do in the UI:
1. Expose the **current dominant accent color(s)** of the console as a JS hook:
   `window.jarvisColors()` → returns an array of `[r,g,b]` (e.g. the live accent + 2 panel hues).
2. Expose `window.jarvisAudioLevel()` → 0..1 (the core's current reactive level).
The bridge will poll these (or we'll push via a tiny WebSocket later). Keep them global + documented.

## Tech / constraints
- Single-page, dependency-light (vanilla JS + CSS + canvas; small libs OK if justified, no React build).
- Deployable as a static site to Vercel (like the current one). 60fps, works in Chrome.
- **No LLM / OpenRouter / paid-API calls.** GitHub reads = public, unauthenticated.
- Keep it a self-contained folder so it deploys clean.

## Deliverable + handoff
- Build under `tasks/T-035/console/` (e.g. `index.html` + assets). Self-contained.
- `git add -A && git -c user.name=Dali -c user.email=warroom@pinla.local commit -m "[Dali] T-035 JARVIS console v1" && (git push || (git pull --rebase origin main && git push))`.
- `bin/warroom-say "[Dali] done: T-035 JARVIS console v1 pushed (tasks/T-035/console/)"`.
- If you hit a blocker, warroom-say the exact issue — don't fake it.

This is the centerpiece Wentian sees every day. Make it feel like stepping into Stark's lab.
