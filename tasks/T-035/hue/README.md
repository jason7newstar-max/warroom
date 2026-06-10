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
- ✅ discover / pair / areas = real (discover already found a bridge at **192.168.50.82**).
- ⏳ DTLS 25Hz streaming loop = scaffolded; to finish + test it needs:
  1. press-link pairing done (gets the clientkey),
  2. an Entertainment area created in the Hue app,
  3. a DTLS lib installed (`pip install python-mbedtls`), then fill the handshake +
     stream loop marked TODO in `hue_bridge.py:run()`.
- Two reactive modes to build on top: **screen-color follow** + **audio beat/volume** (FFT).

State is stored at `~/.phantom/hue.json`.
