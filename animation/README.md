# Charlie's Inferno — clipe animado (anime cinematográfico)

Clipe narrativo para o cover PT-BR de *Charlie's Inferno* (That Handsome Devil).
Conta a **história do Charlie**: um homem "bonzinho" e vaidoso morre esperando o
céu; um anjo confere a lista e o nome dele não está lá; ele é mandado **pra
baixo** — implorando a demônios indiferentes enquanto desce num inferno
burocrático/consumista. Sem redenção. (Narrativa tirada da letra; **nenhuma letra
aparece na tela** por direitos autorais.)

Estilo: **cel-shading**, 24fps fluido (sem traço "fervido"), cortes de câmera,
parallax, silhuetas dramáticas, god-rays, *speed lines*, brasas, *letterbox* e
correção de cor por cena.

## Estrutura (9 movimentos, sincronizados com as seções da música)

| Tempo | Cena |
|------|------|
| 0–50s | Vida oca do "bom homem" — subúrbio cinza e chuvoso, igreja, título |
| 50–57s | Ascensão pra luz (god-rays, nuvens) |
| 57–70s | A lista — anjo confere o livro → nome ausente → coração cai |
| 70–100s | Refrão: o apelo + começo da queda pelo poço |
| 100–130s | O inferno grotesco/consumista ("ABANDON ALL HOPE") |
| 130–150s | A caçada do diabo — agora um demônio confere a lista |
| 150–176s | Refrão: descida mais fundo, "não pertenço aqui" |
| 176–200s | Ponte: a corrida infinita e inútil |
| 200–230s | Outro: sem redenção, engolido pelas chamas |

## Pipeline

1. **`analyze.py`** → `build/timeline.json` (energia, graves, banda vocal, batidas)
   — dirige reações à música (tremor de câmera, brasas, boca cantando).
2. **`transcribe.py`** → `build/lyrics.json` (faster-whisper) — timings das frases
   pra cortar as cenas nos pontos certos. Só referência interna.
3. **`anime.js`** → motor cel-shaded com sistema de cenas, câmera, Charlie
   posável (poses por keyframe), cenários reutilizáveis (portão, poço, multidão).
4. **`render.js`** → Chromium (Playwright) frame a frame → ffmpeg (H.264 + AAC).

```bash
cd animation && node render.js --out ../build/anime_full.mp4   # render completo
node render.js --probe 720,2760,4512                            # frames avulsos p/ QA
```

`engine_v1_handdrawn.js` = versão anterior (diabo desenhado à mão), guardada só
como referência.

## Limite honesto

Isto é **procedural** (gerado por código), não anime de estúdio quadro a quadro.
Os personagens são estilizados (figuras cel-shaded + silhuetas), sem atuação
facial detalhada. A força vem da direção: luz, cor, câmera, composição e ritmo.
