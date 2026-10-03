"""Episode 01 · Quick notes (regression fixture).

Writes (overwrites): compositions/frames/01-story.html, compositions/frames/02-end-card.html, index.html.
Edit this generator, never the generated HTML.

  python -m demofoundry gen tests/fixtures/jot/demofoundry/episodes/01-quick-note

Blocks: B0 intro → B1 "Click New note" → B2 type a title (camera on the editor) → B3 Share → toast → B4 close → end card.
Times come from narration words (``W(clip, word)``), so re-voicing and regenerating keeps everything aligned.
"""
import os

from demofoundry import cues, fx, hf, intro, io, scene, stage, studio

ROOT = os.path.dirname(os.path.abspath(__file__))
S = studio.Studio(ROOT)
ui = S.ui()
TH = S.theme
MOLD = S.sync_mold()

W = cues.Cues(ROOT, 'voice/final')
TOTAL = W.total
END_CARD = 4.0
STORY_END = round(TOTAL - END_CARD, 3)
WORD_TEXT, CORNER_TEXT, CTA = 'Quick Notes', 'Capture first, tidy later', 'Jot it down, share it fast.'
TITLE_TEXT = 'Weekly plan'

# ───────────────────────── world ─────────────────────────
WIN = (0, 0, ui.WIN_W, ui.WIN_H)
at = lambda p: (WIN[0] + p[0], WIN[1] + p[1])
CAM = {
    'all': (600, 360, 1.2),                                  # whole window
    'editor': (ui.TITLE[0] + 260, ui.TITLE[1] + 60, 2.0),    # B2: the title line and the first body lines
}

# ───────────────────────── key words ─────────────────────────
t_quick, t_jot = W('sec0', 'quick'), W('sec0', 'Jot')
t_click, t_opens = W('sec1', 'Click'), W('sec1', 'opens')
t_type, t_title, t_saves = W('sec2', 'Type'), W('sec2', 'title'), W('sec2', 'saves')
t_share, t_team = W('sec3', 'Share'), W('sec3', 'team')

MOVES = [
    (round(W.start['sec2'] - 0.7, 3), 0.6, 'editor'),       # the title is the subject: too small at the overview
    (round(W.start['sec3'] - 0.7, 3), 0.6, 'all'),          # Share sits in the top bar: back out
]

tl = hf.Timeline()
cam = stage.Camera(tl, CAM, MOVES, start='all', canvas=S.canvas)
cur = stage.Cursor(tl, cam, size=TH.cursor_size)
marks = scene.Marks(tl, rgb='29,34,40')                  # Jot is a light UI: dark explanation marks
tl.js('// initial state')
cam.init_state(); cur.init_state()
tl.js('// camera')
cam.emit_moves()

# ───────────────────────── markup ─────────────────────────
NOTES = [(TITLE_TEXT, 'Just now', True), ('Groceries', 'Milk, eggs, coffee', False), ('Ideas', 'Weekend project list', False)]
EDITOR = ui.editor('es-doc', '<span class="tt-car" id="tt-caret0"></span>' + fx.typing_html(TITLE_TEXT, 'tt'))
WORLD = [ui.window('es-win', *WIN[:2], NOTES, EDITOR)]
tl.init('#es-win-n0', '{autoAlpha: 0}')                     # the new note, shown on click
tl.init('#tt-caret0', '{autoAlpha: 0}')
tl.init('#es-doc', '{autoAlpha: 0}')
tl.init('#es-doc-saved', '{autoAlpha: 0}')
fx.typing_init(tl, len(TITLE_TEXT), 'tt')
WORLD.append(marks.box('es-hl-title', (ui.TITLE[0] - 6, ui.TITLE[1] - 4, 280, 52), pad=8, r=10, k=CAM['editor'][2]))
OVER = [ui.toast('es-toast', 960 - ui.TOAST_W / 2, 900, 'Link copied')]
tl.init('#es-toast', '{autoAlpha: 0}')

# ───────────────────────── B0 intro ─────────────────────────
intro.intro_timeline(tl, W.words('sec0'), W.start['sec0'], 'quick', 4.0, '#es-win', last_word='Jot',
                     comment=f'// B0 intro: pill "{WORD_TEXT}" on "quick" → window rises in after "Jot"')
STARS, _, _ = intro.intro_stars(CAM['all'], canvas=S.canvas)

# ───────────────────────── B1 New note ─────────────────────────
tl.js(f'// B1 "Click" {round(t_click, 3)}: new note in the list, empty editor opens')
cur.enter(round(t_click - 0.75, 3), *at(ui.NEW_BTN))
cur.click(round(t_click - 0.05, 3))
scene.appear(tl, '#es-win-n0', round(t_click + 0.05, 3), origin='50% 0%', scale=0.96, d=0.25)
scene.appear(tl, '#es-doc', round(t_click + 0.1, 3), origin='0% 0%', scale=0.98, d=0.3)
cur.exit(round(t_opens + 0.1, 3))

# ───────────────────────── B2 type a title ─────────────────────────
tl.js(f'// B2 "Type" {round(t_type, 3)} → typed title → "saves" {round(t_saves, 3)} Saved')
tl.hide('#es-doc-ph', t_type)
tl.show('#tt-caret0', t_type)
fx.typing(tl, len(TITLE_TEXT), round(t_type + 0.05, 3), round(t_saves - 0.2, 3), 'tt')
scene.pop_in(tl, '#es-doc-saved', t_saves, origin='100% 50%')
marks.box_on('es-hl-title', round(t_title - 0.1, 3), round(W.end['sec2'] + 0.3, 3))

# ───────────────────────── B3 Share ─────────────────────────
tl.js(f'// B3 "Share" {round(t_share, 3)} → toast')
cur.enter(round(W.start['sec3'] + 0.05, 3), *at(ui.SHARE_BTN))
cur.click(round(t_share - 0.05, 3))
scene.pop_in(tl, '#es-toast', round(t_share + 0.2, 3))
tl.hide('#es-toast', round(W.end['sec4'] + 0.2, 3), 0.3)
cur.exit(round(t_team + 0.2, 3))

# ───────────────────────── assemble ─────────────────────────
STYLE = f'''
{intro.intro_css(TH)}{stage.cursor_css(TH)}{scene.scene_css(TH)}      #root{{position:absolute;inset:0;width:{S.canvas[0]}px;height:{S.canvas[1]}px;overflow:hidden}}
      #es-ground{{position:absolute;inset:0;background:{TH.ground}}}
      #es-cam{{position:absolute;left:0;top:0;width:10px;height:10px}}
      #es-world{{position:absolute;left:0;top:0}}
      .es-grid{{position:absolute;left:-2400px;top:-2600px;width:7200px;height:6000px;background:radial-gradient(circle,rgba(255,255,255,.14) 1.3px,transparent 1.6px) 0 0/48px 48px}}
'''
INIT_JS, TL_JS = tl.script()
body = f'''      <div id="es-ground" class="clip" data-start="0" data-duration="{STORY_END}"></div>
      <div id="es-cam"><div id="es-world">
      <div class="es-grid" id="es-grid"></div>
      {''.join(WORLD)}
      </div></div>
      {''.join(OVER)}
      {intro.intro_html(WORD_TEXT, CORNER_TEXT)}
      {stage.cursor_svg(TH).replace('id="es-cur"', 'id="es-cur" data-layout-allow-overflow=""')}'''
script = f'''{INIT_JS}
      const tl = gsap.timeline({{ paused: true }});
      {STARS}
      {TL_JS}'''
io.write(ROOT, 'compositions/frames/01-story.html',
         hf.composition_html('story', STORY_END, body, style=STYLE, script=script, links=[f'{MOLD}/css/jot.css'], canvas=S.canvas))
io.write(ROOT, 'compositions/frames/02-end-card.html', intro.end_card(END_CARD, CTA, TH, canvas=S.canvas))
io.write(ROOT, 'index.html', hf.index_html(
    'quick-note', TOTAL,
    [('scene-story', 'story', 'compositions/frames/01-story.html', 0, STORY_END),
     ('scene-end-card', 'end-card', 'compositions/frames/02-end-card.html', STORY_END, END_CARD)],
    W.clips(), 'voice/final/clips', TH, vo_bus=S.mix['vo_bus'], bgm_vol=S.mix['bgm_vol'], bgm=None,
    badge_hide_at=STORY_END, canvas=S.canvas))
print(f'✓ generated: 01-story ({len(tl.T)} timeline lines) · 02-end-card · index.html ({len(W.clips())} narration clips)  total={TOTAL}  end card from {STORY_END}')
