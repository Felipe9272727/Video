#!/usr/bin/env python3
"""Pipeline MiniMax Hailuo — anima os 55 planos e gera as 31 pontes FLF.

Chave: env MINIMAX_API_KEY ou arquivo /root/.minimax_key
Custo (pay-as-you-go, 768P 6s): clipes $0.28 (Hailuo-2.3) ou $0.19 (--fast);
pontes $0.28 (Hailuo-02, único com primeiro+último frame). Total ~US$19-24.

  python3 clip/hailuo_pipeline.py --dry-run           # valida tudo sem gastar
  python3 clip/hailuo_pipeline.py clips               # anima os 55 planos
  python3 clip/hailuo_pipeline.py clips --fast        # idem c/ Hailuo-2.3-Fast
  python3 clip/hailuo_pipeline.py clips --only s12_crash s40_devil
  python3 clip/hailuo_pipeline.py bridges             # pontes (rodar APÓS clips)
  python3 clip/hailuo_pipeline.py --status            # progresso

Resumável: estado em build/hailuo_state.json — pode interromper e rodar de
novo, só o que falta é (re)submetido. Saída: clip/motion/*.mp4, clip/bridges/*.mp4.
Depois: python3 clip/assemble.py  ->  out/charlie_inferno_cinematic.mp4
"""
import base64, json, os, subprocess, sys, time, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

BASE = "https://api.minimax.io/v1"
STATE_F = "build/hailuo_state.json"
POLL_S = 15          # intervalo de poll (s)
SUBMIT_GAP = 13      # ~4.6 req/min: abaixo de qualquer RPM do free/PAYG
PRICE = {"MiniMax-Hailuo-2.3": 0.28, "MiniMax-Hailuo-2.3-Fast": 0.19, "MiniMax-Hailuo-02": 0.28}

CLIPS = json.load(open("clip/hailuo_prompts.json"))
BRIDGES = json.load(open("clip/direction/bridge_plan.json"))
SB = {s["file"]: s for s in json.load(open("clip/storyboard.json"))["shots"]}
SB_STEM = {os.path.splitext(s["file"])[0]: s for s in json.load(open("clip/storyboard.json"))["shots"]}


def api_key():
    k = os.environ.get("MINIMAX_API_KEY", "").strip()
    if not k and os.path.exists("/root/.minimax_key"):
        k = open("/root/.minimax_key").read().strip()
    if not k:
        sys.exit("Sem chave: export MINIMAX_API_KEY=... (ou /root/.minimax_key)")
    return k


def req(url, body=None, key=None):
    h = {"Authorization": f"Bearer {key}"}
    if body is not None:
        h["Content-Type"] = "application/json"
        body = json.dumps(body).encode()
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=h),
                                        timeout=120) as r:
                out = json.loads(r.read())
            code = out.get("base_resp", {}).get("status_code", 0)
            if code == 1002:                       # rate limit
                time.sleep(20 * (attempt + 1)); continue
            return out
        except urllib.error.URLError as e:
            if attempt == 4:
                raise
            time.sleep(5 * (attempt + 1))
    return out


def data_url(path):
    ext = os.path.splitext(path)[1].lstrip(".").lower().replace("jpg", "jpeg")
    return f"data:image/{ext};base64," + base64.b64encode(open(path, "rb").read()).decode()


def load_state():
    if os.path.exists(STATE_F):
        return json.load(open(STATE_F))
    return {}


def save_state(st):
    os.makedirs("build", exist_ok=True)
    json.dump(st, open(STATE_F, "w"), indent=1)


def ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"


# --------------------------------------------------------------- frames p/ FLF
def seam_frame(stem, which):
    """Frame de emenda da ponte: último ('last') ou primeiro ('first') frame do
    clipe de movimento do plano; cai pra plate se o clipe não existe ainda.
    Respeita flip dos planos reusados (o frame precisa bater com o que aparece
    na tela, senão a ponte 'pula')."""
    s = SB_STEM[stem]
    src = s.get("src") or s["file"]
    flip = bool(s.get("flip"))
    out = f"build/seam/{stem}_{which}.jpg"
    os.makedirs("build/seam", exist_ok=True)
    mp4 = "clip/motion/" + os.path.splitext(src)[0] + ".mp4"
    ff = ffmpeg()
    vf = "hflip," if flip else ""
    if os.path.exists(mp4) and os.path.getsize(mp4) > 150000:
        pos = ["-sseof", "-0.15"] if which == "last" else []
        subprocess.run([ff, "-loglevel", "error", *pos, "-i", mp4,
                        "-vf", vf + "scale=1280:-2", "-frames:v", "1", "-q:v", "3",
                        "-y", out], check=True)
    else:
        subprocess.run([ff, "-loglevel", "error", "-i", f"clip/shots/{src}",
                        "-vf", vf + "scale=1280:-2", "-frames:v", "1", "-q:v", "3",
                        "-y", out], check=True)
    return out


# --------------------------------------------------------------- jobs
def clip_jobs(only=None, fast=False):
    model = "MiniMax-Hailuo-2.3-Fast" if fast else CLIPS.get("model", "MiniMax-Hailuo-2.3")
    jobs = []
    for c in CLIPS["clips"]:
        stem = os.path.splitext(c["file"])[0]
        if only and stem not in only:
            continue
        jobs.append({
            "id": "clip:" + stem,
            "out": f"clip/motion/{stem}.mp4",
            "body": {"model": model, "prompt": c["prompt"],
                     "first_frame_image": lambda p=f"clip/shots/{c['file']}": data_url(p),
                     "duration": CLIPS.get("duration", 6),
                     "resolution": CLIPS.get("resolution", "768P"),
                     "prompt_optimizer": CLIPS.get("prompt_optimizer", False)},
        })
    return jobs


def bridge_jobs(only=None):
    jobs = []
    for br in BRIDGES["bridges"]:
        bid = f"{br['a']}__{br['b']}"
        if only and bid not in only:
            continue
        jobs.append({
            "id": "bridge:" + bid,
            "out": f"clip/bridges/{bid}.mp4",
            "body": {"model": BRIDGES.get("model", "MiniMax-Hailuo-02"),
                     "prompt": br["prompt"],
                     "first_frame_image": lambda a=br["a"]: data_url(seam_frame(a, "last")),
                     "last_frame_image": lambda b=br["b"]: data_url(seam_frame(b, "first")),
                     "duration": BRIDGES.get("duration", 6),
                     "resolution": BRIDGES.get("resolution", "768P"),
                     "prompt_optimizer": BRIDGES.get("prompt_optimizer", False)},
        })
    return jobs


# --------------------------------------------------------------- fases
def materialize(body):
    return {k: (v() if callable(v) else v) for k, v in body.items()}


def run(jobs, key):
    st = load_state()
    pend = [j for j in jobs
            if not (os.path.exists(j["out"]) and os.path.getsize(j["out"]) > 150000)]
    print(f"{len(jobs)} jobs, {len(jobs)-len(pend)} prontos, {len(pend)} a fazer")
    # 1) submete o que ainda não tem task viva
    for j in pend:
        e = st.get(j["id"], {})
        if e.get("task_id") and e.get("status") not in ("Fail", "Failed"):
            continue
        r = req(f"{BASE}/video_generation", materialize(j["body"]), key)
        br = r.get("base_resp", {})
        if br.get("status_code") not in (0, None):
            print(f"[{j['id']}] ERRO submit: {br}")
            if br.get("status_code") == 1008:
                sys.exit("Saldo insuficiente na conta MiniMax — recarregue e rode de novo.")
            continue
        st[j["id"]] = {"task_id": r["task_id"], "status": "submitted", "out": j["out"]}
        save_state(st)
        print(f"[{j['id']}] task {r['task_id']}")
        time.sleep(SUBMIT_GAP)
    # 2) poll + download
    while True:
        waiting = 0
        for j in pend:
            e = st.get(j["id"], {})
            if not e.get("task_id") or e.get("status") == "done":
                continue
            if os.path.exists(j["out"]) and os.path.getsize(j["out"]) > 150000:
                e["status"] = "done"; save_state(st); continue
            q = req(f"{BASE}/query/video_generation?task_id={e['task_id']}", key=key)
            stt = q.get("status")
            if stt == "Success":
                fr = req(f"{BASE}/files/retrieve?file_id={q['file_id']}", key=key)
                os.makedirs(os.path.dirname(j["out"]), exist_ok=True)
                urllib.request.urlretrieve(fr["file"]["download_url"], j["out"])
                e["status"] = "done"; save_state(st)
                print(f"[{j['id']}] OK {os.path.getsize(j['out'])//1024} KB")
            elif stt in ("Fail", "Failed"):
                e["status"] = "Fail"; save_state(st)
                print(f"[{j['id']}] FALHOU: {q.get('base_resp')}")
            else:
                waiting += 1
        if not waiting:
            break
        print(f"... {waiting} em processamento")
        time.sleep(POLL_S)
    done = sum(1 for j in jobs if os.path.exists(j["out"]) and os.path.getsize(j["out"]) > 150000)
    print(f"\n{done}/{len(jobs)} concluídos")


def dry_run(fast=False):
    errs = []
    for c in CLIPS["clips"]:
        p = f"clip/shots/{c['file']}"
        if not os.path.exists(p):
            errs.append("plate ausente: " + p)
        if not (30 < len(c["prompt"]) <= 2000):
            errs.append("prompt fora do limite: " + c["file"])
    for br in BRIDGES["bridges"]:
        for stm in (br["a"], br["b"]):
            if stm not in SB_STEM:
                errs.append("stem fora do storyboard: " + stm)
        if len(br["prompt"]) > 2000:
            errs.append("prompt de ponte longo: " + br["a"])
    # testa extração de frame de emenda (ffmpeg ok? flip ok?)
    try:
        f = seam_frame(BRIDGES["bridges"][0]["a"], "last")
        assert os.path.getsize(f) > 5000
    except Exception as e:
        errs.append(f"seam_frame falhou: {e}")
    n_c, n_b = len(CLIPS["clips"]), len(BRIDGES["bridges"])
    mc = "MiniMax-Hailuo-2.3-Fast" if fast else CLIPS["model"]
    cost = n_c * PRICE[mc] + n_b * PRICE[BRIDGES["model"]]
    print(f"clipes: {n_c} × {mc} 768P 6s = ${n_c*PRICE[mc]:.2f}")
    print(f"pontes: {n_b} × {BRIDGES['model']} 768P 6s = ${n_b*PRICE[BRIDGES['model']]:.2f}")
    print(f"TOTAL ESTIMADO: ${cost:.2f}")
    if errs:
        print("\nPROBLEMAS:"); [print(" -", e) for e in errs]; sys.exit(1)
    print("dry-run OK — tudo validado, pronto pra gerar.")


def status():
    st = load_state()
    for phase, jobs in (("clips", clip_jobs()), ("bridges", bridge_jobs())):
        done = sum(1 for j in jobs if os.path.exists(j["out"]) and os.path.getsize(j["out"]) > 150000)
        live = sum(1 for j in jobs if st.get(j["id"], {}).get("status") == "submitted")
        print(f"{phase}: {done}/{len(jobs)} prontos, {live} na fila MiniMax")


if __name__ == "__main__":
    a = sys.argv[1:]
    fast = "--fast" in a
    only = None
    if "--only" in a:
        only = set(a[a.index("--only") + 1:])
    if "--dry-run" in a:
        dry_run(fast)
    elif "--status" in a:
        status()
    elif a and a[0] == "clips":
        run(clip_jobs(only, fast), api_key())
    elif a and a[0] == "bridges":
        run(bridge_jobs(only), api_key())
    else:
        print(__doc__)
