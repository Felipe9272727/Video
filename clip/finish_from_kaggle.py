#!/usr/bin/env python3
"""FINALIZAÇÃO — puxa os clipes que o Kaggle gerou e monta o episódio.

Pré-requisito: token do Kaggle em /root/.kaggle_api_token (ou ~/.kaggle/access_token),
e o kernel `felipe028382072/charlie-gen` já COMPLETE.

  python3 clip/finish_from_kaggle.py            # baixa + coloca clipes + renderiza
  python3 clip/finish_from_kaggle.py --status   # só checa o status do kernel Kaggle

Depois: git add clip/motion clip/bridges ; git commit ; git push
"""
import os, sys, glob, shutil, subprocess

KERNEL = "felipe028382072/charlie-gen"
TOK = "/root/.kaggle_api_token"
if os.path.exists(TOK):
    os.environ.setdefault("KAGGLE_API_TOKEN", open(TOK).read().strip())

def sh(cmd, **k):
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(cmd, **k)

def status():
    sh(["kaggle", "kernels", "status", KERNEL])

if "--status" in sys.argv:
    status(); sys.exit(0)

# 1) baixa a saída do kernel
K = "/tmp/charlie_kaggle_out"
os.makedirs(K, exist_ok=True)
r = sh(["kaggle", "kernels", "output", KERNEL, "-p", K], capture_output=True, text=True)
print(r.stdout[-500:] if r.stdout else "", r.stderr[-300:] if r.stderr else "")

# 2) coloca clipes e pontes no lugar
os.makedirs("clip/motion", exist_ok=True); os.makedirs("clip/bridges", exist_ok=True)
nm = nb = 0
for p in glob.glob(f"{K}/**/*.mp4", recursive=True):
    base = os.path.basename(p)
    if "/bridges/" in p or base.startswith("b_"):
        # kernel nomeia b_<a>__<b>.mp4; o assemble espera <a>__<b>.mp4
        shutil.copy(p, "clip/bridges/" + (base[2:] if base.startswith("b_") else base)); nb += 1
    else:
        shutil.copy(p, f"clip/motion/{base}"); nm += 1
print(f"clipes: {nm} em clip/motion | pontes: {nb} em clip/bridges")
if nm == 0:
    print("!! nenhum clipe baixado — o kernel terminou? rode com --status"); sys.exit(1)

# 3) renderiza o episódio final (motor já tem as melhorias do Haiku)
print("=== renderizando episódio final ===", flush=True)
sh(["python3", "clip/assemble.py"])
print("\nPRONTO -> out/charlie_inferno_cinematic.mp4")
print("Agora: git add clip/motion clip/bridges && git commit -m 'clipes Kaggle' && git push")
