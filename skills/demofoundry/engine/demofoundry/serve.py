"""No-cache static server for proof pages and technique cards.

  python -m demofoundry serve [port] [--root DIR]

A normal static server lets the browser keep old CSS (``@import``-ed sheets even stay in
memory across navigations), and a proof page then reports results for styles you already
changed. This one sends no-store on every response.
"""
import functools
import http.server
import os
import sys


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache'); self.send_header('Expires', '0')
        super().end_headers()

    def log_message(self, *a):
        pass


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    root = '.'
    if '--root' in args:
        i = args.index('--root'); root = args[i + 1]; args = args[:i] + args[i + 2:]
    port = int(args[0]) if args else 8777
    http.server.ThreadingHTTPServer.allow_reuse_address = True
    handler = functools.partial(Handler, directory=os.path.abspath(root))
    with http.server.ThreadingHTTPServer(('127.0.0.1', port), handler) as s:
        print(f'serving {os.path.abspath(root)} on http://127.0.0.1:{port} (no-store)')
        s.serve_forever()
