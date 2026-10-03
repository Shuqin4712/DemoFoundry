"""Camera and cursor over a world laid out in 1x logical px.

The world (nodes, panels) sits in a container the camera transforms; the
camera is a table of named shots plus a list of moves. Cursor positions are
given in world coordinates and resolved through the camera, so the tip lands
on the target at any zoom.
"""
from . import fx

R3 = lambda v: round(v, 3)


def num(v):
    """Round to 3 places and drop a trailing .0 so 960.0 prints as 960."""
    v = round(v, 3)
    return int(v) if v == int(v) else v


class Camera:
    """shots = {name: (world centre x, world centre y, scale)}; moves = [(start, duration, shot name)].

    Every move should have a reason (write it next to the move). Asking for a
    screen position while the camera is moving raises: cursor work happens on a
    locked camera.
    """

    def __init__(self, tl, shots, moves, start, sel='#es-cam', ease='power3.inOut', canvas=(1920, 1080)):
        self.tl, self.shots, self.moves, self.start, self.sel, self.ease = tl, shots, moves, start, sel, ease
        self.cx, self.cy = num(canvas[0] / 2), num(canvas[1] / 2)

    def at(self, t):
        cur = self.start
        for t0, d, k in self.moves:
            if t >= t0 + d: cur = k
            elif t >= t0: raise ValueError(f'cursor used while the camera moves ({t}s, {k}): lock the camera during cursor work')
        return self.shots[cur]

    def scr(self, wx, wy, t):
        cx, cy, s = self.at(t)
        return self.cx + (wx - cx) * s, self.cy + (wy - cy) * s

    def rect(self, r, shot):
        """World rect (x, y, w, h) → screen rect under a named shot (camera at rest)."""
        cx, cy, k = self.shots[shot]
        return (self.cx + (r[0] - cx) * k, self.cy + (r[1] - cy) * k, r[2] * k, r[3] * k)

    def init_state(self):
        cx, cy, s = self.shots[self.start]
        self.tl.init(self.sel, f'{{x: {R3(self.cx - cx * s)}, y: {R3(self.cy - cy * s)}, scale: {s}, transformOrigin: "0 0"}}')

    def emit_moves(self):
        for t0, d, k in self.moves:
            cx, cy, s = self.shots[k]
            self.tl.to(self.sel, f'{{x: {R3(self.cx - cx * s)}, y: {R3(self.cy - cy * s)}, scale: {s}, duration: {d}, ease: "{self.ease}"}}', t0)


def cursor_css(theme, sel='es-cur'):
    s = theme.cursor_size
    return f'      #{sel}{{position:absolute;left:0;top:0;width:{s}px;height:{s}px;z-index:40;filter:drop-shadow(0 7px 12px rgba(0,0,0,.5));pointer-events:none}}\n'


def cursor_svg(theme, sel='es-cur'):
    return (f'<svg id="{sel}" viewBox="0 0 64 64" aria-hidden="true"><path d="M11 6v43l11-11 9 19 9-5-9-18h17z" '
            f'fill="{theme.cursor_fill}" stroke="{theme.cursor_stroke}" stroke-width="3" stroke-linejoin="round"/></svg>')


class Cursor:
    """Oversized arrow cursor. Tip at (11, 6) of a 64 viewBox, i.e. 17% / 9%.

    Entrance rule: it rises straight up from below the frame. A click is press
    0.1s : release 0.2s.
    """

    def __init__(self, tl, cam, sel='#es-cur', size=96):
        self.tl, self.cam, self.sel = tl, cam, sel
        self.tipx, self.tipy = size * 11 / 64, size * 6 / 64
        w, h = cam.cx * 2, cam.cy * 2
        self.below = num(h + 100)                # parked under the frame
        self.park_x = num(w / 2 - 60)
        self.off = (num(w + 160), num(h + 120))  # exit target, past the bottom-right corner

    def init_state(self):
        self.tl.init(self.sel, f'{{x: {self.park_x}, y: {self.below}, autoAlpha: 0}}')

    def to(self, t, wx, wy, d, ease='power2.inOut', at=None):
        sx, sy = self.cam.scr(wx, wy, at if at is not None else t + d)
        self.tl.to(self.sel, f'{{x: {R3(sx - self.tipx)}, y: {R3(sy - self.tipy)}, duration: {d}, ease: "{ease}"}}', t)
        return sx, sy

    def screen(self, t, sx, sy, d, ease='power2.inOut'):
        self.tl.to(self.sel, f'{{x: {R3(sx - self.tipx)}, y: {R3(sy - self.tipy)}, duration: {d}, ease: "{ease}"}}', t)

    def enter(self, t, wx, wy, d=0.45):
        sx, sy = self.cam.scr(wx, wy, t + d)
        self.tl.set(self.sel, f'{{x: {R3(sx - self.tipx)}, y: {self.below}, autoAlpha: 1}}', t)
        self.tl.to(self.sel, f'{{y: {R3(sy - self.tipy)}, duration: {d}, ease: "power3.out"}}', t)

    def press(self, t, s=0.84):
        self.tl.to(self.sel, f'{{scale: {s}, duration: 0.1, ease: "power2.in", transformOrigin: "17% 9%"}}', t)

    def release(self, t):
        self.tl.to(self.sel, '{scale: 1, duration: 0.2, ease: "power2.out", transformOrigin: "17% 9%"}', t)

    def click(self, t):                           # release 2ms after the press ends so the tweens never touch
        self.press(t); self.release(t + 0.102)

    def exit(self, t, d=0.5):
        self.screen(t, *self.off, d, 'power2.in')

    def drag_wire(self, t, wire_sel, wire_len, drop, d=0.6, press_lead=0.08, ease='power1.inOut'):
        """Drag a wire out of a node's out-port to ``drop`` (world coords).

        Press ``press_lead`` before t; cursor and wire travel the same curve for
        the same duration; release at t + d. The cursor should already rest on
        the port and the wire path must end at ``drop``. Returns the release time.
        Tuned against a product recording: lead 0.08s, travel 0.6s, power1.inOut.
        """
        self.press(t - press_lead)
        self.to(t, *drop, d, ease)
        fx.draw(self.tl, wire_sel, wire_len, t, d, ease)
        self.release(t + d)
        return t + d
