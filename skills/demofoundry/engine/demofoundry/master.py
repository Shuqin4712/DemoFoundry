"""Two-pass final loudness normalization. Keeps the picture stream unchanged."""
import argparse
import json
import math
from pathlib import Path
import re
import subprocess

from . import which


def normalize(source, output, target=-16, peak=-1):
    if Path(source).resolve() == Path(output).resolve():
        raise ValueError('output must differ from source')
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    settings = f'I={target}:TP={peak}:LRA=11'
    scan = subprocess.run([which.ffmpeg(), '-nostats', '-i', str(source), '-af',
                           f'loudnorm={settings}:print_format=json', '-f', 'null', '-'],
                          capture_output=True, text=True, encoding='utf-8', errors='replace', check=True)
    result = json.loads(re.findall(r'\{[^{}]*"input_i"[^{}]*\}', scan.stderr)[-1])
    if not all(math.isfinite(float(result[key])) for key in ('input_i', 'input_tp', 'input_lra', 'input_thresh', 'target_offset')):
        raise ValueError('non-finite loudness measurement; verify that the input contains audible speech')
    params = ':'.join(f'{key}={result[value]}' for key, value in {
        'measured_I': 'input_i', 'measured_TP': 'input_tp', 'measured_LRA': 'input_lra',
        'measured_thresh': 'input_thresh', 'offset': 'target_offset'}.items())
    subprocess.run([which.ffmpeg(), '-y', '-v', 'error', '-i', str(source), '-map', '0:v?', '-map', '0:a:0',
                    '-c:v', 'copy', '-af', f'loudnorm={settings}:{params}:linear=true',
                    '-ar', '48000', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(output)], check=True)
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source'); ap.add_argument('output')
    args = ap.parse_args(argv)
    print(json.dumps(normalize(args.source, args.output), indent=2))
