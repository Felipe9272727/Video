#!/usr/bin/env python3
"""
QC Motion Analysis Script
Analisa movimento em clipes de vídeo (image-to-video)
Detecta clipes estáticos, fracos, com artefatos ou OK.
"""

import os
import sys
import subprocess
import tempfile
import numpy as np
from pathlib import Path
from PIL import Image

# Configurar ffmpeg path
FFMPEG_PATH = "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"

def get_video_duration(mp4_path):
    """Retorna duração do vídeo em segundos."""
    cmd = [FFMPEG_PATH, '-i', mp4_path]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        output = result.stderr
        # Parse "Duration: HH:MM:SS.ms"
        for line in output.split('\n'):
            if 'Duration:' in line:
                parts = line.split('Duration:')[1].split(',')[0].strip()
                h, m, s = parts.split(':')
                return int(h) * 3600 + int(m) * 60 + float(s)
        return None
    except:
        return None

def extract_frames(mp4_path, num_frames=8):
    """Extrai frames uniformemente espaçados ao longo do vídeo."""
    duration = get_video_duration(mp4_path)
    if duration is None or duration <= 0:
        return []

    frames = []
    with tempfile.TemporaryDirectory() as tmpdir:
        # Calcular timestamps para frames uniformemente espaçados
        timestamps = np.linspace(0, duration * 0.95, num_frames)

        for i, ts in enumerate(timestamps):
            output_path = os.path.join(tmpdir, f"frame_{i:02d}.png")
            cmd = [
                FFMPEG_PATH, '-v', 'error',
                '-ss', str(ts),
                '-i', mp4_path,
                '-vf', 'scale=320:180',  # Dimensão reduzida para análise
                '-vframes', '1',
                output_path
            ]
            try:
                subprocess.run(cmd, timeout=5, check=True, capture_output=True)
                if os.path.exists(output_path):
                    img = Image.open(output_path)
                    frames.append(np.array(img))
            except:
                pass

        return frames

def calculate_motion_score(frames):
    """
    Calcula score de movimento (0-100).
    Baseado na diferença média de pixels entre frames consecutivos.
    """
    if len(frames) < 2:
        return 0

    differences = []
    for i in range(len(frames) - 1):
        frame1 = frames[i].astype(np.float32)
        frame2 = frames[i + 1].astype(np.float32)

        # Diferença absoluta média normalizada
        diff = np.mean(np.abs(frame1 - frame2)) / 255.0 * 100
        differences.append(diff)

    mean_diff = np.mean(differences) if differences else 0
    std_diff = np.std(differences) if differences else 0

    # Score: média + bonus se há variação no tempo (não é monotônico)
    score = min(mean_diff, 100)

    return score, mean_diff, std_diff

def detect_frozen_frames(frames):
    """
    Detecta frames quase idênticos ao primeiro (congelamento).
    Retorna percentual de frames congelados.
    """
    if len(frames) < 2:
        return 0

    first_frame = frames[0].astype(np.float32)
    frozen_count = 0
    threshold = 2.0  # Diferença máxima para considerar congelado

    for i in range(1, len(frames)):
        frame = frames[i].astype(np.float32)
        diff = np.mean(np.abs(frame - first_frame)) / 255.0 * 100
        if diff < threshold:
            frozen_count += 1

    return (frozen_count / (len(frames) - 1)) * 100

def detect_artifacts(frames):
    """
    Detecta possíveis artefatos (morphing, flicker).
    Analisa mudanças bruscas e globais entre frames.
    Returns: (has_artifacts, artifact_info)
    """
    if len(frames) < 3:
        return False, ""

    differences = []
    for i in range(len(frames) - 1):
        frame1 = frames[i].astype(np.float32)
        frame2 = frames[i + 1].astype(np.float32)
        diff = np.mean(np.abs(frame1 - frame2)) / 255.0 * 100
        differences.append(diff)

    if not differences:
        return False, ""

    mean_diff = np.mean(differences)
    std_diff = np.std(differences)

    info = f"diffs: mean={mean_diff:.1f}, std={std_diff:.1f}"

    # Artefato: variação muito alta (flicker) ou spike brusco (morphing)
    if std_diff > mean_diff * 1.5:  # Muito instável
        return True, info + " (FLICKER)"

    max_diff = max(differences)
    if max_diff > mean_diff * 3:  # Spike brusco
        return True, info + " (MORPHING)"

    return False, info

def classify_clip(score, frozen_pct, has_artifacts):
    """
    Classifica o clipe em: OK, FRACO, ESTÁTICO ou ARTEFATO
    """
    if has_artifacts:
        return "ARTEFATO"

    if score < 5:
        return "ESTÁTICO"
    elif score < 20:
        if frozen_pct > 30:
            return "ESTÁTICO"
        return "FRACO"
    else:
        return "OK"

def main():
    motion_dir = Path("/home/user/Video/clip/motion")
    mp4_files = sorted(motion_dir.glob("*.mp4"))

    if not mp4_files:
        print("Nenhum arquivo .mp4 encontrado em clip/motion/")
        return

    results = []

    print(f"Analisando {len(mp4_files)} clipes...")
    print()

    for mp4_path in mp4_files:
        filename = mp4_path.name
        stem = mp4_path.stem

        print(f"Processando: {filename}...", end=" ")
        sys.stdout.flush()

        # Extrair frames
        frames = extract_frames(str(mp4_path), num_frames=8)

        if not frames:
            print("ERRO: não conseguiu extrair frames")
            continue

        # Calcular métricas
        score, mean_diff, std_diff = calculate_motion_score(frames)
        frozen_pct = detect_frozen_frames(frames)
        has_artifacts, artifact_info = detect_artifacts(frames)

        # Classificar
        classification = classify_clip(score, frozen_pct, has_artifacts)

        results.append({
            'filename': filename,
            'stem': stem,
            'score': score,
            'mean_diff': mean_diff,
            'frozen_pct': frozen_pct,
            'has_artifacts': has_artifacts,
            'artifact_info': artifact_info,
            'classification': classification
        })

        print(f"Score: {score:.1f} | {classification}")

    # Produzir relatório
    print("\n" + "="*70)
    print("RELATÓRIO DE QC - MOVIMENTO")
    print("="*70)
    print(f"{'Nome':<25} {'Score':<10} {'Classificação':<15}")
    print("-"*70)

    for result in results:
        print(f"{result['filename']:<25} {result['score']:>6.1f}     {result['classification']:<15}")

    print("="*70)

    # Linha de REGENERAR
    to_regenerate = [r['stem'] + '.jpg' for r in results
                     if r['classification'] in ['ESTÁTICO', 'FRACO']]

    if to_regenerate:
        regenerate_line = "REGENERAR: " + " ".join(to_regenerate)
        print()
        print(regenerate_line)
    else:
        print("\nREGENERAR: (nenhum clipe marcado para regeneração)")

if __name__ == "__main__":
    main()
