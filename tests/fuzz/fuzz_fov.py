"""fuzz_fov - stub. Wave 2 agent W8 will implement.

Target: grid.compute_fov() with random origin/radius/algorithm, toggling
grid.at(x,y).transparent mid-run, grid.is_in_fov() queries on invalid coords.

Contract: define fuzz_one_input(data: bytes) -> None.
"""

import mcrfpy

from fuzz_common import ByteStream, EXPECTED_EXCEPTIONS


def fuzz_one_input(data):
    stream = ByteStream(data)
    try:
        g = mcrfpy.Grid(grid_size=(8, 8))
        g.compute_fov((0, 0), radius=3)
    except EXPECTED_EXCEPTIONS:
        pass
