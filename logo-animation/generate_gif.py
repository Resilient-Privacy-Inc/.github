#!/usr/bin/env python3
"""Generate a clean 3D ASCII logo GIF for the GitHub profile README.

Treats the logo as a flat plate in 3D (preserves the mark), projects with
yaw/tilt + lighting, thickens strokes, then converts to ASCII glyphs.
"""

from __future__ import annotations

import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
LOGO_PATH = ROOT / "logo" / "logo-example.png"
OUT_GIF = ROOT / "profile" / "logo-animation.gif"
PREVIEW_DIR = ROOT / "profile" / "_preview"

PLATE = 300
OUT_BUF = 440

COLS = 76
ROWS = 42
CELL_W = 8
CELL_H = 14
CHARS = " .:-=+*#%@"
NUM_CHARS = len(CHARS)

FRAMES = 48
YAW_AMP = 0.50
TILT_BASE = 0.28
TILT_AMP = 0.05
FOCAL = 700.0
ZOOM = 1.08

LIGHT = (-0.4, -0.3, 0.85)
AMBIENT = 0.40
DIFFUSE = 0.60

PALETTE = [
    (10, 28, 42),
    (18, 70, 98),
    (30, 130, 155),
    (45, 185, 185),
    (70, 220, 205),
    (120, 240, 225),
]


def lerp_color(t: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    scaled = t * (len(PALETTE) - 1)
    i = int(scaled)
    f = scaled - i
    c1 = PALETTE[i]
    c2 = PALETTE[min(i + 1, len(PALETTE) - 1)]
    return (
        int(c1[0] + (c2[0] - c1[0]) * f),
        int(c1[1] + (c2[1] - c1[1]) * f),
        int(c1[2] + (c2[2] - c1[2]) * f),
    )


def load_plate(path: Path, size: int) -> Image.Image:
    src = Image.open(path).convert("L")
    ink = src.point(lambda p: 255 if p > 28 else 0)
    bbox = ink.getbbox()
    if not bbox:
        raise RuntimeError("Logo appears empty")
    pad = 44
    x0, y0, x1, y1 = bbox
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(src.width, x1 + pad), min(src.height, y1 + pad)
    cropped = ink.crop((x0, y0, x1, y1))
    # Thicken just enough for ASCII survival; eyes stay open
    cropped = cropped.filter(ImageFilter.MaxFilter(3))
    fitted = ImageOps.contain(cropped, (size, size), method=Image.Resampling.NEAREST)
    plate = Image.new("L", (size, size), 0)
    plate.paste(fitted, ((size - fitted.width) // 2, (size - fitted.height) // 2))
    return plate


def project_plate(plate: Image.Image, yaw: float, tilt: float) -> Image.Image:
    w = h = plate.size[0]
    out_w = out_h = OUT_BUF
    bright = [[0.0] * out_w for _ in range(out_h)]
    zbuf = [[-1e9] * out_w for _ in range(out_h)]

    cos_y, sin_y = math.cos(yaw), math.sin(yaw)
    cos_t, sin_t = math.cos(tilt), math.sin(tilt)
    lx, ly, lz = LIGHT

    # Rotated plate normal
    rnx, rny, rnz = sin_y, -sin_t * cos_y, cos_t * cos_y
    nlen = math.sqrt(rnx * rnx + rny * rny + rnz * rnz) or 1.0
    rnx, rny, rnz = rnx / nlen, rny / nlen, rnz / nlen
    lighting = AMBIENT + DIFFUSE * abs(rnx * lx + rny * ly + rnz * lz)

    cx, cy = out_w / 2.0, out_h / 2.0
    scale = min(out_w, out_h) * ZOOM / w
    pix = plate.load()

    for py in range(h):
        for px in range(w):
            if pix[px, py] < 128:
                continue
            x = (px - w / 2.0) * scale
            y = (py - h / 2.0) * scale

            rx = x * cos_y
            rz = -x * sin_y
            ry = y * cos_t - rz * sin_t
            rz = y * sin_t + rz * cos_t

            proj = FOCAL / (FOCAL + rz)
            sx = cx + rx * proj
            sy = cy + ry * proj
            b = min(1.0, lighting)

            for oy in (0.0, 0.35):
                for ox in (0.0, 0.35):
                    ix = int(sx + ox)
                    iy = int(sy + oy)
                    if 0 <= ix < out_w and 0 <= iy < out_h and rz >= zbuf[iy][ix]:
                        zbuf[iy][ix] = rz
                        bright[iy][ix] = b

    img = Image.new("L", (out_w, out_h), 0)
    op = img.load()
    for y in range(out_h):
        for x in range(out_w):
            if bright[y][x] > 0:
                op[x, y] = int(bright[y][x] * 255)

    # Close pinholes, light thicken — keep eye / crest gaps open
    img = img.filter(ImageFilter.MaxFilter(3))
    img = img.filter(ImageFilter.MinFilter(3))
    img = img.filter(ImageFilter.MaxFilter(3))
    return img


def ascii_from_buffer(buf: Image.Image, font: ImageFont.ImageFont | ImageFont.FreeTypeFont) -> Image.Image:
    small = buf.resize((COLS, ROWS), Image.Resampling.BOX)
    sp = small.load()
    out = Image.new("RGB", (COLS * CELL_W, ROWS * CELL_H), (5, 6, 10))
    draw = ImageDraw.Draw(out)

    for y in range(ROWS):
        for x in range(COLS):
            v = sp[x, y] / 255.0
            if v < 0.18:
                continue
            # Bias toward heavy glyphs — logo strokes should read solid
            t = 0.50 + 0.50 * v
            ci = max(1, min(NUM_CHARS - 1, int(t * (NUM_CHARS - 1) + 0.5)))
            if v > 0.40:
                ci = max(ci, 7)  # '#' or denser
            ch = CHARS[ci]
            color = lerp_color(0.35 + 0.55 * v)
            draw.text((x * CELL_W + 1, y * CELL_H), ch, fill=color, font=font)
    return out


def get_font(size: int) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    for path in (
        r"C:\Windows\Fonts\consola.ttf",
        r"C:\Windows\Fonts\cour.ttf",
        r"C:\Windows\Fonts\lucon.ttf",
    ):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                pass
    return ImageFont.load_default()


def tight_crop(frames: list[Image.Image], pad: int = 16) -> list[Image.Image]:
    union = None
    for fr in frames:
        mask = fr.convert("L").point(lambda p: 255 if p > 14 else 0)
        bbox = mask.getbbox()
        if not bbox:
            continue
        if union is None:
            union = list(bbox)
        else:
            union[0] = min(union[0], bbox[0])
            union[1] = min(union[1], bbox[1])
            union[2] = max(union[2], bbox[2])
            union[3] = max(union[3], bbox[3])
    if union is None:
        return frames
    x0 = max(0, union[0] - pad)
    y0 = max(0, union[1] - pad)
    x1 = min(frames[0].width, union[2] + pad)
    y1 = min(frames[0].height, union[3] + pad)
    if (x1 - x0) % 2:
        x1 = min(frames[0].width, x1 + 1)
    if (y1 - y0) % 2:
        y1 = min(frames[0].height, y1 + 1)
    return [fr.crop((x0, y0, x1, y1)) for fr in frames]


def main() -> None:
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    print("Loading plate...")
    plate = load_plate(LOGO_PATH, PLATE)
    plate.save(PREVIEW_DIR / "plate.png")
    font = get_font(size=CELL_H)

    print(f"Rendering {FRAMES} frames...")
    frames: list[Image.Image] = []
    for i in range(FRAMES):
        phase = (i / FRAMES) * math.tau
        yaw = math.sin(phase) * YAW_AMP
        tilt = TILT_BASE + math.sin(phase * 2.0) * TILT_AMP
        shaded = project_plate(plate, yaw, tilt)
        frame = ascii_from_buffer(shaded, font)
        frames.append(frame)
        if i % 12 == 0:
            shaded.save(PREVIEW_DIR / f"shade_{i:02d}.png")
            frame.save(PREVIEW_DIR / f"gen_{i:02d}.png")
            print(f"  frame {i}/{FRAMES}")

    frames = tight_crop(frames, pad=18)
    target_w = 440
    frames = [
        fr.resize(
            (target_w, max(1, int(fr.height * target_w / fr.width))),
            Image.Resampling.NEAREST,
        )
        for fr in frames
    ]

    for i in (0, FRAMES // 4, FRAMES // 2):
        frames[i].save(PREVIEW_DIR / f"final_{i:02d}.png")

    # Text dump of center frame for sanity checks
    center = project_plate(plate, 0.0, TILT_BASE)
    small = center.resize((COLS, ROWS), Image.Resampling.BOX)
    sp = small.load()
    lines = []
    for y in range(ROWS):
        row = []
        for x in range(COLS):
            v = sp[x, y] / 255.0
            if v < 0.18:
                row.append(" ")
            else:
                ci = 7 if v > 0.45 else max(1, int((0.45 + 0.55 * v) * (NUM_CHARS - 1)))
                row.append(CHARS[min(NUM_CHARS - 1, ci)])
        lines.append("".join(row).rstrip())
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    (PREVIEW_DIR / "ascii_center.txt").write_text("\n".join(lines), encoding="utf-8")

    print(f"Writing GIF -> {OUT_GIF}")
    frames[0].save(
        OUT_GIF,
        save_all=True,
        append_images=frames[1:],
        duration=55,
        loop=0,
        optimize=True,
        disposal=2,
    )
    size_kb = OUT_GIF.stat().st_size / 1024
    print(f"Done: {frames[0].size[0]}x{frames[0].size[1]}, {len(frames)} frames, {size_kb:.0f} KB")


if __name__ == "__main__":
    main()
