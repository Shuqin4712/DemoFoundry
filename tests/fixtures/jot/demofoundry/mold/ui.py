"""Mold markup for "Jot", a made-up notes app used as the regression fixture.

FIXTURE: these components were written for the test, not rebuilt from product
evidence, so they carry no measurements. A real mold's ui.py looks the same but
every constant cites its source (Figma node, recording time, screenshot).

Units: 1x logical px. Components describe how things look; position comes from
the caller. Child ids are ``<instance id>-<part>``.
"""

R3 = lambda v: round(v, 3)

# ───────────────────────── geometry (anchors, relative to the window's top-left) ─────────────────────────
WIN_W, WIN_H = 1200, 720
SIDEBAR_W = 280
NEW_BTN = (140, 116)                         # "New note" centre: left 20 + 240/2; top bar 64 + top 32 + 40/2
TITLE = (SIDEBAR_W + 48, 112)                # title baseline-left in the editor: padding 48, top bar 64 + 48
SHARE_BTN = (WIN_W - 24 - 46, 32)            # "Share" centre: right padding 24, button 92 wide, top bar 64 high
TOAST_W = 260


def window(wid, x, y, notes, body=''):
    """App window: top bar, sidebar with a note list, editor area (``body``)."""
    items = ''.join(f'<div class="jot-item{" is-on" if on else ""}" id="{wid}-n{i}"><b>{t}</b><span>{s}</span></div>'
                    for i, (t, s, on) in enumerate(notes))
    return f'''
      <div class="jot-window" id="{wid}" style="left:{R3(x)}px;top:{R3(y)}px">
        <div class="jot-top"><span class="jot-brand">Jot</span><button class="jot-share" id="{wid}-share">Share</button></div>
        <div class="jot-side"><button class="jot-new" id="{wid}-new">+ New note</button><div class="jot-list" id="{wid}-list">{items}</div></div>
        <div class="jot-editor" id="{wid}-editor">{body}</div>
      </div>'''


def editor(eid, title_html, placeholder='Untitled'):
    """Editor body: title line (``title_html``, e.g. typing spans) over a placeholder, then empty body lines."""
    lines = ''.join(f'<i style="width:{w}%"></i>' for w in (92, 84, 88, 61))
    return f'''<div class="jot-doc" id="{eid}">
          <div class="jot-title"><span class="jot-ph" id="{eid}-ph">{placeholder}</span><span class="jot-tt" id="{eid}-tt">{title_html}</span></div>
          <div class="jot-lines" id="{eid}-lines">{lines}</div>
          <div class="jot-saved" id="{eid}-saved">Saved</div>
        </div>'''


def toast(tid, x, y, text):
    """Bottom toast (screen space)."""
    return f'<div class="jot-toast" id="{tid}" style="left:{R3(x)}px;top:{R3(y)}px;width:{TOAST_W}px" data-layout-ignore="">{text}</div>'
