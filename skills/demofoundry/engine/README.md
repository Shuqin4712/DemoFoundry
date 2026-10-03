# DemoFoundry engine

Python package that turns an episode generator into HyperFrames compositions, plus the media tools around it.
Shared by the `demofoundry-mold` and `demofoundry-episode` skills (they reference this folder as `../demofoundry/engine/`).

| Module | What it does |
| --- | --- |
| `hf` | Everything HyperFrames-specific: GSAP timeline lines, sub-composition shell, `index.html`, audio attributes |
| `cues` | Cue timeline: word times scoped by narration clip |
| `stage` | Camera (named shots + moves) and the oversized cursor |
| `fx` | Strokes, wipe reveal, typing, fly-in |
| `geom` | Wires between nodes |
| `scene` | Scene-level helpers: state swaps, generate → result, explanation marks, media placeholders |
| `intro` | Series intro and end card |
| `theme` / `studio` | Series look; the `demofoundry/` folder (config, mold `ui.py`, mold asset sync) |
| `voice` | Recordings → aligned, checked, cut, laid-out narration |
| `recording` | Index a product screen recording; crop evidence frames |
| `refprofile` | Measure screenshots into JSON |
| `bgm`, `av`, `fingerprint`, `serve`, `which`, `io` | Music trim, ffmpeg helpers, probe pages, no-cache server, cross-platform program lookup, UTF-8 / LF files |

Run a command:

```bash
python -m demofoundry <command> --help
```

Requires Python 3.10+, numpy, ffmpeg; Node 22+ for HyperFrames. Optional extras: `whisper` (transcription), `image` (Pillow).
