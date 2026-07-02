#!/usr/bin/env python3
"""Charlie's Inferno — direção cena a cena.

Um plano por verso da letra oficial (clip/letra_oficial.vtt, legendas do
próprio autor do cover). Cada shot tem: janela de tempo, prompt Higgsfield
(z_image, anime 16:9), câmera (push/pull/pan/dutch/crash-zoom), fx e
transição. Shots com "src" reutilizam a plate de outro shot com câmera nova.

Emite clip/storyboard.json (consumido por assemble.py) e clip/prompts.json
(fila de geração).
"""
import json

STYLE = ("dark cinematic anime film still, hand-painted cel-shaded 2D animation, "
         "bold clean lineart, gritty seinen anime feature film aesthetic, "
         "moody chiaroscuro lighting, detailed painted background, film grain")
CH = ("a gaunt pale anime man in his 40s, sharp angular face, short slicked-back "
      "dark hair, sunken expressive eyes, rumpled charcoal-gray suit, white shirt, "
      "loosened crimson red tie")
DEVIL = ("an elegant tall devil in a black pinstripe suit, dark red skin, slick "
         "curved horns, wide charming predatory grin, glowing amber eyes")

S = []
def shot(t0, t1, file, prompt=None, src=None, cam=None, fx=None, tin="cut",
         tout=None, shake=0.0, kick=0.35, tint=None, flip=False, aberr=0.6, flash=0.5):
    S.append(dict(t0=t0, t1=t1, file=file, prompt=prompt, src=src,
                  cam=cam or dict(z=[1.06, 1.2], c0=[0.5, 0.5], c1=[0.5, 0.5], rot=[0, 0], ease="io"),
                  fx=fx or [], **{"in": tin}, out=tout, shake=shake, kick=kick,
                  tint=tint, flip=flip, aberr=aberr, flash=flash))

def cam(z0, z1, x0=.5, y0=.5, x1=.5, y1=.5, r0=0, r1=0, ease="io"):
    return dict(z=[z0, z1], c0=[x0, y0], c1=[x1, y1], rot=[r0, r1], ease=ease)

# ============================== INTRO (instrumental) ==============================
shot(0.0, 6.2, "s01_cemetery.jpg",
     f"{STYLE}, wide establishing shot of a rainy hillside cemetery at dusk, crooked leafless trees, "
     "rows of old tombstones, a distant gray american suburb below, heavy storm clouds, cold blue-gray palette, rain streaks",
     cam=cam(1.05, 1.2, .5, .45, .5, .55), fx=["rain"], shake=0.15, tin="dip")

shot(6.2, 11.44, "s02_funeral_low.jpg",
     f"{STYLE}, extreme low angle from the wet grass looking up at a row of mourners holding black umbrellas "
     "against a stormy sky, silhouettes, one open grave in the foreground, rain falling toward camera, dramatic dutch angle",
     cam=cam(1.1, 1.28, .5, .55, .5, .45, r0=-3, r1=1), fx=["rain"], shake=0.2)

# "Aqui jaz Charlie"
shot(11.44, 14.31, "s03_tombstone.jpg",
     f"{STYLE}, dramatic extreme close-up of a granite tombstone engraved with the name CHARLIE in bold letters, "
     "rain dripping down the carved letters, wilted flowers at the base, cold gray light, shallow depth of field",
     cam=cam(1.22, 1.06, ease="out"), fx=["rain"], tin="cut", shake=0.1)

# "Dá para notar que é ele porque colocamos o nome dele na lápide" (deadpan)
shot(14.31, 17.92, "s04_funeral_wide.jpg",
     f"{STYLE}, perfectly symmetrical wide shot from behind a tombstone, a small bored funeral crowd with black "
     "umbrellas staring blankly at the grave, flat deadpan composition, rainy gray cemetery, dark comedy mood",
     cam=cam(1.07, 1.07), fx=["rain"], shake=0.0, kick=0.15)

# ============================== VERSO 1 — a vida "correta" ==============================
shot(17.92, 21.12, "s05_shower.jpg",
     f"{STYLE}, extreme top-down overhead angle of {CH} shivering under a cold shower fully miserable, "
     "arms crossed, teal-blue palette, single dim lightbulb, cramped tiled bathroom, steam-less freezing water",
     cam=cam(1.12, 1.3, r0=2, r1=-2), shake=0.25, tin="flash")

shot(21.12, 24.66, "s06_bike.jpg",
     f"{STYLE}, extreme low angle from the asphalt, {CH} pedaling an old rusty bicycle to work at dawn, "
     "front wheel huge in foreground, gray suburb, a gas station sign with high prices behind him, overcast morning",
     cam=cam(1.1, 1.3, .42, .5, .58, .48), shake=0.4, kick=0.5)

shot(24.66, 27.79, "s07_fishing.jpg",
     f"{STYLE}, wide symmetric shot of a tiny rowboat on a vast flat gray lake at dawn, {CH} fishing alone "
     "with a stern judgmental scowl, morning mist, muted colors, lonely mood",
     cam=cam(1.06, 1.18, .5, .48, .5, .52), shake=0.1)

shot(27.79, 31.36, "s08_flag.jpg",
     f"{STYLE}, heroic worm's-eye low angle of {CH} with hand solemnly on his chest pledging to a large american "
     "flag waving on a suburban porch, exaggerated patriotic pose, morning god rays, slightly mocking grandeur",
     cam=cam(1.1, 1.26, .5, .55, .5, .45, r0=-2, r1=2), fx=["rays"], kick=0.5)

shot(31.36, 34.4, "s09_ocean.jpg",
     f"{STYLE}, very high aerial angle looking down at {CH} standing stiff in his suit at the edge of a dark "
     "vast ocean shoreline, a huge ominous shark shadow beneath the waves, he looks terrified, tiny figure, foam lines",
     cam=cam(1.08, 1.26, .45, .5, .55, .5, r0=3, r1=-2), shake=0.2)

shot(34.4, 37.84, "s10_rose.jpg",
     f"{STYLE}, flat frontal deadpan tableau in a gloomy fluorescent kitchen, {CH} stiffly handing a single rose "
     "and a greeting card to his unimpressed deadpan wife in an apron, awkward silence, dark comedy framing",
     cam=cam(1.07, 1.1), shake=0.0, kick=0.15)

shot(37.84, 41.21, "s11_questions.jpg",
     f"{STYLE}, tense dutch angle close-up at a dark dinner table, {CH} sweating and looking away while "
     "shadowed faces lean in around him, harsh single overhead lamp, noir interrogation mood, high contrast",
     cam=cam(1.1, 1.3, .45, .5, .55, .5, r0=-6, r1=-2), shake=0.35)

# "Bateu o carro, infartou, morreu sem nem notar"
shot(41.21, 44.68, "s12_crash.jpg",
     f"{STYLE}, frozen instant of a violent car crash at night, {CH} shocked face seen through the shattering "
     "windshield, glass shards suspended mid-air, headlights flaring, extreme dramatic angle, speed lines, high impact",
     cam=cam(1.32, 1.06, ease="outc"), tin="flash", shake=0.8, kick=1.0, aberr=1.2, flash=0.9)

# ============================== SUBIDA ==============================
shot(44.68, 47.75, "s13_stairs.jpg",
     f"{STYLE}, a colossal golden staircase spiraling up through towering sunset clouds, a tiny soul of {CH} "
     "ascending, god rays bursting between clouds, awe-inspiring scale, warm gold and white palette",
     cam=cam(1.08, 1.26, .5, .6, .5, .4), fx=["rays"], tin="dip", shake=0.1)

shot(47.75, 50.92, "s14_pray_topdown.jpg",
     f"{STYLE}, extreme god's-eye top-down shot directly above a funeral, an open casket with {CH} lying in it, "
     "a perfect ring of mourners with black umbrellas praying around it, wet grass, geometric composition",
     cam=cam(1.1, 1.24, r0=-4, r1=4), fx=["rain_lite"], shake=0.1)

shot(50.92, 53.95, "s15_wave.jpg",
     f"{STYLE}, low angle behind {CH} standing smug on a cloud ledge, waving goodbye down at the tiny earth below, "
     "cocky grin over his shoulder, divine light rim, stars appearing, warm gold clouds",
     cam=cam(1.08, 1.22, .5, .55, .5, .45), fx=["rays"], kick=0.4)

shot(53.95, 57.42, "s16_vertigo.jpg",
     f"{STYLE}, vertigo shot looking straight down past {CH}'s shoes standing on transparent starlight, "
     "the earth a tiny marble far below between his feet, swirling galaxies and divine light around, dizzying scale",
     cam=cam(1.3, 1.07, r0=5, r1=-3, ease="out"), fx=["rays"], shake=0.15)

shot(57.42, 60.89, "s17_angel_gate.jpg",
     f"{STYLE}, extreme worm's-eye angle of a colossal marble angel with enormous glowing wings standing at "
     "towering golden gates, holding a giant open ledger book, cold indifferent face, tiny {CH} at the base looking up, god rays",
     cam=cam(1.1, 1.3, .5, .6, .5, .35), fx=["rays"], kick=0.5)

shot(60.89, 64.03, "s18_list.jpg",
     f"{STYLE}, over-the-shoulder close-up of a giant marble angel finger sliding down a glowing ledger page of "
     "names, none highlighted, the angel's cold face slowly shaking no, {CH} reflected small in the ledger's gold trim",
     cam=cam(1.12, 1.32, .5, .45, .45, .55), shake=0.2)

# "Seu coração caiu" — retrato-âncora (já gerado)
shot(64.03, 67.1, "hero.jpg",
     cam=cam(1.05, 1.35, .5, .42, .5, .42, ease="io"), tin="cut", shake=0.3, kick=0.6)

shot(67.1, 70.8, "s20_no_air.jpg",
     f"{STYLE}, high angle of {CH} doubled over clutching his chest gasping, the cloud floor beneath him cracking "
     "open with blinding light shafts bursting through the cracks, wind-blown, despair, white-gold turning cold",
     cam=cam(1.1, 1.32, .5, .45, .5, .55, r0=3, r1=-4), fx=["rays"], shake=0.5, kick=0.7)

# ============================== REFRÃO 1 (celestial) ==============================
shot(70.8, 73.67, "s21_beg.jpg",
     f"{STYLE}, dramatic silhouette low angle behind {CH} on his knees with clasped begging hands raised toward "
     "the towering radiant golden gates, blinding divine backlight, long shadow toward camera, embers of light floating",
     cam=cam(1.08, 1.3, .5, .55, .5, .45), fx=["rays"], tin="flash", kick=0.8, shake=0.3)

shot(73.67, 76.88, "s22_plead_ecu.jpg",
     f"{STYLE}, extreme close-up of {CH} pleading desperately, exaggerated anime despair, huge glassy tearful eyes, "
     "gritted teeth, sweat drops flying, hands gesturing wildly toward camera, cold divine light, high emotion",
     cam=cam(1.28, 1.08, ease="outc"), kick=0.9, shake=0.45, aberr=0.9)

shot(76.88, 80.51, "s23_church.jpg",
     f"{STYLE}, warm flashback memory, tilted frame of {CH} sliding late into a church pew checking his wristwatch, "
     "kaleidoscopic stained-glass light across the wooden pews, soft nostalgic glow, congregation silhouettes",
     cam=cam(1.1, 1.24, .45, .5, .55, .5, r0=-5, r1=-5), tint=[1.06, 1.0, 0.9], shake=0.15)

shot(80.51, 83.95, "s24_angels_door.jpg",
     f"{STYLE}, wide dutch angle of tall glowing indifferent angels filing through a radiant doorway of light, "
     "{CH} screaming and reaching, held back by an invisible barrier, his fingers pressed flat against glowing air, despair",
     cam=cam(1.1, 1.3, .42, .5, .6, .5, r0=4, r1=-2), fx=["rays"], kick=0.8, shake=0.4)

# ============================== A QUEDA ==============================
shot(83.95, 86.82, "s25_floor_opens.jpg",
     f"{STYLE}, extreme top-down shot of {CH} falling away from camera through a hole broken in the cloud floor, "
     "arms reaching up toward the receding golden gates, perspective plunge, fisheye distortion, dramatic foreshortening",
     cam=cam(1.06, 1.34, r0=-6, r1=6, ease="inc"), tin="whip", shake=0.5, kick=0.9, aberr=1.0)

shot(86.82, 90.03, "s26_fall_storm.jpg",
     f"{STYLE}, low angle looking up at {CH} falling toward camera through dark storm clouds, suit flapping "
     "violently, screaming, lightning veins in the clouds, rain streaks shooting upward, extreme motion energy",
     cam=cam(1.1, 1.32, .5, .45, .5, .55, r0=3, r1=-5), fx=["rain_lite"], shake=0.7, kick=0.9)

shot(90.03, 93.7, "s27_fall_red.jpg", src="s26_fall_storm.jpg", flip=True,
     cam=cam(1.34, 1.12, .45, .55, .55, .45, r0=-10, r1=8, ease="io"),
     tint=[1.12, 0.82, 0.7], fx=["embers_lite"], shake=0.7, kick=0.9)

shot(93.7, 97.2, "s28_pit.jpg",
     f"{STYLE}, god's-eye view straight down at a glowing molten red pit mouth opening in a black scorched plain, "
     "{CH} tiny silhouette falling into it, spiraling smoke and embers rising, concentric rings of fire, vast scale",
     cam=cam(1.08, 1.38, ease="inc"), fx=["embers"], shake=0.5, kick=0.9, tout="dip")

# ============================== VERSO 2 — inferno ==============================
shot(97.2, 100.28, "s29_hell_gate.jpg",
     f"{STYLE}, colossal obsidian gate covered in glowing molten inscriptions, extreme worm's-eye angle, tiny {CH} "
     "standing at its base, rivers of embers, oppressive scale, black and infernal orange palette",
     cam=cam(1.1, 1.3, .5, .6, .5, .35), fx=["embers"], tin="flash", kick=0.7, shake=0.3)

shot(100.28, 103.31, "s30_gulp.jpg",
     f"{STYLE}, horror underlighting extreme close-up of {CH} gulping nervously looking up, face lit blood-red "
     "from below, the glowing gate reflected in his huge terrified eyes, sweat, embers drifting past",
     cam=cam(1.1, 1.3, .5, .5, .5, .45), fx=["embers_lite"], shake=0.35, kick=0.6)

shot(103.31, 107.02, "s31_hellscape.jpg",
     f"{STYLE}, breathtaking panorama of hell, twisted black spires, rivers of lava, storms of embers, endless "
     "chained crowds marching, a bruised red sky with a black sun, epic scale wide shot, painted matte background",
     cam=cam(1.06, 1.22, .35, .5, .65, .5), fx=["embers"], shake=0.15)

shot(107.02, 110.14, "s32_gluttons.jpg",
     f"{STYLE}, grotesque infernal banquet, obese wailing damned souls seated at an endless table with red apples "
     "stuffed in their mouths like trophies, demon waiters in tailcoats, bone chandeliers with candles, high angle",
     cam=cam(1.1, 1.28, .4, .5, .6, .5, r0=2, r1=-3), fx=["embers_lite"], shake=0.25)

shot(110.14, 113.51, "s33_mirrors.jpg",
     f"{STYLE}, corridor of tall ornate gilded mirrors in darkness, vain souls trapped inside the glass clawing "
     "and screaming at their own reflections, {CH} walking between them uneasy, dutch angle, candle-orange rim light",
     cam=cam(1.1, 1.3, .4, .5, .6, .5, r0=-5, r1=3), shake=0.3)

# "Com desejos e vontades..." — reuso dos espelhos, câmera nova (crash-zoom num espelho)
shot(113.51, 116.9, "s34_desires.jpg", src="s33_mirrors.jpg",
     cam=cam(1.3, 1.55, .62, .48, .62, .48, r0=3, r1=-4, ease="inc"), shake=0.4, kick=0.8)

shot(116.9, 119.99, "s35_market.jpg",
     f"{STYLE}, busy infernal night market, demon merchants at stalls selling miniature burning worlds inside "
     "glass jars, hanging cages, glowing hellfire signage, crowds of damned souls shopping, smoky wide shot",
     cam=cam(1.06, 1.24, .38, .5, .62, .5), fx=["embers_lite"], shake=0.2)

# "A imaginação é o limite..." — reuso do mercado, pan invertido + zoom
shot(119.99, 123.22, "s36_market2.jpg", src="s35_market.jpg", flip=True,
     cam=cam(1.24, 1.44, .55, .45, .45, .55, r0=-3, r1=3), fx=["embers_lite"], shake=0.3, kick=0.6)

shot(123.22, 126.59, "s37_elevator.jpg",
     f"{STYLE}, claustrophobic shot inside a rusty caged industrial elevator descending, {CH} pressed in a corner, "
     "a skeletal demon operator in a bellhop uniform at the lever, one flickering bulb, an old TV showing static, sparks",
     cam=cam(1.12, 1.3, .45, .5, .55, .5, r0=2, r1=-2), shake=0.5)

shot(126.59, 129.83, "s38_corridor.jpg",
     f"{STYLE}, perfect one-point perspective of elevator doors opened onto an endless symmetric corridor of "
     "flame-lit black stone, tiny silhouette of {CH} stepping out alone, kubrick symmetry, oppressive geometry",
     cam=cam(1.06, 1.3, ease="in"), fx=["embers_lite"], shake=0.15)

shot(129.83, 132.87, "s39_run_gate.jpg",
     f"{STYLE}, low tracking angle of {CH} sprinting desperately toward a distant burning gate, coat flying, "
     "anime speed lines, embers streaking horizontally, motion blur floor, extreme dynamic diagonal composition",
     cam=cam(1.12, 1.36, .42, .5, .58, .5, r0=-4, r1=2, ease="inc"), fx=["embers"], shake=0.8, kick=0.9)

shot(132.87, 136.14, "s40_devil.jpg",
     f"{STYLE}, {DEVIL} lounging sideways on an obsidian throne wreathed in smoke, low angle, hellfire rim light, "
     "one eyebrow raised in amused delight, cigar smoke curling, art-deco infernal throne room",
     cam=cam(1.08, 1.26, .5, .52, .5, .46), fx=["embers_lite"], tin="flash", kick=0.7)

shot(136.14, 139.71, "s41_demon_list.jpg",
     f"{STYLE}, extreme worm's-eye of a hulking demon clerk behind a towering desk made of skulls, ticking names "
     "in a burning ledger with a quill of fire, looking down over tiny {CH}, mirror composition of a heavenly gate check, embers",
     cam=cam(1.1, 1.3, .5, .58, .5, .38), fx=["embers"], kick=0.7, shake=0.3)

shot(139.71, 143.14, "s42_denied.jpg",
     f"{STYLE}, extreme close-up of the demon clerk's massive clawed fist slamming a glowing brand onto the ledger, "
     "sparks exploding, {CH} flinching small in the foreground bokeh, wide predatory grin of sharp teeth above, impact frame",
     cam=cam(1.26, 1.06, ease="outc"), fx=["embers_lite"], tin="flash", kick=1.0, shake=0.6, aberr=1.1)

# "Tentados pelos desejos cruéis" — reuso dos espelhos com roll lento
shot(143.14, 146.04, "s43_tempt.jpg", src="s33_mirrors.jpg", flip=True,
     cam=cam(1.4, 1.2, .4, .5, .5, .5, r0=8, r1=-6), tint=[1.1, 0.85, 0.75], shake=0.4)

shot(146.04, 149.68, "s44_heart_falls.jpg",
     f"{STYLE}, {CH} dropping to his knees clutching his chest, mouth open gasping for air, embers swirling "
     "around him, blood-red light, camera slightly above, his shadow stretched long by firelight, raw despair",
     cam=cam(1.08, 1.32, .5, .45, .5, .55, r0=-3, r1=3), fx=["embers"], shake=0.5, kick=0.8)

# ============================== REFRÃO 2 (infernal) ==============================
shot(149.68, 152.55, "s45_beg_devil.jpg",
     f"{STYLE}, extreme low angle framed between the silhouetted horns of {DEVIL} in the foreground, tiny {CH} "
     "kneeling and begging far below, wall of fire behind, frame-within-frame composition, theatrical scale",
     cam=cam(1.1, 1.32, .5, .55, .5, .45), fx=["embers"], tin="flash", kick=0.9, shake=0.4)

shot(152.55, 155.75, "s46_uniform.jpg",
     f"{STYLE}, {CH} desperately pulling his own collar and lapels showing his plain suit to a circle of looming "
     "demon guards with spears, fisheye-like curved perspective, torchlight ring, panic, sweat, wide angle distortion",
     cam=cam(1.1, 1.3, .45, .5, .55, .5, r0=5, r1=-5), fx=["embers_lite"], shake=0.5, kick=0.8)

# "Eu não pertenço aqui" — reuso, pull-back + dutch
shot(155.75, 159.39, "s47_not_belong.jpg", src="s46_uniform.jpg", flip=True,
     cam=cam(1.34, 1.1, .55, .48, .45, .52, r0=-8, r1=4, ease="out"), tint=[1.05, 0.9, 0.85], shake=0.5, kick=0.8)

shot(159.39, 162.83, "s48_demon_parade.jpg",
     f"{STYLE}, wide shot of a parade of horned demons marching through a burning archway dragging chained souls, "
     "{CH} in the foreground screaming with his arms spread, ignored by all, ember storm, theatrical staging",
     cam=cam(1.06, 1.26, .4, .5, .6, .5), fx=["embers"], kick=0.8, shake=0.35)

shot(162.83, 165.72, "s49_dragged.jpg",
     f"{STYLE}, two hulking demon brutes dragging {CH} backwards by the arms, his heels scraping grooves in the "
     "ash floor, body sagging, yelling, low tracking side angle, fire wall background, embers, dynamic diagonal",
     cam=cam(1.1, 1.32, .42, .5, .58, .5, r0=-3, r1=3), fx=["embers"], tin="whip", shake=0.6, kick=0.9)

shot(165.72, 168.92, "s50_thrown.jpg",
     f"{STYLE}, god's-eye top-down of {CH} sprawled on the black ash floor where he was thrown, burning papers "
     "raining down around him like snow, he pushes himself up weakly, circle of demon feet surrounding, embers",
     cam=cam(1.12, 1.3, r0=6, r1=-4), fx=["embers"], shake=0.4, kick=0.7)

shot(168.92, 172.53, "s51_pound_door.jpg",
     f"{STYLE}, side profile silhouette of {CH} pounding both fists against a colossal iron door, fire glow "
     "seeping through the door seams, sparks on each impact, his head bowed, exhaustion and fury, chiaroscuro",
     cam=cam(1.1, 1.3, .45, .5, .55, .5), fx=["embers_lite"], shake=0.55, kick=0.9)

# "Gritando pros demônios" — reuso do desfile, crane lento
shot(172.53, 175.96, "s52_scream_wide.jpg", src="s48_demon_parade.jpg", flip=True,
     cam=cam(1.3, 1.08, .55, .55, .5, .42, ease="out"), fx=["embers"], shake=0.3, kick=0.7)

# ============================== PONTE — a caçada ==============================
shot(175.96, 179.53, "s53_chase.jpg",
     f"{STYLE}, {CH} sprinting straight toward camera down a collapsing corridor of fire, a horde of demon "
     "silhouettes with glowing eyes charging behind him, extreme anime speed lines, debris flying, floor cracking, adrenaline",
     cam=cam(1.08, 1.4, ease="inc"), fx=["embers"], tin="whip", shake=1.0, kick=1.0, aberr=1.2)

shot(179.53, 182.99, "s54_they_walk.jpg",
     f"{STYLE}, {CH} collapsed on hands and knees panting in the foreground, behind him the demons do not run — "
     "they walk slowly out of the shadows in a wide line, backlit by fire, glowing eyes, dread, horror pacing",
     cam=cam(1.24, 1.08, .5, .55, .5, .5, ease="out"), fx=["embers_lite"], shake=0.3, kick=0.4)

# "Continua fugindo" — reuso da caçada, espelhada, mais lenta e cansada
shot(182.99, 188.95, "s55_chase_loop.jpg", src="s53_chase.jpg", flip=True,
     cam=cam(1.38, 1.14, .45, .5, .55, .5, r0=4, r1=-4), fx=["embers"], tint=[1.0, 0.88, 0.82], shake=0.8, kick=0.9)

shot(188.95, 192.52, "s56_climb.jpg",
     f"{STYLE}, epic vertical composition of {CH} climbing crumbling black stone stairs toward a tiny distant "
     "shaft of white divine light piercing the cavern ceiling, embers falling past him like reverse snow, hope and exhaustion",
     cam=cam(1.08, 1.28, .5, .6, .5, .35), fx=["embers"], tin="dip", shake=0.25)

shot(192.52, 195.96, "s57_angels_above.jpg",
     f"{STYLE}, worm's-eye from deep in the pit, far above at the rim of the light shaft stand tiny indifferent "
     "angel silhouettes looking down, cold white light flaring around them, unreachable, cathedral scale verticality",
     cam=cam(1.12, 1.3, .5, .42, .5, .3), fx=["rays"], shake=0.2)

# "Continua correndo pros anjos" — reuso da escada, zoom-out + queda de ritmo
shot(195.96, 201.66, "s58_climb2.jpg", src="s56_climb.jpg", flip=True,
     cam=cam(1.3, 1.06, .5, .4, .5, .55, r0=-3, r1=3, ease="out"), fx=["embers"], shake=0.35, kick=0.6)

# ============================== REFRÃO FINAL (eu não quero morrer) ==============================
shot(201.66, 205.17, "s59_final_beg.jpg",
     f"{STYLE}, crane shot rising above {CH} on his knees screaming at the sky with tears streaming, a closing "
     "ring of fire around him, arms spread wide, embers spiraling upward, operatic despair, red and black palette",
     cam=cam(1.28, 1.06, .5, .48, .5, .55, r0=-4, r1=2, ease="out"), fx=["embers"], tin="flash", shake=0.5, kick=1.0)

shot(205.17, 208.37, "s60_ash_list.jpg",
     f"{STYLE}, macro close-up of {CH}'s trembling fingers clutching the edge of the burning ledger as the page "
     "with names crumbles into glowing ash between his fingers, shallow focus, ember particles, loss made physical",
     cam=cam(1.1, 1.32, .5, .5, .45, .5), fx=["embers_lite"], shake=0.4, kick=0.7)

shot(208.37, 212.01, "s61_hand_up.jpg",
     f"{STYLE}, wide shot of a single hand reaching up out of rising flames, silhouetted against a dying shaft "
     "of cold light from far above, embers and smoke, the rest of the body already swallowed, tragic minimalism",
     cam=cam(1.06, 1.28, .5, .55, .5, .42), fx=["embers"], shake=0.3, kick=0.8)

# "(não me deixe morrer)" — reuso do retrato-âncora, zoom extremo no olho + tint vermelho
shot(212.01, 215.44, "s62_eye.jpg", src="hero.jpg",
     cam=cam(1.5, 2.1, .44, .38, .44, .38, r0=2, r1=-2, ease="io"), tint=[1.15, 0.72, 0.6],
     fx=["embers_lite"], shake=0.45, kick=0.8)

shot(215.44, 218.32, "s63_last_scream.jpg",
     f"{STYLE}, full silhouette of {CH} head thrown back in a final scream against an enormous wall of flame, "
     "backlit pure black figure, fire filling the entire frame behind, embers like a blizzard, apocalyptic",
     cam=cam(1.08, 1.3, .5, .5, .5, .45), fx=["embers"], tin="flash", shake=0.6, kick=1.0)

shot(218.32, 221.53, "s64_dissolve.jpg",
     f"{STYLE}, the silhouette of {CH} dissolving into thousands of glowing embers that scatter upward into "
     "black smoke, only half his outline remains, fire dimming to deep red darkness, poetic and final",
     cam=cam(1.2, 1.06, ease="out"), fx=["embers"], shake=0.3, kick=0.6, tout="dip")

# volta ao cemitério (bookend) — reuso das plates da abertura
shot(221.53, 225.4, "s65_grave_return.jpg", src="s03_tombstone.jpg",
     cam=cam(1.06, 1.22, .5, .5, .5, .45), tint=[0.82, 0.9, 1.1], fx=["rain"], tin="dip", shake=0.1, kick=0.2)

shot(225.4, 230.3, "s66_end.jpg", src="s01_cemetery.jpg",
     cam=cam(1.2, 1.05, .5, .55, .5, .45, ease="out"), tint=[0.78, 0.88, 1.12], fx=["rain"], shake=0.05, kick=0.1)

# ============================== emit ==============================
gen = [s for s in S if s["prompt"]]
json.dump({"shots": S}, open("clip/storyboard.json", "w"), indent=1, ensure_ascii=False)
json.dump([{"file": s["file"], "prompt": s["prompt"]} for s in gen],
          open("clip/prompts.json", "w"), indent=1, ensure_ascii=False)
reuse = [s["file"] for s in S if s["src"]]
print(f"{len(S)} shots | {len(gen)} a gerar (~{len(gen)*0.15:.2f} cr) | {len(reuse)} reusos")
for s in S:
    print(f"  {s['t0']:6.1f}-{s['t1']:6.1f}  {s['file']:24s} {'GEN' if s['prompt'] else 'reuse<-'+str(s['src'])}")
