// Demo: real-2D character (charlie2d) driven by 3D mocap skeleton. walk -> run.
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs'); const path = require('path');
const ROOT = path.resolve(__dirname, '..');
const CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const FFMPEG = fs.readFileSync(path.join(ROOT, 'build/ffmpeg_path.txt'), 'utf8').trim();
const walk = JSON.parse(fs.readFileSync(path.join(ROOT, 'mocap/walk_side.json'), 'utf8'));
const run = JSON.parse(fs.readFileSync(path.join(ROOT, 'mocap/run_side.json'), 'utf8'));
(async () => {
  const b = await chromium.launch({ executablePath: CHROME, args: ['--no-sandbox', '--disable-gpu'] });
  const pg = await b.newPage({ viewport: { width: 1280, height: 720 } });
  await pg.setContent('<canvas id="c" width="1280" height="720"></canvas>');
  await pg.addScriptTag({ path: path.join(__dirname, 'charlie2d.js') });
  await pg.addScriptTag({ content: 'window.W=' + JSON.stringify(walk) + ';window.R=' + JSON.stringify(run) });
  const ff = spawn(FFMPEG, ['-y', '-f', 'image2pipe', '-framerate', '24', '-i', 'pipe:0', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'medium', '-crf', '20', '-movflags', '+faststart', path.join(ROOT, 'build/char2d_demo.mp4')], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => ff.on('close', c => c === 0 ? res() : rej(new Error('ff ' + c))));
  const write = buf => new Promise(r => ff.stdin.write(buf) ? r() : ff.stdin.once('drain', r));
  const TOT = 168;
  for (let i = 0; i < TOT; i++) {
    await pg.evaluate((i) => {
      const x = document.getElementById('c').getContext('2d');
      const g = x.createLinearGradient(0, 0, 0, 720); g.addColorStop(0, '#33465e'); g.addColorStop(1, '#6b7c92'); x.fillStyle = g; x.fillRect(0, 0, 1280, 720);
      x.fillStyle = '#2a3340'; x.fillRect(0, 610, 1280, 110);
      x.strokeStyle = 'rgba(255,255,255,0.14)'; x.lineWidth = 4; x.setLineDash([50, 40]); x.beginPath(); x.moveTo(0, 668); x.lineTo(1280, 668); x.stroke(); x.setLineDash([]);
      let clip, speed, phase, label;
      if (i < 96) { clip = 'W'; speed = 3.6; phase = i; label = '2D real — movido por esqueleto 3D (caminhada)'; }
      else { clip = 'R'; speed = 8.2; phase = i - 96; label = '2D real — movido por esqueleto 3D (corrida)'; }
      const cx = ((phase * speed) % 1440) - 80;
      const fr = window[clip].frames[((i % window[clip].count) + window[clip].count) % window[clip].count];
      drawChar2D(x, fr, { x: cx, y: 330, scale: 150, faceDir: 1, emotion: { mouth: 0.25 + 0.2 * Math.sin(i * 0.5), brow: clip === 'R' ? -0.3 : 0.2, smile: clip === 'W' } });
      x.fillStyle = 'rgba(255,255,255,0.85)'; x.font = '22px Georgia'; x.fillText(label, 40, 56);
    }, i);
    await write(await pg.screenshot({ type: 'png' }));
  }
  ff.stdin.end(); await done; await b.close(); console.log('DONE');
})();
