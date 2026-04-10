"""fuzz_grid_entity - stub. Wave 2 agent W4 will implement.

Target bugs: #258-#263 (gridstate overflow on entity transfer between
differently-sized grids), #273 (entity.die during iteration), #274
(set_grid spatial hash). See /home/john/.claude/plans/abundant-gliding-hummingbird.md.

Contract: define fuzz_one_input(data: bytes) -> None. The C++ harness
(tests/fuzz/fuzz_common.cpp) calls this for every libFuzzer iteration.
Use ByteStream to consume bytes. Wrap work in try/except EXPECTED_EXCEPTIONS.
"""

import mcrfpy

from fuzz_common import ByteStream, EXPECTED_EXCEPTIONS


def fuzz_one_input(data):
    stream = ByteStream(data)
    try:
        # Minimal smoke: create one grid so the harness verifies end to end.
        mcrfpy.Grid(grid_size=(4, 4))
    except EXPECTED_EXCEPTIONS:
        pass
