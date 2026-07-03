#!/usr/bin/env python3
"""Gera INSERTS complementares em estilo anime (grátis, Pollinations/FLUX — sem key,
sem tocar na quota ZeroGPU do Wan). NÃO refaz as plates: só adiciona técnicas
clássicas de episódio anime — title card, impact frames (speed lines / manga),
eyecatch — que o assemble.py encaixa em beats-chave. Saída: clip/inserts/<name>.jpg

  python3 clip/anime_inserts.py            # gera os que faltam
  python3 clip/anime_inserts.py --force    # regenera todos
"""
import os, sys, time, urllib.parse, urllib.request

OUT = "clip/inserts"
os.makedirs(OUT, exist_ok=True)

# estética anime forte e coerente com o clipe (seinen sombrio, cel-shaded)
BASE = ("dark seinen anime, cel shaded, bold clean linework, dramatic chiaroscuro, "
        "high contrast, cinematic composition, moody color grade, 2D anime key art")

# name -> (prompt específico, seed)
INSERTS = {
    # abertura: key visual do episódio (o texto do título entra por cima no assemble)
    "title_card": ("epic anime key visual, lone man in a black suit seen from behind, tiny before "
                   "colossal molten hell gates, rivers of lava, ember storm, towering angel statue "
                   "far above in cold light, heaven above and inferno below split composition, awe and dread",
                   11),
    # impact frames — quadros de impacto (curtos, alta energia)
    "impact_crash":  ("anime impact frame, exploding shattered windshield glass shards bursting toward viewer, "
                      "radial speed lines, motion smear, stark black and white with a slash of red, manga screentone",
                      21),
    "impact_denied": ("anime impact frame, a fiery clawed hand slamming a glowing brand stamp, sparks exploding "
                      "outward, radial speed lines, dramatic red and black, manga ink splash, screentone dots",
                      22),
    "impact_fall":   ("anime impact frame, tiny silhouette of a screaming man plummeting head-first into a fiery "
                      "abyss, strong radial speed lines converging, ember streaks, vertigo, red and black inferno",
                      23),
    "impact_scream": ("anime impact frame extreme rage, a screaming silhouette head thrown back, a towering wall "
                      "of flame surging up behind, radial speed lines, ember blizzard, heat ripple, red black gold",
                      24),
    # eyecatch de meio de episódio
    "eyecatch": ("anime episode eyecatch card, minimalist dramatic, a single black suited silhouette standing on "
                 "a thin line between a cold pale heaven above and a burning red inferno below, negative space",
                 31),
}

STYLE_SUFFIX = ", " + BASE
W, H = 1280, 720

def url_for(prompt, seed):
    p = urllib.parse.quote(prompt + STYLE_SUFFIX)
    return (f"https://image.pollinations.ai/prompt/{p}"
            f"?width={W}&height={H}&nologo=true&model=flux&seed={seed}&enhance=true")

def fetch(name, prompt, seed):
    out = os.path.join(OUT, name + ".jpg")
    url = url_for(prompt, seed)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    if len(data) < 8000:
        raise RuntimeError(f"resposta curta ({len(data)}B)")
    open(out, "wb").write(data)
    return f"ok ({len(data)//1024} KB)"

if __name__ == "__main__":
    force = "--force" in sys.argv
    done = 0
    for name, (prompt, seed) in INSERTS.items():
        out = os.path.join(OUT, name + ".jpg")
        if os.path.exists(out) and not force:
            print(f"{name:16s} skip"); continue
        for attempt in range(3):
            t0 = time.time()
            try:
                r = fetch(name, prompt, seed)
                print(f"{name:16s} {r} ({time.time()-t0:.0f}s)", flush=True); done += 1
                break
            except Exception as e:
                print(f"{name:16s} tent{attempt+1} ERRO: {type(e).__name__}: {str(e)[:120]}", flush=True)
                time.sleep(4)
    print(f"\n{done} inserts gerados -> {OUT}/")
