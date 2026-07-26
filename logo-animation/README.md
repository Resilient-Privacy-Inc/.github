# Logo Animation

3D ASCII animation of the Resilient Privacy owl mark — flat-plate projection with yaw/tilt, then ASCII conversion.

## Generate the profile GIF

```bash
python logo-animation/generate_gif.py
```

Writes `profile/logo-animation.gif` (embedded in `profile/README.md`).

## Interactive HTML

```bash
python logo-animation/build_html.py
```

Rebuilds `logo-animation/index.html` and `profile/logo-animation.html` with the logo PNG embedded.

Open either HTML file in a browser for the live animation.

## Embed in the profile README

GitHub strips scripts from READMEs, so the profile uses the GIF:

```markdown
<a href="logo-animation.html">
  <img src="logo-animation.gif" width="420" alt="Resilient Privacy · 3D ASCII Logo Animation" />
</a>
```

## Tuning

Edit constants at the top of `generate_gif.py` / `build_html.py`:

| Constant | Effect |
|---|---|
| `COLS` / `ROWS` | ASCII resolution |
| `YAW_AMP` | Side-to-side swing |
| `TILT_BASE` | Fixed X tilt |
| `CHARS` | ASCII density ramp |
