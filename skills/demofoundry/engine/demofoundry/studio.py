"""The ``demofoundry/`` folder in a product repo: config, mold, episodes.

    demofoundry/
      demofoundry.json        theme, canvas, mix
      mold/ui.py              the product's markup functions and anchors
      mold/css/, mold/icons/, mold/fonts/
      episodes/<NN>-<slug>/   one HyperFrames project per episode (gen.py writes it)

HyperFrames serves only the episode folder, so ``sync_mold`` copies the mold's
css / icons / fonts into ``<episode>/assets/mold/`` on every generate (no
symlinks: they need developer mode on Windows).
"""
import importlib.util
import json
import os
import shutil

from .theme import Theme

MOLD_ASSETS = ('css', 'icons', 'fonts')


class Studio:
    def __init__(self, episode_root):
        self.episode = os.path.abspath(episode_root)
        self.root = self.find_root(self.episode)
        with open(os.path.join(self.root, 'demofoundry.json'), encoding='utf-8') as f:
            self.config = json.load(f)
        self.mold_dir = os.path.join(self.root, 'mold')
        self.theme = Theme.from_dict(self.config.get('theme', {}))
        self.canvas = tuple(self.config.get('canvas', (1920, 1080)))
        self.mix = {'vo_bus': 0.75, 'bgm_vol': 0.32, **self.config.get('mix', {})}

    @staticmethod
    def find_root(start):
        d = start
        while True:
            if os.path.isfile(os.path.join(d, 'demofoundry.json')):
                return d
            parent = os.path.dirname(d)
            if parent == d:
                raise SystemExit(f'✗ no demofoundry.json above {start}')
            d = parent

    def ui(self):
        """Import the mold's ``ui.py`` as a module."""
        p = os.path.join(self.mold_dir, 'ui.py')
        spec = importlib.util.spec_from_file_location('mold_ui', p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def sync_mold(self):
        """Copy mold css / icons / fonts into ``<episode>/assets/mold/`` (replaced each time)."""
        dst_root = os.path.join(self.episode, 'assets', 'mold')
        if os.path.isdir(dst_root):
            shutil.rmtree(dst_root)
        for d in MOLD_ASSETS:
            src = os.path.join(self.mold_dir, d)
            if os.path.isdir(src):
                shutil.copytree(src, os.path.join(dst_root, d))
        return 'assets/mold'
