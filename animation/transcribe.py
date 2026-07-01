#!/usr/bin/env python3
"""Transcribe the sung PT-BR cover with word-level timestamps.
Output: build/lyrics.json (segments + words) and a readable build/lyrics.txt.
"""
import json
from faster_whisper import WhisperModel

MP3 = "Charlie_s Inferno (Excuse Me Sir) - That Handsome Devil _ COVER PT-BR(MP3_160K)_1.mp3"
model = WhisperModel("medium", device="cpu", compute_type="int8")
segments, info = model.transcribe(
    MP3, language="pt", beam_size=5, vad_filter=True,
    word_timestamps=True, condition_on_previous_text=False,
)
print("detected:", info.language, "prob", round(info.language_probability, 2))
segs = []
lines = []
for s in segments:
    words = [{"t": round(w.start, 2), "e": round(w.end, 2), "w": w.word} for w in (s.words or [])]
    segs.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip(), "words": words})
    line = f"[{s.start:6.1f}-{s.end:6.1f}] {s.text.strip()}"
    print(line, flush=True)
    lines.append(line)
with open("build/lyrics.json", "w") as f:
    json.dump({"language": info.language, "segments": segs}, f, ensure_ascii=False, indent=1)
with open("build/lyrics.txt", "w") as f:
    f.write("\n".join(lines))
print("\nwrote build/lyrics.json and build/lyrics.txt  (", len(segs), "segments )")
