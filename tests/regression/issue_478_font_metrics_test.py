"""Regression test for #478 - font metrics from Python, and text standing on a ruled line.

Caption.ascent / descent / line_height / baseline_y and Font.metrics(size) report the
FreeType size metrics the layout itself uses, so a caller can place text from them with
no per-font offsets. Ground truth is the screenshot, using generated fonts whose metrics
are whole pixels (_synthetic_font.py): "X" is a box standing on the baseline, "g" a box
hanging below it to the font's full descent.

The ruled-line gate is the use case: a Line at y = L and a Caption with baseline=BASELINE
at (x, L). A Line at integer y fills pixel row L, so text standing on it has its last ink
row at L - 1 (its bottom edge at L) and a descender's bottom edge at L + descent.
"""
import os
import sys
import tempfile

import mcrfpy
from mcrfpy import automation

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # --exec does not put the script's directory on sys.path
import _png  # noqa: E402
import _synthetic_font  # noqa: E402

TMPDIR = tempfile.mkdtemp(prefix="mcrf478m_")
TB = mcrfpy.TextBaseline
failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


def raises(exc, fn):
    try:
        fn()
    except exc:
        return True
    except Exception as e:
        print("    raised %r" % e)
    return False


def shot(name):
    path = os.path.join(TMPDIR, name + ".png")
    automation.screenshot(path)
    return _png.read_png(path)


UPEM, EM = 1000, 20     # 50 font units per pixel at size 20
FONTS = {
    #        ascender, descender, "X" box,            "gjpqy" box
    "tall":  (800, -200, (100, 0, 500, 700), (100, -200, 500, 500)),
    "short": (600, -400, (100, 0, 500, 500), (100, -400, 500, 400)),
}
fonts = {}
for name, (asc, desc, box, dbox) in FONTS.items():
    fonts[name] = mcrfpy.Font(_synthetic_font.write(
        os.path.join(TMPDIR, name + ".ttf"), units_per_em=UPEM, ascender=asc, descender=desc,
        box=box, descender_box=dbox, advance=600))


def px(units, size=EM):
    return units * size / UPEM


print("1. Font.metrics(size) and Caption.ascent/descent/line_height are the design units")
for name, (asc, desc, _b, _d) in FONTS.items():
    for size in (EM, 2 * EM):
        a, d, lh = fonts[name].metrics(size)
        check((a, d) == (px(asc, size), px(-desc, size)),
              "%s @%d: ascent %r, descent %r" % (name, size, a, d))
        check(a + d == px(asc - desc, size), "%s @%d: ascent + descent == em (%r)" % (name, size, a + d))
        check(lh == px(asc - desc, size), "%s @%d: line_height %r (no line gap)" % (name, size, lh))
        c = mcrfpy.Caption(text="X", font=fonts[name], font_size=size)
        check((c.ascent, c.descent, c.line_height) == (a, d, lh), "%s @%d: Caption agrees" % (name, size))
dm = mcrfpy.default_font.metrics(16)
c = mcrfpy.Caption(text="x", font_size=16)
# FreeType grid-fits each metric on its own, so line_height need not equal ascent + descent.
check((c.ascent, c.descent, c.line_height) == dm and min(dm) > 0,
      "default font @16: %r" % (dm,))
for bad in (0, -3, 4096):
    check(raises(ValueError, lambda: fonts["tall"].metrics(bad)), "metrics(%d) raises ValueError" % bad)
check(raises(TypeError, lambda: fonts["tall"].metrics("20")), "metrics('20') raises TypeError")

print("2. baseline_y per mode")
for font in (fonts["tall"], fonts["short"], mcrfpy.default_font):
    for size in (EM, 33, 48):
        for mode in TB:
            c = mcrfpy.Caption(text="X", pos=(5, 60), font=font, font_size=size, baseline=mode)
            want = {TB.TOP: 60 + c.ascent, TB.BASELINE: 60, TB.EM_TOP: 60 + size}[mode]
            check(c.baseline_y == want, "%s @%d %s: baseline_y %r == %r"
                  % (font.family or "default", size, mode.name, c.baseline_y, want))
c = mcrfpy.Caption(text="X", pos=(5, 60), font=fonts["tall"], font_size=EM)
c.y = 100
check(c.baseline_y == 100 + c.ascent, "baseline_y follows y")

print("3. line_height is the distance between the lines of a two-line caption")
scene = mcrfpy.Scene("m478_lines")
mcrfpy.current_scene = scene
caps = []
for i, name in enumerate(FONTS):
    caps.append(mcrfpy.Caption(text="X\nX", pos=(20 + 60 * i, 20), font=fonts[name], font_size=EM,
                               fill_color=(255, 255, 0) if i == 0 else (0, 255, 255)))
    scene.children.append(caps[-1])
img = shot("lines")
for cap, color in zip(caps, ((255, 255, 0), (0, 255, 255))):
    rows = sorted({y for _x, y in _png.mask(img, color)})
    starts = [r for r in rows if r - 1 not in rows]
    check(len(starts) == 2 and starts[1] - starts[0] == cap.line_height,
          "%s: ink runs start %s, line_height %r" % (cap.font.source.rsplit("/", 1)[-1], starts, cap.line_height))

print("4. Ruled line: text placed at the line with BASELINE stands on it")
L = 80
scene = mcrfpy.Scene("m478_ruled")
mcrfpy.current_scene = scene
RED, YELLOW = (255, 0, 0), (255, 255, 0)
scene.children.append(mcrfpy.Line(start=(0, L), end=(400, L), color=RED))
caps = []
for i, name in enumerate(FONTS):
    for j, size in enumerate((EM, 2 * EM)):
        x = 20 + 100 * (2 * i + j)
        cap = mcrfpy.Caption(text="XgX", pos=(x, L), font=fonts[name], font_size=size,
                             baseline=TB.BASELINE, fill_color=YELLOW)
        scene.children.append(cap)
        caps.append((name, size, cap))
img = shot("ruled")
line_rows = sorted({y for x, y in _png.mask(img, RED, (390, 0, 400, 200))})
check(line_rows == [L], "the Line at y=%d fills row %s" % (L, line_rows))
for name, size, cap in caps:
    adv = cap.advance / 3  # monospace: one glyph advance
    x0 = int(cap.x)
    ink_x = _png.mask(img, YELLOW, (x0, 0, x0 + int(adv), 200))
    ink_g = _png.mask(img, YELLOW, (x0 + int(adv), 0, x0 + int(2 * adv), 200))
    bx, bg = _png.bbox(ink_x), _png.bbox(ink_g)
    check(bx is not None and bx[3] == L,
          "%s @%d: 'X' ink ends on row %s, directly above the line" % (name, size, bx and bx[3] - 1))
    check(bg is not None and bg[3] == L + cap.descent,
          "%s @%d: 'g' hangs %s px below the line == descent %r" % (name, size, bg and bg[3] - L, cap.descent))

print("=" * 50)
if failures:
    print("FAIL (%d)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
