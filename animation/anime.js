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

  // ---------- Charlie (cel-shaded everyman) ----------
  // p: {x,y,s,flip,lean,head,armL:[a1,a2],armR:[a1,a2],legL:[a1,a2],legR:[a1,a2],
  //     mouth,eye,brow,silh,light}
  function charlie(ctx, p) {
    const s = p.s || 1, flip = p.flip ? -1 : 1;
    const SKIN = '#e8b48c', SKIN_S = '#c98d64', HAIR = '#3b2a22', COAT = '#38506b', COAT_S = '#26374d', SHIRT = '#d9dde3', PANT = '#2a2f39', LINE = '#141018';
    const silh = p.silh; const bodyF = silh ? (p.silhCol || '#0b0910') : COAT, bodyL = silh ? (p.silhCol || '#0b0910') : LINE;
    ctx.save(); ctx.translate(p.x, p.y); ctx.scale(flip * s, s); ctx.rotate(p.lean || 0);
    const hipY = 0, shY = -150, headY = -210;
    // legs
    const lg = p.legL || [Math.PI / 2 + 0.12, -0.15], rg = p.legR || [Math.PI / 2 - 0.12, 0.15];
    for (const [hip, dir, g] of [[[-14, hipY], lg, 1], [[14, hipY], rg, -1]]) {
      const kx = hip[0] + Math.cos(dir[0]) * 78, ky = hip[1] + Math.sin(dir[0]) * 78;
      const fx = kx + Math.cos(dir[0] + dir[1]) * 74, fy = ky + Math.sin(dir[0] + dir[1]) * 74;
      limb(ctx, [hip, [kx, ky], [fx, fy]], 22, silh ? bodyF : PANT, bodyL);
      // shoe
      fillShape(ctx, [[fx - 6, fy], [fx + 22, fy - 4], [fx + 24, fy + 10], [fx - 8, fy + 10]], silh ? bodyF : '#15100c', bodyL, 3);
    }
    // arms (behind torso first: right)
    function arm(root, a, col) { const [a1, a2] = a; const ex = root[0] + Math.cos(a1) * 60, ey = root[1] + Math.sin(a1) * 60; const hx = ex + Math.cos(a1 + a2) * 58, hy = ey + Math.sin(a1 + a2) * 58; limb(ctx, [root, [ex, ey], [hx, hy]], 18, col, bodyL); circle(ctx, hx, hy, 10, silh ? bodyF : SKIN, bodyL, 3); return [hx, hy]; }
    const handR = arm([26, shY + 16], p.armR || [Math.PI / 2 + 0.2, 0.2], bodyF);
    // torso (coat)
    const torso = [[-40, shY], [40, shY], [52, shY + 70], [30, hipY + 6], [-30, hipY + 6], [-52, shY + 70]];
    fillShape(ctx, torso, bodyF, bodyL, 4);
    if (!silh) {
      // shirt V + tie
      fillShape(ctx, [[-14, shY + 4], [14, shY + 4], [8, shY + 70], [-8, shY + 70]], SHIRT, null, 0);
      fillShape(ctx, [[-6, shY + 8], [6, shY + 8], [9, shY + 74], [0, shY + 92], [-9, shY + 74]], '#7d2530', null, 0);
      // coat shadow (cel) on right side
      ctx.save(); smoothPoly(ctx, torso); ctx.clip(); fillShape(ctx, [[8, shY], [40, shY], [52, shY + 70], [30, hipY + 6], [12, hipY]], COAT_S, null, 0); ctx.restore();
    }
    const handL = arm([-26, shY + 16], p.armL || [Math.PI / 2 - 0.2, -0.2], bodyF);
    // neck + head
    limb(ctx, [[0, shY], [0, headY + 34]], 22, silh ? bodyF : SKIN, bodyL);
    const hp = [0, headY];
    ctx.save(); ctx.translate(hp[0], hp[1]); ctx.rotate(p.head || 0);
    circle(ctx, 0, 0, 40, silh ? bodyF : SKIN, bodyL, 3.5);
    if (!silh) {
      // face shadow
      ctx.save(); circle(ctx, 0, 0, 40); ctx.clip(); ctx.fillStyle = SKIN_S; ctx.beginPath(); ctx.ellipse(22, 2, 30, 40, 0, 0, TAU); ctx.fill(); ctx.restore();
      // hair
      ctx.fillStyle = HAIR; ctx.beginPath(); ctx.moveTo(-42, -6); ctx.quadraticCurveTo(-46, -46, 0, -46); ctx.quadraticCurveTo(46, -46, 42, -4); ctx.quadraticCurveTo(24, -26, 6, -22); ctx.quadraticCurveTo(-6, -30, -42, -14); ctx.closePath(); ctx.fill();
      // eyes
      const eo = p.eye != null ? p.eye : 1; const ew = 6, eh = 5 * eo + 0.5;
      for (const ex of [-15, 15]) { ellipse(ctx, ex, 4, ew, eh, 0, '#fff', LINE, 1.5); if (eo > 0.4) circle(ctx, ex + (p.look || 0) * 3, 5, 3, LINE, null); }
      // brows (worry/anger via brow)
      const bw = p.brow || 0; ctx.strokeStyle = LINE; ctx.lineWidth = 2.6; ctx.lineCap = 'round';
      for (const bx of [-1, 1]) { ctx.beginPath(); ctx.moveTo(bx * 8, -8 + bw * 5 * bx * 0 - 6); ctx.lineTo(bx * 22, -8 - bw * 6); ctx.stroke(); }
      // mouth
      const mo = clamp(p.mouth || 0); ctx.strokeStyle = LINE; ctx.fillStyle = '#5a2320'; ctx.lineWidth = 2.6;
      if (mo < 0.12) { ctx.beginPath(); ctx.moveTo(-10, 22); ctx.quadraticCurveTo(0, 22 + (p.smile ? -5 : 3), 10, 22); ctx.stroke(); }
      else { ctx.beginPath(); ctx.ellipse(0, 24, 8, 4 + 9 * mo, 0, 0, TAU); ctx.fill(); ctx.stroke(); }
    } else {
      // silhouette rim light
      if (p.rim) { ctx.strokeStyle = p.rim; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.arc(0, 0, 39, Math.PI * 0.9, Math.PI * 1.7); ctx.stroke(); }
    }
    ctx.restore();
    ctx.restore();
    return { handL, handR };
  }

  // ============================ SCENES ============================
  // Each scene: draw(t, f) with t absolute seconds. Camera handled inside.
  const SC = [];
  function scene(t0, t1, draw) { SC.push({ t0, t1, draw }); }

  // ---- S1: Prologue + hollow good life (0–50) : rainy grey suburb, parallax ----
  scene(0, 50, (t, f) => {
    const p = (t) / 50;
    // sky
    const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#5b6472'); g.addColorStop(1, '#8b93a0'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    const camx = -lerp(0, 420, smooth(clamp((t - 4) / 44)));
    // far hills
    ctx.save(); ctx.translate(camx * 0.2, 0); ctx.fillStyle = '#6b7280';
    smoothPoly(ctx, [[-100, 470], [300, 430], [700, 460], [1100, 425], [1500, 460], [1500, 720], [-100, 720]]); ctx.fill(); ctx.restore();
    // mid: houses + church
    ctx.save(); ctx.translate(camx * 0.6, 0);
    for (let i = 0; i < 8; i++) { const x = 120 + i * 260; const hh = 150 + hash(i) * 60; ctx.fillStyle = i === 3 ? '#7a6f66' : ['#8a7d72', '#7f8a86', '#94867a'][i % 3]; poly(ctx, [[x, 560], [x, 560 - hh], [x + 90, 560 - hh - 34], [x + 180, 560 - hh], [x + 180, 560]]); ctx.fill(); for (let w = 0; w < 3; w++) fillShape(ctx, [[x + 24 + w * 52, 560 - hh + 30], [x + 24 + w * 52 + 30, 560 - hh + 30], [x + 24 + w * 52 + 30, 560 - hh + 70], [x + 24 + w * 52, 560 - hh + 70]], '#cdd6de', '#3a3f47', 2, false); }
    // church steeple with cross (irony)
    const cx = 900; ctx.fillStyle = '#6d6258'; poly(ctx, [[cx, 560], [cx, 300], [cx + 45, 250], [cx + 90, 300], [cx + 90, 560]]); ctx.fill(); ctx.strokeStyle = '#efe7d0'; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(cx + 45, 250); ctx.lineTo(cx + 45, 210); ctx.moveTo(cx + 28, 226); ctx.lineTo(cx + 62, 226); ctx.stroke();
    ctx.restore();
    // foreground: Charlie walking with umbrella, cel
    const wx = W * 0.5 + Math.sin(t * 2) * 0, wy = 600 + Math.sin(t * 4) * 3;
    const cyc = t * 3.4; const step = 0.5 * Math.sin(cyc);
    charlie(ctx, { x: wx, y: wy, s: 1.0, lean: 0.02 * Math.sin(cyc), head: -0.05, mouth: f.v * 0.7, eye: 1, brow: 0.2, smile: p < 0.6, armL: [Math.PI / 2 + 0.5, -0.7], armR: [Math.PI / 2 - 0.5 + step, 0.5], legL: [Math.PI / 2 + step, -0.3 - 0.2 * Math.max(0, Math.sin(cyc))], legR: [Math.PI / 2 - step, -0.3 - 0.2 * Math.max(0, -Math.sin(cyc))] });
    // umbrella
    ctx.save(); ctx.translate(wx - 34, wy - 250); ctx.fillStyle = '#2a2f39'; ctx.beginPath(); ctx.arc(0, 0, 70, Math.PI, 0); ctx.closePath(); ctx.fill(); ctx.strokeStyle = '#141018'; ctx.lineWidth = 3; ctx.stroke(); ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, 60); ctx.stroke(); ctx.restore();
    stepRain(f); drawRain(ctx, 0.5);
    grade(ctx, 60, 80, 120, 0.28, 'multiply'); vignette(ctx, 0.5); letterbox(ctx, 1);
    if (t > 2 && t < 10) titleCard(ctx, t);
  });

  // ---- S2: Ascent to gate of light (50–57.5) ----
  scene(50, 57.5, (t, f) => {
    const p = clamp((t - 50) / 7.5);
    ctx.fillStyle = '#eae0c4'; ctx.fillRect(0, 0, W, H);
    const g = ctx.createRadialGradient(W / 2, -100, 50, W / 2, -100, 900); g.addColorStop(0, '#fffef2'); g.addColorStop(1, '#e7cf92'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    godRays(ctx, W / 2, -60, 1100, 40, '255,250,220', 0.5 + 0.3 * Math.sin(t * 2), 0, TAU);
    // clouds rising (parallax down)
    for (let i = 0; i < 6; i++) { const cy = ((i * 160 + p * 500) % (H + 200)) - 100; const cx = 150 + hash(i) * 900; ctx.fillStyle = 'rgba(255,255,255,0.8)'; ellipse(ctx, cx, cy, 130, 46, 0, null); ctx.fill(); ellipse(ctx, cx + 70, cy + 12, 90, 36, 0, 'rgba(255,255,255,0.7)', null); ctx.fill(); }
    // escalator implied by light steps; Charlie rising small -> bigger, hopeful looking up
    const cs = lerp(0.7, 1.05, p), cyy = lerp(560, 470, smooth(p));
    charlie(ctx, { x: W / 2, y: cyy, s: cs, head: -0.25, brow: 0.4, eye: 1, mouth: f.v * 0.6, smile: true, armL: [Math.PI / 2 - 0.6, -0.4], armR: [Math.PI / 2 + 0.6, 0.4], legL: [Math.PI / 2 + 0.05, -0.1], legR: [Math.PI / 2 - 0.05, -0.1] });
    flash(ctx, easeIn(clamp((t - 56.6) / 0.9)) * 0.9); // whiteout into next
    vignette(ctx, 0.25); letterbox(ctx, 1);
  });

  // ---- S3: The list — angel gate, rejection (57.5–70.7) ----
  scene(57.5, 70.7, (t, f) => {
    const p = clamp((t - 57.5) / 13.2);
    const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#f3ecd6'); g.addColorStop(1, '#cdb589'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    godRays(ctx, W * 0.5, -40, 900, 30, '255,248,210', 0.4, 0, TAU);
    gate(ctx, W * 0.5, 250, 1.15, '#efe6cc', ['#fffdf2', '#f0dca6']);
    // towering angel gatekeeper silhouette with ledger
    const ax = W * 0.34;
    charlie(ctx, { x: ax, y: 470, s: 1.5, silh: true, silhCol: '#b9a473', rim: '#fffbe6', head: 0.06, armL: [Math.PI / 2 - 0.7, -0.5], armR: [Math.PI / 2 - 1.0, 0.3] });
    // wings hint
    ctx.save(); ctx.globalAlpha = 0.8; ctx.fillStyle = '#e9dcb4'; smoothPoly(ctx, [[ax - 40, 300], [ax - 180, 250], [ax - 120, 360], [ax - 190, 420], [ax - 60, 400]]); ctx.fill(); ctx.restore();
    // ledger / list
    ctx.save(); ctx.translate(ax + 70, 400); ctx.rotate(-0.15); ctx.fillStyle = '#efe7cf'; fillShape(ctx, [[0, 0], [120, -14], [130, 90], [10, 104]], '#efe7cf', '#3a3020', 3, false); ctx.strokeStyle = '#3a3020'; ctx.lineWidth = 2; for (let i = 0; i < 6; i++) { ctx.beginPath(); ctx.moveTo(14, 12 + i * 14); ctx.lineTo(116, 12 + i * 14 - 6); ctx.stroke(); } if (p > 0.5) { ctx.strokeStyle = '#a01818'; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(20, 40); ctx.lineTo(110, 30); ctx.moveTo(24, 30); ctx.lineTo(106, 44); ctx.stroke(); } ctx.restore();
    // Charlie small, hopeful -> horror
    const horror = clamp((t - 64) / 3);
    charlie(ctx, { x: W * 0.72, y: 560, s: 0.95, head: lerp(-0.1, 0.15, horror), brow: lerp(0.4, -0.8, horror), eye: 1, look: 0, mouth: lerp(0.1, 0.9, horror * f.v + horror * 0.4), armL: [Math.PI / 2 - 0.2 - horror * 0.5, -0.3], armR: [Math.PI / 2 + 0.2 + horror * 0.3, 0.3] });
    if (horror > 0.5) speedLines(ctx, W * 0.72, 420, (horror - 0.5) * 2 * (0.5 + f.beat), '40,30,30', 0.25);
    grade(ctx, 90, 70, 60, 0.15, 'multiply'); vignette(ctx, 0.4); letterbox(ctx, 1);
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
    charlie(ctx, { x: W / 2 + Math.sin(t * 0.9) * 40, y: 430 + Math.sin(t * 1.5) * 20, s: 1.0, lean: tumble, head: -0.3, brow: -0.7, eye: 1, mouth: clamp(0.3 + f.v), armL: [Math.PI * 1.5 - 0.3, -0.2 - reach * 0.2], armR: [Math.PI * 1.5 + 0.3, 0.2 + reach * 0.2], legL: [Math.PI / 2 + 0.4, 0.4], legR: [Math.PI / 2 - 0.5, -0.4] });
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
    charlie(ctx, { x: W * 0.62, y: 615, s: 1.0, head: 0.1, brow: -0.7, eye: 1, mouth: clamp(0.3 + f.v), armL: [Math.PI / 2 - 1.2, -0.4], armR: [Math.PI / 2 + 1.2, 0.4], legL: [Math.PI / 2 + 0.1, -0.1], legR: [Math.PI / 2 - 0.1, -0.1] });
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
    charlie(ctx, { x: W * 0.72, y: 560 + down * 40, s: 0.95, lean: down * 0.5, head: 0.2, brow: -0.9, eye: 1 - down * 0.5, mouth: clamp(0.4 + f.v), armL: [Math.PI / 2 - 0.9 - down, -0.3], armR: [Math.PI / 2 + 0.9 + down, 0.3] });
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
    charlie(ctx, { x: W / 2 + Math.sin(t * 0.9) * 46, y: 430 + Math.sin(t * 1.6) * 22, s: 1.0, lean: Math.sin(t * 1.1) * 0.14, head: -0.2, brow: -0.8, eye: 1, mouth: clamp(0.3 + f.v), armL: [Math.PI * 1.5 - 0.3, -0.3], armR: [Math.PI * 1.5 + 0.3, 0.3], legL: [Math.PI / 2 + 0.5, 0.4], legR: [Math.PI / 2 - 0.6, -0.4] });
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
    const cv = document.getElementById('c'); cv.width = W; cv.height = H; ctx = cv.getContext('2d'); pools = {}; _pn = 0;
  }
  function renderFrame(i) {
    const t = i / FPS; const f = F(i);
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
