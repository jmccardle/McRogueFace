#include "LdtkParse.h"
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <filesystem>

namespace mcrf {
namespace ldtk {

// ============================================================
// Utility helpers (same pattern as TiledParse.cpp)
// ============================================================

// Null-safe string extraction from JSON.
// nlohmann::json::value() throws type_error if the field exists but is null.
static std::string jsonStr(const nlohmann::json& j, const char* key, const std::string& def = "") {
    auto it = j.find(key);
    if (it == j.end() || it->is_null()) return def;
    return it->get<std::string>();
}

static int jsonInt(const nlohmann::json& j, const char* key, int def = 0) {
    auto it = j.find(key);
    if (it == j.end() || it->is_null()) return def;
    return it->get<int>();
}

static float jsonFloat(const nlohmann::json& j, const char* key, float def = 0.0f) {
    auto it = j.find(key);
    if (it == j.end() || it->is_null()) return def;
    return it->get<float>();
}

static bool jsonBool(const nlohmann::json& j, const char* key, bool def = false) {
    auto it = j.find(key);
    if (it == j.end() || it->is_null()) return def;
    return it->get<bool>();
}

static std::string readFile(const std::string& path) {
    std::ifstream f(path);
    if (!f.is_open()) {
        throw std::runtime_error("Cannot open file: " + path);
    }
    std::stringstream ss;
    ss << f.rdbuf();
    return ss.str();
}

static std::string parentDir(const std::string& path) {
    std::filesystem::path p(path);
    return p.parent_path().string();
}

static std::string resolvePath(const std::string& base_dir, const std::string& relative) {
    std::filesystem::path p = std::filesystem::path(base_dir) / relative;
    return p.lexically_normal().string();
}

// ============================================================
// Parse tileset definitions -> TileSetData
// ============================================================

static std::shared_ptr<tiled::TileSetData> parseTilesetDef(
    const nlohmann::json& def, const std::string& base_dir)
{
    auto ts = std::make_shared<tiled::TileSetData>();
    ts->name = jsonStr(def, "identifier");

    // Resolve image path (relPath can be null for embedded atlases)
    std::string rel_path = jsonStr(def, "relPath");
    if (!rel_path.empty()) {
        ts->image_source = resolvePath(base_dir, rel_path);
    }
    ts->source_path = ts->image_source;

    int grid_size = jsonInt(def, "tileGridSize");
    ts->tile_width = grid_size;
    ts->tile_height = grid_size;
    ts->columns = jsonInt(def, "__cWid");
    int rows = jsonInt(def, "__cHei");
    ts->tile_count = ts->columns * rows;
    ts->margin = jsonInt(def, "padding");
    ts->spacing = jsonInt(def, "spacing");
    ts->image_width = jsonInt(def, "pxWid");
    ts->image_height = jsonInt(def, "pxHei");

    // Per-tile custom data
    if (def.contains("customData") && def["customData"].is_array()) {
        for (const auto& cd : def["customData"]) {
            int tile_id = jsonInt(cd, "tileId", -1);
            std::string data = jsonStr(cd, "data");
            if (tile_id >= 0 && !data.empty()) {
                tiled::TileInfo ti;
                ti.id = tile_id;
                ti.properties["customData"] = tiled::PropertyValue(data);
                ts->tile_info[tile_id] = std::move(ti);
            }
        }
    }

    // Enum tags as properties
    if (def.contains("enumTags") && def["enumTags"].is_array()) {
        for (const auto& et : def["enumTags"]) {
            std::string enum_id = jsonStr(et, "enumValueId");
            if (et.contains("tileIds") && et["tileIds"].is_array()) {
                for (const auto& tid_json : et["tileIds"]) {
                    int tile_id = tid_json.get<int>();
                    auto& ti = ts->tile_info[tile_id];
                    ti.id = tile_id;
                    ti.properties["enum_tag"] = tiled::PropertyValue(enum_id);
                }
            }
        }
    }

    return ts;
}

// ============================================================
// Convert LDtk tileRectsIds to flat tile index
// LDtk stores tile references as [x, y] pixel rectangles
// ============================================================

static int rectToTileId(const nlohmann::json& rect, int tile_size, int columns) {
    if (!rect.is_array() || rect.size() < 2) return -1;
    int px_x = rect[0].get<int>();
    int px_y = rect[1].get<int>();
    if (tile_size <= 0 || columns <= 0) return -1;
    int col = px_x / tile_size;
    int row = px_y / tile_size;
    return row * columns + col;
}

// ============================================================
// Parse auto-rule definitions from layer definitions
// ============================================================

static AutoRule parseAutoRule(const nlohmann::json& rule_json,
                              int tileset_grid_size, int tileset_columns)
{
    AutoRule rule;
    rule.uid = jsonInt(rule_json, "uid");
    rule.size = jsonInt(rule_json, "size", 3);
    rule.active = jsonBool(rule_json, "active", true);
    rule.chance = jsonFloat(rule_json, "chance", 1.0f);
    rule.breakOnMatch = jsonBool(rule_json, "breakOnMatch", true);
    rule.outOfBoundsValue = jsonInt(rule_json, "outOfBoundsValue", -1);
    rule.flipX = jsonBool(rule_json, "flipX");
    rule.flipY = jsonBool(rule_json, "flipY");

    // Pivot offset
    rule.pivotX = jsonFloat(rule_json, "pivotX") >= 0.5f ? 1 : 0;
    rule.pivotY = jsonFloat(rule_json, "pivotY") >= 0.5f ? 1 : 0;

    // Pattern: flat array of size*size integers
    if (rule_json.contains("pattern") && rule_json["pattern"].is_array()) {
        for (const auto& val : rule_json["pattern"]) {
            rule.pattern.push_back(val.get<int>());
        }
    }

    // Tile IDs from tileRectsIds
    // Format varies by LDtk version:
    //   Newer: [[tile_id], [tile_id], ...]  - each alternative is [flat_tile_id]
    //   Older: [[[px_x, px_y]], [[px_x, px_y]], ...]  - each alternative is [[x,y] rect]
    if (rule_json.contains("tileRectsIds") && rule_json["tileRectsIds"].is_array()) {
        for (const auto& alt : rule_json["tileRectsIds"]) {
            if (!alt.is_array() || alt.empty()) continue;

            // Check the first element to determine format
            const auto& first = alt[0];
            if (first.is_number_integer()) {
                // Flat tile ID format: [tile_id] or [tile_id, ...]
                // Take first element as the tile ID for this alternative
                rule.tile_ids.push_back(first.get<int>());
            } else if (first.is_array()) {
                // Pixel rect format: [[px_x, px_y], ...]
                int tid = rectToTileId(first, tileset_grid_size, tileset_columns);
                if (tid >= 0) {
                    rule.tile_ids.push_back(tid);
                }
            }
        }
    }

    // Fallback: legacy tileIds field
    if (rule.tile_ids.empty() && rule_json.contains("tileIds") && rule_json["tileIds"].is_array()) {
        for (const auto& tid : rule_json["tileIds"]) {
            rule.tile_ids.push_back(tid.get<int>());
        }
    }

    return rule;
}

static AutoRuleSet parseAutoRuleSet(const nlohmann::json& layer_def,
                                     const std::unordered_map<int, std::shared_ptr<tiled::TileSetData>>& tileset_by_uid)
{
    AutoRuleSet rs;
    rs.name = jsonStr(layer_def, "identifier");
    rs.gridSize = jsonInt(layer_def, "gridSize");
    rs.tilesetDefUid = jsonInt(layer_def, "tilesetDefUid", -1);

    // Determine tileset dimensions for tile rect conversion
    int ts_grid = 0;
    int ts_columns = 0;
    auto ts_it = tileset_by_uid.find(rs.tilesetDefUid);
    if (ts_it != tileset_by_uid.end() && ts_it->second) {
        ts_grid = ts_it->second->tile_width;
        ts_columns = ts_it->second->columns;
    }

    // IntGrid values
    if (layer_def.contains("intGridValues") && layer_def["intGridValues"].is_array()) {
        for (const auto& igv : layer_def["intGridValues"]) {
            IntGridValue v;
            v.value = jsonInt(igv, "value");
            v.name = jsonStr(igv, "identifier");
            rs.intgrid_values.push_back(std::move(v));
        }
    }

    // Auto-rule groups
    if (layer_def.contains("autoRuleGroups") && layer_def["autoRuleGroups"].is_array()) {
        for (const auto& group_json : layer_def["autoRuleGroups"]) {
            AutoRuleGroup group;
            group.name = jsonStr(group_json, "name");
            group.active = jsonBool(group_json, "active", true);

            if (group_json.contains("rules") && group_json["rules"].is_array()) {
                for (const auto& rule_json : group_json["rules"]) {
                    group.rules.push_back(parseAutoRule(rule_json, ts_grid, ts_columns));
                }
            }

            rs.groups.push_back(std::move(group));
        }
    }

    return rs;
}

// ============================================================
// Parse pre-computed auto-layer tiles
// ============================================================

static std::vector<PrecomputedTile> parseAutoLayerTiles(
    const nlohmann::json& tiles_json, int tile_size, int columns, int grid_size)
{
    std::vector<PrecomputedTile> result;
    if (!tiles_json.is_array()) return result;

    for (const auto& t : tiles_json) {
        PrecomputedTile pt;

        // Tile ID from src rect [x, y]
        if (t.contains("src") && t["src"].is_array() && t["src"].size() >= 2) {
            int px_x = t["src"][0].get<int>();
            int px_y = t["src"][1].get<int>();
            if (tile_size > 0 && columns > 0) {
                int col = px_x / tile_size;
                int row = px_y / tile_size;
                pt.tile_id = row * columns + col;
            } else {
                pt.tile_id = 0;
            }
        } else {
            pt.tile_id = jsonInt(t, "t");
        }

        // Grid position from px array [x, y]
        if (t.contains("px") && t["px"].is_array() && t["px"].size() >= 2) {
            int px_x = t["px"][0].get<int>();
            int px_y = t["px"][1].get<int>();
            // Convert pixel position to grid cell
            if (grid_size > 0) {
                pt.grid_x = px_x / grid_size;
                pt.grid_y = px_y / grid_size;
            }
        }

        // Flip flags: f field (0=none, 1=flipX, 2=flipY, 3=both)
        pt.flip = jsonInt(t, "f");
        pt.alpha = jsonFloat(t, "a", 1.0f);

        result.push_back(std::move(pt));
    }

    return result;
}

// ============================================================
// Parse grid tiles (manual placement)
// ============================================================

static std::vector<PrecomputedTile> parseGridTiles(
    const nlohmann::json& tiles_json, int tile_size, int columns, int grid_size)
{
    // Same format as auto-layer tiles
    return parseAutoLayerTiles(tiles_json, tile_size, columns, grid_size);
}

// ============================================================
// Parse level layer instances
// ============================================================

static LevelLayerData parseLayerInstance(
    const nlohmann::json& layer_json,
    const std::unordered_map<int, std::shared_ptr<tiled::TileSetData>>& tileset_by_uid)
{
    LevelLayerData layer;
    layer.name = jsonStr(layer_json, "__identifier");
    layer.type = jsonStr(layer_json, "__type");
    layer.width = jsonInt(layer_json, "__cWid");
    layer.height = jsonInt(layer_json, "__cHei");
    layer.gridSize = jsonInt(layer_json, "__gridSize");
    layer.tilesetDefUid = jsonInt(layer_json, "__tilesetDefUid", -1);

    // Determine tileset parameters for tile rect conversion
    int ts_grid = 0;
    int ts_columns = 0;
    auto ts_it = tileset_by_uid.find(layer.tilesetDefUid);
    if (ts_it != tileset_by_uid.end() && ts_it->second) {
        ts_grid = ts_it->second->tile_width;
        ts_columns = ts_it->second->columns;
    }

    // IntGrid values (CSV format)
    if (layer_json.contains("intGridCsv") && layer_json["intGridCsv"].is_array()) {
        for (const auto& val : layer_json["intGridCsv"]) {
            layer.intgrid.push_back(val.get<int>());
        }
    }

    // Auto-layer tiles
    if (layer_json.contains("autoLayerTiles") && layer_json["autoLayerTiles"].is_array()) {
        layer.auto_tiles = parseAutoLayerTiles(
            layer_json["autoLayerTiles"], ts_grid, ts_columns, layer.gridSize);
    }

    // Grid tiles (manual placement)
    if (layer_json.contains("gridTiles") && layer_json["gridTiles"].is_array()) {
        layer.grid_tiles = parseGridTiles(
            layer_json["gridTiles"], ts_grid, ts_columns, layer.gridSize);
    }

    // Entity instances
    if (layer_json.contains("entityInstances") && layer_json["entityInstances"].is_array()) {
        layer.entities = layer_json["entityInstances"];
    }

    return layer;
}

// ============================================================
// Parse levels
// ============================================================

static LevelData parseLevel(
    const nlohmann::json& level_json,
    const std::unordered_map<int, std::shared_ptr<tiled::TileSetData>>& tileset_by_uid)
{
    LevelData level;
    level.name = jsonStr(level_json, "identifier");
    level.width_px = jsonInt(level_json, "pxWid");
    level.height_px = jsonInt(level_json, "pxHei");
    level.worldX = jsonInt(level_json, "worldX");
    level.worldY = jsonInt(level_json, "worldY");

    // Layer instances
    if (level_json.contains("layerInstances") && level_json["layerInstances"].is_array()) {
        for (const auto& li : level_json["layerInstances"]) {
            level.layers.push_back(parseLayerInstance(li, tileset_by_uid));
        }
    }

    return level;
}

// ============================================================
// Public API: load LDtk project
// ============================================================

std::shared_ptr<LdtkProjectData> loadLdtkProject(const std::string& path) {
    std::string abs_path = std::filesystem::absolute(path).string();
    std::string text = readFile(abs_path);
    nlohmann::json j = nlohmann::json::parse(text);

    auto proj = std::make_shared<LdtkProjectData>();
    proj->source_path = abs_path;
    proj->json_version = jsonStr(j, "jsonVersion");
    std::string base_dir = parentDir(abs_path);

    // Build uid -> tileset map for cross-referencing
    std::unordered_map<int, std::shared_ptr<tiled::TileSetData>> tileset_by_uid;

    // Parse tileset definitions from defs.tilesets
    if (j.contains("defs") && j["defs"].contains("tilesets") && j["defs"]["tilesets"].is_array()) {
        for (const auto& ts_def : j["defs"]["tilesets"]) {
            int uid = jsonInt(ts_def, "uid", -1);
            auto ts = parseTilesetDef(ts_def, base_dir);
            proj->tileset_uid_to_index[uid] = static_cast<int>(proj->tilesets.size());
            proj->tilesets.push_back(ts);
            tileset_by_uid[uid] = ts;
        }
    }

    // Parse layer definitions for auto-rule sets
    if (j.contains("defs") && j["defs"].contains("layers") && j["defs"]["layers"].is_array()) {
        for (const auto& layer_def : j["defs"]["layers"]) {
            std::string layer_type = jsonStr(layer_def, "type");
            // Only IntGrid and AutoLayer types have auto-rules
            if (layer_type == "IntGrid" || layer_type == "AutoLayer") {
                // Only include if there are actual rules
                bool has_rules = false;
                if (layer_def.contains("autoRuleGroups") && layer_def["autoRuleGroups"].is_array()) {
                    for (const auto& grp : layer_def["autoRuleGroups"]) {
                        if (grp.contains("rules") && grp["rules"].is_array() && !grp["rules"].empty()) {
                            has_rules = true;
                            break;
                        }
                    }
                }
                bool has_intgrid = layer_def.contains("intGridValues") &&
                                   layer_def["intGridValues"].is_array() &&
                                   !layer_def["intGridValues"].empty();

                if (has_rules || has_intgrid) {
                    int layer_uid = jsonInt(layer_def, "uid", -1);
                    AutoRuleSet rs = parseAutoRuleSet(layer_def, tileset_by_uid);
                    proj->ruleset_uid_to_index[layer_uid] = static_cast<int>(proj->rulesets.size());
                    proj->rulesets.push_back(std::move(rs));
                }
            }
        }
    }

    // Parse enum definitions
    if (j.contains("defs") && j["defs"].contains("enums") && j["defs"]["enums"].is_array()) {
        proj->enums = j["defs"]["enums"];
    }

    // Parse levels
    if (j.contains("levels") && j["levels"].is_array()) {
        for (const auto& level_json : j["levels"]) {
            proj->levels.push_back(parseLevel(level_json, tileset_by_uid));
        }
    }

    return proj;
}

} // namespace ldtk
} // namespace mcrf
