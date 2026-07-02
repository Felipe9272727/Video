# Charlie's Inferno — clipe anime cinematográfico (Higgsfield + motor de câmera)

Clipe narrativo completo (3:50) para o cover PT-BR de *Charlie's Inferno*
(That Handsome Devil / fandub FazDubz), refeito do zero depois do feedback:
**cada verso da letra oficial vira um plano**, com ângulos exagerados e
emoção vívida, em estilo anime seinen sombrio.

## Como foi feito

1. **Letra oficial com timestamps** — `letra_oficial.vtt`: legendas PT-BR
   publicadas pelo próprio autor do cover no YouTube (conferidas contra
   transcrição faster-whisper do MP3, bate em ±0,1s).
2. **Análise de áudio** — `analyze.py` (numpy puro) extrai energia, graves,
   banda vocal, batidas e onsets por frame → `build/timeline.json`.
   Dirige crash-zooms, flashes, shake e aberração cromática na batida.
3. **Direção** — `storyboard_gen.py`: 66 planos sincronizados verso a verso
   (54 imagens geradas + 12 reusos de plate com câmera nova/espelhada).
   Cada plano tem prompt, janela de tempo, trajetória de câmera
   (push-in / pull-out / pan / dutch roll / crash-zoom com easing),
   transição (cut / whip pan / flash / dip) e efeitos (chuva, brasas,
   god-rays), gravados em `storyboard.json`.
4. **Imagens** — geradas via conector **Higgsfield MCP**, modelo `z_image`
   (0,15 crédito/imagem, 2048×1152), estilo consistente: "dark cinematic
   anime film still, cel-shaded, seinen", personagem fixado por descrição
   idêntica em todos os prompts (terno cinza, gravata vermelha). Total
   gasto: ~8,5 dos 10 créditos do plano free.
5. **Montagem** — `assemble.py`: renderiza 5.526 frames 1280×720\@24fps,
   letterbox 21:9, camera path por plano + micro-shake handheld guiado
   pela energia da música, flash nos onsets fortes, aberração cromática
   nos punches, brasas/chuva/raios procedurais, vinheta, grão de filme,
   títulos, e muxa o MP3 (H.264 + AAC).

```bash
python3 clip/analyze.py 24          # build/timeline.json (requer o raw decodificado)
python3 clip/storyboard_gen.py      # clip/storyboard.json
python3 clip/assemble.py            # out/charlie_inferno_cinematic.mp4
python3 clip/assemble.py probe 65 150 210   # frames avulsos p/ QA
```

## Estrutura narrativa (segue a letra à risca)

| Tempo | Letra | Plano |
|------|-------|------|
| 0:00–0:11 | (instrumental) | cemitério na chuva, enterro, título |
| 0:11–0:18 | "Aqui jaz Charlie…" | lápide CHARLIE + enterro deadpan |
| 0:18–0:44 | Verso 1 (banho frio, bike, pesca, bandeira, oceano, rosa, perguntas) | um plano por verso, vida "correta" e vazia |
| 0:41–0:45 | "Bateu o carro, infartou…" | crash congelado, flash cut |
| 0:45–1:11 | escada dourada, oração, "formiga", anjo com a lista, nome ausente | subida ao céu → recusa |
| 1:11–1:37 | Refrão 1 | implorando no portão, close de desespero, igreja (flashback), anjos passando |
| 1:24–1:37 | (refrão 2ª metade) | o chão de nuvens abre → QUEDA |
| 1:37–2:03 | Verso 2 (Abandone toda esperança, gorduchos, egocêntricos, mercado, elevador) | inferno grotesco/consumista |
| 2:03–2:29 | elevador, corredor, corrida, o diabo, demônio com a lista, "negado" | espelho infernal da recepção celeste |
| 2:29–2:56 | Refrão 2 | implorando ao diabo, arrastado, esmurrando a porta |
| 2:56–3:22 | Ponte (fugir dos demônios / correr pros anjos) | caçada + escalada pra luz inalcançável |
| 3:22–3:48 | Refrão final ("eu não quero morrer") | anel de fogo, lista em cinzas, mão nas chamas, grito final, dissolve em brasas |
| 3:41–3:50 | (outro) | volta à lápide na chuva — bookend |

## Nota de créditos Higgsfield

O plano free (10 créditos) não cobre vídeo AI direto (7,5 créditos por clipe
de 5s ≈ 350+ créditos para a música inteira). A solução: keyframes 2K do
Higgsfield + câmera virtual procedural — cinema de verdade dentro do
orçamento. Com mais créditos dá pra animar os planos-chave com
image-to-video (kling/seedance) usando estas mesmas plates como start frames.
