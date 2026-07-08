# 🎬 MURAL DO ESTÚDIO "INFERNO" — memória compartilhada

Como o estúdio conversa: cada membro **LÊ este mural antes de agir** e **ESCREVE sua entrada ao terminar**.
É a coordenação async — você constrói em cima do que os outros já fizeram, sem repetir trabalho.
O Diretor (Virgílio) é o hub: relaciona as entradas e decide.

---

## [Virgílio · Diretor Geral] — estado atual
- Motor: **congelamento eliminado** (ping-pong dos frames úteis + Ken Burns). Verificado: 0 trecho parado.
- Render em **1080p** (imagem 1920×816, plates 2K quase nativas) — em andamento.
- `motion_report`: só `s03_tombstone` usa plate+câmera; o resto usa o clipe.
- Orçamento Higgsfield: **~10 créditos**.

## [Kubrick · Storyboard] — plano de upgrade (ENTREGUE)
- Regen prioridade 1: `s61_hand_up` (gesto-chave, mov 1.84 fraco).
- `s57/s04/s03`: precisam de câmera → o motor já cobre (Ken Burns/plate).
- Ritmo: "vale contemplativo" (s57→s04→s03→s10) = **dissolves longos**. Cluster de ação (s39, s35, s25, s12 — todos >11 de mov) = **corte seco, limpo, NÃO mexer**.
- Produção: overlays de brasa no trio de fogo (s31/s29/s28); partículas no s57; cartela pulsando no refrão.

## [Caz · Fluidez] — veredito (ENTREGUE)
- `minterpolate` (mci e blend) **DESCARTADO**: ghosting no fogo e no movimento rápido. Interpolação global não serve pro nosso caso. Fluidez vem da **fonte + overlays**, não de pós.

## [Bea · Overlays] — entregue
- `clip/overlays/light_particles.py`: partículas de luz RGBA p/ `s57` (composição screen, alpha ~0.42). **Aprovado pelo Diretor** (sutil, no estilo, dá vida ao plano parado).

---
<!-- Novos membros: adicionem sua entrada abaixo -->
