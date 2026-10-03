"""Series intro and end card. Same rhythm every episode; wording and look come from the theme.

Intro: (optional) star burst that lands on the canvas dot grid → a glowing
pill with the feature name appears when the narration says it → corner
caption fades in → the pill scales out → the first subject rises in.

End card: logo lockup + call to action + site pill (+ optional "Powered by").
"""
import json
import math

from . import hf


def intro_css(theme):
    g = theme.accent_glow_rgb
    face = theme.font_face()
    return f'''      {face}
      @property --orbit-angle{{syntax:"<angle>";inherits:false;initial-value:-120deg}}
      .es-stage{{position:absolute;inset:0;overflow:hidden;pointer-events:none}}
      #es-stars{{z-index:24}}
      .warp-star{{position:absolute;width:0;height:0;will-change:transform}}
      .warp-rotation{{position:absolute;width:0;height:0}}
      .warp-streak{{position:absolute;right:0;top:-1px;width:72px;height:2px;border-radius:999px;background:linear-gradient(to left,rgba(255,255,255,.98),rgba(205,198,228,.45) 42%,rgba(205,198,228,0));transform-origin:100% 50%}}
      .warp-core{{position:absolute;left:0;top:0;width:4px;height:4px;margin:-2px 0 0 -2px;border-radius:50%;background:#fff;box-shadow:0 0 7px rgba(213,205,255,.82)}}
      #es-wordwrap{{position:absolute;inset:0;display:grid;place-items:center;z-index:25;pointer-events:none}}
      .word{{position:relative;height:126px;padding:0 84px;display:grid;place-items:center;border:1px solid rgba(222,211,255,.7);border-radius:64px;background:rgba(10,10,13,.92);font-family:{theme.font_stack};font-size:59px;line-height:.9;letter-spacing:-.055em;font-weight:520;color:{theme.ink};white-space:nowrap;box-shadow:0 0 20px rgba({g},.4),0 22px 44px rgba(0,0,0,.7),inset 0 -2px 14px rgba(111,255,220,.16);overflow:visible}}
      .word-copy{{position:relative;z-index:2}}
      .word-glow{{--orbit-angle:-120deg;position:absolute;inset:-3px;border-radius:67px;padding:3px;pointer-events:none;background:conic-gradient(from var(--orbit-angle),transparent 0deg,transparent 188deg,rgba({g},.12) 216deg,rgba({g},.72) 278deg,#fff 322deg,{theme.accent_soft} 338deg,transparent 360deg);-webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask-composite:exclude;filter:drop-shadow(0 0 5px rgba(255,255,255,.9)) drop-shadow(0 0 15px rgba({g},.82))}}
      .es-corner{{position:absolute;right:82px;bottom:67px;z-index:23;color:{theme.corner_ink};font-family:{theme.font_stack};font-size:15px;letter-spacing:.12em;text-transform:uppercase;pointer-events:none}}
'''


def intro_html(word, corner):
    """Goes after the camera layer (#es-cam) and before the vignette."""
    return (f'<div class="es-stage" id="es-stars"><div id="es-denseStars"></div></div>\n'
            f'      <div id="es-wordwrap"><div class="word" id="es-word"><span class="word-copy">{word}</span><span class="word-glow"></span></div></div>\n'
            f'      <div class="es-corner" id="es-corner">{corner}</div>')


def intro_stars(shot, grid_left=-2400, grid_top=-2600, step=48, canvas=(1920, 1080)):
    """Optional star burst whose stars land on the dot grid as seen through the opening shot.

    For products with a dotted canvas the intro settles into the very canvas the
    episode then plays on. Products without one can skip it (``intro_timeline``
    works without the stars). Returns (JS to place after ``const tl``, xs, ys).
    """
    cx, cy = canvas[0] / 2, canvas[1] / 2
    _hx, _hy, _hs = shot
    _x0 = grid_left + 24 + math.ceil(((_hx - cx / _hs) - (grid_left + 24)) / step) * step
    _y0 = grid_top + 24 + math.ceil(((_hy - cy / _hs) - (grid_top + 24)) / step) * step
    xs = [round(cx + (wx - _hx) * _hs, 2) for wx in range(int(_x0), int(_hx + cx / _hs) + 1, step)]
    ys = [round(cy + (wy - _hy) * _hs, 2) for wy in range(int(_y0), int(_hy + cy / _hs) + 1, step)]
    cxs, cys = hf_num(cx), hf_num(cy)
    block = f'''// stars: burst from the centre, land on the canvas grid points
      const starData = [], starEls = [], streakEls = [], coreEls = [];
      const hash = (v) => {{ const n = Math.sin(v * 127.1 + 311.7) * 43758.5453; return n - Math.floor(n); }};
      let seed = 0;
      for (const x of {json.dumps(xs)}) {{
        for (const y of {json.dumps(ys)}) {{
          seed += 1;
          if (hash(seed + 3000) < 0.18) continue;
          const dx = x - {cxs}, dy = y - {cys}, distance = Math.max(1, Math.hypot(dx, dy));
          const startRatio = 0.035 + hash(seed) * 0.23, midRatio = 0.43 + hash(seed + 1000) * 0.17;
          const length = 28 + hash(seed + 2000) * 98 * Math.min(1, distance / 650);
          const star = document.createElement("i"), rotation = document.createElement("i"), streak = document.createElement("i"), core = document.createElement("i");
          star.className = "warp-star"; rotation.className = "warp-rotation"; streak.className = "warp-streak"; core.className = "warp-core";
          star.style.left = x + "px"; star.style.top = y + "px";
          rotation.style.transform = "rotate(" + (Math.atan2(dy, dx) * 180 / Math.PI) + "deg)";
          rotation.appendChild(streak); star.appendChild(rotation); star.appendChild(core);
          document.querySelector("#es-denseStars").appendChild(star);
          starData.push({{ dx, dy, startRatio, midRatio, length, distance }});
          starEls.push(star); streakEls.push(streak); coreEls.push(core);
        }}
      }}
      gsap.set(starEls, {{ x: (i) => starData[i].dx * (starData[i].startRatio - 1), y: (i) => starData[i].dy * (starData[i].startRatio - 1), autoAlpha: 0 }});
      gsap.set(streakEls, {{ scaleX: 0.02, opacity: 0.92 }});
      gsap.set(coreEls, {{ scale: 0.72 }});
      tl.to(starEls, {{ autoAlpha: (i) => 0.42 + hash(i + 8000) * 0.58, duration: 0.26, ease: "power1.out" }}, 0)
        .to(starEls, {{ x: (i) => starData[i].dx * (starData[i].midRatio - 1), y: (i) => starData[i].dy * (starData[i].midRatio - 1), duration: 1.55, ease: "power2.in" }}, 0)
        .to(streakEls, {{ scaleX: (i) => starData[i].length / 72, duration: 1.55, ease: "power2.in" }}, 0)
        .to(starEls, {{ x: 0, y: 0, duration: (i) => 0.92 + Math.min(0.38, starData[i].distance / 3000), ease: "power4.out" }}, 1.55)
        .to(streakEls, {{ scaleX: 0.015, opacity: 0, duration: 0.72, ease: "power4.out" }}, 1.61)
        .to(coreEls, {{ scale: 0.8, duration: 0.54, ease: "power2.inOut" }}, 2.12)
        .to(starEls, {{ autoAlpha: 0.12, duration: 0.5, ease: "power2.inOut" }}, 2.28)
        .to("#es-stars", {{ autoAlpha: 0, duration: 0.5, ease: "power3.in" }}, 2.5);'''
    return block, xs, ys


def hf_num(v):
    return int(v) if v == int(v) else v


def intro_timeline(tl, words, vo_start, keyword, end, subject_sel, last_word, comment='// intro', grid_sel='#es-grid'):
    """Pill appears on ``keyword`` with its border light orbiting → 1.34s grid and corner fade in →
    0.6s after ``last_word`` the pill scales out → 0.26s later the subject rises in → corner hides at end+0.2.

    words: the intro narration's words.json; vo_start: where that clip sits in the episode. Times are absolute.
    """
    from .cues import word_time
    iw = lambda w: word_time(words, w, vo_start)
    A = lambda t: t - tl.offset
    tl.js(comment)
    if grid_sel:
        tl.init(grid_sel, '{autoAlpha: 0}')
    tl.init('#es-word', '{autoAlpha: 0, scale: 0.72}')
    tl.init('#es-corner', '{autoAlpha: 0}')
    tl.init(subject_sel, '{autoAlpha: 0, y: 120, scale: 0.78, transformOrigin: "50% 50%"}')
    tl.to('#es-word', '{autoAlpha: 1, scale: 1, duration: 0.7, ease: "power4.out"}', A(iw(keyword) - 0.02))
    tl.to('.word-glow', '{"--orbit-angle": "240deg", duration: 2.0, ease: "power1.inOut"}', A(iw(keyword)))
    if grid_sel:
        tl.to(grid_sel, '{autoAlpha: 1, duration: 1.25, ease: "power4.out"}', A(1.34))
    tl.to('#es-corner', '{autoAlpha: 1, duration: 0.6, ease: "power2.out"}', A(1.34))
    t_exit = iw(last_word) + 0.60
    tl.to('#es-word', '{autoAlpha: 0, scale: 1.17, duration: 0.5, ease: "power3.in"}', A(t_exit))
    tl.to(subject_sel, '{autoAlpha: 1, y: 0, scale: 1, duration: 0.62, ease: "power4.out"}', A(t_exit + 0.26))
    tl.to('#es-corner', '{autoAlpha: 0, duration: 0.24}', A(end + 0.2))


def end_card(duration, cta, theme, canvas=(1920, 1080)):
    """End-card sub-composition: logo lockup, CTA, site pill, optional "Powered by" (theme.powered_by)."""
    w, h = canvas
    by = (f'      <div id="ec-by">{f"<img src={chr(34)}{theme.powered_icon}{chr(34)} alt={chr(34)}{chr(34)}>" if theme.powered_icon else ""}'
          f'<span>Powered by {theme.powered_by}</span></div>') if theme.powered_by else ''
    logo = f'<img id="ec-logo" src="{theme.logo}" alt="{theme.logo_alt}">' if theme.logo else ''
    pill = f'<span id="ec-pill">{theme.site}</span>' if theme.site else ''
    # without a logo the CTA leads; animating a missing #ec-logo would warn "GSAP target not found"
    logo_js = ['gsap.set("#ec-logo", {x:5, y:-32});'] if theme.logo else []
    logo_tl = ['tl.fromTo("#ec-logo", {scale:0.72, filter:"blur(13px)"}, {scale:1, filter:"blur(0px)", duration:0.65, ease:"power4.out", immediateRender:false}, 0.06);'] if theme.logo else []
    js = [*logo_js,
          'gsap.set("#ec-lockup", {autoAlpha:0});',
          'gsap.set(".ec-spark", {scale:0});',
          'const tl = gsap.timeline({ paused: true });',
          'tl.to("#ec-lockup", {autoAlpha:1, duration:0.34}, 0.03);',
          *logo_tl,
          'tl.to(".ec-spark", {scale:1, duration:0.5, ease:"back.out(1.7)", stagger:0.1}, 0.03);']
    style = f'''
      {theme.font_face()}
      #root{{position:absolute;inset:0;width:{w}px;height:{h}px;overflow:hidden;font-family:{theme.font_stack};color:{theme.ink}}}
      #ec-ground{{position:absolute;inset:0;background:{theme.ground}}}
      #ec-lockup{{position:absolute;inset:0;display:grid;place-items:center;text-align:center;font-family:{theme.font_stack}}}
      #ec-stack{{display:flex;flex-direction:column;align-items:center}}
      #ec-logo{{display:block;width:{theme.logo_width}px;height:auto;margin:0 auto}}
      #ec-cta{{margin:18px 0 0;color:{theme.ink_mute};font-size:18px;font-weight:400;letter-spacing:.11em;text-transform:uppercase}}
      #ec-pill{{display:inline-flex;margin-top:30px;padding:13px 23px;border:1px solid {theme.accent};border-radius:999px;box-shadow:0 0 28px rgba({theme.accent_glow_rgb},.42);font-size:14px}}
      #ec-by{{position:absolute;left:0;right:0;bottom:80px;display:flex;justify-content:center;align-items:center;gap:8px;font-size:14px;color:{theme.ink_mute}}}
      #ec-by img{{width:18px;height:18px}}
      .ec-spark{{position:absolute;width:5px;height:5px;border-radius:50%;background:{theme.accent_soft};box-shadow:0 0 12px {theme.accent}}}
'''
    body = f'''      <div id="ec-ground" class="clip" data-start="0" data-duration="{duration}"></div>
      <div id="ec-lockup"><div id="ec-stack">
      {logo}
      <p id="ec-cta">{cta}</p>{pill}
      </div><i class="ec-spark" style="left:31%;top:44%"></i><i class="ec-spark" style="left:69%;top:39%"></i><i class="ec-spark" style="left:65%;top:67%"></i></div>
{by}'''
    return hf.composition_html('end-card', duration, body, style=style, script=chr(10).join('      ' + l for l in js).strip(), canvas=canvas)
