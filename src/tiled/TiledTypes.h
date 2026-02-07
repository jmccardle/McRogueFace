#pragma once
#include <string>
#include <vector>
#include <array>
#include <unordered_map>
#include <variant>
#include <memory>
#include <cstdint>
#include <nlohmann/json.hpp>

namespace mcrf {
namespace tiled {

// ============================================================
// Raw intermediate structs — populated by thin XML/JSON parsers
// ============================================================

struct RawProperty {
    std::string name;
    std::string type;   // "bool", "int", "float", "string" (or empty = string)
    std::string value;
};

struct RawTile {
    int id;
    std::vector<RawProperty> properties;
    std::vector<std::pair<int, int>> animation_frames; // (tile_id, duration_ms)
};

struct RawWangColor {
    std::string name;
    int color_index;
    int tile_id;
    float probability;
};

struct RawWangTile {
    int tile_id;
    std::array<int, 8> wang_id;
};

struct RawWangSet {
    std::string name;
    std::string type;  // "corner", "edge", "mixed"
    std::vector<RawWangColor> colors;
    std::vector<RawWangTile> tiles;
};

struct RawTileSet {
    std::string name;
    std::string image_source;
    int tile_width = 0;
    int tile_height = 0;
    int tile_count = 0;
    int columns = 0;
    int margin = 0;
    int spacing = 0;
    int image_width = 0;
    int image_height = 0;
    std::vector<RawProperty> properties;
    std::vector<RawTile> tiles;
    std::vector<RawWangSet> wang_sets;
};

struct RawTileSetRef {
    int firstgid;
    std::string source;
};

struct RawLayer {
    std::string name;
    std::string type;  // "tilelayer", "objectgroup"
    int width = 0;
    int height = 0;
    bool visible = true;
    float opacity = 1.0f;
    std::vector<RawProperty> properties;
    std::vector<uint32_t> tile_data;
    nlohmann::json objects_json;
};

struct RawTileMap {
    int width = 0;
    int height = 0;
    int tile_width = 0;
    int tile_height = 0;
    std::string orientation;  // "orthogonal", etc.
    std::vector<RawProperty> properties;
    std::vector<RawTileSetRef> tileset_refs;
    std::vector<RawLayer> layers;
};

// ============================================================
// Final (built) types — what Python bindings expose
// ============================================================

using PropertyValue = std::variant<bool, int, float, std::string>;

struct KeyFrame {
    int tile_id;
    int duration_ms;
};

struct TileInfo {
    int id;
    std::unordered_map<std::string, PropertyValue> properties;
    std::vector<KeyFrame> animation;
};

enum class WangSetType {
    Corner,
    Edge,
    Mixed
};

struct WangColor {
    std::string name;
    int index;
    int tile_id;
    float probability;
};

struct WangSet {
    std::string name;
    WangSetType type;
    std::vector<WangColor> colors;
    // Maps packed wang_id → tile_id for O(1) lookup
    std::unordered_map<uint64_t, int> wang_lookup;

    static uint64_t packWangId(const std::array<int, 8>& id);
};

struct TileSetData {
    std::string name;
    std::string source_path;    // Filesystem path of the .tsx/.tsj file
    std::string image_source;   // Resolved path to image file
    int tile_width = 0;
    int tile_height = 0;
    int tile_count = 0;
    int columns = 0;
    int margin = 0;
    int spacing = 0;
    int image_width = 0;
    int image_height = 0;
    std::unordered_map<std::string, PropertyValue> properties;
    std::unordered_map<int, TileInfo> tile_info;
    std::vector<WangSet> wang_sets;
};

struct TileLayerData {
    std::string name;
    int width = 0;
    int height = 0;
    bool visible = true;
    float opacity = 1.0f;
    std::vector<uint32_t> global_gids;
};

struct ObjectLayerData {
    std::string name;
    bool visible = true;
    float opacity = 1.0f;
    nlohmann::json objects;
    std::unordered_map<std::string, PropertyValue> properties;
};

struct TileMapData {
    std::string source_path;    // Filesystem path of the .tmx/.tmj file
    int width = 0;
    int height = 0;
    int tile_width = 0;
    int tile_height = 0;
    std::string orientation;
    std::unordered_map<std::string, PropertyValue> properties;

    struct TileSetRef {
        int firstgid;
        std::shared_ptr<TileSetData> tileset;
    };
    std::vector<TileSetRef> tilesets;
    std::vector<TileLayerData> tile_layers;
    std::vector<ObjectLayerData> object_layers;
};

} // namespace tiled
} // namespace mcrf
