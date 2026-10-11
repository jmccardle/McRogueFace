"""Regression test for #456: GridView view properties never appeared inside Frame(cache_subtree=True).

The view's own render early-out compares fill_color/zoom/center/rotation with what it
drew last, so a grid with no caching parent repainted. A caching ancestor only redraws
when told its subtree changed (markDirty), and two writers never told it:
- the fill_color setter (grid.fill_color = ...);
- UIGridView::setProperty, which animate() uses for zoom, center, center_x/center_y,
  camera_rotation and fill_color.

Every change below must change the screenshot under a caching Frame, and (as a
control) without one. Animated values are applied by stepping the animation to its end.
"""
import mcrfpy
from mcrfpy import automation
import sys, os, tempfile

TMPDIR = tempfile.mkdtemp(prefix="mcrf_viewprops_")
_n = 0
failures = []


def shot():
    global _n
    p = os.path.join(TMPDIR, "s%d.png" % _n)
    _n += 1
    automation.screenshot(p)
    with open(p, "rb") as f:
        return f.read()


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)


def finish(g, prop, value):
    g.animate(prop, value, 0.1)
    for _ in range(5):
        mcrfpy.step(0.05)


CHANGES = [
    ("fill_color setter", lambda g: setattr(g, "fill_color", mcrfpy.Color(0, 0, 255))),
    ("animate fill_color", lambda g: finish(g, "fill_color", mcrfpy.Color(0, 0, 255))),
    ("animate zoom", lambda g: finish(g, "zoom", 2.0)),
    ("animate center", lambda g: finish(g, "center", (40.0, 40.0))),
    ("animate center_x", lambda g: finish(g, "center_x", 40.0)),
    ("animate camera_rotation", lambda g: finish(g, "camera_rotation", 45.0)),
]


def build(cached):
    scene = mcrfpy.Scene("viewprops_%d" % _n)
    mcrfpy.current_scene = scene
    frame = mcrfpy.Frame(pos=(0, 0), size=(300, 300), cache_subtree=cached)
    g = mcrfpy.Grid(grid_size=(8, 8), pos=(10, 10), size=(128, 128), texture=tex)
    g.fill_color = mcrfpy.Color(255, 0, 0)
    tiles = g.layers[0]
    for y in range(8):
        for x in range(8):
            # A checkerboard of tiles and holes, so camera moves show and the fill shows through.
            tiles.set((x, y), 5 if (x + y) % 2 else -1)
    frame.children.append(g)
    scene.children.append(frame)
    return g


for cached in (False, True):
    where = "under a caching Frame" if cached else "with no caching parent"
    for name, change in CHANGES:
        g = build(cached)
        before = shot()
        change(g)
        after = shot()
        check(before != after, "%s repaints %s" % (name, where))

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
