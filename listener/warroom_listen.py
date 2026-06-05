#!/usr/bin/env python3
"""War Room listener (token-FRUGAL): a DUMB poller — no LLM.
Reads the war-room Telegram group, and when a HUMAN message @-addresses an agent
that lives on THIS machine, it routes the command to that agent's local inbox.
Unaddressed messages cost nothing. The expensive LLM agent is only engaged when
something is actually for it.

Config: ~/.warroom/env  → WARROOM_BOT_TOKEN, WARROOM_CHAT_ID
        WARROOM_AGENTS  (env) → comma list of agent ids hosted on THIS machine, e.g. "IA10,Dali"
Routes matched commands to: ~/.warroom/inbox/<agent>.jsonl  (one JSON line per command)
"""
import os, re, json, time, urllib.request, urllib.parse, pathlib

HOME = pathlib.Path.home()
ENV = HOME / ".warroom" / "env"
INBOX = HOME / ".warroom" / "inbox"
OFFSET_F = HOME / ".warroom" / ".offset"
ALL_AGENTS = ["IA10", "Dali", "Karen", "Mini"]

def load_env():
    d = {}
    for ln in ENV.read_text().splitlines():
        if "=" in ln:
            k, v = ln.split("=", 1); d[k] = v
    return d

def api(tok, method, params=None):
    url = f"https://api.telegram.org/bot{tok}/{method}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=70) as r:
        return json.load(r)

def addressed_agents(text):
    """Return the set of agent ids this message is addressed to (@Name or 'Name,' or 'Name:')."""
    hits = set()
    low = text.lower()
    for a in ALL_AGENTS:
        al = a.lower()
        if re.search(r"(^|[\s@\(\[])" + re.escape(al) + r"([\s,:\)\]!?。，：]|$)", low):
            hits.add(a)
    return hits

def main():
    env = load_env()
    tok = env["WARROOM_BOT_TOKEN"]; gid = str(env["WARROOM_CHAT_ID"])
    mine = [a.strip() for a in os.environ.get("WARROOM_AGENTS", "").split(",") if a.strip()]
    if not mine:
        print("set WARROOM_AGENTS=IA10,Dali (the agents hosted on this machine)"); return
    INBOX.mkdir(parents=True, exist_ok=True)
    offset = int(OFFSET_F.read_text()) if OFFSET_F.exists() else None
    print(f"[listener] watching group for {mine}  (token-frugal, no LLM)")
    while True:
        try:
            params = {"timeout": 50}
            if offset is not None: params["offset"] = offset
            res = api(tok, "getUpdates", params).get("result", [])
            for u in res:
                offset = u["update_id"] + 1
                m = u.get("message") or {}
                if str(m.get("chat", {}).get("id")) != gid:   # only the war-room group
                    continue
                frm = m.get("from", {})
                if frm.get("is_bot"):     # ignore agent posts (they're the bot's own sends anyway)
                    continue
                text = m.get("text") or ""
                if not text:
                    continue
                for a in addressed_agents(text) & set(mine):
                    rec = {"ts": m.get("date"), "from": frm.get("first_name") or frm.get("username"),
                           "agent": a, "text": text}
                    (INBOX / f"{a}.jsonl").open("a").write(json.dumps(rec, ensure_ascii=False) + "\n")
                    print(f"[listener] → routed to {a}: {text[:60]}")
            OFFSET_F.write_text(str(offset) if offset is not None else "")
        except Exception as e:
            print("[listener] err:", e); time.sleep(5)

if __name__ == "__main__":
    main()
