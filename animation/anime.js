/* Charlie's Inferno — cinematic anime-style engine (v2).
 * Story of Charlie: a smug "good" man dies expecting heaven, an angel finds his
 * name isn't on the list, and he's sent DOWN — pleading to indifferent demons as
 * he descends into a consumerist bureaucratic hell. No lyrics on screen (©).
 * Cel-shaded, fluid 24fps, camera work, parallax, silhouettes, god-rays, grade.
 */
(function (global) {
  const W = 1280, H = 720, TAU = Math.PI * 2;
  let TL = null, FPS = 24, ctx = null, DUR = 230.25;

  // ---------- math / easing ----------
  const lerp = (a, b, t) => a + (b - a) * t;
  const clamp = (v, a = 0, b = 1) => v < a ? a : v > b ? b : v;
  const smooth = t => (t = clamp(t)) * t * (3 - 2 * t);
  const easeIn = t => t * t;
  const easeOut = t => 1 - (1 - t) * (1 - t);
  const easeInOut = t => t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
  function hash(n) { let t = (n * 2654435761) >>> 0; t ^= t >>> 15; t = Math.imul(t, 2246822519); t ^= t >>> 13; t = Math.imul(t, 3266489917); t ^= t >>> 16; return (t >>> 0) / 4294967296; }
  function lerp255(c0, c1, t) { const h = x => [parseInt(x.slice(1, 3), 16), parseInt(x.slice(3, 5), 16), parseInt(x.slice(5, 7), 16)]; const a = h(c0), b = h(c1); return `rgb(${lerp(a[0], b[0], t) | 0},${lerp(a[1], b[1], t) | 0},${lerp(a[2], b[2], t) | 0})`; }
  // keyframe interp: keys = [[t, v], ...] (t seconds), eased
  function kf(t, keys, ease = smooth) {
    if (t <= keys[0][0]) return keys[0][1];
    if (t >= keys[keys.length - 1][0]) return keys[keys.length - 1][1];
    for (let i = 0; i < keys.length - 1; i++) {
      const [t0, v0] = keys[i], [t1, v1] = keys[i + 1];
      if (t >= t0 && t <= t1) return lerp(v0, v1, ease((t - t0) / (t1 - t0)));
    }
    return keys[keys.length - 1][1];
  }
  const F = i => TL.frames[clamp(i, 0, TL.count - 1) | 0]; // frame data

  // ---------- primitives ----------
  function poly(ctx, pts, close = true) { ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]); if (close) ctx.closePath(); }
  function smoothPoly(ctx, pts, close = true) {
    ctx.beginPath();
    if (close) { const m = [(pts[0][0] + pts[pts.length - 1][0]) / 2, (pts[0][1] + pts[pts.length - 1][1]) / 2]; ctx.moveTo(m[0], m[1]); }
    else ctx.moveTo(pts[0][0], pts[0][1]);
    const n = pts.length;
    for (let i = 0; i < (close ? n : n - 1); i++) { const p = pts[i], q = pts[(i + 1) % n]; const mx = (p[0] + q[0]) / 2, my = (p[1] + q[1]) / 2; ctx.quadraticCurveTo(p[0], p[1], mx, my); }
    if (!close) ctx.lineTo(pts[n - 1][0], pts[n - 1][1]); else ctx.closePath();
  }
  function fillShape(ctx, pts, fill, line, lw = 3, sm = true) { (sm ? smoothPoly : poly)(ctx, pts); if (fill) { ctx.fillStyle = fill; ctx.fill(); } if (line) { ctx.strokeStyle = line; ctx.lineWidth = lw; ctx.lineJoin = 'round'; ctx.stroke(); } }
  // outlined limb: fat dark stroke behind + fill stroke on top (cel look)
  function limb(ctx, pts, w, fill, line, lw = 6) { ctx.lineCap = 'round'; ctx.lineJoin = 'round'; poly(ctx, pts, false); ctx.strokeStyle = line; ctx.lineWidth = w + lw; ctx.stroke(); ctx.strokeStyle = fill; ctx.lineWidth = w; ctx.stroke(); }
  function circle(ctx, x, y, r, fill, line, lw = 3) { ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); if (fill) { ctx.fillStyle = fill; ctx.fill(); } if (line) { ctx.strokeStyle = line; ctx.lineWidth = lw; ctx.stroke(); } }
  function ellipse(ctx, x, y, rx, ry, rot, fill, line, lw = 3) { ctx.beginPath(); ctx.ellipse(x, y, rx, ry, rot, 0, TAU); if (fill) { ctx.fillStyle = fill; ctx.fill(); } if (line) { ctx.strokeStyle = line; ctx.lineWidth = lw; ctx.stroke(); } }

  // ---------- FX ----------
  function godRays(ctx, x, y, len, count, col, alpha, rot = 0, spread = TAU) {
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.translate(x, y); ctx.rotate(rot);
    for (let i = 0; i < count; i++) {
      const a = spread * (i / count - 0.5) + Math.sin(i * 12.9) * 0.02;
      const wdt = 0.01 + hash(i * 3) * 0.04;
      const g = ctx.createLinearGradient(0, 0, Math.cos(a) * len, Math.sin(a) * len);
      g.addColorStop(0, `rgba(${col},${alpha})`); g.addColorStop(1, `rgba(${col},0)`);
      ctx.beginPath(); ctx.moveTo(0, 0);
      ctx.lineTo(Math.cos(a - wdt) * len, Math.sin(a - wdt) * len);
      ctx.lineTo(Math.cos(a + wdt) * len, Math.sin(a + wdt) * len);
      ctx.closePath(); ctx.fillStyle = g; ctx.fill();
    }
    ctx.restore();
  }
  function speedLines(ctx, cx, cy, amt, col, alpha) {
    if (amt <= 0.01) return;
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.strokeStyle = `rgba(${col},${alpha})`; ctx.lineCap = 'round';
    const n = 60;
    for (let i = 0; i < n; i++) {
      const a = (i / n) * TAU + hash(i) * 0.1; const r0 = 260 + hash(i * 7) * 260 * (1 - amt);
      const r1 = r0 + 60 + 260 * amt * (0.5 + hash(i * 3));
      ctx.lineWidth = 1 + 3 * hash(i * 5);
      ctx.beginPath(); ctx.moveTo(cx + Math.cos(a) * r0, cy + Math.sin(a) * r0); ctx.lineTo(cx + Math.cos(a) * r1, cy + Math.sin(a) * r1); ctx.stroke();
    }
    ctx.restore();
  }
  function letterbox(ctx, amt) { const bar = 70 * amt; ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, bar); ctx.fillRect(0, H - bar, W, bar); }
  function vignette(ctx, amt) { const g = ctx.createRadialGradient(W / 2, H / 2, H * 0.32, W / 2, H / 2, H * 0.9); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, `rgba(0,0,0,${amt})`); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); }
  function grade(ctx, r, g, b, a, mode = 'overlay') { ctx.save(); ctx.globalCompositeOperation = mode; ctx.globalAlpha = a; ctx.fillStyle = `rgb(${r},${g},${b})`; ctx.fillRect(0, 0, W, H); ctx.restore(); }
  function flash(ctx, a, col = '255,255,255') { if (a <= 0.01) return; ctx.fillStyle = `rgba(${col},${a})`; ctx.fillRect(0, 0, W, H); }

  // ---------- particle pools ----------
  let pools = {};
  function pool(name) { return pools[name] || (pools[name] = []); }
  function stepRain(f, dir = 1) {
    const p = pool('rain'); const spawn = 8;
    for (let k = 0; k < spawn; k++) p.push({ x: hash(p.length * 3 + performance_now()) * (W + 200) - 100, y: -20, v: 22 + hash(k) * 10, len: 18 + hash(k * 2) * 22 });
    for (const d of p) { d.y += d.v; d.x += 2; }
    pools.rain = p.filter(d => d.y < H + 40).slice(-260);
  }
  let _pn = 0; function performance_now() { return (_pn++) * 0.13; }
  function drawRain(ctx, alpha) { ctx.save(); ctx.strokeStyle = `rgba(180,200,230,${alpha})`; ctx.lineWidth = 2; ctx.lineCap = 'round'; for (const d of pool('rain')) { ctx.beginPath(); ctx.moveTo(d.x, d.y); ctx.lineTo(d.x - 2, d.y - d.len); ctx.stroke(); } ctx.restore(); }
  function stepEmbers(f, intensity = 1) {
    const p = pool('emb'); const rate = (1 + 6 * f.h + 8 * f.onset) * intensity;
    let s = rate; while (s > 0) { if (s < 1 && hash(p.length * 9 + _pn) > s) break; s -= 1; p.push({ x: hash(p.length * 7 + _pn * 13) * W, y: H + 10, vx: (hash(p.length) - 0.5) * 0.8, vy: -(0.8 + hash(p.length * 3) * 2.4) - 2 * f.b, life: 0, max: 60 + hash(p.length * 5) * 90, r: 1 + hash(p.length * 2) * 2.6, seed: hash(p.length * 11) * 100 }); }
    for (const e of p) { e.life++; e.x += e.vx + Math.sin((e.life + e.seed) * 0.14) * 0.6; e.y += e.vy; e.vy *= 0.99; }
    pools.emb = p.filter(e => e.life < e.max && e.y > -20).slice(-360);
  }
  function drawEmbers(ctx) { ctx.save(); ctx.globalCompositeOperation = 'lighter'; for (const e of pool('emb')) { const k = 1 - e.life / e.max; const r = e.r * (0.6 + 0.6 * k); const g = ctx.createRadialGradient(e.x, e.y, 0, e.x, e.y, r * 4); g.addColorStop(0, `rgba(255,225,150,${0.9 * k})`); g.addColorStop(0.4, `rgba(255,130,40,${0.5 * k})`); g.addColorStop(1, 'rgba(255,80,0,0)'); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(e.x, e.y, r * 4, 0, TAU); ctx.fill(); } ctx.restore(); }

  // ---------- reusable scenery ----------
  function flameRow(ctx, baseY, scaleH, alpha, t, f) {
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    for (let k = 0; k < 26; k++) {
      const x = (hash(k * 31 + 1) * 1.06 - 0.03) * W; const w = 70 + 120 * hash(k * 7 + 2);
      const h = scaleH * (0.5 + 0.9 * hash(k * 13 + 3)) * (0.7 + 0.6 * f.b) * (0.8 + 0.4 * Math.sin(t * 6 + k));
      const tip = [x + Math.sin(t * 5 + k) * w * 0.2, baseY - h];
      const pts = [[x - w / 2, baseY], [x - w * 0.2, baseY - h * 0.5], tip, [x + w * 0.2, baseY - h * 0.5], [x + w / 2, baseY]];
      const g = ctx.createLinearGradient(0, baseY, 0, baseY - h); g.addColorStop(0, `rgba(150,20,12,${alpha})`); g.addColorStop(0.5, `rgba(255,90,30,${alpha})`); g.addColorStop(1, `rgba(255,210,90,${alpha})`);
      smoothPoly(ctx, pts); ctx.fillStyle = g; ctx.fill();
    }
    ctx.restore();
  }
  function crowd(ctx, baseY, n, col, sway, t) {
    for (let i = 0; i < n; i++) {
      const x = (i + 0.5) / n * W + Math.sin(t * 1.5 + i) * sway; const s = 0.7 + hash(i * 5) * 0.6; const bob = Math.sin(t * 2 + i * 1.7) * 6 * s;
      const hy = baseY - 120 * s + bob;
      ctx.fillStyle = col;
      // body
      smoothPoly(ctx, [[x - 26 * s, baseY], [x - 20 * s, hy + 40 * s], [x + 20 * s, hy + 40 * s], [x + 26 * s, baseY]]); ctx.fill();
      circle(ctx, x, hy, 22 * s, col, null); // head
      // raised arms occasionally
      if (hash(i * 3) > 0.5) { limb(ctx, [[x - 12 * s, hy + 34 * s], [x - 30 * s, hy - 10 * s]], 10 * s, col, col, 0); limb(ctx, [[x + 12 * s, hy + 34 * s], [x + 30 * s, hy - 6 * s]], 10 * s, col, col, 0); }
    }
  }
  // a gate/archway (used for heaven gate & hell gate)
  function gate(ctx, cx, cy, scale, pillarCol, glowCol) {
    ctx.save(); ctx.translate(cx, cy); ctx.scale(scale, scale);
    const g = ctx.createLinearGradient(0, -260, 0, 0); g.addColorStop(0, glowCol[0]); g.addColorStop(1, glowCol[1]);
    ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(-150, 40); ctx.lineTo(-150, -170); ctx.arc(0, -170, 150, Math.PI, 0); ctx.lineTo(150, 40); ctx.closePath(); ctx.fill();
    // pillars
    for (const sx of [-1, 1]) { fillShape(ctx, [[sx * 150, 40], [sx * 200, 40], [sx * 200, -180], [sx * 150, -180]], pillarCol, '#0000', 0); }
    ctx.restore();
  }

  // ---------- character dynamics: springs (secondary motion) + blink ----------
  let NOW = 0, CH = {};
  function chState(id) { return CH[id] || (CH[id] = { px: null, py: null, coat: { a: 0, v: 0 }, tie: { a: 0, v: 0 }, hair: { a: 0, v: 0 }, breath: hash(id.length * 7 + 3) }); }
  function spr(s, target, k, d) { s.v += (target - s.a) * k; s.v *= d; s.a += s.v; return s.a; }
  function blinkAt() { const ph = NOW % 3.4; return ph < 0.12 ? Math.sin(ph / 0.12 * Math.PI) : 0; }

  // ---------- per-line action / gesture system (one action per lyric line) ----------
  // arm = [shoulderAngle, elbowAngle]; angle 0=+x(right), PI/2=down, -PI/2=up, PI=left
  const NEUT = { armL: [Math.PI / 2 - 0.2, -0.3], armR: [Math.PI / 2 + 0.2, 0.3], brow: 0.15 };
  const UP = -Math.PI / 2;
  const P = {
    switch: () => ({ armR: [UP + 0.25, -0.3], head: -0.12, brow: 0.3, smile: true }),
    bike: (u) => ({ armL: [Math.PI / 2 - 1.05, -0.25], armR: [Math.PI / 2 - 0.95, 0.25], lean: 0.13, hip: 5 + 5 * Math.sin(u * 26) }),
    fish: (u) => ({ armR: [Math.PI / 2 - 1.4 + Math.sin(u * Math.PI * 2) * 0.9, 0.2], armL: [Math.PI / 2 - 0.6, -0.2], lean: 0.05 * Math.cos(u * Math.PI * 2) }),
    heart: () => ({ armR: [Math.PI / 2 - 1.35, -0.9], head: 0.05, brow: 0.4, smile: true }),
    recoil: () => ({ armL: [UP - 0.35, 0.4], armR: [UP + 0.35, -0.4], lean: -0.2, head: 0.16, brow: -0.5, mouthOpen: 0.5 }),
    rose: () => ({ armR: [0.15, 0.15], head: -0.06, brow: 0.4, smile: true }),
    shrug: (u) => ({ armL: [Math.PI - 0.55, -0.5], armR: [0.55, 0.5], head: 0.05 + 0.05 * Math.sin(u * 8), brow: 0.35 }),
    wave: (u) => ({ armR: [UP + 0.2 + Math.sin(u * 22) * 0.28, -0.2], head: 0.04, brow: 0.3, smile: true }),
    pray: () => ({ armL: [Math.PI / 2 - 1.05, -1.0], armR: [Math.PI / 2 - 1.05, 1.0], head: 0.2, brow: 0.4 }),
    pointUp: () => ({ armR: [UP + 0.05, -0.12], head: -0.22, brow: 0.4 }),
    awe: () => ({ armL: [Math.PI / 2 - 0.6, -0.3], armR: [Math.PI / 2 + 0.6, 0.3], head: -0.26, brow: 0.5 }),
    plead: (u) => ({ armL: [Math.PI / 2 - 1.0 + Math.sin(u * 11) * 0.12, -0.4], armR: [Math.PI / 2 + 1.0 - Math.sin(u * 11) * 0.12, 0.4], head: 0.1, brow: -0.7, mouthOpen: 0.6 }),
    clutch: () => ({ armL: [Math.PI / 2 - 1.25, -0.9], armR: [Math.PI / 2 - 1.25, 0.9], lean: 0.09, head: 0.16, brow: -0.85, mouthOpen: 0.7, squash: 0.16 }),
    shout: () => ({ armL: [UP - 0.4, 0.3], armR: [UP + 0.4, -0.3], head: -0.14, brow: -0.6, mouthOpen: 0.9 }),
    protest: (u) => ({ armL: [Math.PI - 0.32, -0.3], armR: [0.32, 0.3], head: 0.1 + 0.04 * Math.sin(u * 10), brow: -0.6, mouthOpen: 0.6 }),
    reveal: () => ({ armR: [0.2, 0.3], head: 0.16, brow: -0.3, mouthOpen: 0.5 }),
    look: (u) => ({ head: 0.14 * Math.sin(u * 5), brow: 0.2, look: Math.sin(u * 5), mouthOpen: 0.4 }),
  };
  // [t0, poseKey] — one per lyric line (times from the Whisper transcription)
  const ACT = [
    [19.28, 'switch'], [21.18, 'bike'], [24.62, 'fish'], [27.76, 'heart'], [31.2, 'recoil'],
    [34.5, 'rose'], [37.9, 'shrug'], [44.68, 'wave'], [47.74, 'pray'], [50.92, 'pointUp'],
    [53.82, 'awe'], [57.48, 'look'], [60.86, 'recoil'], [63.94, 'clutch'], [70.72, 'plead'],
    [76.73, 'protest'], [80.59, 'shout'], [83.95, 'plead'], [86.93, 'look'], [89.95, 'protest'],
    [93.79, 'shout'], [97.25, 'shout'], [100.51, 'reveal'], [106.8, 'reveal'], [110.06, 'protest'],
    [113.22, 'reveal'], [116.84, 'reveal'], [119.96, 'awe'], [123.12, 'look'], [126.56, 'protest'],
    [129.82, 'shout'], [132.9, 'recoil'], [136.16, 'look'], [139.66, 'recoil'], [142.76, 'plead'],
    [146.08, 'clutch'], [149.74, 'plead'], [157.5, 'shout'], [162.83, 'plead'],
  ];
  function env(u) { return smooth(clamp(u / 0.26)) * smooth(clamp((1 - u) / 0.2)); }
  function gestureAt(t, f) {
    let a = null, i;
    for (i = 0; i < ACT.length; i++) { const t0 = ACT[i][0], t1 = i + 1 < ACT.length ? ACT[i + 1][0] : t0 + 3; if (t >= t0 && t < t1) { a = ACT[i]; break; } }
    if (!a) return null;
    const t0 = a[0], t1 = i + 1 < ACT.length ? ACT[i + 1][0] : t0 + 3; const u = clamp((t - t0) / Math.max(0.5, t1 - t0));
    const raw = P[a[1]]; const tp = typeof raw === 'function' ? raw(u, f) : raw; const e = env(u);
    const o = {};
    o.armL = [lerp(NEUT.armL[0], (tp.armL || NEUT.armL)[0], e), lerp(NEUT.armL[1], (tp.armL || NEUT.armL)[1], e)];
    o.armR = [lerp(NEUT.armR[0], (tp.armR || NEUT.armR)[0], e), lerp(NEUT.armR[1], (tp.armR || NEUT.armR)[1], e)];
    o.lean = lerp(0, tp.lean || 0, e); o.hip = lerp(0, tp.hip || 0, e); o.head = lerp(0, tp.head || 0, e);
    o.brow = lerp(NEUT.brow, tp.brow != null ? tp.brow : NEUT.brow, e); o.squash = lerp(0, tp.squash || 0, e);
    o.look = (tp.look || 0) * e; o.smile = tp.smile;
    o.mouthOpen = Math.max(tp.mouthOpen || 0, clamp(0.15 + (f ? f.v : 0)) * e); // sing on the vocal band
    return o;
  }

  // ---------- Charlie (cel-shaded everyman) — rigged, idle + springs + smear ----------
  function charlie(ctx, p) {
    const id = p.id || 'main', st = chState(id);
    const s = p.s || 1, flip = p.flip ? -1 : 1;
    const SKIN = '#e8b48c', SKIN_S = '#c98d64', HAIR = '#3b2a22', COAT = '#38506b', COAT_S = '#26374d', SHIRT = '#d9dde3', PANT = '#2a2f39', LINE = '#141018';
    const silh = p.silh; const bodyF = silh ? (p.silhCol || '#0b0910') : COAT, bodyL = silh ? (p.silhCol || '#0b0910') : LINE;
    const g = p.gesture || {};
    // velocity (world px/frame) -> springs + smear
    const vx = st.px == null ? 0 : (p.x - st.px), vy = st.py == null ? 0 : (p.y - st.py); st.px = p.x; st.py = p.y;
    const lvx = vx * flip;
    // idle life (breathing, sway, weight-shift, blink)
    const idle = p.idle === false ? 0 : 1;
    const breath = idle * Math.sin(NOW * 2.2 + st.breath * 7);
    const wShift = idle * Math.sin(NOW * 0.9 + st.breath * 3) * 3;
    const headBob = idle * Math.sin(NOW * 2.2 + st.breath * 7 + 0.5) * 0.03;
    const blink = idle ? blinkAt() : 0;
    const lean = (p.lean || 0) + (g.lean || 0) + idle * Math.sin(NOW * 0.9 + st.breath * 3) * 0.02;
    // secondary-motion springs (coat hem, tie, hair lag behind motion + lean)
    const coatA = spr(st.coat, -lvx * 0.02 - lean * 0.6, 0.35, 0.75);
    const tieA = spr(st.tie, lvx * 0.03 + Math.sin(NOW * 3) * 0.04 + lean * 0.5, 0.4, 0.7);
    const hairA = spr(st.hair, -lvx * 0.03 - lean * 0.4, 0.4, 0.72);

    ctx.save(); ctx.translate(p.x, p.y); ctx.scale(flip * s, s); ctx.rotate(lean);
    ctx.scale(1 + (g.squash || 0) * 0.10, 1 - (g.squash || 0) * 0.12 + breath * 0.006);
    const hipY = 0 - (g.hip || 0), shY = -150 + breath * 1.2, headY = -210 + breath * 1.4;
    // ---- legs ----
    const lg = g.legL || p.legL || [Math.PI / 2 + 0.12, -0.15], rg = g.legR || p.legR || [Math.PI / 2 - 0.12, 0.15];
    for (const [hip, dir, key] of [[[-14 + wShift, hipY], lg, 'fL'], [[14 + wShift, hipY], rg, 'fR']]) {
      const kx = hip[0] + Math.cos(dir[0]) * 78, ky = hip[1] + Math.sin(dir[0]) * 78;
      const fx = kx + Math.cos(dir[0] + dir[1]) * 74, fy = ky + Math.sin(dir[0] + dir[1]) * 74;
      const pv = st[key]; if (pv && (Math.abs(fx - pv[0]) + Math.abs(fy - pv[1])) > 34) { ctx.save(); ctx.globalAlpha = 0.22; limb(ctx, [pv, [fx, fy]], 18, silh ? bodyF : PANT, silh ? bodyF : PANT, 0); ctx.restore(); } st[key] = [fx, fy];
      limb(ctx, [hip, [kx, ky], [fx, fy]], 22, silh ? bodyF : PANT, bodyL);
      fillShape(ctx, [[fx - 6, fy], [fx + 22, fy - 4], [fx + 24, fy + 10], [fx - 8, fy + 10]], silh ? bodyF : '#15100c', bodyL, 3);
    }
    // ---- arm helper (with smear trail) ----
    function arm(root, a, col, key) {
      const [a1, a2] = a; const ex = root[0] + Math.cos(a1) * 60, ey = root[1] + Math.sin(a1) * 60;
      const hx = ex + Math.cos(a1 + a2) * 58, hy = ey + Math.sin(a1 + a2) * 58;
      const pv = st[key]; if (pv && (Math.abs(hx - pv[0]) + Math.abs(hy - pv[1])) > 26) { ctx.save(); ctx.globalAlpha = 0.28; limb(ctx, [pv, [hx, hy]], 15, col, col, 0); ctx.restore(); } st[key] = [hx, hy];
      limb(ctx, [root, [ex, ey], [hx, hy]], 18, col, bodyL); circle(ctx, hx, hy, 10, silh ? bodyF : SKIN, bodyL, 3); return [hx, hy];
    }
    const handR = arm([26, shY + 16], g.armR || p.armR || [Math.PI / 2 + 0.2, 0.2], bodyF, 'phR');
    // ---- torso (coat hem sways via spring) ----
    const torso = [[-40, shY], [40, shY], [52 + coatA * 34, shY + 70], [30 + coatA * 46, hipY + 6], [-30 + coatA * 46, hipY + 6], [-52 + coatA * 34, shY + 70]];
    fillShape(ctx, torso, bodyF, bodyL, 4);
    if (!silh) {
      fillShape(ctx, [[-14, shY + 4], [14, shY + 4], [8, shY + 70], [-8, shY + 70]], SHIRT, null, 0);
      ctx.save(); ctx.translate(0, shY + 8); ctx.rotate(tieA); fillShape(ctx, [[-6, 0], [6, 0], [9, 66], [0, 84], [-9, 66]], '#7d2530', null, 0); ctx.restore();
      ctx.save(); smoothPoly(ctx, torso); ctx.clip(); fillShape(ctx, [[8, shY], [40, shY], [52, shY + 70], [30, hipY + 6], [12, hipY]], COAT_S, null, 0); ctx.restore();
    }
    const handL = arm([-26, shY + 16], g.armL || p.armL || [Math.PI / 2 - 0.2, -0.2], bodyF, 'phL');
    // ---- neck + head ----
    limb(ctx, [[0, shY], [0, headY + 34]], 22, silh ? bodyF : SKIN, bodyL);
    ctx.save(); ctx.translate(0, headY); ctx.rotate((p.head || 0) + (g.head || 0) + headBob + hairA * 0.14);
    circle(ctx, 0, 0, 40, silh ? bodyF : SKIN, bodyL, 3.5);
    if (!silh) {
      ctx.save(); circle(ctx, 0, 0, 40); ctx.clip(); ctx.fillStyle = SKIN_S; ctx.beginPath(); ctx.ellipse(22, 2, 30, 40, 0, 0, TAU); ctx.fill(); ctx.restore();
      ctx.fillStyle = HAIR; ctx.beginPath(); ctx.moveTo(-42, -6); ctx.quadraticCurveTo(-46 + hairA * 26, -46, 0 + hairA * 20, -46); ctx.quadraticCurveTo(46 + hairA * 26, -46, 42, -4); ctx.quadraticCurveTo(24, -26, 6, -22); ctx.quadraticCurveTo(-6, -30, -42, -14); ctx.closePath(); ctx.fill();
      const eo = (p.eye != null ? p.eye : 1) * (1 - blink); const ew = 6, eh = 5 * eo + 0.5; const lookx = (g.look != null ? g.look : (p.look || 0));
      for (const ex of [-15, 15]) { ellipse(ctx, ex, 4, ew, eh, 0, '#fff', LINE, 1.5); if (eo > 0.4) circle(ctx, ex + lookx * 3, 5, 3, LINE, null); }
      const bw = (g.brow != null ? g.brow : (p.brow || 0)); ctx.strokeStyle = LINE; ctx.lineWidth = 2.6; ctx.lineCap = 'round';
      for (const bx of [-1, 1]) { ctx.beginPath(); ctx.moveTo(bx * 8, -14 + (bw < 0 ? -bw * 4 : 0)); ctx.lineTo(bx * 22, -8 - bw * 6); ctx.stroke(); }
      const mo = clamp(Math.max(p.mouth || 0, g.mouthOpen || 0)); ctx.strokeStyle = LINE; ctx.fillStyle = '#5a2320'; ctx.lineWidth = 2.6;
      if (mo < 0.12) { ctx.beginPath(); ctx.moveTo(-10, 22); ctx.quadraticCurveTo(0, 22 + ((p.smile || g.smile) ? -5 : 3), 10, 22); ctx.stroke(); }
      else { ctx.beginPath(); ctx.ellipse(0, 24, 8, 4 + 9 * mo, 0, 0, TAU); ctx.fill(); ctx.stroke(); }
    } else if (p.rim) { ctx.strokeStyle = p.rim; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.arc(0, 0, 39, Math.PI * 0.9, Math.PI * 1.7); ctx.stroke(); }
    ctx.restore();
    ctx.restore();
    return { handL, handR };
  }

  // ---------- props & secondary characters (literal storytelling) ----------
  function rose(ctx, x, y, ang, s) {
    s = s || 1; ctx.save(); ctx.translate(x, y); ctx.rotate(ang || 0); ctx.scale(s, s);
    ctx.strokeStyle = '#2f6b2f'; ctx.lineWidth = 3.5; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(0, 2); ctx.lineTo(0, 40); ctx.stroke();
    ctx.fillStyle = '#3a7a3a'; ctx.beginPath(); ctx.ellipse(-7, 22, 8, 3.5, -0.5, 0, TAU); ctx.fill(); ctx.beginPath(); ctx.ellipse(7, 28, 8, 3.5, 0.5, 0, TAU); ctx.fill();
    ctx.fillStyle = '#9c2a20'; for (let i = 0; i < 6; i++) { const a = i / 6 * TAU; ctx.beginPath(); ctx.ellipse(Math.cos(a) * 5, -2 + Math.sin(a) * 5, 6, 4.5, a, 0, TAU); ctx.fill(); }
    ctx.fillStyle = '#c0392b'; ctx.beginPath(); ctx.arc(0, -2, 7, 0, TAU); ctx.fill();
    ctx.fillStyle = '#d94b3a'; ctx.beginPath(); ctx.arc(-1, -3, 3.5, 0, TAU); ctx.fill();
    ctx.restore();
  }
  function grave(ctx, x, y, s) {
    s = s || 1; ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
    ctx.fillStyle = 'rgba(30,26,20,0.8)'; ctx.beginPath(); ctx.ellipse(0, 4, 96, 20, 0, 0, TAU); ctx.fill();
    ctx.fillStyle = '#8a8f96'; ctx.strokeStyle = '#33383e'; ctx.lineWidth = 4;
    ctx.beginPath(); ctx.moveTo(-46, 0); ctx.lineTo(-46, -86); ctx.arc(0, -86, 46, Math.PI, 0); ctx.lineTo(46, 0); ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.save(); ctx.clip(); ctx.fillStyle = '#767b82'; ctx.fillRect(6, -132, 60, 140); ctx.restore();
    ctx.strokeStyle = '#5a5f66'; ctx.lineWidth = 7; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(0, -58); ctx.lineTo(0, -104); ctx.moveTo(-16, -90); ctx.lineTo(16, -90); ctx.stroke();
    ctx.fillStyle = '#4a4f55'; ctx.font = 'bold 22px Georgia'; ctx.textAlign = 'center'; ctx.fillText('R.I.P.', 0, -26);
    ctx.restore();
  }
  function wife(ctx, p) {
    const s = p.s || 1; ctx.save(); ctx.translate(p.x, p.y); ctx.scale((p.flip ? -1 : 1) * s, s);
    const LINE = '#141018', DRESS = '#7a4a6a', DRESS_S = '#5e3852', SKIN = '#ecb98f', HAIR = '#4a2f1e';
    const ay = -104; const reach = p.reach || 0;
    // arms reaching to receive the rose
    limb(ctx, [[-18, ay], [-40, -74], [-56 - reach * 8, -52 - reach * 6]], 13, DRESS, LINE); circle(ctx, -56 - reach * 8, -52 - reach * 6, 8, SKIN, LINE, 3);
    // dress
    fillShape(ctx, [[-34, 2], [34, 2], [22, -118], [-22, -118]], DRESS, LINE, 4);
    ctx.save(); smoothPoly(ctx, [[-34, 2], [34, 2], [22, -118], [-22, -118]]); ctx.clip(); fillShape(ctx, [[4, 2], [34, 2], [22, -118], [4, -118]], DRESS_S, null, 0); ctx.restore();
    limb(ctx, [[18, ay], [42, -74], [58 + reach * 8, -52 - reach * 6]], 13, DRESS, LINE); circle(ctx, 58 + reach * 8, -52 - reach * 6, 8, SKIN, LINE, 3);
    // neck + head
    limb(ctx, [[0, -116], [0, -146]], 15, SKIN, LINE);
    ctx.save(); ctx.translate(0, -170);
    ctx.fillStyle = HAIR; ctx.beginPath(); ctx.arc(0, 2, 40, Math.PI * 0.9, Math.PI * 2.1); ctx.quadraticCurveTo(30, 44, 0, 40); ctx.quadraticCurveTo(-30, 44, -40, 8); ctx.closePath(); ctx.fill();
    circle(ctx, 0, 0, 32, SKIN, LINE, 3.2);
    ctx.fillStyle = HAIR; ctx.beginPath(); ctx.moveTo(-32, -8); ctx.quadraticCurveTo(-18, -36, 4, -30); ctx.quadraticCurveTo(24, -34, 32, -6); ctx.quadraticCurveTo(10, -20, -32, -8); ctx.fill();
    for (const ex of [-11, 11]) { ellipse(ctx, ex, 2, 4.5, 5, 0, '#fff', LINE, 1.4); circle(ctx, ex, 3, 2.4, LINE, null); }
    ctx.strokeStyle = LINE; ctx.lineWidth = 2; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(-7, 17); ctx.quadraticCurveTo(0, 22, 7, 17); ctx.stroke();
    ctx.restore(); ctx.restore();
  }
  // Charlie from BEHIND, kneeling (for the low-angle judgment shot)
  function charlieBackKneel(ctx, p) {
    const s = p.s || 1; const reach = p.reach || 0; const lookUp = p.lookUp || 0;
    const COAT = '#38506b', COAT_S = '#2a3c52', HAIR = '#3b2a22', PANT = '#2a2f39', SKIN = '#e8b48c', LINE = '#141018';
    ctx.save(); ctx.translate(p.x, p.y); ctx.scale(s, s);
    // kneeling legs from behind (thigh -> knee on ground -> shin/sole back)
    for (const dx of [-26, 26]) {
      limb(ctx, [[dx * 0.62, -150], [dx, -40], [dx * 1.25, -70]], 24, PANT, LINE);
      fillShape(ctx, [[dx * 1.25 - 16, -74], [dx * 1.25 + 18, -78], [dx * 1.25 + 18, -60], [dx * 1.25 - 16, -58]], '#15100c', LINE, 3, false);
    }
    // coat back
    const torso = [[-44, -150], [44, -150], [40, -38], [-40, -38]];
    fillShape(ctx, torso, COAT, LINE, 4);
    ctx.save(); smoothPoly(ctx, torso); ctx.clip(); fillShape(ctx, [[2, -150], [44, -150], [40, -38], [2, -38]], COAT_S, null, 0); ctx.restore();
    ctx.strokeStyle = COAT_S; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(0, -150); ctx.lineTo(0, -44); ctx.stroke();
    // arms (raised pleading up toward the angel)
    for (const dir of [-1, 1]) {
      limb(ctx, [[dir * 40, -142], [dir * (56 + reach * 6), -120 - reach * 46], [dir * (52 + reach * 14), -96 - reach * 104]], 16, COAT, LINE);
      circle(ctx, dir * (52 + reach * 14), -96 - reach * 104, 9, SKIN, LINE, 3);
    }
    // neck + head (back of head; tilts up so a sliver of face shows)
    limb(ctx, [[0, -150], [0, -178]], 20, SKIN, LINE);
    ctx.save(); ctx.translate(0, -196); ctx.rotate(0);
    circle(ctx, 0, -2, 37, SKIN, LINE, 3.5);
    // hair covering the back of the head
    ctx.fillStyle = HAIR; ctx.beginPath(); ctx.arc(0, -2, 38, Math.PI * 0.06, Math.PI * 0.94, false); ctx.quadraticCurveTo(0, -2 + 34 - lookUp * 14, -34, -2 + 22); ctx.quadraticCurveTo(0, -2 + 30 - lookUp * 18, 34, -2 + 22); ctx.closePath(); ctx.fill();
    ctx.restore();
    ctx.restore();
  }
  // Towering angel seen from a LOW ANGLE (imposing), holding the ledger down
  function angelTower(ctx, p) {
    const s = p.s || 1, t = p.t || 0; ctx.save(); ctx.translate(p.x, p.y); ctx.scale(s, s);
    const ROBE = '#eae0c0', ROBE_S = '#cdbf95', LINE = '#8a7c52', SKIN = '#f0d6b0';
    // wings
    ctx.fillStyle = 'rgba(248,243,224,0.92)'; ctx.strokeStyle = ROBE_S; ctx.lineWidth = 2;
    for (const sx of [-1, 1]) { ctx.save(); ctx.scale(sx, 1); const fl = Math.sin(t * 1.2) * 14; ctx.beginPath(); ctx.moveTo(40, -250); ctx.quadraticCurveTo(230, -350 - fl, 300, -180); ctx.quadraticCurveTo(180, -220, 150, -140); ctx.quadraticCurveTo(120, -200, 40, -195); ctx.closePath(); ctx.fill(); ctx.stroke(); ctx.restore(); }
    // robe (wide at bottom = low angle)
    const robe = [[-58, -240], [58, -240], [155, 30], [-155, 30]];
    fillShape(ctx, robe, ROBE, LINE, 4);
    ctx.save(); smoothPoly(ctx, robe); ctx.clip(); fillShape(ctx, [[12, -240], [58, -240], [155, 30], [40, 30]], ROBE_S, null, 0); ctx.restore();
    // arm holding ledger down toward Charlie
    limb(ctx, [[42, -222], [104, -168], [116, -96]], 22, ROBE, LINE);
    ctx.save(); ctx.translate(120, -78); ctx.rotate(0.22); fillShape(ctx, [[-40, 0], [42, -6], [48, 74], [-34, 82]], '#f6efda', '#3a3020', 3, false); ctx.strokeStyle = '#3a3020'; ctx.lineWidth = 2; for (let i = 0; i < 5; i++) { ctx.beginPath(); ctx.moveTo(-30, 14 + i * 13); ctx.lineTo(40, 8 + i * 13); ctx.stroke(); } ctx.strokeStyle = '#a01818'; ctx.lineWidth = 3.5; ctx.beginPath(); ctx.moveTo(-26, 42); ctx.lineTo(38, 32); ctx.moveTo(-22, 32); ctx.lineTo(34, 44); ctx.stroke(); ctx.restore();
    // small head high up + halo (reinforces the height)
    circle(ctx, 0, -286, 30, SKIN, LINE, 3);
    ctx.fillStyle = SKIN; // pointing chin down (looking down at Charlie)
    ctx.fillStyle = '#3b2f1a'; ctx.beginPath(); ctx.arc(0, -292, 31, Math.PI * 0.15, Math.PI * 0.85, false); ctx.fill();
    for (const ex of [-9, 9]) { ellipse(ctx, ex, -282, 4, 3.4, 0, '#fff', '#8a7c52', 1); circle(ctx, ex, -281, 2, '#333', null); }
    ctx.strokeStyle = '#8a7c52'; ctx.lineWidth = 2.4; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(-8, -270); ctx.lineTo(8, -270); ctx.stroke();
    ctx.strokeStyle = '#f5e08a'; ctx.lineWidth = 5; ctx.beginPath(); ctx.ellipse(0, -320, 33, 9, 0, 0, TAU); ctx.stroke();
    ctx.restore();
  }

  // ================= BESPOKE SHOTS (one directed shot per lyric beat) =================
  function shotFrame(gr, vig) { if (gr) grade(ctx, gr[0], gr[1], gr[2], gr[3], gr[4] || 'multiply'); vignette(ctx, vig == null ? 0.5 : vig); letterbox(ctx, 1); }
  function suburbBg(t, camx) {
    const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#5b6472'); g.addColorStop(1, '#8b93a0'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    ctx.save(); ctx.translate(camx * 0.2, 0); ctx.fillStyle = '#6b7280'; smoothPoly(ctx, [[-100, 470], [300, 430], [700, 460], [1100, 425], [1500, 460], [1500, 720], [-100, 720]]); ctx.fill(); ctx.restore();
    ctx.save(); ctx.translate(camx * 0.6, 0);
    for (let i = 0; i < 8; i++) { const x = 120 + i * 260; const hh = 150 + hash(i) * 60; ctx.fillStyle = i === 3 ? '#7a6f66' : ['#8a7d72', '#7f8a86', '#94867a'][i % 3]; poly(ctx, [[x, 560], [x, 560 - hh], [x + 90, 560 - hh - 34], [x + 180, 560 - hh], [x + 180, 560]]); ctx.fill(); for (let w = 0; w < 3; w++) fillShape(ctx, [[x + 24 + w * 52, 560 - hh + 30], [x + 24 + w * 52 + 30, 560 - hh + 30], [x + 24 + w * 52 + 30, 560 - hh + 70], [x + 24 + w * 52, 560 - hh + 70]], '#cdd6de', '#3a3f47', 2, false); }
    const cx = 900; ctx.fillStyle = '#6d6258'; poly(ctx, [[cx, 560], [cx, 300], [cx + 45, 250], [cx + 90, 300], [cx + 90, 560]]); ctx.fill(); ctx.strokeStyle = '#efe7d0'; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(cx + 45, 250); ctx.lineTo(cx + 45, 210); ctx.moveTo(cx + 28, 226); ctx.lineTo(cx + 62, 226); ctx.stroke();
    ctx.restore(); ctx.fillStyle = '#3a4048'; ctx.fillRect(0, 560, W, H - 560);
  }
  function umbrella(x, y) { ctx.save(); ctx.translate(x, y); ctx.fillStyle = '#2a2f39'; ctx.beginPath(); ctx.arc(0, 0, 70, Math.PI, 0); ctx.closePath(); ctx.fill(); ctx.strokeStyle = '#141018'; ctx.lineWidth = 3; ctx.stroke(); ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, 60); ctx.stroke(); ctx.restore(); }
  function bike(ctx, x, y, s, spin) {
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.lineCap = 'round';
    for (const wx of [-72, 72]) { ctx.strokeStyle = '#181b22'; ctx.lineWidth = 7; ctx.beginPath(); ctx.arc(wx, 0, 36, 0, TAU); ctx.stroke(); ctx.save(); ctx.translate(wx, 0); ctx.rotate(spin); ctx.strokeStyle = '#667'; ctx.lineWidth = 2; for (let k = 0; k < 6; k++) { ctx.rotate(TAU / 6); ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(32, 0); ctx.stroke(); } ctx.restore(); }
    ctx.strokeStyle = '#242a34'; ctx.lineWidth = 7; ctx.beginPath(); ctx.moveTo(-72, 0); ctx.lineTo(-10, -50); ctx.lineTo(72, 0); ctx.moveTo(-10, -50); ctx.lineTo(-34, 0); ctx.lineTo(8, 0); ctx.lineTo(-10, -50); ctx.moveTo(-10, -50); ctx.lineTo(-24, -58); ctx.moveTo(72, 0); ctx.lineTo(58, -56); ctx.lineTo(40, -56); ctx.stroke();
    ctx.restore();
  }
  function flag(ctx, x, y, s, t) {
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
    ctx.strokeStyle = '#6a5a44'; ctx.lineWidth = 8; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, -230); ctx.stroke(); ctx.fillStyle = '#c9a44a'; ctx.beginPath(); ctx.arc(0, -234, 7, 0, TAU); ctx.fill();
    const FW = 190, FH = 116; ctx.save(); ctx.translate(4, -226);
    for (let r = 0; r < 7; r++) { const yy = r * (FH / 7); ctx.fillStyle = r % 2 ? '#c9d2dc' : '#a83a3a'; ctx.beginPath(); for (let xx = 0; xx <= FW; xx += 10) { const wob = Math.sin(xx * 0.03 - t * 4) * 9 * (xx / FW); ctx.lineTo(xx, yy + wob); } for (let xx = FW; xx >= 0; xx -= 10) { const wob = Math.sin(xx * 0.03 - t * 4) * 9 * (xx / FW); ctx.lineTo(xx, yy + FH / 7 + wob); } ctx.closePath(); ctx.fill(); }
    ctx.fillStyle = '#2a3a6a'; ctx.beginPath(); for (let xx = 0; xx <= FW * 0.42; xx += 8) { const wob = Math.sin(xx * 0.03 - t * 4) * 9 * (xx / FW); ctx.lineTo(xx, wob); } for (let xx = FW * 0.42; xx >= 0; xx -= 8) { const wob = Math.sin(xx * 0.03 - t * 4) * 9 * (xx / FW); ctx.lineTo(xx, FH * 0.55 + wob); } ctx.closePath(); ctx.fill();
    ctx.restore(); ctx.restore();
  }
  function fish(ctx, x, y, s, a) { ctx.save(); ctx.translate(x, y); ctx.rotate(a); ctx.scale(s, s); ctx.fillStyle = '#8fb0c8'; ctx.strokeStyle = '#26485f'; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.ellipse(0, 0, 28, 13, 0, 0, TAU); ctx.fill(); ctx.stroke(); ctx.beginPath(); ctx.moveTo(24, 0); ctx.lineTo(42, -13); ctx.lineTo(42, 13); ctx.closePath(); ctx.fill(); ctx.stroke(); ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(-17, -3, 3.2, 0, TAU); ctx.fill(); ctx.fillStyle = '#111'; ctx.beginPath(); ctx.arc(-17, -3, 1.6, 0, TAU); ctx.fill(); ctx.restore(); }
  function sharkFin(ctx, x, y, s) { ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.fillStyle = '#3a4652'; ctx.strokeStyle = '#151b22'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(-28, 0); ctx.quadraticCurveTo(-2, -6, 10, -50); ctx.quadraticCurveTo(16, -8, 28, 0); ctx.closePath(); ctx.fill(); ctx.stroke(); ctx.strokeStyle = 'rgba(255,255,255,0.5)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(-42, 5); ctx.lineTo(-96, 12); ctx.moveTo(-32, 12); ctx.lineTo(-74, 20); ctx.stroke(); ctx.restore(); }
  function fence(ctx, y) { for (let x = 16; x < W; x += 56) { ctx.fillStyle = '#b7a98c'; ctx.strokeStyle = '#6a5f48'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x, y - 72); ctx.lineTo(x + 18, y - 88); ctx.lineTo(x + 36, y - 72); ctx.lineTo(x + 36, y); ctx.closePath(); ctx.fill(); ctx.stroke(); } ctx.strokeStyle = '#8a7c5e'; ctx.lineWidth = 9; ctx.beginPath(); ctx.moveTo(0, y - 26); ctx.lineTo(W, y - 26); ctx.moveTo(0, y - 58); ctx.lineTo(W, y - 58); ctx.stroke(); }
  function waterFill(ctx, y, t, col) { ctx.fillStyle = col; ctx.beginPath(); ctx.moveTo(0, y); for (let x = 0; x <= W; x += 18) ctx.lineTo(x, y + Math.sin(x * 0.03 + t * 2) * 5); ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath(); ctx.fill(); }

  function shotEstablish(t, f) {
    const camx = -lerp(0, 300, smooth(clamp((t - 2) / 16))); suburbBg(t, camx);
    const cyc = t * 3.2, step = 0.5 * Math.sin(cyc);
    charlie(ctx, { x: W * 0.5, y: 600, s: 0.92, head: -0.05, brow: 0.2, smile: true, eye: 1, mouth: f.v * 0.6, armL: [Math.PI / 2 + 0.5, -0.6], armR: [Math.PI / 2 - 0.5 + step, 0.5], legL: [Math.PI / 2 + step, -0.3 - 0.2 * Math.max(0, Math.sin(cyc))], legR: [Math.PI / 2 - step, -0.3 - 0.2 * Math.max(0, -Math.sin(cyc))] });
    umbrella(W * 0.5 - 34, 350); stepRain(f); drawRain(ctx, 0.5); shotFrame([60, 80, 120, 0.28]); if (t > 2 && t < 10) titleCard(ctx, t);
  }
  function shotLight(t, f) {
    const dim = smooth(clamp((t - 20) / 0.5));
    ctx.fillStyle = lerp255('#4a3f34', '#241d17', dim); ctx.fillRect(0, 0, W, H);
    const lg = ctx.createRadialGradient(W * 0.5, 90, 20, W * 0.5, 90, 720); lg.addColorStop(0, `rgba(255,220,150,${0.55 * (1 - dim)})`); lg.addColorStop(1, 'rgba(255,220,150,0)'); ctx.fillStyle = lg; ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = lerp255('#33291f', '#1a140f', dim); ctx.fillRect(0, 600, W, H - 600);
    ctx.strokeStyle = '#2a241a'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(W * 0.5, 0); ctx.lineTo(W * 0.5, 92); ctx.stroke(); ctx.fillStyle = dim > 0.5 ? '#5a5240' : '#ffe6a0'; ctx.beginPath(); ctx.arc(W * 0.5, 108, 17, 0, TAU); ctx.fill();
    fillShape(ctx, [[1004, 402], [1048, 402], [1048, 480], [1004, 480]], '#d8d2c4', '#555', 3, false); ctx.fillStyle = dim > 0.5 ? '#555' : '#f4d9a0'; ctx.fillRect(1018, 414, 16, 34);
    charlie(ctx, { x: 900, y: 640, s: 1.18, head: -0.04, brow: 0.4, smile: true, eye: 1, mouth: clamp(0.12 + f.v * 0.6), armR: [-0.62, 0.28], armL: [Math.PI / 2 - 0.2, -0.2] });
    shotFrame([80, 66, 54, 0.18], 0.45);
  }
  function shotBike(t, f) {
    const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#6a6f7e'); g.addColorStop(1, '#9aa0ac'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    const sx = (t * 420) % 280; ctx.fillStyle = '#7f8a86'; for (let i = -1; i < 7; i++) { const x = i * 280 - sx; poly(ctx, [[x, 540], [x, 380], [x + 120, 340], [x + 240, 380], [x + 240, 540]]); ctx.fill(); }
    ctx.fillStyle = '#3a4048'; ctx.fillRect(0, 540, W, H - 540);
    ctx.strokeStyle = '#cfc9b0'; ctx.lineWidth = 6; ctx.setLineDash([40, 40]); ctx.lineDashOffset = -(t * 420) % 80; ctx.beginPath(); ctx.moveTo(0, 666); ctx.lineTo(W, 666); ctx.stroke(); ctx.setLineDash([]);
    const y = 552, ped = t * 9;
    bike(ctx, W * 0.5, y, 1.05, t * 14);
    charlie(ctx, { x: W * 0.5, y: y - 60, s: 1.0, lean: 0.2, head: 0.02, brow: 0.25, eye: 1, smile: true, mouth: clamp(0.1 + f.v * 0.6), armL: [Math.PI / 2 - 0.95, -0.15], armR: [Math.PI / 2 - 0.9, 0.15], legL: [Math.PI / 2 + 0.55 * Math.sin(ped), 0.75], legR: [Math.PI / 2 + 0.55 * Math.sin(ped + Math.PI), 0.75] });
    stepRain(f); drawRain(ctx, 0.4); shotFrame([70, 80, 110, 0.22]);
  }
  function shotFish(t, f) {
    const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#e0a35a'); g.addColorStop(0.5, '#b97a56'); g.addColorStop(1, '#4a6b7a'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = 'rgba(255,220,150,0.85)'; ctx.beginPath(); ctx.arc(W * 0.72, 300, 62, 0, TAU); ctx.fill();
    waterFill(ctx, 470, t, '#456a82');
    ctx.fillStyle = '#5a4632'; ctx.fillRect(0, 536, 430, 30); for (let i = 0; i < 4; i++) ctx.fillRect(70 + i * 110, 562, 16, 130);
    const cast = Math.sin((t - 24.62) * 2.2);
    charlie(ctx, { x: 330, y: 536, s: 1.0, head: 0.02, brow: 0.2, smile: true, eye: 1, mouth: clamp(0.1 + f.v * 0.5), armR: [Math.PI / 2 - 1.35 + cast * 0.5, 0.2], armL: [Math.PI / 2 - 0.9, -0.2] });
    const rx = 470, ry = 350; ctx.strokeStyle = '#3a2a1a'; ctx.lineWidth = 4; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(400, 420); ctx.lineTo(rx, ry); ctx.stroke();
    ctx.strokeStyle = 'rgba(240,240,240,0.7)'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(rx, ry); ctx.lineTo(720, 496 + Math.sin(t * 2) * 6); ctx.stroke();
    const fj = t - 25.6; if (fj > 0 && fj < 1.2) fish(ctx, 730, 470 - Math.sin(fj / 1.2 * Math.PI) * 170, 1.15, -0.7 + fj);
    shotFrame([120, 90, 60, 0.16], 0.42);
  }
  function shotFlag(t, f) {
    const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#9dc3e6'); g.addColorStop(1, '#e2ebf2'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = 'rgba(255,255,255,0.7)'; for (const c of [[220, 170, 92], [860, 130, 72]]) { ctx.beginPath(); ctx.ellipse(c[0], c[1], c[2] * 1.7, c[2] * 0.6, 0, 0, TAU); ctx.fill(); }
    flag(ctx, W * 0.6, 500, 1.55, t);
    charlie(ctx, { x: W * 0.4, y: 700, s: 0.92, head: -0.22, brow: 0.45, smile: true, eye: 1, mouth: clamp(0.1 + f.v * 0.6), armR: [Math.PI / 2 - 1.4, -0.95], armL: [Math.PI / 2 - 0.1, -0.2] });
    shotFrame([120, 120, 140, 0.1], 0.4);
  }
  function shotShark(t, f) {
    const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#3a5a7a'); g.addColorStop(1, '#5f88a2'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    waterFill(ctx, 120, t, '#2f6a86');
    ctx.fillStyle = '#d8c48a'; ctx.beginPath(); ctx.moveTo(0, 560); for (let x = 0; x <= W; x += 20) ctx.lineTo(x, 560 + Math.sin(x * 0.02 + t) * 8); ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath(); ctx.fill();
    const fx = W * 0.5 + Math.cos(t * 1.2) * 230, fy = 340 + Math.sin(t * 1.2) * 60; sharkFin(ctx, fx, fy, 1.15);
    ctx.save(); ctx.translate(W * 0.5, 360); ctx.rotate(0.05); ctx.translate(-W * 0.5, -360);
    charlie(ctx, { x: W * 0.5, y: 646, s: 0.96, lean: -0.16, head: 0.18, brow: -0.7, eye: 1, mouth: 0.7, armL: [Math.PI + 0.3, 0.3], armR: [-0.3, -0.3] });
    ctx.restore(); speedLines(ctx, W * 0.5, 500, 0.35 + 0.3 * f.beat, '40,60,80', 0.12);
    shotFrame([80, 90, 110, 0.2], 0.5);
  }
  function shotRose(t, f) {
    suburbBg(t, -260); const e = smooth(clamp((t - 34.5) / 1.0)) * smooth(clamp((38.4 - t) / 0.9)); const wx = W * 0.44;
    charlie(ctx, { x: wx, y: 600, s: 1.0, head: -0.05, brow: 0.4, smile: true, eye: 1, mouth: clamp(0.1 + f.v * 0.5), armR: [0.15, 0.15], armL: [Math.PI / 2 - 0.2, -0.2] });
    wife(ctx, { x: wx + 182, y: 602, flip: true, reach: e });
    rose(ctx, wx + lerp(82, 150, e), 480 + Math.sin(t * 3) * 2, -0.6 - e * 0.25, 1.05);
    stepRain(f); drawRain(ctx, 0.4); shotFrame([70, 80, 120, 0.26]);
  }
  function shotDodge(t, f) {
    suburbBg(t, -320);
    charlie(ctx, { x: W * 0.46, y: 600, s: 1.05, flip: true, head: 0.12, brow: -0.3, eye: 1, mouth: clamp(0.2 + f.v * 0.5), armR: [Math.PI / 2 - 1.5, -0.4], armL: [Math.PI / 2 + 0.3, 0.4] });
    ctx.fillStyle = '#bfe0ff'; ctx.beginPath(); ctx.arc(W * 0.46 - 26, 300, 6, 0, TAU); ctx.fill();
    ctx.save(); ctx.fillStyle = '#1c1f27'; ctx.beginPath(); ctx.ellipse(W * 0.84, 780, 155, 210, 0, 0, TAU); ctx.fill(); ctx.beginPath(); ctx.arc(W * 0.84, 470, 74, 0, TAU); ctx.fill(); ctx.restore();
    ctx.fillStyle = '#e8d9b0'; ctx.font = 'bold 96px Georgia'; ctx.textAlign = 'center'; ctx.fillText('?', W * 0.7, 320);
    stepRain(f); drawRain(ctx, 0.4); shotFrame([70, 78, 110, 0.26]);
  }
  function shotNeighbors(t, f) {
    suburbBg(t, -360); fence(ctx, 560);
    for (const nx of [W * 0.3, W * 0.72]) { ctx.fillStyle = '#c98d64'; ctx.strokeStyle = '#141018'; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(nx, 500, 30, 0, TAU); ctx.fill(); ctx.stroke(); ctx.fillStyle = '#4a3a2a'; ctx.beginPath(); ctx.arc(nx, 488, 32, Math.PI, 0); ctx.fill(); }
    const wv = Math.sin((t - 44.68) * 10) * 0.3;
    charlie(ctx, { x: W * 0.5, y: 646, s: 1.0, head: 0.02, brow: 0.4, smile: true, eye: 1, mouth: clamp(0.1 + f.v * 0.6), armR: [-Math.PI / 2 + 0.2 + wv, -0.2], armL: [Math.PI / 2 - 0.2, -0.2] });
    stepRain(f); drawRain(ctx, 0.4); shotFrame([70, 80, 118, 0.24]);
  }
  function shotGrave(t, f) {
    suburbBg(t, -400); grave(ctx, W * 0.5, 588, 1.05);
    for (const m of [[W * 0.5 - 200, 616, false, 0.82], [W * 0.5 + 196, 610, true, 0.86], [W * 0.5 - 96, 636, false, 0.72]]) charlie(ctx, { x: m[0], y: m[1], s: m[3], flip: m[2], silh: true, silhCol: '#1c1f27', idle: false, head: 0.34, brow: 0.3, armL: [Math.PI / 2 - 1.0, -1.0], armR: [Math.PI / 2 - 1.0, 1.0] });
    stepRain(f); drawRain(ctx, 0.5); shotFrame([60, 80, 120, 0.3], 0.55);
  }
  function virtues(t, f) {
    if (t < 19) return shotEstablish(t, f);
    if (t < 21.18) return shotLight(t, f);
    if (t < 24.62) return shotBike(t, f);
    if (t < 27.76) return shotFish(t, f);
    if (t < 31.2) return shotFlag(t, f);
    if (t < 34.5) return shotShark(t, f);
    if (t < 38.4) return shotRose(t, f);
    if (t < 44.68) return shotDodge(t, f);
    if (t < 47.74) return shotNeighbors(t, f);
    return shotGrave(t, f);
  }

  // ============================ SCENES ============================
  // Each scene: draw(t, f) with t absolute seconds. Camera handled inside.
  const SC = [];
  function scene(t0, t1, draw) { SC.push({ t0, t1, draw }); }

  // ---- S1: hollow good life (0–50) — one directed shot per lyric beat ----
  scene(0, 50, (t, f) => { virtues(t, f); });

  // ---- S2: Ascent to gate of light (50–57.5) ----
  scene(50, 57.5, (t, f) => {
    const p = clamp((t - 50) / 7.5);
    ctx.fillStyle = '#eae0c4'; ctx.fillRect(0, 0, W, H);
    const g = ctx.createRadialGradient(W / 2, -100, 50, W / 2, -100, 900); g.addColorStop(0, '#fffef2'); g.addColorStop(1, '#e7cf92'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    godRays(ctx, W / 2, -60, 1100, 40, '255,250,220', 0.5 + 0.3 * Math.sin(t * 2), 0, TAU);
    // clouds rising (parallax down)
    for (let i = 0; i < 6; i++) { const cy = ((i * 160 + p * 500) % (H + 200)) - 100; const cx = 150 + hash(i) * 900; ctx.fillStyle = 'rgba(255,255,255,0.8)'; ellipse(ctx, cx, cy, 130, 46, 0, null); ctx.fill(); ellipse(ctx, cx + 70, cy + 12, 90, 36, 0, 'rgba(255,255,255,0.7)', null); ctx.fill(); }
    // the grave he rose from, receding below
    if (p < 0.6) { ctx.save(); ctx.globalAlpha = (0.6 - p) / 0.6; grave(ctx, W / 2, lerp(600, 860, p), lerp(0.9, 1.5, p)); ctx.restore(); }
    // his spirit rising — small -> bigger, hopeful, looking up (soft glow)
    const cs = lerp(0.7, 1.05, p), cyy = lerp(560, 470, smooth(p));
    ctx.save(); const gl = ctx.createRadialGradient(W / 2, cyy - 120, 10, W / 2, cyy - 120, 220); gl.addColorStop(0, 'rgba(255,252,235,0.5)'); gl.addColorStop(1, 'rgba(255,252,235,0)'); ctx.fillStyle = gl; ctx.fillRect(0, 0, W, H); ctx.restore();
    charlie(ctx, { gesture: gestureAt(t, f), x: W / 2, y: cyy, s: cs, head: -0.25, brow: 0.4, eye: 1, mouth: f.v * 0.6, smile: true, armL: [Math.PI / 2 - 0.6, -0.4], armR: [Math.PI / 2 + 0.6, 0.4], legL: [Math.PI / 2 + 0.05, -0.1], legR: [Math.PI / 2 - 0.05, -0.1] });
    flash(ctx, easeIn(clamp((t - 56.6) / 0.9)) * 0.9); // whiteout into next
    vignette(ctx, 0.25); letterbox(ctx, 1);
  });

  // ---- S3: The judgment — LOW ANGLE, Charlie kneeling with back to us, small &
  //         beneath a towering angel who checks the list. Position of inferiority. ----
  scene(57.5, 70.7, (t, f) => {
    const p = clamp((t - 57.5) / 13.2);
    // heavenly light, but tilting cold as the verdict lands
    const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, lerp255('#f6efd8', '#cdb6d0', p)); g.addColorStop(1, lerp255('#d8c79a', '#7a6f86', p)); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    // floor plane (low angle → we look slightly up; horizon high)
    ctx.fillStyle = 'rgba(120,110,90,0.5)'; ctx.beginPath(); ctx.moveTo(0, 470); ctx.lineTo(W, 470); ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath(); ctx.fill();
    // backlight halo behind the angel
    const bl = ctx.createRadialGradient(W / 2, 150, 20, W / 2, 150, 620); bl.addColorStop(0, 'rgba(255,250,225,0.95)'); bl.addColorStop(1, 'rgba(255,250,225,0)'); ctx.fillStyle = bl; ctx.fillRect(0, 0, W, H);
    godRays(ctx, W / 2, 60, 1000, 34, '255,248,215', 0.5 + 0.2 * Math.sin(t * 1.5), 0, TAU);
    // slow push-in
    const zoom = lerp(1.0, 1.12, smooth(p)); ctx.save(); ctx.translate(W / 2, 470); ctx.scale(zoom, zoom); ctx.translate(-W / 2, -470);
    // TOWERING angel, filling the frame from above
    angelTower(ctx, { x: W / 2, y: 470, s: 1.16, t });
    // long cast shadow of the angel over Charlie
    ctx.save(); ctx.globalAlpha = 0.18; ctx.fillStyle = '#20180f'; ctx.beginPath(); ctx.ellipse(W / 2, 690, 320, 40, 0, 0, TAU); ctx.fill(); ctx.restore();
    // Charlie: small, back to camera, kneeling; bows then looks up pleading
    const rise = smooth(clamp((t - 61) / 3));           // starts kneeling low, lifts arms
    const gaze = smooth(clamp((t - 64) / 2));            // looks up when rejected
    charlieBackKneel(ctx, { x: W / 2, y: 700, s: 0.62 + 0.05 * gaze, reach: 0.2 + 0.8 * rise, lookUp: gaze });
    ctx.restore();
    // the red rejection stroke flares on the ledger at the verdict
    if (p > 0.5) flash(ctx, clamp((t - 64) / 0.4) * (1 - clamp((t - 64.6) / 0.6)) * 0.25, '180,40,40');
    speedLines(ctx, W / 2, 300, clamp((t - 64) / 2) * (0.4 + f.beat), '80,60,70', 0.14);
    grade(ctx, 90, 74, 88, 0.16 * p, 'multiply'); vignette(ctx, 0.45); letterbox(ctx, 1);
  });

  // ---- S4: chorus — plea + the descent begins (70.7–100.5) ----
  scene(70.7, 100.5, (t, f) => {
    const p = clamp((t - 70.7) / 29.8);
    // world tips red; long fall down an elevator shaft with rushing floors
    const topcol = lerp(120, 40, p) | 0;
    const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, `rgb(${lerp(60, 30, p) | 0},${lerp(50, 12, p) | 0},${lerp(70, 16, p) | 0})`); g.addColorStop(1, `rgb(${lerp(90, 150, p) | 0},${lerp(40, 30, p) | 0},${lerp(40, 20, p) | 0})`); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    // rushing floor lines (parallax up) => sense of falling
    ctx.save(); ctx.strokeStyle = `rgba(20,10,12,0.5)`; ctx.lineWidth = 6;
    for (let i = 0; i < 14; i++) { const yy = ((i * 90 + (t * 620) % 90 + t * 60) % (H + 180)) - 90; const wob = 1 - Math.abs(yy - H / 2) / (H / 2); ctx.globalAlpha = 0.3 + 0.5 * wob; ctx.beginPath(); ctx.moveTo(0, yy); ctx.lineTo(W, yy + 8); ctx.stroke(); }
    ctx.restore();
    // side shaft walls converging (perspective)
    ctx.fillStyle = 'rgba(15,8,10,0.55)'; smoothPoly(ctx, [[0, 0], [230, 0], [430, H / 2], [230, H], [0, H]]); ctx.fill(); smoothPoly(ctx, [[W, 0], [W - 230, 0], [W - 430, H / 2], [W - 230, H], [W, H]]); ctx.fill();
    // shrinking light above
    const ly = lerp(120, -60, p); const lr = lerp(160, 40, p); const lg = ctx.createRadialGradient(W / 2, ly, 0, W / 2, ly, lr * 3); lg.addColorStop(0, 'rgba(255,245,210,0.9)'); lg.addColorStop(1, 'rgba(255,245,210,0)'); ctx.fillStyle = lg; ctx.beginPath(); ctx.arc(W / 2, ly, lr * 3, 0, TAU); ctx.fill();
    // Charlie falling, reaching up toward the light, tumbling slightly
    const tumble = Math.sin(t * 1.2) * 0.12; const reach = 0.5 + 0.5 * Math.sin(t * 3);
    charlie(ctx, { gesture: gestureAt(t, f), x: W / 2 + Math.sin(t * 0.9) * 40, y: 430 + Math.sin(t * 1.5) * 20, s: 1.0, lean: tumble, head: -0.3, brow: -0.7, eye: 1, mouth: clamp(0.3 + f.v), armL: [Math.PI * 1.5 - 0.3, -0.2 - reach * 0.2], armR: [Math.PI * 1.5 + 0.3, 0.2 + reach * 0.2], legL: [Math.PI / 2 + 0.4, 0.4], legR: [Math.PI / 2 - 0.5, -0.4] });
    speedLines(ctx, W / 2, H / 2, 0.5 + 0.5 * f.e, '255,120,40', 0.18 + 0.2 * f.beat);
    stepEmbers(f, 0.6 + p); drawEmbers(ctx);
    grade(ctx, 150, 40, 20, 0.12 * p, 'overlay'); vignette(ctx, 0.5); letterbox(ctx, 1);
  });

  // ---- S5: the grotesque consumerist inferno (100.5–129.8) ----
  scene(100.5, 129.8, (t, f) => {
    const camx = Math.sin(t * 0.4) * 40;
    const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#2a0a0c'); g.addColorStop(0.6, '#5c1410'); g.addColorStop(1, '#a83218'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    // "ABANDON ALL HOPE" arch (Dante), stylized, not lyrics
    ctx.save(); ctx.translate(camx * 0.3, 0); ctx.strokeStyle = '#3a0d0a'; ctx.lineWidth = 46; ctx.beginPath(); ctx.arc(W / 2, 360, 300, Math.PI, 0); ctx.stroke(); ctx.restore();
    ctx.fillStyle = '#f0c33a'; ctx.font = 'bold 30px Georgia'; ctx.textAlign = 'center'; ctx.fillText('ABANDON  ALL  HOPE', W / 2 + camx * 0.3, 138);
    // pillars of the hall
    ctx.save(); ctx.translate(camx * 0.5, 0); ctx.fillStyle = '#320c0a'; for (const x of [120, 380, 900, 1160]) { fillShape(ctx, [[x, 700], [x, 200], [x + 60, 200], [x + 60, 700]], null); ctx.fill(); } ctx.restore();
    // crowd of the damned (silhouettes) + a demon clerk at a desk
    crowd(ctx, 640, 12, 'rgba(20,6,8,0.9)', 8, t);
    // demon clerk
    charlie(ctx, { x: W * 0.30, y: 600, s: 1.2, silh: true, silhCol: '#180608', rim: '#ff6a2a', head: 0.05, armR: [Math.PI / 2 - 0.9, 0.4] });
    // horns on the demon
    ctx.save(); ctx.fillStyle = '#180608'; ctx.strokeStyle = '#ff6a2a'; ctx.lineWidth = 2; for (const sx of [-1, 1]) { ctx.beginPath(); ctx.moveTo(W * 0.30 + sx * 20, 600 - 210 * 1.2); ctx.quadraticCurveTo(W * 0.30 + sx * 46, 600 - 260 * 1.2, W * 0.30 + sx * 30, 600 - 285 * 1.2); ctx.lineWidth = 10; ctx.strokeStyle = '#180608'; ctx.stroke(); } ctx.restore();
    // Charlie being processed, protesting (arms out)
    charlie(ctx, { gesture: gestureAt(t, f), x: W * 0.62, y: 615, s: 1.0, head: 0.1, brow: -0.7, eye: 1, mouth: clamp(0.3 + f.v), armL: [Math.PI / 2 - 1.2, -0.4], armR: [Math.PI / 2 + 1.2, 0.4], legL: [Math.PI / 2 + 0.1, -0.1], legR: [Math.PI / 2 - 0.1, -0.1] });
    flameRow(ctx, 700, 130, 0.5, t, f); stepEmbers(f, 1); drawEmbers(ctx);
    grade(ctx, 180, 40, 20, 0.14, 'overlay'); vignette(ctx, 0.5); letterbox(ctx, 1);
  });

  // ---- S6: the devil's chase — demon checks the list (129.8–149.7) ----
  scene(129.8, 149.7, (t, f) => {
    const p = clamp((t - 129.8) / 19.9);
    const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#1c0608'); g.addColorStop(1, '#7a1810'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    gate(ctx, W * 0.5, 250, 1.15, '#2a0a0a', ['#a8321a', '#3a0d0a']);
    // demon gatekeeper with ledger (mirror of angel)
    const ax = W * 0.36;
    charlie(ctx, { x: ax, y: 470, s: 1.55, silh: true, silhCol: '#12060a', rim: '#ff5a2a', armR: [Math.PI / 2 - 1.0, 0.3] });
    for (const sx of [-1, 1]) { ctx.strokeStyle = '#12060a'; ctx.lineWidth = 12; ctx.beginPath(); ctx.moveTo(ax + sx * 22, 470 - 210 * 1.55); ctx.quadraticCurveTo(ax + sx * 52, 470 - 265 * 1.55, ax + sx * 34, 470 - 292 * 1.55); ctx.stroke(); }
    ctx.save(); ctx.translate(ax + 74, 400); ctx.rotate(-0.12); fillShape(ctx, [[0, 0], [120, -14], [130, 90], [10, 104]], '#20100e', '#ff7a3a', 3, false); ctx.strokeStyle = '#ff7a3a'; ctx.lineWidth = 2; for (let i = 0; i < 6; i++) { ctx.beginPath(); ctx.moveTo(14, 12 + i * 14); ctx.lineTo(116, 12 + i * 14 - 6); ctx.stroke(); } ctx.restore();
    // Charlie begging, knocked down as p rises
    const down = smooth(clamp((t - 145) / 4));
    charlie(ctx, { gesture: gestureAt(t, f), x: W * 0.72, y: 560 + down * 40, s: 0.95, lean: down * 0.5, head: 0.2, brow: -0.9, eye: 1 - down * 0.5, mouth: clamp(0.4 + f.v), armL: [Math.PI / 2 - 0.9 - down, -0.3], armR: [Math.PI / 2 + 0.9 + down, 0.3] });
    speedLines(ctx, W * 0.72, 420, 0.4 + f.beat, '255,80,30', 0.16);
    stepEmbers(f, 1); drawEmbers(ctx);
    grade(ctx, 180, 40, 20, 0.16, 'overlay'); vignette(ctx, 0.55); letterbox(ctx, 1);
  });

  // ---- S7: chorus reprise — deeper descent (149.7–175.9) ----
  scene(149.7, 175.9, (t, f) => {
    const p = clamp((t - 149.7) / 26.2);
    const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#160406'); g.addColorStop(1, `rgb(${lerp(120, 180, p) | 0},30,18)`); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    ctx.save(); ctx.strokeStyle = 'rgba(30,8,10,0.5)'; ctx.lineWidth = 7; for (let i = 0; i < 16; i++) { const yy = ((i * 80 + (t * 760) % 80) % (H + 160)) - 80; ctx.beginPath(); ctx.moveTo(0, yy); ctx.lineTo(W, yy + 10); ctx.stroke(); } ctx.restore();
    ctx.fillStyle = 'rgba(10,4,6,0.6)'; smoothPoly(ctx, [[0, 0], [260, 0], [460, H / 2], [260, H], [0, H]]); ctx.fill(); smoothPoly(ctx, [[W, 0], [W - 260, 0], [W - 460, H / 2], [W - 260, H], [W, H]]); ctx.fill();
    // faces of demons flashing on beat at the walls
    if (f.beat > 0.5) { ctx.save(); ctx.globalAlpha = f.beat * 0.5; for (const sx of [0.12, 0.88]) { circle(ctx, W * sx, H * (0.3 + hash((t * 24 | 0)) * 0.4), 40, '#2a0a0c', '#ff5a2a', 3); } ctx.restore(); }
    charlie(ctx, { gesture: gestureAt(t, f), x: W / 2 + Math.sin(t * 0.9) * 46, y: 430 + Math.sin(t * 1.6) * 22, s: 1.0, lean: Math.sin(t * 1.1) * 0.14, head: -0.2, brow: -0.8, eye: 1, mouth: clamp(0.3 + f.v), armL: [Math.PI * 1.5 - 0.3, -0.3], armR: [Math.PI * 1.5 + 0.3, 0.3], legL: [Math.PI / 2 + 0.5, 0.4], legR: [Math.PI / 2 - 0.6, -0.4] });
    speedLines(ctx, W / 2, H / 2, 0.6 + 0.4 * f.e, '255,110,40', 0.2 + 0.2 * f.beat);
    stepEmbers(f, 1.2); drawEmbers(ctx);
    grade(ctx, 170, 40, 20, 0.16, 'overlay'); vignette(ctx, 0.55); letterbox(ctx, 1);
  });

  // ---- S8: bridge — the endless futile run (175.9–200.2) ----
  scene(175.9, 200.2, (t, f) => {
    const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#20080a'); g.addColorStop(1, '#8a1e12'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    // scrolling infernal ground + pillars (side-scroller run)
    const sx = (t * 520) % 300;
    ctx.save(); ctx.fillStyle = '#2a0a0a'; for (let i = -1; i < 6; i++) { const x = i * 300 - sx; fillShape(ctx, [[x, 700], [x, 300], [x + 50, 300], [x + 50, 700]], null); ctx.fill(); } ctx.restore();
    ctx.fillStyle = '#12060a'; ctx.fillRect(0, 640, W, 80);
    // pursuing hands/silhouettes behind
    crowd(ctx, 700, 8, 'rgba(12,4,6,0.85)', 4, t);
    // Charlie running (full side profile), hard run cycle
    const cyc = t * 9; const s = 1.05;
    charlie(ctx, { x: W * 0.42, y: 630, s: s, flip: false, lean: 0.16, head: 0.08, brow: -0.7, eye: 1, mouth: clamp(0.3 + f.v),
      armL: [Math.PI / 2 - 1.1 + Math.sin(cyc) * 0.9, -0.9], armR: [Math.PI / 2 + 1.1 - Math.sin(cyc) * 0.9, 0.9],
      legL: [Math.PI / 2 + Math.sin(cyc) * 0.8, -0.6 - 0.4 * Math.max(0, Math.cos(cyc))], legR: [Math.PI / 2 - Math.sin(cyc) * 0.8, -0.6 - 0.4 * Math.max(0, -Math.cos(cyc))] });
    speedLines(ctx, W * 0.42, 500, 0.5 + 0.4 * f.e, '255,120,50', 0.16 + 0.15 * f.beat);
    stepEmbers(f, 0.9); drawEmbers(ctx);
    // horizontal speed streaks
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.strokeStyle = 'rgba(255,160,80,0.15)'; ctx.lineWidth = 3; for (let i = 0; i < 10; i++) { const yy = hash(i * 3 + (t * 12 | 0)) * H; ctx.beginPath(); ctx.moveTo(0, yy); ctx.lineTo(W, yy); ctx.stroke(); } ctx.restore();
    grade(ctx, 180, 50, 20, 0.16, 'overlay'); vignette(ctx, 0.55); letterbox(ctx, 1);
  });

  // ---- S9: outro — no redemption, swallowed (200.2–end) ----
  scene(200.2, 231, (t, f) => {
    const p = clamp((t - 200.2) / (DUR - 200.2));
    const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#160406'); g.addColorStop(1, '#6e1810'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    // gates closing above (two shutters)
    const close = smooth(clamp((t - 206) / 12));
    // Charlie tiny at bottom, alone in vast inferno, looking up
    const cs = lerp(0.9, 0.4, p);
    flameRow(ctx, 720, 200, 0.55, t, f);
    charlie(ctx, { x: W / 2, y: lerp(560, 660, p), s: cs, silh: true, silhCol: '#0c0406', rim: '#ff6a2a', head: -0.3, armL: [Math.PI * 1.5 - 0.2, -0.2], armR: [Math.PI * 1.5 + 0.2, 0.2] });
    stepEmbers(f, 1.3); drawEmbers(ctx);
    // shutters
    ctx.fillStyle = '#0a0304'; ctx.fillRect(0, -20, W, close * 120); // ceiling darkening
    const halo = ctx.createRadialGradient(W / 2, 40, 0, W / 2, 40, lerp(300, 30, close)); halo.addColorStop(0, `rgba(255,240,200,${(1 - close) * 0.5})`); halo.addColorStop(1, 'rgba(255,240,200,0)'); ctx.fillStyle = halo; ctx.fillRect(0, 0, W, H);
    grade(ctx, 160, 40, 20, 0.18, 'overlay'); vignette(ctx, 0.6); letterbox(ctx, 1);
    // end card
    if (t > 214) endCard(ctx, t);
    // final fade
    flash(ctx, clamp((t - 224) / 4) * (t > 224 ? 1 : 0) * 0 + clamp((t - 226) / (DUR - 226)), '0,0,0');
  });

  function titleCard(ctx, t) {
    const a = t < 3 ? clamp((t - 2)) : clamp((10 - t) / 2); ctx.save(); ctx.globalAlpha = a; ctx.textAlign = 'center';
    ctx.fillStyle = '#f4ead0'; ctx.strokeStyle = '#141018'; ctx.lineWidth = 5; ctx.lineJoin = 'round';
    ctx.font = "italic 800 76px Georgia, serif"; ctx.strokeText("Charlie's Inferno", W / 2, H * 0.44); ctx.fillText("Charlie's Inferno", W / 2, H * 0.44);
    ctx.font = "italic 600 28px Georgia, serif"; ctx.fillStyle = '#d8c39a'; ctx.strokeText('That Handsome Devil — cover PT-BR', W / 2, H * 0.44 + 46); ctx.fillText('That Handsome Devil — cover PT-BR', W / 2, H * 0.44 + 46);
    ctx.restore();
  }
  function endCard(ctx, t) {
    const a = clamp((t - 214) / 2); ctx.save(); ctx.globalAlpha = a; ctx.textAlign = 'center'; ctx.fillStyle = '#e8cfa0'; ctx.font = "italic 700 40px Georgia, serif"; ctx.fillText('— fim —', W / 2, H * 0.5); ctx.restore();
  }

  // ---------- main ----------
  function init(timeline) {
    TL = timeline; FPS = timeline.fps; DUR = timeline.duration || 230.25;
    const cv = document.getElementById('c'); cv.width = W; cv.height = H; ctx = cv.getContext('2d'); pools = {}; _pn = 0; CH = {};
  }
  function renderFrame(i) {
    const t = i / FPS; const f = F(i); NOW = t;
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, W, H); ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
    // pick scene
    let s = SC[SC.length - 1]; for (const sc of SC) { if (t >= sc.t0 && t < sc.t1) { s = sc; break; } }
    // subtle global beat camera shake + hard-cut flash at scene starts
    const shake = f.beat * 6 + f.onset * 4; const sx = (hash(i) - 0.5) * shake, sy = (hash(i * 7) - 0.5) * shake;
    ctx.save(); ctx.translate(sx, sy); ctx.scale(1.015, 1.015); ctx.translate(-W * 0.0075, -H * 0.0075);
    s.draw(t, f);
    ctx.restore();
    // cut flash
    for (const sc of SC) { if (Math.abs(t - sc.t0) < 0.05 && sc.t0 > 0.1) { flash(ctx, 0.5, '255,240,220'); } }
    // global intro/outro fade
    flash(ctx, clamp((1.2 - t) / 1.2), '0,0,0');
  }
  global.CharlieInferno = { init, renderFrame, W, H };
})(window);
