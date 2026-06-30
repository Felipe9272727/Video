// Render the Charlie's Inferno animation frame-by-frame in headless Chromium,
// piping PNG frames straight into ffmpeg (H.264 + AAC, audio muxed in one pass).
//
//   node render.js --probe 200,1200,3000        -> PNGs to build/ for QA
//   node render.js --out ../charlie_inferno.mp4  -> full render with audio
//   node render.js --start 1300 --count 360 --out build/clip.mp4 --audio
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
const CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const FFMPEG = fs.readFileSync(path.join(ROOT, 'build/ffmpeg_path.txt'), 'utf8').trim();
const AUDIO = path.join(ROOT, 'Charlie_s Inferno (Excuse Me Sir) - That Handsome Devil _ COVER PT-BR(MP3_160K)_1.mp3');
const TL = JSON.parse(fs.readFileSync(path.join(ROOT, 'build/timeline.json'), 'utf8'));

function arg(name, def) {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : def;
}
const probe = arg('--probe', null);
const out = arg('--out', null);
const start = parseInt(arg('--start', '0'), 10);
const count = parseInt(arg('--count', String(TL.count - start)), 10);
const withAudio = process.argv.includes('--audio') || (start === 0 && !probe);
const FPS = TL.fps;

(async () => {
  const browser = await chromium.launch({ executablePath: CHROME, args: ['--no-sandbox', '--disable-gpu'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720, deviceScaleFactor: 1 } });
  await page.goto('file://' + path.join(__dirname, 'page.html'));
  await page.addScriptTag({ content: 'window.__TL=' + JSON.stringify(TL) + ';' });
  await page.evaluate(() => CharlieInferno.init(window.__TL));

  if (probe) {
    for (const s of probe.split(',')) {
      const i = parseInt(s, 10);
      await page.evaluate((f) => CharlieInferno.renderFrame(f), i);
      const buf = await page.screenshot({ type: 'png' });
      const p = path.join(ROOT, 'build', `frame_${String(i).padStart(5, '0')}.png`);
      fs.writeFileSync(p, buf);
      console.log('wrote', p);
    }
    await browser.close();
    return;
  }

  // warm up particle state from frame 0 if starting mid-song
  for (let i = 0; i < start; i++) await page.evaluate((f) => CharlieInferno.renderFrame(f), i);

  const ffArgs = ['-y', '-f', 'image2pipe', '-framerate', String(FPS), '-i', 'pipe:0'];
  if (withAudio) {
    ffArgs.push('-ss', String(start / FPS), '-i', AUDIO,
      '-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-b:a', '192k');
  } else {
    ffArgs.push('-map', '0:v');
  }
  ffArgs.push('-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'medium', '-crf', '19',
    '-shortest', '-movflags', '+faststart', out);
  const ff = spawn(FFMPEG, ffArgs, { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => { ff.on('close', c => c === 0 ? res() : rej(new Error('ffmpeg ' + c))); });

  function write(buf) {
    return new Promise((res) => { if (ff.stdin.write(buf)) res(); else ff.stdin.once('drain', res); });
  }

  const t0 = Date.now();
  for (let k = 0; k < count; k++) {
    const i = start + k;
    await page.evaluate((f) => CharlieInferno.renderFrame(f), i);
    const buf = await page.screenshot({ type: 'png' });
    await write(buf);
    if (k % 120 === 0) {
      const sec = (Date.now() - t0) / 1000;
      const fpsr = k / (sec || 1);
      console.log(`frame ${k}/${count}  ${fpsr.toFixed(1)} fps  eta ${((count - k) / (fpsr || 1) / 60).toFixed(1)}m`);
    }
  }
  ff.stdin.end();
  await done;
  await browser.close();
  console.log('DONE ->', out, `(${((Date.now() - t0) / 1000).toFixed(0)}s)`);
})();
