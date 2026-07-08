#!/usr/bin/env python3
"""
Light particles overlay: floating dust/pollen + god-rays for ethereal reveals.
RGBA output, loop-friendly, subtle. Composition: Screen blend or Add with alpha ~0.3-0.5.
"""

import numpy as np
from PIL import Image, ImageDraw
import os
from pathlib import Path


def _perlin_like_1d(t, scale=1.0):
    """Smooth pseudo-random walk (use for animation smoothness)."""
    return np.sin(t * scale * 2.5) * 0.5 + 0.5


def render(w=1920, h=816, frames=120, fps=24, seed=7, out_dir=None):
    """
    Render light particle overlay.

    Args:
        w, h: Output resolution (default cinematic 21:9).
        frames: Number of frames to render.
        fps: Frames per second (for timing).
        seed: RNG seed (for reproducibility).
        out_dir: Output directory. If None, no files written.

    Returns:
        List of PIL Images (RGBA).
    """
    np.random.seed(seed)

    images = []
    duration_sec = frames / fps

    # Particle swarm: multiple layers, each with different speeds/scales
    # Layer 1: Slow large particles (god-rays)
    n_large = 8
    large_x = np.random.uniform(0, w, n_large)
    large_y = np.random.uniform(-h * 0.2, h, n_large)
    large_v = np.random.uniform(0.5, 1.5, n_large)  # pixels/frame upward
    large_size = np.random.uniform(60, 150, n_large)
    large_alpha_base = np.random.uniform(0.08, 0.15, n_large)

    # Layer 2: Medium dust (faster, more)
    n_med = 25
    med_x = np.random.uniform(0, w, n_med)
    med_y = np.random.uniform(-h * 0.1, h, n_med)
    med_v = np.random.uniform(2.0, 4.0, n_med)
    med_size = np.random.uniform(15, 45, n_med)
    med_alpha_base = np.random.uniform(0.12, 0.25, n_med)

    # Layer 3: Fine pollen (fastest, most numerous)
    n_fine = 50
    fine_x = np.random.uniform(0, w, n_fine)
    fine_y = np.random.uniform(-h * 0.05, h, n_fine)
    fine_v = np.random.uniform(4.0, 8.0, n_fine)
    fine_size = np.random.uniform(3, 12, n_fine)
    fine_alpha_base = np.random.uniform(0.08, 0.18, n_fine)

    # Shimmer/flicker for each particle (frame-based modulation)
    large_flicker = np.random.uniform(0.6, 1.0, n_large)
    med_flicker = np.random.uniform(0.7, 1.0, n_med)
    fine_flicker = np.random.uniform(0.7, 1.0, n_fine)

    # Slow horizontal drift (gives flow illusion)
    large_drift_phase = np.random.uniform(0, 2 * np.pi, n_large)
    med_drift_phase = np.random.uniform(0, 2 * np.pi, n_med)
    fine_drift_phase = np.random.uniform(0, 2 * np.pi, n_fine)

    for frame_idx in range(frames):
        t = frame_idx / fps  # time in seconds
        progress = frame_idx / frames

        # Create RGBA image (alpha = 0 by default)
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img, "RGBA")

        # --- Layer 1: Large god-ray particles ---
        for i in range(n_large):
            # Vertical position (loop-friendly: wraps at top)
            y = large_y[i] + (t * large_v[i] * fps)
            y_wrapped = y % (h + large_size[i] * 2)
            if y_wrapped > h + large_size[i]:
                y_wrapped -= (h + large_size[i] * 2)

            # Horizontal drift
            drift = np.sin(large_drift_phase[i] + t * 0.3) * (w * 0.05)
            x = (large_x[i] + drift) % w

            # Size oscillation (shimmer)
            shimmer = 0.8 + 0.2 * np.sin(t * 2.0 + i)
            sz = large_size[i] * shimmer

            # Alpha with flicker
            flicker_mod = 0.6 + 0.4 * large_flicker[i] * _perlin_like_1d(t * 0.5 + i * 0.1)
            alpha = int(large_alpha_base[i] * flicker_mod * 255)

            # Draw soft radial gradient (approximated with concentric circles)
            for r_frac in np.linspace(1.0, 0.0, 8):
                r = sz * r_frac
                circle_alpha = int(alpha * (1 - r_frac) ** 0.5)
                if circle_alpha > 2:
                    draw.ellipse(
                        [x - r, y_wrapped - r, x + r, y_wrapped + r],
                        fill=(255, 255, 255, circle_alpha)
                    )

        # --- Layer 2: Medium dust particles ---
        for i in range(n_med):
            y = med_y[i] + (t * med_v[i] * fps)
            y_wrapped = y % (h + med_size[i] * 2)
            if y_wrapped > h + med_size[i]:
                y_wrapped -= (h + med_size[i] * 2)

            drift = np.sin(med_drift_phase[i] + t * 0.4) * (w * 0.03)
            x = (med_x[i] + drift) % w

            shimmer = 0.85 + 0.15 * np.sin(t * 3.0 + i * 0.15)
            sz = med_size[i] * shimmer

            flicker_mod = 0.65 + 0.35 * med_flicker[i] * _perlin_like_1d(t * 0.7 + i * 0.08)
            alpha = int(med_alpha_base[i] * flicker_mod * 255)

            for r_frac in np.linspace(1.0, 0.0, 6):
                r = sz * r_frac
                circle_alpha = int(alpha * (1 - r_frac) ** 0.4)
                if circle_alpha > 2:
                    draw.ellipse(
                        [x - r, y_wrapped - r, x + r, y_wrapped + r],
                        fill=(240, 245, 255, circle_alpha)
                    )

        # --- Layer 3: Fine pollen ---
        for i in range(n_fine):
            y = fine_y[i] + (t * fine_v[i] * fps)
            y_wrapped = y % (h + fine_size[i] * 2)
            if y_wrapped > h + fine_size[i]:
                y_wrapped -= (h + fine_size[i] * 2)

            drift = np.sin(fine_drift_phase[i] + t * 0.5) * (w * 0.02)
            x = (fine_x[i] + drift) % w

            shimmer = 0.9 + 0.1 * np.sin(t * 4.0 + i * 0.2)
            sz = fine_size[i] * shimmer

            flicker_mod = 0.7 + 0.3 * fine_flicker[i] * _perlin_like_1d(t * 0.9 + i * 0.1)
            alpha = int(fine_alpha_base[i] * flicker_mod * 255)

            if sz > 1.5:
                for r_frac in np.linspace(1.0, 0.0, 3):
                    r = sz * r_frac
                    circle_alpha = int(alpha * (1 - r_frac) ** 0.3)
                    if circle_alpha > 1:
                        draw.ellipse(
                            [x - r, y_wrapped - r, x + r, y_wrapped + r],
                            fill=(245, 248, 255, circle_alpha)
                        )

        images.append(img)

        # Save to disk if out_dir specified
        if out_dir:
            out_path = Path(out_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            frame_file = out_path / f"frame_{frame_idx:04d}.png"
            img.save(frame_file)

    return images


def make_contact_sheet(images, out_file, n_frames=6, frame_width=240):
    """
    Create a contact sheet from a subset of frames.

    Args:
        images: List of PIL Images.
        out_file: Path to save contact sheet.
        n_frames: Number of frames to show (evenly spaced).
        frame_width: Width of each frame in the sheet.
    """
    if not images:
        return

    # Select frames evenly spaced
    indices = np.linspace(0, len(images) - 1, n_frames, dtype=int)
    selected = [images[i] for i in indices]

    # Resize to frame_width, keeping aspect ratio
    aspect = selected[0].height / selected[0].width
    frame_height = int(frame_width * aspect)
    resized = [img.resize((frame_width, frame_height), Image.LANCZOS) for img in selected]

    # Create contact sheet (all frames in one row)
    total_width = frame_width * n_frames
    sheet = Image.new("RGBA", (total_width, frame_height), (0, 0, 0, 255))

    for i, img in enumerate(resized):
        sheet.paste(img, (i * frame_width, 0), img)

    # Convert to RGB if saving as JPEG
    if out_file.endswith(('.jpg', '.jpeg')):
        sheet = sheet.convert('RGB')

    sheet.save(out_file)


if __name__ == "__main__":
    import sys

    # Example usage
    out_dir = "/home/user/Video/build/overlays/s57_light"

    print(f"Rendering 24 frames to {out_dir}...")
    frames = render(w=1920, h=816, frames=24, fps=24, seed=7, out_dir=out_dir)
    print(f"Saved {len(frames)} frames.")

    contact_out = "/home/user/Video/build/overlays/s57_light_contact.jpg"
    print(f"Creating contact sheet: {contact_out}...")
    make_contact_sheet(frames, contact_out, n_frames=6, frame_width=240)
    print(f"Done.")
