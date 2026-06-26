#!/usr/bin/env python3
"""Charlie's Inferno (Excuse Me Sir) - YouTube Shorts edit renderer.
Audio-reactive vertical (1080x1920) video. Frames piped to ffmpeg via stdin.
"""
import sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

W, H = 1080, 1920
FPS = 30
TEST = len(sys.argv) > 1 and sys.argv[1] == "test"

# ---------------------------------------------------------------- load features
F = np.load('scratch/feat.npz')
energy = F['energy']; bass = F['bass']; flux = F['flux']; mid = F['mid']
N = int(F['nframes'])
onsets = np.load('scratch/onsets.npy')
beatlag = int(np.load('scratch/beatlag.npy')[0])

# smooth helpers
def smooth(a, k=5):
    ker = np.ones(k)/k
    return np.convolve(a, ker, mode='same')
energy_s = smooth(energy, 5)
bass_s = smooth(bass, 4)

# punch envelope (decaying) triggered by onsets, weighted by flux
punch = np.zeros(N)
tau = 5.0
for p in onsets:
    amp = 0.5 + 0.5*flux[p]
    idx = np.arange(p, min(N, p+25))
    punch[idx] = np.maximum(punch[idx], amp*np.exp(-(idx-p)/tau))
# strong flash from top-tier onsets
strong = [p for p in onsets if flux[p] > np.quantile(flux[onsets], 0.65)]
flash = np.zeros(N)
for p in strong:
    idx = np.arange(p, min(N, p+8))
    flash[idx] = np.maximum(flash[idx], (0.6+0.5*flux[p])*np.exp(-(idx-p)/2.0))

# beat grid aligned to onsets phase
phase_votes = np.bincount(onsets % beatlag, minlength=beatlag)
offset = int(np.argmax(phase_votes))
beat_frames = [i for i in range(N) if (i-offset) % beatlag == 0]
beatpulse = np.zeros(N)
for bf in beat_frames:
    idx = np.arange(bf, min(N, bf+beatlag))
    beatpulse[idx] = np.maximum(beatpulse[idx], np.exp(-(idx-bf)/4.0))

# ---------------------------------------------------------------- background
yy = np.linspace(0, 1, H)[:, None]
top = np.array([6, 3, 8]); midc = np.array([70, 12, 10]); bot = np.array([165, 45, 12])
grad = np.where(yy < 0.55,
                top + (midc-top)*(yy/0.55),
                midc + (bot-midc)*((yy-0.55)/0.45))
bg_base = np.repeat(grad[:, None, :], W, axis=1).astype(np.float32)  # H,W,3
# subtle large-scale warm noise blobs baked in
rng = np.random.default_rng(7)
noise = rng.random((H//8, W//8)).astype(np.float32)
noise = np.asarray(Image.fromarray((noise*255).astype(np.uint8)).resize((W, H)).filter(ImageFilter.GaussianBlur(20)))/255.0
bg_base += (noise[..., None]-0.5) * np.array([26, 8, 4])
bg_base = np.clip(bg_base, 0, 255)

# bottom fire glow layer (additive)
gx = np.linspace(-1, 1, W)[None, :]
gy = np.linspace(0, 1, H)[:, None]
glow = np.clip(gy**2.4, 0, 1) * np.clip(1-0.5*gx**2, 0, 1)
glow_rgb = glow[..., None] * np.array([255, 110, 25], dtype=np.float32)

# vignette
vx = np.linspace(-1, 1, W)[None, :]; vy = np.linspace(-1, 1, H)[:, None]
rad = np.sqrt(vx**2 + (vy*0.62)**2)
vignette = np.clip(1.15 - 0.75*np.clip(rad-0.2, 0, 1.4), 0.15, 1.0).astype(np.float32)[..., None]

# ---------------------------------------------------------------- character
char = Image.open('scratch/char_rgba.png').convert('RGBA')
cw = int(W*0.92)
ch = int(char.height * cw / char.width)
char = char.resize((cw, ch), Image.LANCZOS)
ca = np.asarray(char)[..., 3].astype(np.float32)/255.0
crgb = np.asarray(char)[..., :3].astype(np.float32)
# warm grade the character toward infernal lighting
warm = crgb.copy()
warm[..., 0] = np.clip(crgb[..., 0]*1.12 + 18, 0, 255)
warm[..., 1] = np.clip(crgb[..., 1]*0.98 + 4, 0, 255)
warm[..., 2] = np.clip(crgb[..., 2]*0.82, 0, 255)
crgb = warm
# rim glow: blurred dilated alpha, orange
glowmask = Image.fromarray((ca*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(14))
glowmask = np.asarray(glowmask).astype(np.float32)/255.0
char_x = (W - cw)//2
char_y = int(H*0.30)

# flame sprite for the burning book (procedural, animated by scroll)
fh, fw = 520, 620
fnoise = rng.random((fh*2, fw)).astype(np.float32)
fnoise = np.asarray(Image.fromarray((fnoise*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(7)))/255.0
fy = np.linspace(1, 0, fh)[:, None]          # hot at bottom
fx = np.linspace(-1, 1, fw)[None, :]
flame_shape = np.clip(fy**1.3, 0, 1) * np.clip(1-0.85*fx**2, 0, 1)

# ---------------------------------------------------------------- ember system
NE = 170
ex = rng.random(NE)*W
ephase = rng.random(NE)*1000
espeed = (0.18 + rng.random(NE)*0.5)        # fraction of H per second
esize = (rng.random(NE)*1.6 + 0.5)
ebright = (0.3 + rng.random(NE)*0.7)
ewob = rng.random(NE)*40 + 8
ewobf = rng.random(NE)*1.5 + 0.4
# ember sprite (gaussian)
S = 31
sx = np.linspace(-2, 2, S)
spr = np.exp(-(sx[None, :]**2 + sx[:, None]**2))
spr = (spr[..., None] * np.array([255, 140, 40], dtype=np.float32))

def stamp_add(frame, sprite, cx, cy, amp):
    s = sprite.shape[0]; h2 = s//2
    x0 = int(cx)-h2; y0 = int(cy)-h2
    x1 = x0+s; y1 = y0+s
    fx0 = max(0, x0); fy0 = max(0, y0); fx1 = min(W, x1); fy1 = min(H, y1)
    if fx0 >= fx1 or fy0 >= fy1: return
    sx0 = fx0-x0; sy0 = fy0-y0
    frame[fy0:fy1, fx0:fx1] += sprite[sy0:sy0+(fy1-fy0), sx0:sx0+(fx1-fx0)]*amp

# big foreground embers
NF = 14
fex = rng.random(NF)*W; fephase = rng.random(NF)*1000
fespeed = 0.1+rng.random(NF)*0.25; febright = 0.4+rng.random(NF)*0.5
Sf = 71
sfx = np.linspace(-2, 2, Sf)
fspr = np.exp(-(sfx[None, :]**2+sfx[:, None]**2))
fspr = (fspr[..., None]*np.array([255, 120, 35], dtype=np.float32))

# ---------------------------------------------------------------- text
anton = lambda s: ImageFont.truetype('scratch/Anton.ttf', s)
bebas = lambda s: ImageFont.truetype('scratch/BebasNeue.ttf', s)

def make_text(lines, size, fill, stroke=(20, 2, 2), sw=None, font='anton', ls=0, glow=(255,90,20)):
    fnt = anton(size) if font == 'anton' else bebas(size)
    if sw is None: sw = max(6, size//11)
    # measure
    tmp = Image.new('RGBA', (10, 10)); d = ImageDraw.Draw(tmp)
    widths = []; heights = []
    for ln in lines:
        bb = d.textbbox((0, 0), ln, font=fnt, stroke_width=sw)
        w = bb[2]-bb[0] + ls*(len(ln)-1); widths.append(w); heights.append(bb[3]-bb[1])
    lh = int(size*1.08)
    tw = max(widths)+sw*2+60; th = lh*len(lines)+sw*2+60
    img = Image.new('RGBA', (tw, th), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    y = 30
    for ln, w in zip(lines, widths):
        x = (tw-w)//2
        if ls == 0:
            d.text((x, y), ln, font=fnt, fill=fill, stroke_width=sw, stroke_fill=stroke)
        else:
            cx = x
            for chx in ln:
                d.text((cx, y), chx, font=fnt, fill=fill, stroke_width=sw, stroke_fill=stroke)
                bb = d.textbbox((0, 0), chx, font=fnt, stroke_width=sw)
                cx += (bb[2]-bb[0])+ls
        y += lh
    # add outer glow
    a = np.asarray(img)[..., 3]
    g = Image.fromarray(a).filter(ImageFilter.GaussianBlur(14))
    ga = np.asarray(g).astype(np.float32)/255.0
    base = np.asarray(img).astype(np.float32)
    out = np.zeros_like(base)
    out[..., 0] = glow[0]; out[..., 1] = glow[1]; out[..., 2] = glow[2]
    out[..., 3] = np.clip(ga*210, 0, 255)
    res = Image.alpha_composite(Image.fromarray(out.astype(np.uint8)), img)
    return res

WHITE = (255, 240, 225, 255)
EMBER = (255, 196, 92, 255)
# (start_s, end_s, image, big?)
events = []
def ev(a, b, img, scale=1.0, yoff=0):
    events.append((int(a*FPS), int(b*FPS), img, scale, yoff))

t_title = make_text(["CHARLIE'S", "INFERNO"], 150, WHITE, stroke=(120, 8, 4), font='anton', glow=(255,70,15))
t_sub = make_text(["EXCUSE ME SIR"], 70, EMBER, stroke=(40, 4, 2), font='anton', glow=(255,120,30))
t_hook = make_text(["EXCUSE", "ME SIR"], 175, WHITE, stroke=(120, 8, 4), glow=(255,70,15))
t_l1 = make_text(["THERE MUST", "BE SOMEONE"], 110, WHITE, stroke=(80, 6, 4), glow=(255,90,20))
t_l2 = make_text(["YOU'VE CONFUSED", "ME FOR"], 95, WHITE, stroke=(80, 6, 4), glow=(255,90,20))
t_l3 = make_text(["I DON'T", "BELONG HERE"], 120, EMBER, stroke=(60, 4, 2), glow=(255,120,30))
t_l4 = make_text(["YOU'VE HEARD", "THE TUNE BEFORE"], 92, WHITE, stroke=(80, 6, 4), glow=(255,90,20))
t_end = make_text(["CHARLIE'S", "INFERNO"], 150, EMBER, stroke=(90, 6, 3), glow=(255,120,30))

# timeline (seconds) - hook-forward; text kept in upper third so the face shows
TOP = -560
ev(0.15, 2.5, t_title, yoff=-470)
ev(2.7, 4.6, t_sub, yoff=int(H*0.34))
ev(5.0, 7.4, t_hook, yoff=TOP)
ev(7.7, 9.9, t_l1, yoff=TOP)
ev(10.1, 12.2, t_l2, yoff=TOP)
ev(12.5, 15.0, t_hook, yoff=TOP)
ev(15.3, 17.6, t_l3, yoff=TOP)
ev(18.0, 20.4, t_l4, yoff=TOP)
ev(20.8, 23.4, t_hook, yoff=TOP)
ev(23.8, 26.0, t_l1, yoff=TOP)
ev(26.3, 28.6, t_l2, yoff=TOP)
ev(29.0, 31.6, t_hook, yoff=TOP)
ev(32.0, 34.2, t_l3, yoff=TOP)
ev(34.6, 37.0, t_l4, yoff=TOP)
ev(37.3, 40.0, t_end, yoff=-470)

# persistent credit (bottom)
cred = make_text(["COVER PT-BR  -  FAZ DUBZ"], 46, WHITE, stroke=(30, 3, 2), font='bebas', sw=4, glow=(255,120,30))
cred2 = make_text(["CHARLIE'S INFERNO - THAT HANDSOME DEVIL"], 34, EMBER, stroke=(20, 2, 1), font='bebas', sw=3, glow=(255,120,30))

def composite_rgba(frame, rgba_img, cx, cy, alpha_mul=1.0):
    """alpha-composite a PIL RGBA centered at (cx,cy) onto float frame."""
    arr = np.asarray(rgba_img).astype(np.float32)
    h, w = arr.shape[:2]
    x0 = int(cx-w/2); y0 = int(cy-h/2); x1 = x0+w; y1 = y0+h
    fx0 = max(0, x0); fy0 = max(0, y0); fx1 = min(W, x1); fy1 = min(H, y1)
    if fx0 >= fx1 or fy0 >= fy1: return
    sx0 = fx0-x0; sy0 = fy0-y0
    sub = arr[sy0:sy0+(fy1-fy0), sx0:sx0+(fx1-fx0)]
    a = (sub[..., 3:4]/255.0)*alpha_mul
    frame[fy0:fy1, fx0:fx1] = frame[fy0:fy1, fx0:fx1]*(1-a) + sub[..., :3]*a

# precompute grain frames
grains = [ (rng.random((H, W, 1)).astype(np.float32)-0.5) for _ in range(7) ]

# ---------------------------------------------------------------- ffmpeg pipe
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
if not TEST:
    cmd = [FFMPEG, '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
           '-r', str(FPS), '-i', '-',
           '-ss', '5.0', '-t', '40.0',
           '-i', "Charlie_s Inferno (Excuse Me Sir) - That Handsome Devil _ COVER PT-BR(MP3_160K)_1.mp3",
           '-map', '0:v', '-map', '1:a',
           '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p',
           '-c:a', 'aac', '-b:a', '192k',
           '-af', 'afade=t=in:st=0:d=0.15,afade=t=out:st=39.3:d=0.7',
           '-movflags', '+faststart', '-shortest', 'out/excuse_me_sir_short.mp4']
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

def render_frame(i):
    t = i/FPS
    e = energy_s[i]; b = bass_s[i]; pu = punch[i]; fl = flash[i]; bp = beatpulse[i]
    frame = bg_base.copy()
    # bottom fire glow pulsing with bass
    frame += glow_rgb * (0.26 + 0.66*b + 0.20*bp)
    # background embers (behind char)
    for k in range(NE):
        prog = (t*espeed[k] + ephase[k]) % 1.0
        ey = H - prog*H*1.05
        exx = ex[k] + math.sin(t*ewobf[k]+ephase[k])*ewob[k]
        flick = 0.6+0.4*math.sin(t*7+ephase[k]*3)
        amp = ebright[k]*flick*(0.5+0.7*e)*0.5
        stamp_add(frame, spr, exx, ey, amp*esize[k])
    # character glow rim (additive, behind)
    gy0 = char_y; gx0 = char_x
    gh, gw = glowmask.shape
    sub = frame[gy0:gy0+gh, gx0:gx0+gw]
    if sub.shape[:2] == glowmask.shape:
        amp = (0.25 + 0.55*e + 0.5*pu)
        sub += glowmask[..., None]*np.array([255, 95, 25])*amp
    # burning book flames (additive) under the book region
    scroll = int((t*260) % fh)
    fwin = fnoise[scroll:scroll+fh, :]
    flick = 0.55 + 0.45*math.sin(t*9)+0.3*pu
    flame = flame_shape*fwin*max(0.3, flick)
    flame_rgb = flame[..., None]*np.array([255, 120, 30], dtype=np.float32)
    bx = char_x + int(cw*0.50) - fw//2
    by = char_y + int(ch*0.92) - fh
    fy0 = max(0, by); fx0 = max(0, bx); fy1 = min(H, by+fh); fx1 = min(W, bx+fw)
    if fy0 < fy1 and fx0 < fx1:
        frame[fy0:fy1, fx0:fx1] += flame_rgb[fy0-by:fy1-by, fx0-bx:fx1-bx]*(0.9+0.6*e)
    # character (with bob + shake)
    bob = math.sin(t*2*math.pi*0.45)*7
    dx = (rng.random()-0.5)*22*pu
    dy = (rng.random()-0.5)*22*pu
    cx = char_x + int(dx); cy = char_y + int(bob+dy)
    # paste char rgb with alpha
    x0 = cx; y0 = cy; x1 = x0+cw; y1 = y0+ch
    fx0 = max(0, x0); fy0 = max(0, y0); fx1 = min(W, x1); fy1 = min(H, y1)
    if fx0 < fx1 and fy0 < fy1:
        a = ca[fy0-y0:fy1-y0, fx0-x0:fx1-x0, None]
        rgbsub = crgb[fy0-y0:fy1-y0, fx0-x0:fx1-x0]
        # infernal light boost with energy
        rgbsub = np.clip(rgbsub*(1+0.18*e) + np.array([22, 6, 0])*pu, 0, 255)
        frame[fy0:fy1, fx0:fx1] = frame[fy0:fy1, fx0:fx1]*(1-a) + rgbsub*a
    # foreground big embers (in front of char)
    for k in range(NF):
        prog = (t*fespeed[k] + fephase[k]) % 1.0
        ey = H - prog*H*1.1
        exx = fex[k] + math.sin(t*0.7+fephase[k])*60
        amp = febright[k]*(0.5+0.5*math.sin(t*5+fephase[k]))*(0.4+0.5*e)*0.35
        stamp_add(frame, fspr, exx, ey, amp)
    # text events
    for (sa, sb, img, sc, yoff) in events:
        if sa <= i < sb:
            local = i-sa; dur = sb-sa
            ain = min(1.0, local/3.0)              # quick fade in (3 frames)
            aout = min(1.0, (sb-i)/4.0)
            alpha = min(ain, aout)
            # pop scale
            pop = 1.0 + 0.28*math.exp(-local/3.5)
            pulse = 1.0 + 0.05*beatpulse[i]
            scl = sc*pop*pulse
            im2 = img if abs(scl-1.0) < 0.01 else img.resize(
                (max(1, int(img.width*scl)), max(1, int(img.height*scl))), Image.LANCZOS)
            shk = 6*punch[i]
            tcx = W/2 + (rng.random()-0.5)*shk
            tcy = H/2 + yoff + (rng.random()-0.5)*shk
            composite_rgba(frame, im2, tcx, tcy, alpha)
    # credits
    composite_rgba(frame, cred, W/2, H-150, 0.92)
    composite_rgba(frame, cred2, W/2, H-100, 0.85)
    # white strobe flash
    if fl > 0.01:
        frame += 255*fl*0.55
    # vignette
    frame *= vignette
    # grain
    frame += grains[i % len(grains)]*16
    out = np.clip(frame, 0, 255).astype(np.uint8)
    # global zoom punch (bounce) + chromatic aberration on hits
    z = 1.0 + 0.045*bp + 0.02*e
    img = Image.fromarray(out)
    if z > 1.001:
        nw, nh = int(W*z), int(H*z)
        img = img.resize((nw, nh), Image.BILINEAR)
        l = (nw-W)//2; tcrop = (nh-H)//2
        img = img.crop((l, tcrop, l+W, tcrop+H))
    out = np.asarray(img)
    ab = int(6*pu)
    if ab > 0:
        out = out.copy()
        out[..., 0] = np.roll(out[..., 0], ab, axis=1)
        out[..., 2] = np.roll(out[..., 2], -ab, axis=1)
    return out

if TEST:
    for tf in [int(1.0*FPS), int(6.0*FPS), int(8.5*FPS), int(16.0*FPS)]:
        Image.fromarray(render_frame(tf)).save(f'scratch/test_{tf}.jpg', quality=88)
        print("wrote test frame", tf)
else:
    for i in range(N):
        proc.stdin.write(render_frame(i).tobytes())
        if i % 60 == 0:
            print(f"frame {i}/{N} ({100*i//N}%)", flush=True)
    proc.stdin.close()
    proc.wait()
    print("DONE")
