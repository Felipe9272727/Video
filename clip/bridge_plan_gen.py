#!/usr/bin/env python3
"""Gera clip/direction/bridge_plan.json: quais emendas viram ponte FLF
(primeiro+último frame via Wan 2.2) e com que prompt.

Critério: toda motion_continue e match_cut, e dissolves >= 0.35s — são as
emendas onde "gerar o meio" elimina a sensação de corte. Flash/whip/dip/cut
ficam com a transição procedural do assemble (já é a linguagem certa).

Cada ponte carrega o PLATE REAL + flip de cada lado (planos reusados/espelhados
não têm .jpg próprio; apontam pro src). O nome de saída continua sendo a
fronteira lógica <a>__<b> pra o assemble achar.

  python3 clip/bridge_plan_gen.py
"""
import glob, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

SB = json.load(open("clip/storyboard.json"))["shots"]
TM = json.load(open("clip/direction/transition_map.json"))["transitions"]

DIR = {}
for f in sorted(glob.glob("clip/direction/out_segment_*.json")):
    for sh in json.load(open(f))["shots"]:
        DIR[sh["file"]] = sh

stem = lambda s: os.path.splitext(s["file"])[0]
plate = lambda s: os.path.splitext(s.get("src") or s["file"])[0]   # arquivo real

# preserva prompts de morph já escritos pela direção (Haiku), por (a,b)
PREV = {}
if os.path.exists("clip/direction/bridge_plan.json"):
    for b in json.load(open("clip/direction/bridge_plan.json")).get("bridges", []):
        PREV[(b["a"], b["b"])] = b.get("prompt")


def pick(tr):
    t, d = tr["in"], float(tr.get("dur") or 0)
    return t in ("motion_continue", "match_cut") or (t == "dissolve" and d >= 0.35)


bridges = []
for tr in TM:
    i = tr["i"]
    if i == 0 or not pick(tr):
        continue
    a, b = SB[i - 1], SB[i]
    da = DIR.get(a.get("src") or a["file"], {})
    db = DIR.get(b.get("src") or b["file"], {})
    bridges.append({
        "i": i, "a": stem(a), "b": stem(b), "type": tr["in"], "window": tr["dur"],
        "pa": plate(a), "fa": bool(a.get("flip")),      # plate real + flip (lado A)
        "pb": plate(b), "fb": bool(b.get("flip")),      # plate real + flip (lado B)
        "note_pt": tr.get("note", ""),
        "exit_a": da.get("exit_state", ""), "handoff_a": da.get("handoff", ""),
        "entry_b": (db.get("motion_prompt", "")[:200]),
        "prompt": PREV.get((stem(a), stem(b))) or
                  ("anime style, one continuous cinematic camera move morphs the first "
                   "scene into the second with no cut, coherent motion, "
                   "2D cel animation look, no flicker"),
    })

json.dump({"model": "Wan-AI/Wan2.2-TI2V-5B-Diffusers", "resolution": "768P", "duration": 6,
           "prompt_optimizer": False, "bridges": bridges},
          open("clip/direction/bridge_plan.json", "w"), indent=1, ensure_ascii=False)
tt = {}
for br in bridges:
    tt[br["type"]] = tt.get(br["type"], 0) + 1
print(f"{len(bridges)} pontes -> clip/direction/bridge_plan.json  {tt}")
