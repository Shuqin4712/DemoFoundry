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

The second run also checks the generated fixture with HyperFrames from the current npm `latest` tag (needs network and a browser).
On different cache/project drives, uv automatically copies files instead of hardlinking; this is harmless.
Use `--link-mode copy` to suppress that warning.

Requires Python 3.10+, numpy, ffmpeg; Node 22+ for HyperFrames. Optional extras: `whisper` (transcription), `image` (Pillow).


P3 audio commands (run from the repository root; add the installed engine path when using skills):

```powershell
# Model download is explicit. Default cache: ~/.cache/demofoundry.
uv run --locked --extra local --project skills/demofoundry/engine demofoundry tts setup
uv run --locked --extra local --project skills/demofoundry/engine demofoundry tts generate path/to/voice.json --take local-01
uv run --locked --extra local --project skills/demofoundry/engine demofoundry voice promote path/to/voice.json --take local-01
uv run --locked --project skills/demofoundry/engine demofoundry srt path/to/voice/final path/to/publish/episode.srt
# Explicit final mastering; inspect measured loudness again after AAC encoding.
uv run --locked --project skills/demofoundry/engine demofoundry master raw.mp4 episode.mp4
```

Set `engine` to `kokoro`, `voice_id` to `af_sarah`, and optionally `transcribe_model` to `tiny.en` (smoke test) or `small.en` (default).
Kokoro synthesizes paragraphs; faster-whisper supplies estimated word timestamps, aligned to the original script.
Check `provider.json` for alignment warnings and listen before accepting a take; text alignment alone does not prove correct pronunciation.
`DEMOFOUNDRY_MODEL_DIR` overrides the Kokoro model cache. Model weights are downloaded, not redistributed.

ElevenLabs uses `engine: elevenlabs`, a `voice_id`, and `ELEVENLABS_API_KEY` in the environment.
It calls the paid `with-timestamps` endpoint only when explicitly requested through `tts generate`.
The adapter converts native character times into words. Its network path has not been exercised with a paid key.
Imported recordings continue to use `voice import` by default.

Music commands: `bgm trim`, `bgm extend` (explicit phrase boundaries; needs `--extra local`), and
`bgm register` (source URL, license, attribution and file SHA-256). Extension requires listening to the seams.
Upstream music search/generation remains delegated to `media-use`; catalog retrieval requires HeyGen CLI authentication.
No account is needed to import a track you already have permission to use.

Reproduce a free speech-to-MP4 smoke run without overwriting the synthetic byte-regression fixture:

```powershell
uv run --locked --extra local --project skills/demofoundry/engine python tests/run_p3.py --out .tmp/my-p3-run --render
```

The output directory must be new. It includes check/render logs, the actual HyperFrames version in `run.json`,
real narration, captions and a 1080p60 MP4. It deliberately does not invent or fetch background music.
Python dependencies remain locked by uv; HyperFrames commands now use `@latest` by project decision.
