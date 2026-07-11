"""Regression test for #335 - ColorLayer/TileLayer numpy buffer views via edit().

Per the #328 bulk-edit convention, writable zero-copy views of layer data are
exposed only through `with layer.edit() as view:`. ColorLayer yields an
(h, w, 4) uint8 view; TileLayer yields an (h, w) int32 view (-1 = no tile).
Writes alias the layer storage (no copy); on __exit__ the whole layer is
conservatively invalidated so the edit re-renders.

Verifies buffer shape/format, zero-copy writeback both directions, the -1
sentinel, optional numpy aliasing, and that exiting the context actually
re-renders (screenshot diff -- the edit->markDirty->#351 early-out loop).
"""
import mcrfpy
from mcrfpy import automation
import sys
import os
import tempfile

TMPDIR = tempfile.mkdtemp(prefix="mcrf335_")
_n = 0


def shot():
    global _n
    p = os.path.join(TMPDIR, "s%d.png" % _n)
    _n += 1
    automation.screenshot(p)
    with open(p, "rb") as f:
        return f.read()


def main():
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    scene = mcrfpy.Scene("t335")
    scene.activate()

    cl = mcrfpy.ColorLayer(name="fog", z_index=1)
    tl = mcrfpy.TileLayer(name="terrain", z_index=-2, texture=tex)
    grid = mcrfpy.Grid(grid_size=(8, 6), pos=(10, 10), size=(256, 192),
                       texture=tex, layers=[tl, cl])
    scene.children.append(grid)

    # --- ColorLayer: (h, w, 4) uint8, writable, zero-copy both directions ---
    with cl.edit() as view:
        assert view.shape == (6, 8, 4), f"color shape {view.shape}"
        assert view.format == 'B', f"color format {view.format}"
        assert view.readonly is False
        view[1, 2, 0] = 200   # y=1, x=2, red channel
    assert cl.at(2, 1).r == 200, "color view -> layer writeback failed"

    # layer -> view direction
    cl.set((3, 4), mcrfpy.Color(7, 8, 9, 255))  # x=3, y=4
    with cl.edit() as view:
        assert view[4, 3, 0] == 7 and view[4, 3, 2] == 9, "layer -> view read failed"

    # --- TileLayer: (h, w) int32, -1 sentinel ---
    with tl.edit() as view:
        assert view.shape == (6, 8), f"tile shape {view.shape}"
        assert view.format == 'i', f"tile format {view.format}"
        view[5, 6] = 42   # y=5, x=6
        view[0, 0] = -1
    assert tl.at(6, 5) == 42, "tile view -> layer writeback failed"
    assert tl.at(0, 0) == -1, "tile -1 sentinel round-trip failed"

    # --- Optional numpy zero-copy aliasing ---
    try:
        import numpy as np
        with tl.edit() as view:
            a = np.asarray(view)
            assert a.shape == (6, 8) and a.dtype == np.int32, (a.shape, a.dtype)
            a[3, 3] = 17
        assert tl.at(3, 3) == 17, "numpy write did not alias TileLayer"
        print("  numpy zero-copy verified")
    except ImportError:
        print("  numpy not bundled; memoryview path verified")

    # --- __exit__ invalidation actually re-renders (edit -> markDirty -> #351) ---
    before = shot()
    with cl.edit() as view:
        # paint a visible opaque block through the view
        for y in range(6):
            for x in range(8):
                view[y, x, 0] = 255
                view[y, x, 3] = 255
    after = shot()
    assert before != after, "layer edit did not re-render on __exit__"

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
