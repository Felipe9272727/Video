#!/usr/bin/env python3
"""Anima os 55 planos via fal.ai Wan 2.2 I2V-A14B (o 14B forte).
Prompts de movimento reescritos com AÇÃO EXPLÍCITA. Chave em /root/.fal_key.

  python3 clip/fal_wan.py --all           # gera todos (pula os já feitos com este modelo)
  python3 clip/fal_wan.py s12_crash.jpg   # um plano
  python3 clip/fal_wan.py --cost          # estimativa de custo (1 clipe)
"""
import base64, json, mimetypes, os, sys, time, urllib.request

MODEL = "fal-ai/wan/v2.2-a14b/image-to-video"
QUEUE = f"https://queue.fal.run/{MODEL}"
KEY = open("/root/.fal_key").read().strip() if os.path.exists("/root/.fal_key") else ""
NUM_FRAMES = 81
FPS = 24
STEPS = 30
RESOLUTION = "720p"
NEG = ("static, still, frozen, no motion, blurry, low quality, distorted, deformed face, "
       "morphing, flickering, watermark, text, extra limbs, jpeg artifacts")

# AÇÃO explícita por plano (o que DEVE se mexer) — corrige o "sutil demais"
ACTIONS = {
 "s01_cemetery": "the camera slowly cranes forward over the graves, rain pouring, storm clouds churning overhead, trees swaying",
 "s02_funeral_low": "heavy rain pours down, the mourners' black umbrellas tremble in the wind, camera tilts up toward the stormy sky",
 "s03_tombstone": "rain streams down the carved gravestone, water droplets run over the letters, slow push-in",
 "s04_funeral_wide": "wind sweeps the grass and umbrellas, the mourners shift and bow their heads, rain falling, slow dolly-in",
 "s05_shower": "cold water pours down over him, he shivers and hugs himself tightly, water streaming off, slow tilt",
 "s06_bike": "he pedals hard, legs pumping, the bicycle wheels spinning, moving across the frame, hair blown by wind",
 "s07_fishing": "the small boat rocks on the water, ripples spreading out, morning mist drifting, his fishing rod swaying",
 "s08_flag": "the huge american flag ripples and waves in the wind, he stands rigid with hand on chest, god rays shifting",
 "s09_ocean": "the enormous shark shadow glides and rises beneath the waves, foam churning, he stands frozen in terror",
 "s10_rose": "he stiffly pushes the rose forward, his wife slowly turns her head unimpressed, awkward tension, flickering light",
 "s11_questions": "he sweats and shifts nervously, the shadowed faces lean in closer around him, he glances away, tense breathing",
 "s12_crash": "the windshield shatters and glass shards explode toward the camera, he lurches forward screaming, violent camera shake",
 "s13_stairs": "he climbs the golden staircase, clouds drifting and swirling, god rays sweeping, the camera rising with him",
 "s14_pray_topdown": "the mourners sway praying around the open casket, rain falling, candlelight flickering, slow overhead rotation",
 "s15_wave": "he waves goodbye over his shoulder with a smug grin, clouds drifting past, stars twinkling, his coat fluttering",
 "s16_vertigo": "the camera plunges straight down past his shoes toward the tiny earth far below, galaxies swirling, dizzying fall",
 "s17_angel_gate": "the colossal marble angel's wings shift, the camera cranes up the towering figure, god rays pouring, the book glowing",
 "s18_list": "the giant angel finger slides down the glowing list of names, the angel slowly shakes its head no, light pulsing",
 "hero": "he gasps, his eyes widen in devastation, a single tear rolls down his cheek, his mouth trembles, light flickering",
 "s20_no_air": "he clutches his chest gasping for air, the cloud floor cracks open with bursting light beneath him, wind whipping",
 "s21_beg": "he kneels and raises clasped begging hands toward the gates, the radiant light blazing brighter, embers of light floating up",
 "s22_plead_ecu": "he pleads desperately into the camera, tears streaming down, hands gesturing wildly, sweat flying, whole body trembling",
 "s23_church": "he slides into the pew checking his wristwatch, kaleidoscopic stained-glass light shifting across the pews",
 "s24_angels_door": "glowing angels file through the radiant doorway, he screams and pounds against an invisible barrier, reaching desperately",
 "s25_floor_opens": "he falls away from the camera through the breaking cloud floor, arms flailing upward, plunging fast into darkness",
 "s26_fall_storm": "he plummets toward the camera through storm clouds, his suit flapping violently, lightning flashing, screaming",
 "s28_pit": "the camera dives toward the glowing molten pit, he falls into it, smoke and embers spiraling upward fast",
 "s29_hell_gate": "embers stream upward, the molten inscriptions glowing and pulsing, the camera cranes up the colossal black gate",
 "s30_gulp": "he gulps nervously and sweat drips down, his terrified eyes darting, blood-red light flickering, embers drifting past",
 "s31_hellscape": "lava rivers flow, ember storms swirl, chained crowds marching, the camera slowly pans across the vast hellscape",
 "s32_gluttons": "the damned souls writhe and wail at the endless table, demon waiters moving, candle flames flickering",
 "s33_mirrors": "trapped souls claw and scream inside the tall mirrors, he walks warily between them, candlelight flickering",
 "s35_market": "demon merchants gesture at their stalls, caged burning worlds glowing, crowds shuffling through the smoky market",
 "s37_elevator": "the caged elevator descends shaking, sparks flying, the skeletal operator pulling the lever, the bulb flickering",
 "s38_corridor": "he steps out into the endless flame-lit corridor, embers drifting, the camera pushing down the symmetric hall",
 "s39_run_gate": "he sprints hard toward the burning gate, coat flying, embers streaking past, fast camera tracking, anime speed lines",
 "s40_devil": "the devil grins wider and exhales cigar smoke, tapping the throne with his claws, flames flickering, smoke curling up",
 "s41_demon_list": "the demon clerk ticks names in the burning ledger with a fiery quill, looking down menacingly, embers rising",
 "s42_denied": "the clawed fist slams a glowing brand onto the ledger, sparks exploding outward, he flinches back hard",
 "s44_heart_falls": "he drops to his knees clutching his chest gasping, embers swirling around him, blood-red light, long shadow stretching",
 "s45_beg_devil": "he kneels begging, the towering horned devil silhouette leans closer, the wall of fire roaring and rising",
 "s46_uniform": "he desperately tugs his lapels showing his plain suit, demon guards closing in with spears, torchlight flickering, panic",
 "s48_demon_parade": "a parade of demons marches through the burning archway dragging chained souls, he screams with arms spread, ember storm",
 "s49_dragged": "two hulking demon brutes drag him backward, his heels scraping the ash, he struggles and yells, fire wall behind, embers",
 "s50_thrown": "he sprawls on the ash floor, burning papers raining down around him, he pushes himself up weakly, embers drifting",
 "s51_pound_door": "he pounds both fists on the colossal iron door, sparks bursting on each hit, fire glowing through the seams, furious",
 "s53_chase": "he sprints straight at the camera in terror, the demon horde charging behind him, debris flying, the corridor collapsing",
 "s54_they_walk": "he collapses panting on hands and knees, behind him the demons walk slowly out of the shadows, glowing eyes, dread",
 "s56_climb": "he climbs the crumbling black stairs toward the distant shaft of white light, embers falling past like reverse snow",
 "s57_angels_above": "far above at the rim of the light shaft, tiny indifferent angel silhouettes look down, cold light flaring",
 "s59_final_beg": "the camera cranes up as he screams at the sky with tears streaming, the ring of fire flaring higher, embers spiraling up",
 "s60_ash_list": "his trembling fingers clutch the burning ledger as the page crumbles into glowing ash, embers drifting, shallow focus",
 "s61_hand_up": "a single hand reaches up out of the rising flames toward the dying light, embers and smoke swirling upward",
 "s63_last_scream": "he throws his head back screaming as the wall of flame surges and fills the frame, ember blizzard, heat ripple",
 "s64_dissolve": "his dark silhouette dissolves into thousands of glowing embers scattering upward into black smoke, the fire dimming",
}
STYLE = "anime style, {}, strong fluid motion, dynamic cinematic animation, high detail, consistent anime art style"

def prompt_for(stem):
    a = ACTIONS.get(stem, "the scene comes alive with clear cinematic motion")
    return STYLE.format(a)

def hdr():
    return {"Authorization": f"Key {KEY}", "Content-Type": "application/json"}

def post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=hdr())
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())

def get(url):
    req = urllib.request.Request(url, headers=hdr())
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())

def data_url(path):
    mime = mimetypes.guess_type(path)[0] or "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(open(path, "rb").read()).decode()

def animate(fname):
    stem = os.path.splitext(fname)[0]
    out = f"clip/motion/{stem}.mp4"
    body = {
        "prompt": prompt_for(stem),
        "image_url": data_url(f"clip/shots/{fname}"),
        "negative_prompt": NEG,
        "num_frames": NUM_FRAMES, "frames_per_second": FPS,
        "num_inference_steps": STEPS, "resolution": RESOLUTION,
        "enable_safety_checker": False,
    }
    r = post(QUEUE, body)
    rid = r["request_id"]; status_url = r["status_url"]; resp_url = r["response_url"]
    while True:
        time.sleep(8)
        s = get(status_url)
        st = s.get("status")
        if st == "COMPLETED":
            break
        if st in ("FAILED", "ERROR"):
            raise RuntimeError(f"fal {st}: {s}")
    res = get(resp_url)
    url = res["video"]["url"] if isinstance(res.get("video"), dict) else res.get("video")
    os.makedirs("clip/motion", exist_ok=True)
    urllib.request.urlretrieve(url, out)
    return f"ok ({os.path.getsize(out)//1024} KB)"

if __name__ == "__main__":
    args = sys.argv[1:]
    if not KEY:
        print("!! sem /root/.fal_key — cole a API key da fal primeiro"); sys.exit(1)
    if "--all" in args:
        import glob
        files = [os.path.basename(p) for p in sorted(glob.glob("clip/shots/*.jpg"))]
    else:
        files = [a for a in args if a.endswith(".jpg")] or ["s12_crash.jpg"]
    done = 0
    for i, f in enumerate(files, 1):
        t0 = time.time()
        try:
            r = animate(f)
            done += 1
            print(f"[{i}/{len(files)}] {f} {r} ({time.time()-t0:.0f}s)", flush=True)
        except Exception as e:
            print(f"[{i}/{len(files)}] {f} ERRO: {type(e).__name__}: {str(e)[:200]}", flush=True)
            time.sleep(4)
    print(f"\n{done}/{len(files)} animados")
