"""Fit a music bed to an episode.

  python -m demofoundry bgm trim <source.wav> <total seconds> <out track.wav> [--from 3.0] [--fade-in 1.2] [--fade-out 2.5]

Rules this follows (measured on reference tutorials):
- buy / pick a **flat** track (loudness steady within ~5 dB); the shape of the episode comes from
  volume automation on the ``<audio id="bgm">`` element, not from the music;
- always cut from the full source, never from a previous episode's track (it only has that episode's length);
- the trim is baked into the wav, so a changed episode length needs a new trim (the fade-out must land on the end).
"""
import argparse
import json
from pathlib import Path
import tempfile
import numpy as np

from . import av, which


def trim(src, total, out, start=0.0, fade_in=1.2, fade_out=2.5):
    if total <= 0 or start < 0 or min(fade_in, fade_out) < 0 or max(fade_in, fade_out) > total:
        raise ValueError('invalid duration, offset or fades')
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    av.run([which.ffmpeg(), '-v', 'error', '-y', '-ss', str(start), '-t', str(total), '-i', src,
            '-af', f'afade=t=in:st=0:d={fade_in},afade=t=out:st={total - fade_out:.2f}:d={fade_out}', '-c:a', 'pcm_s16le', out])


def extend(src, total, out, loop_start, loop_end, crossfade=0.03):
    """Repeat an explicitly chosen musical phrase, preserving the original ending.

    The user/agent supplies phrase boundaries; this does not pretend to detect beats.
    Equal-power crossfades hide discontinuities. Listen to each seam before publishing.
    """
    import soundfile as sf
    x, sr = sf.read(src, always_2d=True)
    duration = len(x) / sr
    if not 0 <= loop_start < loop_end <= duration or total <= 0:
        raise ValueError('loop must lie inside source; total must be positive')
    if not 0 < crossfade < (loop_end - loop_start) / 2:
        raise ValueError('crossfade must be positive and shorter than half a phrase')
    a, b, n = round(loop_start * sr), round(loop_end * sr), round(crossfade * sr)
    phrase = x[a:b].copy()
    ramp = np.linspace(0, np.pi / 2, n)[:, None]
    seams = []
    # Keep the source ending. Insert whole phrases before its tail; trim only excess lead-in.
    while len(x) / sr < total:
        seams.append(b / sr)
        x = np.concatenate([x[:b - n], x[b - n:b] * np.cos(ramp) + phrase[:n] * np.sin(ramp), phrase[n:], x[b:]])
        b += len(phrase) - n
    with tempfile.TemporaryDirectory() as td:
        temp = Path(td) / 'extended.wav'
        sf.write(temp, x, sr, subtype='PCM_16')
        offset = len(x) / sr - total
        trim(str(temp), total, out, offset, min(1.2, total / 3), min(2.5, total / 3))
    return {'source': str(src), 'loop': [loop_start, loop_end], 'crossfade': crossfade,
            'total': total, 'insertions': len(seams), 'review_required': True}


def register(src, ledger, source_url, license_name, attribution):
    """Record supplied licensing facts; this does not certify redistribution permission."""
    import hashlib
    if not source_url or not license_name or not attribution:
        raise ValueError('source URL, license and attribution are required')
    path = Path(ledger)
    rows = json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    row = {'file': str(src), 'source': source_url, 'license': license_name, 'attribution': attribution,
           'sha256': hashlib.sha256(Path(src).read_bytes()).hexdigest()}
    rows = [r for r in rows if r['sha256'] != row['sha256']] + [row]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    return row


def main(argv=None):
    ap = argparse.ArgumentParser(prog='demofoundry bgm', description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    t = sub.add_parser('trim')
    t.add_argument('src'); t.add_argument('total', type=float); t.add_argument('out')
    t.add_argument('--from', dest='start', type=float, default=0.0)
    t.add_argument('--fade-in', type=float, default=1.2); t.add_argument('--fade-out', type=float, default=2.5)
    e = sub.add_parser('extend')
    e.add_argument('src'); e.add_argument('total', type=float); e.add_argument('out')
    e.add_argument('--loop-start', type=float, required=True); e.add_argument('--loop-end', type=float, required=True)
    e.add_argument('--crossfade', type=float, default=0.03)
    r = sub.add_parser('register')
    r.add_argument('src'); r.add_argument('ledger')
    r.add_argument('--source-url', required=True); r.add_argument('--license', required=True)
    r.add_argument('--attribution', required=True)
    a = ap.parse_args(argv)
    if a.cmd == 'extend':
        result = extend(a.src, a.total, a.out, a.loop_start, a.loop_end, a.crossfade)
        Path(a.out + '.json').write_text(json.dumps(result, indent=2), encoding='utf-8', newline='\n')
        print(f'{a.out}: {result["insertions"]} phrase insertions; listen to the seams')
        return
    if a.cmd == 'register':
        register(a.src, a.ledger, a.source_url, a.license, a.attribution)
        return
    src_len = av.probe_audio(a.src)
    if a.start + a.total > src_len + 0.01:
        av.die(f'the source has {src_len:.2f}s from 0; {a.total}s from {a.start}s does not fit (extend the track first)')
    trim(a.src, a.total, a.out, a.start, a.fade_in, a.fade_out)
    print(f'✓ {a.out} {a.total}s (from {a.start}s, fade in {a.fade_in}s / out {a.fade_out}s)')
