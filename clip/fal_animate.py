#!/usr/bin/env python3
"""Anima os planos-chave via fal.ai (image-to-video), usando as plates
Higgsfield como start frame.

  python3 clip/fal_animate.py submit s12_crash.jpg   # submete um plano
  python3 clip/fal_animate.py submit --all           # submete todos
  python3 clip/fal_animate.py poll                   # poll + download -> clip/motion/

Chave em /root/.fal_key (nunca impressa). Estado em build/fal_requests.json.
Modelo: Seedance 1.0 Lite 720p 5s (~US$0,18/clipe).
"""
import json, os, sys, time, urllib.request

MODEL = "fal-ai/bytedance/seedance/v1/lite/image-to-video"
QUEUE = f"https://queue.fal.run/{MODEL}"
KEY = open("/root/.fal_key").read().strip()
STATE = "build/fal_requests.json"

PLAN = json.load(open("clip/animate_plan.json"))
JOBS = json.load(open("clip/plates_jobs.json"))
state = json.load(open(STATE)) if os.path.exists(STATE) else {}


def api(url, body=None):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Key {KEY}", "Content-Type": "application/json"})
    data = json.dumps(body).encode() if body is not None else None
    if data:
        req.data = data
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def submit(files):
    for c in PLAN["clips"]:
        if c["file"] not in files:
            continue
        if c["file"] in state and state[c["file"]].get("status") != "failed":
            print("já submetido:", c["file"]); continue
        body = {
            "prompt": c["prompt"],
            "image_url": JOBS[c["file"]]["url"],
            "duration": "5",
            "resolution": "720p",
        }
        r = api(QUEUE, body)
        state[c["file"]] = {"request_id": r["request_id"],
                            "status_url": r["status_url"],
                            "response_url": r["response_url"],
                            "status": "queued"}
        print("submetido:", c["file"], r["request_id"])
    json.dump(state, open(STATE, "w"), indent=1)


def poll():
    os.makedirs("clip/motion", exist_ok=True)
    pending = True
    while pending:
        pending = False
        for f, st in state.items():
            if st.get("status") == "done":
                continue
            try:
                s = api(st["status_url"])
            except Exception as e:
                print(f, "status err:", e); pending = True; continue
            if s.get("status") == "COMPLETED":
                try:
                    res = api(st["response_url"])
                except Exception as e:
                    print(f, "resp err:", e); pending = True; continue
                url = res["video"]["url"]
                out = os.path.join("clip/motion", os.path.splitext(f)[0] + ".mp4")
                urllib.request.urlretrieve(url, out)
                st["status"] = "done"; st["video_url"] = url
                print("BAIXADO:", out, f"({os.path.getsize(out)//1024} KB)")
            elif s.get("status") in ("IN_QUEUE", "IN_PROGRESS"):
                pending = True
            else:
                st["status"] = "failed"; st["detail"] = s
                print("FALHOU:", f, s)
        json.dump(state, open(STATE, "w"), indent=1)
        if pending:
            time.sleep(15)
    print("poll concluído")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "poll"
    if cmd == "submit":
        if "--all" in sys.argv:
            submit([c["file"] for c in PLAN["clips"]])
        else:
            submit(sys.argv[2:])
    else:
        poll()
