#!/usr/bin/env python3
"""Gera clip/colab/bridges_wan.ipynb — notebook Colab (A100) que produz as 31
pontes FLF do episódio com Wan 2.1 FLF2V 14B 720p (mesma família 14B que fez os
clipes bons), lê o bridge_plan.json, pula as marcadas 'procedural' no bridge_qc,
extrai os frames de emenda dos clipes já commitados (com flip correto) e faz
commit+push de cada ponte. Rode este builder e commite o .ipynb resultante.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
BRANCH = "claude/trusting-lamport-6ktlzm"
REPO = "Felipe9272727/Video"

md = f"""# Charlie's Inferno — Pontes FLF (Colab A100)

Gera as **pontes** que costuram os cortes (a IA gera o movimento entre o fim de
um plano e o começo do outro). Roda **Wan 2.1 FLF2V 14B 720p** — precisa de GPU
**A100** (Colab Pro, Runtime → Change runtime type → A100).

**Ordem:** rode as células de cima pra baixo. No fim, as pontes vão commitadas
pro branch `{BRANCH}`. Depois é só me avisar que eu monto o episódio final.

**Armazenamento (importante):** o 14B baixa ~30-40 GB e enche o disco do Colab.
A célula "ARMAZENAMENTO" monta o **Google Drive** e joga o cache lá — precisa de
~40 GB livres no Drive (plano Google One; o Drive grátis de 15 GB não cabe).
Se seu Drive não tiver espaço, me avise que eu troco por um modelo pré-quantizado
menor (~14 GB). Precisa também de um **GitHub token** (Settings → Developer
settings → Tokens) com acesso ao repo.
"""

c_pip = ('%pip -q install "git+https://github.com/huggingface/diffusers" '
         '"transformers>=4.49.0" accelerate safetensors ftfy imageio imageio-ffmpeg '
         'bitsandbytes hf_transfer')

c_clone = f'''import subprocess, os
REPO='{REPO}'; BRANCH='{BRANCH}'; REPO_DIR='/content/video'
TOKEN=None
try:
    from google.colab import userdata; TOKEN=userdata.get('GITHUB_TOKEN')
except Exception: TOKEN=None
if not TOKEN:
    from getpass import getpass; TOKEN=getpass('Cole seu GitHub token e Enter: ').strip()
assert TOKEN and TOKEN.startswith(('ghp_','github_pat_')), 'Token invalido.'
url=f'https://x-access-token:{{TOKEN}}@github.com/{{REPO}}.git'
if not os.path.isdir(REPO_DIR):
    subprocess.run(['git','clone','--branch',BRANCH,'--depth','1',url,REPO_DIR], check=True)
subprocess.run(['git','-C',REPO_DIR,'config','user.email','colab-wan@local'], check=False)
subprocess.run(['git','-C',REPO_DIR,'config','user.name','Colab Wan'], check=False)
subprocess.run(['git','-C',REPO_DIR,'remote','set-url','origin',url], check=False)
print('repo ok | clipes:', len([f for f in os.listdir(REPO_DIR+'/clip/motion') if f.endswith('.mp4')]))'''

c_storage = '''# ARMAZENAMENTO: joga o cache dos modelos no Google Drive (o disco do Colab enche
# com os ~30-40GB do 14B). Precisa de ESPACO no Drive (~40GB livre -> plano Google
# One; o Drive gratis de 15GB NAO cabe o 14B). Rode ANTES de carregar o modelo.
import os, subprocess
USE_DRIVE = True                      # False = usa o disco do Colab mesmo
if USE_DRIVE:
    from google.colab import drive; drive.mount('/content/drive')
    HF='/content/drive/MyDrive/hf_cache'; os.makedirs(HF+'/hub', exist_ok=True)
    os.environ['HF_HOME']=HF; os.environ['HF_HUB_CACHE']=HF+'/hub'
    print('cache HF -> Drive:', HF)
os.environ['HF_HUB_ENABLE_HF_TRANSFER']='1'   # download mais rapido/robusto
print(subprocess.run(['df','-h'], capture_output=True, text=True).stdout)
print('Drive livre:'); print(subprocess.run(['bash','-lc','df -h /content/drive/MyDrive 2>/dev/null || echo (Drive nao montado)'], capture_output=True, text=True).stdout)'''

c_model = '''import torch
from diffusers import AutoencoderKLWan, WanImageToVideoPipeline, WanTransformer3DModel
from transformers import CLIPVisionModel
MODEL_ID='Wan-AI/Wan2.1-FLF2V-14B-720P-diffusers'   # first-last-frame 14B
QUANTIZE = False    # False = qualidade cheia (A100 c/ offload cabe). True = 4-bit se a VRAM apertar.
if QUANTIZE:
    from diffusers import BitsAndBytesConfig as DiffBnb
    qcfg=DiffBnb(load_in_4bit=True, bnb_4bit_quant_type='nf4', bnb_4bit_compute_dtype=torch.bfloat16)
    transformer=WanTransformer3DModel.from_pretrained(MODEL_ID, subfolder='transformer',
                  quantization_config=qcfg, torch_dtype=torch.bfloat16)
else:
    transformer=WanTransformer3DModel.from_pretrained(MODEL_ID, subfolder='transformer', torch_dtype=torch.bfloat16)
image_encoder=CLIPVisionModel.from_pretrained(MODEL_ID, subfolder='image_encoder', torch_dtype=torch.bfloat16)
vae=AutoencoderKLWan.from_pretrained(MODEL_ID, subfolder='vae', torch_dtype=torch.float32)
pipe=WanImageToVideoPipeline.from_pretrained(MODEL_ID, transformer=transformer, vae=vae,
              image_encoder=image_encoder, torch_dtype=torch.bfloat16)
try:
    pipe.enable_model_cpu_offload()            # move modulos ociosos p/ CPU -> 14B cheio cabe na A100
except Exception as e:
    print('offload indisponivel, indo direto p/ GPU:', str(e)[:80]); pipe.to('cuda')
try: pipe.enable_vae_tiling(); pipe.vae.enable_slicing()
except Exception: pass
MOD=pipe.vae_scale_factor_spatial*pipe.transformer.config.patch_size[1]
print('FLF 14B pronto ('+('4-bit' if QUANTIZE else 'full')+') | MOD=', MOD,
      '| VRAM livre GB:', round(torch.cuda.mem_get_info()[0]/1e9,1))'''

c_gen = '''import os, json, glob, time, gc, subprocess
import numpy as np, imageio.v3 as iio
from PIL import Image
from diffusers.utils import export_to_video
os.chdir(REPO_DIR)
RES_AREA=480*832; NUM_FRAMES=49; STEPS=30; GUID=5.5; FPS=24   # casa com os clipes (480x832); fallback auto se OOM
NEG='worst quality, static, blurred, distorted, watermark, text, extra limbs, deformed face, flickering, morphing'
BR=json.load(open('clip/direction/bridge_plan.json'))['bridges']
try: SKIP={(v['a'],v['b']) for v in json.load(open('clip/direction/bridge_qc.json'))['verdicts'] if v['suggest']=='procedural'}
except Exception: SKIP=set()
os.makedirs('clip/bridges', exist_ok=True)

def _flip(im, do): return im.transpose(Image.FLIP_LEFT_RIGHT) if do else im
def edge(plate, flip, which):
    p=f'clip/motion/{plate}.mp4'
    if os.path.exists(p):
        v=iio.imread(p); fr=v[-1] if which=='last' else v[0]
        return _flip(Image.fromarray(np.asarray(fr)), flip)
    jp=f'clip/shots/{plate}.jpg'
    return _flip(Image.open(jp).convert('RGB'), flip) if os.path.exists(jp) else None

def dims(im, area=RES_AREA):
    ar=im.height/im.width
    h=max(MOD,int(round(np.sqrt(area*ar)))//MOD*MOD); w=max(MOD,int(round(np.sqrt(area/ar)))//MOD*MOD)
    return h,w

def push():
    subprocess.run(['git','add','clip/bridges'], check=False)
    if subprocess.run(['git','diff','--cached','--quiet']).returncode!=0:
        subprocess.run(['git','commit','-q','-m','colab flf: pontes'], check=False)
        for _ in range(4):
            if subprocess.run(['git','push','origin',BRANCH]).returncode==0: break
            time.sleep(3)

ok=0
for i,b in enumerate(BR,1):
    a,bb=b['a'],b['b']
    out=f'clip/bridges/{a}__{bb}.mp4'
    if (a,bb) in SKIP: print(f'[{i}/{len(BR)}] {a}->{bb} SKIP (procedural)'); continue
    if os.path.exists(out) and os.path.getsize(out)>150000: print(f'[{i}/{len(BR)}] {a}->{bb} ja existe'); ok+=1; continue
    first=edge(b.get('pa',a), b.get('fa',False), 'last'); last=edge(b.get('pb',bb), b.get('fb',False), 'first')
    if first is None or last is None: print(f'[{i}/{len(BR)}] {a}->{bb} sem plate'); continue
    gc.collect(); torch.cuda.empty_cache()
    t0=time.time()
    def _run(area, nf):
        h,w=dims(first, area)
        return pipe(image=first.resize((w,h)), last_image=last.resize((w,h)), prompt=b['prompt'],
                    negative_prompt=NEG, height=h, width=w, num_frames=nf,
                    guidance_scale=GUID, num_inference_steps=STEPS).frames[0]
    try:
        try:
            fr=_run(RES_AREA, NUM_FRAMES)
        except torch.cuda.OutOfMemoryError:
            gc.collect(); torch.cuda.empty_cache()
            print(f'   OOM em {a}->{bb}, tentando menor...')
            fr=_run(320*576, 33)                       # fallback mais leve
        export_to_video(fr, out, fps=FPS); ok+=1
        print(f'[{i}/{len(BR)}] {a}->{bb} OK {os.path.getsize(out)//1024}KB {time.time()-t0:.0f}s')
        if ok%5==0: push()
    except Exception as e:
        print(f'[{i}/{len(BR)}] {a}->{bb} ERRO {type(e).__name__}: {str(e)[:150]}')
push()
print(f'\\nCONCLUIDO: {ok} pontes commitadas. Avise o assistente pra montar o episodio.')'''

cell = lambda src: {"cell_type": "code", "metadata": {}, "execution_count": None,
                    "outputs": [], "source": src.splitlines(keepends=True)}
nb = {"nbformat": 4, "nbformat_minor": 0,
      "metadata": {"accelerator": "GPU", "colab": {"provenance": []},
                   "kernelspec": {"name": "python3", "display_name": "Python 3"}},
      "cells": [{"cell_type": "markdown", "metadata": {}, "source": md.splitlines(keepends=True)},
                cell(c_pip), cell(c_clone), cell(c_storage), cell(c_model), cell(c_gen)]}
json.dump(nb, open("clip/colab/bridges_wan.ipynb", "w"), indent=1, ensure_ascii=False)
print("escrito clip/colab/bridges_wan.ipynb")
