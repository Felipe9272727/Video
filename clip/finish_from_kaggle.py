#!/usr/bin/env python3
"""FINALIZAÇÃO AUTÔNOMA — puxa os clipes do Kaggle, salva no git e monta o episódio.

Seguro e RESUMÁVEL: pode rodar quantas vezes for. Os clipes ficam duráveis no
Kaggle (re-baixáveis sempre) e são commitados+pushados ASSIM QUE baixados, antes
mesmo do render, pra nunca se perderem se o container morrer.

Pré-requisito: token Kaggle em /root/.kaggle_api_token (export KAGGLE_API_TOKEN=$(cat ...)).

  python3 clip/finish_from_kaggle.py --status   # só checa o kernel
  python3 clip/finish_from_kaggle.py            # baixa+commita+pusha+renderiza+commita
  python3 clip/finish_from_kaggle.py --no-render # só baixa e salva os clipes no git

Depois: out/charlie_inferno_cinematic.mp4 (commitado e pushado).
"""
import glob, os, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

KERNEL = "felipe028382072/charlie-gen"
BRANCH = "claude/trusting-lamport-6ktlzm"
TOK = "/root/.kaggle_api_token"
if os.path.exists(TOK):
    os.environ.setdefault("KAGGLE_API_TOKEN", open(TOK).read().strip())


def sh(cmd, **k):
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(cmd, **k)


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True)


def push_retry():
    for i, wait in enumerate([0, 2, 4, 8, 16]):
        if wait:
            time.sleep(wait)
        r = git("push", "-u", "origin", BRANCH)
        if r.returncode == 0:
            print("push OK", flush=True)
            return True
        print(f"push falhou (tentativa {i+1}): {r.stderr[-160:]}", flush=True)
    return False


def commit_push(paths, msg):
    """Adiciona, commita e pusha. No-op se nada mudou."""
    git("add", *paths)
    st = git("status", "--porcelain")
    if not st.stdout.strip():
        print("nada novo pra commitar:", msg, flush=True)
        return
    r = git("commit", "-q", "-m", msg)
    if r.returncode != 0:
        print("commit:", r.stdout[-160:], r.stderr[-160:], flush=True)
        return
    print("commit:", msg, flush=True)
    push_retry()


def kernel_status():
    r = sh(["kaggle", "kernels", "status", KERNEL], capture_output=True, text=True)
    out = (r.stdout or "") + (r.stderr or "")
    print(out.strip(), flush=True)
    return out


if "--status" in sys.argv:
    kernel_status(); sys.exit(0)

st = kernel_status()
if "COMPLETE" not in st.upper():
    print("Kernel ainda não COMPLETE — nada a baixar. Rode de novo mais tarde.", flush=True)
    # não é erro fatal: sai limpo pra o agendador tentar de novo
    sys.exit(0)

# 1) baixa a saída do kernel (durável — pode re-baixar sempre)
K = "/tmp/charlie_kaggle_out"
os.makedirs(K, exist_ok=True)
r = sh(["kaggle", "kernels", "output", KERNEL, "-p", K], capture_output=True, text=True)
print((r.stdout or "")[-300:], (r.stderr or "")[-200:], flush=True)

# 2) posiciona clipes e pontes
os.makedirs("clip/motion", exist_ok=True)
os.makedirs("clip/bridges", exist_ok=True)
nm = nb = 0
for p in glob.glob(f"{K}/**/*.mp4", recursive=True):
    base = os.path.basename(p)
    if os.path.getsize(p) < 40000:
        continue
    if "/bridges/" in p or base.startswith("b_"):
        dst = "clip/bridges/" + (base[2:] if base.startswith("b_") else base)
        if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(p):
            shutil.copy(p, dst); nb += 1
    else:
        dst = f"clip/motion/{base}"
        if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(p):
            shutil.copy(p, dst); nm += 1
n_clips = len(glob.glob("clip/motion/*.mp4"))
n_br = len(glob.glob("clip/bridges/*.mp4"))
print(f"novos: {nm} clipes, {nb} pontes | total no repo: {n_clips} clipes, {n_br} pontes", flush=True)

# 3) COMMIT+PUSH imediato dos clipes (durabilidade antes do render)
if nm or nb:
    commit_push(["clip/motion", "clip/bridges"],
                f"Clipes Kaggle: {n_clips} clipes + {n_br} pontes (Wan 2.2)")

if n_clips == 0:
    print("!! nenhum clipe baixado — o kernel terminou mas sem saída? confira o log:", flush=True)
    print("   kaggle kernels output " + KERNEL + " -p /tmp/ck && head /tmp/ck/*.log", flush=True)
    sys.exit(1)

# 4) QC de movimento (relatório; não bloqueia)
sh(["python3", "clip/qc_motion.py"])
commit_push(["clip/qc"], "QC de movimento dos clipes Kaggle")

if "--no-render" in sys.argv:
    print("--no-render: clipes salvos, pulando render.", flush=True)
    sys.exit(0)

# 5) pré-requisitos do render + timeline (container novo pode não ter)
sh([sys.executable, "-m", "pip", "install", "-q", "numpy", "pillow", "imageio_ffmpeg"])
if not os.path.exists("build/timeline.json"):
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    os.makedirs("build", exist_ok=True)
    mp3 = glob.glob("*.mp3")[0]
    sh([ff, "-loglevel", "error", "-i", mp3, "-ac", "1", "-ar", "22050",
        "-f", "f32le", "-y", "build/audio_mono_22050.raw"])
    sh([sys.executable, "clip/analyze.py", "24"])

# 6) render final
print("=== renderizando episódio final ===", flush=True)
r = sh([sys.executable, "clip/assemble.py"])
out = "out/charlie_inferno_cinematic.mp4"
if os.path.exists(out) and os.path.getsize(out) > 1_000_000:
    commit_push(["out"], "Render final do episódio (clipes Wan + pontes + motor)")
    print("\nPRONTO -> " + out, flush=True)
else:
    print("!! render não produziu saída válida — clipes já estão salvos no git.", flush=True)
    sys.exit(1)
