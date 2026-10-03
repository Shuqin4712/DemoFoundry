"""ffmpeg / ffprobe helpers shared by the media tools, plus stills and play clips for episode media."""
import json
import os
import subprocess
import sys

import numpy as np

from . import which


def die(msg):
    sys.exit(f'✗ {msg}')


def run(args, **kw):
    r = subprocess.run(args, capture_output=True, **kw)
    if r.returncode:
        die(f'ffmpeg failed: {" ".join(str(a) for a in args[:8])}…\n{r.stderr.decode(errors="ignore")[-400:]}')
    return r.stdout


def probe(path):
    """{w, h, fps, dur}. Uses the video stream's duration: when the audio runs longer the container
    duration goes past the last frame and frame grabs come back empty."""
    o = json.loads(run([which.ffprobe(), '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                        'stream=width,height,r_frame_rate,duration:format=duration', '-of', 'json', path]))
    s = o['streams'][0]
    num, den = s['r_frame_rate'].split('/')
    dur = float(s.get('duration') or o['format']['duration'])
    return {'w': s['width'], 'h': s['height'], 'fps': round(int(num) / int(den), 3), 'dur': round(dur, 3)}


def probe_audio(path):
    """Duration of the first audio stream (s)."""
    o = json.loads(run([which.ffprobe(), '-v', 'error', '-select_streams', 'a:0', '-show_entries',
                        'stream=duration:format=duration', '-of', 'json', path]))
    s = (o.get('streams') or [{}])[0]
    return float(s.get('duration') or o['format']['duration'])


def frame_count(path):
    return int(run([which.ffprobe(), '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries',
                    'stream=nb_read_frames', '-of', 'csv=p=0', path]).decode().strip())


def gray_frames(path, w, h, fps=None):
    vf = (f'fps={fps},' if fps else '') + f'scale={w}:{h}'
    b = run([which.ffmpeg(), '-v', 'error', '-i', path, '-vf', vf, '-f', 'rawvideo', '-pix_fmt', 'gray', '-'])
    return np.frombuffer(b, dtype=np.uint8).astype(np.float32).reshape(-1, h, w)


def rgb_frame(path, t, w, h):
    b = run([which.ffmpeg(), '-v', 'error', '-ss', str(t), '-i', path, '-frames:v', '1', '-vf', f'scale={w}:{h}',
             '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
    return np.frombuffer(b, dtype=np.uint8).astype(np.float32).reshape(h, w, 3)


def save_png(path, arr):
    """H×W×3 uint8 → PNG through ffmpeg (no Pillow needed)."""
    h, w = arr.shape[:2]
    run([which.ffmpeg(), '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-i', '-', path],
        input=np.ascontiguousarray(arr, dtype=np.uint8).tobytes())


def extract_frames(src, indices, w, h, pattern):
    """Frames by index (seeking by time lands on neighbours), centre-cropped to w:h; numbered from 1 by pattern."""
    sel = '+'.join(f'eq(n\\,{i})' for i in indices)
    vf = f"select='{sel}',crop='min(iw,ih*{w}/{h})':'min(ih,iw*{h}/{w})',scale={w}:{h}"
    run([which.ffmpeg(), '-v', 'error', '-y', '-i', src, '-vf', vf, '-fps_mode', 'passthrough', '-q:v', '2', pattern])  # -vsync was removed in ffmpeg 9


# ───────────────────────── episode media ─────────────────────────
def still(src, t, dst, width=960):
    """One frame as JPEG. ``t`` is kept as given in file names by callers (e.g. "1.05")."""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    run([which.ffmpeg(), '-v', 'error', '-y', '-ss', str(t), '-i', src, '-frames:v', '1', '-vf', f'scale={width}:-2', '-q:v', '2', dst])


def play_clip(src, start, dur, dst, width=960, fps=30, gop=12, crf=20, keep_size=False):
    """Re-encode a clip for playback inside a composition.

    Product output often has very sparse keyframes (one per clip); the renderer
    grabs frames by seeking and then shows wrong or frozen frames. A short GOP
    (default a keyframe every 0.4s at 30fps) fixes it. Audio is dropped.
    """
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    scale = [] if keep_size else ['-vf', f'scale={width}:-2,fps={fps}']
    run([which.ffmpeg(), '-v', 'error', '-y', '-ss', str(start), '-i', src, '-an', *scale,
         '-frames:v', str(round(dur * fps)), '-c:v', 'libx264', '-crf', str(crf), '-g', str(gop), '-keyint_min', str(gop),
         '-sc_threshold', '0', '-bf', '3', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', dst])


def last_frame(clip, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    run([which.ffmpeg(), '-v', 'error', '-y', '-sseof', '-0.5', '-i', clip, '-update', '1', '-q:v', '2', dst])
