"""Everything that emits HyperFrames-specific markup lives in this module.

HyperFrames renders HTML + GSAP to video. Its contract is a few conventions:
GSAP timelines registered on ``window.__timelines``, ``data-composition-*``
attributes, ``<template>``-wrapped sub-compositions, ``<audio>`` clips with
``data-start`` / ``data-duration``, ``<hf-audio-group>``, and the declarative
audio attributes ``data-fx-chain`` / ``data-fx-carve`` / ``data-automation``.

Keeping all of it here leaves one place to change if the format moves or the
engine is ever swapped out. Other modules only call ``Timeline`` methods.
"""
import html as _html
import json
import os
import re
import sys

from . import io

R3 = lambda v: round(v, 3)

# Same pin HyperFrames' own project template uses (hyperframes init, 0.8.114); not redistributed in this repo.
GSAP_CDN = 'https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js'


# ───────────────────────── timeline ─────────────────────────
class Timeline:
    """Collects GSAP timeline lines.

    ``t`` is episode time; ``offset`` shifts everything on output (e.g. when an
    intro is inserted in front). Lines are emitted in call order.
    """

    def __init__(self, offset=0.0):
        self.offset = offset
        self.T, self.INIT = [], []

    def js(self, s): self.T.append(s)
    def init(self, sel, props): self.INIT.append(f'gsap.set("{sel}", {props});')
    def set(self, sel, props, t): self.js(f'tl.set("{sel}", {props}, {R3(t + self.offset)});')
    def to(self, sel, props, t): self.js(f'tl.to("{sel}", {props}, {R3(t + self.offset)});')
    def fromto(self, sel, a, b, t): self.js(f'tl.fromTo("{sel}", {a}, {{...{b}, immediateRender: false}}, {R3(t + self.offset)});')

    def show(self, sel, t, d=0.0):
        if d == 0: self.set(sel, '{autoAlpha: 1}', t)
        else: self.to(sel, f'{{autoAlpha: 1, duration: {d}}}', t)

    def hide(self, sel, t, d=0.0):
        if d == 0: self.set(sel, '{autoAlpha: 0}', t)
        else: self.to(sel, f'{{autoAlpha: 0, duration: {d}}}', t)

    def script(self, indent='      '):
        """(initial gsap.set lines, timeline lines), indented for the template."""
        return (chr(10).join(indent + l for l in self.INIT).strip(),
                chr(10).join(indent + l for l in self.T).strip())


# ───────────────────────── sub-composition ─────────────────────────
def composition_html(comp_id, duration, body, style='', script='', links=(), canvas=(1920, 1080), title=None):
    """A ``<template>``-wrapped sub-composition.

    ``links`` are stylesheet hrefs. They must sit in ``<head>``: a ``<link>``
    inside ``<template>`` is never loaded and HyperFrames ``check`` does not
    report it (learned the hard way).
    """
    w, h = canvas
    head_links = ''.join(f'\n  <link rel="stylesheet" href="{l}">' for l in links)
    return f'''<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>{title or comp_id}</title>{head_links}
</head>
<body>
  <template>
    <style>{style}    </style>
    <div id="root" data-composition-id="{comp_id}" data-width="{w}" data-height="{h}" data-duration="{duration}">
      <!-- generated; edit the generator, not this file -->
{body}
    </div>
    <script>
      {script}
      window.__timelines["{comp_id}"] = tl;
    </script>
  </template>
</body>
</html>
'''


# ───────────────────────── audio ─────────────────────────
def fx_chain(*nodes):
    """``data-fx-chain`` JSON. Nodes are dicts like ``{"type": "gain", "id": "g1", "params": {"gain": 6}}``."""
    return json.dumps({'version': 1, 'nodes': list(nodes)}, separators=(',', ':'))


def gain_limiter(gain_db, prefix='g', limit=-1, attack=5, release=80):
    """Gain then limiter. Used to lift quiet narration (e.g. imported TTS around -22 LUFS) without touching the wav."""
    return fx_chain({'type': 'gain', 'id': f'{prefix}1', 'params': {'gain': gain_db}},
                    {'type': 'limiter', 'id': f'{prefix}2', 'params': {'limit': limit, 'attack': attack, 'release': release}})


def bgm_length_check(root, total, rel='assets/bgm/track.wav'):
    """The BGM trim is baked into the wav, so a changed episode length needs a re-trim (the fade-out must land on the end)."""
    n = io.wav_duration(root, rel)
    if abs(n - total) > 0.02:
        print(f'! {rel} is {n:.2f}s, episode is {total}s: re-trim it so the fade-out lands on the end')


def carve(root, rel='_build/bgm-carve.json', index='index.html', extra_lanes=(), extra_nodes=()):
    """Persist and replay the voice-ducking attributes written by upstream ``carve.mjs``.

    ``carve.mjs`` writes ``data-fx-carve`` / ``data-fx-chain`` / ``data-automation``
    straight into ``index.html``; regenerating would wipe them. Run the generator
    with ``--save-carve`` once after ``carve.mjs`` to store them; later runs replay
    them. Only carve's own nodes and lanes are stored, so nodes the generator
    appends (``extra_nodes`` / ``extra_lanes``, e.g. a whole-episode volume arc)
    are never duplicated.

    Returns the attribute string for ``<audio id="bgm">`` ('' when nothing saved).
    """
    p = os.path.join(root, rel)
    if '--save-carve' in sys.argv:
        cur = io.read(root, index)
        m = re.search(r'<audio[^>]*id="bgm"[^>]*>', cur).group(0)
        saved = {a: json.loads(_html.unescape(re.search(a + r'="([^"]*)"', m).group(1)))
                 for a in ('data-fx-carve', 'data-fx-chain', 'data-automation')}
        saved['data-fx-carve']['sources'] = ['voiceover']        # carve.mjs lists clips; point it back at the group
        own = {n['id'] for n in saved['data-fx-chain']['nodes'] if n.get('fromCarve')}
        saved['data-fx-chain']['nodes'] = [n for n in saved['data-fx-chain']['nodes'] if n['id'] in own]
        saved['data-automation']['lanes'] = [l for l in saved['data-automation']['lanes'] if l['target'].split('.')[1] in own]
        io.write_json(root, rel, saved, indent=1)
        print(f'saved carve to {rel}')
        sys.exit(0)
    if not os.path.exists(p):
        return ''
    saved = io.load_json(root, rel)
    saved['data-fx-chain']['nodes'] += list(extra_nodes)
    saved['data-automation']['lanes'] += list(extra_lanes)
    return ''.join(f' {k}="{_html.escape(json.dumps(v, separators=(",", ":")), quote=True)}"'
                   for k, v in saved.items())


# ───────────────────────── index.html ─────────────────────────
def index_html(comp_id, total, scenes, vo, clip_dir, theme, vo_bus=0.75, bgm_vol=0.32, carve_attrs='',
               bgm='assets/bgm/track.wav', vo_chain=None, extra_audio=(), badge_hide_at=None, badge_hide_ranges=(),
               canvas=(1920, 1080), gsap_src=GSAP_CDN):
    """The root timeline: scene mounts, the voiceover group, BGM and an optional series badge.

    scenes = [(element id, composition id, src, start, duration)]
    vo     = [{clip, start, dur}] from the voice layout
    vo_chain: ``data-fx-chain`` for every narration clip (see ``gain_limiter``); put it
              on the clips, not on the group (group chains lost the audio on export in 0.8.34)
    extra_audio: ready-made ``<audio>`` tags, e.g. a product clip's own sound
    theme: ``Theme``; its ``badge_text`` / ``badge_logo`` draw the series badge (empty = none)
    badge_hide_at: hide the badge from this time on (e.g. the end card)
    badge_hide_ranges: [(a, b)] fade the badge out over scenes it would cover, back in at b
    bgm: set to None when there is no track yet
    """
    w, h = canvas
    scene_lines = '\n'.join(
        f'      <div id="{sid}" class="scene" data-composition-id="{cid}" data-composition-src="{src}" data-start="{start}" data-duration="{dur}" data-track-index="1" data-width="{w}" data-height="{h}"></div>'
        for sid, cid, src, start, dur in scenes)
    chain = f" data-fx-chain='{vo_chain}'" if vo_chain else ''
    audios = '\n'.join(
        f'      <audio id="vo-{c["clip"]}" src="{clip_dir}/{c["clip"]}.wav" data-start="{c["start"]}" data-duration="{c["dur"]}" data-audio-group="voiceover" data-track-index="10" data-volume="1"{chain}></audio>'
        for c in vo)
    audios += ''.join('\n      ' + a for a in extra_audio)
    bgm_line = (f'\n      <audio id="bgm" src="{bgm}" data-start="0" data-duration="{total}" '
                f'data-track-index="20" data-volume="{bgm_vol}"{carve_attrs}></audio>') if bgm else ''
    badge, badge_css = '', ''
    if theme.badge_text or theme.badge_logo:
        logo = f'<img src="{theme.badge_logo}" alt="">' if theme.badge_logo else ''
        badge = f'\n      <div id="seriesBrand" class="series-brand" data-layout-ignore="">{logo}{theme.badge_text}</div>'
        badge_css = (f'\n      {theme.font_face()}'
                     f'\n      .series-brand {{ position: absolute; left: 82px; top: 67px; z-index: 50; display: flex; align-items: center; color: {theme.badge_ink}; font-family: {theme.font_stack}; font-size: 16px; letter-spacing: 0.14em; text-transform: uppercase; pointer-events: none; }}'
                     f'\n      .series-brand img {{ width: 24px; height: 24px; display: block; margin-right: 10px; border-radius: 6px; }}')
    hide = f'\n      tl.set("#seriesBrand", {{autoAlpha:0}}, {badge_hide_at});' if badge and badge_hide_at is not None else ''
    if badge:
        hide += ''.join(f'\n      tl.to("#seriesBrand", {{autoAlpha:0, duration:0.3}}, {a});\n      tl.to("#seriesBrand", {{autoAlpha:1, duration:0.3}}, {b});' for a, b in badge_hide_ranges)
    return f'''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width={w}, height={h}">
    <script src="{gsap_src}"></script>
    <style>
      * {{ box-sizing: border-box; }}
      html, body {{ width: {w}px; height: {h}px; margin: 0; overflow: hidden; background: {theme.ground}; }}
      #root {{ position: relative; width: {w}px; height: {h}px; overflow: hidden; background: {theme.ground}; }}
      .scene {{ position: absolute; inset: 0; width: 100%; height: 100%; }}{badge_css}
    </style>
  </head>
  <body>
    <!-- generated; seam blocks are stamped from ledger.json by seam-stamp.mjs -->
    <div id="root" data-composition-id="{comp_id}" data-start="0" data-duration="{total}" data-width="{w}" data-height="{h}">
{scene_lines}
      <hf-audio-group id="voiceover" data-label="Voiceover" data-volume="{vo_bus}"></hf-audio-group>{badge}{bgm_line}
{audios}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      // <seams:auto>
      // </seams:auto>{hide}
      window.__timelines["{comp_id}"] = tl;
    </script>
  </body>
</html>
'''
