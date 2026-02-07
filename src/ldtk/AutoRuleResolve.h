#pragma once
#include "LdtkTypes.h"
#include <vector>
#include <cstdint>

namespace mcrf {
namespace ldtk {

// Resolve auto-rules against IntGrid data.
// Returns a flat array of AutoTileResult (one per cell).
// tile_id = -1 means no rule matched that cell.
std::vector<AutoTileResult> resolveAutoRules(
    const int* intgrid_data, int width, int height,
    const AutoRuleSet& ruleset, uint32_t seed = 0);

} // namespace ldtk
} // namespace mcrf
