"""Grid.find_path heuristic/weight kwargs produce valid paths across each built-in."""
import mcrfpy
import sys


def make_open_grid(w, h):
    g = mcrfpy.Grid(grid_size=(w, h))
    for y in range(h):
        for x in range(w):
            c = g.at(x, y)
            c.walkable = True
            c.transparent = True
    return g


def main():
    g = make_open_grid(30, 30)

    # On an obstacle-free grid every admissible heuristic yields an optimal-length path.
    # libtcod returns steps (excluding origin), so a diagonal-permitting move from (0,0)
    # to (20,20) is 20 steps.
    for h in (mcrfpy.Heuristic.EUCLIDEAN,
              mcrfpy.Heuristic.MANHATTAN,
              mcrfpy.Heuristic.CHEBYSHEV,
              mcrfpy.Heuristic.DIAGONAL,
              mcrfpy.Heuristic.ZERO):
        p = g.find_path((0, 0), (20, 20), heuristic=h)
        assert p is not None, f"no path for {h}"
        steps = list(p)
        assert len(steps) == 20, f"heuristic {h} gave {len(steps)} steps, expected 20"
        # Last step must be the goal.
        assert (int(steps[-1].x), int(steps[-1].y)) == (20, 20), \
            f"heuristic {h} did not end at goal"

    # Weighted A* with weight>=1 must still find a path (not necessarily optimal).
    for w in (1.0, 1.5, 2.0):
        p = g.find_path((0, 0), (20, 20), heuristic=mcrfpy.Heuristic.EUCLIDEAN, weight=w)
        assert p is not None, f"no path for weight={w}"
        steps = list(p)
        assert len(steps) >= 20, f"weight={w} gave impossibly short path"

    # With an obstacle, the path still reaches the goal.
    g2 = make_open_grid(30, 30)
    for y in range(5, 25):
        g2.at(15, y).walkable = False

    p = g2.find_path((0, 0), (29, 0), heuristic=mcrfpy.Heuristic.MANHATTAN)
    assert p is not None
    steps = list(p)
    assert (int(steps[-1].x), int(steps[-1].y)) == (29, 0)
    # No step may land on a blocked cell.
    for s in steps:
        assert not (int(s.x) == 15 and 5 <= int(s.y) < 25), \
            f"path stepped through wall at {s}"

    print("PASS")


if __name__ == "__main__":
    main()
    sys.exit(0)
