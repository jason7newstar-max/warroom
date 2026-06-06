#!/usr/bin/env python3
"""War Room listener — token-FRUGAL dumb poller (no LLM).
Reads the war-room Telegram group (text + VOICE→STT), matches agent names (with
aliases for STT slips), routes addressed commands to ~/.warroom/inbox/<agent>.jsonl,
and posts a short ACK to the group so you can see it heard you.
The expensive LLM is only engaged downstream (the wake/inject step), never here.

env (~/.warroom/env): WARROOM_BOT_TOKEN, WARROOM_CHAT_ID
env (process):        WARROOM_AGENTS=IA10,Dali   (agents hosted on THIS machine)
needs: voice-stt on PATH (for voice messages)
"""
import os, re, json, time, subprocess, urllib.request, urllib.parse, pathlib

HOME = pathlib.Path.home()
ENV = HOME / ".warroom" / "env"
INBOX = HOME / ".warroom" / "inbox"
OFFSET_F = HOME / ".warroom" / ".offset"

# agent name → aliases (lowercased; covers STT mangling of the names)
ALIASES = {
    "IA10":  ["ia10", "ia 10", "a10", "a 10", "ih", "ai10", "ai 10", "爱艾", "爱一零", "矮一零", "ia一零", "艾10"],
    "Dali":  ["dali", "达利", "大力", "达里", "dolly"],
    "Karen": ["karen", "凯伦", "卡伦", "凯琳", "凯伦"],
    "Mini":  ["mini", "迷你", "米妮", "咪你", "mimi"],
    "Gemma": ["gemma", "杰玛", "吉玛", "gema", "gamma", "加马", "哥马", "捷玛"],
}

# which engine each agent runs on + how to wake it
ENGINE = {"IA10": "claude", "Karen": "claude", "Dali": "codex", "Mini": "codex"}
CODEX_BIN = os.environ.get("CODEX_BIN", "/Applications/Codex.app/Contents/Resources/codex")
CODEX_WS  = os.path.expanduser(os.environ.get("CODEX_WS", "~/codex-work/warroom"))
WAKE_LOG  = HOME / ".warroom" / "wake.log"

def wake_codex(agent, message):
    """Launch a fresh headless `codex exec` worker for a Codex agent (Dali/Mini).
    Non-blocking. The worker pulls, handles the addressed message, commits/pushes,
    and reports via warroom-say. Continuity lives in git, not chat."""
    import subprocess, shlex
    ws = AGENT_WS.get(agent, CODEX_WS)
    prompt = (
        f"You are {agent}, a worker in the ONE TEN war room. A message in the war-room "
        f"Telegram group is addressed to you:\n\n>>> {message}\n\n"
        f"Do this, staying strictly within this repo ({ws}):\n"
        f"1) `git pull` to get the latest board.\n"
        f"2) Read BOARD.md and any referenced task file in tasks/.\n"
        f"3) Do exactly what the message asks (edit files / write a proposal / etc). "
        f"Stay in scope; do not run destructive commands.\n"
        f"4) `git add -A && git -c user.name=\"{agent}\" -c user.email=warroom@pinla.local "
        f"commit -m \"[{agent}] <what you did>\" && git push`.\n"
        f"5) Report: `bin/warroom-say \"[{agent}] done: <one line>\"`.\n"
        f"Be concise and token-frugal."
    )
    logf = open(WAKE_LOG, "a")
    logf.write(f"\n=== wake {agent} @ {time.strftime('%H:%M:%S')} :: {message[:60]} ===\n"); logf.flush()
    try:
        subprocess.Popen(
            [CODEX_BIN, "exec", "-s", "danger-full-access", "--skip-git-repo-check", prompt],
            cwd=ws, stdout=logf, stderr=subprocess.STDOUT, start_new_session=True)
        print(f"[listener] 🚀 launched codex exec worker for {agent}")
    except Exception as e:
        print(f"[listener] wake_codex err: {e}")

CLAUDE_BIN = os.environ.get("CLAUDE_BIN", os.path.expanduser("~/.local/bin/claude"))
CLAUDE_WS  = os.path.expanduser(os.environ.get("CLAUDE_WS", "~/claude-work/warroom"))

# Per-agent git checkout, so multiple agents can run on ONE machine without
# colliding on the same working tree. Each agent pulls/commits/pushes its own clone.
AGENT_WS = {
    "IA10":  os.path.expanduser("~/claude-work/warroom"),
    "Karen": os.path.expanduser("~/claude-work/warroom-karen"),
    "Dali":  os.path.expanduser("~/codex-work/warroom"),
    "Mini":  os.path.expanduser("~/codex-work/warroom-mini"),
}

def wake_claude(agent, message):
    """Launch a fresh headless `claude -p` worker for a Claude WORKER agent (e.g. Karen).
    Symmetric to wake_codex; continuity via git, token-frugal (only on a real pickup)."""
    import subprocess
    ws = AGENT_WS.get(agent, CLAUDE_WS)
    prompt = (
        f"You are {agent}, a worker in the ONE TEN war room. A war-room group message is "
        f"addressed to you:\n\n>>> {message}\n\nStaying strictly within {ws}: "
        f"git pull; read BOARD.md + any referenced tasks/ file; do exactly what the message asks "
        f"(no destructive commands); then git add -A && git -c user.name=\"{agent}\" "
        f"-c user.email=warroom@pinla.local commit -m \"[{agent}] <what>\" && git push; "
        f"then run bin/warroom-say \"[{agent}] done: <one line>\". Be concise."
    )
    logf = open(WAKE_LOG, "a")
    logf.write(f"\n=== wake {agent} (claude) @ {time.strftime('%H:%M:%S')} :: {message[:60]} ===\n"); logf.flush()
    try:
        subprocess.Popen([CLAUDE_BIN, "-p", "--allow-dangerously-skip-permissions", prompt],
            cwd=ws, stdout=logf, stderr=subprocess.STDOUT, start_new_session=True)
        print(f"[listener] 🚀 launched claude -p worker for {agent}")
    except Exception as e:
        print(f"[listener] wake_claude err: {e}")

# ── RELAY: for agents hosted on ANOTHER machine (e.g. the Air), don't wake locally —
# write a work-order into the shared git repo and push it. A relay worker on that
# machine (warroom_relay_worker.py) pulls + runs it. Only THIS side writes relay/inbox
# → race-free. Set WARROOM_RELAY_AGENTS="Karen,Mini,Gemma" to route those remotely.
RELAY_AGENTS = set(a.strip() for a in os.environ.get("WARROOM_RELAY_AGENTS", "").split(",") if a.strip())
RELAY_REPO = os.path.expanduser(os.environ.get("RELAY_REPO", "~/claude-work/warroom"))
RELAY_INBOX = os.path.join(RELAY_REPO, "relay", "inbox")

def relay_dispatch(agent, message):
    import json as _j, random
    os.makedirs(RELAY_INBOX, exist_ok=True)
    oid = f"{agent}-{int(time.time())}-{random.randint(1000,9999)}"
    rel = os.path.join("relay", "inbox", oid + ".json")
    with open(os.path.join(RELAY_REPO, rel), "w") as f:
        _j.dump({"id": oid, "agent": agent, "text": message, "ts": int(time.time())},
                f, ensure_ascii=False)
    for _ in range(3):
        subprocess.run(["git", "-C", RELAY_REPO, "add", rel])
        subprocess.run(["git", "-C", RELAY_REPO, "-c", "user.name=IA10",
                        "-c", "user.email=warroom@pinla.local", "commit", "-q",
                        "-m", f"[relay] order {oid}: {message[:40]}", "--", rel])
        subprocess.run(["git", "-C", RELAY_REPO, "pull", "--rebase", "-q", "origin", "main"])
        if subprocess.run(["git", "-C", RELAY_REPO, "push", "-q", "origin", "main"]).returncode == 0:
            print(f"[listener] 📤 relayed → {agent} (remote): {message[:50]}"); return
        time.sleep(1)
    print(f"[listener] relay push failed for {agent}")

# ── LIVE status: write live/now.json the moment an agent is dispatched, so the
# web front-end can show "who's on what NOW" (zero LLM/token; front-end polls it).
LIVE_FILE = os.path.join(RELAY_REPO, "live", "now.json")

def mark_live(agent, message):
    import json as _j
    os.makedirs(os.path.dirname(LIVE_FILE), exist_ok=True)
    try:
        data = _j.load(open(LIVE_FILE)) if os.path.exists(LIVE_FILE) else {}
    except Exception:
        data = {}
    data.setdefault("agents", {})
    data["agents"][agent] = {"task": message[:90], "ts": int(time.time())}
    data["updated"] = int(time.time())
    with open(LIVE_FILE, "w") as f:
        _j.dump(data, f, ensure_ascii=False)
    for _ in range(2):
        subprocess.run(["git", "-C", RELAY_REPO, "add", "live/now.json"])
        subprocess.run(["git", "-C", RELAY_REPO, "-c", "user.name=IA10",
                        "-c", "user.email=warroom@pinla.local", "commit", "-q",
                        "-m", f"[live] {agent} → {message[:30]}", "--", "live/now.json"])
        subprocess.run(["git", "-C", RELAY_REPO, "pull", "--rebase", "-q", "origin", "main"])
        if subprocess.run(["git", "-C", RELAY_REPO, "push", "-q", "origin", "main"]).returncode == 0:
            return
        time.sleep(1)

def load_env():
    d = {}
    for ln in ENV.read_text().splitlines():
        if "=" in ln:
            k, v = ln.split("=", 1); d[k] = v
    return d

def api(tok, method, params=None, timeout=70):
    url = f"https://api.telegram.org/bot{tok}/{method}"
    if params: url += "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.load(r)

def say(tok, gid, text):
    data = urllib.parse.urlencode({"chat_id": gid, "text": text}).encode()
    urllib.request.urlopen(urllib.request.Request(
        f"https://api.telegram.org/bot{tok}/sendMessage", data=data), timeout=15).read()

def stt_voice(tok, file_id):
    """download a voice file_id and transcribe via voice-stt."""
    try:
        info = api(tok, "getFile", {"file_id": file_id}, timeout=20)
        path = info["result"]["file_path"]
        url = f"https://api.telegram.org/file/bot{tok}/{path}"
        tmp = "/tmp/wr_voice.oga"
        urllib.request.urlretrieve(url, tmp)
        out = subprocess.run(["voice-stt", "-l", "zh", tmp], capture_output=True, text=True, timeout=60)
        return out.stdout.strip()
    except Exception as e:
        print("[listener] stt err:", e); return ""

def addressed(text):
    low = text.lower()
    hits = set()
    for agent, al in ALIASES.items():
        for a in al:
            if a in low:
                hits.add(agent); break
    return hits

def main():
    env = load_env()
    tok = env["WARROOM_BOT_TOKEN"]; gid = str(env["WARROOM_CHAT_ID"])
    mine = [a.strip() for a in os.environ.get("WARROOM_AGENTS", "").split(",") if a.strip()]
    if not mine:
        print("set WARROOM_AGENTS=IA10,Dali (agents on this machine)"); return
    INBOX.mkdir(parents=True, exist_ok=True)
    offset = int(OFFSET_F.read_text()) if OFFSET_F.exists() and OFFSET_F.read_text().strip() else None
    print(f"[listener] watching war-room group for {mine} (voice+text, token-frugal)")
    while True:
        try:
            params = {"timeout": 50}
            if offset is not None: params["offset"] = offset
            for u in api(tok, "getUpdates", params).get("result", []):
                offset = u["update_id"] + 1
                m = u.get("message") or {}
                if str(m.get("chat", {}).get("id")) != gid: continue
                frm = m.get("from", {})
                if frm.get("is_bot"): continue
                text = m.get("text") or ""
                if not text and m.get("voice"):
                    text = stt_voice(tok, m["voice"]["file_id"])
                    if text: print(f"[listener] voice→ {text[:60]}")
                if not text: continue
                tgt = addressed(text) & set(mine)
                if tgt:
                    for a in tgt:
                        rec = {"ts": m.get("date"), "from": frm.get("first_name") or frm.get("username"),
                               "agent": a, "text": text}
                        (INBOX / f"{a}.jsonl").open("a").write(json.dumps(rec, ensure_ascii=False) + "\n")
                        print(f"[listener] → routed to {a}: {text[:60]}")
                        mark_live(a, text)                     # update web LIVE panel
                        if a in RELAY_AGENTS:
                            relay_dispatch(a, text)            # remote machine (Air) handles it
                        elif ENGINE.get(a) == "codex":
                            wake_codex(a, text)                # local Codex worker (Dali)
                        elif ENGINE.get(a) == "claude" and a != "IA10":
                            wake_claude(a, text)               # local Claude worker (Karen, if local)
                        # IA10 = the supervisor session; it reads the group directly, no wake
                    say(tok, gid, f"👂 [listener] heard → {', '.join(sorted(tgt))}: \"{text[:50]}\"")
            OFFSET_F.write_text(str(offset) if offset is not None else "")
        except Exception as e:
            print("[listener] err:", e); time.sleep(5)

if __name__ == "__main__":
    main()
