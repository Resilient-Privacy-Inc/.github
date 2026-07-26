# Logo Animation

3D ASCII art animation of the Resilient Privacy logo, rendered in real-time in the browser.

## What It Does

- Rasterizes the company SVG logo to a hidden canvas
- Extracts a **height map** from pixel brightness (brighter = closer)
- Treats each pixel as a 3D point and applies a **Y-axis rotation** every frame
- Projects the rotating 3D points back to 2D with **perspective** and a **z-buffer**
- Maps depth/brightness to ASCII characters (` .:-=+*#%@`)
- Renders at 60 FPS with `requestAnimationFrame`

## How to Use

### Standalone

Open `index.html` in any modern browser. No server required — the SVG is embedded inline.

### Embed in a README

GitHub strips `<script>` and `<iframe>` tags from README markdown, so you can't embed the animation directly. Instead:

1. **Host the file** on GitHub Pages, your website, or any static host.
2. **Link to it** from your README:

```markdown
[![3D ASCII Logo](https://img.shields.io/badge/View-3D_ASCII_Animation-green?style=flat-square)](https://your-domain.com/logo-animation/index.html)
```

3. Or **record a GIF** of the animation and embed that:

```markdown
<img src="logo-animation.gif" width="400" alt="3D ASCII Logo Animation" />
```

## Configuration

Edit the constants at the top of `<script>` in `index.html`:

| Constant | Default | Effect |
|---|---|---|
| `COLS` | 100 | ASCII width (higher = more detail) |
| `ROWS` | 50 | ASCII height |
| `FOCAL` | 900 | Perspective focal length (higher = less distortion) |
| `ROT_SPEED` | 0.0072 | Rotation speed (radians/frame) |
| `TILT` | 0.15 | X-axis tilt for 3D feel (radians) |
| `DEPTH_SCALE` | 30 | How "thick" the 3D relief is |
| `CHARS` | `' .:-=+*#%@'` | ASCII ramp (dark → light) |

## Browser Support

Works in all modern browsers (Chrome, Firefox, Safari, Edge). Uses Canvas 2D API and `requestAnimationFrame`.
