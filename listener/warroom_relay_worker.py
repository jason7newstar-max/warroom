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


GEMMA_SYS = (
    "你是 Gemma,运行在文天的 M4 MacBook Air 本地(不是 Google,也不联网)。"
    "用中文直接给最终答案,最多 3 句话。严禁输出任何思考过程、推理、'Thinking'、"
    "选项罗列、英文分析或重复。只用这一行格式回复,不要别的:\n答案:<你的话>"
)


def _clean_gemma(raw):
    """gemma4:12b is a reasoning model that dumps its whole chain-of-thought.
    Keep only the real answer: prefer text after the last '答案:'; else drop
    reasoning-looking lines and keep the last substantive paragraph."""
    import re
    t = (raw or "").strip()
    m = list(re.finditer(r"答案\s*[:：]\s*", t))
    if m:
        t = t[m[-1].end():].strip()
    else:
        paras = [p.strip() for p in t.splitlines() if p.strip()]
        paras = [p for p in paras if not p.lower().lstrip("*-# ").startswith(
            ("thinking", "option", "wait", "identify", "platform", "special", "let's", "strictly"))]
        t = paras[-1] if paras else t
    return t[:600].strip() or "(no output)"


def run_gemma(agent, message, ws):
    """Gemma = free local model = a diverse 3rd voice / opinion (no Anthropic/OpenAI
    tokens). It only TALKS — no git, no file edits, no internet. Output is cleaned of
    the model's verbose reasoning before posting."""
    git(ws, "pull", "--rebase", "origin", "main")
    prompt = GEMMA_SYS + "\n\n问题:" + message
    r = subprocess.run([OLLAMA_BIN, "run", GEMMA_MODEL, prompt],
                       capture_output=True, text=True)
    raw = (r.stdout or "").strip() or (r.stderr or "").strip() or "(no output)"
    ans = _clean_gemma(raw)
    # Record Gemma's voice into GIT so the Supervisor (IA10) can READ it — the bot
    # can't see its own group messages, so warroom-say alone is invisible to IA10.
    vp = os.path.join(ws, "relay", "voices")
    os.makedirs(vp, exist_ok=True)
    with open(os.path.join(vp, f"gemma-{int(time.time())}.md"), "w") as f:
        f.write(f"# Gemma · {time.strftime('%Y-%m-%d %H:%M')}\n\n**Q:** {message}\n\n**A:** {ans}\n")
    git(ws, "add", "relay/voices")
    git(ws, "-c", "user.name=Gemma", "-c", "user.email=warroom@pinla.local",
        "commit", "-q", "-m", f"[Gemma] voice: {ans[:50]}")
    for _ in range(2):
        git(ws, "pull", "--rebase", "origin", "main")
        if git(ws, "push", "-q", "origin", "main").returncode == 0:
            break
    subprocess.run([os.path.join(ws, "bin", "warroom-say"), f"[Gemma] {ans}"], cwd=ws)


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
