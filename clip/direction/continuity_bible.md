# CONTINUITY BIBLE — "Charlie's Inferno" (3:50, PT-BR)

Documento de coesão global. Objetivo: os 66 planos devem se ler como UM episódio de
anime seinen, não como 66 artes soltas animadas. Isto é a referência que trava
personagem, cor e regras de câmera/montagem para os 5 animadores e para o grade
final.

---

## 1. MODEL SHEET RESUMIDO (travar identidade visual)

### Charlie
- **Corpo/rosto**: magro, pálido, ~40 anos, rosto anguloso e cavado, olheiras,
  olhos fundos e muito expressivos (o principal veículo de emoção — sempre
  vívidos: medo, súplica, desespero, nunca neutros).
- **Cabelo**: curto, escuro (quase preto-azulado, `#1B1B22`), penteado pra trás,
  mechas caindo na testa quando ele sofre/corre.
- **Roupa (idêntica em 100% dos planos, mesmo danificada depois)**:
  - Terno cinza-carvão amassado — `#4A4A4D` (nunca preto puro, nunca azul).
  - Camisa branca — leve tom quente/sujo, nunca branco-papel puro.
  - **Gravata vermelho-carmim frouxa** — `#8E1B2E` a `#A32138`. É o único toque
    de cor saturada nele; funciona como "farol" visual do herói em qualquer
    plano, inclusive silhueta (deve reter um brilho mínimo de cor mesmo em
    contraluz total).
- **Regra de reforço no prompt**: sempre que ele aparecer, manter "keep
  character design consistent, gray suit, red tie" — evita derretimento de
  traços entre planos reaproveitados/flipados.

### O Diabo ("that handsome devil")
- Pele vermelho-escura — `#8A1F1F` a `#B23A2E` (mais viva/saturada que a
  gravata de Charlie — ele é a versão "cheia" daquela cor que Charlie só
  carrega em fiapo).
- Chifres curvos marrom-escuros/quase pretos, cabelo escuro curto.
- Terno risca-de-giz **preto** (nunca cinza — para não ser confundido com o
  terno de Charlie), charuto sempre presente, corrente/colar.
- Olhos âmbar brilhantes — `#FFB43D`, único elemento que deve brilhar como luz
  própria (glow) em qualquer nível de exposição da cena.
- Postura sempre relaxada/de posse (reclinado, de lado, sorriso predador) —
  contraste de linguagem corporal com a rigidez tensa de Charlie.

### Anjos
- Mármore branco/cinza-claro frio, enormes, aditivo dourado só na luz ambiente
  ao redor deles — nunca na pele/pedra. Rosto sempre parado, sem raiva nem
  pena — indiferença absoluta. Isso é o oposto do Diabo (que reage, ri,
  sorri) — reforça que o céu do clipe é mais frio que o inferno.

### Demônios (tropa)
- Silhuetas negras puras, sem detalhe de pele, só olhos/brasas brilhando
  (mesmo âmbar do Diabo, mas menor e mais "sujo"/irregular). Nunca dar rosto
  detalhado a eles — mantém o Diabo como único demônio "com rosto" do
  episódio, o que reforça sua importância narrativa.

---

## 2. COLOR SCRIPT POR ATO

A lógica: **frio → dourado → virada pro laranja → vermelho-sangue → frio de
novo**. O grade é cumulativo e gradual dentro de cada ato — não trocar de
grade abruptamente exceto nas viradas de ato marcadas com `dip` no mapa de
transições.

| Ato | Planos (i) | Paleta / mood | Grade alvo (multiplicador RGB aprox., base 1.0/1.0/1.0) | Notas de render |
|---|---|---|---|---|
| **1 — Subúrbio / Morte** | 0–11 | Cinza-azulado frio, chuva, vida vazia | R 0.85 · G 0.95 · B 1.15 | Contraste baixo-médio, saturação reduzida (~70%), leve grão, nunca preto puro nas sombras (levanta o preto ~5%) — sensação de tédio "lavado". |
| **2a — Ascensão celestial** | 12–18 | Dourado/branco quente, deslumbre | R 1.15 · G 1.08 · B 0.85 | Contraste alto, halação/bloom nos brancos, god rays. Vira o mais quente do episódio inteiro — o auge de esperança falsa de Charlie. |
| **2b — Rejeição** | 19–24 | O dourado esfria e endurece | R 1.05 → 1.0 · G 1.0 → 0.98 · B 0.9 → 1.0 (interpolar ao longo do trecho) | Mesma cena celestial, mas a luz vira dura e clínica — retirar o bloom quente gradualmente, deixar os brancos "de mármore" (frio) tomarem conta. É o presságio antes da queda. |
| **3 — A Queda** | 24–28 | Tempestade azul virando tempestade vermelha | Interpolar de R 0.85/B1.15 (Ato 1) até R 1.30/B 0.60 ao longo destes 4 planos | Esta é a rampa de cor mais importante do episódio — deve ser visível *dentro* do plano 25→26 (dissolve descrito no transition_map). Relâmpagos brancos pontuam, mas o ambiente vira de frio pra quente plano a plano. |
| **4 — Tour do Inferno** | 28–38 | Laranja infernal + preto, brasas | R 1.30 · G 0.90 · B 0.55 | Pretos esmagados (crush), highlights em laranja puro (`#FF6A1E` a `#FF9B3D`), névoa de fumaça acinzentada só pra dar profundidade — nunca azul aqui. |
| **5 — Diabo / Julgamento** | 39–51 | Vermelho-sangue entra, mais denso e teatral | R 1.35 · G 0.75 · B 0.50 | Reduz o laranja "cartunesco" do Ato 4, aumenta saturação do vermelho puro — cenas de trono/carimbo/tentação ficam quase monocromáticas em vermelho-preto, iluminação de contraluz forte (rim light). |
| **6 — Perseguição / Clímax** | 52–59 | Vermelho-sangue no limite, quase monocromático | R 1.40 · G 0.60 · B 0.45 | Contraste máximo do episódio. Exceção pontual: plano 56 (`s57_angels_above`, i=56) — luz do facho de esperança pode subir brevemente pra R 1.0/G1.0/B1.10 (frio) só na área do facho de luz, mantendo o resto do quadro vermelho — é a "esperança fria" inatingível. |
| **7 — Consumação / Epílogo** | 59–65 | Vermelho-sangue esfria de volta pro cinza-azulado inicial | Interpolar de R1.40/B0.45 (i=59) de volta a R0.85/B1.15 (i=64–65) | A dissolução (i=63) é o ponto médio da rampa de retorno. `s65_grave_return` e `s66_end` devem bater EXATAMENTE no grade do Ato 1 (mesmos planos reaproveitados) — fechamento circular, sem redenção, só o mundo frio de novo como se nada tivesse mudado. |

**Regra geral de grade**: dentro de um ato, interpole linearmente entre o
grade de entrada e saída do ato ao longo dos planos — não é um degrau único.
As únicas mudanças de grade "em degrau" (corte seco de paleta) acontecem nos
`dip`s de virada de ato (i=0, 12, 55, 64) — em todos os outros pontos a
mudança deve ser gradual, plano a plano, pra não quebrar a sensação de mundo
contínuo.

---

## 3. REGRAS DE CONTINUIDADE DE MOVIMENTO E CÂMERA

1. **Vetor de movimento consistente por sequência.** Dentro de uma mesma
   "cena" (ex.: montage da vida em i=4–10, tour do inferno i=28–38, perseguição
   i=52–59), a direção geral de movimento de câmera e do olhar de Charlie deve
   se manter no mesmo eixo (esquerda→direita ou o inverso) por pelo menos 2-3
   planos seguidos antes de inverter — inversão só é permitida em corte de
   cena ou como choque intencional (ex.: `whip`).
2. **Eyeline match sempre que Charlie olha pra algo que o próximo plano
   revela** (anjo → livro; escada em espiral → poço; ele olha pra cima →
   anjos indiferentes no topo). Use isso como cola narrativa, não decoração.
3. **Match de escala/composição como eco temático.** O episódio repete 3
   vezes o motivo "figura enorme com livro julgando Charlie pequeno" (anjo
   com ledger, demônio-escrivão com ledger, cinzas do próprio livro
   derretendo). Cada vez que esse motivo reaparecer, a composição
   (verticalidade, ângulo worm's-eye, posição do livro no quadro) deve casar
   o mais próximo possível — é o que dá sensação de "roteiro visual", não
   coincidência de asset.
4. **Continuidade de queda física.** A sequência de queda (chão do céu se
   abre → tempestade → poço do inferno) é fisicamente UMA queda contínua de
   ~12s dividida em 4 planos. Câmera deve manter a mesma velocidade
   percebida de queda (não desacelerar entre planos) e o corpo de Charlie
   deve manter a mesma orientação relativa (de bruços, braços pra cima)
   plano a plano.
5. **Planos reaproveitados/flipados não são "preenchimento".** Cada reuso
   (`reuse_of`) deve ser tratado como uma variação dramática legítima — o
   segundo uso precisa ganhar um motivo de câmera/luz levemente diferente
   (zoom mais fechado, ou a cor já mudou por causa do color script) pra não
   parecer um loop preguiçoso. Nunca cortar direto entre um plano e seu
   próprio reuso sem pelo menos uma pequena progressão (de escala, de cor ou
   de tempo de tela).
6. **Silhueta e gravata como âncora em contraluz.** Em qualquer plano de
   Charlie em silhueta/contraluz (queda, portão do inferno, corredor,
   consumação final), a gravata vermelha deve manter um mínimo de saturação
   visível — é o "farol" que garante que o espectador sempre o reconheça
   mesmo sem luz frontal.
7. **Ritmo de corte casa com a estrutura musical.** Os dois "montages" do
   episódio (vida em subúrbio, i=4–10; tour do inferno, i=30–36) usam corte
   seco e rápido no beat (~0.15s de transição) propositalmente — é o único
   trecho onde cortes secos consecutivos são desejáveis, simulando um
   estribilho/verso cantado em versos curtos. Fora desses dois trechos,
   cortes secos consecutivos (mais de 2 seguidos) devem ser evitados; prefira
   dissolve curto ou continuidade de movimento.
8. **Escala emocional cresce, nunca recua, dentro de um ato.** Do plano de
   entrada ao de saída de cada ato (exceto os de alívio irônico, como
   `they_walk`), o nível de desespero/violência da pose e da câmera (mais
   dutch angle, mais close, mais tremor) deve aumentar — se um animador
   entregar um plano "calmo demais" no meio de uma escalada, o diretor deve
   compensar no grade/velocidade, não na pose.
9. **Bookend estrutural.** Abertura (i=0, cemitério largo) e fechamento (i=65,
   mesmo plano reaproveitado) devem ser tratados como espelho um do outro —
   mesmo enquadramento, mesmo grade, para fechar o círculo "ele morre, desce
   ao inferno, o mundo dos vivos segue idêntico e frio, sem redenção".
