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
    prompt = (
        f"You are {agent}, a worker in the ONE TEN war room. A message in the war-room "
        f"Telegram group is addressed to you:\n\n>>> {message}\n\n"
        f"Do this, staying strictly within this repo ({CODEX_WS}):\n"
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
            cwd=CODEX_WS, stdout=logf, stderr=subprocess.STDOUT, start_new_session=True)
        print(f"[listener] 🚀 launched codex exec worker for {agent}")
    except Exception as e:
        print(f"[listener] wake_codex err: {e}")

CLAUDE_BIN = os.environ.get("CLAUDE_BIN", os.path.expanduser("~/.local/bin/claude"))
CLAUDE_WS  = os.path.expanduser(os.environ.get("CLAUDE_WS", "~/claude-work/warroom"))

def wake_claude(agent, message):
    """Launch a fresh headless `claude -p` worker for a Claude WORKER agent (e.g. Karen).
    Symmetric to wake_codex; continuity via git, token-frugal (only on a real pickup)."""
    import subprocess
    prompt = (
        f"You are {agent}, a worker in the ONE TEN war room. A war-room group message is "
        f"addressed to you:\n\n>>> {message}\n\nStaying strictly within {CLAUDE_WS}: "
        f"git pull; read BOARD.md + any referenced tasks/ file; do exactly what the message asks "
        f"(no destructive commands); then git add -A && git -c user.name=\"{agent}\" "
        f"-c user.email=warroom@pinla.local commit -m \"[{agent}] <what>\" && git push; "
        f"then run bin/warroom-say \"[{agent}] done: <one line>\". Be concise."
    )
    logf = open(WAKE_LOG, "a")
    logf.write(f"\n=== wake {agent} (claude) @ {time.strftime('%H:%M:%S')} :: {message[:60]} ===\n"); logf.flush()
    try:
        subprocess.Popen([CLAUDE_BIN, "-p", "--allow-dangerously-skip-permissions", prompt],
            cwd=CLAUDE_WS, stdout=logf, stderr=subprocess.STDOUT, start_new_session=True)
        print(f"[listener] 🚀 launched claude -p worker for {agent}")
    except Exception as e:
        print(f"[listener] wake_claude err: {e}")

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
                        if ENGINE.get(a) == "codex":
                            wake_codex(a, text)
                    say(tok, gid, f"👂 [listener] heard → waking {', '.join(sorted(tgt))}: \"{text[:50]}\"")
            OFFSET_F.write_text(str(offset) if offset is not None else "")
        except Exception as e:
            print("[listener] err:", e); time.sleep(5)

if __name__ == "__main__":
    main()
