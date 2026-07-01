/* REAL 2D character, driven by a 3D skeleton underneath (mocap/three.js joints).
 * The 3D is only a rig: it gives natural motion + any angle. Everything drawn
 * here is flat 2D — but ORGANIC/DEFORMABLE (variable-width tapered strands and a
 * curvy torso), not rigid geometric primitives. This is the Spine/Live2D idea.
 *
 * fr: { hip:[x,y,z], chest, neck, head, lsh,lel,lwr, rsh,rel,rwr,
 *       lhip,lkn,lank, rhip,rkn,rank }   (hip at origin, ~unit tall)
 * o : { x, y, scale, faceDir, lookDir, emotion:{brow,mouth,smile,eye}, style, horns, glow }
 */
(function (global) {
  const TAU = Math.PI * 2;
  const V = (a, b) => [a[0] + b[0], a[1] + b[1]];
  const sub = (a, b) => [a[0] - b[0], a[1] - b[1]];
  const mul = (a, s) => [a[0] * s, a[1] * s];
  const lerp2 = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
  const norm = (a) => { const l = Math.hypot(a[0], a[1]) || 1; return [a[0] / l, a[1] / l]; };
  const perp = (a) => [-a[1], a[0]];

  // Catmull-Rom sample through control points -> dense polyline
  function cr(pts, seg) {
    if (pts.length < 3) { // straight
      const out = []; for (let i = 0; i <= seg; i++) out.push(lerp2(pts[0], pts[pts.length - 1], i / seg)); return out;
    }
    const P = [pts[0], ...pts, pts[pts.length - 1]]; const out = [];
    for (let i = 1; i < P.length - 2; i++) {
      const p0 = P[i - 1], p1 = P[i], p2 = P[i + 1], p3 = P[i + 2];
      for (let j = 0; j < seg; j++) {
        const t = j / seg, t2 = t * t, t3 = t2 * t;
        out.push([
          0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
          0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
        ]);
      }
    }
    out.push(pts[pts.length - 1]); return out;
  }

  // variable-width tapered "strand" along a centerline -> organic limb/neck
  function strand(ctx, pts, wRoot, wTip, fill, line, lw, capTip) {
    const C = cr(pts, 10); const n = C.length;
    const L = [], R = [];
    for (let i = 0; i < n; i++) {
      const a = C[Math.max(0, i - 1)], b = C[Math.min(n - 1, i + 1)];
      const nrm = perp(norm(sub(b, a)));
      const w = (wRoot + (wTip - wRoot) * (i / (n - 1))) * 0.5;
      L.push(V(C[i], mul(nrm, w))); R.push(V(C[i], mul(nrm, -w)));
    }
    ctx.beginPath(); ctx.moveTo(L[0][0], L[0][1]);
    for (let i = 1; i < n; i++) ctx.lineTo(L[i][0], L[i][1]);
    if (capTip) { const c = C[n - 1], w = wTip * 0.5; const ang = Math.atan2(L[n - 1][1] - c[1], L[n - 1][0] - c[0]); ctx.arc(c[0], c[1], w, ang, ang - Math.PI, true); }
    for (let i = n - 1; i >= 0; i--) ctx.lineTo(R[i][0], R[i][1]);
    const c0 = C[0], w0 = wRoot * 0.5; const ang0 = Math.atan2(R[0][1] - c0[1], R[0][0] - c0[0]); ctx.arc(c0[0], c0[1], w0, ang0, ang0 - Math.PI, true);
    ctx.closePath();
    if (fill) { ctx.fillStyle = fill; ctx.fill(); }
    if (line) { ctx.strokeStyle = line; ctx.lineWidth = lw; ctx.lineJoin = 'round'; ctx.stroke(); }
  }

  // smooth closed blob through control points (torso)
  function blob(ctx, pts, fill, line, lw) {
    const C = cr([...pts, pts[0], pts[1]], 12);
    ctx.beginPath(); ctx.moveTo(C[0][0], C[0][1]); for (let i = 1; i < C.length; i++) ctx.lineTo(C[i][0], C[i][1]); ctx.closePath();
    if (fill) { ctx.fillStyle = fill; ctx.fill(); }
    if (line) { ctx.strokeStyle = line; ctx.lineWidth = lw; ctx.lineJoin = 'round'; ctx.stroke(); }
  }

  function drawChar2D(ctx, fr, o) {
    const S = o.scale, X = o.x, Y = o.y; const em = o.emotion || {}; const st = o.style || {};
    const SKIN = st.skin || '#eab98f', SKIN_S = st.skinS || '#cd9268', HAIR = st.hair || '#3a2820',
      COAT = st.coat || '#3d5570', COAT_S = st.coatS || '#2b3d52', SHIRT = st.shirt || '#dfe3e9',
      TIE = st.tie || '#8f2b34', PANT = st.pant || '#2b303a', PANT_S = st.pantS || '#1e222b',
      SHOE = st.shoe || '#171009', LINE = st.line || '#15110d';
    const LW = Math.max(2.5, S * 0.02);
    const P = {}; for (const k in fr) P[k] = [X + fr[k][0] * S, Y + fr[k][1] * S, fr[k][2]];
    const B = (P.lsh[2] + P.lhip[2]) >= (P.rsh[2] + P.rhip[2]) ? 'l' : 'r';
    const Fs = B === 'l' ? 'r' : 'l';
    const uArm = S * 0.115, loArm = S * 0.09, thigh = S * 0.17, calf = S * 0.115;

    // ---- torso geometry (computed FIRST so arms attach at the coat's shoulder) ----
    const shMid = lerp2(P.lsh, P.rsh, 0.5), hipMid = lerp2(P.lhip, P.rhip, 0.5);
    const spineDir = norm(sub(shMid, hipMid)); const side = perp(spineDir);
    const shHalf = Math.hypot(P.rsh[0] - P.lsh[0], P.rsh[1] - P.lsh[1]) * 0.5;
    const base = Math.max(shHalf, S * 0.15);
    const topW = base * 1.32, midW = base * 1.16, hipW2 = base * 1.28;
    const waistC = lerp2(hipMid, shMid, 0.5);
    const nb = lerp2(shMid, P.neck || shMid, 0.35);
    const torso = [
      V(hipMid, mul(side, -hipW2)), V(waistC, mul(side, -midW)), V(shMid, mul(side, -topW)),
      V(nb, mul(side, -topW * 0.42)), V(nb, mul(side, topW * 0.42)),
      V(shMid, mul(side, topW)), V(waistC, mul(side, midW)), V(hipMid, mul(side, hipW2)),
    ];
    // outer shoulder attach points (so arms come out of the coat, not from inside)
    const shoulderOf = (sd) => { const s2 = sd === 'l' ? -1 : 1; return V(shMid, mul(side, s2 * topW * 0.86)); };

    function armOf(sd, shade) {
      strand(ctx, [shoulderOf(sd), P[sd + 'el'], P[sd + 'wr']], uArm, loArm, shade ? COAT_S : COAT, LINE, LW, true);
      const wr = P[sd + 'wr'], el = P[sd + 'el']; const d = norm(sub(wr, el));
      const hc = V(wr, mul(d, loArm * 0.4));
      ctx.beginPath(); ctx.ellipse(hc[0], hc[1], loArm * 0.66, loArm * 0.78, Math.atan2(d[1], d[0]), 0, TAU); ctx.fillStyle = SKIN; ctx.fill(); ctx.strokeStyle = LINE; ctx.lineWidth = LW; ctx.stroke();
    }
    function legOf(sd, shade) {
      const hipOut = V(hipMid, mul(side, (sd === 'l' ? -1 : 1) * hipW2 * 0.5));
      strand(ctx, [hipOut, P[sd + 'kn'], P[sd + 'ank']], thigh, calf, shade ? PANT_S : PANT, LINE, LW, false);
      const an = P[sd + 'ank']; const fd = o.faceDir || 1;
      ctx.save(); ctx.translate(an[0], an[1]);
      ctx.beginPath(); ctx.moveTo(-calf * 0.5, -calf * 0.2); ctx.quadraticCurveTo(-calf * 0.6, calf * 0.7, -calf * 0.2, calf * 0.7);
      ctx.lineTo(fd * calf * 1.5, calf * 0.7); ctx.quadraticCurveTo(fd * calf * 1.7, calf * 0.2, fd * calf * 1.1, -calf * 0.1);
      ctx.closePath(); ctx.fillStyle = SHOE; ctx.fill(); ctx.strokeStyle = LINE; ctx.lineWidth = LW; ctx.stroke(); ctx.restore();
    }

    // depth order: back arm, back leg, torso, front leg, front arm, head
    armOf(B, true);
    legOf(B, true);
    blob(ctx, torso, COAT, LINE, LW);
    // clean cel shadow: darker on the back half (clip to torso, fill one side)
    ctx.save(); blob(ctx, torso); ctx.clip(); ctx.globalAlpha = 0.5; ctx.fillStyle = COAT_S;
    const ss = (B === 'l' ? -1 : 1); const bigD = base * 4;
    ctx.beginPath(); ctx.moveTo(shMid[0] + spineDir[0] * bigD, shMid[1] + spineDir[1] * bigD);
    ctx.lineTo(shMid[0] - spineDir[0] * bigD, shMid[1] - spineDir[1] * bigD);
    ctx.lineTo(shMid[0] - spineDir[0] * bigD + side[0] * ss * bigD, shMid[1] - spineDir[1] * bigD + side[1] * ss * bigD);
    ctx.lineTo(shMid[0] + spineDir[0] * bigD + side[0] * ss * bigD, shMid[1] + spineDir[1] * bigD + side[1] * ss * bigD);
    ctx.closePath(); ctx.fill(); ctx.globalAlpha = 1; ctx.restore();
    if (!st.demon) {
      // shirt V at the collar + tie down the front midline
      ctx.save(); blob(ctx, torso); ctx.clip();
      ctx.fillStyle = SHIRT; ctx.beginPath();
      ctx.moveTo(nb[0] - side[0] * topW * 0.42, nb[1] - side[1] * topW * 0.42);
      ctx.lineTo(nb[0] + side[0] * topW * 0.42, nb[1] + side[1] * topW * 0.42);
      ctx.lineTo(waistC[0] + side[0] * base * 0.28, waistC[1] + side[1] * base * 0.28);
      ctx.lineTo(waistC[0] - side[0] * base * 0.28, waistC[1] - side[1] * base * 0.28);
      ctx.closePath(); ctx.fill();
      ctx.strokeStyle = TIE; ctx.lineWidth = S * 0.05; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(nb[0], nb[1]); ctx.lineTo(lerp2(nb, waistC, 0.92)[0], lerp2(nb, waistC, 0.92)[1]); ctx.stroke();
      ctx.restore();
    }

    legOf(Fs, false);
    armOf(Fs, false);

    // ---- neck + head ----
    const headTop = P.head; const headPos = lerp2(shMid, headTop, 0.55);
    strand(ctx, [shMid, headPos], S * 0.11, S * 0.10, SKIN, LINE, LW, false);
    const hr = S * 0.175; const hx = headPos[0], hy = headPos[1] - hr * 0.35;
    const fd = o.lookDir != null ? o.lookDir : (o.faceDir || 1);
    ctx.beginPath(); ctx.ellipse(hx, hy, hr * 0.92, hr, 0, 0, TAU); ctx.fillStyle = SKIN; ctx.fill(); ctx.strokeStyle = LINE; ctx.lineWidth = LW; ctx.stroke();
    ctx.save(); ctx.translate(hx, hy);
    // cheek shadow (away from facing)
    ctx.save(); ctx.beginPath(); ctx.ellipse(0, 0, hr * 0.92, hr, 0, 0, TAU); ctx.clip(); ctx.fillStyle = SKIN_S; ctx.beginPath(); ctx.ellipse(-fd * hr * 0.55, hr * 0.12, hr * 0.75, hr, 0, 0, TAU); ctx.fill(); ctx.restore();
    // hair (organic sweep)
    ctx.fillStyle = HAIR; ctx.beginPath(); ctx.moveTo(-hr * 0.95, hr * 0.05); ctx.quadraticCurveTo(-hr * 1.05, -hr * 0.95, hr * 0.1, -hr * 0.98); ctx.quadraticCurveTo(hr * 1.05, -hr * 0.9, hr * 0.95, -hr * 0.1); ctx.quadraticCurveTo(hr * 0.5 + fd * hr * 0.2, -hr * 0.55, hr * 0.1 + fd * hr * 0.2, -hr * 0.5); ctx.quadraticCurveTo(-hr * 0.2, -hr * 0.62, -hr * 0.95, hr * 0.05); ctx.closePath(); ctx.fill();
    // eyes
    const eo = em.eye == null ? 1 : em.eye;
    for (const s of [-0.4, 0.4]) { const ex = (s + 0.26 * fd) * hr, ey = hr * 0.06; ctx.beginPath(); ctx.ellipse(ex, ey, hr * 0.15, hr * 0.19 * eo + 0.5, 0, 0, TAU); ctx.fillStyle = '#fff'; ctx.fill(); ctx.strokeStyle = LINE; ctx.lineWidth = LW * 0.6; ctx.stroke(); if (eo > 0.35) { ctx.beginPath(); ctx.arc(ex + 0.05 * hr * fd, ey + 1, hr * 0.075, 0, TAU); ctx.fillStyle = LINE; ctx.fill(); } }
    // brows
    const bw = em.brow || 0; ctx.strokeStyle = LINE; ctx.lineWidth = LW * 0.85; ctx.lineCap = 'round';
    for (const s of [-1, 1]) { const bx = (0.4 * s + 0.26 * fd) * hr; ctx.beginPath(); ctx.moveTo(bx - hr * 0.16, -hr * 0.2 + (bw < 0 ? -bw * hr * 0.22 : 0)); ctx.lineTo(bx + hr * 0.16, -hr * 0.2 - bw * hr * 0.28); ctx.stroke(); }
    // mouth
    const mo = Math.max(0, em.mouth || 0); const mx = 0.2 * fd * hr, my = hr * 0.5;
    ctx.strokeStyle = LINE; ctx.lineWidth = LW * 0.85;
    if (mo < 0.12) { ctx.beginPath(); ctx.moveTo(mx - hr * 0.18, my); ctx.quadraticCurveTo(mx, my + (em.smile ? -hr * 0.16 : hr * 0.09), mx + hr * 0.18, my); ctx.stroke(); }
    else { ctx.beginPath(); ctx.ellipse(mx, my, hr * 0.15, hr * 0.1 + hr * 0.24 * mo, 0, 0, TAU); ctx.fillStyle = '#5a2320'; ctx.fill(); ctx.stroke(); }
    if (o.horns) { ctx.fillStyle = st.coat || '#2c0e0e'; ctx.strokeStyle = LINE; ctx.lineWidth = LW; for (const hd of [-1, 1]) { ctx.beginPath(); ctx.moveTo(hd * hr * 0.55, -hr * 0.7); ctx.quadraticCurveTo(hd * hr * 1.1, -hr * 1.3, hd * hr * 0.78, -hr * 1.85); ctx.quadraticCurveTo(hd * hr * 0.6, -hr * 1.25, hd * hr * 0.3, -hr * 0.85); ctx.closePath(); ctx.fill(); ctx.stroke(); } }
    if (o.glow) { ctx.save(); ctx.globalCompositeOperation = 'lighter'; for (const s of [-0.4, 0.4]) { const ex = (s + 0.26 * fd) * hr, ey = hr * 0.06; const g = ctx.createRadialGradient(ex, ey, 0, ex, ey, hr * 0.6); g.addColorStop(0, 'rgba(255,220,90,0.95)'); g.addColorStop(1, 'rgba(255,120,0,0)'); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(ex, ey, hr * 0.6, 0, TAU); ctx.fill(); } ctx.restore(); }
    ctx.restore();
  }
  global.drawChar2D = drawChar2D;
})(window);
