#!/usr/bin/env python3
"""Pontes "sem corte" entre planos via Wan 2.2 First-Last-Frame (HF Space grátis).
Pega o ÚLTIMO frame do clipe A + o PRIMEIRO frame do clipe B e gera o movimento
no meio -> emenda fluida em vez de corte.

  python3 clip/flf_bridge.py s03_tombstone s04_funeral_wide "prompt do morph"
  python3 clip/flf_bridge.py --auto            # todas as emendas do bridge_plan.json

Saída: clip/bridges/<a>__<b>.mp4  (o motor insere na janela de transição).
"""
import json, os, subprocess, sys, time
from gradio_client import Client, handle_file
import imageio_ffmpeg

SPACE = "multimodalart/wan-2-2-first-last-frame"
HF_TOKEN = open("/root/.hf_token").read().strip() if os.path.exists("/root/.hf_token") else None
FF = imageio_ffmpeg.get_ffmpeg_exe()
NEG = "worst quality, jitter, morphing face, distorted, watermark, text, flicker, deformed"
SHOTS = {s["file"].replace(".jpg", ""): s for s in json.load(open("clip/storyboard.json"))["shots"]}
os.makedirs("clip/bridges", exist_ok=True)
os.makedirs("build/seam", exist_ok=True)

def motion_mp4(stem):
    s = SHOTS.get(stem, {})
    for base in [s.get("file", stem + ".jpg"), s.get("src") or ""]:
        if not base: continue
        p = "clip/motion/" + os.path.splitext(base)[0] + ".mp4"
        if os.path.exists(p) and os.path.getsize(p) > 180000:
            return p
    return None

def _vf(stem, scale=False):
    # planos reusados espelhados: o frame de emenda precisa bater com o que
    # aparece na tela (assemble aplica flip), senão a ponte "pula"
    flip = bool(SHOTS.get(stem, {}).get("flip"))
    parts = (["hflip"] if flip else []) + (["scale=896:-1"] if scale else [])
    return ["-vf", ",".join(parts)] if parts else []

def last_frame(stem):
    p = motion_mp4(stem); out = f"build/seam/{stem}_last.jpg"
    if p: subprocess.run([FF, "-loglevel", "error", "-sseof", "-0.1", "-i", p, *_vf(stem), "-frames:v", "1", "-y", out], check=False)
    else:
        src = SHOTS.get(stem, {}).get("src") or stem + ".jpg"
        subprocess.run([FF, "-loglevel", "error", "-i", f"clip/shots/{src}", *_vf(stem, True), "-frames:v", "1", "-y", out], check=False)
    return out

def first_frame(stem):
    p = motion_mp4(stem); out = f"build/seam/{stem}_first.jpg"
    if p: subprocess.run([FF, "-loglevel", "error", "-i", p, *_vf(stem), "-frames:v", "1", "-y", out], check=False)
    else:
        src = SHOTS.get(stem, {}).get("src") or stem + ".jpg"
        subprocess.run([FF, "-loglevel", "error", "-i", f"clip/shots/{src}", *_vf(stem, True), "-frames:v", "1", "-y", out], check=False)
    return out

def bridge(a, b, prompt, client, dur=1.5):
    out = f"clip/bridges/{a}__{b}.mp4"
    if os.path.exists(out) and os.path.getsize(out) > 180000:
        print(f"{a}->{b} skip"); return "skip"
    fa, fb = last_frame(a), first_frame(b)
    r = client.predict(
        start_image_pil=handle_file(fa), end_image_pil=handle_file(fb),
        prompt=prompt, negative_prompt=NEG, duration_seconds=dur,
        steps=6, guidance_scale=1, guidance_scale_2=1, seed=42, randomize_seed=True,
        api_name="/generate_video",
    )
    vid = r[0]["video"] if isinstance(r[0], dict) else r[0]
    subprocess.run(["cp", vid, out], check=False)
    return f"ok ({os.path.getsize(out)//1024} KB)"

if __name__ == "__main__":
    client = Client(SPACE, token=HF_TOKEN, verbose=False)
    if sys.argv[1] == "--auto":
        plan = json.load(open("clip/direction/bridge_plan.json"))["bridges"]
        for br in plan:
            t0 = time.time()
            try:
                print(f"{br['a']}->{br['b']} {bridge(br['a'], br['b'], br['prompt'], client)} ({time.time()-t0:.0f}s)", flush=True)
            except Exception as e:
                print(f"{br['a']}->{br['b']} ERRO: {str(e)[:150]}", flush=True); time.sleep(5)
    else:
        a, b = sys.argv[1], sys.argv[2]
        pr = sys.argv[3] if len(sys.argv) > 3 else "anime style, smooth continuous cinematic camera move connecting the two scenes, no cut"
        print(bridge(a, b, pr, client))
