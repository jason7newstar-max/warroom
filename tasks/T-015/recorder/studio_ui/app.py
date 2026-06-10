#!/usr/bin/env python3
"""PHANTOM — temporary studio UI (T-015). A dark, Logic-ish web front-end over the
sounddevice recorder: live level meter, record/stop, take list, one-click mix chain.

Run:  ../.venv/bin/python app.py    then open http://127.0.0.1:7860
"""
from __future__ import annotations
import io, os, threading, time, wave
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf
from flask import Flask, jsonify, send_file, send_from_directory, abort

SR = 48000
TAKES = Path(__file__).parent / "takes"
TAKES.mkdir(exist_ok=True)

# NATIVE mode: the JUCE engine owns the Duet (low-latency monitor + 5 templates).
# This UI becomes a control surface — it writes a control file the engine polls and
# reads a status file the engine writes. (No audio device opened here, so no Duet
# contention with the native engine.)
NATIVE = os.environ.get("PHANTOM_NATIVE", "") == "1"
PHDIR = Path.home() / ".phantom"; PHDIR.mkdir(exist_ok=True)
CTRL_F = PHDIR / "control.txt"; STAT_F = PHDIR / "status.txt"
PRESET_NAMES = ["POP SHEEN", "RAP UPFRONT", "R&B SILK", "STAGE BIG", "VINTAGE WARM"]

# Real-plugin combo generator (combines the user's actual VST3 plugins).
import sys as _sys
_sys.path.insert(0, str(Path(__file__).parent.parent))
import chain_generator
RECIPES = chain_generator.batch(5)

def recipe_view():
    out = []
    for i, r in enumerate(RECIPES):
        chain = " → ".join(nm for _, nm in r["inserts"]) + " → 〔rev〕" + r["reverb"]
        out.append({"i": i, "name": r["name"], "chain": chain})
    return out

def write_ctrl(**kw):
    cur = {}
    if CTRL_F.exists():
        for ln in CTRL_F.read_text().splitlines():
            if "=" in ln:
                k, v = ln.split("=", 1); cur[k] = v
    cur.update({k: str(v) for k, v in kw.items()})
    CTRL_F.write_text("".join(f"{k}={v}\n" for k, v in cur.items()))

def read_stat():
    d = {}
    if STAT_F.exists():
        for ln in STAT_F.read_text().splitlines():
            if "=" in ln:
                k, v = ln.split("=", 1); d[k] = v
    return d

# ---- pick the Duet for input + output ----
def pick_devices():
    inp = out = None
    for i, d in enumerate(sd.query_devices()):
        n = d["name"].lower()
        if "duet" in n and d["max_input_channels"] > 0 and inp is None:
            inp = i
        if "duet" in n and d["max_output_channels"] > 0 and out is None:
            out = i
    return (inp if inp is not None else sd.default.device[0],
            out if out is not None else sd.default.device[1])

DEVICE_IN, DEVICE_OUT = pick_devices()
DEVICE_NAME = sd.query_devices(DEVICE_IN)["name"]

# ---- shared audio state ----
_lock = threading.Lock()
_recording = False
_monitor = False
_frames: list[np.ndarray] = []
_peak_db = -90.0

# live monitor chain = "CLA STAGE VOCAL" — compressed, upfront, bright, stage reverb.
# (CLA Vocals-style preset.) The RECORDED file stays DRY (先干后湿).
from pedalboard import (Pedalboard as _PB, HighpassFilter as _HP, Compressor as _Cp,
                        PeakFilter as _PK, HighShelfFilter as _HS, Gain as _Gn, Reverb as _Rv)

def _cla_stage():
    return _PB([
        _HP(cutoff_frequency_hz=90),                                   # clean lows
        _Cp(threshold_db=-22, ratio=4.0, attack_ms=3, release_ms=80),  # CLA-style squeeze
        _PK(cutoff_frequency_hz=350, gain_db=-2.0, q=1.0),             # de-mud -> upfront
        _PK(cutoff_frequency_hz=4000, gain_db=3.0, q=1.2),             # presence / forward
        _HS(cutoff_frequency_hz=8000, gain_db=3.5),                    # air / bright
        _Gn(gain_db=3.0),                                             # upfront makeup
        _Rv(room_size=0.82, damping=0.25, wet_level=0.28,             # BIG church space
            dry_level=0.82, width=1.0),
    ])

_mon_board = _cla_stage()
_live_board = None     # when set (non-native mode), live-monitor through REAL plugins
_live_lock = threading.Lock()


def _duplex_cb(indata, outdata, frames, t, status):
    global _peak_db
    mono = indata[:, 0]
    pk = float(np.abs(mono).max()) if mono.size else 0.0
    _peak_db = 20 * np.log10(max(pk, 1e-9))
    if _recording:
        with _lock:
            _frames.append(mono.copy().reshape(-1, 1))
    if _monitor:
        board = _live_board if _live_board is not None else _mon_board
        try:
            wet = board(mono, SR, reset=False)
        except Exception:
            wet = mono
        outdata[:, 0] = wet
        if outdata.shape[1] > 1:
            outdata[:, 1] = wet
    else:
        outdata.fill(0)


def _input_cb(indata, frames, t, status):
    global _peak_db
    pk = float(np.abs(indata).max()) if indata.size else 0.0
    _peak_db = 20 * np.log10(max(pk, 1e-9))
    if _recording:
        with _lock:
            _frames.append(indata.copy())


if NATIVE:
    MONITOR_OK = True          # the JUCE native engine owns the device, not this app
else:
    try:  # duplex (enables live wet monitoring)
        _stream = sd.Stream(samplerate=SR, blocksize=512, device=(DEVICE_IN, DEVICE_OUT),
                            dtype="float32", channels=(1, 2), latency="low", callback=_duplex_cb)
        _stream.start()
        MONITOR_OK = True
    except Exception as e:  # fall back to record-only so the app still works
        print("duplex monitor unavailable, input-only:", e)
        _stream = sd.InputStream(samplerate=SR, blocksize=1024, device=DEVICE_IN,
                                 dtype="float32", channels=1, callback=_input_cb)
        _stream.start()
        MONITOR_OK = False

app = Flask(__name__, static_folder=None)


@app.route("/")
def index():
    return send_from_directory(Path(__file__).parent, "index.html")


@app.route("/daw")
def daw():
    return send_from_directory(Path(__file__).parent, "daw.html")


@app.route("/api/save_comp", methods=["POST"])
def save_comp():
    """Persist a comped / punched-in vocal (WAV bytes posted from the DAW view)."""
    from flask import request
    raw = request.get_data()
    if not raw:
        abort(400)
    name = request.args.get("name") or f"take-{time.strftime('%H%M%S')}_comp.wav"
    if not name.endswith(".wav"):
        name += ".wav"
    (TAKES / name).write_bytes(raw)
    info = sf.info(str(TAKES / name))
    return jsonify(ok=True, name=name, duration=round(info.duration, 2))


@app.route("/stage.png")
def stage():
    return send_from_directory(Path(__file__).parent, "stage.png")


@app.route("/fx/<path:fname>")
def fx(fname):
    return send_from_directory(Path(__file__).parent / "fx", fname)


@app.route("/api/meter")
def meter():
    if NATIVE:
        st = read_stat()
        return jsonify(peak_db=float(st.get("peak", -90)), recording=False,
                       device="Duet · native ~2.7ms", monitor=st.get("monitor", "0") == "1",
                       monitor_ok=True, native=True, preset=int(st.get("preset", 0)),
                       preset_name=st.get("name", ""), callbacks=int(st.get("callbacks", 0)),
                       engine_up=STAT_F.exists())
    return jsonify(peak_db=round(_peak_db, 1), recording=_recording, device=DEVICE_NAME,
                   monitor=_monitor, monitor_ok=MONITOR_OK, native=False)


@app.route("/api/monitor", methods=["POST"])
def monitor():
    global _monitor
    from flask import request
    on = bool((request.get_json(silent=True) or {}).get("on", False))
    if NATIVE:
        write_ctrl(monitor=1 if on else 0)
        return jsonify(ok=True, monitor=on, monitor_ok=True)
    _monitor = on and MONITOR_OK
    return jsonify(ok=True, monitor=_monitor, monitor_ok=MONITOR_OK)


def native_preset_names():
    pf = PHDIR / "presets.txt"
    names = []
    if pf.exists():
        for ln in pf.read_text().splitlines():
            if "|" in ln and not ln.strip().startswith("#"):
                names.append(ln.split("|")[0].strip())
    return names or PRESET_NAMES


@app.route("/api/presets")
def presets_list():
    return jsonify(names=native_preset_names())


@app.route("/api/preset", methods=["POST"])
def preset():
    from flask import request
    names = native_preset_names()
    idx = max(0, min(len(names) - 1, int((request.get_json(silent=True) or {}).get("preset", 0))))
    if NATIVE:
        write_ctrl(preset=idx)
    return jsonify(ok=True, preset=idx, name=names[idx])


@app.route("/api/newnative", methods=["POST"])
def newnative():
    import subprocess
    subprocess.run(["python3", str(Path(__file__).parent.parent / "native_gen.py"), "12"])
    return jsonify(ok=True, names=native_preset_names())

@app.route("/api/gate", methods=["POST"])
def gate():
    from flask import request
    db = float((request.get_json(silent=True) or {}).get("db", -90))
    if NATIVE: write_ctrl(gate=db)
    return jsonify(ok=True, db=db)

@app.route("/api/revwet", methods=["POST"])
def revwet():
    from flask import request
    pct = float((request.get_json(silent=True) or {}).get("pct", -1))
    if NATIVE: write_ctrl(revwet=pct)
    return jsonify(ok=True, pct=pct)


FAVES = PHDIR / "favorites.txt"

@app.route("/api/like", methods=["POST"])
def like():
    # Save a combo's full params permanently (favorites.txt) — the keepers, for curating into a product.
    from flask import request
    i = int((request.get_json(silent=True) or {}).get("preset", 0))
    pf = PHDIR / "presets.txt"
    if not pf.exists():
        return jsonify(ok=False, error="no presets")
    lines = [ln for ln in pf.read_text().splitlines() if "|" in ln]
    if not (0 <= i < len(lines)):
        return jsonify(ok=False, error="bad index")
    line = lines[i]
    existing = FAVES.read_text().splitlines() if FAVES.exists() else []
    if line not in existing:
        existing.append(line)
        FAVES.write_text("\n".join(existing) + "\n")
        # also append a human-readable, timestamped product record (the keeper template)
        import datetime as _dt
        tk = line.split("|")
        names = ["hp","compThr","ratio","att","rel","deMudHz","deMudG","presHz","presG","presQ",
                 "airHz","airG","lowHz","lowG","driveDb","makeupDb","revRoom","revWet","revDamp","delayMs","delayFb","delayMix"]
        params = ", ".join(f"{k}={v}" for k,v in zip(names, tk[1:]))
        with open(PHDIR / "favorites_log.txt","a") as lf:
            lf.write(f"[{_dt.datetime.now():%Y-%m-%d %H:%M}] {tk[0]} | {params}\n")
    return jsonify(ok=True, name=line.split("|")[0], count=len([l for l in existing if "|" in l]))


@app.route("/api/favorites")
def favorites():
    names = []
    if FAVES.exists():
        for ln in FAVES.read_text().splitlines():
            if "|" in ln:
                names.append(ln.split("|")[0].strip())
    return jsonify(names=names, count=len(names))


@app.route("/api/loadfaves", methods=["POST"])
def loadfaves():
    # Make the favorites the active bank (so you can A/B only your keepers, live at 2.7ms).
    if FAVES.exists() and FAVES.read_text().strip():
        (PHDIR / "presets.txt").write_text(FAVES.read_text())
    return jsonify(ok=True, names=native_preset_names())


@app.route("/api/record", methods=["POST"])
def record():
    global _recording
    if NATIVE:                       # the native engine records dry (monitor stays wet)
        write_ctrl(record=1)
        return jsonify(ok=True)
    with _lock:
        _frames.clear()
    _recording = True
    return jsonify(ok=True)


@app.route("/api/stop", methods=["POST"])
def stop():
    global _recording
    if NATIVE:
        write_ctrl(record=0)
        time.sleep(0.25)             # let the engine flush the WAV
        st = read_stat()
        name = st.get("last_take", "")
        return jsonify(ok=True, name=name, duration=0, peak_db=0, native=True)
    _recording = False
    time.sleep(0.05)
    with _lock:
        data = np.concatenate(_frames) if _frames else np.zeros((1, 1), np.float32)
    name = f"take-{time.strftime('%H%M%S')}.wav"
    sf.write(TAKES / name, data, SR)
    dur = len(data) / SR
    pk = 20 * np.log10(max(float(np.abs(data).max()), 1e-9))
    return jsonify(ok=True, name=name, duration=round(dur, 1), peak_db=round(pk, 1))


@app.route("/api/takes")
def takes():
    out = []
    for w in sorted(TAKES.glob("take-*.wav"), reverse=True):
        if w.stem.endswith("_mixed"):
            continue
        info = sf.info(str(w))
        mixed = (TAKES / f"{w.stem}_mixed.wav").exists()
        out.append(dict(name=w.name, duration=round(info.duration, 1), mixed=mixed))
    return jsonify(takes=out)


@app.route("/api/audio/<path:fname>")
def audio(fname):
    f = TAKES / fname
    if not f.exists():
        abort(404)
    return send_file(str(f), mimetype="audio/wav")


@app.route("/api/recipes")
def recipes():
    return jsonify(recipes=recipe_view())


@app.route("/api/newbatch", methods=["POST"])
def newbatch():
    global RECIPES, _live_board
    RECIPES = chain_generator.batch(5)
    _live_board = None
    return jsonify(ok=True, recipes=recipe_view())


@app.route("/api/livecombo", methods=["POST"])
def livecombo():
    # Load a recipe's REAL plugins into the LIVE monitor (non-native Python mode only).
    global _live_board
    from flask import request
    if NATIVE:
        return jsonify(ok=False, live=False, reason="native-mode: live real-plugin monitor needs non-native PHANTOM")
    i = max(0, min(len(RECIPES) - 1, int((request.get_json(silent=True) or {}).get("recipe", 0))))
    import traceback
    with _live_lock:                       # serialize loads (rapid clicks queue)
        try:
            _live_board = None             # stop processing the OLD plugins first so we don't
            time.sleep(0.06)               # instantiate a new VST while another VST is running
            _live_board = chain_generator.build_board(RECIPES[i])
            return jsonify(ok=True, live=True, name=RECIPES[i]["name"])
        except Exception as e:
            traceback.print_exc()
            return jsonify(ok=False, live=False, error=str(e)[:160])


@app.route("/api/process/<path:fname>", methods=["POST"])
def process(fname):
    src = TAKES / fname
    if not src.exists():
        abort(404)
    from flask import request
    fx = request.get_json(silent=True) or {}
    # If a generated REAL-PLUGIN recipe is chosen, render the take through the user's
    # actual VST3 plugins (separate reverb dry/wet) instead of the built-in DSP.
    if fx.get("recipe") is not None:
        i = max(0, min(len(RECIPES) - 1, int(fx["recipe"])))
        wet = float(fx.get("reverb_wet", 0.35))
        dst = TAKES / f"{src.stem}_mixed.wav"
        chain_generator.render(RECIPES[i], str(src), str(dst), reverb_wet=wet)
        return jsonify(ok=True, name=dst.name, recipe=RECIPES[i]["name"])
    # plain-language effects -> DSP. Order: clean -> punch -> warmth -> air -> space.
    from pedalboard import (Pedalboard, HighpassFilter, Compressor, Gain,
                            LowShelfFilter, HighShelfFilter, Distortion, Reverb)
    from pedalboard.io import AudioFile
    chain = [HighpassFilter(cutoff_frequency_hz=80)]            # always: clean rumble
    if fx.get("punch", True):
        chain += [Compressor(threshold_db=-18, ratio=3.0, attack_ms=5, release_ms=120),
                  Gain(gain_db=2.0)]
    if fx.get("warmth", False):
        chain += [LowShelfFilter(cutoff_frequency_hz=200, gain_db=3.0),
                  Distortion(drive_db=4.0)]
    if fx.get("air", False):
        chain += [HighShelfFilter(cutoff_frequency_hz=8000, gain_db=4.0)]
    if fx.get("space", True):
        chain += [Reverb(room_size=0.25, wet_level=0.12, dry_level=0.88, width=0.9)]
    board = Pedalboard(chain)
    with AudioFile(str(src)) as f:
        audio_data = f.read(f.frames); sr = f.samplerate
    out = board(audio_data, sr)
    dst = TAKES / f"{src.stem}_mixed.wav"
    with AudioFile(str(dst), "w", sr, num_channels=out.shape[0]) as f:
        f.write(out)
    return jsonify(ok=True, name=dst.name)


if __name__ == "__main__":
    print(f"PHANTOM studio UI · in={DEVICE_NAME} dev({DEVICE_IN}->{DEVICE_OUT}) monitor={MONITOR_OK} · http://127.0.0.1:7860")
    app.run(host="127.0.0.1", port=7860, threaded=True)
