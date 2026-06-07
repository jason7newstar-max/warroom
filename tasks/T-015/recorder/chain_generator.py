#!/usr/bin/env python3
"""PHANTOM · Vocal-Chain GENERATOR — combines the user's REAL VST3 plugins into
fresh vocal-chain "recipes" (no right answer; endless variety). Sonic-logic order:
EQ -> Comp -> de-ess/soothe -> saturation/color -> REVERB (separate, dry/wet 0-100%).

Only plugins verified to load headless are in the catalog. Reverb is a parallel
send blended at `reverb_wet` so the user gets a universal 0-100% space control
independent of the plugin (he wants wide/thick space to sing comfortably).

  list:    python3 chain_generator.py            # print a fresh batch of 5 recipes
  render:  python3 chain_generator.py <in.wav> [reverb_wet]   # apply recipe #1 to a take
"""
import os, sys, json, random

DIRS = ["/Library/Audio/Plug-Ins/VST3", os.path.expanduser("~/Library/Audio/Plug-Ins/VST3")]
def vst(name):
    for d in DIRS:
        p = os.path.join(d, name + ".vst3")
        if os.path.exists(p): return p
    return None

# verified-loading catalog (2026-06-07), by sonic role
CATALOG = {
    "eq":     ["FabFilter Pro-Q 4", "Neutron 3 Equalizer", "Ozone 9 Vintage EQ"],
    "comp":   ["FabFilter Pro-C 3", "Neutron 3 Compressor", "Ozone 9 Vintage Compressor", "AVOX PUNCH"],
    "deess":  ["FabFilter Pro-DS", "soothe2", "LANDR VoxDeEss"],
    "color":  ["Dirt", "Bite", "Ozone 9 Vintage Tape", "Neutron 3 Exciter"],
    "reverb": ["Raum", "Neoverb", "LANDR VoxVerb", "Crystalline"],
}
ADJ = ["Velvet", "Neon", "Glass", "Smoke", "Amber", "Cobalt", "Ash", "Halo", "Dusk", "Chrome",
       "Saffron", "Onyx", "Mist", "Ember", "Slate", "Ivory", "Crimson", "Indigo", "Frost", "Gold"]
NOUN = ["Throat", "Air", "Room", "Tape", "Bloom", "Grit", "Sheen", "Body", "Edge", "Wash",
        "Pulse", "Lift", "Veil", "Punch", "Drift", "Spark", "Haze", "Core", "Bite", "Halo"]

def make_recipe():
    chain = []
    if random.random() < 0.7: chain.append(("eq", random.choice(CATALOG["eq"])))
    chain.append(("comp", random.choice(CATALOG["comp"])))               # always
    if random.random() < 0.6: chain.append(("deess", random.choice(CATALOG["deess"])))
    if random.random() < 0.6: chain.append(("color", random.choice(CATALOG["color"])))
    rev = random.choice(CATALOG["reverb"])                               # always (separate dry/wet)
    name = f"{random.choice(ADJ)} {random.choice(NOUN)}"
    return {"name": name, "inserts": chain, "reverb": rev}

def batch(n=5):
    return [make_recipe() for _ in range(n)]

def build_board(recipe):
    """Build a live Pedalboard of the recipe's REAL plugins (inserts + reverb at chain end).
    For live monitoring the reverb uses its own internal mix (separate dry/wet blend is
    file-only). Loading takes ~1-2s/plugin."""
    from pedalboard import Pedalboard, load_plugin
    plugins = [load_plugin(vst(nm)) for _, nm in recipe["inserts"]]
    plugins.append(load_plugin(vst(recipe["reverb"])))
    return Pedalboard(plugins)


def render(recipe, in_wav, out_wav, reverb_wet=0.35):
    from pedalboard import Pedalboard, load_plugin
    from pedalboard.io import AudioFile
    import numpy as np
    insert_plugins = [load_plugin(vst(nm)) for _, nm in recipe["inserts"]]
    board = Pedalboard(insert_plugins)
    with AudioFile(in_wav) as f:
        audio = f.read(f.frames); sr = f.samplerate
    dry = board(audio, sr)
    rv = Pedalboard([load_plugin(vst(recipe["reverb"]))])
    wet = rv(dry, sr)
    n = min(dry.shape[-1], wet.shape[-1])
    mix = (1.0 - reverb_wet) * dry[..., :n] + reverb_wet * wet[..., :n]
    with AudioFile(out_wav, "w", sr, num_channels=mix.shape[0]) as f:
        f.write(mix)
    return out_wav

if __name__ == "__main__":
    random.seed()
    b = batch(5)
    if len(sys.argv) > 1 and sys.argv[1].endswith(".wav"):
        in_wav = sys.argv[1]
        wet = float(sys.argv[2]) if len(sys.argv) > 2 else 0.35
        r = b[0]
        out = in_wav.replace(".wav", "_combo.wav")
        print("RECIPE:", r["name"])
        print("  chain:", " -> ".join(nm for _, nm in r["inserts"]), "-> [REVERB]", r["reverb"], f"(wet {int(wet*100)}%)")
        render(r, in_wav, out, wet)
        print("RENDERED:", out)
    else:
        for i, r in enumerate(b, 1):
            chain = " -> ".join(nm for _, nm in r["inserts"])
            print(f"{i}. {r['name']:14}  {chain} -> [REVERB] {r['reverb']}")
