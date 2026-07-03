#!/usr/bin/env python3
"""Charlie's Inferno — cinematic assembly engine.

Takes Higgsfield-painted 21:9 stills (clip/shots/*.jpg) + a storyboard
(clip/storyboard.json) + per-frame audio features (build/timeline.json)
and renders the full music video with a moving camera:

  - camera paths per shot: push-in / pull-out / pan / dutch roll, eased
  - crash-zoom kicks + micro shake driven by the music's beat envelope
  - transitions: hard cut, whip pan, flash cut, dip-to-black, crossfade
  - overlays: embers, rain, god-rays, heat ripple
  - post: beat flash, chromatic aberration, vignette, film grain, letterbox

Usage:
  python3 clip/assemble.py            # full render -> out/charlie_inferno_cinematic.mp4
  python3 clip/assemble.py probe 12.5 40 88   # dump single frames -> build/probe_*.jpg
"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageFont, ImageDraw, ImageFilter

W, H = 1280, 720
AW, AH = 1280, 544            # active 21:9-ish picture area (even for yuv420)
BAR = (H - AH) // 2
FPS = 24
MP3 = "Charlie_s Inferno (Excuse Me Sir) - That Handsome Devil _ COVER PT-BR(MP3_160K)_1.mp3"
OUT = "out/charlie_inferno_cinematic.mp4"

TL = json.load(open("build/timeline.json"))
FR = TL["frames"]; NF = TL["count"]; DUR = TL["duration"]
SB = json.load(open("clip/storyboard.json"))
SHOTS = SB["shots"]

# motor de parallax 2.5D (profundidade -> movimento de câmera 3D em planos sem Wan)
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("parallax", os.path.join(os.path.dirname(__file__), "parallax.py"))
PLX = _ilu.module_from_spec(_spec); _spec.loader.exec_module(PLX)

# ------------------------------------------------------------------ easing
def ease(name, t):
    t = min(1.0, max(0.0, t))
    if name == "lin":  return t
    if name == "in":   return t * t
    if name == "out":  return 1 - (1 - t) ** 2
    if name == "io":   return t * t * (3 - 2 * t)
    if name == "outc": return 1 - (1 - t) ** 3       # strong decel (crash-zoom settle)
    if name == "inc":  return t ** 3                  # strong accel (run-up)
    return t

# ------------------------------------------------------------------ smooth noise (handheld)
rng = np.random.default_rng(7)
_nk = rng.standard_normal((6, 4096)).astype(np.float64)
for i in range(6):
    k = np.ones(31) / 31
    _nk[i] = np.convolve(_nk[i], k, "same")
    _nk[i] /= (np.abs(_nk[i]).max() + 1e-9)
def noise(ch, t, speed=1.0):
    x = (t * 24.0 * speed) % 4095
    i = int(x); f = x - i
    return _nk[ch][i] * (1 - f) + _nk[ch][i + 1] * f

# ------------------------------------------------------------------ shot images
_imcache = {}
def shot_img(s):
    fname = s.get("src") or s["file"]
    key = (fname, bool(s.get("flip")))
    if key not in _imcache:
        im = Image.open(os.path.join("clip/shots", fname)).convert("RGB")
        # normalize height for stable math; keep native width for detail
        if im.height > 1100:
            im = im.resize((int(im.width * 1100 / im.height), 1100), Image.LANCZOS)
        if s.get("flip"):
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        _imcache[key] = im
    return _imcache[key]

# ------------------------------------------------------------------ motion clips (image-to-video Higgsfield)
# Se existir clip/motion/<stem>.mp4 para o shot (ou para a plate de origem em
# reusos), o clipe animado substitui o still + camera path; o pós (flash,
# aberração, tint, vinheta, grão, letterbox) continua por cima.
_motion_cache = {}
def get_motion(s):
    import subprocess as sp
    for base in [s["file"], s.get("src") or ""]:
        if not base:
            continue
        path = os.path.join("clip/motion", os.path.splitext(base)[0] + ".mp4")
        if os.path.exists(path):
            if path not in _motion_cache:
                if len(_motion_cache) > 2:
                    _motion_cache.clear()
                import imageio_ffmpeg
                ff = imageio_ffmpeg.get_ffmpeg_exe()
                cmd = [ff, "-loglevel", "error", "-i", path,
                       "-vf", f"scale={AW}:{AH}:force_original_aspect_ratio=increase,crop={AW}:{AH}",
                       "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
                raw = sp.run(cmd, capture_output=True).stdout
                n = len(raw) // (AW * AH * 3)
                _motion_cache[path] = np.frombuffer(raw[:n * AW * AH * 3], np.uint8).reshape(n, AH, AW, 3)
            return _motion_cache[path]
    return None

# ------------------------------------------------------------------ camera
def cam_frame(s, im, tl, dur, gf):
    """Render the eased, shaken, rotated crop of shot s at local time tl -> (AW,AH) RGB."""
    c = s.get("cam", {})
    e = ease(c.get("ease", "io"), tl / max(dur, 1e-6))
    z0, z1 = c.get("z", [1.06, 1.22])[:2]
    x0, y0 = c.get("c0", [0.5, 0.5]); x1, y1 = c.get("c1", [0.5, 0.5])
    r0, r1 = c.get("rot", [0.0, 0.0])
    z = z0 + (z1 - z0) * e
    cx = x0 + (x1 - x0) * e
    cy = y0 + (y1 - y0) * e
    rot = math.radians(r0 + (r1 - r0) * e)

    f = FR[min(gf, NF - 1)]
    # beat kick: extra zoom + roll on strong hits
    kick = s.get("kick", 0.0)
    z *= 1.0 + 0.055 * kick * f["beat"]
    rot += math.radians(0.5 * kick * f["beat"] * noise(3, tl, 2.0))
    # handheld shake scaled by music energy
    sh = s.get("shake", 0.0) * (0.35 + 0.65 * f["e"])
    cx += 0.006 * sh * noise(0, tl, 1.7)
    cy += 0.008 * sh * noise(1, tl, 1.9)
    rot += math.radians(0.7 * sh * noise(2, tl, 1.3))

    iw, ih = im.size
    crop_w = iw / z
    crop_h = crop_w * AH / AW
    if crop_h > ih:
        crop_h = ih; crop_w = crop_h * AW / AH
    # clamp center so the rotated crop stays inside the plate
    mg = 0.5 * (abs(math.sin(rot)) * crop_w + abs(math.cos(rot)) * crop_h)
    mgx = 0.5 * (abs(math.cos(rot)) * crop_w + abs(math.sin(rot)) * crop_h)
    cxp = min(max(cx * iw, mgx), iw - mgx)
    cyp = min(max(cy * ih, mg), ih - mg)

    s_ = crop_w / AW
    cosr, sinr = math.cos(rot), math.sin(rot)
    a = s_ * cosr; b = -s_ * sinr
    d = s_ * sinr; ee = s_ * cosr
    cxo = cxp - (a * AW / 2 + b * AH / 2)
    cyo = cyp - (d * AW / 2 + ee * AH / 2)
    return im.transform((AW, AH), Image.AFFINE, (a, b, cxo, d, ee, cyo), resample=Image.BILINEAR)

# ------------------------------------------------------------------ particle overlays
NE = 140
epx = rng.random(NE) * AW; eph = rng.random(NE) * 1000
esp = 0.10 + rng.random(NE) * 0.38; esz = rng.integers(2, 6, NE)
ewb = 10 + rng.random(NE) * 46; ewf = 0.4 + rng.random(NE) * 1.5
SP = 17; _s = np.linspace(-2, 2, SP)
SPR = np.exp(-(_s[None, :] ** 2 + _s[:, None] ** 2))[..., None].astype(np.float32)
EMBER = SPR * np.array([255, 130, 40], np.float32)
def add_embers(fr, t, e, dense=1.0):
    for k in range(int(NE * dense)):
        prog = (t * esp[k] + eph[k]) % 1.0
        ey = AH - prog * (AH + 60) + 20
        exx = (epx[k] + math.sin(t * ewf[k] + eph[k]) * ewb[k]) % AW
        fl = 0.65 + 0.35 * math.sin(t * 8 + eph[k] * 3)
        amp = fl * (0.4 + 0.8 * e) * (esz[k] / 5.0)
        x0i = int(exx) - SP // 2; y0i = int(ey) - SP // 2
        fx0, fy0 = max(0, x0i), max(0, y0i)
        fx1, fy1 = min(AW, x0i + SP), min(AH, y0i + SP)
        if fx0 >= fx1 or fy0 >= fy1: continue
        fr[fy0:fy1, fx0:fx1] += EMBER[fy0 - y0i:fy1 - y0i, fx0 - x0i:fx1 - x0i] * amp

NR = 170
rpx = rng.random(NR) * AW; rph = rng.random(NR) * 1000
rsp = 1.6 + rng.random(NR) * 1.4; rln = 14 + rng.random(NR) * 22
def add_rain(im, t, amt=1.0):
    d = ImageDraw.Draw(im, "RGBA")
    for k in range(int(NR * amt)):
        prog = (t * rsp[k] + rph[k]) % 1.0
        ry = prog * (AH + 80) - 40
        rx = (rpx[k] - prog * 26) % AW
        d.line([(rx, ry), (rx - 3, ry + rln[k])], fill=(190, 205, 225, 70), width=1)

_ray_grad = None
def add_rays(fr, t, amt=1.0):
    global _ray_grad
    if _ray_grad is None:
        yy, xx = np.mgrid[0:AH, 0:AW].astype(np.float32)
        ang = np.arctan2(yy + 300, xx - AW * 0.5)
        _ray_grad = (0.5 + 0.5 * np.sin(ang * 26.0)) * np.clip(1.1 - yy / AH, 0, 1)
    fl = 0.75 + 0.25 * math.sin(t * 1.7)
    fr += (_ray_grad * 34 * amt * fl)[..., None] * np.array([255, 230, 180], np.float32) / 255.0

# ------------------------------------------------------------------ post
vx = np.linspace(-1, 1, AW)[None, :]; vy = np.linspace(-1, 1, AH)[:, None]
VIG = np.clip(1.10 - 0.62 * np.clip(np.sqrt(vx ** 2 + (vy * 0.7) ** 2) - 0.3, 0, 1.4), 0.24, 1.0)[..., None]
GRAINS = [(rng.random((AH, AW, 1)).astype(np.float32) - 0.5) for _ in range(7)]

def find_shot(t):
    for i, s in enumerate(SHOTS):
        if s["t0"] <= t < s["t1"]:
            return i, s
    return len(SHOTS) - 1, SHOTS[-1]

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
def title(im, lines, y, size, fill, alpha, tracking=6):
    if not os.path.exists(FONT): return
    fnt = ImageFont.truetype(FONT, size)
    d = ImageDraw.Draw(im, "RGBA")
    for li, ln in enumerate(lines):
        txt = (" " * 1).join(ln)  # letterspacing
        bb = d.textbbox((0, 0), txt, font=fnt)
        tw = bb[2] - bb[0]
        x = (W - tw) / 2
        yy = y + li * size * 1.3
        d.text((x + 3, yy + 3), txt, font=fnt, fill=(0, 0, 0, int(alpha * 0.8)))
        d.text((x, yy), txt, font=fnt, fill=fill + (int(alpha),))
    return im

# ------------------------------------------------------------------ direção do estúdio
# transition map (Sonnet), hooks "Perdão senhor", color script por ato.
try:
    TMAP = {t["i"]: t for t in json.load(open("clip/direction/transition_map.json"))["transitions"]}
except Exception:
    TMAP = {}
TRDUR = {"cut": 0.0, "match_cut": 0.12, "motion_continue": 0.25, "dissolve": 0.4,
         "flash": 0.12, "whip": 0.17, "dip": 0.22}
try:
    HOOK_TS = [h["t"] for h in json.load(open("clip/direction/hooks.json"))["hooks"]]
except Exception:
    HOOK_TS = []
HOOK_W = 1.4  # janela de destaque do gancho (s)

# color script: keyframes (índice do plano -> multiplicador RGB), interpolado
GKF = [(0, (.85, .95, 1.15)), (11, (.85, .95, 1.15)), (12, (1.15, 1.08, .85)),
       (18, (1.15, 1.08, .85)), (19, (1.05, 1.0, .90)), (24, (1.0, .98, 1.0)),
       (25, (.90, .96, 1.10)), (28, (1.30, .90, .55)), (38, (1.30, .90, .55)),
       (39, (1.35, .75, .50)), (51, (1.35, .75, .50)), (52, (1.40, .60, .45)),
       (59, (1.40, .60, .45)), (64, (.85, .95, 1.15)), (65, (.85, .95, 1.15))]
def grade_for(i):
    if i <= GKF[0][0]: return np.array(GKF[0][1], np.float32)
    if i >= GKF[-1][0]: return np.array(GKF[-1][1], np.float32)
    for k in range(len(GKF) - 1):
        a, ca = GKF[k]; b, cb = GKF[k + 1]
        if a <= i <= b:
            f = (i - a) / (b - a) if b > a else 0.0
            return np.array([ca[j] + (cb[j] - ca[j]) * f for j in range(3)], np.float32)
    return np.array((1., 1., 1.), np.float32)

def parallax_frame(s, tl, dur, gf):
    """Câmera 2.5D por profundidade: frente e fundo se movem em velocidades
    diferentes -> vida 3D em cima do still. Fallback pra câmera plana se não há depth."""
    stem = (s.get("src") or s["file"]).replace(".jpg", "")
    im = shot_img(s)
    w, h = im.size
    depth = PLX.load_depth(stem, w, h)
    if depth is None:
        return cam_frame(s, im, tl, dur, gf)
    rgb = np.asarray(im).astype(np.float32)
    if s.get("flip"):
        rgb = rgb[:, ::-1].copy(); depth = depth[:, ::-1].copy()
    c = s.get("cam", {})
    p = ease(c.get("ease", "io"), tl / max(dur, 1e-6))
    z0, z1 = c.get("z", [1.06, 1.2])[:2]; zoom = z0 + (z1 - z0) * p
    x0, y0 = c.get("c0", [0.5, 0.5]); x1, y1 = c.get("c1", [0.5, 0.5])
    cx = x0 + (x1 - x0) * p; cy = y0 + (y1 - y0) * p
    r0, r1 = c.get("rot", [0, 0]); rot = math.radians(r0 + (r1 - r0) * p)
    t = gf / FPS; f = FR[min(gf, NF - 1)]
    ph = (hash(stem) % 100) / 100.0 * 6.28
    # parallax lateral/vertical evolui ao longo do plano (varredura) + deriva idle
    tx = 0.075 * (x1 - x0) + 0.055 * (p - 0.5) + 0.012 * math.sin(t * 0.55 + ph)
    ty = 0.05 * (y1 - y0) + 0.022 * (p - 0.5) + 0.008 * math.sin(t * 0.45 + ph)
    dz = 0.16 * (zoom - 1.0) + 0.03 + 0.03 * f["beat"]     # dolly em perspectiva + batida
    out = PLX.parallax_view(rgb, depth, AW, AH, cx, cy, zoom, rot, tx, ty, dz)
    return Image.fromarray(out)

def build_content(s, si, tl, dur, gf):
    """Conteúdo do plano (motion clip OU câmera 2.5D sobre still) + embers/rays/chuva.
    Sem vinheta/grão/grade — isso é global, aplicado depois."""
    mo = get_motion(s)
    if mo is not None:
        idx = min(len(mo) - 1, max(0, int(tl / max(dur, 1e-6) * len(mo))))
        frame = mo[idx]
        if s.get("flip"):
            frame = frame[:, ::-1]
        pic = Image.fromarray(np.ascontiguousarray(frame))
    else:
        pic = parallax_frame(s, tl, dur, gf)
    fr = np.asarray(pic).astype(np.float32)
    t = gf / FPS
    e = FR[min(gf, NF - 1)]["e"]
    fx = s.get("fx", [])
    if "embers" in fx: add_embers(fr, t, e, 1.0)
    if "embers_lite" in fx: add_embers(fr, t, e, 0.45)
    if "rays" in fx: add_rays(fr, t, 1.0)
    if "rain" in fx or "rain_lite" in fx:
        im = Image.fromarray(np.clip(fr, 0, 255).astype(np.uint8))
        add_rain(im, t, 1.0 if "rain" in fx else 0.4)
        fr = np.asarray(im).astype(np.float32)
    return fr

def render_frame(gf):
    t = gf / FPS
    si, s = find_shot(t)
    dur = s["t1"] - s["t0"]; tl = t - s["t0"]
    f = FR[min(gf, NF - 1)]
    cur = build_content(s, si, tl, dur, gf)

    # ---- transição de ENTRADA (mapa do diretor de continuidade)
    tr = TMAP.get(si, {})
    ttype = tr.get("in", s.get("in", "cut"))
    tdur = float(tr.get("dur") or TRDUR.get(ttype, 0.0))
    if si > 0 and ttype in ("dissolve", "motion_continue", "match_cut") and 0 <= tl < tdur:
        prev = SHOTS[si - 1]; pdur = prev["t1"] - prev["t0"]
        pcont = build_content(prev, si - 1, pdur + tl, pdur, gf)
        k = ease("io", tl / tdur)
        cur = pcont * (1 - k) + cur * k
    elif si > 0 and ttype == "whip" and tl < 0.17:
        prev = SHOTS[si - 1]; pdur = prev["t1"] - prev["t0"]
        pcont = build_content(prev, si - 1, pdur + tl, pdur, gf)
        k = tl / 0.17
        cur = pcont * (1 - k) + cur * k
        sh = int(48 * (1 - abs(2 * k - 1)))
        if sh > 0:
            cur = 0.5 * cur + 0.5 * np.roll(cur, sh, axis=1)
    if ttype == "flash" and tl < 0.12:
        cur += 255 * (1 - tl / 0.12) * np.array([1.0, 0.82, 0.6], np.float32) * 0.85
    if ttype == "dip" and tl < 0.22:
        cur *= ease("out", tl / 0.22)
    if s.get("out") == "dip" and (s["t1"] - t) < 0.22:
        cur *= ease("out", (s["t1"] - t) / 0.22)

    # ---- beat flash + aberração cromática
    if f["onset"] > 0.55:
        cur += 46 * s.get("flash", 0.5) * f["onset"]
    ab = int(5 * s.get("aberr", 0.6) * f["beat"])
    if ab > 0:
        cur[..., 0] = np.roll(cur[..., 0], ab, axis=1)
        cur[..., 2] = np.roll(cur[..., 2], -ab, axis=1)

    # ---- COLOR SCRIPT por ato (grade global interpolado)
    cur *= grade_for(si)

    # ---- DESTAQUE "Perdão, senhor..." (gancho/refrão): crash-zoom + pulso vermelho + vinheta
    for th in HOOK_TS:
        if th <= t < th + HOOK_W:
            u = (t - th) / HOOK_W; p = 1 - u
            z = 1 + 0.13 * ease("out", min(1.0, u * 6.0))   # fecha rápido e segura no rosto
            if z > 1.001:
                im = Image.fromarray(np.clip(cur, 0, 255).astype(np.uint8))
                nw, nh = int(AW * z), int(AH * z)
                im = im.resize((nw, nh), Image.BILINEAR).crop(
                    ((nw - AW) // 2, (nh - AH) // 2, (nw - AW) // 2 + AW, (nh - AH) // 2 + AH))
                cur = np.asarray(im).astype(np.float32)
            cur *= np.array([1 + 0.22 * p, 1 - 0.08 * p, 1 - 0.13 * p], np.float32)  # sangue
            if u < 0.06:
                cur += 46 * (1 - u / 0.06)                   # micro white-flash no ataque
            cur *= VIG ** (0.7 * p)                          # vinheta extra fechando
            break

    cur *= VIG
    cur += GRAINS[gf % 7] * 13
    pic = Image.fromarray(np.clip(cur, 0, 255).astype(np.uint8))

    # ---- compose letterbox canvas
    cv = Image.new("RGB", (W, H), (0, 0, 0))
    cv.paste(pic, (0, BAR))

    # ---- titles
    if t < 6.5:
        al = min(1.0, max(0.0, (t - 1.2) / 1.2)) * min(1.0, max(0.0, (6.5 - t) / 0.8))
        title(cv, ["CHARLIE'S INFERNO"], H * 0.30, 64, (245, 228, 205), 255 * al)
        title(cv, ["that handsome devil — cover pt-br"], H * 0.44, 22, (210, 180, 150), 220 * al)
    if t > DUR - 12.5:
        al = min(1.0, (t - (DUR - 12.5)) / 1.5)
        title(cv, ["CHARLIE'S INFERNO"], H * 0.34, 58, (255, 210, 120), 255 * al)
        title(cv, ["( excuse me sir )"], H * 0.47, 24, (230, 170, 120), 230 * al)

    # ---- global fade in/out
    g = 1.0
    if t < 1.0: g = t / 1.0
    if t > DUR - 1.6: g = max(0.0, (DUR - t) / 1.6)
    if g < 1.0:
        cv = Image.eval(cv, (lambda v, gg=g: int(v * gg)))
    return np.asarray(cv)

# ------------------------------------------------------------------ main
if len(sys.argv) > 1 and sys.argv[1] == "probe":
    for ts in sys.argv[2:]:
        tt = float(ts)
        Image.fromarray(render_frame(int(tt * FPS))).save(f"build/probe_{tt:07.2f}.jpg", quality=88)
        print("probe", tt)
    sys.exit(0)

import imageio_ffmpeg
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
cmd = [FFMPEG, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
       "-i", MP3, "-map", "0:v", "-map", "1:a",
       "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k",
       "-af", "afade=t=in:st=0:d=0.3,afade=t=out:st=%.2f:d=1.4" % (DUR - 1.4),
       "-movflags", "+faststart", "-shortest", OUT]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
for i in range(NF):
    proc.stdin.write(render_frame(i).tobytes())
    if i % 240 == 0:
        print(f"frame {i}/{NF} ({100 * i // NF}%)", flush=True)
proc.stdin.close(); proc.wait()
print("DONE ->", OUT)
