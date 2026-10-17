"""Export readable captions from the same final word timeline used by pictures."""
import argparse
import json
from pathlib import Path
import textwrap


def timestamp(seconds):
    ms = round(seconds * 1000)
    if ms < 0:
        raise ValueError('negative subtitle time')
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'


def export(final, output, max_chars=64, max_seconds=5):
    final = Path(final)
    layout = json.loads((final / 'layout.json').read_text(encoding='utf-8'))
    blocks = []
    for clip in layout['clips']:
        data = json.loads((final / 'clips' / (clip['clip'] + '.words.json')).read_text(encoding='utf-8'))
        words = data['words'] if isinstance(data, dict) else data
        group = []

        def flush():
            if group:
                start = clip['start'] + group[0]['start']
                end = clip['start'] + group[-1]['end']
                if end <= start:
                    raise ValueError('subtitle has no duration')
                blocks.append((start, end, ' '.join(w['text'] for w in group)))
                group.clear()

        for word in words:
            if group and (len(' '.join(w['text'] for w in group)) + len(word['text']) + 1 > max_chars
                          or word['end'] - group[0]['start'] > max_seconds):
                flush()
            group.append(word)
            if word['text'].endswith(('.', '?', '!')):
                flush()
        flush()
    previous = 0
    lines = []
    for i, (start, end, text) in enumerate(blocks, 1):
        if start < previous:
            raise ValueError('overlapping captions; check word timestamps')
        wrapped = textwrap.wrap(text, width=42, break_long_words=False, break_on_hyphens=False)
        if len(wrapped) > 2 or any(len(line) > 42 for line in wrapped):
            raise ValueError('caption cannot fit two 42-character lines; shorten the text or caption group')
        caption = '\n'.join(wrapped)
        lines.append(f'{i}\n{timestamp(start)} --> {timestamp(end)}\n{caption}\n')
        previous = end
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text('\n'.join(lines), encoding='utf-8', newline='\n')
    return len(blocks)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('final'); ap.add_argument('output')
    args = ap.parse_args(argv)
    print(f'{export(args.final, args.output)} captions → {args.output}')
