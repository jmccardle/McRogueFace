"""Multi-root Dijkstra distance equals min of per-root distances.

Also covers the DiscreteMap-mask root-input form introduced in #315.
"""
import mcrfpy
import sys


def make_grid(w, h):
    g = mcrfpy.Grid(grid_size=(w, h))
    for y in range(h):
        for x in range(w):
            c = g.at(x, y)
            c.walkable = True
            c.transparent = True
    return g


def approx(a, b, tol=0.01):
    return abs(a - b) < tol


def main():
    g = make_grid(20, 20)
    roots = [(0, 0), (19, 19), (0, 19)]

    multi = g.get_dijkstra_map(roots=roots)
    singles = [g.get_dijkstra_map(r) for r in roots]

    # Pick sample cells spread across the grid.
    samples = [(5, 5), (10, 10), (15, 5), (2, 18), (18, 2), (9, 15)]
    for p in samples:
        expected = min(s.distance(p) for s in singles)
        got = multi.distance(p)
        assert approx(got, expected), (
            f"multi-root distance at {p} was {got}, expected {expected}")

    # Distance at each root is 0.
    for r in roots:
        assert multi.distance(r) == 0.0, f"root {r} distance should be 0"

    # Single-root via roots= also works.
    d_single = g.get_dijkstra_map(roots=[(5, 5)])
    d_ref = g.get_dijkstra_map((5, 5))
    for p in samples:
        assert approx(d_single.distance(p), d_ref.distance(p)), \
            f"single-element roots list diverges at {p}"

    # DiscreteMap mask form: mark four corners, compare against explicit roots.
    dmap = mcrfpy.DiscreteMap((20, 20))
    corners = [(0, 0), (19, 0), (0, 19), (19, 19)]
    for x, y in corners:
        dmap.set(x, y, 1)

    d_mask = g.get_dijkstra_map(roots=dmap)
    d_corners = g.get_dijkstra_map(roots=corners)
    for p in samples:
        assert approx(d_mask.distance(p), d_corners.distance(p)), \
            f"mask-root diverges from explicit corners at {p}"

    # Empty mask errors out rather than silently returning all-infinity.
    empty_mask = mcrfpy.DiscreteMap((20, 20))
    try:
        g.get_dijkstra_map(roots=empty_mask)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError on empty DiscreteMap mask")

    # Passing both root and roots raises.
    try:
        g.get_dijkstra_map(root=(0, 0), roots=[(1, 1)])
    except TypeError:
        pass
    else:
        raise AssertionError("expected TypeError when both root and roots supplied")

    print("PASS")


if __name__ == "__main__":
    main()
    sys.exit(0)
