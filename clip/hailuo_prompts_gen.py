#!/usr/bin/env python3
"""Gera clip/hailuo_prompts.json: prompt final por plano pro MiniMax Hailuo.

Mescla o motion_prompt da direção (clip/direction/out_segment_*.json) com a
trajetória de câmera do storyboard (clip/storyboard.json) convertida pra
sintaxe de comandos do Hailuo ([Push in], [Truck left], [Shake]...), que o
modelo segue com muito mais precisão que descrição livre.

  python3 clip/hailuo_prompts_gen.py          # escreve clip/hailuo_prompts.json
"""
import glob, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

CHAR = ("consistent character design: gaunt pale man, short dark slicked-back "
        "hair, charcoal-gray suit, loose crimson-red tie")
STYLE = "2D cel animation look, clean lineart, no morphing, no style drift"

SB = {s["file"]: s for s in json.load(open("clip/storyboard.json"))["shots"] if not s.get("src")}


def cam_commands(s):
    """Trajetória do storyboard -> comandos Hailuo (máx. 3 combinados)."""
    c = s.get("cam", {})
    z0, z1 = (c.get("z") or [1.06, 1.2])[:2]
    x0, y0 = c.get("c0") or [0.5, 0.5]
    x1, y1 = c.get("c1") or [0.5, 0.5]
    r0, r1 = c.get("rot") or [0, 0]
    cmds = []
    dz, dx, dy = z1 - z0, x1 - x0, y1 - y0
    if dz > 0.05:
        cmds.append("Push in")
    elif dz < -0.05:
        cmds.append("Pull out")
    if dx > 0.03:
        cmds.append("Truck right")
    elif dx < -0.03:
        cmds.append("Truck left")
    if dy > 0.03:
        cmds.append("Pedestal down")
    elif dy < -0.03:
        cmds.append("Pedestal up")
    if s.get("shake", 0) >= 0.55 and len(cmds) < 3:
        cmds.append("Shake")
    extra = ""
    if abs(r1 - r0) >= 2.0:
        extra = "slow dutch angle roll, "
    if not cmds:
        # nunca 100% estático: um push sutil mantém vida na imagem
        cmds = ["Push in"] if dz >= 0 else ["Pull out"]
    return "[" + ",".join(cmds[:3]) + "]", extra


def build():
    shots = {}
    for f in sorted(glob.glob("clip/direction/out_segment_*.json")):
        seg = json.load(open(f))
        for sh in seg["shots"]:
            shots[sh["file"]] = sh
    out = []
    for fname, sh in shots.items():
        sb = SB.get(fname)
        if sb is None:
            continue  # reuso (herda o clipe da plate de origem)
        cmd, extra = cam_commands(sb)
        mp = sh["motion_prompt"].strip().rstrip(".")
        # o prompt da direção já começa com "anime style," — injeta o comando
        # de câmera logo após o estilo, onde o Hailuo lê melhor
        mp = re.sub(r"^anime style,\s*", "", mp)
        prompt = (f"anime style, {cmd} {extra}{mp}. {CHAR}. {STYLE}."
                  if "charlie" in mp.lower() or "man" in mp.lower() or "he " in mp.lower()
                  else f"anime style, {cmd} {extra}{mp}. {STYLE}.")
        out.append({
            "file": fname,
            "prompt": prompt[:1990],
            "exit_state": sh.get("exit_state", ""),
            "handoff": sh.get("handoff", ""),
        })
    json.dump({"model": "MiniMax-Hailuo-2.3", "resolution": "768P", "duration": 6,
               "prompt_optimizer": False, "clips": out},
              open("clip/hailuo_prompts.json", "w"), indent=1, ensure_ascii=False)
    print(f"{len(out)} prompts -> clip/hailuo_prompts.json")


if __name__ == "__main__":
    build()
