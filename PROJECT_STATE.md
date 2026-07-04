# Charlie's Inferno — estado do projeto

Videoclipe anime (~3:50) da música "Charlie's Inferno" (cover PT-BR). Estilo seinen
sombrio, cel-shaded, câmera cinematográfica, ênfase nos refrões "Perdão, senhor".

## COMO RETOMAR (se a sessão caiu / limite estourou)

Os clipes ficam DURÁVEIS na saída do kernel Kaggle — nunca se perdem, mesmo que
o container morra. Pra finalizar tudo (baixar → commitar → renderizar → commitar),
UM comando resolve, resumável:
```bash
export KAGGLE_API_TOKEN=$(cat /root/.kaggle_api_token)
python3 clip/finish_from_kaggle.py            # faz tudo; se o kernel ainda roda, sai limpo
```
Estado do kernel: `python3 clip/finish_from_kaggle.py --status`. Se der ERROR,
baixe o log (`kaggle kernels output felipe028382072/charlie-gen -p /tmp/ck`) e
veja as primeiras linhas (torch/arch) e as linhas `[C x/55]`. Re-disparar após
corrigir: `python3 clip/kaggle/build_dataset.py`.

Tokens salvos: `/root/.kaggle_api_token`, `/root/.hf_token`, `/root/.modelscope_key`.

## ROTA ATUAL: 100% GRÁTIS (orçamento zero — decisão do usuário 2026-07-04)

Kaggle/Wan-5B abandonado (lento, qualidade fraca, sem CLI/token no container).
MiniMax Hailuo (pago, ~US$19-24) fica de RESERVA — pipeline pronto em
`clip/hailuo_pipeline.py` caso um dia haja verba. A rota ativa é:

1. **Clipes (55): ModelScope API-Inference — Wan 2.2 I2V-A14B** (o 14B de
   qualidade máxima, que nem cabia no Kaggle!). Tier GRÁTIS: 2000 chamadas/dia,
   sem cartão. `clip/modelscope_wan.py` (paralelo x4, resumável, usa os prompts
   revisados de hailuo_prompts.json com comandos convertidos pra linguagem
   natural).
2. **Pontes (31): HF Space `multimodalart/wan-2-2-first-last-frame`** (grátis,
   ZeroGPU). `clip/flf_bridge.py --auto` lê `clip/direction/bridge_plan.json`
   (31 prompts de morph escritos pela direção). Flip de reusos corrigido.
3. **Colab Pro do usuário** (já pago) = acelerador opcional pros planos-herói
   em 14B local (`clip/colab/animate_wan.ipynb`).

### O que o USUÁRIO precisa fazer (tudo grátis, sem cartão)
- Conta em https://modelscope.cn → perfil → Access Tokens → colar o token
  (chat, ou `export MODELSCOPE_KEY=...`, ou `/root/.modelscope_key`).
- Conta em https://huggingface.co → Settings → Access Tokens (read) →
  `/root/.hf_token` (dá quota ZeroGPU pras pontes; sem token a quota anônima é
  minúscula).

### Ordem de execução (tudo resumável)
```bash
pip install numpy pillow imageio_ffmpeg gradio_client
python3 clip/modelscope_wan.py s12_crash.jpg   # 1 teste de qualidade
python3 clip/modelscope_wan.py --all           # 55 clipes -> clip/motion/
python3 clip/flf_bridge.py --auto              # 31 pontes -> clip/bridges/
FF=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
"$FF" -loglevel error -i "Charlie_s Inferno (Excuse Me Sir) - That Handsome Devil _ COVER PT-BR(MP3_160K)_1.mp3" -ac 1 -ar 22050 -f f32le -y build/audio_mono_22050.raw
python3 clip/analyze.py 24                     # build/timeline.json
python3 clip/assemble.py                       # -> out/charlie_inferno_cinematic.mp4
```

## Arquivos-chave
- `clip/hailuo_prompts.json` — 55 prompts finais (direção + comandos de câmera
  do storyboard + trava de design do personagem), revisados por QC Haiku.
  Fonte única de prompts: o modelscope_wan converte na hora pro Wan.
- `clip/direction/bridge_plan.json` — 31 pontes (a, b, tipo, prompt de morph
  específico escrito pela direção de continuidade).
- `clip/assemble.py` — motor de render; toca as pontes de `clip/bridges/`
  numa janela de ~0,72s cavalgando cada corte (fade nas bordas, sync musical
  intacto). Testado com ponte sintética (probe frames OK).
- `clip/hailuo_pipeline.py` — rota paga de reserva (MiniMax, ~US$19-24 total).

## Pipeline (tudo pronto e testado)
- `clip/assemble.py` — clipes de movimento (ou parallax 2.5D de fallback),
  pontes FLF, transições conectivas, color script por ato, inserts anime,
  ênfase nos ganchos, letterbox 21:9.
- `clip/inserts/` — title card, 4 impact frames manga, eyecatch. Integrados.
- `clip/direction/` — bíblia de continuidade, mapa de transições, hooks
  sincronizados, prompts de movimento por segmento (out_segment_*.json).
- `clip/shots/*.jpg` — 55 plates anime 2K (Higgsfield z_image).

## Saldos / contas (2026-07-04)
- Higgsfield: 1,51 crédito (free) — vídeo mínimo custa 4,5 cr → inviável pra
  vídeo; sobra dá pra ~10 imagens z_image se precisar de plate extra.
- Kaggle: sem CLI/token neste container; rota descontinuada.
- MiniMax: aguardando chave do usuário (único bloqueio).

## Branch de trabalho
`claude/trusting-lamport-6ktlzm` (conteúdo do antigo
`claude/video-animation-cinematic-59xnch` já incorporado via fast-forward).
