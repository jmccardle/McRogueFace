"""Regression test for #332 - GridData SoA plane storage.

Cell walkable/transparent moved from an array-of-UIGridPoint (24 B/cell, and
chunked into non-contiguous 64x64 blocks above size 64) to two dense row-major
uint8 planes (2 B/cell, contiguous at ANY size). This verifies behavior is
preserved -- especially on LARGE grids that formerly used chunked storage, at
and across the old 64-cell chunk boundary -- and that the coordinate-keyed
GridPoint wrapper round-trips writes both directions.

Direct-execution style.
"""
import mcrfpy
import sys
import os
import gc


def rss_bytes():
    with open("/proc/self/statm") as f:
        return int(f.read().split()[1]) * os.sysconf("SC_PAGE_SIZE")


def main():
    # Large grid: formerly chunked (>64 in both dims). Exercise cells at and
    # across the old 64-cell chunk boundary -- the storage seam SoA removed.
    W, H = 200, 160
    g = mcrfpy.Grid(grid_size=(W, H))
    cells = [(0, 0), (63, 63), (64, 64), (64, 0), (0, 64), (65, 65),
             (127, 127), (128, 120), (W - 1, H - 1)]

    for (x, y) in cells:
        g.at(x, y).walkable = True
        g.at(x, y).transparent = True

    for (x, y) in cells:
        gp = g.at(x, y)
        assert gp.walkable is True, f"walkable round-trip failed at {(x, y)}"
        assert gp.transparent is True, f"transparent round-trip failed at {(x, y)}"

    # A cell never set keeps the default (False, False)
    assert g.at(100, 100).walkable is False, "default walkable should be False"
    assert g.at(100, 100).transparent is False, "default transparent should be False"

    # Toggling back works (write False)
    g.at(64, 64).walkable = False
    assert g.at(64, 64).walkable is False, "toggle-off failed"

    # Wrapper's coordinate-derived properties still work
    assert g.at(5, 7).grid_pos == (5, 7), "grid_pos"
    assert isinstance(g.at(5, 7).entities, list), "entities list"

    # Subscript form reaches the same storage
    g[10, 11].walkable = True
    assert g.at(10, 11).walkable is True, "subscript vs at() disagree"

    print("  large-grid boundary round-trip OK")

    # Memory: per-cell footprint far below the old 24 B array-of-struct cell.
    # Total includes the TCOD map + spatial hash, so this is a loose gross-regression
    # guard, not the isolated 2 B/cell plane cost.
    gc.collect()
    base = rss_bytes()
    N, gs = 40, 100
    grids = [mcrfpy.Grid(grid_size=(gs, gs)) for _ in range(N)]
    after = rss_bytes()
    per_cell = (after - base) / (N * gs * gs)
    print(f"  ~{per_cell:.1f} bytes/cell total ({N} grids of {gs}x{gs}, incl. TCOD map)")
    assert per_cell < 40, f"per-cell {per_cell:.1f} B too high -- storage regression?"
    assert len(grids) == N

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
