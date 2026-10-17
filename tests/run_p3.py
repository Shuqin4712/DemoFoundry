"""Free end-to-end P3 smoke run in a separate workspace, keeping the byte baseline intact.

uv run --locked --extra local --project skills/demofoundry/engine python tests/run_p3.py --out .tmp/p3-smoke --render
The first run downloads Kokoro and faster-whisper models. No API keys or paid services.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.request import urlopen

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'skills/demofoundry/engine'))
from demofoundry import hf, master, srt, tts, voice, which


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    ap.add_argument('--model', default='tiny.en')
    ap.add_argument('--render', action='store_true')
    args = ap.parse_args()
    root = Path(args.out).resolve()
    if root.exists():
        raise ValueError('use a new output directory to preserve previous runs')
    shutil.copytree(REPO / 'tests/fixtures/jot', root, ignore=shutil.ignore_patterns('__pycache__', '_takes', '.hyperframes'))
    ep = root / 'demofoundry/episodes/01-quick-note'
    spec_path = ep / 'voice/voice.json'
    config = json.loads(spec_path.read_text(encoding='utf-8'))
    config.update(engine='kokoro', voice_id='af_sarah', voice_name='Kokoro Sarah', transcribe_model=args.model)
    spec_path.write_text(json.dumps(config, indent=2), encoding='utf-8', newline='\n')
    tts.setup()
    take = Path(tts.generate(str(spec_path), 'local-01'))
    metadata = json.loads((take / 'provider.json').read_text(encoding='utf-8'))
    if metadata['review_required']:
        raise ValueError('alignment needs review; see provider.json before promoting')
    voice.cmd_promote(str(spec_path), 'local-01')
    subprocess.run([sys.executable, '-m', 'demofoundry', 'gen', str(ep)], check=True)
    # Cache the upstream pinned script in this disposable run, not in the repository.
    vendor = ep / 'assets/vendor/gsap.min.js'
    vendor.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(hf.GSAP_CDN, timeout=60) as response:
        vendor.write_bytes(response.read())
    index = ep / 'index.html'
    index.write_text(index.read_text(encoding='utf-8').replace(hf.GSAP_CDN, 'assets/vendor/gsap.min.js'), encoding='utf-8', newline='\n')
    publish = ep / 'publish'
    srt.export(ep / 'voice/final', publish / 'captions.srt')
    report = {'hyperframes_policy': 'latest', 'hyperframes_version': subprocess.check_output(
        [*which.npx(), '--yes', 'hyperframes@latest', '--version'], text=True).strip(), 'voice': metadata}
    (root / 'run.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    check = subprocess.run([*which.npx(), '--yes', 'hyperframes@latest', 'check', str(ep), '--no-browser-gpu', '--timeout', '10000'],
                           capture_output=True, timeout=180)
    (root / 'check.log').write_bytes(check.stdout + check.stderr)
    if check.returncode:
        raise RuntimeError(f'HyperFrames check failed: {root / "check.log"}')
    if args.render:
        raw = publish / 'raw.mp4'
        with (root / 'render.log').open('wb') as log:
            subprocess.run([*which.npx(), '--yes', 'hyperframes@latest', 'render', str(ep), '--fps', '60',
                            '--quality', 'draft', '--no-browser-gpu', '-o', str(raw)], stdout=log, stderr=log, check=True, timeout=600)
        master.normalize(raw, publish / 'episode.mp4')
    print(f'P3 smoke run: {root}', flush=True)


if __name__ == '__main__':
    main()
