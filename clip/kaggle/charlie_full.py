import os, json, glob, time, subprocess, sys
subprocess.run([sys.executable,"-m","pip","install","-q","--upgrade",
   "git+https://github.com/huggingface/diffusers","transformers>=4.49.0","accelerate",
   "safetensors","ftfy","imageio","imageio-ffmpeg","imageio[ffmpeg]"], check=False)
import torch, numpy as np, imageio.v3 as iio
from PIL import Image
from diffusers import AutoencoderKLWan, WanImageToVideoPipeline
from diffusers.utils import export_to_video, load_image
print("torch", torch.__version__, "GPU", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU", flush=True)

# ---- dataset (auto-localiza) ----
for root,dirs,files in os.walk("/kaggle/input"): print(" IN", root, files[:4], flush=True)
cand=glob.glob("/kaggle/input/**/prompts.json", recursive=True)
assert cand, "prompts.json nao encontrado"
DATA=os.path.dirname(cand[0]); print("DATA =", DATA, flush=True)
cfg=json.load(open(f"{DATA}/prompts.json")); NEG=cfg["neg"]; PROMPTS=cfg["prompts"]

OUT="/kaggle/working"; MOT=f"{OUT}/motion"; BRG=f"{OUT}/bridges"
os.makedirs(MOT,exist_ok=True); os.makedirs(BRG,exist_ok=True)

# pontes: do prompts.json (bridge_plan da direção, com prompt de morph
# específico por emenda); fallback pros 27 pares antigos se o dataset for velho
BRIDGES=cfg.get("bridges") or [{"a":a,"b":b,"prompt":None} for a,b in [["s04_funeral_wide", "s05_shower"], ["s05_shower", "s06_bike"], ["s06_bike", "s07_fishing"], ["s07_fishing", "s08_flag"], ["s08_flag", "s09_ocean"], ["s09_ocean", "s10_rose"], ["s10_rose", "s11_questions"], ["s11_questions", "s12_crash"], ["s12_crash", "s13_stairs"], ["s20_no_air", "s21_beg"], ["s28_pit", "s29_hell_gate"], ["s31_hellscape", "s32_gluttons"], ["s32_gluttons", "s33_mirrors"], ["s33_mirrors", "s35_market"], ["s35_market", "s37_elevator"], ["s39_run_gate", "s40_devil"], ["s41_demon_list", "s42_denied"], ["s42_denied", "s33_mirrors"], ["s44_heart_falls", "s45_beg_devil"], ["s45_beg_devil", "s46_uniform"], ["s46_uniform", "s48_demon_parade"], ["s50_thrown", "s51_pound_door"], ["s53_chase", "s54_they_walk"], ["s53_chase", "s56_climb"], ["s56_climb", "s59_final_beg"], ["hero", "s63_last_scream"], ["s64_dissolve", "s03_tombstone"]]]

MODEL="Wan-AI/Wan2.2-TI2V-5B-Diffusers"
RES_AREA=352*640; NF=49; NF_BR=33; STEPS=28; GUID=5.0; FPS=24

vae=AutoencoderKLWan.from_pretrained(MODEL, subfolder="vae", torch_dtype=torch.float32)
pipe=WanImageToVideoPipeline.from_pretrained(MODEL, vae=vae, torch_dtype=torch.bfloat16)
pipe.enable_model_cpu_offload()
for fn in ("enable_vae_tiling","enable_vae_slicing"):
    try: getattr(pipe,fn)()
    except Exception: pass
try: pipe.vae.enable_tiling(); pipe.vae.enable_slicing()
except Exception: pass
MOD=pipe.vae_scale_factor_spatial*pipe.transformer.config.patch_size[1]
print("modelo pronto | MOD=",MOD,"| VRAM livre",round(torch.cuda.mem_get_info()[0]/1e9,2),"GB",flush=True)

def dims(img):
    ar=img.height/img.width
    h=max(MOD,int(round((RES_AREA*ar)**0.5))//MOD*MOD); w=max(MOD,int(round((RES_AREA/ar)**0.5))//MOD*MOD)
    return h,w

def gen_i2v(stem):
    out=f"{MOT}/{stem}.mp4"
    if os.path.exists(out) and os.path.getsize(out)>60000: return "skip"
    img=load_image(f"{DATA}/{stem}.jpg"); h,w=dims(img); img=img.resize((w,h))
    fr=pipe(image=img, prompt=PROMPTS[stem], negative_prompt=NEG, height=h, width=w,
            num_frames=NF, guidance_scale=GUID, num_inference_steps=STEPS).frames[0]
    export_to_video(fr,out,fps=FPS); return f"ok {os.path.getsize(out)//1024}KB"

def last_frame(stem):
    p=f"{MOT}/{stem}.mp4"
    if os.path.exists(p):
        try:
            v=iio.imread(p); return Image.fromarray(np.asarray(v[-1]))
        except Exception: pass
    return load_image(f"{DATA}/{stem}.jpg")

def first_frame(stem):
    p=f"{MOT}/{stem}.mp4"
    if os.path.exists(p):
        try:
            v=iio.imread(p); return Image.fromarray(np.asarray(v[0]))
        except Exception: pass
    return load_image(f"{DATA}/{stem}.jpg")

def gen_flf(a,b,prompt=None):
    out=f"{BRG}/b_{a}__{b}.mp4"
    if os.path.exists(out) and os.path.getsize(out)>40000: return "skip"
    first=last_frame(a); last=first_frame(b)
    h,w=dims(first); first=first.resize((w,h)); last=last.resize((w,h))
    prompt=prompt or "anime style, seamless continuous cinematic camera transition between two moments, fluid smooth motion, no cut"
    fr=pipe(image=first, last_image=last, prompt=prompt, negative_prompt=NEG, height=h, width=w,
            num_frames=NF_BR, guidance_scale=GUID, num_inference_steps=STEPS).frames[0]
    export_to_video(fr,out,fps=FPS); return f"ok {os.path.getsize(out)//1024}KB"

# ===== FASE 1: 55 clipes principais =====
stems=[os.path.splitext(os.path.basename(p))[0] for p in sorted(glob.glob(f"{DATA}/*.jpg"))]
print(f"=== FASE 1: {len(stems)} clipes ===",flush=True)
ok1=0
for i,s in enumerate(stems,1):
    t0=time.time()
    try:
        r=gen_i2v(s); ok1+= (r!="skip"); print(f"[C {i}/{len(stems)}] {s} {r} {time.time()-t0:.0f}s",flush=True)
    except Exception as e:
        print(f"[C {i}/{len(stems)}] {s} ERRO {type(e).__name__}: {str(e)[:160]}",flush=True)
        import gc; gc.collect(); torch.cuda.empty_cache()

# ===== FASE 2: pontes FLF (best-effort) =====
print(f"=== FASE 2: {len(BRIDGES)} pontes FLF ===",flush=True)
ok2=0; flf_broken=False
for i,br in enumerate(BRIDGES,1):
    if flf_broken: break
    a,b,bp=br["a"],br["b"],br.get("prompt")
    t0=time.time()
    try:
        r=gen_flf(a,b,bp); ok2+=(r!="skip"); print(f"[B {i}/{len(BRIDGES)}] {a}->{b} {r} {time.time()-t0:.0f}s",flush=True)
    except TypeError as e:
        # last_image nao suportado nesta versao -> aborta pontes, mantem clipes
        print(f"[B {i}] FLF nao suportado ({str(e)[:120]}) — pulando todas as pontes",flush=True); flf_broken=True
    except Exception as e:
        print(f"[B {i}/{len(BRIDGES)}] {a}->{b} ERRO {type(e).__name__}: {str(e)[:150]}",flush=True)
        import gc; gc.collect(); torch.cuda.empty_cache()

print(f"\nCONCLUIDO: {ok1} clipes, {ok2} pontes em {OUT}",flush=True)
print("DONE",flush=True)
