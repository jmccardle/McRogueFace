"""Regression test for #351 - UIGridView clean-state render early-out.

UIGridView::render() now re-blits its cached RenderTexture instead of clearing
and redrawing when nothing that affects the raster changed (camera parameters,
compared directly, plus GridData::content_generation for grid content).

This test guards the DANGEROUS direction: a *false* early-out would display a
STALE frame. It screenshots before/after each kind of mutation and asserts the
rendered pixels actually changed -- proving every mutation still invalidates the
cached raster. It also asserts an idle (no-mutation) pair is byte-identical, so
the skip path itself does not corrupt output.

Headless screenshots are synchronous (#153): screenshot() renders-then-captures,
so all mutations + checks run inline (no Timer dance required).
"""
import mcrfpy
from mcrfpy import automation
import sys, os, tempfile

TMPDIR = tempfile.mkdtemp(prefix="mcrf351_")
_counter = 0
_results = []


def shot():
    """Render a frame to PNG and return its bytes (identical pixels -> identical
    bytes with the deterministic PNG encoder)."""
    global _counter
    path = os.path.join(TMPDIR, "s%d.png" % _counter)
    _counter += 1
    automation.screenshot(path)
    with open(path, "rb") as f:
        return f.read()


def check(label, before, after, expect_change):
    changed = (before != after)
    ok = (changed == expect_change)
    _results.append((label, ok))
    print("  [%s] %s: changed=%s (expected changed=%s)" %
          ("PASS" if ok else "FAIL", label, changed, expect_change))


def run_tests():
    texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)

    scene = mcrfpy.Scene("t351")
    scene.activate()

    grid = mcrfpy.Grid(grid_size=(12, 10), pos=(20, 20), size=(320, 280), texture=texture)

    tl = mcrfpy.TileLayer(name="terrain", z_index=-2, texture=texture)
    cl = mcrfpy.ColorLayer(name="fog", z_index=1)
    grid.add_layer(tl)
    grid.add_layer(cl)
    tl.fill(0)

    e1 = mcrfpy.Entity((3, 3), grid=grid)
    e1.sprite_index = 5

    scene.children.append(grid)

    # Baseline raster (first render: full, records early-out state)
    a = shot()

    # 1. Entity move via draw_pos (set_position -- the latent-bug path #351 fixed)
    e1.draw_pos = (6, 6)
    b = shot(); check("entity set_position", a, b, True)

    # 2. Tile edit (TileLayer.set -> GridLayer::markDirty choke)
    tl.set((2, 2), 40)
    c = shot(); check("tile set", b, c, True)

    # 3. Color edit (ColorLayer.set, opaque -> clearly visible overlay)
    cl.set((3, 3), mcrfpy.Color(255, 0, 0, 255))
    d = shot(); check("color set", c, d, True)

    # 4. Add an entity (default camera -> cell (4,4) is on-screen)
    e2 = mcrfpy.Entity((4, 4), grid=grid)
    e2.sprite_index = 3
    e = shot(); check("entity add", d, e, True)

    # 5. Entity die (removal)
    e2.die()
    f = shot(); check("entity die", e, f, True)

    # 6. Camera pan (view center compare, no content bump)
    cx, cy = grid.center
    grid.center = (cx + 48, cy)
    g = shot(); check("camera pan", f, g, True)

    # 7. Zoom (view compare)
    grid.zoom = 2.0
    h = shot(); check("zoom", g, h, True)

    # 8. Entity move via animation + step (setProperty -> markCompositeDirty)
    e1.animate("draw_x", 9.0, 1.0, mcrfpy.Easing.LINEAR)
    mcrfpy.step(0.5)
    i = shot(); check("entity animate+step", h, i, True)

    # 9. Idle: no mutation -> two frames must be byte-identical (skip path clean)
    j = shot()
    k = shot(); check("idle stable", j, k, False)

    return all(ok for _, ok in _results)


if __name__ == "__main__":
    try:
        ok = run_tests()
        print("PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)
    except Exception as ex:
        import traceback
        traceback.print_exc()
        print("FAIL")
        sys.exit(1)
