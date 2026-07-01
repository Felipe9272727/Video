/* Draw the cel-shaded Charlie following real mocap joints (from bvh2d.py).
 * clip.frames[i] = { hip:[x,y,z], chest, neck, head, lsh,lel,lwr, rsh,rel,rwr,
 *                    lhip,lkn,lank, rhip,rkn,rank }  (hip at origin, ~unit tall)
 * o = { x, y, scale, emotion:{brow,mouth,smile,eye}, faceDir }
 */
(function (global) {
  const TAU = Math.PI * 2;
  const SKIN = '#e8b48c', SKIN_S = '#c98d64', HAIR = '#3b2a22', COAT = '#38506b',
    COAT_S = '#2a3c52', SHIRT = '#d9dde3', TIE = '#7d2530', PANT = '#2a2f39',
    SHOE = '#15100c', LINE = '#141018';

  function limb(ctx, pts, w, fill, line, lw) {
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
    if (line) { ctx.strokeStyle = line; ctx.lineWidth = w + (lw == null ? 6 : lw); ctx.stroke(); }
    ctx.strokeStyle = fill; ctx.lineWidth = w; ctx.stroke();
  }
  function poly(ctx, pts, fill, line, lw) { ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]); ctx.closePath(); if (fill) { ctx.fillStyle = fill; ctx.fill(); } if (line) { ctx.strokeStyle = line; ctx.lineWidth = lw || 3; ctx.lineJoin = 'round'; ctx.stroke(); } }

  function drawCharlieMocap(ctx, clip, fi, o) {
    const n = clip.count; const fr = clip.frames[((fi % n) + n) % n];
    const S = o.scale, X = o.x, Y = o.y; const em = o.emotion || {};
    const P = {}; for (const k in fr) P[k] = [X + fr[k][0] * S, Y + fr[k][1] * S, fr[k][2]];
    const wLeg = S * 0.09, wArm = S * 0.075, wNeck = S * 0.085;
    // depth: the side with greater z is farther -> draw first
    const leftBehind = (P.lsh[2] + P.lhip[2]) >= (P.rsh[2] + P.rhip[2]);
    const back = leftBehind ? 'l' : 'r', front = leftBehind ? 'r' : 'l';

    function leg(sd) {
      const hip = P[sd + 'hip'], kn = P[sd + 'kn'], an = P[sd + 'ank'];
      limb(ctx, [hip, kn, an], wLeg * 2.0, PANT, LINE, 6);
      // foot
      const dir = Math.sign((P.rank[0] - P.lank[0]) || 1) * (sd === 'l' ? -1 : 1);
      poly(ctx, [[an[0] - 6, an[1] - 4], [an[0] + 26 * (o.faceDir || 1), an[1] - 6], [an[0] + 28 * (o.faceDir || 1), an[1] + 8], [an[0] - 8, an[1] + 8]], SHOE, LINE, 3);
    }
    function arm(sd) {
      const sh = P[sd + 'sh'], el = P[sd + 'el'], wr = P[sd + 'wr'];
      limb(ctx, [sh, el, wr], wArm * 2.0, COAT, LINE, 6);
      ctx.beginPath(); ctx.arc(wr[0], wr[1], wArm * 1.15, 0, TAU); ctx.fillStyle = SKIN; ctx.fill(); ctx.strokeStyle = LINE; ctx.lineWidth = 3; ctx.stroke();
    }

    leg(back); arm(back);
    // ---- torso (coat) from shoulders to hips, bulging via chest ----
    const torso = [P.lsh, P.rsh, [P.rhip[0], P.rhip[1] + wLeg], [P.lhip[0], P.lhip[1] + wLeg]];
    // widen shoulders/hips a touch
    const cxs = (P.lsh[0] + P.rsh[0]) / 2;
    const T = [
      [P.lsh[0] - (P.lsh[0] < cxs ? 8 : -8), P.lsh[1] - 6], [P.rsh[0] + (P.rsh[0] > cxs ? 8 : -8), P.rsh[1] - 6],
      [P.rhip[0] + 6, P.rhip[1] + wLeg], [P.lhip[0] - 6, P.lhip[1] + wLeg]
    ];
    poly(ctx, T, COAT, LINE, Math.max(3, S * 0.03));
    // shirt + tie down the chest->hip midline
    const neckMid = P.neck, hipMid = [(P.lhip[0] + P.rhip[0]) / 2, (P.lhip[1] + P.rhip[1]) / 2];
    ctx.save(); poly(ctx, T); ctx.clip();
    ctx.strokeStyle = SHIRT; ctx.lineWidth = S * 0.10; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(neckMid[0], neckMid[1]); ctx.lineTo(hipMid[0], hipMid[1]); ctx.stroke();
    ctx.strokeStyle = TIE; ctx.lineWidth = S * 0.045; ctx.beginPath(); ctx.moveTo(neckMid[0], neckMid[1]); ctx.lineTo(hipMid[0], hipMid[1] - S * 0.05); ctx.stroke();
    // cel shadow on the back side
    ctx.globalAlpha = 0.22; ctx.fillStyle = COAT_S; ctx.fillRect(back === 'l' ? Math.min(P.lsh[0], P.lhip[0]) - 30 : cxs, Math.min(P.lsh[1], P.rsh[1]) - 10, 80, S * 0.9); ctx.globalAlpha = 1;
    ctx.restore();

    // ---- neck + head (compress the tall mocap neck for a stylized proportion) ----
    const shMid = [(P.lsh[0] + P.rsh[0]) / 2, (P.lsh[1] + P.rsh[1]) / 2];
    const headPos = [shMid[0] + (P.head[0] - shMid[0]) * 0.5, shMid[1] + (P.head[1] - shMid[1]) * 0.5];
    limb(ctx, [shMid, headPos], wNeck * 1.7, SKIN, LINE, 6);
    const hr = S * 0.16, hx = headPos[0], hy = headPos[1] - hr * 0.35;
    ctx.beginPath(); ctx.arc(hx, hy, hr, 0, TAU); ctx.fillStyle = SKIN; ctx.fill(); ctx.strokeStyle = LINE; ctx.lineWidth = 3.5; ctx.stroke();
    // face turned by faceDir (which way he's moving/looking)
    const fd = o.faceDir || 1;
    ctx.save(); ctx.translate(hx, hy);
    // cheek shadow
    ctx.save(); ctx.beginPath(); ctx.arc(0, 0, hr, 0, TAU); ctx.clip(); ctx.fillStyle = SKIN_S; ctx.beginPath(); ctx.ellipse(hr * 0.55 * -fd, hr * 0.1, hr * 0.8, hr, 0, 0, TAU); ctx.fill(); ctx.restore();
    // hair
    ctx.fillStyle = HAIR; ctx.beginPath(); ctx.arc(0, -hr * 0.15, hr * 1.02, Math.PI * 1.02, Math.PI * 2.05, false); ctx.quadraticCurveTo(hr * 0.5 * fd, -hr * 0.7, -hr * 0.2 * fd, -hr * 0.55); ctx.closePath(); ctx.fill();
    // eyes (shifted toward facing dir)
    const eo = (em.eye == null ? 1 : em.eye);
    for (const s of [-0.42, 0.42]) { const ex = (s + 0.28 * fd) * hr, ey = hr * 0.1; ctx.beginPath(); ctx.ellipse(ex, ey, hr * 0.14, hr * 0.17 * eo + 1, 0, 0, TAU); ctx.fillStyle = '#fff'; ctx.fill(); ctx.strokeStyle = LINE; ctx.lineWidth = 1.5; ctx.stroke(); if (eo > 0.4) { ctx.beginPath(); ctx.arc(ex + 0.06 * hr * fd, ey + 1, hr * 0.07, 0, TAU); ctx.fillStyle = LINE; ctx.fill(); } }
    // brows
    const bw = em.brow || 0; ctx.strokeStyle = LINE; ctx.lineWidth = 2.4; ctx.lineCap = 'round';
    for (const s of [-1, 1]) { const bx = (0.42 * s + 0.28 * fd) * hr; ctx.beginPath(); ctx.moveTo(bx - hr * 0.14, -hr * 0.16 + (bw < 0 ? -bw * hr * 0.2 : 0)); ctx.lineTo(bx + hr * 0.14, -hr * 0.16 - bw * hr * 0.25); ctx.stroke(); }
    // mouth
    const mo = Math.max(0, em.mouth || 0); ctx.strokeStyle = LINE; ctx.lineWidth = 2.4;
    const mx = 0.22 * fd * hr, my = hr * 0.52;
    if (mo < 0.12) { ctx.beginPath(); ctx.moveTo(mx - hr * 0.16, my); ctx.quadraticCurveTo(mx, my + (em.smile ? -hr * 0.14 : hr * 0.08), mx + hr * 0.16, my); ctx.stroke(); }
    else { ctx.beginPath(); ctx.ellipse(mx, my, hr * 0.14, hr * 0.1 + hr * 0.22 * mo, 0, 0, TAU); ctx.fillStyle = '#5a2320'; ctx.fill(); ctx.stroke(); }
    ctx.restore();

    leg(front); arm(front);
  }
  global.drawCharlieMocap = drawCharlieMocap;
})(window);
