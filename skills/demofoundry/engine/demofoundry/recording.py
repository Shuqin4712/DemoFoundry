"""Index a product screen recording: find where the UI changes state → state table + overview sheet → crop evidence.

  python -m demofoundry recording index <recording.mp4>
      → _index/ next to it: index.json, overview.png (one cell per state; red box = what changed on entering it,
        top-left label = #id start–end s), states.md (time, size and place filled in; "state / notes" left for a
        person or agent to fill after looking at the overview)
      --ignore x0,y0,x1,y1   ignore a region (fractions, repeatable): something that always moves, like a clock
      --min-state 0.3        how long the picture must hold to count as a state (s)

  python -m demofoundry recording crop <recording> --t 24.5 --name palette__brush --box 640,40,640,80
  python -m demofoundry recording crop <recording> --t 24.5 --name palette__brush --change 18
      → crops/<name>-<t>s.png at full resolution. --box is pixels x,y,w,h; --change uses change #N from index.json, padded 24px.

How "the state changed" is decided:
  1. 10 fps greyscale at a fixed analysis width; a 0.5 s temporal median per pixel removes the moving cursor
     and keeps whatever stays (tooltips, strokes, panels);
  2. pixels that differ by >18 between steps; pixels changing more than 25% of the time within ±1 s are treated
     as "always playing" and masked;
  3. steps changing >0.02% of the frame are changes; changes ≤0.2 s apart merge; a hold ≥ min-state between
     changes is a "held" state;
  4. changes lasting ≥1 s (a video playing in a node, a preview flickering, the canvas moving) are "moving"
     spans, one cell per second, so a hover inside them is not swallowed.
It sees that the picture changed, not what changed: state names and on-screen text are still read by a person or agent.
"""
import argparse
import json
import os

import numpy as np

from . import av, which

AW = 519           # analysis width
FPS = 10
MED = 5            # temporal median window (frames) = 0.5 s
PX_TH = 18
PLAY_RATE = 0.25   # changing this share of ±1 s = always playing
EV_AREA = 0.02     # change area threshold (%)
MERGE = 2          # changes ≤ 2 steps (0.2 s) apart merge
DYNAMIC = 1.0      # changes lasting longer than this are moving spans


# ───────────────────────── detection ─────────────────────────
def analyse(path, ignore):
    m = av.probe(path)
    AH = round(AW * m['h'] / m['w'] / 2) * 2
    b = av.run([which.ffmpeg(), '-v', 'error', '-i', path, '-vf', f'fps={FPS},scale={AW}:{AH}', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'])
    F = np.frombuffer(b, dtype=np.uint8).astype(np.float32).reshape(-1, AH, AW)
    n = len(F)
    M = np.stack([np.median(F[max(0, i - MED // 2):i + MED // 2 + 1], axis=0) for i in range(n)])
    D = np.abs(np.diff(M, axis=0)) > PX_TH
    keep = np.ones((AH, AW), bool)
    for x0, y0, x1, y1 in ignore:
        keep[int(y0 * AH):int(y1 * AH), int(x0 * AW):int(x1 * AW)] = False
    cum = np.concatenate([np.zeros((1, AH, AW), np.float32), np.cumsum(D, axis=0, dtype=np.float32)])
    steps = []
    for i in range(len(D)):
        lo, hi = max(0, i - FPS), min(len(D), i + FPS + 1)
        mask = D[i] & keep & ((cum[hi] - cum[lo]) / (hi - lo) < PLAY_RATE)
        area = float(mask.mean() * 100)
        ys, xs = np.nonzero(mask)
        steps.append((area, (float(xs.min() / AW), float(ys.min() / AH), float((xs.max() + 1) / AW), float((ys.max() + 1) / AH)) if len(xs) else None))
    return m, steps


def group(steps, dur, min_state):
    changes = []
    for i, (a, bb) in enumerate(steps):
        if a <= EV_AREA:
            continue
        if changes and i - changes[-1]['_last'] <= MERGE:
            c = changes[-1]
            c['_last'] = i; c['peak'] = max(c['peak'], a)
            c['box'] = [min(c['box'][0], bb[0]), min(c['box'][1], bb[1]), max(c['box'][2], bb[2]), max(c['box'][3], bb[3])]
        else:
            changes.append({'_first': i, '_last': i, 'peak': a, 'box': list(bb)})
    for k, c in enumerate(changes):
        c['id'] = k
        c['start'] = round((c.pop('_first') + 1) / FPS, 1)      # step i = frame i → i+1
        c['end'] = round((c.pop('_last') + 1) / FPS, 1)
        c['peak'] = round(c['peak'], 2)
        c['size'] = 'screen' if c['peak'] > 5 else ('panel' if c['peak'] > 0.5 else 'element')
        c['box'] = [round(v, 3) for v in c['box']]
    states, t = [], 0.0
    for c in changes + [{'start': dur, 'end': dur, 'id': None}]:
        if c['start'] - t >= min_state:
            prev = next((x for x in reversed(changes) if x['end'] <= t + 1e-6), None) if t > 0 else None
            states.append({'kind': 'held', 'start': round(t, 1), 'end': round(c['start'], 1), 'enter_change': prev['id'] if prev else None})
        if c['id'] is not None and c['end'] - c['start'] >= DYNAMIC:
            for s in np.arange(c['start'], c['end'], 1.0):
                states.append({'kind': 'moving', 'start': round(float(s), 1), 'end': round(min(float(s) + 1.0, c['end']), 1), 'enter_change': c['id']})
        t = max(t, c['end'])
    states.sort(key=lambda s: (s['start'], s['kind'] == 'moving'))
    for k, s in enumerate(states):
        s['id'] = k
    return changes, states


# ───────────────────────── overview sheet ─────────────────────────
DIGITS = {  # 3×5 bitmap font
    '0': '111101101101111', '1': '010110010010111', '2': '111001111100111', '3': '111001111001111', '4': '101101111001001',
    '5': '111100111001111', '6': '111100111101111', '7': '111001001001001', '8': '111101111101111', '9': '111101111001111',
    '.': '000000000000010', 's': '000011110001110', '–': '000000111000000', '#': '101111101111101', '~': '000011110000000'}


def label(img, text, x, y, s=3, color=(255, 255, 255)):
    for ch in text:
        g = DIGITS.get(ch)
        if g:
            img[y - 1:y + 5 * s + 1, x - 1:x + 3 * s + 1] = (0, 0, 0)
            for r in range(5):
                for c in range(3):
                    if g[r * 3 + c] == '1':
                        img[y + r * s:y + (r + 1) * s, x + c * s:x + (c + 1) * s] = color
        x += 4 * s


def overview(path, m, states, changes, out, cols=4, tw=346):
    th = round(tw * m['h'] / m['w'])
    cells = []
    for st in states:
        t = round((st['start'] + st['end']) / 2, 2)
        b = av.run([which.ffmpeg(), '-v', 'error', '-ss', str(t), '-i', path, '-frames:v', '1', '-vf', f'scale={tw}:{th}',
                    '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
        img = np.frombuffer(b, dtype=np.uint8).reshape(th, tw, 3).copy()
        c = changes[st['enter_change']] if st['enter_change'] is not None else None
        dyn = st['kind'] == 'moving'
        if c:
            col = (255, 170, 40) if dyn else (255, 60, 40)
            x0, y0 = int(c['box'][0] * tw), int(c['box'][1] * th)
            x1, y1 = min(int(c['box'][2] * tw), tw - 1), min(int(c['box'][3] * th), th - 1)
            for x in (x0, x1):
                img[y0:y1 + 1, max(x - 1, 0):x + 1] = col
            for y in (y0, y1):
                img[max(y - 1, 0):y + 1, x0:x1 + 1] = col
        label(img, f'#{st["id"]}{"~" if dyn else ""}{st["start"]}–{st["end"]}s', 6, 6, color=(255, 200, 90) if dyn else (255, 255, 255))
        cells.append(img)
    if not cells:
        return
    while len(cells) % cols:
        cells.append(np.full((th, tw, 3), 18, np.uint8))
    gap = lambda h: np.full((h, 4, 3), 18, np.uint8)
    rows = [np.hstack([x for c in cells[i:i + cols] for x in (c, gap(th))]) for i in range(0, len(cells), cols)]
    av.save_png(os.path.join(out, 'overview.png'), np.vstack([x for r in rows for x in (r, np.full((4, r.shape[1], 3), 18, np.uint8))]))


# ───────────────────────── commands ─────────────────────────
def cmd_index(a):
    ignore = [tuple(float(v) for v in s.split(',')) for s in (a.ignore or [])]
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.video)), '_index')
    os.makedirs(out, exist_ok=True)
    print('1 analysing changes (temporal median drops the cursor, always-playing regions masked)')
    m, steps = analyse(a.video, ignore)
    changes, states = group(steps, m['dur'], a.min_state)
    n_dyn = sum(s['kind'] == 'moving' for s in states)
    print(f'  {len(changes)} changes · {len(states) - n_dyn} held states · {n_dyn} moving cells')
    print('2 overview sheet')
    overview(a.video, m, states, changes, out)
    with open(os.path.join(out, 'index.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'video': os.path.basename(a.video), **m, 'ignore': ignore, 'changes': changes, 'states': states}, f, ensure_ascii=False, indent=1)
    rows = ['# Recording state index (generated by recording index)', '',
            f'`{os.path.basename(a.video)}` · {m["w"]}×{m["h"]} · {m["fps"]:g}fps · {m["dur"]}s.',
            'Overview `overview.png`: one cell per state. White label + red box = a held state; the box is what changed '
            'on entering it. Yellow `~` label + yellow box = a moving span (video playing / preview flickering / canvas '
            'moving), one cell per second.',
            'Fill "state / notes" after looking at the overview (copy on-screen text verbatim); move the checked rows '
            'into the feature README\'s state index.', '',
            '| # | kind | time | change on entry | where (x0, y0, x1, y1) | state | notes |', '| ---: | --- | --- | --- | --- | --- | --- |']
    for st in states:
        c = changes[st['enter_change']] if st['enter_change'] is not None else None
        chg = (f'#{c["id"]} {c["size"]} {c["peak"]}% @ {c["start"]}–{c["end"]}s' if c else 'start')
        box = ', '.join(f'{v:.3f}' for v in c['box']) if c else ''
        rows.append(f'| {st["id"]} | {st["kind"]} | {st["start"]}–{st["end"]}s | {chg} | {box} |  |  |')
    with open(os.path.join(out, 'states.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(rows) + '\n')
    for p in ('states.md', 'overview.png', 'index.json'):
        print(f'  → {os.path.join(out, p)}')


def cmd_crop(a):
    m = av.probe(a.video)
    if a.box:
        x, y, w, h = (int(v) for v in a.box.split(','))
    elif a.change is not None:
        idx = os.path.join(os.path.dirname(os.path.abspath(a.video)), '_index', 'index.json')
        if not os.path.exists(idx):
            av.die('no _index/index.json; run index first')
        with open(idx, encoding='utf-8') as f:
            c = json.load(f)['changes'][a.change]
        pad = 24
        x0 = max(0, int(c['box'][0] * m['w']) - pad) // 8 * 8
        y0 = max(0, int(c['box'][1] * m['h']) - pad) // 8 * 8
        x1 = min(m['w'], int(c['box'][2] * m['w']) + pad)
        y1 = min(m['h'], int(c['box'][3] * m['h']) + pad)
        x, y, w, h = x0, y0, (x1 - x0 + 7) // 8 * 8, (y1 - y0 + 7) // 8 * 8
    else:
        av.die('needs --box x,y,w,h or --change N')
    w, h = min(w, m['w'] - x), min(h, m['h'] - y)
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.video)), 'crops')
    os.makedirs(out, exist_ok=True)
    dst = os.path.join(out, f'{a.name}-{a.t:.1f}s.png')
    av.run([which.ffmpeg(), '-v', 'error', '-y', '-ss', str(a.t), '-i', a.video, '-frames:v', '1', '-vf', f'crop={w}:{h}:{x}:{y}', dst])
    print(f'✓ {dst} ({w}×{h} @ {x},{y})')


def main(argv=None):
    ap = argparse.ArgumentParser(prog='demofoundry recording', description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('index'); p.add_argument('video'); p.add_argument('--out')
    p.add_argument('--ignore', action='append', help='x0,y0,x1,y1 (fractions)'); p.add_argument('--min-state', type=float, default=0.3)
    c = sub.add_parser('crop'); c.add_argument('video'); c.add_argument('--t', type=float, required=True)
    c.add_argument('--name', required=True, help='<component>__<state>'); c.add_argument('--box'); c.add_argument('--change', type=int); c.add_argument('--out')
    a = ap.parse_args(argv)
    if not os.path.isfile(a.video):
        av.die(f'not found: {a.video}')
    {'index': cmd_index, 'crop': cmd_crop}[a.cmd](a)
