#!/usr/bin/env python3
"""Build standalone HTML animation with embedded logo PNG."""

from __future__ import annotations

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOGO = ROOT / "logo" / "logo-example.png"
OUTS = [
    ROOT / "logo-animation" / "index.html",
    ROOT / "profile" / "logo-animation.html",
]

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Resilient Privacy — 3D ASCII Logo</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: #050608;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    font-family: Consolas, "Courier New", monospace;
  }
  canvas { display: block; image-rendering: pixelated; }
  #loading {
    color: #4a7a88;
    font-size: 13px;
    letter-spacing: 0.08em;
  }
</style>
</head>
<body>
<div id="loading">Initializing 3D ASCII…</div>
<canvas id="view"></canvas>
<script>
(function () {
  const COLS = 76;
  const ROWS = 42;
  const CELL_W = 8;
  const CELL_H = 14;
  const CHARS = " .:-=+*#%@";
  const YAW_AMP = 0.50;
  const TILT_BASE = 0.28;
  const TILT_AMP = 0.05;
  const FOCAL = 700;
  const ZOOM = 1.08;
  const LIGHT = [-0.4, -0.3, 0.85];
  const AMBIENT = 0.40;
  const DIFFUSE = 0.60;
  const PALETTE = [
    [10, 28, 42],
    [18, 70, 98],
    [30, 130, 155],
    [45, 185, 185],
    [70, 220, 205],
    [120, 240, 225],
  ];
  const LOGO_B64 = "__LOGO_B64__";

  const loading = document.getElementById("loading");
  const view = document.getElementById("view");
  const vctx = view.getContext("2d");
  view.width = COLS * CELL_W;
  view.height = ROWS * CELL_H;

  function lerpColor(t) {
    t = Math.max(0, Math.min(1, t));
    const scaled = t * (PALETTE.length - 1);
    const i = Math.floor(scaled);
    const f = scaled - i;
    const c1 = PALETTE[i];
    const c2 = PALETTE[Math.min(i + 1, PALETTE.length - 1)];
    return [
      (c1[0] + (c2[0] - c1[0]) * f) | 0,
      (c1[1] + (c2[1] - c1[1]) * f) | 0,
      (c1[2] + (c2[2] - c1[2]) * f) | 0,
    ];
  }

  function thicken(src, w, h) {
    const out = new Uint8ClampedArray(w * h);
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        let m = 0;
        for (let dy = -1; dy <= 1; dy++) {
          for (let dx = -1; dx <= 1; dx++) {
            const xx = Math.min(w - 1, Math.max(0, x + dx));
            const yy = Math.min(h - 1, Math.max(0, y + dy));
            m = Math.max(m, src[yy * w + xx]);
          }
        }
        out[y * w + x] = m;
      }
    }
    return out;
  }

  function minify(src, w, h) {
    const out = new Uint8ClampedArray(w * h);
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        let m = 255;
        for (let dy = -1; dy <= 1; dy++) {
          for (let dx = -1; dx <= 1; dx++) {
            const xx = Math.min(w - 1, Math.max(0, x + dx));
            const yy = Math.min(h - 1, Math.max(0, y + dy));
            m = Math.min(m, src[yy * w + xx]);
          }
        }
        out[y * w + x] = m;
      }
    }
    return out;
  }

  function loadPlate(img) {
    const SIZE = 300;
    const c = document.createElement("canvas");
    c.width = SIZE;
    c.height = SIZE;
    const ctx = c.getContext("2d");
    ctx.fillStyle = "#000";
    ctx.fillRect(0, 0, SIZE, SIZE);
    const scale = Math.min(SIZE / img.width, SIZE / img.height) * 0.86;
    const dw = img.width * scale;
    const dh = img.height * scale;
    ctx.drawImage(img, (SIZE - dw) / 2, (SIZE - dh) / 2, dw, dh);
    const data = ctx.getImageData(0, 0, SIZE, SIZE).data;
    let plate = new Uint8ClampedArray(SIZE * SIZE);
    for (let i = 0; i < SIZE * SIZE; i++) {
      const v = (data[i * 4] + data[i * 4 + 1] + data[i * 4 + 2]) / 3;
      plate[i] = v > 28 ? 255 : 0;
    }
    plate = thicken(plate, SIZE, SIZE);
    return { plate, size: SIZE };
  }

  function project(plate, size, yaw, tilt) {
    const OUT = 440;
    const bright = new Float32Array(OUT * OUT);
    const zbuf = new Float32Array(OUT * OUT);
    zbuf.fill(-1e9);

    const cosY = Math.cos(yaw), sinY = Math.sin(yaw);
    const cosT = Math.cos(tilt), sinT = Math.sin(tilt);
    let rnx = sinY, rny = -sinT * cosY, rnz = cosT * cosY;
    const nlen = Math.hypot(rnx, rny, rnz) || 1;
    rnx /= nlen; rny /= nlen; rnz /= nlen;
    const lighting = AMBIENT + DIFFUSE * Math.abs(
      rnx * LIGHT[0] + rny * LIGHT[1] + rnz * LIGHT[2]
    );

    const cx = OUT / 2, cy = OUT / 2;
    const scale = (Math.min(OUT, OUT) * ZOOM) / size;

    for (let py = 0; py < size; py++) {
      for (let px = 0; px < size; px++) {
        if (plate[py * size + px] < 128) continue;
        const x = (px - size / 2) * scale;
        const y = (py - size / 2) * scale;
        let rx = x * cosY;
        let rz = -x * sinY;
        let ry = y * cosT - rz * sinT;
        rz = y * sinT + rz * cosT;
        const proj = FOCAL / (FOCAL + rz);
        const sx = cx + rx * proj;
        const sy = cy + ry * proj;
        for (let oy = 0; oy <= 0.35; oy += 0.35) {
          for (let ox = 0; ox <= 0.35; ox += 0.35) {
            const ix = (sx + ox) | 0;
            const iy = (sy + oy) | 0;
            if (ix < 0 || ix >= OUT || iy < 0 || iy >= OUT) continue;
            const idx = iy * OUT + ix;
            if (rz >= zbuf[idx]) {
              zbuf[idx] = rz;
              bright[idx] = lighting;
            }
          }
        }
      }
    }

    let img = new Uint8ClampedArray(OUT * OUT);
    for (let i = 0; i < OUT * OUT; i++) {
      img[i] = bright[i] > 0 ? (bright[i] * 255) | 0 : 0;
    }
    img = thicken(img, OUT, OUT);
    img = minify(img, OUT, OUT);
    img = thicken(img, OUT, OUT);
    return { img, w: OUT, h: OUT };
  }

  function toAscii(buf) {
    const { img, w, h } = buf;
    const cells = new Float32Array(COLS * ROWS);
    const cellW = w / COLS, cellH = h / ROWS;
    for (let row = 0; row < ROWS; row++) {
      for (let col = 0; col < COLS; col++) {
        let sum = 0, n = 0;
        const x0 = (col * cellW) | 0, x1 = ((col + 1) * cellW) | 0;
        const y0 = (row * cellH) | 0, y1 = ((row + 1) * cellH) | 0;
        for (let y = y0; y < y1; y++) {
          for (let x = x0; x < x1; x++) {
            sum += img[y * w + x];
            n++;
          }
        }
        cells[row * COLS + col] = n ? sum / n / 255 : 0;
      }
    }
    return cells;
  }

  function drawAscii(cells) {
    vctx.fillStyle = "#050608";
    vctx.fillRect(0, 0, view.width, view.height);
    vctx.font = CELL_H + 'px Consolas, "Courier New", monospace';
    vctx.textBaseline = "top";
    for (let y = 0; y < ROWS; y++) {
      for (let x = 0; x < COLS; x++) {
        const v = cells[y * COLS + x];
        if (v < 0.18) continue;
        const t = 0.50 + 0.50 * v;
        let ci = Math.max(1, Math.min(CHARS.length - 1, (t * (CHARS.length - 1) + 0.5) | 0));
        if (v > 0.40) ci = Math.max(ci, 7);
        const col = lerpColor(0.35 + 0.55 * v);
        vctx.fillStyle = "rgb(" + col[0] + "," + col[1] + "," + col[2] + ")";
        vctx.fillText(CHARS[ci], x * CELL_W + 1, y * CELL_H);
      }
    }
  }

  const img = new Image();
  img.onload = function () {
    const { plate, size } = loadPlate(img);
    loading.style.display = "none";
    let t0 = performance.now();
    function frame(now) {
      const t = (now - t0) / 1000;
      const phase = t * 0.55;
      const yaw = Math.sin(phase) * YAW_AMP;
      const tilt = TILT_BASE + Math.sin(phase * 2) * TILT_AMP;
      drawAscii(toAscii(project(plate, size, yaw, tilt)));
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  };
  img.onerror = function () {
    loading.textContent = "Failed to load logo";
  };
  img.src = "data:image/png;base64," + LOGO_B64;
})();
</script>
</body>
</html>
"""


def main() -> None:
    b64 = base64.b64encode(LOGO.read_bytes()).decode("ascii")
    html = TEMPLATE.replace("__LOGO_B64__", b64)
    for out in OUTS:
        out.write_text(html, encoding="utf-8")
        print(f"wrote {out} ({len(html)} bytes)")


if __name__ == "__main__":
    main()
