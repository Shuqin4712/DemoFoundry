"""Voice pipeline: recordings → transcribe & align to the script → word check → measure pauses
→ pad dashes → cut clips at real silences → lay out → preview.

Input is an episode's ``voice/voice.json``:

  engine          "import" (default): recordings you bring, one file per paragraph
  dash_pause_ms   pause length a dash should get (recordings often run dashes together)
  end_hold        seconds of silence after the last clip
  tempo           (import) speed-up / slow-down applied on import, e.g. 1.03
  aliases         {"heard": "script"} spellings a transcriber gets wrong for product names
  paragraphs      {"A": "whole paragraph text", ...}   ← recorded as one take each, never stitched per sentence
  clips           [{clip, para, text, gap_before, gap_reason}, ...]
                  ← each paragraph cut in order; the clip texts must add up to the paragraph

Commands (paths are examples):

  python -m demofoundry voice import  voice/voice.json --take t01 --src <dir of recordings>
  python -m demofoundry voice build   voice/voice.json --take t01   # raw → check, pad, cut, lay out, preview
  python -m demofoundry voice layout  voice/voice.json --take t01   # only gap_before changed: re-lay out + preview
  python -m demofoundry voice measure voice/voice.json --take t01   # report only: word check, pace, pause at each punctuation
  python -m demofoundry voice promote voice/voice.json --take t01   # approved: take → final/ (old final kept under _takes)

Recordings are named after paragraphs (``A.wav``, ``sec0.mp3``). One file may cover consecutive
paragraphs (``sec0-1.mp3``); it is split at the longest real silence between them.

Rules behind it: read whole paragraphs (stitched sentences sound wrong); add pauses only where it is
crowded; feedback changes voice.json and the script reruns, nobody hand-cuts wavs.
"""
import argparse, datetime, difflib, glob, json, os, re, shutil, subprocess, sys, tempfile, wave
import numpy as np

from . import which

SIL_DB = -40.0      # silence = below the paragraph's peak −40 dB
SIL_MIN = 0.060     # only runs ≥ 60 ms count (stop-consonant closures are shorter)
WIN, HOP = 0.010, 0.005
GRAIN = 0.030       # grain of room tone used to pad pauses
DASHES = {'—', '–', '--'}


# ───────────────────────── io ─────────────────────────
def die(msg):
    sys.exit(f'✗ {msg}')


def read_wav(p):
    with wave.open(p) as f:
        if f.getsampwidth() != 2 or f.getnchannels() != 1:
            die(f'{p}: only 16-bit mono is supported')
        return np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(np.float64) / 32768, f.getframerate()


def write_wav(p, x, sr):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with wave.open(p, 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr)
        f.writeframes((np.clip(x, -1, 32767 / 32768) * 32768).round().astype(np.int16).tobytes())


def read_words(p):
    with open(p, encoding='utf-8') as f:
        w = json.load(f)
    return w['words'] if isinstance(w, dict) else w


def write_json(p, obj, indent=1):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)


def write_words(p, words):
    out = [{'id': f'w{i}', 'text': w['text'], 'start': round(w['start'], 3), 'end': round(w['end'], 3)} for i, w in enumerate(words)]
    write_json(p, {'words': out})


def load_spec(path):
    with open(path, encoding='utf-8') as f:
        s = json.load(f)
    s.setdefault('engine', 'import')
    for k in ('dash_pause_ms', 'paragraphs', 'clips'):
        if k not in s:
            die(f'voice.json is missing {k}')
    s.setdefault('voice_id', ''); s.setdefault('voice_name', '')
    s.setdefault('speed', 1.0); s.setdefault('tempo', 1.0)
    s.setdefault('end_hold', 1.5); s.setdefault('aliases', {})
    for c in s['clips']:
        if c.get('para') not in s['paragraphs']:
            die(f'clip {c.get("clip")}: para is not in paragraphs')
    return s


def dirs(spec_path, take):
    base = os.path.dirname(os.path.abspath(spec_path))
    return base, os.path.join(base, '_takes', take)


# ───────────────────────── text ─────────────────────────
def norm(tok):
    t = tok.replace('’', "'").lower().strip('.,;:!?"“”()[]…')
    return '' if t in DASHES or not t.strip('—–-') else t


def tokens(text):
    return [t for t in (norm(x) for x in re.split(r'\s+|(?<=\w)(?=—)|(?<=—)(?=\w)', text)) if t]


def word_index(words):
    """Indexes of the non-dash words."""
    return [i for i, w in enumerate(words) if norm(w['text'])]


def verify(name, text, words):
    want, got = tokens(text), [norm(w['text']) for w in words if norm(w['text'])]
    if want == got:
        return True
    k = next((i for i, (a, b) in enumerate(zip(want, got)) if a != b), min(len(want), len(got)))
    print(f'  ✗ paragraph {name} differs from the script at word {k}: script {want[k:k+4]} / recording {got[k:k+4]}')
    return False


# ───────────────────────── silence ─────────────────────────
def silence_runs(x, sr):
    n, h = int(WIN * sr), int(HOP * sr)
    env = np.lib.stride_tricks.sliding_window_view(np.abs(x), n)[::h].max(axis=1)
    q = env < np.abs(x).max() * 10 ** (SIL_DB / 20)
    runs = []
    edges = np.flatnonzero(np.diff(np.r_[0, q.astype(np.int8), 0]))
    for s, e in zip(edges[::2], edges[1::2]):
        t0, t1 = s * HOP, (e - 1) * HOP + WIN
        if t1 - t0 >= SIL_MIN:
            runs.append((t0, t1))
    return runs


def gap_run(runs, prev_w, next_w, before=0.10, after=0.20):
    """Longest real silence between two words, or None.

    Word times from TTS engines are estimates (a short word can be placed inside
    the following silence), so the run only has to overlap
    [previous end − 0.1s, next start + 0.2s] rather than sit between them.
    """
    lo, hi = prev_w['end'] - before, next_w['start'] + after
    c = [r for r in runs if r[1] > lo and r[0] < hi]
    return max(c, key=lambda r: r[1] - r[0]) if c else None


def pause_report(name, x, sr, words):
    runs = silence_runs(x, sr)
    idx = word_index(words)
    rows = []
    for a, b in zip(idx, idx[1:]):
        dash = any(words[k]['text'] in DASHES for k in range(a + 1, b)) or words[a]['text'].endswith(('—', '–'))
        punct = 'dash' if dash else ('.' if words[a]['text'].endswith(('.', '?', '!')) else (',' if words[a]['text'].endswith((',', ';', ':')) else ''))
        if not punct:
            continue
        r = gap_run(runs, words[a], words[b])
        rows.append((punct, words[a]['text'], words[b]['text'], round((r[1] - r[0]) * 1000) if r else 0))
    n = len(idx)
    dur = words[idx[-1]]['end'] - words[idx[0]]['start']
    print(f'  paragraph {name}: {n} words · {dur:.2f}s · {n / dur:.2f} words/s')
    for kind in ('dash', ',', '.'):
        ms = [r[3] for r in rows if r[0] == kind]
        if ms:
            print(f'    {kind:>4} silence ms: ' + ' '.join(str(m) for m in ms) + f' (median {int(np.median(ms))})')
    return rows


# ───────────────────────── pad dash pauses ─────────────────────────
def fill(x, sr, run, length):
    """Room tone of the same level: the quietest 30 ms of the silence, Hann-windowed and overlap-added (no periodic clicks)."""
    g = int(GRAIN * sr)
    s, e = int((run[0] + 0.01) * sr), int((run[1] - 0.01) * sr)
    core = x[s:e] if e - s >= g else x[int(run[0] * sr):int(run[1] * sr)]
    if len(core) < g:
        return np.zeros(int(round(length * sr)))
    rms = np.sqrt(np.convolve(core ** 2, np.ones(g) / g, 'valid'))
    k = int(np.argmin(rms))
    grain = core[k:k + g] * (np.hanning(g + 1)[:-1])
    L = int(round(length * sr)); hop = g // 2
    out = np.zeros(L + g)
    for i in range(0, L, hop):
        out[i:i + g] += grain
    return out[:L]


def pad_dashes(name, x, sr, words, target_ms):
    runs = silence_runs(x, sr)
    idx = word_index(words)
    inserts = []
    for a, b in zip(idx, idx[1:]):
        if not (any(words[k]['text'] in DASHES for k in range(a + 1, b)) or words[a]['text'].endswith(('—', '–'))):
            continue
        r = gap_run(runs, words[a], words[b])
        if not r:
            print(f'  ! paragraph {name}: no real silence in "{words[a]["text"]} — {words[b]["text"]}", not padded '
                  f'(change the dash to a colon or full stop and re-record that paragraph)')
            continue
        need = target_ms / 1000 - (r[1] - r[0])
        if need > 0.005:
            inserts.append(((r[0] + r[1]) / 2, need, r))
    if not inserts:
        return x, words, []
    parts, words = [], [dict(w) for w in words]
    last = 0
    for t, need, r in sorted(inserts):
        cut = int(round(t * sr))
        parts += [x[last:cut], fill(x, sr, r, need)]
        last = cut
    parts.append(x[last:])
    for t, need, _ in sorted(inserts, reverse=True):
        add = int(round(need * sr)) / sr
        for w in words:
            if w['start'] >= t:
                w['start'] += add; w['end'] += add
            elif w['end'] > t:
                w['end'] += add
    return np.concatenate(parts), words, [(round(t, 3), round(n * 1000)) for t, n, _ in inserts]


# ───────────────────────── cut clips ─────────────────────────
def split(name, x, sr, words, clips):
    idx = word_index(words)
    runs = silence_runs(x, sr)
    pos, cuts, spans = 0, [0], []
    for c in clips:
        n = len(tokens(c['text']))
        seg = [norm(words[k]['text']) for k in idx[pos:pos + n]]
        if seg != tokens(c['text']):
            die(f'clip {c["clip"]}: text does not match the recording of paragraph {name}: {tokens(c["text"])[:4]} / {seg[:4]}')
        # words belong to clips by alignment, not by time (estimated times can fall into the next clip); a dash in between goes with the word before
        first = idx[pos] if pos == 0 else idx[pos - 1] + 1
        last = idx[pos + n] - 1 if pos + n < len(idx) else len(words) - 1
        spans.append((first, last))
        pos += n
        if pos < len(idx):
            r = gap_run(runs, words[idx[pos - 1]], words[idx[pos]])
            if not r:
                die(f'paragraph {name}: no real silence between "{words[idx[pos - 1]]["text"]}" and "{words[idx[pos]]["text"]}", '
                    f'cannot cut after clip {c["clip"]} (merge the two clips, or re-record)')
            cuts.append(int(round((r[0] + r[1]) / 2 * sr)))
    if pos != len(idx):
        die(f'paragraph {name}: the clips cover only {pos}/{len(idx)} words')
    cuts.append(len(x))
    out = []
    for c, s, e, (first, last) in zip(clips, cuts, cuts[1:], spans):
        t0, dur = s / sr, (e - s) / sr
        cw = [{**w, 'start': min(max(w['start'] - t0, 0), dur), 'end': min(max(w['end'] - t0, 0), dur)}
              for w in words[first:last + 1]]
        out.append((c, x[s:e], cw))
    return out


# ───────────────────────── layout and preview ─────────────────────────
def make_layout(spec, clip_dir):
    rows, t = [], 0.0
    for i, c in enumerate(spec['clips']):
        with wave.open(os.path.join(clip_dir, c['clip'] + '.wav')) as f:
            dur = round(f.getnframes() / f.getframerate(), 3)
        start = round((t if i else 0) + c['gap_before'], 2)
        t = round(start + dur, 3)
        rows.append({'clip': c['clip'], 'start': start, 'dur': dur, 'end': t,
                     'gap_before': c['gap_before'], 'gap_reason': c.get('gap_reason', '')})
    return {'voice': f'{spec["voice_name"]} ({spec["voice_id"]})'.strip() if spec['voice_id'] else spec['voice_name'],
            'speed': spec['speed'], 'dash_pause_ms': spec['dash_pause_ms'], 'end_hold_after_cta': spec['end_hold'],
            'total': round(t + spec['end_hold'], 2), 'clips': rows}


def preview(layout, clip_dir, out_mp3):
    sr = None; parts = []
    for c in layout['clips']:
        x, sr = read_wav(os.path.join(clip_dir, c['clip'] + '.wav'))
        parts.append((c['start'], x))
    mix = np.zeros(int(round(layout['total'] * sr)) + 1)
    for s, x in parts:
        i = int(round(s * sr)); mix[i:i + len(x)] += x[:len(mix) - i]
    with tempfile.TemporaryDirectory() as td:
        tmp = os.path.join(td, 'mix.wav'); write_wav(tmp, mix, sr)
        subprocess.run([which.ffmpeg(), '-y', '-v', 'error', '-i', tmp, '-b:a', '128k', out_mp3], check=True)
        r = subprocess.run([which.ffmpeg(), '-nostats', '-i', tmp, '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                           capture_output=True, text=True, encoding='utf-8', errors='replace').stderr
    lufs = re.findall(r'I:\s+(-?[\d.]+) LUFS', r); peak = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', r)
    return (float(lufs[-1]) if lufs else None), (float(peak[-1]) if peak else None)


# ───────────────────────── import recordings ─────────────────────────
EXTS = ('.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg')
HEAD_KEEP, TAIL_KEEP = 0.03, 0.25   # after trimming: keep 30 ms before the first word, 250 ms after the last


def trim_edges(x, sr):
    """Trim leading / trailing silence; uneven lead-in would make every clip start late."""
    n, h = int(WIN * sr), int(HOP * sr)
    env = np.lib.stride_tricks.sliding_window_view(np.abs(x), n)[::h].max(axis=1)
    loud = np.flatnonzero(env >= np.abs(x).max() * 10 ** (SIL_DB / 20))
    if not len(loud):
        return x, 0.0
    t0 = max(loud[0] * HOP - HEAD_KEEP, 0)
    t1 = min(loud[-1] * HOP + WIN + TAIL_KEEP, len(x) / sr)
    return x[int(t0 * sr):int(t1 * sr)], t0


def transcribe(wav, engine='auto'):
    """Word timestamps for a wav → [{text, start, end}].

    auto: faster-whisper (Windows / Linux / Mac); on Apple silicon ``parakeet`` can be
    asked for explicitly through ``hyperframes transcribe``.
    """
    if engine == 'parakeet':
        return transcribe_parakeet(wav)
    return transcribe_whisper(wav)


def transcribe_whisper(wav, model='small.en'):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        die('transcription needs faster-whisper: install the engine with the "whisper" extra '
            '(uv: `uv sync --extra whisper`; pip: `pip install faster-whisper`)')
    m = WhisperModel(model, device='cpu', compute_type='int8')
    segs, _ = m.transcribe(wav, word_timestamps=True, language='en')
    return [{'text': w.word.strip(), 'start': round(w.start, 3), 'end': round(w.end, 3)} for s in segs for w in s.words]


def transcribe_parakeet(wav):
    with tempfile.TemporaryDirectory() as td:
        r = subprocess.run([*which.npx(), 'hyperframes', 'transcribe', wav, '--engine', 'parakeet', '--json', '-d', td],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        out = r.stdout.strip().splitlines()
        info = json.loads(out[-1]) if out and out[-1].startswith('{') else {}
        if not info.get('ok'):
            die(f'parakeet transcription failed (Apple silicon only): {info or r.stderr[-400:]}')
        return read_words(info['transcriptPath'])


def align(name, text, heard, aliases=None):
    """Put transcribed word times on the script's words; output text is always the script (with punctuation).

    Where transcript and script disagree ("3 by 3" ↔ "3x3", a misheard product name),
    the block's time is shared out by character length and listed: usually a spelling
    difference, sometimes a real misreading someone should listen to. ``aliases``
    ({"heard": "script"}, lower case) silences known spelling differences.
    """
    aliases = {k.lower(): v.lower() for k, v in (aliases or {}).items()}
    script = text.split()
    a = [norm(t) for t in script]
    b = [norm(w['text']) for w in heard]
    words, notes = [], []
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)

    def squash(t):
        t = t.lower().replace(' by ', 'x')
        for k, v in aliases.items():
            t = t.replace(k, v)
        return re.sub(r'[^a-z0-9]', '', t)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == 'equal':
            words += [{'text': script[i1 + k], 'start': heard[j1 + k]['start'], 'end': heard[j1 + k]['end']} for k in range(i2 - i1)]
            continue
        if op == 'insert':
            notes.append(f'recording has extra "{" ".join(w["text"] for w in heard[j1:j2])}"')
            continue
        if j2 > j1:
            t0, t1 = heard[j1]['start'], heard[j2 - 1]['end']
        else:                                   # in the script, not heard: squeeze between neighbours
            t0 = words[-1]['end'] if words else (heard[j1]['start'] if j1 < len(heard) else 0)
            t1 = heard[j1]['start'] if j1 < len(heard) else t0
        lens = [max(len(a[k]), 1) for k in range(i1, i2)]
        acc = t0
        for k, L in zip(range(i1, i2), lens):
            d = (t1 - t0) * L / sum(lens)
            words.append({'text': script[k], 'start': acc, 'end': acc + d}); acc += d
        said, wrote = ' '.join(script[i1:i2]), ' '.join(w['text'] for w in heard[j1:j2])
        if squash(said) != squash(wrote):       # "Double-click" ↔ "Double click", "3 by 3" ↔ "3x3": spelling only, not reported
            notes.append(f'script "{said}" ↔ heard "{wrote or "(nothing)"}" @ {t0:.2f}s')
    if notes:
        print(f'  ! paragraph {name}: {len(notes)} difference(s) from the script (times shared out; listen whether it was misread):')
        for n_ in notes:
            print(f'      {n_}')
    return words, notes


def find_recordings(spec, src):
    """Recording files → the paragraphs they cover. ``sec3.mp3`` → [sec3]; ``sec0-1.mp3`` → [sec0, sec1]."""
    names = list(spec['paragraphs'])
    out, used = [], set()
    for f in sorted(glob.glob(os.path.join(src, '*'))):
        stem, ext = os.path.splitext(os.path.basename(f))
        if ext.lower() not in EXTS:
            continue
        m = re.fullmatch(r'(\D+)(\d+)-(\d+)', stem)
        cover = [f'{m.group(1)}{i}' for i in range(int(m.group(2)), int(m.group(3)) + 1)] if m else [stem]
        if not all(c in names for c in cover):
            print(f'  · skipping {os.path.basename(f)} (name does not match a paragraph in voice.json)'); continue
        if used & set(cover):
            die(f'{os.path.basename(f)} covers {sorted(used & set(cover))} again')
        used |= set(cover); out.append((f, cover))
    return out


def split_joint(wav, spec, cover, raw, engine):
    """One recording of consecutive paragraphs → one file per paragraph, cut in the middle of the longest real silence at each boundary."""
    x, sr = read_wav(wav)
    text = ' '.join(spec['paragraphs'][n] for n in cover)
    words, _ = align('+'.join(cover), text, transcribe(wav, engine), spec['aliases'])
    runs = silence_runs(x, sr)
    cuts, k = [0], 0
    for n in cover[:-1]:
        k += len(spec['paragraphs'][n].split())
        r = gap_run(runs, words[k - 1], words[k], before=0.3, after=0.4)
        if not r:
            die(f'{os.path.basename(wav)}: no real silence after "{words[k - 1]["text"]}" ({n}), cannot split; record the paragraphs separately')
        cuts.append(int(round((r[0] + r[1]) / 2 * sr)))
        print(f'    {n} | next: cut at {(r[0] + r[1]) / 2:.2f}s (silence {round((r[1] - r[0]) * 1000)} ms)')
    cuts.append(len(x))
    for n, a, b in zip(cover, cuts, cuts[1:]):
        write_wav(os.path.join(raw, f'para-{n}.wav'), x[a:b], sr)


def cmd_import(spec, spec_path, take, src, engine):
    _, td = dirs(spec_path, take)
    raw = os.path.join(td, 'raw')
    os.makedirs(raw, exist_ok=True)
    tempo = spec.get('tempo', 1.0)
    recs = find_recordings(spec, src)
    if not recs:
        die(f'{src} has no recordings named after paragraphs ({"/".join(spec["paragraphs"])}, or joint like sec0-1; {"/".join(EXTS)})')
    report, done = [], []
    for f, cover in recs:
        af = ['-af', f'atempo={tempo}'] if abs(tempo - 1) > 1e-6 else []
        tmp = os.path.join(raw, f'_in-{cover[0]}.wav')
        subprocess.run([which.ffmpeg(), '-y', '-v', 'error', '-i', f, *af, '-ac', '1', '-ar', '44100', '-sample_fmt', 's16', tmp], check=True)
        if len(cover) > 1:
            print(f'  → {os.path.basename(f)} covers {", ".join(cover)}; splitting first')
            split_joint(tmp, spec, cover, raw, engine)
        else:
            shutil.copy(tmp, os.path.join(raw, f'para-{cover[0]}.wav'))
        os.remove(tmp)
        for name in cover:
            wav = os.path.join(raw, f'para-{name}.wav')
            x, sr = read_wav(wav)
            x, cut = trim_edges(x, sr)
            write_wav(wav, x, sr)
            print(f'  → paragraph {name}: {len(x) / sr:.2f}s (trimmed {cut:.2f}s at the head{f", tempo {tempo}x" if af else ""}) · transcribing')
            words, notes = align(name, spec['paragraphs'][name], transcribe(wav, engine), spec['aliases'])
            write_words(os.path.join(raw, f'para-{name}.words.json'), words)
            report += [f'{name}: {n_}' for n_ in notes]
            done.append(name)
    with open(os.path.join(raw, 'align-notes.txt'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(report) + ('\n' if report else ''))
    print(f'  imported {len(done)}/{len(spec["paragraphs"])} paragraphs → {raw}')


def restrict(spec, src):
    """Only the paragraphs that have a recording (useful when trying one paragraph first)."""
    have = [n for n in spec['paragraphs'] if os.path.exists(os.path.join(src, f'para-{n}.wav'))]
    if len(have) == len(spec['paragraphs']) or not have:
        return spec
    print(f'  (only {len(have)}/{len(spec["paragraphs"])} paragraphs recorded: {", ".join(have)}; the preview has just these)')
    return {**spec, 'paragraphs': {n: spec['paragraphs'][n] for n in have}, 'clips': [c for c in spec['clips'] if c['para'] in have]}


def cmd_measure(spec, src):
    ok = True
    for name, text in spec['paragraphs'].items():
        x, sr = read_wav(os.path.join(src, f'para-{name}.wav'))
        w = read_words(os.path.join(src, f'para-{name}.words.json'))
        ok &= verify(name, text, w)
        pause_report(name, x, sr, w)
    return ok


def cmd_build(spec, src, out):
    print('1 word check · 2 pauses (before padding)')
    if not cmd_measure(spec, src):
        die('the recording does not match the script: fix the script or re-record')
    print(f'3 pad dashes to {spec["dash_pause_ms"]} ms · 4 cut at silences')
    clip_dir = os.path.join(out, 'clips')
    if os.path.isdir(clip_dir):
        shutil.rmtree(clip_dir)
    for name in spec['paragraphs']:
        x, sr = read_wav(os.path.join(src, f'para-{name}.wav'))
        w = read_words(os.path.join(src, f'para-{name}.words.json'))
        x, w, ins = pad_dashes(name, x, sr, w, spec['dash_pause_ms'])
        if ins:
            print(f'  paragraph {name}: padded ' + ', '.join(f'{t}s +{ms}ms' for t, ms in ins))
        write_wav(os.path.join(out, f'para-{name}.wav'), x, sr)
        write_words(os.path.join(out, f'para-{name}.words.json'), w)
        for c, cx, cw in split(name, x, sr, w, [c for c in spec['clips'] if c['para'] == name]):
            write_wav(os.path.join(clip_dir, c['clip'] + '.wav'), cx, sr)
            write_words(os.path.join(clip_dir, c['clip'] + '.words.json'), cw)
    print('  after padding:')
    for name in spec['paragraphs']:
        pause_report(name, *read_wav(os.path.join(out, f'para-{name}.wav')), read_words(os.path.join(out, f'para-{name}.words.json')))
    cmd_layout(spec, out)


def cmd_layout(spec, out):
    print('5 lay out · 6 preview')
    clip_dir = os.path.join(out, 'clips')
    names = {c['clip'] for c in spec['clips']}
    have = {f[:-4] for f in os.listdir(clip_dir) if f.endswith('.wav')} if os.path.isdir(clip_dir) else set()
    if names - have:
        die(f'missing clips: {sorted(names - have)} (run build first)')
    lay = make_layout(spec, clip_dir)
    write_json(os.path.join(out, 'layout.json'), lay)
    lufs, peak = preview(lay, clip_dir, os.path.join(out, 'preview-final.mp3'))
    print(f'  {len(lay["clips"])} clips · total {lay["total"]}s · loudness {lufs} LUFS · true peak {peak} dBFS')
    print(f'  → {out}/layout.json · preview-final.mp3 (for the listener)')


def cmd_promote(spec_path, take):
    base, td = dirs(spec_path, take)
    final = os.path.join(base, 'final')
    for f in ('layout.json', 'preview-final.mp3', 'clips'):
        if not os.path.exists(os.path.join(td, f)):
            die(f'_takes/{take} has no {f}; run build first')
    if os.path.exists(final):
        keep = os.path.join(base, '_takes', 'final-prev-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
        shutil.move(final, keep)
        print(f'  old final → {os.path.relpath(keep, base)}')
    shutil.copytree(td, final, ignore=shutil.ignore_patterns('raw'))
    print(f'✓ _takes/{take} → final/. Regenerate the pictures; they read final/layout.json')


def main(argv=None):
    ap = argparse.ArgumentParser(prog='demofoundry voice', description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['import', 'build', 'layout', 'measure', 'promote'])
    ap.add_argument('spec', help='voice/voice.json')
    ap.add_argument('--take', help='take name, e.g. t01 (folder _takes/<take>/)')
    ap.add_argument('--src', help='import: folder of recordings; build / measure: input folder (default _takes/<take>/raw)')
    ap.add_argument('--out', help='build / layout output folder (default _takes/<take>)')
    ap.add_argument('--transcriber', default='auto', choices=['auto', 'whisper', 'parakeet'])
    a = ap.parse_args(argv)
    spec = load_spec(a.spec)
    if not a.take and not (a.src or a.out):
        die('needs --take (or --src / --out)')
    _, td = dirs(a.spec, a.take or '_')
    src = a.src or os.path.join(td, 'raw')
    out = a.out or td
    if a.cmd == 'import':
        if not a.src:
            die('import needs --src <folder of recordings named after paragraphs>')
        cmd_import(spec, a.spec, a.take, a.src, a.transcriber)
        src = os.path.join(td, 'raw')
    if a.cmd in ('import', 'build', 'layout', 'measure'):
        spec = restrict(spec, src if a.cmd != 'layout' else os.path.join(out, '.'))
    if a.cmd in ('build', 'import'):
        cmd_build(spec, src, out)
    elif a.cmd == 'measure':
        sys.exit(0 if cmd_measure(spec, src) else 1)
    elif a.cmd == 'layout':
        cmd_layout(spec, out)
    elif a.cmd == 'promote':
        cmd_promote(a.spec, a.take)
