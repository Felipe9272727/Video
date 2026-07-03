import os, json, glob, time, subprocess, sys
subprocess.run([sys.executable,"-m","pip","install","-q","--upgrade",
   "git+https://github.com/huggingface/diffusers","transformers>=4.49.0","accelerate",
   "safetensors","ftfy","imageio","imageio-ffmpeg"], check=False)
import torch, numpy as np
from diffusers import AutoencoderKLWan, WanImageToVideoPipeline
from diffusers.utils import export_to_video, load_image
print("torch", torch.__version__, "cuda?", torch.cuda.is_available(),
      torch.cuda.get_device_name(0) if torch.cuda.is_available() else "")

OUT="/kaggle/working"
# localiza o dataset automaticamente (o slug/path pode variar) + loga o que está montado
print("INPUT TREE:", flush=True)
for root,dirs,files in os.walk("/kaggle/input"):
    print("  ", root, "->", files[:6], flush=True)
cand=glob.glob("/kaggle/input/**/prompts.json", recursive=True)
assert cand, "prompts.json nao encontrado em /kaggle/input — dataset nao montado"
DATA=os.path.dirname(cand[0]); print("DATA =", DATA, flush=True)
cfg=json.load(open(f"{DATA}/prompts.json")); NEG=cfg["neg"]; PROMPTS=cfg["prompts"]

# ==== validação: só estes 3 (troco pra None no run completo) ====
ONLY=["s12_crash","hero","s31_hellscape"]

MODEL="Wan-AI/Wan2.2-TI2V-5B-Diffusers"
# T4 16GB: precisa apertar VRAM -> resolução/frames menores + slicing
RES_AREA=352*640; NUM_FRAMES=49; STEPS=28; GUID=5.0; FPS=24

vae=AutoencoderKLWan.from_pretrained(MODEL, subfolder="vae", torch_dtype=torch.float32)
pipe=WanImageToVideoPipeline.from_pretrained(MODEL, vae=vae, torch_dtype=torch.bfloat16)
pipe.enable_model_cpu_offload()
for fn in ("enable_vae_tiling","enable_vae_slicing"):
    try: getattr(pipe,fn)()
    except Exception: pass
try:
    pipe.vae.enable_tiling(); pipe.vae.enable_slicing()
except Exception: pass
MOD=pipe.vae_scale_factor_spatial*pipe.transformer.config.patch_size[1]
import torch as _t
print("modelo pronto | MOD=", MOD, "| VRAM livre:",
      round(_t.cuda.mem_get_info()[0]/1e9,2),"GB", flush=True)

def gen(stem):
    img=load_image(f"{DATA}/{stem}.jpg"); ar=img.height/img.width
    h=int(round((RES_AREA*ar)**0.5))//MOD*MOD; w=int(round((RES_AREA/ar)**0.5))//MOD*MOD
    h=max(MOD,h); w=max(MOD,w); img=img.resize((w,h))
    fr=pipe(image=img, prompt=PROMPTS[stem], negative_prompt=NEG, height=h, width=w,
            num_frames=NUM_FRAMES, guidance_scale=GUID, num_inference_steps=STEPS).frames[0]
    export_to_video(fr, f"{OUT}/{stem}.mp4", fps=FPS)

stems=[os.path.splitext(os.path.basename(p))[0] for p in sorted(glob.glob(f"{DATA}/*.jpg"))]
if ONLY: stems=[s for s in stems if s in ONLY]
print("gerando:", stems, flush=True)
for i,s in enumerate(stems,1):
    t0=time.time()
    try:
        gen(s); print(f"[{i}/{len(stems)}] {s} OK {time.time()-t0:.0f}s", flush=True)
    except Exception as e:
        print(f"[{i}/{len(stems)}] {s} ERRO {type(e).__name__}: {str(e)[:200]}", flush=True)
        import gc; gc.collect(); torch.cuda.empty_cache()
print("DONE")
