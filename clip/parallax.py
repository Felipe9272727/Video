#!/usr/bin/env python3
"""Animação 2.5D por profundidade (CPU, ilimitado). Dado o plate + seu mapa de
profundidade, sintetiza parallax multiplano: a câmera faz um pequeno orbit/dolly
e as camadas de profundidade se deslocam em velocidades diferentes -> sensação 3D
em vez de imagem parada. Usado pelo assemble.py nos planos sem clipe Wan.
"""
import os
import numpy as np
from PIL import Image

_dcache = {}
def load_depth(stem, w, h):
    key = (stem, w, h)
    if key not in _dcache:
        p = f"build/depth/{stem}.png"
        if not os.path.exists(p):
            _dcache[key] = None
        else:
            d = Image.open(p).convert("L").resize((w, h), Image.BILINEAR)
            dd = np.asarray(d).astype(np.float32) / 255.0
            # suaviza e realça contraste de profundidade
            _dcache[key] = dd
    return _dcache[key]

# grade base reutilizável por tamanho
_grid = {}
def grid(w, h):
    if (w, h) not in _grid:
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        _grid[(w, h)] = (xs, ys)
    return _grid[(w, h)]

def bilinear(img, sx, sy):
    h, w = img.shape[:2]
    sx = np.clip(sx, 0, w - 1.001); sy = np.clip(sy, 0, h - 1.001)
    x0 = np.floor(sx).astype(np.int32); y0 = np.floor(sy).astype(np.int32)
    x1 = x0 + 1; y1 = y0 + 1
    wx = (sx - x0)[..., None]; wy = (sy - y0)[..., None]
    return (img[y0, x0] * (1 - wx) * (1 - wy) + img[y0, x1] * wx * (1 - wy)
            + img[y1, x0] * (1 - wx) * wy + img[y1, x1] * wx * wy)

def parallax_view(rgb, depth, out_w, out_h, cx, cy, zoom, rot, tx, ty, dz):
    """Renderiza uma vista (out_w x out_h) do plate com parallax por profundidade.
    cx,cy: centro do crop (0..1). zoom: fator base. rot: rad. tx,ty: translação de
    câmera (parallax lateral/vertical, em fração da largura). dz: dolly por profundidade."""
    ih, iw = rgb.shape[:2]
    xs, ys = grid(out_w, out_h)
    # crop base (afim: zoom+rotação centrado em cx,cy)
    crop_w = iw / zoom
    crop_h = crop_w * out_h / out_w
    if crop_h > ih:
        crop_h = ih; crop_w = crop_h * out_w / out_h
    cxp = min(max(cx * iw, crop_w / 2), iw - crop_w / 2)
    cyp = min(max(cy * ih, crop_h / 2), ih - crop_h / 2)
    s = crop_w / out_w
    cosr, sinr = np.cos(rot), np.sin(rot)
    # coords base no plate
    bx = cxp + (xs - out_w / 2) * s * cosr - (ys - out_h / 2) * s * sinr
    by = cyp + (xs - out_w / 2) * s * sinr + (ys - out_h / 2) * s * cosr
    # amostra profundidade nessas coords (near=1)
    d = bilinear(depth[..., None], bx, by)[..., 0]
    dc = d - 0.5  # centrado: perto>0, longe<0
    # parallax: perto desloca mais na direção da câmera; dolly empurra perto pra fora
    px = tx * iw * dc
    py = ty * ih * dc
    scaledz = 1.0 + dz * dc
    sx = cxp + ((bx - cxp) * scaledz) + px
    sy = cyp + ((by - cyp) * scaledz) + py
    out = bilinear(rgb, sx, sy)
    return np.clip(out, 0, 255).astype(np.uint8)
