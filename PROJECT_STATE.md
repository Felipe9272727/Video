# Charlie's Inferno — estado do projeto

Videoclipe anime (~3:50) da música "Charlie's Inferno" (cover PT-BR). Estilo seinen
sombrio, cel-shaded, câmera cinematográfica, ênfase nos refrões "Perdão, senhor".

## Onde está a geração de movimento (IMPORTANTE)

Os 55 clipes de animação + 27 pontes FLF estão sendo gerados **no Kaggle** (GPU T4
grátis), kernel **`felipe028382072/charlie-gen`** (Wan 2.2 TI2V-5B + prompts de ação
forte). Roda sozinho (~4-8h). Token Kaggle em `/root/.kaggle_api_token`.

### Como FINALIZAR quando o kernel terminar
```bash
python3 clip/finish_from_kaggle.py --status   # confere se está COMPLETE
python3 clip/finish_from_kaggle.py            # baixa clipes+pontes, coloca no lugar, renderiza
git add clip/motion clip/bridges && git commit -m "clipes Kaggle + render final" && git push -u origin claude/video-animation-cinematic-59xnch
```
Saída: `out/charlie_inferno_cinematic.mp4`.

## Pipeline (tudo pronto e testado)
- `clip/assemble.py` — motor de render: clipes de movimento (ou parallax 2.5D de
  fallback), transições conectivas, color script por ato, inserts anime, ênfase nos
  ganchos, letterbox 21:9. Já com as melhorias da revisão (contorno de título,
  impacts segurando, contraste/saturação/vinheta/grão reforçados, ganchos mais fortes).
- `clip/inserts/` — title card, 4 impact frames manga, eyecatch (FLUX grátis). Integrados.
- `clip/direction/hooks.json` — 6 ganchos "Perdão senhor" sincronizados à voz.
- `clip/shots/*.jpg` — 55 plates anime (2K). `build/depth/*.png` — mapas de profundidade.
- `clip/kaggle/` e `clip/finish_from_kaggle.py` — pipeline Kaggle + finalização.

## Pendências ao voltar
1. Kernel Kaggle COMPLETE? → rodar `clip/finish_from_kaggle.py`.
2. Se as **pontes FLF** vieram (clip/bridges/*.mp4): integrar no assemble (opcional —
   o motor já tem transições conectivas se não houver pontes).
3. Render final → commit → push.

## Notas
- 14B (qualidade máxima) NÃO cabe na GPU grátis do Kaggle (RAM). Só na A100 do Colab Pro
  do usuário (`clip/colab/animate_wan.ipynb`, já pronto pra 14B). O Kaggle usa 5B (cabe,
  grátis, movimento forte com os prompts de ação).
- Branch de trabalho: `claude/video-animation-cinematic-59xnch`.
