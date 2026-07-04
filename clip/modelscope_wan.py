#!/usr/bin/env python3
"""Anima os 55 planos via ModelScope API-Inference (Wan 2.2 I2V-A14B) — tier
GRÁTIS (2000 chamadas/dia, sem cartão). Token: env MODELSCOPE_KEY ou
/root/.modelscope_key (conta gratuita em modelscope.cn -> Access Token).

Usa os prompts revisados de clip/hailuo_prompts.json (direção + QC), com os
comandos de câmera [Push in]/[Truck left]/... convertidos pra linguagem
natural que o Wan entende. Resumável: pula clipes já baixados.

  python3 clip/modelscope_wan.py s12_crash.jpg   # 1 teste (resposta crua)
  python3 clip/modelscope_wan.py --all           # todos os 55 (paralelo x4)
  python3 clip/modelscope_wan.py --status        # progresso
"""
import base64, json, mimetypes, os, re, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

BASE = os.environ.get("MODELSCOPE_BASE", "https://api-inference.modelscope.ai")
MODEL_ID = "Wan-AI/Wan2.2-I2V-A14B"
PAR = 4            # tasks simultâneas (gentil com o tier grátis)
NEG = ("worst quality, static, still image, blurred, distorted, watermark, "
       "text, subtitles, extra limbs, deformed face, flickering, morphing, 3d render")

KEY = os.environ.get("MODELSCOPE_KEY", "").strip()
if not KEY and os.path.exists("/root/.modelscope_key"):
    KEY = open("/root/.modelscope_key").read().strip()

CLIPS = {c["file"]: c for c in json.load(open("clip/hailuo_prompts.json"))["clips"]}

# comandos Hailuo -> linguagem natural pro Wan
CMD_NL = {"Push in": "camera slowly pushes in", "Pull out": "camera slowly pulls back",
          "Truck left": "camera trucks left", "Truck right": "camera trucks right",
          "Pan left": "camera pans left", "Pan right": "camera pans right",
          "Pedestal up": "camera rises", "Pedestal down": "camera lowers",
          "Tilt up": "camera tilts up", "Tilt down": "camera tilts down",
          "Zoom in": "camera zooms in", "Zoom out": "camera zooms out",
          "Shake": "handheld camera shake", "Tracking shot": "tracking shot",
          "Static shot": "locked static camera"}


def wan_prompt(fname):
    p = CLIPS[fname]["prompt"]
    def sub(m):
        parts = [CMD_NL.get(x.strip(), x.strip().lower()) for x in m.group(1).split(",")]
        return ", ".join(parts) + ","
    return re.sub(r"\[([^\]]+)\]", sub, p)


def data_url(path):
    mime = mimetypes.guess_type(path)[0] or "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(open(path, "rb").read()).decode()


def req(url, method="GET", body=None, extra=None):
    h = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    if extra:
        h.update(extra)
    r = urllib.request.Request(url, method=method,
                               data=json.dumps(body).encode() if body is not None else None,
                               headers=h)
    for att in range(4):
        try:
            with urllib.request.urlopen(r, timeout=120) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 429:                       # rate limit do tier grátis
                time.sleep(30 * (att + 1)); continue
            raise
    raise RuntimeError("rate limit persistente")


def submit(fname):
    body = {"model": MODEL_ID, "prompt": wan_prompt(fname),
            "image_url": data_url(f"clip/shots/{fname}"), "negative_prompt": NEG}
    s = req(BASE + "/v1/images/generations", "POST", body, {"X-ModelScope-Async-Mode": "true"})
    tid = s.get("task_id") or s.get("id") or (s.get("data") or {}).get("task_id")
    if not tid:
        raise RuntimeError(f"sem task_id: {json.dumps(s)[:300]}")
    return tid


def poll(task_id):
    return req(f"{BASE}/v1/tasks/{task_id}", "GET", None,
               {"X-ModelScope-Task-Type": "image_to_video"})


def find_video_url(d):
    for k in ("output_video_url", "video_url", "output_url"):
        if isinstance(d.get(k), str):
            return d[k]
    for k in ("output_videos", "videos", "output"):
        v = d.get(k)
        if isinstance(v, list) and v:
            it = v[0]
            return it if isinstance(it, str) else it.get("url") or it.get("video_url")
        if isinstance(v, dict):
            u = v.get("url") or v.get("video_url") or find_video_url(v)
            if u:
                return u
    return None


def out_path(fname):
    return "clip/motion/" + os.path.splitext(fname)[0] + ".mp4"


def done(fname):
    return os.path.exists(out_path(fname)) and os.path.getsize(out_path(fname)) > 150000


def run(files, verbose=False):
    os.makedirs("clip/motion", exist_ok=True)
    todo = [f for f in files if not done(f)]
    print(f"{len(files)} planos, {len(files)-len(todo)} prontos, {len(todo)} a animar")
    live = {}                                   # fname -> task_id
    ok = err = 0
    while todo or live:
        while todo and len(live) < PAR:
            f = todo.pop(0)
            try:
                live[f] = submit(f)
                print(f"[{f}] task {live[f]}", flush=True)
            except Exception as e:
                err += 1
                print(f"[{f}] ERRO submit: {str(e)[:200]}", flush=True)
            time.sleep(3)
        time.sleep(8)
        for f, tid in list(live.items()):
            try:
                p = poll(tid)
            except Exception as e:
                print(f"[{f}] poll err: {str(e)[:120]}", flush=True); continue
            st = (p.get("task_status") or p.get("status") or "").upper()
            if st in ("SUCCEED", "SUCCESS", "SUCCEEDED", "FINISHED"):
                url = find_video_url(p) or find_video_url(
                    p.get("output", {}) if isinstance(p.get("output"), dict) else {})
                if verbose:
                    print("DONE resp:", json.dumps(p)[:400])
                if url:
                    urllib.request.urlretrieve(url, out_path(f))
                    ok += 1
                    print(f"[{f}] OK {os.path.getsize(out_path(f))//1024} KB", flush=True)
                else:
                    err += 1
                    print(f"[{f}] sem url: {json.dumps(p)[:200]}", flush=True)
                del live[f]
            elif st in ("FAILED", "FAIL", "ERROR"):
                err += 1
                print(f"[{f}] FALHOU: {json.dumps(p)[:200]}", flush=True)
                del live[f]
    print(f"\n{ok} animados, {err} erros")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--status" in args:
        allf = sorted(CLIPS)
        print(f"{sum(done(f) for f in allf)}/{len(allf)} clipes prontos em clip/motion/")
        sys.exit(0)
    if not KEY:
        sys.exit("!! sem token: export MODELSCOPE_KEY=... (ou /root/.modelscope_key)\n"
                 "   Conta gratuita: modelscope.cn -> perfil -> Access Tokens")
    if "--all" in args:
        run(sorted(CLIPS))
    else:
        files = [a for a in args if a.endswith(".jpg")] or ["s12_crash.jpg"]
        run(files, verbose=True)
