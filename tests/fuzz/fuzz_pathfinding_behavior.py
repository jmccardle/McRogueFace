"""fuzz_pathfinding_behavior - stub. Wave 2 agent W9 will implement.

Target: grid.get_dijkstra_map() with random roots and collide sets,
.path_from/.step_from/.to_heightmap(), grid.step() with random turn_order,
entity step/default_behavior/target_label mutation.

Contract: define fuzz_one_input(data: bytes) -> None.
"""

import mcrfpy

from fuzz_common import ByteStream, EXPECTED_EXCEPTIONS


def fuzz_one_input(data):
    stream = ByteStream(data)
    try:
        mcrfpy.Grid(grid_size=(6, 6))
    except EXPECTED_EXCEPTIONS:
        pass
