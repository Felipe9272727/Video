#!/usr/bin/env python3
"""Gera material de QC pros agentes revisores:
  - clip/qc/strip_<stem>.jpg  : 5 frames do clipe em linha (julga movimento/consistência)
  - clip/qc/seam_<a>__<b>.jpg : último frame de A + primeiro de B (julga a emenda/continuidade)

  python3 clip/qc_strips.py strips            # tiras de todos os clipes existentes
  python3 clip/qc_strips.py seams            # costuras entre planos consecutivos (storyboard)
  python3 clip/qc_strips.py all
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
SHOTS = json.load(open("clip/storyboard.json"))["shots"]
os.makedirs("clip/qc", exist_ok=True)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def motion_path(shot):
    """caminho do mp4 que ESTE plano usa (próprio ou da plate de origem em reuso)."""
    for base in [shot["file"], shot.get("src") or ""]:
        if not base: continue
        p = os.path.join("clip/motion", os.path.splitext(base)[0] + ".mp4")
        if os.path.exists(p) and os.path.getsize(p) > 300000:
            return p, bool(shot.get("flip")) and base == shot.get("src")
    return None, False

def frames(path, n, flip=False):
    """extrai n frames uniformes como arrays RGB (320px de largura)."""
    # duração
    out = []
    for i in range(n):
        f = (i + 0.5) / n
        tmp = f"/tmp/_qcf.jpg"
        subprocess.run([FF, "-loglevel", "error", "-ss", f"{f*2.9:.2f}", "-i", path,
                        "-frames:v", "1", "-vf", "scale=320:-1", "-y", tmp],
                       check=False)
        if os.path.exists(tmp):
            im = Image.open(tmp).convert("RGB")
            if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT)
            out.append(im)
    return out

def label(im, text):
    d = ImageDraw.Draw(im)
    try: fnt = ImageFont.truetype(FONT, 16)
    except Exception: fnt = ImageFont.load_default()
    d.rectangle([0, 0, im.width, 20], fill=(0, 0, 0))
    d.text((4, 2), text, fill=(255, 230, 120), font=fnt)
    return im

def strip_for(shot):
    p, flip = motion_path(shot)
    if not p: return None
    fs = frames(p, 5, flip)
    if not fs: return None
    w = sum(f.width for f in fs); h = fs[0].height
    strip = Image.new("RGB", (w, h + 20), (20, 20, 20))
    x = 0
    for f in fs:
        strip.paste(f, (x, 20)); x += f.width
    label(strip, f"{shot['file']}  t={shot['t0']:.0f}-{shot['t1']:.0f}s  ({'reuse '+shot['src'] if shot.get('src') else 'own'})")
    outp = f"clip/qc/strip_{os.path.splitext(shot['file'])[0]}.jpg"
    strip.save(outp, quality=85)
    return outp

def seam_for(a, b):
    pa, fa = motion_path(a); pb, fb = motion_path(b)
    if not pa or not pb: return None
    la = frames(pa, 5, fa)[-1:] ; fbf = frames(pb, 5, fb)[:1]
    if not la or not fbf: return None
    la, fbf = la[0], fbf[0]
    w = la.width + fbf.width + 6; h = max(la.height, fbf.height)
    seam = Image.new("RGB", (w, h + 20), (20, 20, 20))
    seam.paste(la, (0, 20)); seam.paste(fbf, (la.width + 6, 20))
    tr = ""
    try:
        tm = {t["i"]: t for t in json.load(open("clip/direction/transition_map.json"))["transitions"]}
        idx = [s["file"] for s in SHOTS].index(b["file"])
        tr = tm.get(idx, {}).get("in", "")
    except Exception: pass
    label(seam, f"FIM {a['file']}  |  INICIO {b['file']}   [transicao: {tr}]")
    outp = f"clip/qc/seam_{os.path.splitext(a['file'])[0]}__{os.path.splitext(b['file'])[0]}.jpg"
    seam.save(outp, quality=85)
    return outp

def run(files=None):
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    made = []
    if mode in ("strips", "all"):
        for s in SHOTS:
            if files and s["file"] not in files: continue
            r = strip_for(s)
            if r: made.append(r)
    if mode in ("seams", "all"):
        for i in range(len(SHOTS) - 1):
            a, b = SHOTS[i], SHOTS[i + 1]
            if files and a["file"] not in files and b["file"] not in files: continue
            r = seam_for(a, b)
            if r: made.append(r)
    print(f"gerados {len(made)} arquivos de QC em clip/qc/")

if __name__ == "__main__":
    run()
