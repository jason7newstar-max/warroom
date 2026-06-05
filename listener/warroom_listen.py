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
                    say(tok, gid, f"👂 [listener] heard → routing to {', '.join(sorted(tgt))}: \"{text[:50]}\"")
            OFFSET_F.write_text(str(offset) if offset is not None else "")
        except Exception as e:
            print("[listener] err:", e); time.sleep(5)

if __name__ == "__main__":
    main()
