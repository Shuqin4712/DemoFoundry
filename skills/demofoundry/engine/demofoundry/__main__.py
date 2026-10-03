"""Command line: ``python -m demofoundry <command> ...`` (or ``demofoundry <command>`` when installed).

  voice        recordings → aligned, checked, cut, laid-out narration
  recording    index a product screen recording; crop evidence frames
  refprofile   measure screenshots into JSON
  bgm          fit a music bed to an episode
  fingerprint  make a standalone probe page from a sub-composition
  serve        no-cache static server for proof pages
  gen          run an episode generator (episodes/<NN>-<slug>/gen.py)
"""
import importlib
import os
import runpy
import sys

COMMANDS = {'voice': 'voice', 'recording': 'recording', 'refprofile': 'refprofile', 'bgm': 'bgm',
            'fingerprint': 'fingerprint', 'serve': 'serve'}


def gen(argv):
    """Run an episode's gen.py with the engine importable, from the episode folder."""
    if not argv:
        sys.exit('usage: demofoundry gen <episode folder> [generator args]')
    ep = os.path.abspath(argv[0])
    script = os.path.join(ep, 'gen.py')
    if not os.path.isfile(script):
        sys.exit(f'✗ no gen.py in {ep}')
    sys.argv = [script] + argv[1:]
    runpy.run_path(script, run_name='__main__')


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        sys.exit(__doc__)
    cmd, rest = sys.argv[1], sys.argv[2:]
    if cmd == 'gen':
        return gen(rest)
    if cmd not in COMMANDS:
        sys.exit(f'unknown command {cmd!r}\n{__doc__}')
    importlib.import_module(f'demofoundry.{COMMANDS[cmd]}').main(rest)


if __name__ == '__main__':
    main()
