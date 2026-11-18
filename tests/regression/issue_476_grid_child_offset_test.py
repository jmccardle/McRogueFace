"""Regression test for #476 - grid children were drawn at twice their position.

A grid child's `pos` is in grid-world pixels (docs/grid-coordinate-spaces.md), so it
must draw at grid.pos + (pos - camera_top_left) * zoom. UIGridView::render passed the
child its final pixel position as the render offset, and every drawable adds its own
position to the offset, so the child drew at (pos - top_left) * zoom + pos.

Ground truth is the screenshot, decoded here.
"""
import os
import sys
import tempfile

import mcrfpy
from mcrfpy import automation

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # --exec does not
from _png import read_png  # noqa: E402

TMPDIR = tempfile.mkdtemp(prefix="mcrf476_")
failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


        failures.append(msg)


def shot(name):
    path = os.path.join(TMPDIR, name + ".png")
    mcrfpy.step(0)  # the screenshot shows the last complete frame; draw this one (#529)
    automation.screenshot(path)
    return read_png(path, *CROP)


def bbox(img, rgb, region):
    """Bounding box (x0, y0, x1, y1) of pixels exactly `rgb` inside region, or None."""
    w, h, ch, px = img
    x0, y0, x1, y1 = region
    assert x1 <= w and y1 <= h, "region %s is outside the decoded crop %dx%d" % (region, w, h)
    xs, ys = [], []
    for y in range(y0, y1):
        for x in range(x0, x1):
            i = (y * w + x) * ch
            if tuple(px[i:i + 3]) == rgb:
                xs.append(x)
                ys.append(y)
    if not xs:
        return None
    return (min(xs), min(ys), max(xs) + 1, max(ys) + 1)


MAGENTA = (255, 0, 255)
GX, GY, GW, GH = 100, 100, 320, 240
GRID_REGION = (GX, GY, GX + GW, GY + GH)
# bbox() only searches GRID_REGION (x < 420, y < 340); decoding just this corner of the 1024x768
# screenshot (exact, see _png.read_png) skips the rest.
CROP = (448, 352)
CHILD = (96, 64)          # grid-world pixels
CHILD_SIZE = (10, 10)


def expected(center, zoom):
    # UIGridView truncates the camera's top-left to whole sprite pixels.
    tl_x = int(center[0] - GW / 2.0 / zoom)
    tl_y = int(center[1] - GH / 2.0 / zoom)
    return (round(GX + (CHILD[0] - tl_x) * zoom), round(GY + (CHILD[1] - tl_y) * zoom))


def build(center, zoom):
    scene = mcrfpy.Scene("s476")
    scene.activate()
    grid = mcrfpy.Grid(grid_size=(40, 30), pos=(GX, GY), size=(GW, GH),
                       texture=mcrfpy.default_texture)
    grid.fill_color = mcrfpy.Color(0, 0, 0)
    for layer in list(grid.layers):
        grid.remove_layer(layer)
    grid.zoom = zoom
    grid.center = center
    scene.children.append(grid)
    return scene, grid


CASES = [
    ("default camera, zoom 1", (160, 120), 1.0),
    ("panned camera, zoom 1", (200, 150), 1.0),
    ("zoom 2", (160, 120), 2.0),
    ("zoom 0.5", (320, 240), 0.5),
]

print("1. a Frame child draws at grid.pos + (pos - camera_top_left) * zoom")
for label, center, zoom in CASES:
    scene, grid = build(center, zoom)
    f = mcrfpy.Frame(pos=CHILD, size=CHILD_SIZE, fill_color=mcrfpy.Color(*MAGENTA))
    f.outline = 0
    grid.children.append(f)
    box = bbox(shot("frame_%s" % zoom), MAGENTA, GRID_REGION)
    ex = expected(center, zoom)
    check(box is not None and box[:2] == ex,
          "%s: frame top-left %s, expected %s" % (label, box and box[:2], ex))

print("2. a Caption child lands at its position too (all drawables share the fix)")
for label, center, zoom in CASES[:3]:
    scene, grid = build(center, zoom)
    c = mcrfpy.Caption(text="#", pos=CHILD, font_size=16,
                       fill_color=mcrfpy.Color(*MAGENTA))
    c.outline = 0
    grid.children.append(c)
    box = bbox(shot("caption_%s" % zoom), MAGENTA, GRID_REGION)
    ex = expected(center, zoom)
    # Glyph ink starts a few pixels inside the caption's box (bearing, line gap).
    ok = box is not None and 0 <= box[0] - ex[0] <= 8 and 0 <= box[1] - ex[1] <= 16
    check(ok, "%s: caption ink at %s, box origin expected %s" % (label, box and box[:2], ex))

print("=" * 50)
if failures:
    print("FAIL (%d)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
