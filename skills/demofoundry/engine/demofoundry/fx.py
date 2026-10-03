"""Small picture effects that write timeline lines: strokes, wipe reveal, typing, fly-in."""
import math

R3 = lambda v: round(v, 3)


# ───────────────────────── strokes ─────────────────────────
def ellipse_pts(cx, cy, rx, ry, n=72, a0=-100, a1=292, seed=0.6):
    """A hand-drawn ellipse: overshoots the start a little and wobbles 3.5%."""
    pts = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        k = 1 + 0.035 * math.sin(2 * a + seed)
        pts.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)))
    return pts


def path_d(pts): return 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts)
def path_len(pts): return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def draw(tl, sel, L, t, d, ease='power1.inOut'):
    """Draw a stroke of length L from nothing (dashoffset L → 0)."""
    tl.init(sel, f'{{strokeDasharray: {R3(L)}, strokeDashoffset: {R3(L)}, autoAlpha: 0}}')
    tl.set(sel, '{autoAlpha: 1}', t)
    tl.to(sel, f'{{strokeDashoffset: 0, duration: {d}, ease: "{ease}"}}', t)


# ───────────────────────── wipe reveal ─────────────────────────
def wipe(tl, after_sel, wipe_sel, t, width, d=0.55):
    """The 'after' layer opens left to right (clip-path) while a light bar sweeps with it; the bar hides at t+0.56."""
    tl.to(after_sel, f'{{clipPath: "inset(0% 0% 0% 0%)", duration: {d}, ease: "power2.inOut"}}', t)
    tl.show(wipe_sel, t)
    tl.fromto(wipe_sel, '{x: 0}', f'{{x: {width}, duration: {d}, ease: "power2.inOut"}}', t)
    tl.hide(wipe_sel, t + 0.56)


# ───────────────────────── typing ─────────────────────────
def typing_html(text, p='es'):
    """One span per character plus a caret after each; characters switch on one by one (no onUpdate)."""
    return ''.join(f'<span class="{p}-ch" id="{p}-ch{i}">{c if c != " " else "&nbsp;"}</span><span class="{p}-car" id="{p}-car{i+1}"></span>'
                   for i, c in enumerate(text))


def typing_init(tl, n, p='es'):
    for i in range(n):
        tl.init(f'#{p}-ch{i}', '{autoAlpha: 0}'); tl.init(f'#{p}-car{i+1}', '{autoAlpha: 0}')


def typing(tl, n, t0, t1, p='es'):
    """Character i appears evenly between t0 and t1 and the caret follows; ``#<p>-caret0`` is the caret before typing."""
    for i in range(n):
        t = t0 + (t1 - t0) * i / (n - 1)
        tl.show(f'#{p}-ch{i}', t); tl.hide(f'#{p}-car{i}' if i else f'#{p}-caret0', t); tl.show(f'#{p}-car{i+1}', t)


# ───────────────────────── fly-in ─────────────────────────
def fly(tl, sel, src, dst, t):
    """Fly a node-sized element into a target cell. src / dst = (x, y, w, h, radius); the element's left/top sit at src.

    It ends scaled to the target height with the extra width cropped. Three phases:
    0.20s take-off (power3.in) → 0.18s linear → 0.62s settle (power4.out).
    """
    s_end = dst[3] / src[3]
    crop = (src[2] * s_end - dst[2]) / 2 / s_end
    end = (dst[0] - crop * s_end - src[0], dst[1] - src[1], s_end, crop, dst[4] / s_end)
    beg = (0, 0, 1, 0, src[4])
    mix = lambda k: tuple(beg[i] + (end[i] - beg[i]) * k for i in range(5))

    def props(k):
        x, y, sc, c, r = mix(k)
        return f'x: {R3(x)}, y: {R3(y)}, scale: {R3(sc)}, clipPath: "inset(0px {R3(c)}px 0px {R3(c)}px round {R3(r)}px)"'
    tl.init(sel, f'{{{props(0)}, transformOrigin: "0 0"}}')
    tl.show(sel, t)
    tl.to(sel, f'{{{props(0.10)}, duration: 0.20, ease: "power3.in"}}', t)
    tl.to(sel, f'{{{props(0.75)}, duration: 0.18, ease: "none"}}', t + 0.20)
    tl.to(sel, f'{{{props(1)}, duration: 0.62, ease: "power4.out"}}', t + 0.38)
