# T-035 Hue bridge — setup

Drives Philips Hue lights to sync with the JARVIS console (screen color + audio).
Runs locally; the web page feeds it colors/level. Browsers can't do UDP/DTLS, so this
local service does the real-time Hue **Entertainment API** streaming.

## One-time setup (needs the Hue Bridge v2 + lights on the LAN)
```
python3 hue_bridge.py discover          # finds the bridge IP (auto-saved)
# → press the round LINK button on top of the Bridge, then within 30s:
python3 hue_bridge.py pair              # saves app key + clientkey (DTLS PSK)
python3 hue_bridge.py areas             # list "entertainment areas" (make one in the Hue app first)
python3 hue_bridge.py run --area <id>   # activate + start the feed endpoint
```
The JARVIS page then POSTs `{ "colors": [[r,g,b],...], "level": 0..1 }` to
`http://127.0.0.1:7878` (or we wire a WebSocket later). Colors come from
`window.jarvisColors()`, level from `window.jarvisAudioLevel()`.

## Status (2026-06-10)
- ✅ discover / pair = done (bridge **192.168.50.82**, appkey + clientkey stored).
- ✅ **CLOSED LOOP LIVE (REST mode)**: `python3 hue_bridge.py run` now auto-detects
  reachable color lights (5 Long, 6/7 floor, 9 lightstrip), serves the feed on
  `http://127.0.0.1:7878`, and drives the lights at ~2.5Hz with soft transitions —
  colors distributed round-robin across lights, `level` breathes the brightness.
  The JARVIS console (`tasks/T-035/console/`) POSTs `{colors, level}` every 450ms
  and shows BRIDGE LINK: ONLINE + a real HUE_SYNC gauge. Verified end-to-end
  2026-06-10: page → bridge → physical lights took cyan/gold/purple.
- ⏳ Entertainment DTLS 25Hz mode = future upgrade (needs an Entertainment area in
  the Hue app + `pip install python-mbedtls`; notes in `hue_bridge.py:run()`).
- `screen_follow.py` = bonus mode: screen-capture dominant color → lights (REST v1).

State is stored at `~/.phantom/hue.json`.
