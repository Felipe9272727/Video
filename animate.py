#!/usr/bin/env python3
"""Charlie's Inferno - original animated short (PT-BR cover, 'perdão senhor').
Narrative: Charlie dies, falls into a bureaucratic Hell, pleads his case at the
demon clerk's desk, and gets dragged through the fiery door by guards.
"""
import sys, math, subprocess
import numpy as np
from PIL import Image, ImageFilter
import imageio_ffmpeg
import engine as E
from engine import (Canvas, draw_person, draw_text, key, lerp, clerp, smooth, rot,
                    W, H, S, SKIN, SKIN_SH, DRED, DRED_SH, SUIT, ANTON)

FPS = 30
TEST = len(sys.argv) > 1 and sys.argv[1] == 'test'
N = 1200  # 40s

# ---------------------------------------------------------------- audio feats
F = np.load('scratch/feat.npz')
energy = F['energy']; bass = F['bass']; flux = F['flux']; mid = F['mid']
onsets = np.load('scratch/onsets.npy'); beatlag = int(np.load('scratch/beatlag.npy')[0])
def envz(src, tau, amp_from_flux=True):
    e = np.zeros(N)
    for p in src:
        a = (0.5 + 0.5 * flux[p]) if amp_from_flux else 1.0
        idx = np.arange(p, min(N, p + int(tau * 6)))
        e[idx] = np.maximum(e[idx], a * np.exp(-(idx - p) / tau))
    return e
punch = envz(onsets, 5.0)
strong = [p for p in onsets if flux[p] > np.quantile(flux[onsets], 0.7)]
flash = envz(strong, 2.0)
offset = int(np.argmax(np.bincount(onsets % beatlag, minlength=beatlag)))
beats = [i for i in range(N) if (i - offset) % beatlag == 0]
beatpulse = envz(beats, 4.0, amp_from_flux=False)
def sm(a, k=5):
    return np.convolve(a, np.ones(k) / k, mode='same')
energy_s = sm(energy); mid_s = sm(mid, 3)

# ---------------------------------------------------------------- bg gradients (SS res)
def vgrad(stops):
    yy = np.linspace(0, 1, H * S)[:, None]
    cols = np.zeros((H * S, 3))
    ts = [s[0] for s in stops]
    for i in range(len(stops) - 1):
        t0, c0 = stops[i]; t1, c1 = stops[i + 1]
        m = (yy[:, 0] >= t0) & (yy[:, 0] <= t1)
        f = (yy[m, 0] - t0) / (t1 - t0)
        for ch in range(3):
            cols[m, ch] = c0[ch] + (c1[ch] - c0[ch]) * f
    arr = np.repeat(cols[:, None, :], W * S, axis=1).astype(np.uint8)
    return arr
SKY = vgrad([(0, (24, 6, 14)), (0.45, (96, 16, 18)), (0.8, (168, 40, 18)), (1, (210, 70, 22))])
HALL = vgrad([(0, (16, 8, 18)), (0.5, (34, 14, 22)), (0.78, (40, 16, 22)), (0.781, (26, 10, 16)), (1, (16, 6, 10))])
DOORG = vgrad([(0, (20, 12, 18)), (0.5, (30, 16, 20)), (1, (22, 10, 14))])

# ---------------------------------------------------------------- embers (post, final res)
rng = np.random.default_rng(11)
NE = 150
ex = rng.random(NE) * W; eph = rng.random(NE) * 1000
esp = 0.12 + rng.random(NE) * 0.4; esz = 0.4 + rng.random(NE) * 1.3
ebr = 0.3 + rng.random(NE) * 0.6; ewb = 8 + rng.random(NE) * 40; ewf = 0.4 + rng.random(NE) * 1.4
SP = 25; _s = np.linspace(-2, 2, SP)
SPR = np.exp(-(_s[None, :] ** 2 + _s[:, None] ** 2))[..., None] * np.array([255, 140, 45], np.float32)
def stamp(fr, cx, cy, amp, spr=SPR):
    s = spr.shape[0]; h = s // 2
    x0 = int(cx) - h; y0 = int(cy) - h
    fx0 = max(0, x0); fy0 = max(0, y0); fx1 = min(W, x0 + s); fy1 = min(H, y0 + s)
    if fx0 >= fx1 or fy0 >= fy1: return
    fr[fy0:fy1, fx0:fx1] += spr[fy0 - y0:fy1 - y0, fx0 - x0:fx1 - x0] * amp
def add_embers(fr, t, e, dense=1.0):
    for k in range(int(NE * dense)):
        prog = (t * esp[k] + eph[k]) % 1.0
        ey = H - prog * H * 1.05
        exx = ex[k] + math.sin(t * ewf[k] + eph[k]) * ewb[k]
        fl = 0.6 + 0.4 * math.sin(t * 7 + eph[k] * 3)
        stamp(fr, exx, ey, ebr[k] * fl * (0.45 + 0.7 * e) * 0.5 * esz[k])

# vignette + grain
vx = np.linspace(-1, 1, W)[None, :]; vy = np.linspace(-1, 1, H)[:, None]
vig = np.clip(1.12 - 0.7 * np.clip(np.sqrt(vx ** 2 + (vy * 0.62) ** 2) - 0.25, 0, 1.4), 0.18, 1.0)[..., None]
grains = [(rng.random((H, W, 1)).astype(np.float32) - 0.5) for _ in range(6)]

# ---------------------------------------------------------------- props
def flame(C, cx, by, w, h, t, seed=0, bright=1.0):
    """layered flame tongues centered at (cx) rising from baseline by."""
    for li, (ww, hh, col) in enumerate([(w, h, E.FIRE1), (w * 0.66, h * 0.78, E.FIRE2), (w * 0.34, h * 0.5, E.FIRE_CORE)]):
        ph = t * 6 + seed + li
        pts = [(cx - ww / 2, by)]
        steps = 7
        for i in range(steps + 1):
            fx = cx - ww / 2 + ww * i / steps
            wob = math.sin(ph + i * 1.3) * (8 + 6 * li)
            tip = by - hh * (0.5 + 0.5 * math.sin(i * 1.0 + ph * 0.7)) - hh * 0.3
            pts.append((fx + wob, tip if i % 1 == 0 else by))
        pts.append((cx + ww / 2, by))
        C.poly(pts, col)

def scene_columns(C, camx, t, e):
    # floor line
    C.rrect(-50 + camx * 0.2, 1500, W + 50 + camx * 0.2, 1560, 0, (30, 12, 16), outline=None)
    for bx in range(-1, 4):
        x = bx * 360 - (camx % 360) + 120
        C.rrect(x - 46, 360, x + 46, 1510, 14, (40, 20, 26), outline=(20, 10, 14), ow=4)
        C.rrect(x - 62, 330, x + 62, 380, 10, (52, 26, 32))
        C.rrect(x - 62, 1490, x + 62, 1540, 10, (52, 26, 32))

# ---------------------------------------------------------------- scenes
def s_fall(C, tl, gf):
    t = gf / FPS; e = energy_s[gf]
    # rushing clouds (downward)
    for i in range(9):
        cy = (i * 240 + (t * 520) % 240 * 0 + (t * 520)) % (H + 300) - 150
        cy = (i * 230 + (t * 560)) % (H + 300) - 150
        cx = (i * 173) % W
        col = clerp((150, 30, 22), (90, 18, 18), (i % 3) / 2)
        C.ellipse(cx, cy, 150, 46, col)
        C.ellipse(cx + 90, cy + 10, 110, 40, col)
    # speed lines
    for i in range(26):
        lx = (i * 47 + 13) % W
        ly = (i * 311 + t * 1700) % (H + 200) - 100
        C.capsule((lx, ly), (lx, ly + 120), 4, (255, 180, 90), outline=None)
    # glowing hell crack growing at bottom near end
    grow = key(tl, [(4.0, 0), (7.0, 1)])
    if grow > 0:
        r = 120 + grow * 520
        C.ellipse(W / 2, H + 120, r, r * 0.5, E.FIRE1)
        C.ellipse(W / 2, H + 140, r * 0.7, r * 0.34, E.FIRE2)
    # Charlie falling: grows, tumbling, flailing
    sc = key(tl, [(0, 0.7), (6.5, 1.5)])
    cy = key(tl, [(0, 420), (5.0, 980), (7.0, 1180)])
    rotv = math.sin(t * 2.2) * 0.5 + 0.2
    flail = math.sin(t * 9)
    draw_person(C, dict(x=W / 2 + math.sin(t * 1.5) * 60, y=cy, s=sc, rot=rotv,
                        eye=1.0, brow=1.0, mouth=0.7, look=0.0,
                        arm_l=(2.0 + flail * 0.5, 1.4 + flail * 0.6),
                        arm_r=(1.0 - flail * 0.5, 0.6 - flail * 0.6),
                        leg_l=0.5 + flail * 0.3, leg_r=-0.5 + flail * 0.3))

def s_arrival(C, tl, gf):
    t = gf / FPS; e = energy_s[gf]
    scene_columns(C, 0, t, e)
    # banner
    C.rrect(W / 2 - 300, 250, W / 2 + 300, 360, 12, (52, 14, 16), outline=(24, 8, 10), ow=4)
    # desk with clerk on right
    draw_clerk(C, 800, 1240, tl, gf, point=0.0)
    C.rrect(560, 1180, 1010, 1320, 12, (60, 34, 24), outline=(26, 12, 12), ow=4)
    C.rrect(560, 1180, 1010, 1212, 6, (84, 50, 34))
    # Charlie drops from top, lands ~1.0s, gets up confused
    land = 1.0
    if tl < land:
        cy = key(tl, [(0, -200), (land, 1180)])
        draw_person(C, dict(x=360, y=cy, s=1.45, rot=0.3, eye=1.0, brow=1.0, mouth=0.6,
                            arm_l=(2.2, 1.6), arm_r=(0.9, 0.5), leg_l=0.4, leg_r=-0.4))
    else:
        squash = key(tl, [(land, 1.0), (land + 0.18, 0.0)])
        look = math.sin((tl - land) * 2.2)
        draw_person(C, dict(x=360, y=1180 + squash * 30, s=1.45,
                            eye=1.0, brow=1.0, mouth=0.2 + 0.1 * abs(look), look=look,
                            arm_l=(2.5, 2.2), arm_r=(0.7, 1.1), leg_l=0.22, leg_r=-0.22))
        if tl < land + 0.4:
            for k in range(8):
                a = k / 8 * 6.28
                pr = (tl - land) / 0.4
                C.circle(360 + math.cos(a) * 120 * pr, 1300 - 10 * pr, 14 * (1 - pr) + 4, (120, 70, 50), ow=0)

def draw_clerk(C, x, y, tl, gf, point=0.0, head_shake=0.0):
    t = gf / FPS
    arm_r = (0.6, 1.9)
    if point > 0:   # point to the right (toward door, screen-left since clerk faces left)
        arm_r = (lerp(0.6, 3.4, point), lerp(1.9, 3.3, point))
    draw_person(C, dict(x=x, y=y, s=1.55, facing=-1, demon=True, suit=True, t=t,
                        skin=DRED, skin_sh=DRED_SH, body=SUIT, body_sh=(40, 30, 46),
                        eye=0.55, brow=-0.7, mouth=0.05, look=-0.4 + head_shake,
                        rot=head_shake * 0.04,
                        arm_l=(2.5, 1.3), arm_r=arm_r, leg_l=0.15, leg_r=-0.15))

def s_plea(C, tl, gf):
    t = gf / FPS; e = energy_s[gf]
    scene_columns(C, 60, t, e)
    C.rrect(560, 1180, 1010, 1320, 12, (60, 34, 24), outline=(26, 12, 12), ow=4)
    C.rrect(560, 1180, 1010, 1212, 6, (84, 50, 34))
    # clerk shakes head; points near the end
    shake = math.sin(t * 4.0) if tl < 7.5 else 0.0
    point = key(tl, [(7.6, 0), (8.6, 1)])
    draw_clerk(C, 800, 1240, tl, gf, point=point, head_shake=shake * 0.6)
    # Charlie pleads: mouth synced, arms imploring, leaning forward, beat bob
    mo = 0.2 + 0.8 * mid_s[gf]
    raise_amt = 0.4 + 0.5 * beatpulse[gf]
    lean = math.sin(t * 1.6) * 0.04
    draw_person(C, dict(x=330, y=1230 - beatpulse[gf] * 14, s=1.55, rot=lean,
                        eye=1.0, brow=1.0, mouth=mo, mouth_shape='o', look=0.5,
                        arm_l=(2.3 - raise_amt, 1.7 - raise_amt * 0.6),
                        arm_r=(0.9 + raise_amt * 0.2, 0.4 - raise_amt * 0.5),
                        leg_l=0.2, leg_r=-0.2))

def draw_guard(C, x, y, s, tl, gf, facing, grab_dir):
    t = gf / FPS
    # arm reaching toward Charlie (grab)
    al = (2.4, 2.0); ar = (0.7, 0.9)
    if facing == 1:   # guard on left, grabs to the right
        ar = (0.5, 0.2)
    else:             # guard on right, grabs to the left
        al = (2.7, 2.9)
    draw_person(C, dict(x=x, y=y, s=s, facing=facing, demon=True, bare=True, t=t,
                        skin=DRED, skin_sh=DRED_SH, body=DRED, body_sh=DRED_SH,
                        collar=False, eye=0.8, brow=-1.0, mouth=0.5, look=0.3 * facing,
                        arm_l=al, arm_r=ar, leg_l=0.3, leg_r=-0.3, hair=None))

def s_drag(C, tl, gf):
    t = gf / FPS; e = energy_s[gf]
    camx = key(tl, [(0, 0), (9, 700)])
    scene_columns(C, camx, t, e)
    # fiery door appears from the right as they approach
    dx = key(tl, [(0, W + 400), (8.5, 760)])
    draw_door(C, dx, 980, 1.0, t, fire=0.8)
    # Charlie dragged, leaning back, heels out, yelling
    cxp = key(tl, [(0, 360), (8.5, 560)])
    drag = math.sin(t * 6) * 0.06
    draw_person(C, dict(x=cxp, y=1230, s=1.5, rot=-0.18 + drag,
                        eye=1.0, brow=1.0, mouth=0.6, look=-0.6,
                        arm_l=(3.4, 3.2), arm_r=(3.0, 3.4),
                        leg_l=0.9, leg_r=0.6))
    draw_guard(C, cxp - 150, 1210, 1.7, tl, gf, facing=1, grab_dir=1)
    draw_guard(C, cxp + 160, 1210, 1.72, tl, gf, facing=-1, grab_dir=-1)

def draw_door(C, x, y, s, t, fire=1.0):
    # stone arch
    C.rrect(x - 200 * s, y - 520 * s, x + 200 * s, y + 540 * s, 8, (44, 24, 26), outline=(22, 10, 12), ow=5)
    # inner opening (fire)
    C.rrect(x - 150 * s, y - 470 * s, x + 150 * s, y + 540 * s, 4, (255, 150, 40), outline=None)
    C.ellipse(x, y - 470 * s, 150 * s, 150 * s, (255, 150, 40))
    if fire > 0:
        for fxk in (-90, -30, 30, 90):
            flame(C, x + fxk * s, y + 520 * s, 150 * s, (380 + 120 * math.sin(t * 5 + fxk)) * s, t, seed=fxk)

def s_shove(C, tl, gf):
    t = gf / FPS; e = energy_s[gf]
    base_fade = key(tl, [(0, 0), (4.0, 1)])
    draw_door(C, W / 2, 1000, 1.25, t, fire=1.0)
    # Charlie shoved forward into the doorway -> becomes silhouette
    cxp = key(tl, [(0, 470), (1.6, W / 2 + 10)])
    intod = key(tl, [(0.6, 0), (1.8, 1)])
    sil = clerp((30, 12, 12), (12, 4, 6), intod)
    if tl < 2.2:
        draw_person(C, dict(x=cxp, y=1230 - intod * 40, s=lerp(1.5, 1.3, intod), rot=0.2 + intod * 0.3,
                            eye=1.0, brow=1.0, mouth=0.7, look=0.0,
                            skin=clerp(SKIN, sil, intod), skin_sh=clerp(SKIN_SH, sil, intod),
                            body=clerp(E.SHIRT, sil, intod), body_sh=clerp(E.SHIRT_SH, sil, intod),
                            hair=clerp(E.HAIR, sil, intod), legcol=clerp(E.PANTS, sil, intod),
                            arm_l=(3.6, 3.6), arm_r=(3.2, 3.6), leg_l=0.7, leg_r=0.3))
        # guards shoving from behind
        draw_guard(C, 300, 1220, 1.7, tl, gf, facing=1, grab_dir=1)

# ---------------------------------------------------------------- timeline
SCENES = [(0.0, 7.0, s_fall), (7.0, 13.5, s_arrival), (13.5, 24.0, s_plea),
          (24.0, 33.0, s_drag), (33.0, 40.0, s_shove)]
def base_for(fn):
    return {s_fall: SKY, s_arrival: HALL, s_plea: HALL, s_drag: HALL, s_shove: DOORG}[fn]

SUBS = [  # (start, end, lines, size, color)
    (13.7, 16.6, ["PERDÃO,", "SENHOR..."], 150, (255, 238, 220)),
    (16.9, 20.0, ["DEVE TER UM", "ENGANO AQUI"], 120, (255, 238, 220)),
    (20.2, 23.6, ["EU NÃO", "PERTENÇO AQUI!"], 120, (255, 214, 120)),
    (25.0, 28.0, ["NÃO! ESPERA—"], 120, (255, 238, 220)),
    (28.4, 32.5, ["ME SOLTA!"], 140, (255, 214, 120)),
]

def render_frame(gf):
    t = gf / FPS
    for (a, b, fn) in SCENES:
        if a <= t < b or (fn is s_shove and t >= b - 0.001):
            scene = fn; tl = t - a; break
    C = Canvas(Image.fromarray(base_for(scene).copy(), 'RGB'))
    scene(C, tl, gf)
    rgb = np.asarray(C.finish()).astype(np.float32)
    # post: embers
    dense = 1.0 if scene in (s_drag, s_shove) else 0.7
    add_embers(rgb, t, energy_s[gf], dense)
    # scene transition flash (white) at each cut + audio strong flashes
    for (a, b, fn) in SCENES:
        if 0 <= t - a < 0.12:
            rgb += 255 * (1 - (t - a) / 0.12) * 0.5
    rgb += 255 * flash[gf] * 0.4
    rgb *= vig
    rgb += grains[gf % len(grains)] * 14
    out = np.clip(rgb, 0, 255).astype(np.uint8)
    img = Image.fromarray(out).convert('RGBA')
    # subtitles
    for (sa, sb, lines, size, col) in SUBS:
        if sa <= t < sb:
            lo = t - sa; al = min(1.0, lo / 0.15, (sb - t) / 0.2)
            pop = 1.0 + 0.22 * math.exp(-lo / 3.5) + 0.04 * beatpulse[gf]
            draw_text(img, lines, int(H * 0.30), size, fill=col,
                      alpha=int(255 * al), scale=pop)
    # reception banner label (bureaucratic hell)
    if 7.2 <= t < 13.3:
        al = min(1.0, (t - 7.2) / 0.4, (13.3 - t) / 0.4)
        draw_text(img, ["RECEPÇÃO"], 306, 56, fill=(232, 182, 120),
                  alpha=int(235 * al), scale=1.0, glow=None)
    # opening + closing title cards
    if t < 4.2:
        al = min(1.0, t / 0.3, (4.2 - t) / 0.5)
        draw_text(img, ["CHARLIE'S", "INFERNO"], int(H * 0.16), 130,
                  fill=(255, 230, 210), alpha=int(255 * al), scale=1.0)
    if t >= 35.5:
        al = min(1.0, (t - 35.5) / 0.6)
        draw_text(img, ["CHARLIE'S", "INFERNO"], int(H * 0.40), 150,
                  fill=(255, 210, 110), alpha=int(255 * al), scale=1.0)
        draw_text(img, ["COVER PT-BR  •  FAZ DUBZ"], int(H * 0.55), 50,
                  fill=(255, 238, 220), alpha=int(255 * al), scale=1.0, glow=None)
        draw_text(img, ["( excuse me sir )"], int(H * 0.60), 40,
                  fill=(230, 170, 120), alpha=int(255 * al), scale=1.0, glow=None)
    out = np.asarray(img.convert('RGB'))
    # global beat zoom + chromatic aberration
    z = 1.0 + 0.04 * beatpulse[gf] + 0.015 * energy_s[gf]
    if z > 1.001:
        im = Image.fromarray(out)
        nw, nh = int(W * z), int(H * z)
        im = im.resize((nw, nh), Image.BILINEAR).crop(((nw - W) // 2, (nh - H) // 2, (nw - W) // 2 + W, (nh - H) // 2 + H))
        out = np.asarray(im)
    ab = int(6 * punch[gf])
    if ab > 0:
        out = out.copy()
        out[..., 0] = np.roll(out[..., 0], ab, axis=1)
        out[..., 2] = np.roll(out[..., 2], -ab, axis=1)
    return out

# ---------------------------------------------------------------- main
if TEST:
    times = [2.0, 8.5, 15.0, 21.0, 27.0, 31.0, 34.5, 38.0]
    sheet = []
    for tt in times:
        f = render_frame(int(tt * FPS))
        Image.fromarray(f).resize((W // 2, H // 2)).save(f'scratch/an_{tt}.jpg', quality=86)
    print("test frames done", times)
else:
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [FFMPEG, '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-ss', '5.0', '-t', '40.0',
           '-i', "Charlie_s Inferno (Excuse Me Sir) - That Handsome Devil _ COVER PT-BR(MP3_160K)_1.mp3",
           '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
           '-pix_fmt', 'yuv420p', '-maxrate', '12M', '-bufsize', '24M',
           '-c:a', 'aac', '-b:a', '192k',
           '-af', 'afade=t=in:st=0:d=0.2,afade=t=out:st=39.2:d=0.8',
           '-movflags', '+faststart', '-shortest', 'out/charlie_inferno_anim.mp4']
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(N):
        proc.stdin.write(render_frame(i).tobytes())
        if i % 60 == 0: print(f"frame {i}/{N} ({100*i//N}%)", flush=True)
    proc.stdin.close(); proc.wait(); print("DONE")
