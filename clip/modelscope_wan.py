#!/usr/bin/env python3
"""Anima os 55 planos via ModelScope API-Inference (Wan 2.2 I2V-A14B) — tier
GRÁTIS (2000 chamadas/dia, sem cartão). Token em /root/.modelscope_key.
Reusa os prompts de AÇÃO explícita de clip/fal_wan.py.

  python3 clip/modelscope_wan.py s12_crash.jpg   # 1 teste (mostra resposta crua)
  python3 clip/modelscope_wan.py --all           # todos
"""
import base64, json, mimetypes, os, sys, time, urllib.request, importlib.util

BASE = "https://api-inference.modelscope.cn"
SUBMIT = BASE + "/v1/images/generations"
MODEL_ID = "Wan-AI/Wan2.2-I2V-A14B"
KEY = open("/root/.modelscope_key").read().strip() if os.path.exists("/root/.modelscope_key") else ""

# reusa ACTIONS/prompt_for do fal_wan.py
_spec = importlib.util.spec_from_file_location("fw", os.path.join(os.path.dirname(__file__), "fal_wan.py"))
_fw = importlib.util.module_from_spec(_spec)
# fal_wan importa nada pesado; mas evita rodar o __main__
_src = open(os.path.join(os.path.dirname(__file__), "fal_wan.py")).read().split("if __name__")[0]
exec(_src, _fw.__dict__)
prompt_for = _fw.prompt_for
NEG = _fw.NEG

def data_url(path):
    mime = mimetypes.guess_type(path)[0] or "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(open(path, "rb").read()).decode()

def req(url, method="GET", body=None, extra=None):
    h = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    if extra: h.update(extra)
    r = urllib.request.Request(url, method=method,
                              data=json.dumps(body).encode() if body is not None else None, headers=h)
    with urllib.request.urlopen(r, timeout=120) as resp:
        return json.loads(resp.read())

def submit(stem, fname):
    body = {"model": MODEL_ID, "prompt": prompt_for(stem),
            "image_url": data_url(f"clip/shots/{fname}"), "negative_prompt": NEG}
    return req(SUBMIT, "POST", body, {"X-ModelScope-Async-Mode": "true"})

def poll(task_id):
    return req(f"{BASE}/v1/tasks/{task_id}", "GET", None, {"X-ModelScope-Task-Type": "image_to_video"})

def find_video_url(d):
    for k in ("output_video_url", "video_url", "output_url"):
        if isinstance(d.get(k), str): return d[k]
    for k in ("output_videos", "videos", "output"):
        v = d.get(k)
        if isinstance(v, list) and v:
            it = v[0]
            return it if isinstance(it, str) else it.get("url") or it.get("video_url")
        if isinstance(v, dict):
            return v.get("url") or v.get("video_url")
    return None

def animate(fname, verbose=False):
    stem = os.path.splitext(fname)[0]; out = f"clip/motion/{stem}.mp4"
    s = submit(stem, fname)
    if verbose: print("SUBMIT resp:", json.dumps(s)[:400])
    task_id = s.get("task_id") or s.get("id") or (s.get("data") or {}).get("task_id")
    if not task_id: raise RuntimeError(f"sem task_id: {s}")
    for _ in range(150):
        time.sleep(6)
        p = poll(task_id)
        st = (p.get("task_status") or p.get("status") or "").upper()
        if st in ("SUCCEED", "SUCCESS", "SUCCEEDED", "FINISHED"):
            url = find_video_url(p) or find_video_url(p.get("output", {}) if isinstance(p.get("output"), dict) else {})
            if verbose: print("DONE resp:", json.dumps(p)[:400])
            if not url: raise RuntimeError(f"sem url no resultado: {json.dumps(p)[:300]}")
            os.makedirs("clip/motion", exist_ok=True)
            urllib.request.urlretrieve(url, out)
            return f"ok ({os.path.getsize(out)//1024} KB)"
        if st in ("FAILED", "FAIL", "ERROR"):
            raise RuntimeError(f"task {st}: {json.dumps(p)[:300]}")
    raise RuntimeError("timeout no poll")

if __name__ == "__main__":
    if not KEY:
        print("!! sem /root/.modelscope_key — cole o token do ModelScope"); sys.exit(1)
    args = sys.argv[1:]
    if "--all" in args:
        import glob
        files = [os.path.basename(p) for p in sorted(glob.glob("clip/shots/*.jpg"))]
    else:
        files = [a for a in args if a.endswith(".jpg")] or ["s12_crash.jpg"]
    done = 0
    for i, f in enumerate(files, 1):
        t0 = time.time()
        try:
            r = animate(f, verbose=(i == 1))
            done += 1
            print(f"[{i}/{len(files)}] {f} {r} ({time.time()-t0:.0f}s)", flush=True)
        except Exception as e:
            print(f"[{i}/{len(files)}] {f} ERRO: {type(e).__name__}: {str(e)[:250]}", flush=True)
            time.sleep(4)
    print(f"\n{done}/{len(files)} animados")
