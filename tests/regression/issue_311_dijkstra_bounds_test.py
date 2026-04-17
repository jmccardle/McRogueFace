"""Regression test for issue #311.

DijkstraMap.distance, .path_from, and .step_from previously forwarded
out-of-bounds coordinates directly to TCOD's dijkstra routines, which
call abort() on assertion failure. The fuzz target fuzz_pathfinding_behavior
surfaced a specific crash input.

Fixed by bounds-checking at the Python binding layer: out-of-range coords
now raise IndexError with a message including the map dimensions.
"""

import mcrfpy
import sys


def _make_dmap(w, h):
    grid = mcrfpy.Grid(grid_size=(w, h))
    return grid.get_dijkstra_map((w // 2, h // 2))


def _expect_index_error(fn, label):
    try:
        fn()
    except IndexError:
        return
    except Exception as exc:
        print(f"FAIL: {label} raised {type(exc).__name__}: {exc} (expected IndexError)")
        sys.exit(1)
    print(f"FAIL: {label} did not raise")
    sys.exit(1)


def main():
    dmap = _make_dmap(10, 8)

    # Valid in-bounds coordinates should work
    _ = dmap.distance((0, 0))
    _ = dmap.distance((9, 7))  # corner
    _ = dmap.distance((5, 4))  # middle

    # Each out-of-range call must raise IndexError
    _expect_index_error(lambda: dmap.distance((-1, 0)), "distance neg x")
    _expect_index_error(lambda: dmap.distance((0, -1)), "distance neg y")
    _expect_index_error(lambda: dmap.distance((10, 0)), "distance x>=width")
    _expect_index_error(lambda: dmap.distance((0, 8)), "distance y>=height")
    _expect_index_error(lambda: dmap.distance((9999, 9999)), "distance huge")

    _expect_index_error(lambda: dmap.path_from((-5, -5)), "path_from negative")
    _expect_index_error(lambda: dmap.path_from((100, 100)), "path_from too large")

    _expect_index_error(lambda: dmap.step_from((-1, -1)), "step_from negative")
    _expect_index_error(lambda: dmap.step_from((10, 8)), "step_from on boundary")

    # After a bounds violation, the dmap must still be usable (no abort, no
    # torn-down TCOD state)
    _ = dmap.distance((1, 1))
    _ = dmap.path_from((2, 2))
    _ = dmap.step_from((3, 3))

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
