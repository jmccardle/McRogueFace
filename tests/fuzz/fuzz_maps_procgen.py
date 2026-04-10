"""fuzz_maps_procgen - stub. Wave 2 agent W7 will implement.

Target: HeightMap and DiscreteMap are the standardized abstract data
containers; fuzz them exhaustively and fuzz the one-directional conversions
(NoiseSource.sample -> HeightMap, BSP.to_heightmap, DiscreteMap.from_heightmap,
DiscreteMap.to_heightmap). Using HM/DM as the interface layer covers every
downstream procgen system without having to fuzz each one.

Contract: define fuzz_one_input(data: bytes) -> None.
"""

import mcrfpy

from fuzz_common import ByteStream, EXPECTED_EXCEPTIONS


def fuzz_one_input(data):
    stream = ByteStream(data)
    try:
        mcrfpy.HeightMap(size=(4, 4))
    except EXPECTED_EXCEPTIONS:
        pass
