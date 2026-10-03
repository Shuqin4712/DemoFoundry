"""Find external programs the same way on Windows, macOS and Linux.

On Windows ``npx`` is ``npx.cmd`` and ``subprocess`` will not find it by the bare
name; executables carry ``.exe``. Everything that shells out goes through here.
"""
import glob
import os
import shutil
import sys


def _find(name, hint):
    p = shutil.which(name)
    if not p:
        sys.exit(f'✗ {name} not found on PATH. {hint}')
    return p


def ffmpeg(): return _find('ffmpeg', 'Install ffmpeg (https://ffmpeg.org/download.html) and reopen the terminal.')
def ffprobe(): return _find('ffprobe', 'It ships with ffmpeg.')
def node(): return _find('node', 'Install Node 22+ (https://nodejs.org).')


def npx():
    """Command prefix for npx, as a list (``[path]``)."""
    return [_find('npx', 'It ships with Node 22+ (https://nodejs.org).')]


def headless_chrome():
    """The headless Chrome HyperFrames downloads on first check / render (~/.cache/hyperframes/chrome/)."""
    pat = os.path.expanduser('~/.cache/hyperframes/chrome/chrome-headless-shell/*/*/chrome-headless-shell')
    hits = sorted(glob.glob(pat) + glob.glob(pat + '.exe'))
    if not hits:
        sys.exit('✗ headless Chrome not found. Run a HyperFrames check or render once so it downloads.')
    return hits[-1]
