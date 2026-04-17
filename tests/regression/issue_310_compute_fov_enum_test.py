"""Regression test for issue #310.

Grid.compute_fov's algorithm argument was passed directly as an int into
GridData::computeFOV, where it was cast to TCOD_fov_algorithm_t. Values
outside the enum range caused UBSan to report an invalid enum load. Fuzz
target fuzz_fov surfaced this with algorithm=-49.

The fix routes the argument through PyFOV::from_arg, which accepts FOV
enum members, ints in [0, NB_FOV_ALGORITHMS), or None (defaults to BASIC),
and raises ValueError for out-of-range ints.
"""

import mcrfpy
import sys


def main():
    grid = mcrfpy.Grid(grid_size=(10, 10))

    # Valid paths: enum, int, None, omitted
    grid.compute_fov((5, 5), radius=3, algorithm=mcrfpy.FOV.BASIC)
    grid.compute_fov((5, 5), radius=3, algorithm=0)       # FOV_BASIC
    grid.compute_fov((5, 5), radius=3, algorithm=None)    # default
    grid.compute_fov((5, 5), radius=3)                    # default, no arg

    # Out-of-range negative int (this was the UBSan trigger)
    try:
        grid.compute_fov((5, 5), radius=3, algorithm=-49)
    except ValueError:
        pass
    else:
        print("FAIL: algorithm=-49 should raise ValueError")
        sys.exit(1)

    # Out-of-range positive int (above NB_FOV_ALGORITHMS sentinel)
    try:
        grid.compute_fov((5, 5), radius=3, algorithm=9999)
    except ValueError:
        pass
    else:
        print("FAIL: algorithm=9999 should raise ValueError")
        sys.exit(1)

    # Wrong type still rejected
    try:
        grid.compute_fov((5, 5), radius=3, algorithm="basic")
    except (TypeError, ValueError):
        pass
    else:
        print("FAIL: algorithm='basic' should raise TypeError")
        sys.exit(1)

    # Boundary int -1 should fail (negative)
    try:
        grid.compute_fov((5, 5), radius=3, algorithm=-1)
    except ValueError:
        pass
    else:
        print("FAIL: algorithm=-1 should raise ValueError")
        sys.exit(1)

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
