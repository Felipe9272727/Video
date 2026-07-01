const { chromium } = require('playwright');
const fs = require('fs'); const path = require('path');
const CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const clipFile = process.argv[2] || '../mocap/walk.json';
const N = parseInt(process.argv[3] || '16', 10);
(async () => {
  const clip = JSON.parse(fs.readFileSync(path.join(__dirname, clipFile), 'utf8'));
  const b = await chromium.launch({ executablePath: CHROME, args: ['--no-sandbox'] });
  const pg = await b.newPage({ viewport: { width: 400, height: 540 } });
  await pg.setContent('<canvas id="c" width="400" height="540"></canvas>');
  await pg.addScriptTag({ path: path.join(__dirname, 'charlie_mocap.js') });
  await pg.addScriptTag({ content: 'window.CLIP=' + JSON.stringify(clip) });
  for (let i = 0; i < N; i++) {
    await pg.evaluate((i) => {
      const c = document.getElementById('c'); const x = c.getContext('2d');
      x.fillStyle = '#20242c'; x.fillRect(0, 0, 400, 540);
      drawCharlieMocap(x, window.CLIP, i, { x: 200, y: 380, scale: 250, faceDir: 1, emotion: { mouth: 0.35, brow: 0.2, smile: true } });
    }, i);
    fs.writeFileSync(`/home/user/Video/build/mc_${String(i).padStart(2, '0')}.png`, await pg.screenshot());
  }
  await b.close(); console.log('rendered', N, 'frames from', clipFile);
})();
