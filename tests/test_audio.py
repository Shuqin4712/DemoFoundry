"""P3 contracts: caption timing, provider alignment and phrase extension."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/demofoundry/engine'))
from demofoundry import bgm, srt, tts


class Captions(unittest.TestCase):
    def test_millisecond_carry(self):
        self.assertEqual(srt.timestamp(59.9996), '00:01:00,000')

    def test_global_clip_offsets(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / 'clips').mkdir()
            (root / 'layout.json').write_text(json.dumps({'clips': [{'clip': 'a', 'start': 4.2}]}))
            (root / 'clips/a.words.json').write_text(json.dumps({'words': [
                {'text': 'Hello', 'start': .1, 'end': .4}, {'text': 'team.', 'start': .5, 'end': .9}]}))
            output = root / 'test.srt'
            self.assertEqual(srt.export(root, output), 1)
            self.assertIn('00:00:04,300 --> 00:00:05,100', output.read_text())

    def test_elevenlabs_character_offsets(self):
        a = {'characters': list('Hi all.'), 'character_start_times_seconds': [i / 10 for i in range(7)],
             'character_end_times_seconds': [(i + 1) / 10 for i in range(7)]}
        words = tts.character_words(a)
        self.assertEqual(words, [{'text': 'Hi', 'start': 0, 'end': .2}, {'text': 'all.', 'start': .3, 'end': .7}])

    def test_missing_credentials_do_not_call_network(self):
        from unittest.mock import patch
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
            tts.ElevenLabs({'voice_id': 'test'})


class Music(unittest.TestCase):
    def test_license_record_deduplicates_by_content(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / 'music.wav'; src.write_bytes(b'test')
            ledger = Path(td) / 'licenses.json'
            for _ in range(2):
                bgm.register(src, ledger, 'https://example.com/source', 'CC0', 'Test author')
            self.assertEqual(len(json.loads(ledger.read_text())), 1)

    def test_invalid_trim_is_rejected_before_ffmpeg(self):
        with self.assertRaises(ValueError):
            bgm.trim('unused', 1, 'unused', fade_out=2)

    @unittest.skipUnless(os.environ.get('DF_AUDIO_CHECK') == '1', 'set DF_AUDIO_CHECK=1 for ffmpeg phrase test')
    def test_phrase_extension_preserves_length(self):
        import numpy as np
        import soundfile as sf
        with tempfile.TemporaryDirectory() as td:
            sr = 24000
            source = Path(td) / 'source.wav'; out = Path(td) / 'out.wav'
            sf.write(source, .1 * np.sin(2 * np.pi * 220 * np.arange(sr * 3) / sr), sr)
            info = bgm.extend(str(source), 7, str(out), .5, 1.5)
            audio, got_sr = sf.read(out)
            self.assertEqual(got_sr, sr)
            self.assertAlmostEqual(len(audio) / sr, 7, places=3)
            self.assertGreater(info['insertions'], 0)


if __name__ == '__main__':
    unittest.main()
