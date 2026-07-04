#!/usr/bin/env python3
"""QC de movimento dos clipes (image-to-video).

Mede movimento por diferença de pixels entre frames amostrados e classifica
cada clipe. O ponto-chave: usa um PISO POR PLANO (clip/direction/motion_tiers.json,
tier calm/medium/high/extreme) — assim um close contemplativo não é marcado como
"estático" pela mesma régua de uma batida de carro. Sem o arquivo de tiers, cai
num piso global.

  python3 clip/qc_motion.py            # relatório + clip/qc/motion_report.json
  python3 clip/qc_motion.py --regen    # imprime só a lista de stems a regerar
"""
import json, os, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG = "ffmpeg"

# piso de movimento (score 0-100) por tier — abaixo disso o clipe está estático
# DEMAIS pro que a cena pede e entra na lista de regeração
TIER_FLOOR = {"calm": 4.0, "medium": 9.0, "high": 16.0, "extreme": 26.0}
DEFAULT_TIER = "medium"

try:
    TIERS = json.load(open("clip/direction/motion_tiers.json"))["tiers"]
except Exception:
    TIERS = {}


def duration(mp4):
    r = subprocess.run([FFMPEG, "-i", mp4], capture_output=True, text=True)
    for line in r.stderr.split("\n"):
        if "Duration:" in line:
            p = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = p.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return None


def extract(mp4, n=8):
    d = duration(mp4)
    if not d or d <= 0:
        return []
    out = []
    with tempfile.TemporaryDirectory() as td:
        for i, ts in enumerate(np.linspace(0, d * 0.95, n)):
            op = os.path.join(td, f"f{i}.png")
            subprocess.run([FFMPEG, "-v", "error", "-ss", str(ts), "-i", mp4,
                            "-vf", "scale=320:180", "-vframes", "1", op],
                           capture_output=True)
            if os.path.exists(op):
                out.append(np.asarray(Image.open(op).convert("RGB")))
    return out


def analyze(frames):
    if len(frames) < 2:
        return dict(score=0.0, frozen=100.0, artifact=None)
    diffs = [np.mean(np.abs(frames[i].astype(np.float32) - frames[i + 1].astype(np.float32))) / 255 * 100
             for i in range(len(frames) - 1)]
    md, sd = float(np.mean(diffs)), float(np.std(diffs))
    f0 = frames[0].astype(np.float32)
    frozen = sum(np.mean(np.abs(f.astype(np.float32) - f0)) / 255 * 100 < 2.0
                 for f in frames[1:]) / (len(frames) - 1) * 100
    art = None
    if sd > md * 1.5 and md > 3:
        art = "flicker"
    elif max(diffs) > md * 3 and md > 3:
        art = "morphing"
    return dict(score=min(md, 100.0), frozen=float(frozen), artifact=art)


def verdict(stem, a):
    tier = TIERS.get(stem, {}).get("tier", DEFAULT_TIER)
    floor = TIER_FLOOR.get(tier, TIER_FLOOR[DEFAULT_TIER])
    if a["artifact"]:
        return "ARTEFATO", tier, floor
    if a["score"] < floor or a["frozen"] > 40:
        return ("ESTATICO" if a["score"] < floor * 0.5 else "FRACO"), tier, floor
    return "OK", tier, floor


def main():
    mp4s = sorted(Path("clip/motion").glob("*.mp4"))
    if not mp4s:
        print("Nenhum clipe em clip/motion/ ainda.")
        return
    rows = []
    for p in mp4s:
        a = analyze(extract(str(p)))
        v, tier, floor = verdict(p.stem, a)
        rows.append(dict(stem=p.stem, score=round(a["score"], 1), frozen=round(a["frozen"], 1),
                         artifact=a["artifact"], tier=tier, floor=floor, verdict=v))
        if "--regen" not in sys.argv:
            print(f"{p.stem:<22} score={a['score']:5.1f} tier={tier:<7} piso={floor:<4} -> {v}")
    regen = [r["stem"] for r in rows if r["verdict"] in ("ESTATICO", "FRACO", "ARTEFATO")]
    os.makedirs("clip/qc", exist_ok=True)
    json.dump({"clips": rows, "regen": regen}, open("clip/qc/motion_report.json", "w"), indent=1)
    if "--regen" in sys.argv:
        print(" ".join(regen))
    else:
        print("\n" + "=" * 60)
        print(f"{len(rows)} clipes | OK: {sum(r['verdict']=='OK' for r in rows)} | "
              f"a regerar: {len(regen)}")
        if regen:
            print("REGERAR:", " ".join(regen))
        print("relatório -> clip/qc/motion_report.json")


if __name__ == "__main__":
    main()
