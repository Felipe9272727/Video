// Real 2.5D: a 3D toon-shaded character (cel + outline) rendered on CPU via
// SwiftShader WebGL, rotated 360° (full body incl. head) to prove the form.
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs'); const path = require('path');
const ROOT = path.resolve(__dirname, '..');
const CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const FFMPEG = fs.readFileSync(path.join(ROOT, 'build/ffmpeg_path.txt'), 'utf8').trim();
const THREEJS = fs.readFileSync(path.join(ROOT, 'node_modules/three/build/three.min.js'), 'utf8');
const PROBE = process.argv.includes('--probe');

const SCENE = `
const W=960,H=720;
const renderer=new THREE.WebGLRenderer({canvas:document.getElementById('c'),antialias:true});
renderer.setSize(W,H,false); renderer.outputEncoding=THREE.sRGBEncoding;
const scene=new THREE.Scene(); scene.background=new THREE.Color('#2b3444');
const cam=new THREE.PerspectiveCamera(32,W/H,0.1,100); cam.position.set(0,1.15,5.4); cam.lookAt(0,1.0,0);
scene.add(new THREE.AmbientLight(0x8090a0,0.75));
const key=new THREE.DirectionalLight(0xfff2e0,2.1); key.position.set(-3,5,4); scene.add(key);
const rim=new THREE.DirectionalLight(0x88a0ff,0.7); rim.position.set(3,2,-4); scene.add(rim);
// cel ramp
const ramp=new Uint8Array([70,70,70,150,150,255,255,255]);
const grad=new THREE.DataTexture(ramp,4,1,THREE.RedFormat); grad.needsUpdate=true;
const toon=(c)=>new THREE.MeshToonMaterial({color:new THREE.Color(c),gradientMap:grad});
const OUT=new THREE.MeshBasicMaterial({color:0x0b0b12,side:THREE.BackSide});
function outline(m,s){ const o=new THREE.Mesh(m.geometry,OUT); o.scale.setScalar(s||1.06); m.add(o); return m; }
function add(geo,mat,x,y,z,parent){ const m=new THREE.Mesh(geo,mat); m.position.set(x,y,z); (parent||char).add(m); return m; }

const char=new THREE.Group(); scene.add(char);
const SKIN='#e8b48c',COAT='#3b5570',PANT='#2a2f39',HAIR='#3a281f',SHOE='#181009';
// legs (capsules, slight A)
for(const s of [-1,1]){ const leg=add(new THREE.CapsuleGeometry(0.135,0.78,6,14),toon(PANT), s*0.16,0.52,0); leg.rotation.z=s*0.04; outline(leg,1.07);
  add(new THREE.BoxGeometry(0.2,0.12,0.34),toon(SHOE), s*0.17,0.06,0.06); }
// torso (tapered capsule)
const torso=add(new THREE.CapsuleGeometry(0.3,0.5,8,16),toon(COAT), 0,1.28,0); torso.scale.set(1.05,1,0.72); outline(torso,1.06);
// shirt V + tie (front, z+)
add(new THREE.ConeGeometry(0.16,0.34,3),toon('#d9dde3'), 0,1.42,0.2).rotation.x=Math.PI;
const tie=add(new THREE.BoxGeometry(0.07,0.42,0.03),toon('#7d2530'), 0,1.28,0.235);
// arms
for(const s of [-1,1]){ const up=add(new THREE.CapsuleGeometry(0.1,0.42,6,12),toon(COAT), s*0.4,1.42,0); up.rotation.z=s*0.22; outline(up,1.08);
  const lo=add(new THREE.CapsuleGeometry(0.088,0.4,6,12),toon(COAT), s*0.52,1.0,0.02); lo.rotation.z=s*0.12; outline(lo,1.08);
  add(new THREE.SphereGeometry(0.1,12,12),toon(SKIN), s*0.57,0.76,0.03); }
// neck
add(new THREE.CylinderGeometry(0.1,0.12,0.16,12),toon(SKIN), 0,1.66,0);
// head group (so face+hair rotate with the head)
const head=new THREE.Group(); head.position.set(0,1.86,0); char.add(head);
const skull=new THREE.Mesh(new THREE.SphereGeometry(0.27,20,20),toon(SKIN)); head.add(skull); outline(skull,1.05);
// hair (cap covering top/back)
const hairGeo=new THREE.SphereGeometry(0.285,20,20,0,Math.PI*2,0,Math.PI*0.62);
const hair=new THREE.Mesh(hairGeo,toon(HAIR)); hair.position.y=0.02; head.add(hair);
const hairBack=new THREE.Mesh(new THREE.SphereGeometry(0.285,20,20,Math.PI*0.55,Math.PI*0.9,Math.PI*0.32,Math.PI*0.5),toon(HAIR)); head.add(hairBack);
// face (on +z)
for(const s of [-1,1]){
  add(new THREE.SphereGeometry(0.05,10,10),toon('#ffffff'), s*0.1,0.02,0.235,head);
  add(new THREE.SphereGeometry(0.026,8,8),toon('#181018'), s*0.1,0.02,0.275,head);
  const brow=add(new THREE.BoxGeometry(0.09,0.02,0.02),toon('#2a1c14'), s*0.1,0.1,0.25,head); brow.rotation.z=s*0.18;
}
add(new THREE.SphereGeometry(0.04,10,10),toon(SKIN), 0,-0.02,0.265,head); // nose
add(new THREE.SphereGeometry(0.05,10,10),toon('#7a2f2a'), 0,-0.13,0.24,head).scale.set(1.4,0.7,0.6); // mouth

window.__ready=true;
window.renderAngle=(deg)=>{ char.rotation.y=deg*Math.PI/180; renderer.render(scene,cam); };
window.renderAngle(0);
`;

(async () => {
  const b = await chromium.launch({ executablePath: CHROME, args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--no-sandbox'] });
  const pg = await b.newPage({ viewport: { width: 960, height: 720 } });
  pg.on('pageerror', e => console.log('PAGEERR', e.message));
  await pg.setContent('<canvas id="c" width="960" height="720"></canvas>');
  await pg.addScriptTag({ content: THREEJS });
  await pg.addScriptTag({ content: SCENE });
  await pg.waitForFunction(() => window.__ready === true, { timeout: 20000 });

  if (PROBE) {
    for (const d of [0, 45, 90, 135, 180, 270]) { await pg.evaluate(dg => window.renderAngle(dg), d); fs.writeFileSync(path.join(ROOT, 'build/tt_' + d + '.png'), await pg.screenshot()); }
    await b.close(); console.log('probe done'); return;
  }
  const ff = spawn(FFMPEG, ['-y', '-f', 'image2pipe', '-framerate', '24', '-i', 'pipe:0', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'medium', '-crf', '20', '-movflags', '+faststart', path.join(ROOT, 'build/turntable.mp4')], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => ff.on('close', c => c === 0 ? res() : rej(new Error('ff ' + c))));
  const write = buf => new Promise(r => ff.stdin.write(buf) ? r() : ff.stdin.once('drain', r));
  const N = 120;
  for (let i = 0; i < N; i++) { await pg.evaluate(dg => window.renderAngle(dg), (i / N) * 360); await write(await pg.screenshot({ type: 'png' })); }
  ff.stdin.end(); await done; await b.close(); console.log('DONE turntable.mp4');
})();
