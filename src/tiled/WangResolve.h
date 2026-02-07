#pragma once
#include "TiledTypes.h"
#include <vector>
#include <cstdint>

namespace mcrf {
namespace tiled {

// Resolve terrain data (from DiscreteMap) to tile indices using a WangSet.
// Returns a vector of tile IDs (one per cell). -1 means no matching tile found.
// terrain_data: row-major uint8 array, width*height elements
std::vector<int> resolveWangTerrain(
    const uint8_t* terrain_data, int width, int height,
    const WangSet& wang_set);

} // namespace tiled
} // namespace mcrf
