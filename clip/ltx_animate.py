#!/usr/bin/env python3
"""Anima cada plate (still Higgsfield) em vídeo LTX via a HF Space pública
Lightricks/ltx-video-distilled — GRÁTIS, sem chave, sem cadastro.

  python3 clip/ltx_animate.py            # anima todas as plates que faltam
  python3 clip/ltx_animate.py s12_crash.jpg s40_devil.jpg   # só essas

Saída: clip/motion/<stem>.mp4. Resumível (pula o que já existe).
Os 11 planos de reuso herdam o movimento da plate de origem no assemble.py.
"""
import json, os, re, shutil, sys, time
from gradio_client import Client, handle_file

SPACE = "Lightricks/ltx-video-distilled"
SB = json.load(open("clip/storyboard.json"))["shots"]
CURATED = {c["file"]: c["prompt"] for c in json.load(open("clip/animate_plan.json"))["clips"]}
os.makedirs("clip/motion", exist_ok=True)

MOTION_HINT = ("natural cinematic motion, subtle parallax camera move, drifting embers and "
               "atmosphere, flowing fabric and hair, living anime scene, smooth")

def scene_of(prompt):
    """Tira o prefixo de estilo e devolve a descrição da cena."""
    p = re.sub(r"^dark cinematic anime film still,.*?film grain,\s*", "", prompt or "")
    return p.strip() or "the anime scene comes to life"

def motion_prompt(s):
    if s["file"] in CURATED:
        return CURATED[s["file"]]
    return f"anime style, {scene_of(s['prompt'])}, {MOTION_HINT}"

def targets(argv):
    plates = [s for s in SB if s.get("prompt")]  # só stills únicos (reuso herda)
    # retrato-âncora (shot "Seu coração caiu") não tem prompt no storyboard
    plates.append({"file": "hero.jpg",
                   "prompt": "extreme close-up of a devastated gaunt anime man in a gray suit, "
                             "he breathes shakily, eyes trembling with despair, light flickers"})
    if argv:
        want = set(argv)
        plates = [s for s in plates if s["file"] in want]
    return plates

def animate(s, client, dur=3.0):
    out = os.path.join("clip/motion", os.path.splitext(s["file"])[0] + ".mp4")
    if os.path.exists(out) and os.path.getsize(out) > 1000:
        print("já existe:", out); return "skip"
    src = os.path.join("clip/shots", s["file"])
    res = client.predict(
        prompt=motion_prompt(s),
        negative_prompt="worst quality, inconsistent motion, blurry, jittery, distorted, watermark, text",
        input_image_filepath=handle_file(src),
        input_video_filepath=None,
        height_ui=384, width_ui=704, mode="image-to-video",
        duration_ui=dur, ui_frames_to_use=9, seed_ui=42,
        randomize_seed=True, ui_guidance_scale=1, improve_texture_flag=True,
        api_name="/image_to_video",
    )
    vid = res[0]["video"] if isinstance(res[0], dict) else res[0]
    shutil.copy(vid, out)
    return f"ok ({os.path.getsize(out)//1024} KB)"

if __name__ == "__main__":
    queue = targets(sys.argv[1:])
    print(f"{len(queue)} plates para animar", flush=True)
    client = Client(SPACE, verbose=False)
    done = skipped = 0
    errors = {}
    while queue:
        s = queue.pop(0)
        t0 = time.time()
        try:
            r = animate(s, client)
            print(f"{s['file']:24s} {r}  ({time.time()-t0:.0f}s) | faltam {len(queue)}", flush=True)
            if r != "skip":
                done += 1
        except Exception as e:
            msg = str(e)[:180]
            if "quota" in msg.lower() or "exceeded" in msg.lower():
                print(f"{s['file']:24s} quota — esperando 150s (faltam {len(queue)+1})", flush=True)
                queue.insert(0, s)
                time.sleep(150)
                continue
            errors[s["file"]] = errors.get(s["file"], 0) + 1
            print(f"{s['file']:24s} ERRO {errors[s['file']]}: {type(e).__name__}: {msg}", flush=True)
            if errors[s["file"]] < 3:
                queue.append(s)
            else:
                skipped += 1
            time.sleep(5)
    print(f"\nRESUMO: {done} animadas, {skipped} desistidas", flush=True)
