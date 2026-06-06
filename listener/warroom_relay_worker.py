#!/usr/bin/env python3
"""War-room RELAY WORKER — runs on a SECONDARY machine (e.g. the home M4 Air).

The iMac listener is the SOLE Telegram poller (one bot can only be polled by one
machine). When the group @s a REMOTE agent (Karen / Mini / Gemma), the iMac writes
a JSON work-order into `relay/inbox/` in the shared git repo and pushes it. THIS
worker — on the Air — pulls those orders, runs each one LOCALLY using the Air's own
Claude / Codex / Gemma, and the worker pushes its results normally.

Design note (why this is race-free): only the iMac ever WRITES relay/inbox. This
worker only READS it and remembers which orders it has handled in a LOCAL file
(~/.warroom/relay-seen) — it never pushes coordination files, so it can't collide
with the iMac or with task workers' own `git add -A` pushes.

    group @Karen ─▶ iMac listener writes relay/inbox/Karen-….json ─▶ push
                 ─▶ (Air) this worker pulls ─▶ runs claude -p in Air's checkout
                 ─▶ Karen pushes her work + warroom-say, all on the Air's M4

Run on the Air:
    WARROOM_RELAY_AGENTS="Karen,Mini,Gemma" python3 -u listener/warroom_relay_worker.py
"""
import os, sys, json, time, glob, subprocess

HOME = os.path.expanduser("~")
# Coordination checkout the worker PULLS to read orders (also Karen's checkout).
COORD_REPO = os.path.expanduser(os.environ.get("WARROOM_COORD_REPO", "~/claude-work/warroom"))
INBOX = os.path.join(COORD_REPO, "relay", "inbox")
SEEN_F = os.path.join(HOME, ".warroom", "relay-seen")
POLL = int(os.environ.get("WARROOM_RELAY_POLL", "8"))
MINE = set(a.strip() for a in os.environ.get("WARROOM_RELAY_AGENTS", "Karen,Mini,Gemma").split(",") if a.strip())

CODEX_BIN  = os.environ.get("CODEX_BIN", "/Applications/Codex.app/Contents/Resources/codex")
CLAUDE_BIN = os.path.expanduser(os.environ.get("CLAUDE_BIN", "~/.local/bin/claude"))
OLLAMA_BIN = os.environ.get("OLLAMA_BIN", "ollama")
GEMMA_MODEL = os.environ.get("GEMMA_MODEL", "gemma4:12b")

ENGINE = {"Karen": "claude", "Mini": "codex", "Gemma": "gemma"}
# Each agent runs in its OWN local checkout (so concurrent git stays clean).
WS = {
    "Karen": os.path.expanduser(os.environ.get("KAREN_WS", "~/claude-work/warroom")),
    "Mini":  os.path.expanduser(os.environ.get("MINI_WS",  "~/codex-work/warroom")),
    "Gemma": os.path.expanduser(os.environ.get("GEMMA_WS", "~/claude-work/warroom")),
}


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)


def load_seen():
    try:
        return set(l.strip() for l in open(SEEN_F) if l.strip())
    except FileNotFoundError:
        return set()


def mark_seen(oid):
    os.makedirs(os.path.dirname(SEEN_F), exist_ok=True)
    with open(SEEN_F, "a") as f:
        f.write(oid + "\n")


def task_prompt(agent, message, ws):
    return (
        f"You are {agent}, a worker in the ONE TEN war room. A war-room group message "
        f"is addressed to you:\n\n>>> {message}\n\nStaying strictly within {ws}: git pull; "
        f"read BOARD.md + any referenced tasks/ file; do exactly what the message asks "
        f"(no destructive commands); then git add -A && git -c user.name=\"{agent}\" "
        f"-c user.email=warroom@pinla.local commit -m \"[{agent}] <what>\" && git push; "
        f"then run bin/warroom-say \"[{agent}] done: <one line>\". Be concise."
    )


def run_claude(agent, message, ws):
    git(ws, "pull", "--rebase", "origin", "main")
    subprocess.run([CLAUDE_BIN, "-p", "--allow-dangerously-skip-permissions",
                    task_prompt(agent, message, ws)], cwd=ws)


def run_codex(agent, message, ws):
    git(ws, "pull", "--rebase", "origin", "main")
    subprocess.run([CODEX_BIN, "exec", "-s", "danger-full-access", "--skip-git-repo-check",
                    task_prompt(agent, message, ws)], cwd=ws)


def run_gemma(agent, message, ws):
    """Gemma = free local model. Answer the message and post it to the war room.
    Good for quick opinions / a diverse 3rd voice — no Anthropic/OpenAI tokens."""
    git(ws, "pull", "--rebase", "origin", "main")
    r = subprocess.run([OLLAMA_BIN, "run", GEMMA_MODEL, message],
                       capture_output=True, text=True)
    out = (r.stdout or "").strip() or (r.stderr or "").strip() or "(no output)"
    say = os.path.join(ws, "bin", "warroom-say")
    subprocess.run([say, f"[Gemma] {out[:1400]}"], cwd=ws)


RUN = {"claude": run_claude, "codex": run_codex, "gemma": run_gemma}


def main():
    print(f"[relay-worker] up for {sorted(MINE)} · coord={COORD_REPO} · poll={POLL}s", flush=True)
    seen = load_seen()
    while True:
        try:
            git(COORD_REPO, "pull", "--rebase", "origin", "main")
            for op in sorted(glob.glob(os.path.join(INBOX, "*.json"))):
                try:
                    order = json.load(open(op))
                except Exception:
                    continue
                oid = order.get("id") or os.path.basename(op)
                agent = order.get("agent")
                if oid in seen or agent not in MINE:
                    continue
                eng = ENGINE.get(agent)
                if eng not in RUN:
                    continue
                # Mark seen BEFORE running so a crash mid-task won't loop it.
                mark_seen(oid); seen.add(oid)
                print(f"[relay-worker] ▶ {agent} ({eng}): {order.get('text','')[:60]}", flush=True)
                try:
                    RUN[eng](agent, order.get("text", ""), WS.get(agent, COORD_REPO))
                    print(f"[relay-worker] ✓ {agent} done {oid}", flush=True)
                except Exception as e:
                    print(f"[relay-worker] ✗ {agent} err: {e}", flush=True)
        except Exception as e:
            print("[relay-worker] loop err:", e, flush=True); time.sleep(5)
        time.sleep(POLL)


if __name__ == "__main__":
    main()
