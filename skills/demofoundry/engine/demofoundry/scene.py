"""Scene-level helpers: the moves every tutorial repeats.

These were rewritten in almost every episode of the source series; they live
here once. They write through a ``hf.Timeline`` and never touch the DOM layout.

Part naming contract (a mold's ``ui.py`` emits these ids for anything that
"generates" a result):

    <id>-card    the card; selection is a class switch on it
    <id>-gen     "generating" layer, holds <id>-spin
    <id>-after   result layer, starts clipped (clip-path inset 0 100% 0 0)
    <id>-wipe    light bar that sweeps during the reveal
    <id>-badge   size badge shown after the reveal (optional)
"""
import os

from . import fx

R3 = lambda v: round(v, 3)


# ───────────────────────── states ─────────────────────────
def cls(tl, sel, c, t):
    """Switch an element's class (the way component states change)."""
    tl.set(sel, f'{{className: "{c}"}}', t)


def swap(tl, old, new, t):
    """Replace one layer with another at the same instant.

    Two separate fades, even 0.01s apart, leave a frame at 60fps where neither
    is visible: a flicker. Set both at exactly ``t``.
    """
    tl.set(old, '{autoAlpha: 0}', t); tl.set(new, '{autoAlpha: 1}', t)


def pop_in(tl, sel, t, origin='50% 100%', d=0.18):
    """Popover / menu entrance: slight scale-up from its anchor edge."""
    tl.fromto(sel, f'{{autoAlpha: 0, scale: 0.97, transformOrigin: "{origin}"}}', f'{{autoAlpha: 1, scale: 1, duration: {d}, ease: "power3.out"}}', t)


def appear(tl, sel, t, origin='50% 50%', scale=0.94, d=0.34):
    """Node / card entrance."""
    tl.fromto(sel, f'{{autoAlpha: 0, scale: {scale}, transformOrigin: "{origin}"}}', f'{{autoAlpha: 1, scale: 1, duration: {d}, ease: "power3.out"}}', t)


def emit_from(tl, sel, src, dst, t, d=0.45):
    """A new node leaves its source: it starts small at the source's centre and flies to its own place.
    Use it when the product shows no wire for the relation but the origin should read."""
    dx, dy = src[0] + src[2] / 2 - (dst[0] + dst[2] / 2), src[1] + src[3] / 2 - (dst[1] + dst[3] / 2)
    tl.fromto(sel, f'{{x: {R3(dx)}, y: {R3(dy)}, scale: 0.85, transformOrigin: "50% 50%"}}', f'{{x: 0, y: 0, scale: 1, duration: {d}, ease: "power3.out"}}', t)
    tl.fromto(sel, '{autoAlpha: 0}', '{autoAlpha: 1, duration: 0.12, ease: "power1.out"}', t)


def dim(tl, sels, t, on=True, d=0.35, level=0.32):
    """Darken what is not being talked about (and bring it back with on=False)."""
    for s in sels:
        tl.to(s, f'{{filter: "brightness({level if on else 1})", duration: {d}, ease: "power2.inOut"}}', t)


def fly_to(tl, sel, src, dst, t, d=0.75, ease='power3.inOut'):
    """FLIP: an element laid out at ``dst`` starts looking like ``src`` (screen rects) and moves into place."""
    tl.fromto(sel, f'{{x: {R3(src[0] - dst[0])}, y: {R3(src[1] - dst[1])}, scaleX: {R3(src[2] / dst[2])}, scaleY: {R3(src[3] / dst[3])}, transformOrigin: "0 0"}}',
              f'{{x: 0, y: 0, scaleX: 1, scaleY: 1, duration: {d}, ease: "{ease}"}}', t)


# ───────────────────────── generate → result ─────────────────────────
def spin(tl, nid, t, d):
    """Show the generating layer and turn its spinner for d seconds."""
    tl.show(f'#{nid}-gen', t)
    tl.fromto(f'#{nid}-spin', '{rotation: 0}', f'{{rotation: {int(d * 450)}, duration: {R3(d)}, ease: "none"}}', t)


def reveal(tl, nid, t, width, gen=True, badge=False):
    """Wipe the result in, drop the generating layer, optionally fade the badge in."""
    fx.wipe(tl, f'#{nid}-after', f'#{nid}-wipe', t, width)
    if gen: tl.hide(f'#{nid}-gen', t + 0.56)
    if badge: tl.show(f'#{nid}-badge', t + 0.4, 0.2)


# ───────────────────────── explanation marks ─────────────────────────
# Not product UI: marks we add to explain. Keep them quiet (thin, translucent).
class Marks:
    """Collects the markup of explanation marks and their initial states.

        m = Marks(tl)                      # Marks(tl, rgb='29,34,40') on a light UI
        html += m.box('hl-a', rect, k=cam_scale)
        m.box_on('hl-a', t0, t1)
    """

    def __init__(self, tl, rgb='255,255,255'):
        self.tl, self.rgb = tl, rgb                # white suits dark UIs; give a dark rgb for light UIs

    def box(self, hid, rect, pad=6, r=14, k=1.0, opacity=0.75):
        """Dashed box drawn on clockwise. k = camera scale of the beat, so the line is ~2px on screen at any zoom."""
        x, y, w, h = rect
        sw, dash = R3(2.08 / k), f'{R3(9.1 / k)} {R3(6.5 / k)}'
        W_, H_ = R3(w + 2 * pad), R3(h + 2 * pad)
        rr = f'x="1" y="1" width="{R3(W_ - 2)}" height="{R3(H_ - 2)}" rx="{r}"'   # the dashed layer must not carry pathLength
        self.tl.init(f'#{hid}', '{autoAlpha: 0}')
        return f'''<svg class="es-hld" id="{hid}" style="left:{R3(x - pad)}px;top:{R3(y - pad)}px" width="{W_}" height="{H_}">
        <mask id="{hid}-m"><rect id="{hid}-draw" {rr} pathLength="1" fill="none" stroke="#fff" stroke-width="6" stroke-dasharray="1 1" stroke-dashoffset="1"/></mask>
        <rect {rr} fill="none" stroke="rgba({self.rgb},{opacity})" stroke-width="{sw}" stroke-dasharray="{dash}" mask="url(#{hid}-m)"/></svg>'''

    def box_on(self, hid, t0, t1):
        self.tl.show(f'#{hid}', t0, 0.1)
        self.tl.fromto(f'#{hid}-draw', '{attr: {"stroke-dashoffset": 1}}', '{attr: {"stroke-dashoffset": 0}, duration: 0.4, ease: "power2.inOut"}', t0)
        self.tl.hide(f'#{hid}', t1, 0.3)

    def tag(self, tid, x, y, text, k=1.0, align='right'):
        """Small caps caption. (x, y) = the aligned end (or centre) and vertical centre; ~22px on screen at any zoom."""
        c = {'left': ' l', 'center': ' c'}.get(align, '')
        self.tl.init(f'#{tid}', '{autoAlpha: 0}')
        return f'<div class="es-cltag{c}" id="{tid}" style="left:{R3(x)}px;top:{R3(y)}px;--fs:{R3(22 / k)}px"><span>{text}</span></div>'

    def tag_on(self, tid, t0, t1, dx=6):
        self.tl.fromto(f'#{tid}', f'{{autoAlpha: 0, x: {dx}}}', '{autoAlpha: 1, x: 0, duration: 0.25, ease: "power3.out"}', t0)
        self.tl.hide(f'#{tid}', t1, 0.2)


def line_hl(tl, sel, t0, t1=None, rgb='120,57,238', alpha=0.38):
    """Light up a line of text (background fades in, and out at t1)."""
    tl.to(sel, f'{{backgroundColor: "rgba({rgb},{alpha})", duration: 0.22, ease: "power2.out"}}', t0)
    if t1 is not None:
        tl.to(sel, f'{{backgroundColor: "rgba({rgb},0)", duration: 0.35, ease: "power2.in"}}', t1)


# ───────────────────────── wires ─────────────────────────
def pulses(tl, wires, wid, t0, t1, d=0.8, seg=80, n=[0]):
    """Light dots travelling along a wire from t0 until t1 (input flowing into a node). Returns the path markup."""
    L = wires.length(wid)
    k = max(1, int((t1 - t0) / d))
    pid = f'{wid}-pl{n[0]}'; n[0] += 1
    tl.init(f'#{pid}', '{autoAlpha: 0}')
    tl.show(f'#{pid}', t0)
    for i in range(k):
        tl.fromto(f'#{pid}', f'{{strokeDashoffset: {seg}}}', f'{{strokeDashoffset: {R3(-L)}, duration: {d}, ease: "power1.inOut"}}', R3(t0 + i * d))
    tl.hide(f'#{pid}', R3(t0 + k * d), 0.1)
    return f'<path class="es-pulse" id="{pid}" d="{wires.d[wid]}" stroke-dasharray="{seg} {R3(L + seg + 20)}" stroke-dashoffset="{seg}"/>'


# ───────────────────────── glow ─────────────────────────
def dominant_rgb(path):
    """Main colour of an image (near-white / near-black ignored), saturated and brightened for a glow. Needs Pillow."""
    import colorsys
    from PIL import Image
    im = Image.open(path).convert('RGB').resize((64, 64))
    px = [c for c in (im.get_flattened_data() if hasattr(im, 'get_flattened_data') else im.getdata()) if 24 < sum(c) / 3 < 232]
    r, g, b = (sum(c[i] for c in px) / len(px) / 255 for i in range(3))
    h, sa, v = colorsys.rgb_to_hsv(r, g, b)
    r, g, b = colorsys.hsv_to_rgb(h, min(1, sa * 1.9 + 0.08), max(v, 0.78))
    return int(r * 255), int(g * 255), int(b * 255)


def halo(tl, nid, rect, rgb, pad=90):
    """Soft light behind a node in its result's colour. Returns markup; start it with ``glow_reveal``."""
    x, y, w, h = rect
    c = ','.join(map(str, rgb))
    tl.init(f'#{nid}-halo', '{autoAlpha: 0}')
    return (f'<div class="es-halo" id="{nid}-halo" style="left:{R3(x - pad)}px;top:{R3(y - pad)}px;width:{R3(w + 2 * pad)}px;height:{R3(h + 2 * pad)}px;'
            f'background:radial-gradient(closest-side,rgba({c},.5),rgba({c},.14) 55%,rgba({c},0) 80%)"></div>')


def glow_reveal(tl, nid, t):
    """The halo flares when the result lands, then settles to a low steady glow."""
    tl.fromto(f'#{nid}-halo', '{autoAlpha: 0, scale: 0.85, transformOrigin: "50% 50%"}', '{autoAlpha: 1, scale: 1, duration: 0.55, ease: "power2.out"}', t)
    tl.to(f'#{nid}-halo', '{autoAlpha: 0.32, duration: 1.6, ease: "power2.inOut"}', R3(t + 1.0))


# ───────────────────────── media ─────────────────────────
class Media:
    """Episode media with placeholders: missing files draw a striped placeholder,
    so pictures can be built before the assets arrive; drop the file in and regenerate.

    files = {key: path relative to ``base``}
    """

    def __init__(self, root, files, base='assets/media'):
        self.root, self.files, self.base = root, files, base

    def has(self, k): return os.path.exists(os.path.join(self.root, self.base, self.files[k]))
    def path(self, k): return f'{self.base}/{self.files[k]}'
    def missing(self): return [k for k in self.files if not self.has(k)]

    @staticmethod
    def placeholder(label, note='pending'):
        return f'<div class="es-phm"><span>{label}</span><small>{note}</small></div>'

    def img(self, k, label):
        return f'<img class="es-fill" src="{self.path(k)}" alt="">' if self.has(k) else self.placeholder(label)

    def video(self, k, label, vid, start, dur, media_start=0.0, track=2):
        if not self.has(k):
            return self.placeholder(label)
        return (f'<video id="{vid}" class="clip es-fill" src="{self.path(k)}" data-start="{R3(start)}" data-duration="{R3(dur)}" '
                f'data-media-start="{R3(media_start)}" data-track-index="{track}" muted playsinline></video>')

    def video_block(self, tl, k, label, vid, runs, length, first, last, restore=()):
        """A clip shown inside a card that plays once per appearance, never loops.

        Layers: last frame at the bottom, first frame on top, clips above both.
        Before the first run the card holds the first frame; after each run it
        rests on the last frame (a finished node is still). ``restore`` = times
        to show the first frame again (e.g. after a "rebuild from scratch").
        first / last = media keys of the two stills.
        """
        if not self.has(k):
            return self.placeholder(label)
        layers = f'<img class="es-fill" src="{self.path(last)}" alt=""><img class="es-fill" id="{vid}-f0" src="{self.path(first)}" alt="">'
        clips = []
        for j, (a, b) in enumerate(runs):
            b = min(b, a + length)
            if b - a > 0.05:
                clips.append(self.video(k, '', f'{vid}{j}', a, b - a))
                tl.set(f'#{vid}-f0', '{autoAlpha: 0}', R3(b))
        for t in restore:
            tl.set(f'#{vid}-f0', '{autoAlpha: 1}', t)
        return layers + ''.join(clips)


def scene_css(theme):
    """CSS the helpers above rely on."""
    return f'''      .es-fill{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block}}
      .es-after{{position:absolute;inset:0}}
      .es-wipe{{position:absolute;top:0;bottom:0;left:-1.5px;width:3px;background:#fff;box-shadow:0 0 18px 4px rgba({theme.accent_glow_rgb},.85),0 0 6px #fff}}
      .es-hld{{position:absolute;overflow:visible;pointer-events:none;z-index:30}}
      .es-halo{{position:absolute;border-radius:50%;pointer-events:none}}
      .es-pulse{{fill:none;stroke:{theme.accent_soft};stroke-width:3.2;stroke-linecap:round}}
      .es-cltag{{position:absolute;z-index:31;width:0;height:0;pointer-events:none}}
      .es-cltag.l>span{{right:auto;left:0}}
      .es-cltag.c>span{{right:auto;left:0;transform:translateX(-50%)}}
      .es-cltag>span{{position:absolute;right:0;top:-.5em;white-space:nowrap;color:{theme.ink_mute};font-family:{theme.font_stack};font-size:var(--fs,8.5px);line-height:1;letter-spacing:.14em;text-transform:uppercase}}
      .es-phm{{position:absolute;inset:0;display:grid;place-content:center;justify-items:center;gap:6px;background:repeating-linear-gradient(135deg,#15151b 0 14px,#18181f 14px 28px);color:#8b8a99;font-size:15px;text-align:center}}
      .es-phm small{{font-size:11px;color:#5d5c6a;letter-spacing:.08em}}
'''
