# ESTÚDIO "INFERNO" — organograma de produção

Estrutura de agentes pra dirigir e elevar o episódio. Cada um tem nome + função fixa.
Doutrina central: **modelo de texto anima por CÓDIGO** (câmera procedural, SVG/partículas,
interpolação, params do motor) — não gera vídeo. É assim que os Haikus "animam".

## Hierarquia
| Nome | Modelo | Cargo | Quando age |
|---|---|---|---|
| **Dante** | Fable | Showrunner / teto de qualidade | SÓ no fim; quando o Diretor não consegue deixar bom. Provavelmente não hoje. |
| **Virgílio (eu)** | Opus | **Diretor Geral** | Sempre. Classifico, decido arquitetura do motor, roteio, verifico, integro. |
| **Kubrick** | Sonnet | Diretor de cena + Storyboard | Plano-a-plano: o que cada shot precisa (movimento/câmera/regen), continuidade, ritmo. |
| **Lean** | Sonnet | Editor / Fotografia | Ritmo, transições, cor, onde entram pontes, direção de fluidez. |
| **Aki** | Haiku | Animador de câmera procedural | Escreve params por plano (c0/c1, zoom, rot, fx) pro motor → dá vida aos holds. |
| **Bea** | Haiku | Animador de overlays/vetor | Title, painéis, transições, partículas via SVG/CSS/canvas → render → composita. |
| **Caz** | Haiku | Fluidez / interpolação | RIFE/minterpolate/deflicker por clipe; testa e mede o ganho. |
| **Deni** | Haiku | QC / continuidade | Caça freeze, artefato, corte seco (folhas de contato, segmentos). |
| **Emi** | Haiku | Assets / keyframes | Extrai keyframes limpos (EbSynth/pontes), afina prompts, prepara plates. |

## Regras (economia — Sonnets são caros)
- **Sonnets (Kubrick/Lean): rédea curta.** Contexto mínimo, saída só estruturada (tabela/JSON),
  proibido prosa longa. Acionados só quando a direção realmente exige síntese.
- **Haikus: braçais**, sempre verifico a saída antes de assumir como boa (draft-verify).
- **Dante (Fable):** um acionamento, no fim, sobre o corte final. Caro — só quando eu travar.
- Não spawnar agente ocioso: cada acionamento carrega uma tarefa concreta com entregável.

## Doutrina "Haiku animador" (como texto vira animação)
1. **Câmera procedural** (Aki): o motor já consome c0/c1/zoom/rot/fx por plano — o Haiku
   escreve esses valores → move-se a câmera 2.5D sobre o frame (Ken Burns/parallax).
2. **Vetor/partícula** (Bea): SVG/SMIL/CSS/canvas → frames PNG → composita (fogo, brasa,
   luz, transições, cartelas). Fluidez vetorial onde ela funciona (overlays), como pesquisado.
3. **Interpolação** (Caz): RIFE/minterpolate geram os frames intermediários (fluidez raster).
