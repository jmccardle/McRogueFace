#!/usr/bin/env python3
"""Regression test for #355 - cell hit testing under camera_rotation.

UIGridView::localToGridWorld() rasterizes-then-rotates in render(), but the hit
test used to skip the rotation entirely (and used the widget size instead of the
rotated AABB). With camera_rotation != 0 every cell handed to on_cell_click /
on_cell_enter / on_cell_exit / hovered_cell was the cell that WOULD be under the
mouse if the camera were unrotated -- plausible-looking, silently wrong data.
Before #355 all grid input was dead, so this ships as new behavior; it has to be
right.

GROUND TRUTH IS THE RENDERED IMAGE, not a re-derivation of the camera math: one
cell is painted pure red by a ColorLayer, the frame is screenshotted, the red
pixels are located by decoding the PNG, and the click is aimed at their centroid.
The cell reported back by on_cell_click must be the red cell.
"""
import sys
import os
import tempfile

import mcrfpy
from mcrfpy import automation

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # --exec does not
from _png import read_png  # noqa: E402

CELL = 16
# The grid sits at (100, 100), 80x80 (its rotated AABB is at most ~113 px across, centred on (140, 140)),
# and nothing else is drawn: the red marker is within x, y < 200. Decoding only this corner of the
# 1024x768 screenshot (exact, see _png.read_png) skips the rest.
CROP = (200, 200)
TMPDIR = tempfile.mkdtemp(prefix="mcrf355rot_")
FAILURES = []


def check(cond, msg):
    if not cond:
        print("FAIL: %s" % msg, file=sys.stderr)
        FAILURES.append(msg)


def red_centroid(path):
    """Centroid of pure-red pixels in the screenshot, or None."""
    w, h, ch, px = read_png(path, *CROP)
    sx = sy = n = 0
    for y in range(h):
        row = y * w * ch
        for x in range(w):
            i = row + x * ch
            if px[i] > 200 and px[i + 1] < 60 and px[i + 2] < 60:
                sx += x
                sy += y
                n += 1
    if n == 0:
        return None
    return (sx / n, sy / n, n)


def build_scene(rotation):
    scene = mcrfpy.Scene("rot%d" % int(rotation))
    scene.activate()
    # 5x5 cells of 16px = 80x80 of content; widget is 80x80 and the camera is
    # centered, so content exactly fills the widget at zoom 1.
    grid = mcrfpy.Grid(grid_size=(5, 5), texture=mcrfpy.default_texture, pos=(100, 100), size=(80, 80))
    scene.children.append(grid)
    grid.center = (40, 40)
    grid.zoom = 1.0

    layer = mcrfpy.ColorLayer(z_index=-1, grid_size=(5, 5))
    grid.add_layer(layer)
    for x in range(5):
        for y in range(5):
            layer.set((x, y), mcrfpy.Color(20, 20, 20))
    layer.set(RED_CELL, mcrfpy.Color(255, 0, 0))

    grid.camera_rotation = rotation
    return scene, grid


RED_CELL = (0, 1)  # off-center and off-diagonal: distinguishable under any rotation


def run_case(rotation):
    scene, grid = build_scene(rotation)

    clicks = []
    grid.on_cell_click = lambda pos, button, action: clicks.append((int(pos.x), int(pos.y)))

    path = os.path.join(TMPDIR, "rot%d.png" % int(rotation))
    mcrfpy.step(0)  # the screenshot shows the last complete frame; draw this one (#529)
    automation.screenshot(path)  # headless: step() above makes the shot draw the current scene (#529)

    c = red_centroid(path)
    check(c is not None, "[rot=%s] red marker cell was not rendered at all" % rotation)
    if c is None:
        return
    cx, cy, n = c
    check(n > 100, "[rot=%s] red marker too small (%d px) to aim at" % (rotation, n))

    automation.click((int(round(cx)), int(round(cy))))
    check(len(clicks) >= 1,
          "[rot=%s] clicking the visible red cell fired no on_cell_click" % rotation)
    if clicks:
        check(clicks[0] == RED_CELL,
              "[rot=%s] clicked the pixel where cell %s is DRAWN (%.1f,%.1f); "
              "on_cell_click reported %s" % (rotation, RED_CELL, cx, cy, clicks[0]))

    automation.moveTo((int(round(cx)), int(round(cy))))
    check(grid.hovered_cell is not None and tuple(grid.hovered_cell) == RED_CELL,
          "[rot=%s] hovered_cell over the drawn red cell should be %s, got %s"
          % (rotation, RED_CELL, grid.hovered_cell))


def main():
    for rotation in (0.0, 90.0, 180.0, 270.0, 45.0):
        run_case(rotation)

    if FAILURES:
        print("\n%d FAILURE(S)" % len(FAILURES), file=sys.stderr)
        sys.exit(1)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print("\nTEST CRASHED: %s" % e, file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
