"""DemoFoundry engine: builds HyperFrames compositions for narrated product tutorials.

An episode generator (``episodes/<NN>-<slug>/gen.py``) imports the pieces it needs:

    from demofoundry import hf, cues, stage, fx, geom, scene, intro, studio, theme, io

hf      HyperFrames output: timeline lines, sub-composition shell, index.html, audio attributes
cues    cue timeline: word times scoped by narration clip
stage   camera (named shots + moves) and the oversized cursor
fx      strokes, wipe reveal, typing, fly-in
geom    wires between nodes
studio  the demofoundry/ folder: config → theme, mold ui.py, mold assets sync
scene   scene-level helpers (state swaps, generate → result, explanation marks, media placeholders)
intro   series intro and end card
theme   series look (colours, font, cursor, wording slots)
io      UTF-8 / LF file helpers
"""
__version__ = '0.1.0'
