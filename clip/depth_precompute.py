#!/usr/bin/env python3
"""Pré-calcula mapas de profundidade (Depth-Anything V2 small, ONNX/CPU) para
cada plate. Saída: build/depth/<stem>.png (uint8, claro=perto). ~0.7s/imagem."""
import glob, json, os
import numpy as np
import onnxruntime as ort
from PIL import Image

MODEL = "build/models/depth_small.onnx"
os.makedirs("build/depth", exist_ok=True)
sess = ort.InferenceSession(MODEL, providers=["CPUExecutionProvider"])
INP = sess.get_inputs()[0].name
MEAN = np.array([0.485, 0.456, 0.406], np.float32)
STD = np.array([0.229, 0.224, 0.225], np.float32)

def depth(path, out, longside=960):
    im = Image.open(path).convert("RGB")
    W, H = im.size
    S = 518
    x = np.asarray(im.resize((S, S), Image.BILINEAR)).astype(np.float32) / 255.0
    x = np.transpose((x - MEAN) / STD, (2, 0, 1))[None]
    d = np.array(sess.run(None, {INP: x})[0]).squeeze()
    d = (d - d.min()) / (d.max() - d.min() + 1e-9)
    # resize de volta ao aspecto do plate, limitando o lado maior
    scale = longside / max(W, H)
    ow, oh = int(W * scale), int(H * scale)
    Image.fromarray((d * 255).astype(np.uint8)).resize((ow, oh), Image.BILINEAR).save(out)

if __name__ == "__main__":
    plates = sorted(glob.glob("clip/shots/*.jpg"))
    for i, p in enumerate(plates, 1):
        stem = os.path.splitext(os.path.basename(p))[0]
        out = f"build/depth/{stem}.png"
        if os.path.exists(out):
            print(f"[{i}/{len(plates)}] {stem} skip"); continue
        depth(p, out)
        print(f"[{i}/{len(plates)}] {stem} ok", flush=True)
    print("depth pronto")
