"""Regression test for #478 - TextBaseline.EM_TOP reproduces the pre-#478 placement exactly.

Before #478 every Caption put its first baseline at pos.y + font_size (SFML's rule).
TextBaseline.EM_TOP keeps that rule for layouts that depend on it. The reference image
tests/fixtures/issue_478_em_top_reference.png was captured from the engine *before*
the change (0.3.3-dev at c1b05a7), by running this script with
MCRF_478_WRITE_REFERENCE=1 (which skips the comparison and writes the reference).

Everything is drawn at whole-pixel positions without rotation, so the image is the
font rasterizer's output blitted 1:1 and does not depend on the GL implementation.
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

REFERENCE = os.path.join(HERE, "..", "fixtures", "issue_478_em_top_reference.png")
WRITE = os.environ.get("MCRF_478_WRITE_REFERENCE") == "1"
TMPDIR = tempfile.mkdtemp(prefix="mcrf478ref_")
REGION = (0, 0, 480, 260)

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


def em_top():
    # Before #478 there is no TextBaseline; the old rule is the only one.
    if hasattr(mcrfpy, "TextBaseline"):
        return {"baseline": mcrfpy.TextBaseline.EM_TOP}
    return {}


def build_scene():
    tall = mcrfpy.Font(_synthetic_font.write(os.path.join(TMPDIR, "tall.ttf"),
        units_per_em=1000, ascender=800, descender=-200, box=(100, 0, 500, 700), advance=600))
    short = mcrfpy.Font(_synthetic_font.write(os.path.join(TMPDIR, "short.ttf"),
        units_per_em=1000, ascender=600, descender=-400, box=(100, 0, 500, 500), advance=600))
    scene = mcrfpy.Scene("issue478ref")
    mcrfpy.current_scene = scene
    bg = mcrfpy.Frame(pos=(0, 0), size=(REGION[2], REGION[3]), fill_color=(0, 0, 40))
    scene.children.append(bg)
    kw = em_top()
    y = 4
    for size in (12, 16, 23, 32):
        scene.children.append(mcrfpy.Caption(text="Hgjy {%d} ░▒█" % size, pos=(4, y),
                                             font_size=size, fill_color=(255, 255, 255), **kw))
        y += size + 6
    scene.children.append(mcrfpy.Caption(text="two\nlines", pos=(240, 4), font_size=18,
                                         fill_color=(255, 255, 0), **kw))
    scene.children.append(mcrfpy.Caption(text="Outlined", pos=(240, 60), font_size=20,
                                         fill_color=(255, 255, 255), outline=2,
                                         outline_color=(255, 0, 0), **kw))
    scene.children.append(mcrfpy.Caption(text="XX", pos=(240, 110), font=tall, font_size=20,
                                         fill_color=(0, 255, 0), **kw))
    scene.children.append(mcrfpy.Caption(text="XX", pos=(300, 110), font=short, font_size=20,
                                         fill_color=(0, 255, 255), **kw))
    inner = mcrfpy.Frame(pos=(240, 150), size=(200, 80), fill_color=(40, 0, 0))
    inner.children.append(mcrfpy.Caption(text="child @ (7, 9)", pos=(7, 9), font_size=16,
                                         fill_color=(255, 128, 0), **kw))
    scene.children.append(inner)
    return scene


build_scene()
path = os.path.join(TMPDIR, "em_top.png")
automation.screenshot(path)
img = _png.read_png(path)

if WRITE:
    import shutil
    shutil.copyfile(path, REFERENCE)
    print("wrote", os.path.normpath(REFERENCE))
    sys.exit(0)

ref = _png.read_png(REFERENCE)
print("EM_TOP draws exactly the pre-#478 pixels")
check(ref[0] >= REGION[2] and ref[1] >= REGION[3], "reference covers the region")
same = _png.rows(img, REGION) == _png.rows(ref, REGION)
if not same:
    w, h, ch, px = img
    rw, rh, rch, rpx = ref
    diff = [(x, y) for y in range(REGION[1], REGION[3]) for x in range(REGION[0], REGION[2])
            if px[(y * w + x) * ch:(y * w + x) * ch + 3] != rpx[(y * rw + x) * rch:(y * rw + x) * rch + 3]]
    print("  %d pixels differ, bbox %s" % (len(diff), _png.bbox(set(diff))))
check(same, "region %s is pixel-identical to the reference" % (REGION,))

print("=" * 50)
if failures:
    print("FAIL (%d)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
