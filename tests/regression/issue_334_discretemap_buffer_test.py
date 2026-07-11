"""Regression test for #334 - DiscreteMap buffer protocol (zero-copy numpy view).

DiscreteMap now implements the C buffer protocol (tp_as_buffer / bf_getbuffer),
exposing its dense uint8 storage as a 2-D (height, width) C-contiguous writable
view. `memoryview(dmap)` and `np.asarray(dmap)` share memory with the map -- no
copy -- so edits through either side are visible on the other.

Direct-execution style (no game loop needed).
"""
import mcrfpy
import sys


def main():
    # width=5, height=3 -> buffer shape is (h, w) = (3, 5)
    dm = mcrfpy.DiscreteMap((5, 3), fill=0)
    dm[1, 2] = 7  # dmap indexing is [x, y]

    mv = memoryview(dm)
    assert mv.shape == (3, 5), f"shape {mv.shape}, expected (3, 5)"
    assert mv.format == 'B', f"format {mv.format}, expected 'B' (uint8)"
    assert mv.ndim == 2, f"ndim {mv.ndim}"
    assert mv.readonly is False, "buffer should be writable"
    assert mv.strides == (5, 1), f"strides {mv.strides}, expected row-major (5, 1)"

    # Row-major mapping: dmap[x, y] == buffer[y, x]
    assert mv[2, 1] == 7, f"buffer[y=2,x=1] {mv[2, 1]}, expected 7"

    # Zero-copy writeback: buffer -> dmap
    mv[0, 4] = 9  # y=0, x=4
    assert dm[4, 0] == 9, f"dmap[4,0] {dm[4, 0]}, expected 9 (write via buffer)"

    # ... and dmap -> buffer
    dm[3, 1] = 4  # x=3, y=1
    assert mv[1, 3] == 4, f"buffer[y=1,x=3] {mv[1, 3]}, expected 4 (write via dmap)"

    # Optional numpy path (only if bundled); asserts true zero-copy sharing.
    try:
        import numpy as np
        a = np.asarray(dm)
        assert a.shape == (3, 5) and a.dtype == np.uint8, (a.shape, a.dtype)
        assert a[2, 1] == 7
        a[2, 2] = 11  # y=2, x=2 -- must alias
        assert dm[2, 2] == 11, "numpy write did not alias DiscreteMap (not zero-copy)"
        print("  numpy zero-copy verified")
    except ImportError:
        print("  numpy not bundled; memoryview path verified")

    # Buffer over a live entity perspective_map (the #294 use case)
    scene = mcrfpy.Scene("t334")
    tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
    grid = mcrfpy.Grid(grid_size=(8, 6), texture=tex)
    scene.children.append(grid)
    ent = mcrfpy.Entity((2, 2), grid=grid)
    pm = ent.perspective_map  # DiscreteMap sized to grid
    if pm is not None:
        pmv = memoryview(pm)
        assert pmv.shape == (6, 8), f"perspective buffer shape {pmv.shape}, expected (6, 8)"

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
