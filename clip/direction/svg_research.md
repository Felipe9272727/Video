# SVG / vetor pra fluidez + artefato — pesquisa (4 Haikus, web 2024-2026)
Reuso: NÃO re-pesquisar. Consultar aqui.

## Pergunta do usuário
Usar SVG (Claude redesenha frame em vetor) pra melhorar fluidez e reduzir artefato do videoclipe anime.

## Veredito (convergência das 4 frentes)
**SVG nos QUADROS de anime detalhados = NÃO.** Motivos, consistentes nas 4 pesquisas:
- Gradiente/fogo/textura = "inimigo #1" da vetorização → explode nós ou vira aproximação chapada (perde a qualidade que o usuário curtiu).
- LLM (Claude/GPT) escreve *código* SVG → vira "coordinate soup"/blob em cena complexa (~20% viável em frame anime).
- Boiling temporal: SVG frame-a-frame vibra; só some com atlas/mesh (Deformable Sprites, Layered Neural Atlas) = ~horas/vídeo.
- StarVector: ótimo em ícone/logo, inútil em anime. OmniSVG: melhor (anime no dataset), mas ~75% e só pesquisa 2026, QA pesado.

**SVG nos OVERLAYS gráficos chapados = SIM.** title card, painéis de mangá, créditos, letterbox, texto → vetorial nítido, escala infinita, custo ~zero. Aqui a intuição do usuário está certa.

## O que DE FATO ataca fluidez + artefato (não-vetorial, vence)
| Ferramenta | Ataca | Anime+fogo? | Custo | Onde roda |
|---|---|---|---|---|
| **RIFE** (interp. frames, anime-model) | fluidez | sim | free | local (torch) |
| **EbSynth 2** (propaga 1 keyframe estilizado por textura) | artefato/coerência | sim (Undone, Wednesday) | free | app desktop (usuário) |
| **ffmpeg deflicker/minterpolate** | flicker/fluidez | genérico | free | já temos ffmpeg |
| **Topaz** (denoise/upscale) | limpeza | parcial (cuidado c/ linework) | pago | app |

**EbSynth = o que o usuário REALMENTE quis** ("pegar a animação como base e melhorar coerência"): propaga um keyframe limpo pelo clipe mantendo cel-art + fogo, sem alucinação de IA e sem chapar em vetor.

## Recomendação
1. SVG **só nos overlays** (title/créditos/painéis) — faço aqui, grátis.
2. Fluidez: teste RIFE/minterpolate em 1 clipe antes de aplicar no episódio.
3. Coerência/limpeza dos frames: EbSynth 2 (rota usuário, como o Colab).
