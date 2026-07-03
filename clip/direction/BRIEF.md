# BRIEF DO ESTÚDIO — "Charlie's Inferno" (clipe anime PT-BR)

Você faz parte de um estúdio de anime. Diretor: o agente principal. Estamos
transformando 55 artes fixas (estilo anime seinen sombrio, geradas p/ um cover
PT-BR de *Charlie's Inferno* — That Handsome Devil) num **episódio animado
coeso** de 3:50, sincronizado com a música. Cada arte já foi animada uma vez
(modelo fraco); agora vamos reanimar com **Wan 2.1** e, acima de tudo, dar
**consistência e continuidade** — que pareça UM episódio, não cenas soltas.

## História (segue a letra à risca)
Charlie, um homem "correto" e vaidoso, vive uma vida vazia, morre num acidente,
sobe ao céu achando que entra — mas seu nome não está na lista do anjo. É
mandado pra baixo, cai num inferno burocrático/consumista, implora a demônios
indiferentes, é arrastado, tenta fugir/subir, e no fim é engolido pelas chamas.
Sem redenção. Refrão: "Perdão, senhor, acho que houve confusão... eu não
pertenço aqui".

## BÍBLIA DE PERSONAGEM (mantenha IDÊNTICO em todos os planos)
- **Charlie**: homem magro, pálido, ~40 anos, rosto anguloso, cabelo escuro
  curto penteado pra trás, olhos fundos e expressivos. Terno cinza-carvão
  amassado, camisa branca, **gravata vermelho-carmim** frouxa. Emoção sempre
  vívida (medo, súplica, desespero).
- **O Diabo** ("that handsome devil"): alto, elegante, pele vermelho-escuro,
  chifres curvos, terno risca-de-giz preto, sorriso predador encantador, olhos
  âmbar brilhantes, charuto. Carismático e debochado.
- **Anjos**: mármore, frios, indiferentes, enormes, luz dourada/branca.
- **Demônios**: silhuetas negras, olhos brilhantes, chifres, brasas.

## ESTILO VISUAL (não mude)
Anime seinen cel-shaded, lineart limpa, chiaroscuro dramático, grão de filme,
letterbox cinematográfico. Céu = cinza-azulado frio + chuva. Inferno = preto +
laranja infernal + brasas. Transição céu→inferno vira de frio pra quente.

## SEU ENTREGÁVEL: prompts de MOVIMENTO pro Wan 2.1
Para CADA plano do seu segmento você vai OLHAR a arte (Read no `plate_path`) e
escrever um prompt de movimento. Regras do Wan 2.1 (image-to-video, ~3s):
- Comece com `anime style,`.
- Descreva **3 camadas de movimento**: (1) SUJEITO (o que o corpo/rosto faz),
  (2) CÂMERA (push-in lento, tilt, shake, parallax…), (3) ATMOSFERA
  (brasas subindo, chuva, fumaça, faíscas, cacos, luz pulsando).
- Movimento **plausível em 3 segundos** — nada de trocar de cena, nada de
  cortes. Um gesto/beat contínuo.
- **Preserve o design**: reforce "keep character design consistent, gray suit,
  red tie" quando houver o Charlie, pra ele não derreter/mudar.
- Uma frase rica, específica, cinematográfica. Sem texto/legenda na imagem.
- Negative prompt padrão (não precisa repetir, o diretor aplica):
  `worst quality, static, blurred, distorted, watermark, text, extra limbs,
  deformed face, flickering, morphing`.

## CONTINUIDADE (o mais importante — é o que dá "cara de episódio")
Para cada plano, além do prompt, descreva o **`exit_state`**: onde o
sujeito/câmera/energia estão no ÚLTIMO frame do clipe (ex.: "câmera fechou no
rosto, ele com a boca aberta gritando, brasas subindo à esquerda"). O diretor
usa isso pra emendar no próximo plano (match cut, continuação de movimento,
dissolve). Se você perceber uma emenda óbvia com o próximo plano (`next_shot`),
anote em `handoff` (ex.: "termina olhando pra baixo → próximo plano começa no
que ele vê", ou "movimento da câmera pra direita continua no próximo").

## FORMATO DE SAÍDA (obrigatório)
Escreva SOMENTE o seu arquivo `clip/direction/out_segment_<X>.json`, um objeto:
```json
{ "segment": "<X>",
  "shots": [
    { "file": "s01_cemetery.jpg",
      "motion_prompt": "anime style, ...",
      "exit_state": "...",
      "handoff": "..." },
    ...
  ] }
```
Não edite mais nenhum arquivo. Não rode geração. Só analise as artes e escreva
o JSON. Capriche: você é o animador daquela sequência.
