#!/usr/bin/env python3
"""PHANTOM · NATIVE DSP combo generator. Writes ~/.phantom/presets.txt which the native
engine HOT-RELOADS — endless varied vocal chains, all native DSP = 2.7 ms (no real
plugins, no Apollo). Our own sounds, by ear; pick winners -> package & sell.

Mix (user 2026-06-07): **50% archetype** (coherent, usable vocal styles) + **50% wild**
(wide ranges / unexpected combos — to BREAK the established "good sound" conventions).

Sonic-order graph (fixed in the engine; the generator varies params/structure):
  HPF -> Comp -> de-mud EQ -> presence EQ -> air shelf -> low shelf -> saturation -> Delay -> Reverb

Line format (engine parser, 23 pipe-tokens): name + 22 floats:
  hp|compThr|ratio|att|rel|deMudHz|deMudG|presHz|presG|presQ|airHz|airG|lowHz|lowG|driveDb|makeupDb|revRoom|revWet|revDamp|delayMs|delayFb|delayMix

  python3 native_gen.py [N]      # N presets (default 12)
"""
import random, sys
from pathlib import Path

PH = Path.home() / ".phantom"; PH.mkdir(exist_ok=True)
ADJ = ["Velvet","Neon","Glass","Smoke","Amber","Cobalt","Ash","Halo","Dusk","Chrome",
       "Saffron","Onyx","Mist","Ember","Slate","Ivory","Crimson","Indigo","Frost","Gold",
       "Lunar","Sable","Coral","Jade","Rust","Pearl","Storm","Haze","Flux","Nova"]
NOUN = ["Throat","Air","Room","Tape","Bloom","Grit","Sheen","Body","Edge","Wash",
        "Pulse","Lift","Veil","Punch","Drift","Spark","Haze","Core","Bite","Halo",
        "Glow","Crush","Silk","Steel","Breath","Ash","Frost","Hollow","Ridge","Echo"]

def _j(v, amt): return round(v + random.uniform(-amt, amt), 2)

# coherent vocal-style archetypes (base params, jittered for variety)
ARCHETYPES = [
    # tag      hp   comp(thr,ratio,att,rel) deMud(hz,g) pres(hz,g,q)   air(hz,g)   low(hz,g) drv mk   rev(room,wet,damp)  dly(ms,fb,mix)
    ("pop",    95, (-22,4,3,80),   (350,-2.0), (3500,3.5,1.3), (9000,3.5), (200,0),  0, 3.0, (0.45,0.14,0.40), (0,0,0)),
    ("rnb",    80, (-20,3,8,120),  (300,-1.5), (4500,2.5,1.4), (11000,3.0),(180,2.5),0, 2.5, (0.60,0.22,0.30), (180,0.18,0.12)),
    ("rap",   100, (-24,6,2,60),   (300,-2.5), (3000,4.0,1.0), (9000,2.0), (200,0),  3, 4.0, (0.12,0.05,0.50), (110,0.10,0.09)),
    ("vintage",120,(-18,3,10,140), (350,0.0),  (2500,2.0,1.0), (9000,-3.0),(180,3.0),6, 2.5, (0.25,0.10,0.60), (0,0,0)),
    ("ballad", 80, (-21,3,5,100),  (350,-1.0), (4000,2.5,1.3), (10000,4.0),(180,1.5),0, 2.5, (0.80,0.30,0.25), (250,0.20,0.10)),
    ("modern", 90, (-23,5,3,70),   (300,-2.0), (3500,3.0,1.2), (12000,4.0),(200,0),  2, 3.0, (0.40,0.12,0.40), (140,0.12,0.08)),
]

def archetype():
    (_, hp, (cthr,cr,catt,crel), (dmhz,dmg), (preshz,presg,presq),
     (airhz,airg), (lowhz,lowg), drv, mk, (rr,rw,rd), (dms,dfb,dmix)) = random.choice(ARCHETYPES)
    return [hp, _j(cthr,2), cr, catt, crel, dmhz, _j(dmg,0.8), preshz, _j(presg,1), _j(presq,0.2),
            airhz, _j(airg,1.5), lowhz, _j(lowg,1), drv, _j(mk,0.5),
            _j(rr,0.08), _j(rw,0.04), _j(rd,0.1), dms, dfb, dmix]

def wild():
    """Break the rules — wide ranges, unexpected combos (the happy-accidents half)."""
    hp   = random.choice([60,70,80,90,100,120,140])
    cthr = round(random.uniform(-30,-8),1); cr = random.choice([1.5,2,3,4,6,8,10])
    catt = random.choice([0.5,1,3,8,20,40]); crel = random.choice([40,80,150,300,500])
    dmhz = random.choice([200,300,400,600,800]); dmg = round(random.uniform(-6,2),1)
    preshz = random.choice([2000,3000,4000,5000,7000]); presg = round(random.uniform(-4,10),1); presq = round(random.uniform(0.5,3.5),1)
    airhz = random.choice([5000,8000,10000,14000,16000]); airg = round(random.uniform(-10,10),1)
    lowhz = random.choice([100,150,200,300]); lowg = round(random.uniform(-4,6),1)
    drive = round(random.uniform(0,12),1); makeup = round(random.uniform(0,5),1)
    rroom = round(random.uniform(0.25,0.95),2); rwet = round(random.uniform(0.22,0.70),2); rdamp = round(random.uniform(0.05,0.9),2)
    if random.random() < 0.5: dms,dfb,dmix = random.choice([60,120,250,400,600]), round(random.uniform(0,0.5),2), round(random.uniform(0.05,0.3),2)
    else: dms,dfb,dmix = 0,0.0,0.0
    return [hp,cthr,cr,catt,crel,dmhz,dmg,preshz,presg,presq,airhz,airg,lowhz,lowg,drive,makeup,rroom,rwet,rdamp,dms,dfb,dmix]


def rnd_preset():
    f = archetype() if random.random() < 0.5 else wild()      # 50/50 coherent vs wild
    f[17] = 0.0   # DRY combo — reverb is a separate Space send (user's Aux-bus model)
    # NEW character dims so each combo is a DIFFERENT sound, not just EQ on the same voice:
    lp = random.choice([20000,20000,7000,5000,3500,2200,1600])   # ~30% dark / telephone / lo-fi
    ch = random.choice([0,0,0.4,0.55,0.7])                        # ~40% doubler / wide
    cd = round(random.uniform(0.25,0.65),2)
    if random.random() < 0.30: f[14] = round(random.uniform(8,20),1)   # crank drive (grit) sometimes
    f = f + [lp, round(ch,2), cd]
    name = f"{random.choice(ADJ)} {random.choice(NOUN)}"
    return name + "|" + "|".join(str(x) for x in f)


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    lines = [rnd_preset() for _ in range(n)]
    (PH / "presets.txt").write_text("\n".join(lines) + "\n")
    print(f"wrote {n} native presets (50% archetype / 50% wild) -> {PH/'presets.txt'}")
    for l in lines:
        print("  ", l.split("|")[0])
