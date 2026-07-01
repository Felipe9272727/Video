#!/usr/bin/env python3
"""Parse a BVH mocap clip, run forward kinematics, project to 2D from a chosen
camera angle, and emit compact per-frame joint positions for the canvas rig.

Usage: bvh2d.py in.bvh out.json --yaw 20 --pitch 5 --fps 24 --preview strip.png
This is what lets a CPU-only agent get *real human motion* (not stiff procedural)
and any camera angle (rotate the 3D skeleton before projecting).
"""
import sys, json, math, argparse
import numpy as np

def parse_bvh(path):
    toks = open(path).read().split()
    i = 0
    def nxt():
        nonlocal i; t = toks[i]; i += 1; return t
    joints = []  # list of dict(name, parent, offset, channels, chan_start)
    stack = []
    chan_total = 0
    assert nxt() == 'HIERARCHY'
    while True:
        t = nxt()
        if t in ('ROOT', 'JOINT'):
            name = nxt(); assert nxt() == '{'
            j = dict(name=name, parent=(stack[-1] if stack else -1), offset=[0,0,0], channels=[], chan_start=0)
            joints.append(j); idx = len(joints)-1; stack.append(idx)
        elif t == 'End':
            nxt(); assert nxt() == '{'  # 'Site' '{'
            j = dict(name='End', parent=stack[-1], offset=[0,0,0], channels=[], chan_start=0, end=True)
            joints.append(j); stack.append(len(joints)-1)
        elif t == 'OFFSET':
            joints[stack[-1]]['offset'] = [float(nxt()), float(nxt()), float(nxt())]
        elif t == 'CHANNELS':
            n = int(nxt()); ch = [nxt() for _ in range(n)]
            joints[stack[-1]]['channels'] = ch
            joints[stack[-1]]['chan_start'] = chan_total; chan_total += n
        elif t == '}':
            stack.pop()
        elif t == 'MOTION':
            break
    assert nxt() == 'Frames:'; nframes = int(nxt())
    assert nxt() == 'Frame'; assert nxt() == 'Time:'; ftime = float(nxt())
    data = np.array([float(nxt()) for _ in range(nframes*chan_total)]).reshape(nframes, chan_total)
    return joints, data, ftime

def rot_mat(axis, deg):
    r = math.radians(deg); c, s = math.cos(r), math.sin(r)
    if axis == 'X': return np.array([[1,0,0],[0,c,-s],[0,s,c]])
    if axis == 'Y': return np.array([[c,0,s],[0,1,0],[-s,0,c]])
    return np.array([[c,-s,0],[s,c,0],[0,0,1]])

def fk(joints, frame):
    """Return dict name->3D world position for one motion frame."""
    pos = {}; T = {}
    for idx, j in enumerate(joints):
        off = np.array(j['offset'])
        R = np.eye(3); t = np.zeros(3)
        for k, ch in enumerate(j['channels']):
            v = frame[j['chan_start']+k]
            if ch.endswith('position'):
                ax = ch[0]; t[{'X':0,'Y':1,'Z':2}[ax]] = v
            else:
                R = R @ rot_mat(ch[0], v)
        if j['parent'] == -1:
            world_pos = off + t
            world_R = R
        else:
            pR, pP = T[j['parent']]
            world_pos = pP + pR @ off
            world_R = pR @ R
        T[idx] = (world_R, world_pos)
        pos[idx] = world_pos
    return pos

# joints we map onto the 2D rig
WANT = {'Hips':'hip','Spine1':'chest','Neck':'neck','Head':'head',
        'LeftArm':'lsh','LeftForeArm':'lel','LeftHand':'lwr',
        'RightArm':'rsh','RightForeArm':'rel','RightHand':'rwr',
        'LeftUpLeg':'lhip','LeftLeg':'lkn','LeftFoot':'lank',
        'RightUpLeg':'rhip','RightLeg':'rkn','RightFoot':'rank'}

def convert(path, yaw, pitch, fps_out, frame0=None, frame1=None):
    joints, data, ftime = parse_bvh(path)
    name_idx = {j['name']: i for i, j in enumerate(joints)}
    src_fps = 1.0/ftime
    step = max(1, round(src_fps/fps_out))
    Ry = rot_mat('Y', yaw); Rx = rot_mat('X', pitch); cam = Rx @ Ry
    f0 = frame0 or 0; f1 = frame1 or len(data)
    out = []
    for fi in range(f0, f1, step):
        p = fk(joints, data[fi])
        # project
        proj = {}
        for nm, key in WANT.items():
            if nm in name_idx:
                v = cam @ p[name_idx[nm]]
                proj[key] = [float(v[0]), float(-v[1]), float(v[2])]  # x, screen-y down, depth
        out.append(proj)
    # normalize: center hips at origin, scale so hip->head ~ 1.0
    hs = []
    for fr in out:
        if 'hip' in fr and 'head' in fr:
            hs.append(math.hypot(fr['head'][0]-fr['hip'][0], fr['head'][1]-fr['hip'][1]))
    scale = 1.0/(np.median(hs) if hs else 1.0)
    norm = []
    for fr in out:
        hx, hy, hz = fr['hip']
        norm.append({k: [round((x-hx)*scale,4), round((y-hy)*scale,4), round((z-hz)*scale,4)] for k,(x,y,z) in fr.items()})
    return dict(fps=fps_out, count=len(norm), frames=norm)

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('inp'); ap.add_argument('out')
    ap.add_argument('--yaw', type=float, default=0); ap.add_argument('--pitch', type=float, default=0)
    ap.add_argument('--fps', type=float, default=24); ap.add_argument('--f0', type=int, default=0); ap.add_argument('--f1', type=int, default=0)
    ap.add_argument('--preview', default=None)
    a = ap.parse_args()
    clip = convert(a.inp, a.yaw, a.pitch, a.fps, a.f0, a.f1 or None)
    json.dump(clip, open(a.out,'w'), separators=(',',':'))
    print(f"{a.inp}: {clip['count']} frames @ {a.fps}fps -> {a.out}")
    if a.preview:
        from PIL import Image, ImageDraw
        n = min(8, clip['count']); step = max(1, clip['count']//n)
        cell=200; sheet=Image.new('RGB',(cell*n,cell*2),(20,20,24)); d=ImageDraw.Draw(sheet)
        BONES=[('hip','chest'),('chest','neck'),('neck','head'),('chest','lsh'),('lsh','lel'),('lel','lwr'),('chest','rsh'),('rsh','rel'),('rel','rwr'),('hip','lhip'),('lhip','lkn'),('lkn','lank'),('hip','rhip'),('rhip','rkn'),('rkn','rank')]
        for c in range(n):
            fr=clip['frames'][c*step]; ox=c*cell+cell//2; oy=cell
            def P(k): return (ox+fr[k][0]*70, oy+fr[k][1]*70)
            for a2,b2 in BONES:
                if a2 in fr and b2 in fr: d.line([P(a2),P(b2)],fill=(230,220,180),width=3)
        sheet.save(a.preview); print('preview', a.preview)
