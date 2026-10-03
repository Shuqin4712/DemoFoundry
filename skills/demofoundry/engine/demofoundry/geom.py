"""Wires between nodes: horizontal out of the out-port, horizontal into the in-port.

Node-editor products (canvases, flow builders) draw connections this way. The
end points sit ``port_r`` outside the node edges so the line plugs into the
port; set ``port_r`` from the product's measured port radius.
"""
import math

from . import fx


def wire_between(a, b, k=0.5, port_r=0.0):
    """Two node rects (x, y, w, h) → cubic Bézier path ``d``."""
    ax, ay = a[0] + a[2] + port_r, a[1] + a[3] / 2
    bx, by = b[0] - port_r, b[1] + b[3] / 2
    dx = bx - ax
    ext = max(48, min(abs(dx) * k, 320))
    if dx < 0: ext = max(ext, abs(dx) * 0.9 + 90)
    r = lambda n: round(n * 10) / 10
    return f'M{r(ax)} {r(ay)} C{r(ax + ext)} {r(ay)} {r(bx - ext)} {r(by)} {r(bx)} {r(by)}'


def bez_len(d, n=200):
    """Length of a ``wire_between`` path (for the stroke-dasharray of a draw-on)."""
    v = [float(x) for x in d.replace('M', ' ').replace('C', ' ').split()]
    P = [(v[i], v[i + 1]) for i in range(0, 8, 2)]
    pt = lambda t: tuple((1 - t) ** 3 * P[0][k] + 3 * (1 - t) ** 2 * t * P[1][k] + 3 * (1 - t) * t * t * P[2][k] + t ** 3 * P[3][k] for k in (0, 1))
    return sum(math.dist(pt(i / n), pt((i + 1) / n)) for i in range(n))


def port_out(r, port_r=0.0): return (r[0] + r[2] + port_r, r[1] + r[3] / 2)
def port_in(r, port_r=0.0): return (r[0] - port_r, r[1] + r[3] / 2)


class Wires:
    """Remembers each wire's path so it can be drawn on or measured later.

        W = Wires(port_r=5.75, cls='acme-wire')
        svg += W.path('w-a', rect_a, rect_b)
        W.draw(tl, 'w-a', t)
    """

    def __init__(self, port_r=0.0, cls='wire'):
        self.port_r, self.cls = port_r, cls
        self.d = {}

    def path(self, wid, a, b, k=0.5):
        self.d[wid] = wire_between(a, b, k, self.port_r)
        return f'<path class="{self.cls}" id="{wid}" d="{self.d[wid]}"/>'

    def length(self, wid):
        return bez_len(self.d[wid])

    def draw(self, tl, wid, t, dur=0.4, ease='power2.out'):
        fx.draw(tl, f'#{wid}', self.length(wid), t, dur, ease)
