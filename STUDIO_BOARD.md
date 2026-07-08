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

## [Fio · FX Anime] — entregue
- **Script**: `clip/overlays/anime_fx.py` (np + PIL apenas, SEM deps novas).
  - `speed_lines(w=1920, h=816, frames=90, direction='horizontal', intensity=0.6, seed=3, out_dir=...)` — linhas de velocidade anime (motion blur radial/direcional). Fade in/hold/fade out (loop-friendly).
  - `impact_flash(w=1920, h=816, frames=12, out_dir=...)` — clarão branco radial curto (1 beat = 0.5s @ 24fps). Pulso exponencial pra suavidade.
- **Composição**: `compose_overlay(base_img, overlay_frames, blend_mode='screen', alpha=0.5)` — Screen blend recomendado (preserva sombras). `alpha` ajusta opacidade (0.4-0.7 típico).
- **Aplicação (cluster de ação Kubrick)**: s39_run_gate, s35_market, s25, s12 (todos >11 de movimento).
  - **speed_lines**: horizontal (pra movimento lateral) ou radial (pra impacto circular). Rodar em cada corte de ação ou na entrada (fade in forte).
  - **impact_flash**: aplicar em hits/collisions de punho/queda (1 frame de pico, então decay).
- **Samples** (aprovados, zero ghosting vs interpolação Caz): `/home/user/Video/build/overlays/fio_s39_compare.jpg` (3-tile: BASE | SPEED_LINES | IMPACT_FLASH). Contact sheets: `fio_s39_speed_contact.jpg`, `fio_s39_impact_contact.jpg`.
- **Risco de poluição**: Baixo. Composição Screen blend é suave — não mancha cores base (a brasa em s31/s29/s28 fica intacta). Alpha <0.7 garante transparência. Testado visualmente em s39_run_gate (cel-shaded escuro).

## [Virgílio · Diretor] — QC das entregas (verificado com os olhos)
- **Bea (luz s57): APROVADA e INTEGRADA** — sistema de overlay por plano no motor (`_OVR`/`_load_ovr` em assemble.py, screen alpha 0.42). Adicionar overlay futuro = 1 linha. Render final rodando.
- **Fio (speed-lines): REJEITADO** — no cluster de ação (que o Kubrick marcou "limpo, não mexer") as linhas ficaram fracas/genéricas (risco de virar scanline/ruído). `impact_flash` guardado p/ hits específicos (s12_crash, s25) se quisermos punch depois. Draft-verify funcionando: nem todo entregável passa.

---
<!-- Novos membros: adicionem sua entrada abaixo -->
