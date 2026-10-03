"""Cue timeline: named points in time that pictures hang on.

v1 cues come from the narration: a cue is a word inside one narration clip,
``cue('sec2', 'Character')``. Scoping by clip keeps a word that recurs in
another clip from matching the wrong place; a word that recurs inside the same
clip takes an occurrence number (``n=2``). Re-voice, regenerate, and every
picture event moves with its word.

Later sources (captions, music beats) can add cues without touching the
generators that read them.
"""
from . import io

R3 = lambda v: round(v, 3)


def word_time(words, word, offset=0.0, n=1):
    """Start of the ``n``-th occurrence of ``word`` (trailing ``.`` / ``,`` ignored)."""
    hits = [x['start'] for x in words if x.get('text', x.get('word', '')).strip('.,') == word]
    if len(hits) < n:
        raise KeyError(f'word {word!r} occurrence {n} not found ({len(hits)} found)')
    return offset + hits[n - 1]


class Cues:
    """Reads a voice layout (``layout.json``) and its per-clip ``words.json``.

    layout = {total, clips: [{clip, start, dur, ...}]}; words live in ``<voice>/clips/<clip>.words.json``.
    """

    def __init__(self, root, voice_dir):
        self.root, self.voice_dir = root, voice_dir
        self.layout = io.load_json(root, f'{voice_dir}/layout.json')
        self.total = self.layout['total']
        self.start = {c['clip']: c['start'] for c in self.layout['clips']}
        self.end = {c['clip']: R3(c['start'] + c['dur']) for c in self.layout['clips']}
        self._words = {}

    def words(self, clip):
        if clip not in self._words:
            self._words[clip] = io.load_words(self.root, f'{self.voice_dir}/clips/{clip}.words.json')
        return self._words[clip]

    def __call__(self, clip, word, n=1):
        """Global time of a word in a clip."""
        return word_time(self.words(clip), word, self.start[clip], n)

    def clips(self):
        return [{'clip': c['clip'], 'start': c['start'], 'dur': c['dur']} for c in self.layout['clips']]
