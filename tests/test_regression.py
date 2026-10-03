"""Regression and unit tests for the engine.

  python -m unittest discover -s tests -v

Regression: the fixture episode (tests/fixtures/jot) is regenerated in a temp copy and its output
compared byte for byte with the committed files. An intended change shows up as a diff: regenerate
the fixture, review the diff, commit it with the engine change.

Set DF_HF_CHECK=1 to also run ``hyperframes check`` on the regenerated episode (needs Node and network).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
ENGINE = os.path.join(REPO, 'skills', 'demofoundry', 'engine')
sys.path.insert(0, ENGINE)

from demofoundry import cues, fx, hf, intro, scene, stage, theme, voice  # noqa: E402

FIXTURE = os.path.join(HERE, 'fixtures', 'jot')
EPISODE = os.path.join('demofoundry', 'episodes', '01-quick-note')
GENERATED = ['index.html', 'compositions/frames/01-story.html', 'compositions/frames/02-end-card.html']
HF_VERSION = '0.8.114'


def read_bytes(p):
    with open(p, 'rb') as f:
        return f.read()


class FixtureRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix='df-regress-')
        shutil.copytree(FIXTURE, os.path.join(cls.tmp, 'jot'))
        cls.ep = os.path.join(cls.tmp, 'jot', EPISODE)
        for rel in GENERATED:
            os.remove(os.path.join(cls.ep, rel))
        env = {**os.environ, 'PYTHONPATH': ENGINE, 'PYTHONIOENCODING': 'utf-8'}
        cls.gen = subprocess.run([sys.executable, '-m', 'demofoundry', 'gen', cls.ep], env=env, capture_output=True, text=True, encoding='utf-8')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_generator_runs(self):
        self.assertEqual(self.gen.returncode, 0, self.gen.stderr)

    def test_output_matches_committed(self):
        for rel in GENERATED:
            with self.subTest(file=rel):
                got = read_bytes(os.path.join(self.ep, rel))
                want = read_bytes(os.path.join(FIXTURE, EPISODE, rel))
                self.assertEqual(got, want, f'{rel} changed; if intended, regenerate the fixture and commit the diff')

    def test_output_is_lf_utf8(self):
        for rel in GENERATED:
            b = read_bytes(os.path.join(self.ep, rel))
            self.assertNotIn(b'\r\n', b, rel)
            b.decode('utf-8')

    def test_mold_assets_synced(self):
        self.assertTrue(os.path.isfile(os.path.join(self.ep, 'assets', 'mold', 'css', 'jot.css')))

    @unittest.skipUnless(os.environ.get('DF_HF_CHECK') == '1', 'set DF_HF_CHECK=1 to run hyperframes check')
    def test_hyperframes_check(self):
        subprocess.run([sys.executable, os.path.join(HERE, 'make_fixture_voice.py'), '--wav-only'], check=True)
        src = os.path.join(FIXTURE, EPISODE, 'voice', 'final', 'clips')
        dst = os.path.join(self.ep, 'voice', 'final', 'clips')
        for f in os.listdir(src):
            if f.endswith('.wav'):
                shutil.copy(os.path.join(src, f), dst)
        npx = shutil.which('npx')
        r = subprocess.run([npx, '--yes', f'hyperframes@{HF_VERSION}', 'check'], cwd=self.ep, capture_output=True, text=True, encoding='utf-8', errors='replace')
        self.assertEqual(r.returncode, 0, r.stdout[-3000:])


class Cues(unittest.TestCase):
    words = [{'text': 'Start', 'start': 0.1}, {'text': 'with,', 'start': 0.4}, {'text': 'Character', 'start': 0.9}, {'text': 'with', 'start': 1.5}]

    def test_punctuation_ignored_and_offset(self):
        self.assertAlmostEqual(cues.word_time(self.words, 'with', 10.0), 10.4)

    def test_nth_occurrence(self):
        self.assertAlmostEqual(cues.word_time(self.words, 'with', 10.0, n=2), 11.5)

    def test_missing_word_raises(self):
        with self.assertRaises(KeyError):
            cues.word_time(self.words, 'nope')

    def test_fixture_layout(self):
        W = cues.Cues(os.path.join(FIXTURE, EPISODE), 'voice/final')
        self.assertEqual([c['clip'] for c in W.clips()], ['sec0', 'sec1', 'sec2', 'sec3', 'sec4'])
        self.assertGreater(W('sec1', 'Click'), W.start['sec1'])


class Stage(unittest.TestCase):
    def setUp(self):
        self.tl = hf.Timeline()
        self.cam = stage.Camera(self.tl, {'a': (100, 100, 1.0), 'b': (500, 300, 2.0)}, [(2.0, 1.0, 'b')], start='a')

    def test_screen_position(self):
        self.assertEqual(self.cam.scr(100, 100, 0), (960, 540))
        self.assertEqual(self.cam.scr(510, 300, 3.5), (980, 540))

    def test_cursor_while_camera_moves_raises(self):
        with self.assertRaises(ValueError):
            self.cam.scr(0, 0, 2.5)

    def test_canvas_parameter(self):
        cam = stage.Camera(self.tl, {'a': (0, 0, 1.0)}, [], start='a', canvas=(1080, 1920))
        self.assertEqual(cam.scr(0, 0, 0), (540, 960))
        cur = stage.Cursor(self.tl, cam)
        self.assertEqual((cur.park_x, cur.below, cur.off), (480, 2020, (1240, 2040)))

    def test_integral_numbers_print_without_decimals(self):
        stage.Cursor(self.tl, self.cam).init_state()
        self.assertIn('{x: 900, y: 1180, autoAlpha: 0}', self.tl.INIT[-1])


class Effects(unittest.TestCase):
    def test_typing_markup(self):
        self.assertEqual(fx.typing_html('a b', 'p').count('class="p-ch"'), 3)

    def test_swap_is_simultaneous(self):
        tl = hf.Timeline()
        scene.swap(tl, '#old', '#new', 1.5)
        self.assertEqual(tl.T, ['tl.set("#old", {autoAlpha: 0}, 1.5);', 'tl.set("#new", {autoAlpha: 1}, 1.5);'])

    def test_marks_colour(self):
        tl = hf.Timeline()
        self.assertIn('rgba(29,34,40,0.75)', scene.Marks(tl, rgb='29,34,40').box('h', (0, 0, 10, 10)))


class EndCard(unittest.TestCase):
    @staticmethod
    def script(html):
        return html.split('<script>', 1)[1]

    def test_no_logo_means_no_logo_animation(self):
        html = intro.end_card(4.0, 'Go', theme.Theme())
        self.assertNotIn('id="ec-logo"', html)
        self.assertNotIn('#ec-logo', self.script(html))     # a missing target makes GSAP warn in check

    def test_logo_animated_when_set(self):
        html = intro.end_card(4.0, 'Go', theme.Theme(logo='assets/logo.png'))
        self.assertIn('id="ec-logo"', html)
        self.assertEqual(self.script(html).count('#ec-logo'), 2)

    def test_theme_from_dict_keeps_unknown_keys(self):
        t = theme.Theme.from_dict({'accent': '#123456', 'tagline': 'x'})
        self.assertEqual((t.accent, t.extra), ('#123456', {'tagline': 'x'}))


class Voice(unittest.TestCase):
    def test_tokens_split_dashes(self):
        self.assertEqual(voice.tokens('Type a title — it saves.'), ['type', 'a', 'title', 'it', 'saves'])

    def test_verify(self):
        words = [{'text': t} for t in ['Type', 'a', 'title', '—', 'it', 'saves.']]
        self.assertTrue(voice.verify('p', 'Type a title — it saves.', words))

    def test_align_aliases(self):
        heard = [{'text': 'Open', 'start': 0, 'end': .3}, {'text': 'Jaht', 'start': .3, 'end': .6}]
        _, notes = voice.align('p', 'Open Jot', heard, aliases={'jaht': 'jot'})
        self.assertEqual(notes, [])


class Fingerprint(unittest.TestCase):
    def test_refuses_to_overwrite_real_file(self):
        from demofoundry import fingerprint
        d = tempfile.mkdtemp()
        try:
            src, out = os.path.join(d, 'a.html'), os.path.join(d, 'b.html')
            for p in (src, out):
                with open(p, 'w', encoding='utf-8') as f:
                    f.write('<div data-composition-id="x"></div>')
            with self.assertRaises(SystemExit):
                fingerprint.main([src, out])
        finally:
            shutil.rmtree(d)


if __name__ == '__main__':
    unittest.main()
