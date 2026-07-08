#!/usr/bin/env python3
"""
Anime FX overlays: speed lines (motion blur + direction) + impact flash.
RGBA output, loop-friendly. Composition: Screen blend or Add with alpha ~0.4-0.7.
"""

import numpy as np
from PIL import Image, ImageDraw
import os
from pathlib import Path


def speed_lines(w=1920, h=816, frames=90, direction='horizontal', intensity=0.6, seed=3, out_dir=None):
    """
    Render speed lines overlay (anime motion lines).

    Args:
        w, h: Output resolution (default cinematic 21:9).
        frames: Number of frames to render (default 90 = 3.75s @ 24fps).
        direction: 'horizontal', 'vertical', 'radial', or 'diagonal'.
        intensity: Line density/thickness (0.0-1.0, default 0.6).
        seed: RNG seed (for reproducibility).
        out_dir: Output directory. If None, no files written.

    Returns:
        List of PIL Images (RGBA).
    """
    np.random.seed(seed)

    images = []
    center_x, center_y = w // 2, h // 2

    # Line parameters
    n_lines = int(8 + intensity * 12)  # 8-20 lines based on intensity
    line_length = int(200 + intensity * 400)  # 200-600 pixels
    line_width_base = int(2 + intensity * 6)  # 2-8 pixels

    # Pre-generate line angles and start positions
    if direction == 'radial':
        angles = np.linspace(0, 2 * np.pi, n_lines, endpoint=False)
    elif direction == 'horizontal':
        n_left = n_lines // 2
        n_right = n_lines - n_left
        angles = np.array([0] * n_left + [np.pi] * n_right)
    elif direction == 'vertical':
        n_up = n_lines // 2
        n_down = n_lines - n_up
        angles = np.array([np.pi / 2] * n_up + [3 * np.pi / 2] * n_down)
    elif direction == 'diagonal':
        base_angles = np.array([np.pi / 4, np.pi / 4 + np.pi, 3 * np.pi / 4, 3 * np.pi / 4 + np.pi])
        angles = np.tile(base_angles, (n_lines // 4 + 1))[:n_lines]
    else:
        angles = np.random.uniform(0, 2 * np.pi, n_lines)

    # Random jitter to angles
    angles = angles + np.random.uniform(-0.15, 0.15, n_lines)

    # Random offsets for each line (distance from center at start)
    start_dist = np.random.uniform(-line_length * 0.5, 0, n_lines)

    # Line colors: mostly white/pale, some color tint
    colors = []
    for i in range(n_lines):
        if np.random.rand() < 0.7:
            colors.append((255, 255, 255))  # White
        else:
            colors.append((220, 240, 255))  # Pale blue tint

    for frame_idx in range(frames):
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img, "RGBA")

        # Envelope: fade in at start, hold, fade out at end
        progress = frame_idx / frames
        if progress < 0.15:  # Fade in (first 15%)
            alpha_envelope = progress / 0.15
        elif progress < 0.85:  # Hold (middle 70%)
            alpha_envelope = 1.0
        else:  # Fade out (last 15%)
            alpha_envelope = (1.0 - progress) / 0.15

        # Animate line positions
        for i in range(n_lines):
            # Expand outward from center
            expand_factor = progress  # 0 to 1
            dist = start_dist[i] + expand_factor * line_length

            # Start and end points
            x1 = center_x + dist * np.cos(angles[i])
            y1 = center_y + dist * np.sin(angles[i])

            x2 = center_x + (dist + line_length * 0.3) * np.cos(angles[i])
            y2 = center_y + (dist + line_length * 0.3) * np.sin(angles[i])

            # Line width (tapers at end)
            lw = max(1, int(line_width_base * (1.0 - expand_factor * 0.5)))

            # Alpha: per-line flicker + envelope
            line_alpha = int(
                (100 + intensity * 155) * alpha_envelope
                * (0.7 + 0.3 * np.sin(frame_idx * 0.2 + i))
            )
            if line_alpha < 5:
                line_alpha = 0

            if line_alpha > 0:
                r, g, b = colors[i]
                draw.line(
                    [(x1, y1), (x2, y2)],
                    fill=(r, g, b, line_alpha),
                    width=lw
                )

        images.append(img)

        # Save to disk if out_dir specified
        if out_dir:
            out_path = Path(out_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            frame_file = out_path / f"frame_{frame_idx:04d}.png"
            img.save(frame_file)

    return images


def impact_flash(w=1920, h=816, frames=12, out_dir=None):
    """
    Render impact flash overlay (white radial burst for hits).

    Args:
        w, h: Output resolution (default cinematic 21:9).
        frames: Number of frames (default 12 = 0.5s @ 24fps, one beat).
        out_dir: Output directory. If None, no files written.

    Returns:
        List of PIL Images (RGBA).
    """
    np.random.seed(42)

    images = []
    center_x, center_y = w // 2, h // 2

    max_radius = int(np.sqrt(w**2 + h**2) * 0.6)  # Expand to ~60% of diagonal

    for frame_idx in range(frames):
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img, "RGBA")

        # Progress: 0 to 1
        progress = frame_idx / frames

        # Pulse envelope: very bright at start, drop sharply
        brightness = 1.0 - progress ** 0.5  # Exponential decay

        # Radial gradient: draw concentric circles fading
        n_rings = 20
        for ring_idx in range(n_rings):
            ring_progress = ring_idx / n_rings
            radius = int(max_radius * ring_progress * (0.3 + progress * 0.7))

            # Alpha drops with distance and time
            ring_alpha = int(255 * brightness * (1.0 - ring_progress) * (1.0 - progress * 0.5))

            if ring_alpha > 2:
                x0 = center_x - radius
                y0 = center_y - radius
                x1 = center_x + radius
                y1 = center_y + radius
                draw.ellipse([x0, y0, x1, y1], fill=(255, 255, 255, ring_alpha))

        images.append(img)

        # Save to disk if out_dir specified
        if out_dir:
            out_path = Path(out_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            frame_file = out_path / f"frame_{frame_idx:04d}.png"
            img.save(frame_file)

    return images


def compose_overlay(base_img, overlay_frames, blend_mode='screen', alpha=0.5):
    """
    Composite overlay frames onto a base image using screen or add blend.

    Args:
        base_img: PIL Image (RGB or RGBA) to composite onto.
        overlay_frames: List of PIL Images (RGBA) to overlay.
        blend_mode: 'screen' or 'add'.
        alpha: Opacity of overlay (0.0-1.0).

    Returns:
        List of PIL Images (RGB) composited.
    """
    if base_img.mode == 'RGBA':
        base_img = base_img.convert('RGB')

    results = []
    for overlay in overlay_frames:
        overlay_rgb = overlay.convert('RGB')
        overlay_a = overlay.split()[3] if overlay.mode == 'RGBA' else Image.new('L', overlay.size, 255)

        if blend_mode == 'screen':
            # Screen blend: 1 - (1-A) * (1-B)
            base_arr = np.array(base_img, dtype=np.float32) / 255.0
            overlay_arr = np.array(overlay_rgb, dtype=np.float32) / 255.0
            alpha_arr = np.array(overlay_a, dtype=np.float32) / 255.0
            alpha_arr = alpha_arr * alpha

            # Expand alpha to 3 channels
            alpha_3ch = np.dstack([alpha_arr] * 3)

            result_arr = 1.0 - (1.0 - base_arr) * (1.0 - overlay_arr * alpha_3ch)
            result_arr = np.clip(result_arr * 255, 0, 255).astype(np.uint8)
            result_img = Image.fromarray(result_arr, 'RGB')
        else:  # 'add'
            base_arr = np.array(base_img, dtype=np.float32)
            overlay_arr = np.array(overlay_rgb, dtype=np.float32)
            alpha_arr = np.array(overlay_a, dtype=np.float32) / 255.0
            alpha_arr = alpha_arr * alpha

            alpha_3ch = np.dstack([alpha_arr] * 3)
            result_arr = base_arr + overlay_arr * alpha_3ch
            result_arr = np.clip(result_arr, 0, 255).astype(np.uint8)
            result_img = Image.fromarray(result_arr, 'RGB')

        results.append(result_img)

    return results


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
    sheet = Image.new("RGB", (total_width, frame_height), (30, 30, 30))

    for i, img in enumerate(resized):
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        sheet.paste(img, (i * frame_width, 0))

    sheet.save(out_file)


if __name__ == "__main__":
    # Example: render speed_lines and impact_flash, then composite onto a base plate
    import sys

    # Paths
    base_plate = "/home/user/Video/clip/shots/s39_run_gate.jpg"
    out_dir_speed = "/home/user/Video/build/overlays/fio_s39_speed"
    out_dir_impact = "/home/user/Video/build/overlays/fio_s39_impact"

    print("[Fio] Rendering speed_lines (90 frames, horizontal, intensity=0.6)...")
    speed_frames = speed_lines(w=1920, h=816, frames=90, direction='horizontal', intensity=0.6, seed=3, out_dir=out_dir_speed)
    print(f"  → {len(speed_frames)} frames saved to {out_dir_speed}")

    print("[Fio] Rendering impact_flash (12 frames)...")
    impact_frames = impact_flash(w=1920, h=816, frames=12, out_dir=out_dir_impact)
    print(f"  → {len(impact_frames)} frames saved to {out_dir_impact}")

    # Load base plate and resize to match FX resolution
    print(f"[Fio] Loading base plate: {base_plate}")
    try:
        base = Image.open(base_plate)
        print(f"  → Original: {base.size}")
        # Resize to 1920×816 to match FX frames
        if base.size != (1920, 816):
            base = base.resize((1920, 816), Image.LANCZOS)
            print(f"  → Resized to: {base.size}")
    except Exception as e:
        print(f"  ERROR: {e}")
        sys.exit(1)

    # Composite and show samples
    print("[Fio] Compositing samples (first 3 frames)...")
    speed_composite = compose_overlay(base, speed_frames[:3], blend_mode='screen', alpha=0.5)
    impact_composite = compose_overlay(base, impact_frames[:3], blend_mode='screen', alpha=0.7)

    # Create comparison tiles: base | speed | impact
    tile_width = 480
    tile_height = int(tile_width * 816 / 1920)
    base_tile = base.resize((tile_width, tile_height), Image.LANCZOS)
    speed_tile = speed_composite[1].resize((tile_width, tile_height), Image.LANCZOS)  # Frame 1
    impact_tile = impact_composite[0].resize((tile_width, tile_height), Image.LANCZOS)  # Frame 0

    # Horizontal layout: base | speed | impact
    comparison = Image.new("RGB", (tile_width * 3, tile_height), (20, 20, 20))
    comparison.paste(base_tile, (0, 0))
    comparison.paste(speed_tile, (tile_width, 0))
    comparison.paste(impact_tile, (tile_width * 2, 0))

    # Add labels
    from PIL import ImageFont
    draw = ImageDraw.Draw(comparison)
    # Try default font; fallback to ImageFont.load_default()
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except:
        font = ImageFont.load_default()

    draw.text((10, 10), "BASE", fill=(200, 200, 200), font=font)
    draw.text((tile_width + 10, 10), "SPEED_LINES", fill=(200, 200, 200), font=font)
    draw.text((tile_width * 2 + 10, 10), "IMPACT_FLASH", fill=(200, 200, 200), font=font)

    out_comparison = "/home/user/Video/build/overlays/fio_s39_compare.jpg"
    comparison.save(out_comparison)
    print(f"[Fio] Comparison saved: {out_comparison}")

    # Contact sheets
    print("[Fio] Creating contact sheets...")
    contact_speed = "/home/user/Video/build/overlays/fio_s39_speed_contact.jpg"
    contact_impact = "/home/user/Video/build/overlays/fio_s39_impact_contact.jpg"
    make_contact_sheet(speed_composite, contact_speed, n_frames=6, frame_width=240)
    make_contact_sheet(impact_composite, contact_impact, n_frames=6, frame_width=240)
    print(f"  → {contact_speed}")
    print(f"  → {contact_impact}")

    print("[Fio] Done.")
