#!/usr/bin/env python3
"""Audio analysis -> per-video-frame timeline JSON.

Extracts, for each output video frame:
  e   overall energy (0..1)
  b   bass energy        (drives flame surge, kick squash)
  lm  low-mid energy
  m   mid energy
  h   high energy        (drives ember/spark spawn)
  v   vocal-band energy  (drives the devil's singing mouth)
  beat  decaying beat-impulse envelope (0..1) for accents/pumps
  onset strength of an onset landing exactly on this frame (0 otherwise)
  phase tempo sawtooth 0..1 for steady bob

Pure numpy (no librosa) so it stays fast and dependency-light.
"""
import json
import sys
import numpy as np

SR = 22050
RAW = "build/audio_mono_22050.raw"
OUT = "build/timeline.json"
FPS = float(sys.argv[1]) if len(sys.argv) > 1 else 24.0

x = np.fromfile(RAW, dtype=np.float32)
x = x / (np.max(np.abs(x)) + 1e-9)
dur = len(x) / SR

hop = 512
win = 1024
fps_a = SR / hop  # analysis frame rate (~43 Hz)
n = 1 + (len(x) - win) // hop
window = np.hanning(win).astype(np.float32)
idx = np.arange(win)[None, :] + hop * np.arange(n)[:, None]
frames = x[idx] * window[None, :]
spec = np.abs(np.fft.rfft(frames, axis=1))
freqs = np.fft.rfftfreq(win, 1.0 / SR)
times = hop * np.arange(n) / SR


def band(lo, hi):
    m = (freqs >= lo) & (freqs < hi)
    return spec[:, m].sum(axis=1)


bass = band(20, 160)
lowmid = band(160, 500)
mid = band(500, 2000)
pres = band(2000, 6000)
high = band(6000, 11025)
vocal = band(350, 3500)
rms = np.sqrt((frames ** 2).mean(axis=1))


def smooth(a, k):
    k = int(k)
    if k <= 1:
        return a.astype(np.float64)
    ker = np.ones(k) / k
    return np.convolve(a.astype(np.float64), ker, mode="same")


def norm(a, p=99.0):
    a = a.astype(np.float64)
    hi = np.percentile(a, p)
    return np.clip(a / (hi + 1e-9), 0.0, 1.0)


# Spectral flux -> onset envelope
flux = np.maximum(0.0, np.diff(spec, axis=0, prepend=spec[:1])).sum(axis=1)
onset_env = norm(smooth(flux, 2), 99.5)

# --- Tempo via autocorrelation of onset envelope ---
oe = onset_env - onset_env.mean()
ac = np.correlate(oe, oe, "full")[len(oe) - 1:]
min_lag = int(round(fps_a * 60 / 180))   # 180 bpm
max_lag = int(round(fps_a * 60 / 70))    # 70 bpm
lag = int(np.argmax(ac[min_lag:max_lag]) + min_lag)
bpm = 60.0 * fps_a / lag

# --- Adaptive peak picking for onsets/accents ---
onsets_t = []
onsets_s = []
W = 4                      # local window (analysis frames)
min_gap = int(fps_a * 0.12)  # >=120ms apart
last = -10 ** 9
for i in range(n):
    a, b2 = max(0, i - W), min(n, i + W + 1)
    seg = onset_env[a:b2]
    if onset_env[i] < seg.max():
        continue
    lo, hi = max(0, i - 20), min(n, i + 20)
    local = onset_env[lo:hi]
    thr = local.mean() + 1.3 * local.std()
    if onset_env[i] >= max(thr, 0.12) and (i - last) >= min_gap:
        onsets_t.append(times[i])
        onsets_s.append(float(onset_env[i]))
        last = i

# Phase locked to first solid onset
phase0 = onsets_t[0] if onsets_t else 0.0
beat_period = 60.0 / bpm

# --- Resample everything to video frame rate ---
N = int(round(dur * FPS))
vt = np.arange(N) / FPS


def to_video(env, sm=3):
    e = norm(smooth(env, sm))
    return np.interp(vt, times, e)


E = to_video(rms, 3)
B = to_video(bass, 2)
LM = to_video(lowmid, 3)
M = to_video(mid, 3)
H = to_video(high, 2)
V = to_video(vocal, 2)

# Beat impulse envelope (decaying) + per-frame onset spikes
tau = 0.16
beat_env = np.zeros(N)
onset_spike = np.zeros(N)
ot = np.array(onsets_t)
os = np.array(onsets_s)
for k in range(N):
    if len(ot):
        recent = ot <= vt[k]
        if recent.any():
            dt = vt[k] - ot[recent]
            beat_env[k] = float(np.max(os[recent] * np.exp(-dt / tau)))
    # spike: nearest onset within half a frame
    if len(ot):
        j = int(np.argmin(np.abs(ot - vt[k])))
        if abs(ot[j] - vt[k]) <= (0.5 / FPS):
            onset_spike[k] = float(os[j])

phase = ((vt - phase0) / beat_period) % 1.0

frames_out = []
for k in range(N):
    frames_out.append({
        "e": round(float(E[k]), 3),
        "b": round(float(B[k]), 3),
        "lm": round(float(LM[k]), 3),
        "m": round(float(M[k]), 3),
        "h": round(float(H[k]), 3),
        "v": round(float(V[k]), 3),
        "beat": round(float(beat_env[k]), 3),
        "onset": round(float(onset_spike[k]), 3),
        "phase": round(float(phase[k]), 4),
    })

out = {
    "fps": FPS,
    "count": N,
    "duration": round(dur, 3),
    "bpm": round(bpm, 2),
    "n_onsets": len(onsets_t),
    "frames": frames_out,
}
with open(OUT, "w") as f:
    json.dump(out, f, separators=(",", ":"))

print(f"duration={dur:.2f}s fps={FPS} frames={N} bpm={bpm:.1f} onsets={len(onsets_t)}")
print(f"energy med={np.median(E):.2f} max={E.max():.2f} | bass med={np.median(B):.2f} | vocal med={np.median(V):.2f}")
print(f"wrote {OUT}")
