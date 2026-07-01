// PROOF SCENE (mocap): Charlie flees through the inferno, chased by demons.
// Bridge section 176–200s, real motion-capture run, synced to the audio.
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs'); const path = require('path');
const ROOT = path.resolve(__dirname, '..');
const CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const FFMPEG = fs.readFileSync(path.join(ROOT, 'build/ffmpeg_path.txt'), 'utf8').trim();
const AUDIO = path.join(ROOT, "Charlie_s Inferno (Excuse Me Sir) - That Handsome Devil _ COVER PT-BR(MP3_160K)_1.mp3");
const run = JSON.parse(fs.readFileSync(path.join(ROOT, 'mocap/run.json'), 'utf8'));
const TL = JSON.parse(fs.readFileSync(path.join(ROOT, 'build/timeline.json'), 'utf8'));
const T0 = 176.0, T1 = 200.2, FPS = 24;

(async () => {
  const b = await chromium.launch({ executablePath: CHROME, args: ['--no-sandbox', '--disable-gpu'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 720, deviceScaleFactor: 1 } });
  await pg.setContent('<canvas id="c" width="1280" height="720"></canvas>');
  await pg.addScriptTag({ path: path.join(__dirname, 'charlie_mocap.js') });
  await pg.addScriptTag({ content: 'window.RUN=' + JSON.stringify(run) + ';window.EMB=[];' });
  await pg.evaluate(() => {
    const W = 1280, H = 720, TAU = Math.PI * 2;
    function hash(n) { let t = (n * 2654435761) >>> 0; t ^= t >>> 15; t = Math.imul(t, 2246822519); t ^= t >>> 13; t = Math.imul(t, 3266489917); t ^= t >>> 16; return (t >>> 0) / 4294967296; }
    window.drawChase = function (t, f, i) {
      const c = document.getElementById('c'); const x = c.getContext('2d');
      x.setTransform(1, 0, 0, 1, 0, 0); x.clearRect(0, 0, W, H);
      // ---- background: inferno gradient ----
      const g = x.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#180406'); g.addColorStop(0.6, '#5a1410'); g.addColorStop(1, '#a5301a'); x.fillStyle = g; x.fillRect(0, 0, W, H);
      const glow = x.createRadialGradient(W / 2, H * 0.9, 40, W / 2, H * 0.9, 700); glow.addColorStop(0, `rgba(255,150,50,${0.4 + 0.3 * f.b})`); glow.addColorStop(1, 'rgba(255,80,0,0)'); x.fillStyle = glow; x.fillRect(0, 0, W, H);
      // camera: run bob + beat shake
      const camY = Math.sin(t * 12) * 4 + (hash(i) - 0.5) * 10 * f.beat;
      x.save(); x.translate((hash(i * 7) - 0.5) * 8 * f.beat, camY);
      // ---- parallax pillars (2 layers) ----
      for (let L = 0; L < 2; L++) {
        const spd = L ? 900 : 480, col = L ? '#12060a' : '#25090b', wdt = L ? 46 : 80, gap = L ? 210 : 340, base = L ? 690 : 700, top = L ? 250 : 150;
        const sc = (t * spd) % gap;
        for (let k = -1; k < W / gap + 2; k++) { const px = k * gap - sc; x.fillStyle = col; x.fillRect(px, top, wdt, base - top); }
      }
      x.fillStyle = '#12060a'; x.fillRect(0, 660, W, 60);
      // ---- fire tongues along the ground ----
      x.save(); x.globalCompositeOperation = 'lighter';
      for (let k = 0; k < 22; k++) { const fx = (hash(k * 13) * 1.05 - 0.025) * W; const fw = 60 + 90 * hash(k * 7); const fh = (70 + 150 * f.b) * (0.5 + hash(k * 3)) * (0.8 + 0.4 * Math.sin(t * 6 + k)); const fg = x.createLinearGradient(0, 690, 0, 690 - fh); fg.addColorStop(0, 'rgba(150,20,12,0.6)'); fg.addColorStop(0.5, 'rgba(255,90,30,0.6)'); fg.addColorStop(1, 'rgba(255,210,90,0.5)'); x.fillStyle = fg; x.beginPath(); x.moveTo(fx - fw / 2, 690); x.quadraticCurveTo(fx, 690 - fh, fx + fw / 2, 690); x.closePath(); x.fill(); }
      x.restore();
      // ---- embers ----
      const rate = 1 + 6 * f.h + 8 * f.onset; let sp = rate; while (sp > 0) { if (sp < 1 && hash(window.EMB.length * 9 + i) > sp) break; sp -= 1; window.EMB.push({ x: hash(window.EMB.length * 7 + i * 13) * W, y: 700, vx: (hash(window.EMB.length) - 0.5), vy: -(1 + hash(window.EMB.length * 3) * 2.5) - 2 * f.b, life: 0, max: 60 + hash(window.EMB.length * 5) * 90, r: 1 + hash(window.EMB.length * 2) * 2.4 }); }
      x.save(); x.globalCompositeOperation = 'lighter'; window.EMB = window.EMB.filter(e => { e.life++; e.x += e.vx; e.y += e.vy; e.vy *= 0.99; if (e.life > e.max || e.y < -20) return false; const k = 1 - e.life / e.max; const gg = x.createRadialGradient(e.x, e.y, 0, e.x, e.y, e.r * 4); gg.addColorStop(0, `rgba(255,225,150,${0.9 * k})`); gg.addColorStop(1, 'rgba(255,80,0,0)'); x.fillStyle = gg; x.beginPath(); x.arc(e.x, e.y, e.r * 4, 0, TAU); x.fill(); return true; }); if (window.EMB.length > 400) window.EMB.splice(0, window.EMB.length - 400); x.restore();
      // ---- demons chasing (same real run motion, dark + horns + glow) ----
      const dstyle = { coat: '#2c0e0e', coatS: '#1c0708', pant: '#1a0708', shoe: '#0c0304', tie: '#2c0e0e', shirt: '#2c0e0e', skin: '#3a1512', skinS: '#2a0f0c', hair: '#1a0708', line: '#0a0406' };
      const dbob = Math.sin(t * 12) * 3;
      drawCharlieMocap(x, window.RUN, i + 3, { x: 210 + Math.sin(t * 0.5) * 20, y: 452 + dbob, scale: 210, faceDir: 1, lookDir: 1, style: dstyle, horns: true, glow: true, emotion: { mouth: 0.5, brow: -0.6, eye: 1 } });
      drawCharlieMocap(x, window.RUN, i + 9, { x: 60 + Math.cos(t * 0.6) * 20, y: 462 - dbob, scale: 195, faceDir: 1, lookDir: 1, style: dstyle, horns: true, glow: true, emotion: { mouth: 0.6, brow: -0.6, eye: 1 } });
      // ---- Charlie fleeing, glancing back in terror every ~2s ----
      const glance = (Math.sin(t * 3.1) > 0.75) ? -1 : 1;
      drawCharlieMocap(x, window.RUN, i, { x: 760 + Math.sin(t * 0.7) * 30, y: 448, scale: 205, faceDir: 1, lookDir: glance, emotion: { mouth: 0.5 + 0.4 * f.v, brow: -0.85, eye: 1 } });
      // ---- speed lines / streaks ----
      x.save(); x.globalCompositeOperation = 'lighter'; x.strokeStyle = `rgba(255,150,70,${0.12 + 0.14 * f.beat})`; x.lineWidth = 3; for (let k = 0; k < 12; k++) { const yy = hash(k * 3 + (i / 2 | 0)) * H; x.beginPath(); x.moveTo(0, yy); x.lineTo(W, yy + 6); x.stroke(); } x.restore();
      x.restore();
      // ---- grade + vignette + letterbox ----
      x.save(); x.globalCompositeOperation = 'overlay'; x.globalAlpha = 0.16; x.fillStyle = 'rgb(180,50,20)'; x.fillRect(0, 0, W, H); x.restore();
      const vg = x.createRadialGradient(W / 2, H / 2, H * 0.32, W / 2, H / 2, H * 0.9); vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,0.55)'); x.fillStyle = vg; x.fillRect(0, 0, W, H);
      x.fillStyle = '#000'; x.fillRect(0, 0, W, 70); x.fillRect(0, H - 70, W, 70);
    };
  });

  const ffA = ['-y', '-f', 'image2pipe', '-framerate', String(FPS), '-i', 'pipe:0', '-ss', String(T0), '-i', AUDIO,
    '-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-b:a', '160k', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
    '-preset', 'medium', '-crf', '20', '-shortest', '-movflags', '+faststart', path.join(ROOT, 'build/chase.mp4')];
  const ff = spawn(FFMPEG, ffA, { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => ff.on('close', c => c === 0 ? res() : rej(new Error('ff ' + c))));
  const write = buf => new Promise(r => ff.stdin.write(buf) ? r() : ff.stdin.once('drain', r));

  const N = Math.round((T1 - T0) * FPS);
  for (let i = 0; i < N; i++) {
    const t = T0 + i / FPS; const f = TL.frames[Math.min(TL.count - 1, Math.round(t * FPS))];
    await pg.evaluate(([t, f, i]) => window.drawChase(t, f, i), [t, f, i]);
    await write(await pg.screenshot({ type: 'png' }));
    if (i % 120 === 0) console.log('frame', i, '/', N);
  }
  ff.stdin.end(); await done; await b.close(); console.log('DONE build/chase.mp4');
})();
