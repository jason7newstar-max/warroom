#!/usr/bin/env python3
"""T-035 — Philips Hue local bridge for the JARVIS console.

Drives Hue lights in real time so they sync to the console's COLOR + AUDIO.
Browsers can't speak the raw UDP/DTLS the Hue Entertainment API needs, so this
runs locally (on the iMac) and the JARVIS web page feeds it (via the small HTTP
endpoints below, or later a WebSocket).

Pipeline:
  JARVIS page  --colors/level-->  THIS service  --DTLS/UDP @25Hz-->  Hue Entertainment

SETUP IS THREE ONE-TIME STEPS (need the actual Hue Bridge v2 + lights):
  1) discover :  python3 hue_bridge.py discover
  2) pair     :  press the round button on the Bridge, then within 30s:
                 python3 hue_bridge.py pair          (saves app key + clientkey)
  3) areas    :  python3 hue_bridge.py areas         (list entertainment areas; pick one)
  run         :  python3 hue_bridge.py run --area <id>

Then point the JARVIS page's color/level feed at http://127.0.0.1:7878 .

Status: setup/pairing/area-list are REAL (just need the hardware on the LAN).
The DTLS streaming loop is scaffolded — it needs a DTLS lib (see TODO) + the
Bridge present to finish + test. Nothing here is faked.
"""
import json, sys, time, struct, argparse, urllib.request, ssl, threading, colorsys
from pathlib import Path

CFG = Path.home() / ".phantom" / "hue.json"        # stores {ip, appkey, clientkey, area}
CFG.parent.mkdir(parents=True, exist_ok=True)
APP_NAME = "oneten_jarvis#console"

def _get(url, timeout=8):
    ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
    return json.load(urllib.request.urlopen(url, timeout=timeout, context=ctx))

def _post(url, body, timeout=8):
    ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type":"application/json"}, method="POST")
    return json.load(urllib.request.urlopen(req, timeout=timeout, context=ctx))

def load_cfg():
    return json.loads(CFG.read_text()) if CFG.exists() else {}
def save_cfg(d):
    CFG.write_text(json.dumps(d, indent=2)); print("saved", CFG)

# ---- 1) discover the bridge on the LAN ----
def discover():
    try:
        hits = _get("https://discovery.meethue.com/")     # Philips N-UPnP cloud discovery
        if hits:
            ip = hits[0]["internalipaddress"]
            print("found bridge:", ip)
            cfg = load_cfg(); cfg["ip"] = ip; save_cfg(cfg); return ip
    except Exception as e:
        print("cloud discovery failed:", e)
    print("No bridge found. Make sure the square Hue Bridge v2 is on the same network,"
          " or set its IP manually:  python3 hue_bridge.py setip <ip>")
    return None

# ---- 2) pair (press the link button first) ----
def pair():
    cfg = load_cfg(); ip = cfg.get("ip")
    if not ip: ip = discover()
    if not ip: return
    # generate_clientkey=true also returns the PSK we need for Entertainment DTLS
    try:
        res = _post(f"https://{ip}/api", {"devicetype": APP_NAME, "generateclientkey": True})
    except Exception as e:
        print("pair request failed:", e); return
    if isinstance(res, list) and res and "error" in res[0]:
        print("PAIR ERROR:", res[0]["error"].get("description"),
              "\n→ press the Bridge's round link button, then re-run within 30s.")
        return
    s = res[0]["success"]
    cfg["appkey"] = s["username"]; cfg["clientkey"] = s["clientkey"]; save_cfg(cfg)
    print("paired ✓  appkey + clientkey stored.")

# ---- 3) list entertainment areas (CLIP API v2) ----
def areas():
    cfg = load_cfg(); ip, key = cfg.get("ip"), cfg.get("appkey")
    if not (ip and key): print("pair first."); return
    ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
    req = urllib.request.Request(f"https://{ip}/clip/v2/resource/entertainment_configuration",
                                 headers={"hue-application-key": key})
    data = json.load(urllib.request.urlopen(req, timeout=8, context=ctx))
    for a in data.get("data", []):
        print(f"  {a['id']}  ·  {a.get('metadata',{}).get('name','?')}  ·  {len(a.get('channels',[]))} channels")
    print("pick one:  python3 hue_bridge.py run --area <id>")

# ---- 4) the realtime streaming loop ----
def _entertainment_msg(channels):
    """Build one Hue Entertainment API v2 binary frame.
    channels = [(id, r16, g16, b16), ...]  (16-bit color per channel)."""
    msg = b"HueStream" + bytes([0x02,0x00, 0,0,0, 0x00, 0x00])  # ver2.0, no seq, RGB, no reason
    msg += b"\x00" * 36  # entertainment configuration id (UUID as ascii) — filled in run()
    for cid, r, g, b in channels:
        msg += struct.pack(">BHHH", cid, r, g, b)
    return msg

def _put(url, body, timeout=4):
    ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="PUT")
    return json.load(urllib.request.urlopen(req, timeout=timeout, context=ctx))

def _reachable_color_lights(ip, key):
    data = _get(f"https://{ip}/api/{key}/lights")
    out = []
    for lid, l in sorted(data.items(), key=lambda kv: int(kv[0])):
        if l.get("state", {}).get("reachable") and "hue" in l.get("state", {}):
            out.append(lid)
    return out

def run(area):
    """Closed loop, CLIP v1 REST mode (no extra deps): serve the feed endpoint and
    push the latest colors/level to every reachable color light at ~2.5Hz with soft
    transitions. The Entertainment DTLS path (25Hz, --area) stays a future upgrade:
      PSK handshake identity=appkey psk=bytes.fromhex(clientkey) to udp ip:2100
      (lib: python-mbedtls), then send _entertainment_msg() frames at 25Hz."""
    cfg = load_cfg(); ip, key = cfg.get("ip"), cfg.get("appkey")
    if not (ip and key):
        print("need ip + appkey (run discover/pair first)."); return
    if area:
        print(f"[hue] DTLS Entertainment mode for area {area} not built yet — using REST mode.")
    lights = _reachable_color_lights(ip, key)
    if not lights:
        print("[hue] no reachable color lights found — check the Bridge/lights."); return
    print(f"[hue] driving lights {lights} on {ip} (CLIP v1 REST @2.5Hz)")
    threading.Thread(target=_rest_loop, args=(ip, key, lights), daemon=True).start()
    _serve_feed()

# Latest frame from the JARVIS page; the REST loop consumes it.
_latest = {"colors": [[34,211,238]], "level": 0.0}
_latest_lock = threading.Lock()
_stats = {"pushes": 0, "last_push": 0.0, "lights": []}

def _rest_loop(ip, key, lights):
    _stats["lights"] = lights
    last_sent = {}
    while True:
        with _latest_lock:
            colors = list(_latest.get("colors") or [[34,211,238]])
            level = max(0.0, min(1.0, float(_latest.get("level") or 0)))
        for i, lid in enumerate(lights):
            r, g, b = colors[i % len(colors)]
            h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
            hue = int(h * 65535)
            sat = int(min(254, s * 254 + 30))
            # level breathes the brightness on top of the color's own value
            bri = int(min(254, max(25, (0.35 + 0.65 * level) * max(v, 0.35) * 254)))
            state = (hue, sat, bri)
            prev = last_sent.get(lid)
            # skip a push when nothing moved enough — keeps Zigbee traffic sane
            if prev and abs(prev[0]-hue) < 400 and abs(prev[1]-sat) < 6 and abs(prev[2]-bri) < 6:
                continue
            try:
                _put(f"https://{ip}/api/{key}/lights/{lid}/state",
                     {"on": True, "hue": hue, "sat": sat, "bri": bri, "transitiontime": 3})
                last_sent[lid] = state
                _stats["pushes"] += 1; _stats["last_push"] = time.time()
            except Exception:
                pass
        time.sleep(0.4)

def _serve_feed():
    from http.server import BaseHTTPRequestHandler, HTTPServer
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def _cors(self):
            self.send_header("Access-Control-Allow-Origin", "*")
        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            try:
                body = json.loads(self.rfile.read(n) or b"{}")
                with _latest_lock:
                    if "colors" in body: _latest["colors"] = body["colors"]
                    if "level" in body: _latest["level"] = body["level"]
            except Exception: pass
            self.send_response(200); self._cors(); self.end_headers()
            self.wfile.write(b'{"ok":true}')
        def do_GET(self):
            self.send_response(200); self._cors()
            self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "mode": "rest",
                "lights": _stats["lights"], "pushes": _stats["pushes"],
                "last_push": _stats["last_push"]}).encode())
        def do_OPTIONS(self):
            self.send_response(204); self._cors()
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            # Chrome Private Network Access preflight (HTTPS page -> 127.0.0.1)
            self.send_header("Access-Control-Allow-Private-Network", "true")
            self.end_headers()
    print("[hue] feed endpoint up on http://127.0.0.1:7878  (POST {colors:[[r,g,b],...],level:0..1})")
    HTTPServer(("127.0.0.1", 7878), H).serve_forever()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["discover","pair","areas","run","setip"])
    ap.add_argument("ip", nargs="?")
    ap.add_argument("--area")
    a = ap.parse_args()
    if a.cmd == "discover": discover()
    elif a.cmd == "pair": pair()
    elif a.cmd == "areas": areas()
    elif a.cmd == "run": run(a.area)
    elif a.cmd == "setip":
        cfg = load_cfg(); cfg["ip"] = a.ip; save_cfg(cfg)
