#!/usr/bin/env python3
"""Reanima cada plate com Wan 2.1 (HF Space pública multimodalart/wan2-1-fast),
usando os prompts de movimento do estúdio (clip/direction/out_segment_*.json).
GRÁTIS, anônimo. Serial (fila ZeroGPU). Resumível, tolerante a quota.

  python3 clip/wan_animate.py            # todas as plates que faltam
  python3 clip/wan_animate.py s40_devil.jpg s53_chase.jpg
"""
import glob, json, os, shutil, sys, time
from gradio_client import Client, handle_file

SPACE = "multimodalart/wan2-1-fast"
NEG = ("worst quality, static, blurred, distorted, watermark, text, extra limbs, "
       "deformed face, flickering, morphing, low quality")
SB = {s["file"]: s for s in json.load(open("clip/storyboard.json"))["shots"]}

# prompts de movimento do estúdio
PROMPTS = {}
for fp in glob.glob("clip/direction/out_segment_*.json"):
    try:
        for sh in json.load(open(fp))["shots"]:
            PROMPTS[sh["file"]] = sh["motion_prompt"]
    except Exception as e:
        print("aviso: falha lendo", fp, e)

os.makedirs("clip/motion", exist_ok=True)

def scene_fallback(f):
    p = SB.get(f, {}).get("prompt", "") or ""
    return "anime style, " + p.split("film grain,", 1)[-1].strip() + ", natural cinematic motion"

def plates():
    ps = [s["file"] for s in SB.values() if s.get("prompt")]
    ps.append("hero.jpg")
    seen=set(); out=[]
    for f in ps:
        if f not in seen and os.path.exists("clip/shots/"+f):
            seen.add(f); out.append(f)
    return out

def animate(f, client):
    out = os.path.join("clip/motion", os.path.splitext(f)[0] + ".mp4")
    if os.path.exists(out) and os.path.getsize(out) > 500000:  # já é Wan (LTX era <300KB)
        return "skip"
    prompt = PROMPTS.get(f) or scene_fallback(f)
    res = client.predict(
        input_image=handle_file("clip/shots/" + f),
        prompt=prompt, height=512, width=896, negative_prompt=NEG,
        duration_seconds=3, guidance_scale=1.0, steps=4,
        seed=42, randomize_seed=True, api_name="/generate_video",
    )
    vid = res[0]["video"] if isinstance(res[0], dict) else res[0]
    shutil.copy(vid, out)
    return f"ok ({os.path.getsize(out)//1024} KB)"

if __name__ == "__main__":
    queue = sys.argv[1:] or plates()
    print(f"{len(queue)} plates | {len(PROMPTS)} prompts do estúdio carregados", flush=True)
    client = Client(SPACE, verbose=False)
    done = 0; errs = {}
    while queue:
        f = queue.pop(0); t0 = time.time()
        try:
            r = animate(f, client)
            tag = "usa estúdio" if f in PROMPTS else "fallback"
            print(f"{f:24s} {r} [{tag}] ({time.time()-t0:.0f}s) | faltam {len(queue)}", flush=True)
            if r != "skip": done += 1
        except Exception as e:
            m = str(e)[:160]
            if any(w in m.lower() for w in ("quota", "exceeded", "gpu", "rate", "429")):
                print(f"{f:24s} quota — 150s (faltam {len(queue)+1})", flush=True)
                queue.insert(0, f); time.sleep(150); continue
            errs[f] = errs.get(f, 0)+1
            print(f"{f:24s} ERRO{errs[f]}: {type(e).__name__}: {m}", flush=True)
            if errs[f] < 3: queue.append(f)
            time.sleep(5)
    print(f"\nRESUMO: {done} reanimadas", flush=True)
