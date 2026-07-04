# Charlie's Inferno — estado do projeto

Videoclipe anime (~3:50) da música "Charlie's Inferno" (cover PT-BR). Estilo seinen
sombrio, cel-shaded, câmera cinematográfica, ênfase nos refrões "Perdão, senhor".

## ROTA ATUAL DE GERAÇÃO: MiniMax Hailuo (IMPORTANTE)

A rota Kaggle/Wan foi abandonada (lenta demais, qualidade duvidosa do 5B, e o
container remoto não tem CLI/token do Kaggle). A nova rota é a **API do MiniMax
Hailuo**, escolhida porque:
- **Hailuo 2.3** (image-to-video) tem qualidade de movimento muito superior e
  suporta **comandos de câmera explícitos** (`[Push in]`, `[Truck left]`,
  `[Shake]`…) que o modelo segue de verdade — já embutidos nos prompts.
- **Hailuo-02** tem API de **primeiro+último frame (FLF)** — usada pras 31
  pontes que "geram o meio" entre planos (match cut, motion continue,
  dissolve), eliminando a cara de "vários cortes".
- Custo total do episódio: **~US$24** (Hailuo 2.3) ou **~US$19** (`--fast`,
  Hailuo 2.3-Fast), 768P 6s. Cada clipe sai em ~1 min (vs. 4-8h do Kaggle).

### O que falta: SÓ a chave da API
Criar conta em https://platform.minimax.io → recarregar ~US$25 → API Key →
`export MINIMAX_API_KEY=...` (ou salvar em `/root/.minimax_key`).

### Ordem de execução (tudo resumável, pode interromper)
```bash
python3 clip/hailuo_pipeline.py --dry-run    # valida + mostra custo, não gasta
python3 clip/hailuo_pipeline.py clips        # 55 clipes -> clip/motion/*.mp4
python3 clip/hailuo_pipeline.py bridges      # 31 pontes -> clip/bridges/*.mp4  (APÓS clips!)
python3 clip/qc_motion.py                    # QC de movimento dos clipes
# pré-requisitos do render (container novo):
pip install numpy pillow imageio_ffmpeg
FF=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
"$FF" -loglevel error -i "Charlie_s Inferno (Excuse Me Sir) - That Handsome Devil _ COVER PT-BR(MP3_160K)_1.mp3" -ac 1 -ar 22050 -f f32le -y build/audio_mono_22050.raw
python3 clip/analyze.py 24                   # build/timeline.json
python3 clip/assemble.py                     # -> out/charlie_inferno_cinematic.mp4
```

## Arquivos-chave da rota Hailuo
- `clip/hailuo_pipeline.py` — pipeline completo (submit paralelo com throttle,
  poll, download, estado em `build/hailuo_state.json`, `--status`, `--only`).
- `clip/hailuo_prompts.json` — 55 prompts finais (direção + comandos de câmera
  derivados do storyboard + trava de design do personagem). Gerado por
  `clip/hailuo_prompts_gen.py`, revisado por QC.
- `clip/direction/bridge_plan.json` — 31 pontes FLF (a, b, tipo, prompt de
  morph). Gerado por `clip/bridge_plan_gen.py`, prompts escritos pela direção.
- `clip/assemble.py` — motor de render; agora toca as pontes de `clip/bridges/`
  numa janela de ~0,72s cavalgando cada corte (fade nas bordas, sync musical
  intacto). Testado com ponte sintética (probe frames OK).

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
