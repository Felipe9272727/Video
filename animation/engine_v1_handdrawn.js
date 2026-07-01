/* Charlie's Inferno — hand-drawn devil engine.
 * Deterministic per-frame rendering driven by build/timeline.json.
 * Aesthetic goals: boiling ink lines, paper/film grain, limited (~12fps) boil
 * cadence, squash & stretch, beat-reactive flames + a singing devil.
 * No clean geometric primitives are used directly — everything is wobbled.
 */
(function (global) {
  const W = 1280, H = 720;
  const HOLD = 2;            // redraw line-boil every 2 video frames -> ~12fps boil
  const TAU = Math.PI * 2;

  // ---- palette ----
  const INK = '#241308';
  const RED = '#d23b2e';
  const RED_D = '#9c2a1f';
  const RED_L = '#ec6a4e';
  const BELLY2 = '#eec19a';
  const HORN = '#e9d7b0';
  const HORN_D = '#c2a878';
  const PRONG = '#cda96b';
  const STAFF = '#5a4327';

  // ---- deterministic RNG ----
  function mulberry32(a) {
    return function () {
      a |= 0; a = a + 0x6D2B79F5 | 0;
      let t = Math.imul(a ^ a >>> 15, 1 | a);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }
  function hash01(n) { // stable per-integer noise
    let t = (n * 2654435761) >>> 0;
    t ^= t >>> 15; t = Math.imul(t, 2246822519); t ^= t >>> 13;
    t = Math.imul(t, 3266489917); t ^= t >>> 16;
    return (t >>> 0) / 4294967296;
  }

  // boil rng — reseeded each held-frame so lines "boil"
  let BR = mulberry32(1);
  function jit(s) { return (BR() * 2 - 1) * s; }

  // ---- rough drawing primitives ----
  function smoothClosed(ctx, pts) {
    const n = pts.length;
    ctx.beginPath();
    const m0x = (pts[0][0] + pts[n - 1][0]) / 2, m0y = (pts[0][1] + pts[n - 1][1]) / 2;
    ctx.moveTo(m0x, m0y);
    for (let i = 0; i < n; i++) {
      const p = pts[i], q = pts[(i + 1) % n];
      const mx = (p[0] + q[0]) / 2, my = (p[1] + q[1]) / 2;
      ctx.quadraticCurveTo(p[0], p[1], mx, my);
    }
    ctx.closePath();
  }
  function smoothOpen(ctx, pts) {
    const n = pts.length;
    ctx.beginPath();
    ctx.moveTo(pts[0][0], pts[0][1]);
    for (let i = 0; i < n - 1; i++) {
      const p = pts[i], q = pts[i + 1];
      const mx = (p[0] + q[0]) / 2, my = (p[1] + q[1]) / 2;
      ctx.quadraticCurveTo(p[0], p[1], mx, my);
    }
    ctx.lineTo(pts[n - 1][0], pts[n - 1][1]);
  }
  function jitterPts(pts, wob, sub) {
    // optionally insert a jittered midpoint between control points so the
    // tremor frequency is higher -> reads as a shaky hand-drawn line, not vector
    let src = pts;
    if (sub) {
      src = [];
      for (let i = 0; i < pts.length; i++) {
        const p = pts[i], q = pts[(i + 1) % pts.length];
        src.push(p);
        src.push([(p[0] + q[0]) / 2 + jit(wob * 0.8), (p[1] + q[1]) / 2 + jit(wob * 0.8)]);
      }
    }
    const o = [];
    for (let i = 0; i < src.length; i++) o.push([src[i][0] + jit(wob), src[i][1] + jit(wob)]);
    return o;
  }
  // rough pen hatching inside a shape, for hand-drawn shading
  function hatch(ctx, pts, ang, gap, col, alpha) {
    let minx = 1e9, miny = 1e9, maxx = -1e9, maxy = -1e9;
    for (const p of pts) { minx = Math.min(minx, p[0]); miny = Math.min(miny, p[1]); maxx = Math.max(maxx, p[0]); maxy = Math.max(maxy, p[1]); }
    ctx.save();
    smoothClosed(ctx, jitterPts(pts, 1.2)); ctx.clip();
    ctx.globalAlpha = alpha; ctx.strokeStyle = col; ctx.lineCap = 'round';
    const dx = Math.cos(ang), dy = Math.sin(ang), L = (maxx - minx) + (maxy - miny);
    for (let s = -L; s < L; s += gap) {
      const ox = minx + s, oy = miny;
      ctx.beginPath();
      ctx.moveTo(ox + jit(1.5), oy + jit(1.5));
      ctx.quadraticCurveTo(ox + dx * L * 0.5 + jit(3), oy + dy * L * 0.5 + jit(3), ox + dx * L, oy + dy * L);
      ctx.lineWidth = 1.6 * (0.7 + 0.6 * BR()); ctx.stroke();
    }
    ctx.restore(); ctx.globalAlpha = 1;
  }
  // filled organic blob with a sketchy double-stroke outline
  function blob(ctx, pts, { fill, stroke = INK, w = 3, wob = 2.7, alpha = 1, strokeAlpha = 1 }) {
    if (fill) {
      ctx.globalAlpha = alpha;
      smoothClosed(ctx, jitterPts(pts, wob * 0.6));
      ctx.fillStyle = fill; ctx.fill();
    }
    if (stroke) {
      ctx.globalAlpha = strokeAlpha;
      ctx.strokeStyle = stroke; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
      for (let p = 0; p < 2; p++) {
        smoothClosed(ctx, jitterPts(pts, wob, true));
        ctx.lineWidth = w * (0.65 + 0.5 * BR());
        ctx.stroke();
      }
    }
    ctx.globalAlpha = 1;
  }
  function inkLine(ctx, x1, y1, x2, y2, { w = 3, wob = 1.8, col = INK, alpha = 1, bow = 0 }) {
    ctx.globalAlpha = alpha; ctx.strokeStyle = col; ctx.lineCap = 'round';
    const nx = -(y2 - y1), ny = (x2 - x1); const L = Math.hypot(nx, ny) || 1;
    for (let p = 0; p < 2; p++) {
      const ax = x1 + jit(wob), ay = y1 + jit(wob), bx = x2 + jit(wob), by = y2 + jit(wob);
      const b = bow + jit(wob * 1.2);
      const mx = (x1 + x2) / 2 + nx / L * b, my = (y1 + y2) / 2 + ny / L * b;
      ctx.beginPath(); ctx.moveTo(ax, ay); ctx.quadraticCurveTo(mx, my, bx, by);
      ctx.lineWidth = w * (0.8 + 0.35 * BR()); ctx.stroke();
    }
    ctx.globalAlpha = 1;
  }
  function inkPath(ctx, pts, { w = 3, wob = 1.6, col = INK, alpha = 1 }) {
    ctx.globalAlpha = alpha; ctx.strokeStyle = col; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    for (let p = 0; p < 2; p++) {
      smoothOpen(ctx, jitterPts(pts, wob));
      ctx.lineWidth = w * (0.8 + 0.35 * BR()); ctx.stroke();
    }
    ctx.globalAlpha = 1;
  }

  // ---- ember / spark particle pool (smooth, per-frame stepping) ----
  let embers = [];
  function stepEmbers(f, t) {
    // spawn rate from highs + onsets
    const rate = 0.6 + 5 * f.h + 9 * f.onset;
    let spawn = rate; // expected per frame
    while (spawn > 0) {
      if (spawn < 1 && BR() > spawn) break;
      spawn -= 1;
      const x = W * (0.08 + 0.84 * hash01(embers.length * 7 + (t * 1000 | 0)));
      embers.push({
        x, y: H * (0.78 + 0.18 * BR()),
        vx: jit(0.4), vy: -(0.6 + 1.8 * BR()) - 1.5 * f.b,
        life: 0, max: 40 + 70 * BR(), r: 1 + 2.4 * BR(), seed: BR() * 1000,
      });
    }
    for (const e of embers) {
      e.life++; e.x += e.vx + Math.sin((e.life + e.seed) * 0.15) * 0.5; e.y += e.vy; e.vy *= 0.992;
    }
    embers = embers.filter(e => e.life < e.max && e.y > -20);
    if (embers.length > 320) embers.splice(0, embers.length - 320);
  }
  function drawEmbers(ctx) {
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    for (const e of embers) {
      const k = 1 - e.life / e.max;
      const r = e.r * (0.6 + 0.6 * k);
      const g = ctx.createRadialGradient(e.x, e.y, 0, e.x, e.y, r * 4);
      g.addColorStop(0, `rgba(255,225,150,${0.9 * k})`);
      g.addColorStop(0.4, `rgba(255,140,40,${0.5 * k})`);
      g.addColorStop(1, 'rgba(255,80,0,0)');
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(e.x, e.y, r * 4, 0, TAU); ctx.fill();
    }
    ctx.restore();
  }

  // ---- flames ----
  // One organic, asymmetric licking tongue (rough edges, curling tip).
  function tongue(ctx, x, baseY, w, h, t, seed, alpha, fill) {
    const r = mulberry32(seed >>> 0 || 1);
    const curl = (r() * 2 - 1);                       // tip leans left/right
    const flick = Math.sin(t * (4 + r() * 4) + seed) * 0.5 + 0.5;
    h *= 0.8 + 0.5 * flick + 0.3 * r();
    const segs = 7;
    const left = [], right = [];
    for (let s = 0; s <= segs; s++) {
      const u = s / segs;                             // 0 base -> 1 tip
      const y = baseY - h * u;
      const lean = curl * w * 0.55 * u * u + Math.sin(u * 5 + seed) * w * 0.10 * (1 - u);
      const half = w * 0.5 * Math.pow(1 - u, 1.25) * (0.7 + 0.5 * Math.sin(u * 9 + seed * 2));
      left.push([x + lean - half + jit(w * 0.04), y]);
      right.push([x + lean + half + jit(w * 0.04), y]);
    }
    const tipx = left[segs][0] + curl * w * 0.25;
    const pts = left.slice(0, segs).concat([[tipx, baseY - h]], right.slice(0, segs).reverse());
    const g = ctx.createLinearGradient(0, baseY, 0, baseY - h);
    g.addColorStop(0, `rgba(150,22,14,${alpha})`);
    g.addColorStop(0.4, `rgba(${fill[0]},${fill[1]},${fill[2]},${alpha})`);
    g.addColorStop(0.82, `rgba(255,150,30,${alpha})`);
    g.addColorStop(1, `rgba(255,228,110,${alpha * 0.9})`);
    smoothClosed(ctx, jitterPts(pts, w * 0.02, true)); ctx.fillStyle = g; ctx.fill();
  }
  // a flame body = a few overlapping tongues -> irregular, hand-drawn fire
  function drawFlame(ctx, x, baseY, w, h, t, seed, alpha) {
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    tongue(ctx, x, baseY, w, h, t, seed, alpha, [255, 86, 28]);
    const r = mulberry32((seed * 7 + 3) >>> 0 || 1);
    const nT = 1 + (r() * 3 | 0);
    for (let k = 0; k < nT; k++) {
      const ox = (r() * 2 - 1) * w * 0.32, sw = w * (0.35 + 0.4 * r()), sh = h * (0.5 + 0.45 * r());
      tongue(ctx, x + ox, baseY, sw, sh, t, seed * 13 + k * 91, alpha * 0.95, [255, 110, 36]);
    }
    // bright inner core
    tongue(ctx, x + jit(w * 0.04), baseY, w * 0.42, h * 0.6, t, seed * 5 + 1, alpha * 0.8, [255, 205, 70]);
    ctx.restore();
  }

  // ---- the devil ----
  function drawDevil(ctx, f, t, i) {
    const beat = f.beat, E = f.e, V = f.v;
    const bob = Math.sin(f.phase * TAU);
    const breathe = Math.sin(t * 1.6) * 0.5 + 0.5;

    // anchor at feet
    const footY = H * 0.70;
    const cx = W * 0.5 + Math.sin(t * 0.7) * 10;
    const lift = 10 + 16 * (0.5 + 0.5 * bob) + 26 * beat;     // hops on the beat
    const s = (1 + 0.05 * E + 0.10 * beat) * 0.92;            // overall scale
    const sx = 1 + 0.12 * beat;                               // squash & stretch
    const sy = 1 - 0.10 * beat + 0.03 * breathe;
    const lean = Math.sin(t * 0.9) * 0.03 + bob * 0.02;

    ctx.save();
    ctx.translate(cx, footY - lift);
    ctx.rotate(lean);
    ctx.scale(s * sx, s * sy);

    // ----- TAIL (behind) -----
    const tw = Math.sin(t * 3 + 1) * 26 + 30 * beat;
    const tailPts = [
      [18, -150], [55, -120], [80, -95 + tw * 0.3], [95, -55 + tw * 0.6], [86, -18 + tw]
    ];
    inkPath(ctx, tailPts, { w: 9, col: RED_D, wob: 2.2 });
    inkPath(ctx, tailPts, { w: 5, col: RED, wob: 2.2 });
    // arrow tip
    const tip = tailPts[tailPts.length - 1];
    blob(ctx, [[tip[0] + 18, tip[1] - 12], [tip[0] + 30, tip[1] + 2], [tip[0] + 14, tip[1] + 16],
    [tip[0] + 8, tip[1] + 2]], { fill: RED, w: 3, wob: 1.6 });

    // ----- LEGS -----
    for (const dx of [-32, 32]) {
      inkLine(ctx, dx * 0.7, -120, dx, -34, { w: 14, col: RED, wob: 2 });
      blob(ctx, [[dx - 16, -34], [dx + 18, -40], [dx + 24, -16], [dx - 14, -12]],
        { fill: RED_D, w: 3, wob: 1.6 }); // hoof/foot
    }

    // ----- BODY -----
    const body = [
      [0, -250], [62, -232], [82, -185], [70, -120], [40, -86],
      [0, -78], [-40, -86], [-70, -120], [-82, -185], [-62, -232]
    ];
    blob(ctx, body, { fill: RED, w: 4.5, wob: 3.4 });
    // belly patch
    blob(ctx, [[0, -210], [34, -195], [40, -150], [22, -108], [0, -100],
    [-22, -108], [-40, -150], [-34, -195]], { fill: BELLY2, w: 0, wob: 1.8, alpha: 0.9, stroke: null });
    // body shading (right side) — pen hatching
    hatch(ctx, [[24, -238], [66, -218], [80, -176], [64, -118], [40, -96], [34, -150]], -0.95, 7, '#6e1810', 0.5);

    // ----- ARMS + TRIDENT -----
    const pump = 0.5 + 0.5 * Math.sin(f.phase * TAU) + 1.4 * beat; // raise on beat
    // left arm gesture
    const la = [[-66, -210], [-104, -190 - 20 * pump], [-128, -150 - 40 * pump]];
    inkPath(ctx, la, { w: 12, col: RED, wob: 2 });
    blob(ctx, [[la[2][0] - 10, la[2][1] - 10], [la[2][0] + 8, la[2][1] - 8],
    [la[2][0] + 6, la[2][1] + 12], [la[2][0] - 12, la[2][1] + 8]], { fill: RED_L, w: 2.5, wob: 1.4 });
    // right arm holds trident, pumps up on beat
    const ry = -150 - 60 * pump;
    const ra = [[66, -210], [108, -200], [132, ry]];
    inkPath(ctx, ra, { w: 12, col: RED, wob: 2 });
    drawTrident(ctx, 132, ry, f, t);

    // ----- HEAD -----
    ctx.save();
    const headY = -250;
    const nod = Math.sin(f.phase * TAU) * 0.05 + beat * 0.04;
    ctx.translate(0, headY); ctx.rotate(nod);
    drawHead(ctx, f, t, i);
    ctx.restore();

    ctx.restore();
  }

  function drawTrident(ctx, x, y, f, t) {
    const ang = -0.2 + Math.sin(t * 0.8) * 0.05;
    ctx.save(); ctx.translate(x, y); ctx.rotate(ang);
    inkLine(ctx, 0, 10, 0, -150, { w: 7, col: STAFF, wob: 1.6 });
    // three prongs
    inkLine(ctx, 0, -150, 0, -210, { w: 6, col: PRONG, wob: 1.4 });
    inkLine(ctx, 0, -150, -22, -205, { w: 6, col: PRONG, wob: 1.4 });
    inkLine(ctx, 0, -150, 22, -205, { w: 6, col: PRONG, wob: 1.4 });
    inkLine(ctx, -22, -178, -22, -205, { w: 6, col: PRONG, wob: 1.4 });
    inkLine(ctx, 22, -178, 22, -205, { w: 6, col: PRONG, wob: 1.4 });
    inkLine(ctx, -22, -178, 22, -178, { w: 6, col: PRONG, wob: 1.4 });
    // glowing tips on beat
    const glow = 0.3 + 1.0 * f.beat + 0.5 * f.onset;
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    for (const px of [-22, 0, 22]) {
      const g = ctx.createRadialGradient(px, -205, 0, px, -205, 26 * glow);
      g.addColorStop(0, `rgba(255,235,160,${0.9 * Math.min(1, glow)})`);
      g.addColorStop(1, 'rgba(255,120,20,0)');
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(px, -205, 26 * glow, 0, TAU); ctx.fill();
    }
    ctx.restore();
    ctx.restore();
  }

  function drawHead(ctx, f, t, i) {
    const V = f.v, beat = f.beat;
    // ----- HORNS -----
    for (const dir of [-1, 1]) {
      const hx = dir * 58, hy = -64;
      const horn = [
        [dir * 40, -50], [dir * 58, -70], [hx + dir * 8, -118], [hx + dir * 2, -150]
      ];
      inkPath(ctx, horn, { w: 16, col: HORN_D, wob: 1.8 });
      inkPath(ctx, horn, { w: 9, col: HORN, wob: 1.8 });
    }
    // ----- EARS -----
    for (const dir of [-1, 1]) {
      blob(ctx, [[dir * 86, -30], [dir * 120, -44], [dir * 104, 6], [dir * 78, 0]],
        { fill: RED, w: 3, wob: 1.8 });
    }
    // ----- FACE -----
    const face = [
      [0, -86], [70, -64], [88, -8], [70, 52], [30, 84],
      [0, 90], [-30, 84], [-70, 52], [-88, -8], [-70, -64]
    ];
    blob(ctx, face, { fill: RED, w: 5, wob: 3.6 });
    // cheek shade — light hatching
    hatch(ctx, [[34, 8], [70, 30], [56, 70], [22, 64]], -0.95, 8, '#6e1810', 0.38);

    // ----- EYEBROWS (devilish, expressive) -----
    const brow = -0.18 - 0.5 * beat; // raise on accents
    for (const dir of [-1, 1]) {
      const bx = dir * 30, by = -34 + brow * 14;
      inkLine(ctx, bx - dir * 22, by - 6, bx + dir * 18, by + 10, { w: 6, wob: 1.4 });
    }
    // ----- EYES -----
    const blink = blinkAt(i);
    for (const dir of [-1, 1]) {
      const ex = dir * 30, ey = -10;
      if (blink > 0.5) { inkLine(ctx, ex - 18, ey, ex + 18, ey, { w: 4, wob: 1.2 }); continue; }
      blob(ctx, [[ex - 20, ey - 14], [ex + 20, ey - 14], [ex + 22, ey + 10], [ex - 22, ey + 10]],
        { fill: '#fbf3e0', w: 3, wob: 1.4 });
      // pupil darts on onsets
      const look = Math.sin(t * 0.6 + dir) * 5 + f.onset * 6;
      ctx.fillStyle = INK;
      ctx.beginPath(); ctx.arc(ex + look + jit(0.6), ey + 1 + jit(0.6), 7.5, 0, TAU); ctx.fill();
      ctx.fillStyle = '#fff';
      ctx.beginPath(); ctx.arc(ex + look - 2, ey - 2, 2.4, 0, TAU); ctx.fill();
    }
    // ----- NOSE -----
    inkLine(ctx, -4, 14, 6, 22, { w: 4, col: RED_D, wob: 1 });

    // ----- MOUTH (sings with the vocal band) -----
    const open = Math.max(0, Math.min(1, (V - 0.18) * 1.5));
    const my = 44;
    if (open < 0.12) {
      // grin
      inkPath(ctx, [[-34, my], [-12, my + 10], [12, my + 10], [34, my]], { w: 5, wob: 1.5 });
      inkLine(ctx, -18, my + 6, -16, my + 12, { w: 3, wob: 1 });
      inkLine(ctx, 16, my + 6, 18, my + 12, { w: 3, wob: 1 });
    } else {
      const mw = 30 + 10 * open, mh = 8 + 34 * open;
      blob(ctx, [[-mw, my - 2], [-mw * 0.4, my - mh * 0.4], [mw * 0.4, my - mh * 0.4], [mw, my - 2],
      [mw * 0.5, my + mh], [-mw * 0.5, my + mh]], { fill: '#3a0d0a', w: 4, wob: 1.6 });
      // tongue
      blob(ctx, [[-mw * 0.4, my + mh * 0.3], [mw * 0.4, my + mh * 0.3], [mw * 0.3, my + mh],
      [-mw * 0.3, my + mh]], { fill: '#c34', w: 0, stroke: null, alpha: 0.9 });
      // upper teeth
      ctx.fillStyle = '#f7eed8';
      ctx.beginPath(); ctx.moveTo(-mw * 0.7, my - 2);
      ctx.lineTo(mw * 0.7, my - 2); ctx.lineTo(mw * 0.55, my + 5); ctx.lineTo(-mw * 0.55, my + 5);
      ctx.closePath(); ctx.fill();
    }
    // little goatee — the "handsome devil"
    inkPath(ctx, [[-12, my + 18], [0, my + 40 + 8 * open], [12, my + 18]], { w: 5, col: INK, wob: 1.6 });
  }

  // blink schedule (deterministic)
  let blinkFrames = [];
  function buildBlinks(n, fps) {
    const r = mulberry32(99);
    let t = 1.0;
    while (t < n / fps) { t += 1.6 + r() * 3.4; blinkFrames.push(Math.round(t * fps)); }
  }
  function blinkAt(i) {
    for (const bf of blinkFrames) { if (i >= bf && i < bf + 5) return 1; }
    return 0;
  }

  // ---- grain texture (built once) ----
  let grain = null;
  function buildGrain() {
    grain = document.createElement('canvas'); grain.width = 256; grain.height = 256;
    const g = grain.getContext('2d'); const id = g.createImageData(256, 256);
    for (let k = 0; k < id.data.length; k += 4) {
      const v = 120 + Math.random() * 135 | 0;
      id.data[k] = id.data[k + 1] = id.data[k + 2] = v; id.data[k + 3] = 255;
    }
    g.putImageData(id, 0, 0);
  }

  // ---- background ----
  function drawBackground(ctx, f, t) {
    const E = f.e, B = f.b;
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, `rgb(${28 + 20 * E | 0},${8},${8})`);
    g.addColorStop(0.5, `rgb(${92 + 40 * E | 0},${22 + 10 * E | 0},${12})`);
    g.addColorStop(1, `rgb(${178 + 50 * B | 0},${56 + 30 * B | 0},${22})`);
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    // horizon glow behind devil
    const gy = H * 0.7;
    const rg = ctx.createRadialGradient(W / 2, gy, 0, W / 2, gy, 520 * (0.7 + 0.5 * B));
    rg.addColorStop(0, `rgba(255,150,40,${0.35 + 0.4 * B})`);
    rg.addColorStop(1, 'rgba(255,80,0,0)');
    ctx.fillStyle = rg; ctx.fillRect(0, 0, W, H);
    // jagged hell ridge
    ctx.fillStyle = 'rgba(40,8,6,0.9)';
    const ridge = [[-20, H * 0.78]];
    for (let x = 0; x <= W + 20; x += 80) {
      ridge.push([x, H * 0.74 + Math.sin(x * 0.05) * 18 + hash01(x) * 26]);
    }
    ridge.push([W + 20, H]); ridge.push([-20, H]);
    smoothClosed(ctx, ridge); ctx.fill();
  }

  // ---- per-frame entry ----
  let TL = null, FPS = 24, ctx = null;
  function init(timeline) {
    TL = timeline; FPS = timeline.fps;
    const cv = document.getElementById('c'); cv.width = W; cv.height = H;
    ctx = cv.getContext('2d');
    buildGrain(); buildBlinks(timeline.count, FPS); embers = [];
  }

  function renderFrame(i) {
    const f = TL.frames[Math.max(0, Math.min(TL.count - 1, i))];
    const t = i / FPS;
    BR = mulberry32(((i / HOLD) | 0) * 2654435761 >>> 0 || 1);

    // intro/outro fades + camera
    const fadeIn = Math.min(1, t / 1.4);
    const fadeOut = Math.min(1, (TL.duration - t) / 1.6);
    const camx = Math.sin(t * 0.5) * 8 + jit(2.5 * f.beat + 0.6);
    const camy = Math.cos(t * 0.43) * 6 + jit(2.5 * f.beat + 0.6);

    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, W, H);
    ctx.save();
    ctx.translate(camx, camy);
    ctx.scale(1.02, 1.02); // overscan to hide camera shake edges
    ctx.translate(-W * 0.01, -H * 0.01);

    drawBackground(ctx, f, t);

    // wall of fire — irregular, layered (no grid)
    const lvl = 0.5 + 0.7 * f.b + 0.4 * f.e;
    for (let k = 0; k < 24; k++) { // dim back layer
      const x = (hash01(k * 37 + 1) * 1.06 - 0.03) * W;
      const w = 80 + 120 * hash01(k * 7 + 2);
      const hgt = (60 + 150 * lvl) * (0.5 + 0.8 * hash01(k * 13 + 3));
      drawFlame(ctx, x, H * 0.83 + hash01(k * 5) * 22, w, hgt, t, k * 9 + 1, 0.30);
    }
    for (let k = 0; k < 16; k++) { // brighter mid layer
      const x = (hash01(k * 53 + 9) * 1.06 - 0.03) * W;
      const w = 120 + 150 * hash01(k * 11 + 4);
      const hgt = (110 + 230 * lvl) * (0.6 + 0.7 * hash01(k * 17 + 5));
      drawFlame(ctx, x, H * 0.87 + hash01(k * 3) * 16, w, hgt, t, k * 23 + 5, 0.5);
    }

    stepEmbers(f, t);
    drawEmbers(ctx);

    drawDevil(ctx, f, t, i);

    // foreground fire the devil stands in (frames the shot)
    for (let k = 0; k < 7; k++) {
      const x = (k / 6) * W + jit(24);
      const w = 230 + 130 * hash01(k * 29 + 1);
      const hgt = (190 + 230 * f.b) * (0.7 + 0.5 * hash01(k * 31 + 2));
      drawFlame(ctx, x, H + 46, w, hgt, t, k * 41 + 7, 0.85);
    }

    ctx.restore();

    // grain
    ctx.save(); ctx.globalAlpha = 0.06; ctx.globalCompositeOperation = 'overlay';
    const gx = (jit(120)) | 0, gy = (jit(120)) | 0;
    for (let yy = -256; yy < H; yy += 256) for (let xx = -256; xx < W; xx += 256)
      ctx.drawImage(grain, xx + gx, yy + gy);
    ctx.restore();

    // vignette
    const vg = ctx.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 0.85);
    vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,0.55)');
    ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);

    // title card
    if (t < 6) drawTitle(ctx, t);

    // fades
    const fade = Math.min(fadeIn, fadeOut);
    if (fade < 1) { ctx.fillStyle = `rgba(0,0,0,${1 - fade})`; ctx.fillRect(0, 0, W, H); }
  }

  function drawTitle(ctx, t) {
    const a = t < 1 ? t : (t > 5 ? Math.max(0, (6 - t)) : 1);
    ctx.save(); ctx.globalAlpha = a;
    ctx.translate(W / 2 + jit(2), H * 0.30 + jit(2));
    ctx.textAlign = 'center'; ctx.fillStyle = '#f7e4b0';
    ctx.font = "italic 700 70px Georgia, 'Times New Roman', serif";
    ctx.strokeStyle = INK; ctx.lineWidth = 5; ctx.lineJoin = 'round';
    ctx.rotate(jit(0.01));
    ctx.strokeText("Charlie's Inferno", 0, 0);
    ctx.fillText("Charlie's Inferno", 0, 0);
    ctx.font = "italic 600 30px Georgia, serif"; ctx.fillStyle = '#e8b27a';
    ctx.strokeText('That Handsome Devil — cover PT-BR', 0, 48);
    ctx.fillText('That Handsome Devil — cover PT-BR', 0, 48);
    ctx.restore();
  }

  global.CharlieInferno = { init, renderFrame, W, H };
})(window);
