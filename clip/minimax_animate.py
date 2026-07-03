#!/usr/bin/env python3
"""Anima plates via MiniMax Hailuo (image-to-video). Chave em /root/.minimax_key.

  python3 clip/minimax_animate.py s12_crash.jpg            # 1 take de teste
  python3 clip/minimax_animate.py --all                    # todos os planos-chave
  python3 clip/minimax_animate.py --list s12_crash.jpg s40_devil.jpg

Fluxo assíncrono: cria task -> poll -> retrieve file_id -> baixa mp4.
Saída: clip/motion/<stem>.mp4  (substitui o clipe LTX no assemble.py).
"""
import base64, json, mimetypes, os, sys, time, urllib.request

KEY = open("/root/.minimax_key").read().strip()
BASE = "https://api.minimax.io/v1"
MODEL = "MiniMax-Hailuo-2.3"
DURATION = 6
RESOLUTION = "1080P"

SB = {s["file"]: s for s in json.load(open("clip/storyboard.json"))["shots"]}
CUR = {c["file"]: c["prompt"] for c in json.load(open("clip/animate_plan.json"))["clips"]}
KEY_SHOTS = [c["file"] for c in json.load(open("clip/animate_plan.json"))["clips"]]


def hdr(json_ct=True):
    h = {"Authorization": f"Bearer {KEY}"}
    if json_ct:
        h["Content-Type"] = "application/json"
    return h


def post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=hdr())
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())


def get(url):
    req = urllib.request.Request(url, headers=hdr(False))
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())


def data_url(path):
    mime = mimetypes.guess_type(path)[0] or "image/jpeg"
    b = base64.b64encode(open(path, "rb").read()).decode()
    return f"data:{mime};base64,{b}"


def prompt_for(f):
    if f in CUR:
        return CUR[f]
    p = SB.get(f, {}).get("prompt", "") or "the anime scene, natural cinematic motion"
    return "anime style, " + p.split("film grain,", 1)[-1].strip()


def animate(f):
    out = os.path.join("clip/motion", os.path.splitext(f)[0] + ".mp4")
    src = os.path.join("clip/shots", f)
    print(f"[{f}] criando task...", flush=True)
    r = post(f"{BASE}/video_generation", {
        "model": MODEL,
        "prompt": prompt_for(f),
        "first_frame_image": data_url(src),
        "duration": DURATION,
        "resolution": RESOLUTION,
    })
    br = r.get("base_resp", {})
    if br.get("status_code") not in (0, None):
        print(f"[{f}] ERRO na criação: {br}"); return False
    task = r["task_id"]
    print(f"[{f}] task {task} — aguardando...", flush=True)
    while True:
        time.sleep(10)
        q = get(f"{BASE}/query/video_generation?task_id={task}")
        st = q.get("status")
        if st == "Success":
            fid = q["file_id"]; break
        if st in ("Fail", "Failed"):
            print(f"[{f}] FALHOU: {q}"); return False
        print(f"[{f}] status={st}", flush=True)
    fr = get(f"{BASE}/files/retrieve?file_id={fid}")
    dl = fr["file"]["download_url"]
    os.makedirs("clip/motion", exist_ok=True)
    urllib.request.urlretrieve(dl, out)
    print(f"[{f}] BAIXADO {out} ({os.path.getsize(out)//1024} KB)", flush=True)
    return True


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--all" in args:
        files = KEY_SHOTS
    elif "--list" in args:
        files = [a for a in args if a != "--list"]
    else:
        files = args or ["s12_crash.jpg"]
    ok = 0
    for f in files:
        try:
            ok += animate(f)
        except Exception as e:
            print(f"[{f}] EXC: {type(e).__name__}: {str(e)[:200]}", flush=True)
    print(f"\n{ok}/{len(files)} animados")
