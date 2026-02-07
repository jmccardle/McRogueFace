#pragma once
#include <string>
#include <vector>
#include <unordered_map>
#include <memory>
#include <cstdint>
#include <nlohmann/json.hpp>
#include "TiledTypes.h"  // Reuse TileSetData

namespace mcrf {
namespace ldtk {

// ============================================================
// IntGrid terrain value definition
// ============================================================

struct IntGridValue {
    int value;           // 1-indexed (0 = empty)
    std::string name;    // e.g. "grass", "wall"
};

// ============================================================
// Auto-tile rule system
// ============================================================

// Single auto-tile rule
struct AutoRule {
    int uid;
    int size;                     // Pattern dimension: 1, 3, 5, or 7
    std::vector<int> pattern;     // size*size flat array
                                  //   0 = wildcard (any value)
                                  //   +N = must match IntGrid value N
                                  //   -N = must NOT be IntGrid value N
    std::vector<int> tile_ids;    // Alternative tiles (random pick)
    bool flipX = false;
    bool flipY = false;
    float chance = 1.0f;          // 0.0-1.0 probability
    bool breakOnMatch = true;
    int outOfBoundsValue = -1;    // -1 = treat as empty (0)
    bool active = true;
    int pivotX = 0, pivotY = 0;  // Pivot offset within pattern
};

// Group of rules (evaluated together)
struct AutoRuleGroup {
    std::string name;
    bool active = true;
    std::vector<AutoRule> rules;
};

// Resolution result for a single cell
struct AutoTileResult {
    int tile_id;
    int flip;        // 0=none, 1=flipX, 2=flipY, 3=both
};

// Full rule set for one IntGrid/AutoLayer
struct AutoRuleSet {
    std::string name;
    int gridSize = 0;
    int tilesetDefUid = -1;
    std::vector<IntGridValue> intgrid_values;
    std::vector<AutoRuleGroup> groups;

    // Flip expansion mapping: (tile_id << 2) | flip_bits -> expanded_tile_id
    std::unordered_map<uint32_t, int> flip_mapping;
    int expanded_tile_count = 0;  // Total tiles after flip expansion
};

// ============================================================
// Level and layer data
// ============================================================

// Pre-computed tile from LDtk editor
struct PrecomputedTile {
    int tile_id;
    int grid_x, grid_y;    // Cell coordinates
    int flip;               // 0=none, 1=flipX, 2=flipY, 3=both
    float alpha = 1.0f;
};

// Layer data within a level
struct LevelLayerData {
    std::string name;
    std::string type;       // "IntGrid", "AutoLayer", "Tiles", "Entities"
    int width = 0, height = 0;      // In cells
    int gridSize = 0;                // Cell size in pixels
    int tilesetDefUid = -1;
    std::vector<int> intgrid;                      // Source IntGrid values
    std::vector<PrecomputedTile> auto_tiles;       // Pre-computed from editor
    std::vector<PrecomputedTile> grid_tiles;       // Manual tile placement
    nlohmann::json entities;                        // Entity data as JSON
};

// Level
struct LevelData {
    std::string name;
    int width_px = 0, height_px = 0;  // Pixel dimensions
    int worldX = 0, worldY = 0;
    std::vector<LevelLayerData> layers;
};

// ============================================================
// Top-level project
// ============================================================

struct LdtkProjectData {
    std::string source_path;
    std::string json_version;
    std::vector<std::shared_ptr<tiled::TileSetData>> tilesets;
    std::unordered_map<int, int> tileset_uid_to_index;  // uid -> index into tilesets
    std::vector<AutoRuleSet> rulesets;
    std::unordered_map<int, int> ruleset_uid_to_index;  // layer uid -> index into rulesets
    std::vector<LevelData> levels;
    nlohmann::json enums;   // Enum definitions (lightweight JSON exposure)
};

} // namespace ldtk
} // namespace mcrf
