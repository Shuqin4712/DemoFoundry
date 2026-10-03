"""Build the fixture episode's voice output without a recording.

Each clip gets its ``fixture_dur``; words are spread evenly across it (weighted
by length). Writes what the voice pipeline would: ``final/layout.json`` and
``final/clips/<clip>.words.json`` (committed), plus silent ``.wav`` clips of the
same length (not committed, so `check` / `render` have audio files to point at).

  python tests/make_fixture_voice.py [--wav-only]
"""
import json
import os
import sys
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
VOICE = os.path.join(HERE, 'fixtures', 'jot', 'demofoundry', 'episodes', '01-quick-note', 'voice')
SR = 16000


def silent_wav(path, dur):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes(b'\x00\x00' * int(round(dur * SR)))


def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def main():
    wav_only = '--wav-only' in sys.argv
    with open(os.path.join(VOICE, 'voice.json'), encoding='utf-8') as f:
        spec = json.load(f)
    final = os.path.join(VOICE, 'final')
    rows, t = [], 0.0
    for i, c in enumerate(spec['clips']):
        dur = c['fixture_dur']
        silent_wav(os.path.join(final, 'clips', c['clip'] + '.wav'), dur)
        if wav_only:
            continue
        toks = c['text'].split()
        weights = [max(len(w.strip('.,—')), 1) for w in toks]
        acc, words = 0.05, []
        span = dur - 0.15
        for k, (w, wt) in enumerate(zip(toks, weights)):
            d = span * wt / sum(weights)
            words.append({'id': f'w{k}', 'text': w, 'start': round(acc, 3), 'end': round(acc + d * 0.85, 3)})
            acc += d
        dump(os.path.join(final, 'clips', c['clip'] + '.words.json'), {'words': words})
        start = round((t if i else 0) + c['gap_before'], 2)
        t = round(start + dur, 3)
        rows.append({'clip': c['clip'], 'start': start, 'dur': dur, 'end': t,
                     'gap_before': c['gap_before'], 'gap_reason': c.get('gap_reason', '')})
    if not wav_only:
        dump(os.path.join(final, 'layout.json'), {'voice': spec['voice_name'], 'speed': 1.0, 'dash_pause_ms': spec['dash_pause_ms'],
                                                  'end_hold_after_cta': spec['end_hold'], 'total': round(t + spec['end_hold'], 2), 'clips': rows})
    print(f'fixture voice → {final}' + (' (wav only)' if wav_only else ''))


if __name__ == '__main__':
    main()
