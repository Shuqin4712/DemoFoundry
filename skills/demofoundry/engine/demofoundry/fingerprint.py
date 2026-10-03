"""Turn a sub-composition into a standalone probe page that can be driven and measured on its own.

  python -m demofoundry fingerprint <compositions/frames/01-story.html> [.fp-before.html] [--force]

Removes the root's ``data-composition-id`` (a second root composition in the project would make
HyperFrames ``check`` report multiple_root_compositions); the timeline registers by literal id,
so playback is unaffected. Seek the timeline strictly (``tl.seek(t)``) and read geometry with
``getBoundingClientRect()`` / ``gsap.getProperty``: hand maths is wrong under 3D transforms.

Guard: the output must be a dot-file (``.fingerprint.html``) unless ``--force``; a shell glob once
expanded into two files and overwrote a production composition.
"""
import os
import re
import sys


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    force = '--force' in args
    args = [a for a in args if a != '--force']
    if not args:
        sys.exit(__doc__)
    src, out = args[0], (args[1] if len(args) > 1 else '.fingerprint.html')
    if os.path.exists(out) and not os.path.basename(out).startswith('.') and not force:
        sys.exit(f'refusing to overwrite {out}: probe pages are dot-files (default .fingerprint.html). '
                 'Add --force if you really mean it. A shell glob expanding into two files is the usual cause.')
    with open(src, encoding='utf-8') as f:
        s = f.read()
    s = re.sub(r'(<script src="[^"]*gsap[^"]*"></script>)', r'\1\n<script>window.__timelines={};</script>', s, count=1)
    s = re.sub(r'\sdata-composition-id="[^"]*"', '', s, count=1)
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write(s)
    print(f'{src} → {out} ({len(s)} bytes, data-composition-id removed)')
