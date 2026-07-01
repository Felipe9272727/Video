// Showcase: same mocap run, cutting between many camera angles (2D over 3D rig).
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs'); const path = require('path');
const ROOT = path.resolve(__dirname, '..');
const CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const FFMPEG = fs.readFileSync(path.join(ROOT, 'build/ffmpeg_path.txt'), 'utf8').trim();
const NAMES = ['run_side', 'run_low', 'run_34f', 'run_high', 'run_34b', 'run_front'];
const LABELS = ['perfil', 'contra-plongée', '3/4 frente', 'plongée', '3/4 costas', 'frente'];
const clips = {}; for (const n of NAMES) clips[n] = JSON.parse(fs.readFileSync(path.join(ROOT, 'mocap/' + n + '.json'), 'utf8'));

(async () => {
  const b = await chromium.launch({ executablePath: CHROME, args: ['--no-sandbox', '--disable-gpu'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  await pg.setContent('<canvas id="c" width="1280" height="720"></canvas>');
  await pg.addScriptTag({ path: path.join(__dirname, 'charlie2d.js') });
  await pg.addScriptTag({ content: 'window.C=' + JSON.stringify(clips) + ';window.NM=' + JSON.stringify(NAMES) + ';window.LB=' + JSON.stringify(LABELS) });
  const ff = spawn(FFMPEG, ['-y', '-f', 'image2pipe', '-framerate', '24', '-i', 'pipe:0', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'medium', '-crf', '20', '-movflags', '+faststart', path.join(ROOT, 'build/angles_demo.mp4')], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => ff.on('close', c => c === 0 ? res() : rej(new Error('ff ' + c))));
  const write = buf => new Promise(r => ff.stdin.write(buf) ? r() : ff.stdin.once('drain', r));
  const SHOT = 30, N = SHOT * NAMES.length; // ~7.5s
  for (let i = 0; i < N; i++) {
    await pg.evaluate((i) => {
      const x = document.getElementById('c').getContext('2d'); const W = 1280, H = 720;
      const g = x.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#232a38'); g.addColorStop(1, '#3d4658'); x.fillStyle = g; x.fillRect(0, 0, W, H);
      x.fillStyle = '#1b2230'; x.fillRect(0, 600, W, 120);
      const shot = Math.floor(i / 30) % window.NM.length; const nm = window.NM[shot];
      // per-angle framing: scale + a slow push
      const frames = { run_side: [150, 640], run_low: [175, 690], run_34f: [155, 655], run_high: [140, 600], run_34b: [155, 655], run_front: [150, 650] }[nm];
      const sc = frames[0] * (1 + 0.06 * ((i % 30) / 30));
      const cl = window.C[nm]; const fr = cl.frames[i % cl.count];
      // ground shadow
      x.save(); x.globalAlpha = 0.3; x.fillStyle = '#0c1018'; x.beginPath(); x.ellipse(W / 2, 660, sc * 0.9, sc * 0.13, 0, 0, Math.PI * 2); x.fill(); x.restore();
      drawChar2D(x, fr, { x: W / 2, y: frames[1] - sc, scale: sc, faceDir: 1, emotion: { mouth: 0.55, brow: -0.5, eye: 1 } });
      // letterbox + label + cut flash
      x.fillStyle = '#000'; x.fillRect(0, 0, W, 70); x.fillRect(0, H - 70, W, 70);
      x.fillStyle = 'rgba(255,235,150,0.9)'; x.font = 'bold 26px Georgia'; x.fillText('ângulo: ' + window.LB[shot], 44, H - 30);
      x.fillStyle = 'rgba(255,255,255,0.8)'; x.font = '20px Georgia'; x.fillText('mesmo movimento (mocap), câmera 3D girada', 44, 46);
      if (i % 30 < 2) { x.fillStyle = 'rgba(255,255,255,0.35)'; x.fillRect(0, 0, W, H); }
    }, i);
    await write(await pg.screenshot({ type: 'png' }));
  }
  ff.stdin.end(); await done; await b.close(); console.log('DONE');
})();
