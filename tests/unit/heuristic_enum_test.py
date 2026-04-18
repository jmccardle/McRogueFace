"""mcrfpy.Heuristic enum exists with expected members and accepts several arg forms."""
import mcrfpy
import sys


def main():
    assert hasattr(mcrfpy, "Heuristic"), "mcrfpy.Heuristic missing"
    H = mcrfpy.Heuristic

    expected = {"EUCLIDEAN": 0, "MANHATTAN": 1, "CHEBYSHEV": 2, "DIAGONAL": 3, "ZERO": 4}
    for name, value in expected.items():
        assert hasattr(H, name), f"Heuristic.{name} missing"
        assert int(getattr(H, name)) == value, f"Heuristic.{name} != {value}"

    members = list(H)
    assert len(members) == 5, f"expected 5 members, got {len(members)}"

    # find_path accepts enum, int, string
    g = mcrfpy.Grid(grid_size=(20, 20))
    for y in range(20):
        for x in range(20):
            c = g.at(x, y)
            c.walkable = True
            c.transparent = True

    for arg in (H.MANHATTAN, 1, "MANHATTAN"):
        p = g.find_path((0, 0), (10, 10), heuristic=arg)
        assert p is not None, f"find_path returned None for heuristic={arg!r}"
        steps = list(p)
        assert len(steps) > 0, f"empty path for heuristic={arg!r}"

    # Invalid string raises
    try:
        g.find_path((0, 0), (10, 10), heuristic="NOT_A_HEURISTIC")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for bad heuristic string")

    # Invalid int raises
    try:
        g.find_path((0, 0), (10, 10), heuristic=99)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for out-of-range heuristic int")

    # Non-positive weight raises
    try:
        g.find_path((0, 0), (10, 10), weight=0.0)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for non-positive weight")

    print("PASS")


if __name__ == "__main__":
    main()
    sys.exit(0)
