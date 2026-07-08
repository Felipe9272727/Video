# CLAUDE.md — Charlie's Inferno (videoclipe anime)

Videoclipe anime (~3:50) do cover PT-BR de *Charlie's Inferno* (That Handsome Devil).
55 planos animados por IA (image-to-video) + pontes entre cortes, montados por um motor
de câmera procedural. Estado sempre em `PROJECT_STATE.md` — **leia-o antes de agir**.

## Protocolo de orquestração (economia de tokens SEM perder qualidade)

Regra absoluta: se economia conflitar com qualidade, **qualidade vence**.

**Antes de cada tarefa, classifique a complexidade e roteie:**

| Tipo de tarefa | Estratégia | Modelo |
|---|---|---|
| Trivial (1 arquivo, resposta direta) | resolver direto, **sem** subagente | Opus (eu) |
| Fan-out / exploração (varrer N arquivos, ler logs) | delegar, receber só a conclusão | Explore/**Haiku** |
| Lote paralelizável (revisar/gradear os 55 planos) | lote de subagentes, contexto mínimo cada | **Haiku** |
| QC, classificação, revisão de prompt | delegar | **Haiku** |
| Síntese média / edição contida | quando valer | Sonnet |
| Decisão de arquitetura / trade-off | resolver direto | Opus (eu) |

**Escala de modelos (rank do usuário — regem a delegação):**
- **Haiku padrão** — a maior parte do trabalho braçal.
- **Haiku (ultracode / max thinking)** — trabalhador geral pesado; **sempre verifico a saída
  antes do final** (modelo pequeno → avaliar antes de assumir como bom = "draft-verify").
- **Sonnet** — tarefas complexas, mas não tanto quanto as minhas; o que **menos** uso.
- **Opus (eu)** — orquestrador: classifico, roteio, decido arquitetura/direção, verifico deltas.
- **Fable** — teto de escalada: só quando **eu não consigo deixar realmente bom**.

Preço/1M (input/output): Haiku $1/$5 · Sonnet $2–3/$10–15 · Opus $5/$25 · Fable $10/$50.
Haiku é 5× mais barato que Opus no input. **Não** spawnar subagente pra tarefa trivial
(cold start + re-derivação custa mais que fazer direto).

## Regras de economia (aplicar sempre)

1. **Despejo verboso → arquivo, não contexto.** Logs de kernel, blobs de URL, folhas de
   contato: gravar em `build/` e ler de volta só o essencial. Encolhe o prefixo re-cacheado.
2. **Não re-ler arquivo recém-editado** — o harness rastreia o estado; Edit/Write erram se falhar.
3. **Reusar estado do repo** — nunca recomputar o que já está em `PROJECT_STATE.md`,
   `clip/qc/motion_report.json`, `build/qc_visual_*.json`. Isso é reuso de inferência.
4. **Output enxuto** — a régua é "o que o usuário agiria em cima", não prosa. Output é o lado caro.
5. **Não pesquisar o que já se sabe** — responder direto quando o dado já está no contexto.

## Geração de vídeo (o que funciona)

- **Movimento de verdade = Wan 14B na A100 (Colab do usuário)** OU **Higgsfield** (Seedance
  1.5 480p ~2,4 cr/close; Kling Turbo 720p ~4,5 cr pra ação com câmera). O Wan 5B grátis
  sai estático — descartado.
- **Motor** (`clip/assemble.py`): toca clipe em velocidade nativa, corta 24% final
  (o Wan/Seedance derrete no fim), pula clipe marcado ESTATICO no `motion_report.json`
  (volta pra plate 2K com câmera). Pontes de `clip/bridges/` cavalgam o corte.
- **QC**: `python3 clip/qc_motion.py` (movimento por-plano, piso calibrado) + revisão
  visual por Haikus (folhas de contato em `build/contact/`).
- **Prompts**: pedir "fast natural-speed motion, no slow motion" — nunca "slowly"/"slow motion".

## Git

Branch de trabalho: `claude/trusting-lamport-6ktlzm`. Commitar+pushar trabalho concluído;
render full (500MB) fica fora do git (só a versão web ~37MB).
