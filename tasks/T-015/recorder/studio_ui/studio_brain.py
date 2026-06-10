#!/usr/bin/env python3
"""PHANTOM — hands-free STUDIO SESSION brain (:8092).

The无人值守 recording flow. Two-layer brain (per Wentian 2026-06-10):
  - FAST layer (this service): a tiny intent parser over a FIXED command set using
    Groq Llama (cheap, ~ms). Handles all live-room control. NO Fable 5 in the loop.
  - SMART layer (Fable 5 / main Claude session): only for creative/judgement asks,
    reached separately — not here.

Session model (solves "唤醒词太频繁" + "踩着脚踏累"):
  - Say "Hey Mini, 开始录歌" once → SESSION OPENS → mic stays hot, NO more wake word.
  - A FOOT-PEDAL TAP (or SPACE while no pedal) is the SING signal: tap → count-in →
    record one phrase → auto-stop on phrase end → back to LISTEN-for-commands.
  - Between phrases just SPEAK commands (no wake word): "第二段重来", "伴奏大一点",
    "听一下", "出歌". They map to PHANTOM's existing endpoints.
  - Idle a while → session sleeps; next "Hey Mini" reopens it.

This service exposes:
  POST /intent {"text": "..."}        -> {"action","args","say"}   (parse a spoken command)
  GET  /state                         -> current session state
  POST /state {"state": "..."}        -> set session state (sing/listen/idle)
The web view (or a headless mic loop) calls /intent with transcribed speech and then
drives the PHANTOM /api endpoints. Recording stays DRY; this only routes intent.
"""
import json, ssl, re, urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ENV = Path.home() / ".hermes" / ".env"
KEY = ""
if ENV.exists():
    for ln in ENV.read_text().splitlines():
        if ln.startswith("GROQ_API_KEY="):
            KEY = ln.split("=", 1)[1].strip().strip('"\''); break

# The fixed studio command set the fast layer must map onto.
ACTIONS = """
record_take      — start recording a fresh full take (从头录 / 录一遍 / 开始)
sing_phrase      — record/redo a specific phrase N (重唱第N句/段, 第N段重来)
stop             — stop the current recording / punch out (停, 够了, 这句可以了)
play             — audition backing+vocal (听一下, 回放, 放来听听)
play_from        — play from phrase/段 N (从第N段开始放)
set_backing_gain — change backing volume, dir=up|down (伴奏大一点/小一点)
set_monitor      — change ear-return style: silk|stage|dry (耳返换成丝滑/现场/干声)
analyze          — split into phrases (分句, 分析段落)
pitch            — run pitch report (听一下音准, 音准报告)
finish           — comp + save the finished song (出歌, 搞定, 导出, 完成)
import_backing   — load a backing track (导入伴奏, 用我刚发的伴奏)
end_session      — close the session (结束, 收工, 拜拜)
unknown          — none of the above
"""

SYS = (
    "You are the dispatcher for a hands-free recording studio in New York City. The singer may speak "
    "ANY of: Chinese(中/粤), English, Spanish(español), Korean(한국어), Japanese(日本語), or a mix. "
    "Map their utterance to EXACTLY ONE action from this list and extract args. "
    "Reply ONLY compact JSON: {\"action\":\"...\",\"args\":{...},\"say\":\"<short spoken confirmation IN THE SAME LANGUAGE the singer used>\"}. "
    "For phrase numbers put {\"n\": <int>} (parse numerals in any language: 第三句/line three/línea tres/세 번째/3番目 → 3). "
    "For gain put {\"dir\":\"up|down\"}. For monitor put {\"style\":\"silk|stage|dry\"}. "
    "Examples across languages: 'redo line 2' / 'repite la segunda' / '두 번째 다시' / '2番目もう一回' → sing_phrase n=2; "
    "'export'/'termina'/'끝내자'/'書き出して' → finish; 'louder backing'/'más alto el playback' → set_backing_gain up. "
    "If unclear use action \"unknown\".\n\nACTIONS:\n" + ACTIONS
)

_CN = {"一":1,"二":2,"两":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9,"十":10,"第一":1,"首":1}
_WORDNUM = {  # english/spanish/korean/japanese ordinals & cardinals → int
    "one":1,"first":1,"two":2,"second":2,"three":3,"third":3,"four":4,"fourth":4,"five":5,"fifth":5,
    "uno":1,"primera":1,"primer":1,"dos":2,"segunda":2,"segundo":2,"tres":3,"tercera":3,"tercer":3,
    "cuatro":4,"cuarta":4,"cinco":5,"quinta":5,
    "하나":1,"첫":1,"둘":2,"두":2,"셋":3,"세":3,"넷":4,"네":4,"다섯":5,"다섯번":5,
    "ひとつ":1,"いち":1,"ふたつ":2,"に":2,"みっつ":3,"さん":3,"よん":4,"し":4,"ご":5,
}

def _quick(text):
    """Offline fallback parser (no network) — multilingual (中英西韩日)."""
    t = text.strip(); tl = t.lower()
    def num():
        m = re.search(r'第?\s*([0-9]+|[一二两三四五六七八九十])\s*[句段遍条]', t)
        if m:
            g = m.group(1); return int(g) if g.isdigit() else _CN.get(g)
        m = re.search(r'(?:line|phrase|l[ií]nea|frase|번째|番目)\s*([0-9]+)', tl)
        if m: return int(m.group(1))
        m = re.search(r'([0-9]+)\s*(?:번째|番目|줄|line)', tl)
        if m: return int(m.group(1))
        for w,v in _WORDNUM.items():
            if w in tl: return v
        return None
    # finish / export
    if re.search(r'(出歌|搞定|完成|导出|存(歌|盘)|可以了出|export|finish|done|termina|exporta|listo|끝|완성|내보내|書き出|完成|終わり)', tl):
        return {"action":"finish","args":{},"say":"Done · 出歌"}
    if re.search(r'(结束|收工|拜拜|退出|end session|quit|exit|terminar sesión|종료|끝내자|終了|やめ)', tl):
        return {"action":"end_session","args":{},"say":"收工 · bye"}
    # redo / sing a phrase
    if re.search(r'(重唱|重来|再来|再录|redo|again|re-?sing|repite|repetir|otra vez|다시|한번 더|もう一回|もういちど|やり直)', tl):
        n=num(); return {"action":"sing_phrase","args":{"n":n} if n else {},"say":(f"重唱第{n}句·redo line {n}" if n else "重唱·redo")}
    if re.search(r'(play from|从.*[句段].*放|reproduce desde|부터 재생|から再生)', tl):
        n=num(); return {"action":"play_from","args":{"n":n},"say":f"from {n}"}
    if re.search(r'(听一下|回放|放来听|放一下|play|listen|playback|escuchar|reproduce|들어|재생|聞いて|再生)', tl):
        return {"action":"play","args":{},"say":"播放 · play"}
    if re.search(r'(伴奏.*(大|高|响)|louder|backing up|más alto|크게|大きく)', tl):
        return {"action":"set_backing_gain","args":{"dir":"up"},"say":"伴奏 ↑"}
    if re.search(r'(伴奏.*(小|低|轻)|quieter|softer|backing down|más bajo|작게|小さく)', tl):
        return {"action":"set_backing_gain","args":{"dir":"down"},"say":"伴奏 ↓"}
    if re.search(r'(丝滑|silk|smooth|suave|부드럽|シルク)', tl): return {"action":"set_monitor","args":{"style":"silk"},"say":"丝滑·silk"}
    if re.search(r'(现场|舞台|stage|live|escenario|스테이지|ステージ)', tl): return {"action":"set_monitor","args":{"style":"stage"},"say":"现场·stage"}
    if re.search(r'(干声|dry|seco|드라이|ドライ)', tl): return {"action":"set_monitor","args":{"style":"dry"},"say":"干声·dry"}
    if re.search(r'(音准|准不准|跑调|pitch|tune|afinación|음정|ピッチ|音程)', tl): return {"action":"pitch","args":{},"say":"音准·pitch"}
    if re.search(r'(分句|分析段落|断句|analyze|split|segment|analiza|분석|分析)', tl): return {"action":"analyze","args":{},"say":"分句·split"}
    if re.search(r'(导入|用.*伴奏|加载.*伴奏|import|load backing|importa|불러|読み込)', tl): return {"action":"import_backing","args":{},"say":"导入伴奏"}
    if re.search(r'(停|够了|结束这句|stop|cut|punch|para|alto|멈춰|그만|止めて|ストップ)', tl): return {"action":"stop","args":{},"say":"停·stop"}
    if re.search(r'(录一遍|从头|重新录|录个|开始录|录音|record|take|start|graba|empezar|녹음|시작|録音|スタート)', tl): return {"action":"record_take","args":{},"say":"开始录·rec"}
    return {"action":"unknown","args":{},"say":""}

def groq_intent(text):
    body = {"model":"llama-3.3-70b-versatile",
            "messages":[{"role":"system","content":SYS},{"role":"user","content":text}],
            "max_tokens":120,"temperature":0,"response_format":{"type":"json_object"}}
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization":f"Bearer {KEY}","Content-Type":"application/json",
                 "User-Agent":"oneten-studio/1.0"})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        return json.loads(json.load(r)["choices"][0]["message"]["content"])

STATE = {"state": "idle"}   # idle | listen | sing

class H(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
    def _json(self,o,code=200):
        d=json.dumps(o,ensure_ascii=False).encode()
        self.send_response(code); self._cors()
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(d))); self.end_headers(); self.wfile.write(d)
    def do_OPTIONS(self): self.send_response(204); self._cors(); self.end_headers()
    def do_GET(self):
        if self.path=="/state": return self._json(STATE)
        self._json({"ok":True,"service":"studio_brain"})
    def do_POST(self):
        n=int(self.headers.get("Content-Length",0)); raw=self.rfile.read(n) or b"{}"
        try: d=json.loads(raw)
        except Exception: d={}
        if self.path=="/state":
            STATE["state"]=d.get("state","idle"); return self._json(STATE)
        if self.path=="/intent":
            text=(d.get("text") or "").strip()
            if not text: return self._json({"action":"unknown","args":{},"say":""})
            try:
                out = groq_intent(text) if KEY else _quick(text)
                if not out.get("action"): out=_quick(text)
            except Exception:
                out=_quick(text)            # network/parse fail → offline parser
            out.setdefault("args",{}); out.setdefault("say","")
            return self._json(out)
        self._json({"ok":False},404)

if __name__=="__main__":
    print("PHANTOM studio brain on http://127.0.0.1:8092 (intent: Groq Llama + offline fallback)")
    HTTPServer(("127.0.0.1",8092),H).serve_forever()
