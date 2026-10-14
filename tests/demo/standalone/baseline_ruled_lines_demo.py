#!/usr/bin/env python3
"""Text standing on ruled lines, placed purely from font metrics (#478).

Each row is one font: a Line at y = L, a Caption with baseline=TextBaseline.BASELINE at
(x, L), so the text stands on the line and descenders (g, j, p, q, y) hang below it,
and two faint guides at L + caption.descent and L - caption.ascent. Every position comes
from the metrics properties (ascent, descent, line_height, advance); nothing is tuned
per font. The bottom panel shows the same text at one pos.y under TOP, BASELINE and
EM_TOP, with a line at that y.

Fonts: the bundled JetBrains Mono at three sizes, plus any font files given on the
command line or in MCRF_DEMO_FONTS (colon-separated). A path may end in "@SIZE" to pick
its pixel size (default 32), e.g. Px437_IBM_EGA_8x14.ttf@32: the Px437 pixel fonts have a
16 px em whatever their cell height, so multiples of 16 keep their pixels whole.

    ./mcrogueface ../tests/demo/standalone/baseline_ruled_lines_demo.py
    MCRF_DEMO_FONTS=/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf@28 \\
        ./mcrogueface --headless --exec ../tests/demo/standalone/baseline_ruled_lines_demo.py

MCRF_DEMO_SHOT=path.png saves a screenshot and exits.
"""
import os
import sys

import mcrfpy

TB = mcrfpy.TextBaseline
TEXT = "Typography: jumpy quokka"
DEFAULT_SIZE = 32
MARGIN = 10                     # px of air between rows and around panels
LABEL_SIZE = 12
LINE = mcrfpy.Color(220, 80, 80)
GUIDE = mcrfpy.Color(90, 90, 140)
INK = mcrfpy.Color(240, 240, 240)
LABEL = mcrfpy.Color(150, 150, 170)
BUILTIN = [("assets/JetbrainsMono.ttf", 16), ("assets/JetbrainsMono.ttf", 24),
           ("assets/JetbrainsMono.ttf", 40)]


def parse(spec):
    path, _, size = spec.rpartition("@")
    if path and size.isdigit():
        return path, int(size)
    return spec, DEFAULT_SIZE


def font_specs():
    specs = list(BUILTIN)
    extra = [a for a in sys.argv[1:] if not a.startswith("-")]
    extra += [s for s in os.environ.get("MCRF_DEMO_FONTS", "").split(":") if s]
    specs += [parse(s) for s in extra]
    return specs


def hline(parent, y, x0, x1, color):
    parent.children.append(mcrfpy.Line(start=(x0, y), end=(x1, y), color=color))


def ruled_row(scene, font, size, top, width):
    """Lay one row out below `top`; return the y below it."""
    label = mcrfpy.Caption(text="%s @%d" % (os.path.basename(font.source), size), font_size=LABEL_SIZE,
                           pos=(MARGIN, top), fill_color=LABEL)
    scene.children.append(label)
    cap = mcrfpy.Caption(text=TEXT, font=font, font_size=size, baseline=TB.BASELINE, fill_color=INK)
    L = top + label.line_height + cap.ascent          # room for the label, then the ascent
    cap.pos = (MARGIN, L)
    hline(scene, L - cap.ascent, MARGIN, width - MARGIN, GUIDE)
    hline(scene, L + cap.descent, MARGIN, width - MARGIN, GUIDE)
    hline(scene, L, MARGIN, width - MARGIN, LINE)
    scene.children.append(cap)
    label.text += "   ascent %g  descent %g  line_height %g" % (cap.ascent, cap.descent, cap.line_height)
    print("row %s @%d: line y=%g ascent=%g descent=%g line_height=%g"
          % (font.source, size, L, cap.ascent, cap.descent, cap.line_height))
    return L + cap.descent + MARGIN


def modes_panel(scene, font, size, top, width):
    """The same text at one y under each TextBaseline, with a line at that y."""
    probe = mcrfpy.Caption(text="Hgy", font=font, font_size=size)
    y = top + LABEL_SIZE * 2 + max(probe.ascent, 0) + MARGIN   # BASELINE's ink reaches ascent above y
    hline(scene, y, MARGIN, width - MARGIN, LINE)
    x = MARGIN
    for mode in (TB.TOP, TB.BASELINE, TB.EM_TOP):
        scene.children.append(mcrfpy.Caption(text="pos.y, " + mode.name, font_size=LABEL_SIZE,
                                             pos=(x, top), fill_color=LABEL))
        cap = mcrfpy.Caption(text="Hgy", font=font, font_size=size, baseline=mode,
                             pos=(x, y), fill_color=INK)
        scene.children.append(cap)
        x += max(cap.advance, 120) + 4 * MARGIN
    return y + size + probe.descent + MARGIN


def build():
    scene = mcrfpy.Scene("baseline_ruled_lines")
    mcrfpy.current_scene = scene
    width = 1024
    y = MARGIN
    for path, size in font_specs():
        try:
            font = mcrfpy.Font(path)
        except IOError as e:
            print("skipping %s: %s" % (path, e))
            continue
        y = ruled_row(scene, font, size, y, width)
    modes_panel(scene, mcrfpy.default_font, 40, y + MARGIN, width)
    return scene


build()

shot = os.environ.get("MCRF_DEMO_SHOT")
if shot:
    from mcrfpy import automation
    automation.screenshot(shot)
    print("screenshot:", shot)
    sys.exit(0)
