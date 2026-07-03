#!/usr/bin/env python3
"""Vigia: emite 'SEGMENT_READY <X>' quando todos os clipes Wan daquele segmento
existem, pra disparar um agente revisor. Emite 'ALL_SEGMENTS_READY' no fim."""
import json, os, sys, time

segs = {s: [sh["file"] for sh in json.load(open(f"clip/direction/segment_{s}.json"))["shots"]]
        for s in "ABCDE"}
def clip_ok(f):
    p = "clip/motion/" + os.path.splitext(f)[0] + ".mp4"
    return os.path.exists(p) and os.path.getsize(p) > 300000
def ready(files):
    return all(clip_ok(f) for f in files)

ann = set()
while len(ann) < 5:
    for s in "ABCDE":
        if s not in ann and ready(segs[s]):
            print("SEGMENT_READY " + s, flush=True)
            ann.add(s)
    if len(ann) < 5:
        time.sleep(45)
print("ALL_SEGMENTS_READY", flush=True)
