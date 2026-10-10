"""Regression test for issue #311.

DijkstraMap.distance, .path_from, and .step_from previously forwarded
out-of-bounds coordinates directly to TCOD's dijkstra routines, which
call abort() on assertion failure. The fuzz target fuzz_pathfinding_behavior
surfaced a specific crash input.

Fixed by bounds-checking at the Python binding layer: out-of-range coords
raised IndexError.

#445 changed the contract, not the guarantee: every position is now ANSWERED
(entities can stand off a full map). A complete field (the window is the whole
grid) says None -- certainly unreachable; a windowed field gives its heuristic
estimate; only a windowed map built with heuristic=None raises IndexError. What
must still hold is the #311 property: no off-map coordinate ever reaches TCOD.
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

    OFF = [(-1, 0), (0, -1), (10, 0), (0, 8), (9999, 9999), (-5, -5), (100, 100),
           (-1, -1), (10, 8), (-2**31, 2**31 - 1)]

    # Complete field: certainly unreachable, never a crash.
    check = lambda cond, label: cond or (print("FAIL: " + label), sys.exit(1))
    check(dmap.complete, "a 10x8 field from its centre is complete")
    for p in OFF:
        check(dmap.distance(p) is None, "distance%r on a complete map is None" % (p,))
        check(dmap.path_from(p) is not None and len(dmap.path_from(p)) == 0,
              "path_from%r on a complete map is an empty path" % (p,))
        check(dmap.step_from(p) is None, "step_from%r is None" % (p,))
        check(dmap.descent_step(p) is None, "descent_step%r is None" % (p,))

    # Windowed field: an estimate off the grid...
    grid = mcrfpy.Grid(grid_size=(40, 40))
    for y in range(40):
        for x in range(40):
            grid.at(x, y).walkable = True
    windowed = grid.get_dijkstra_map((20, 20), radius=3)
    check(not windowed.complete, "a radius-3 field on an open 40x40 grid is not complete")
    for p in OFF:
        d = windowed.distance(p)
        check(isinstance(d, float) and d >= 3.0, "distance%r is an estimate >= radius: %r" % (p, d))
        check(not windowed.is_exact(p), "is_exact%r is False" % (p,))
    # ...and with heuristic=None, IndexError.
    bare = grid.get_dijkstra_map((20, 20), radius=3, heuristic=None)
    for p in OFF:
        _expect_index_error(lambda: bare.distance(p), "distance%r without a heuristic" % (p,))
        _expect_index_error(lambda: bare.step_from(p), "step_from%r without a heuristic" % (p,))

    # After a bounds violation, the dmap must still be usable (no abort, no
    # torn-down TCOD state)
    _ = dmap.distance((1, 1))
    _ = dmap.path_from((2, 2))
    _ = dmap.step_from((3, 3))

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
