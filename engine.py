"""Vector drawing toolkit + characters for the Charlie's Inferno animation.
All layout coordinates are in final 1080x1920 space; the Canvas supersamples
internally by S for anti-aliasing.
"""
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

W, H = 1080, 1920
S = 2  # supersample factor

# ---------------------------------------------------------------- palette
OUTLINE = (24, 12, 16)
SKIN = (242, 201, 160); SKIN_SH = (214, 168, 128)
HAIR = (74, 52, 36)
SHIRT = (228, 230, 238); SHIRT_SH = (193, 198, 212)
PANTS = (58, 62, 92)
DRED = (176, 48, 40); DRED_SH = (132, 32, 28)   # demon skin
HORN = (224, 210, 178); HORN_SH = (188, 172, 140)
SUIT = (22, 18, 28); TIE = (122, 22, 30)
FIRE1 = (255, 122, 24); FIRE2 = (255, 206, 58); FIRE_CORE = (255, 244, 190)

def lerp(a, b, t): return a + (b - a) * t
def clerp(c1, c2, t): return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))
def smooth(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def key(t, pts):
    """pts: [(time,val),...] sorted; smoothstep interpolation."""
    if t <= pts[0][0]: return pts[0][1]
    if t >= pts[-1][0]: return pts[-1][1]
    for i in range(len(pts) - 1):
        t0, v0 = pts[i]; t1, v1 = pts[i + 1]
        if t0 <= t <= t1:
            return lerp(v0, v1, smooth((t - t0) / (t1 - t0)))
    return pts[-1][1]
def rot(px, py, cx, cy, ang):
    s, c = math.sin(ang), math.cos(ang)
    dx, dy = px - cx, py - cy
    return (cx + dx * c - dy * s, cy + dx * s + dy * c)

class Canvas:
    def __init__(self, base_rgb=None):
        if base_rgb is None:
            self.img = Image.new('RGBA', (W * S, H * S), (0, 0, 0, 255))
        else:
            self.img = base_rgb.convert('RGBA')
        self.d = ImageDraw.Draw(self.img, 'RGBA')
    def _p(self, pts): return [(x * S, y * S) for (x, y) in pts]
    def line(self, p1, p2, w, fill):
        self.d.line(self._p([p1, p2]), fill=fill, width=int(w * S), joint='curve')
    def capsule(self, p1, p2, w, fill, outline=OUTLINE, ow=3.5):
        if outline is not None and ow > 0:
            self._cap(p1, p2, w + 2 * ow, outline)
        self._cap(p1, p2, w, fill)
    def _cap(self, p1, p2, w, fill):
        self.d.line(self._p([p1, p2]), fill=fill, width=int(w * S))
        r = w * S / 2
        for (x, y) in (p1, p2):
            self.d.ellipse([x * S - r, y * S - r, x * S + r, y * S + r], fill=fill)
    def circle(self, cx, cy, r, fill, outline=OUTLINE, ow=3.5):
        if outline is not None and ow > 0:
            R = (r + ow) * S
            self.d.ellipse([cx * S - R, cy * S - R, cx * S + R, cy * S + R], fill=outline)
        R = r * S
        self.d.ellipse([cx * S - R, cy * S - R, cx * S + R, cy * S + R], fill=fill)
    def ellipse(self, cx, cy, rx, ry, fill, outline=None, ow=3.0, ang=0.0):
        if ang == 0.0 and outline is None:
            self.d.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], fill=fill)
            return
        n = 28
        pts = []
        for i in range(n):
            a = 2 * math.pi * i / n
            px = cx + math.cos(a) * rx; py = cy + math.sin(a) * ry
            pts.append(rot(px, py, cx, cy, ang))
        if outline is not None and ow > 0:
            self.poly(pts, outline)  # cheap outline by slight overdraw
        self.poly(pts, fill)
    def poly(self, pts, fill, outline=None, ow=3.0):
        if outline is not None and ow > 0:
            self.d.line(self._p(pts + [pts[0]]), fill=outline, width=int(ow * 2 * S), joint='curve')
        self.d.polygon(self._p(pts), fill=fill)
    def rrect(self, x0, y0, x1, y1, r, fill, outline=OUTLINE, ow=3.0):
        if outline is not None and ow > 0:
            self.d.rounded_rectangle([(x0 - ow) * S, (y0 - ow) * S, (x1 + ow) * S, (y1 + ow) * S],
                                     radius=(r + ow) * S, fill=outline)
        self.d.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], radius=r * S, fill=fill)
    def finish(self):
        return self.img.resize((W, H), Image.LANCZOS).convert('RGB')

# ---------------------------------------------------------------- character
def draw_person(C, P):
    """Draw a humanoid. P is a dict of parameters (final-space)."""
    x = P['x']; y = P['y']; s = P.get('s', 1.0)          # y = pelvis/anchor
    skin = P.get('skin', SKIN); skin_sh = P.get('skin_sh', SKIN_SH)
    body = P.get('body', SHIRT); body_sh = P.get('body_sh', SHIRT_SH)
    demon = P.get('demon', False)
    suit = P.get('suit', False)
    facing = P.get('facing', 1)   # 1 right, -1 left
    rotc = P.get('rot', 0.0)      # whole-body rotation about (x,y)
    def T(px, py):
        return rot(x + (px) * s * facing, y + py * s, x, y, rotc)
    # dimensions (relative to pelvis)
    torso_top = -150; head_cy = -210; head_r = 64
    sh_y = -130; hip_y = 0
    # legs
    lh = P.get('leg', (0.35, 0.0))  # (spread, lift) basic
    leg_col = P.get('legcol', PANTS)
    if P.get('legs', True):
        for side, ang in ((-1, P.get('leg_l', 0.25)), (1, P.get('leg_r', -0.15))):
            hipx = side * 26
            knee = T(hipx + math.sin(ang) * 70, hip_y + math.cos(ang) * 86)
            foot = T(hipx + math.sin(ang) * 70 + math.sin(ang * 0.6) * 8,
                     hip_y + math.cos(ang) * 86 + 92)
            hp = T(hipx, hip_y - 6)
            C.capsule(hp, knee, 30, leg_col)
            C.capsule(knee, foot, 26, leg_col)
            # shoe
            sh = T(hipx + math.sin(ang) * 70 + facing * 22, hip_y + math.cos(ang) * 86 + 96)
            C.capsule(foot, sh, 22, OUTLINE, outline=None)
    # tail (demon)
    if demon and P.get('tail', True):
        base = T(-30 * 1, hip_y - 10)
        mid = T(-90, hip_y + 30 + math.sin(P.get('t', 0) * 3) * 14)
        tip = T(-120, hip_y - 20 + math.sin(P.get('t', 0) * 3 + 1) * 18)
        C.capsule(base, mid, 16, skin); C.capsule(mid, tip, 9, skin)
        # arrow tip
        ang = math.atan2(tip[1] - mid[1], tip[0] - mid[0])
        a1 = (tip[0] + math.cos(ang + 2.5) * 22, tip[1] + math.sin(ang + 2.5) * 22)
        a2 = (tip[0] + math.cos(ang - 2.5) * 22, tip[1] + math.sin(ang - 2.5) * 22)
        C.poly([tip, a1, (tip[0] + math.cos(ang) * 26, tip[1] + math.sin(ang) * 26), a2], DRED_SH)
    # back arm
    def arm(ashoulder, a1, a2, hand_col=None):
        shp = T(ashoulder * 1, sh_y)
        elb = (shp[0] + math.cos(a1) * 64 * s, shp[1] + math.sin(a1) * 64 * s)
        hnd = (elb[0] + math.cos(a2) * 60 * s, elb[1] + math.sin(a2) * 60 * s)
        C.capsule(shp, elb, 26, body if not P.get('bare') else skin)
        C.capsule(elb, hnd, 22, skin)
        C.circle(hnd[0] / 1, hnd[1], 16 * s, skin, ow=2.5)
        return hnd
    al = P.get('arm_l', (2.4, 2.2)); ar = P.get('arm_r', (0.8, 1.0))
    hand_back = arm(-44, al[0], al[1])
    # torso
    tp = T(0, torso_top); bp = T(0, hip_y)
    C.capsule(tp, bp, 86, body)
    if suit:
        # lapels + tie
        C.poly([T(-30, torso_top + 6), T(0, torso_top + 70), T(-12, torso_top + 4)], (12, 9, 16))
        C.poly([T(30, torso_top + 6), T(0, torso_top + 70), T(12, torso_top + 4)], (12, 9, 16))
        C.capsule(T(0, torso_top + 18), T(0, torso_top + 96), 14, TIE, outline=None)
    elif P.get('collar', True):
        C.capsule(T(-22, torso_top + 6), T(0, torso_top + 40), 12, body_sh, outline=None)
        C.capsule(T(22, torso_top + 6), T(0, torso_top + 40), 12, body_sh, outline=None)
    # front arm
    hand_front = arm(44, ar[0], ar[1])
    # neck
    C.capsule(T(0, torso_top + 8), T(0, head_cy + head_r - 18), 26, skin)
    # head
    hc = T(0, head_cy)
    C.circle(hc[0], hc[1], head_r * s, skin)
    # ears
    C.circle(*T(-head_r + 6, head_cy + 6), 14 * s, skin)
    C.circle(*T(head_r - 6, head_cy + 6), 14 * s, skin)
    if demon:
        # pointy ear overlays
        C.poly([T(-head_r - 2, head_cy - 6), T(-head_r - 34, head_cy - 28), T(-head_r + 16, head_cy + 14)], skin)
        C.poly([T(head_r + 2, head_cy - 6), T(head_r + 34, head_cy - 28), T(head_r - 16, head_cy + 14)], skin)
        # horns
        for sx in (-1, 1):
            b = T(sx * 34, head_cy - head_r + 12)
            t = T(sx * 56, head_cy - head_r - 56)
            m = T(sx * 40, head_cy - head_r - 20)
            C.poly([T(sx * 18, head_cy - head_r + 16), t, T(sx * 52, head_cy - head_r + 8)], HORN, outline=OUTLINE, ow=2.5)
    else:
        # hair
        C.poly([T(-head_r - 4, head_cy - 6), T(-head_r + 4, head_cy - head_r - 20),
                T(0, head_cy - head_r - 26), T(head_r + 4, head_cy - head_r - 16),
                T(head_r + 6, head_cy - 2), T(head_r - 10, head_cy - head_r + 8),
                T(20, head_cy - head_r - 2), T(-8, head_cy - head_r + 6),
                T(-head_r + 8, head_cy - head_r + 2)], P.get('hair', HAIR), outline=OUTLINE, ow=2.5)
    # face
    eye = P.get('eye', 1.0)        # openness
    brow = P.get('brow', 0.0)      # +up(worried) -down(angry)
    mouth = P.get('mouth', 0.2)    # openness 0..1
    msh = P.get('mouth_shape', 'o')
    look = P.get('look', 0.0)
    ex = 26; ey = -6
    for sx in (-1, 1):
        e = T(sx * ex, head_cy + ey)
        C.ellipse(e[0] / 1, e[1], 15 * s, (8 + 16 * eye) * s, (255, 255, 255), outline=OUTLINE, ow=2.0)
        if eye > 0.25:
            pcx, pcy = T(sx * ex + look * 8, head_cy + ey + 3)
            C.circle(pcx, pcy, 7 * s, (20, 14, 18), ow=0)
        # brow: +brow = worried (inner up), -brow = angry (inner down)
        bx_out = T(sx * (ex + 16), head_cy + ey - 20 + brow * 5)
        bx_in = T(sx * (ex - 10), head_cy + ey - 16 - brow * 15)
        C.capsule(bx_out, bx_in, 8, P.get('browcol', (60, 40, 30)) if not demon else (92, 22, 22), outline=None)
    # nose
    n0 = T(0, head_cy + 6); n1 = T(facing * -8, head_cy + 20)
    C.capsule(n0, n1, 6, skin_sh, outline=None)
    # mouth
    mc = T(0, head_cy + 38)
    mo = mouth
    if mo < 0.12:
        C.capsule(T(-16, head_cy + 38), T(16, head_cy + 38), 6, (120, 50, 50), outline=None)
    else:
        C.ellipse(mc[0] / 1, mc[1], 18 * s, (8 + 26 * mo) * s, (96, 30, 36), outline=OUTLINE, ow=2.0)
        if mo > 0.4:
            C.ellipse(mc[0] / 1, mc[1] + 6 * mo, 12 * s, (10 * mo) * s, (200, 90, 96), outline=None)
    return {'hand_front': hand_front, 'hand_back': hand_back, 'head': hc}

# ---------------------------------------------------------------- text
_FONTS = {}
def font(path, size):
    k = (path, size)
    if k not in _FONTS: _FONTS[k] = ImageFont.truetype(path, size)
    return _FONTS[k]
ANTON = 'scratch/Anton.ttf'

def draw_text(img, lines, cy, size, fill=(255,238,220), stroke=(60,8,6), sw=None,
              font_path=ANTON, ls=0, alpha=255, scale=1.0, glow=(255,90,20), ga=160):
    if sw is None: sw = max(5, size // 12)
    fnt = font(font_path, max(6, int(size * scale)))
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    lh = int(size * scale * 1.05)
    total = lh * len(lines)
    y = cy - total // 2
    for ln in lines:
        bb = d.textbbox((0, 0), ln, font=fnt, stroke_width=sw)
        w = bb[2] - bb[0]
        x = (img.width - w) // 2 - bb[0]
        d.text((x, y), ln, font=fnt, fill=fill + (alpha,), stroke_width=sw, stroke_fill=stroke + (alpha,))
        y += lh
    if glow:
        a = np.asarray(layer)[..., 3]
        g = Image.fromarray(a).filter(ImageFilter.GaussianBlur(12))
        ga_arr = (np.asarray(g).astype(np.float32) / 255.0 * ga * (alpha / 255.0)).astype(np.uint8)
        gl = Image.new('RGBA', img.size, glow + (0,))
        gl.putalpha(Image.fromarray(ga_arr))
        img.alpha_composite(gl)
    img.alpha_composite(layer)
