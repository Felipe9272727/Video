# Charlie's Inferno — animação desenhada à mão

Clipe animado para o cover PT-BR de *Charlie's Inferno* (That Handsome Devil),
sincronizado com a música. Um diabinho desenhado à mão "canta" e reage à batida
dentro de um inferno de chamas — com estética feita à mão (traço **fervendo**,
textura de papel/grão, cadência ~12fps), nada de formas geométricas limpas.

## Como funciona (3 etapas)

1. **`analyze.py`** — analisa o MP3 (numpy, sem librosa) e gera
   `build/timeline.json`: por frame de vídeo extrai energia geral, graves,
   médios, agudos, **banda vocal** (controla a boca cantando), um envelope de
   **batida** com decaimento (acentos/pulos) e a fase do tempo (~143 BPM).
2. **`engine.js`** — motor de desenho em Canvas, determinístico por frame.
   Tudo é desenhado com traços ásperos que "fervem" (re-sorteados a cada 2
   frames → ~12fps), hachuras à caneta para sombra, chamas orgânicas irregulares
   (várias "línguas" sobrepostas), brasas, e o personagem com squash & stretch,
   piscadas, sobrancelhas expressivas, boca que abre com a voz e tridente que
   pulsa na batida.
3. **`render.js`** — abre o Chromium (Playwright), renderiza frame a frame e
   joga os PNGs direto no ffmpeg (H.264 + AAC), juntando o áudio numa passada só.

## Re-renderizar

```bash
pip install imageio-ffmpeg numpy playwright
# 1) decodificar o áudio p/ análise (ffmpeg do imageio-ffmpeg)
ffmpeg -i "<arquivo>.mp3" -ac 1 -ar 22050 -f f32le build/audio_mono_22050.raw
# 2) análise (24 fps)
python3 animation/analyze.py 24
# 3) render completo (com áudio)
cd animation && node render.js --out ../charlie_inferno_animacao.mp4
# Conferir frames soltos sem renderizar tudo:
node render.js --probe 60,1200,3000
```

## Ajustes rápidos (em `engine.js`)

- **Mais "fervido"/tremido:** aumente `wob` nos `blob(...)` do personagem.
- **Cadência:** `HOLD` (2 = ~12fps de boil; 3 = ~8fps, mais "stop-motion").
- **Cores:** constantes `RED`, `INK`, paleta das chamas em `tongue(...)`.
- **Intensidade da reação à batida:** fatores `beat` em `drawDevil`/`drawTrident`.
