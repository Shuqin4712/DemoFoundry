"""Fit a music bed to an episode.

  python -m demofoundry bgm trim <source.wav> <total seconds> <out track.wav> [--from 3.0] [--fade-in 1.2] [--fade-out 2.5]

Rules this follows (measured on reference tutorials):
- buy / pick a **flat** track (loudness steady within ~5 dB); the shape of the episode comes from
  volume automation on the ``<audio id="bgm">`` element, not from the music;
- always cut from the full source, never from a previous episode's track (it only has that episode's length);
- the trim is baked into the wav, so a changed episode length needs a new trim (the fade-out must land on the end).
"""
import argparse

from . import av, which


def trim(src, total, out, start=0.0, fade_in=1.2, fade_out=2.5):
    av.run([which.ffmpeg(), '-v', 'error', '-y', '-ss', str(start), '-t', str(total), '-i', src,
            '-af', f'afade=t=in:st=0:d={fade_in},afade=t=out:st={total - fade_out:.2f}:d={fade_out}', '-c:a', 'pcm_s16le', out])


def main(argv=None):
    ap = argparse.ArgumentParser(prog='demofoundry bgm', description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    t = sub.add_parser('trim')
    t.add_argument('src'); t.add_argument('total', type=float); t.add_argument('out')
    t.add_argument('--from', dest='start', type=float, default=0.0)
    t.add_argument('--fade-in', type=float, default=1.2); t.add_argument('--fade-out', type=float, default=2.5)
    a = ap.parse_args(argv)
    src_len = av.probe_audio(a.src)
    if a.start + a.total > src_len + 0.01:
        av.die(f'the source has {src_len:.2f}s from 0; {a.total}s from {a.start}s does not fit (extend the track first)')
    trim(a.src, a.total, a.out, a.start, a.fade_in, a.fade_out)
    print(f'✓ {a.out} {a.total}s (from {a.start}s, fade in {a.fade_in}s / out {a.fade_out}s)')
