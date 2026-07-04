#!/usr/bin/env python3
"""Monta e publica o dataset do Kaggle com os prompts NOVOS (direção + QC) e
as 31 pontes do bridge_plan, depois (re)lança o kernel charlie-gen completo.

Pré-requisito: pip install kaggle + credencial (~/.kaggle/kaggle.json ou
KAGGLE_USERNAME/KAGGLE_KEY no env).

  python3 clip/kaggle/build_dataset.py            # dataset + kernel push
  python3 clip/kaggle/build_dataset.py --dataset-only
"""
import glob, importlib.util, json, os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)

USER = "felipe028382072"
DS_ID = f"{USER}/charlie-inferno-plates"

# converte os prompts revisados (sintaxe Hailuo) pra linguagem natural do Wan
spec = importlib.util.spec_from_file_location("mw", "clip/modelscope_wan.py")
mw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mw)

NEG = ("worst quality, static, still image, blurred, distorted, watermark, text, "
       "subtitles, extra limbs, deformed face, flickering, morphing, 3d render")

D = "/tmp/charlie_dataset"
shutil.rmtree(D, ignore_errors=True)
os.makedirs(D)
for p in sorted(glob.glob("clip/shots/*.jpg")):
    shutil.copy(p, D)

prompts = {os.path.splitext(f)[0]: mw.wan_prompt(f) for f in sorted(mw.CLIPS)}
bridges = [{"a": b["a"], "b": b["b"], "prompt": b["prompt"]}
           for b in json.load(open("clip/direction/bridge_plan.json"))["bridges"]]
json.dump({"neg": NEG, "prompts": prompts, "bridges": bridges},
          open(f"{D}/prompts.json", "w"), indent=1, ensure_ascii=False)
json.dump({"title": "charlie-inferno-plates", "id": DS_ID, "licenses": [{"name": "other"}]},
          open(f"{D}/dataset-metadata.json", "w"))
print(f"dataset: {len(prompts)} prompts, {len(bridges)} pontes, "
      f"{len(glob.glob(D + '/*.jpg'))} plates em {D}")

r = subprocess.run(["kaggle", "datasets", "version", "-p", D,
                    "-m", "prompts direção+QC, 31 pontes bridge_plan"],
                   capture_output=True, text=True)
print(r.stdout[-400:], r.stderr[-400:])
if "Dataset not found" in (r.stdout + r.stderr) or "404" in (r.stdout + r.stderr):
    r = subprocess.run(["kaggle", "datasets", "create", "-p", D], capture_output=True, text=True)
    print("create:", r.stdout[-400:], r.stderr[-400:])

if "--dataset-only" not in sys.argv:
    # kernel completo (55 clipes + pontes) no lugar do de validação
    kd = "/tmp/charlie_kernel"
    shutil.rmtree(kd, ignore_errors=True)
    os.makedirs(kd)
    shutil.copy("clip/kaggle/charlie_full.py", f"{kd}/charlie_gen.py")
    meta = json.load(open("clip/kaggle/kernel-metadata.json"))
    json.dump(meta, open(f"{kd}/kernel-metadata.json", "w"), indent=1)
    r = subprocess.run(["kaggle", "kernels", "push", "-p", kd], capture_output=True, text=True)
    print("kernel push:", r.stdout[-400:], r.stderr[-400:])
    print("\nAcompanhe: kaggle kernels status " + meta["id"])
