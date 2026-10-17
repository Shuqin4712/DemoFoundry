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

Run from the product repository root (use the installed engine's path after skill installation):

```powershell
uv run --locked --project skills/demofoundry/engine demofoundry recording --help
uv run --locked --project skills/demofoundry/engine demofoundry gen tests/fixtures/jot/demofoundry/episodes/01-quick-note
```

`uv` creates an isolated `.venv` inside the engine and installs the dependencies in `uv.lock`.
No activation or global numpy installation is needed. If `uv` is not on PATH yet, use `python -m uv` in its place.
Install uv with `python -m pip install --user uv` when Python is already available.
Commit `uv.lock`; use `--locked` so normal runs cannot silently change dependency versions.
The `whisper` and `image` extras are resolved in the lock but installed only when requested with `--extra whisper` or `--extra image`.
Node and ffmpeg remain system prerequisites.

Run the regression suite from the DemoFoundry repository root:

```powershell
uv run --locked --project skills/demofoundry/engine python -m unittest discover -s tests -v
$env:DF_HF_CHECK = '1'
uv run --locked --project skills/demofoundry/engine python -m unittest discover -s tests -v
```

The second run also checks the generated fixture with HyperFrames 0.8.114 (needs network and a browser).
On different cache/project drives, uv automatically copies files instead of hardlinking; this is harmless.
Use `--link-mode copy` to suppress that warning.

Requires Python 3.10+, numpy, ffmpeg; Node 22+ for HyperFrames. Optional extras: `whisper` (transcription), `image` (Pillow).
