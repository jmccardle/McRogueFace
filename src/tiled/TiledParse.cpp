#include "TiledParse.h"
#include "RapidXML/rapidxml.hpp"
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <algorithm>
#include <filesystem>

namespace mcrf {
namespace tiled {

// ============================================================
// Utility helpers
// ============================================================

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

static bool endsWith(const std::string& str, const std::string& suffix) {
    if (suffix.size() > str.size()) return false;
    return str.compare(str.size() - suffix.size(), suffix.size(), suffix) == 0;
}

// Get attribute value or empty string
static std::string xmlAttr(rapidxml::xml_node<>* node, const char* name) {
    auto* attr = node->first_attribute(name);
    return attr ? std::string(attr->value(), attr->value_size()) : "";
}

static int xmlAttrInt(rapidxml::xml_node<>* node, const char* name, int def = 0) {
    auto* attr = node->first_attribute(name);
    if (!attr) return def;
    return std::stoi(std::string(attr->value(), attr->value_size()));
}

static float xmlAttrFloat(rapidxml::xml_node<>* node, const char* name, float def = 0.0f) {
    auto* attr = node->first_attribute(name);
    if (!attr) return def;
    return std::stof(std::string(attr->value(), attr->value_size()));
}

// ============================================================
// Property conversion (Raw → Final)
// ============================================================

static PropertyValue convertProperty(const RawProperty& raw) {
    if (raw.type == "bool") {
        return PropertyValue(raw.value == "true");
    } else if (raw.type == "int") {
        return PropertyValue(std::stoi(raw.value));
    } else if (raw.type == "float") {
        return PropertyValue(std::stof(raw.value));
    } else {
        // Default: string (includes empty type)
        return PropertyValue(raw.value);
    }
}

static std::unordered_map<std::string, PropertyValue> convertProperties(
    const std::vector<RawProperty>& raw_props) {
    std::unordered_map<std::string, PropertyValue> result;
    for (const auto& rp : raw_props) {
        result[rp.name] = convertProperty(rp);
    }
    return result;
}

// ============================================================
// WangSet packing
// ============================================================

uint64_t WangSet::packWangId(const std::array<int, 8>& id) {
    // Pack 8 values (each 0-255) into 64-bit integer
    // Each value gets 8 bits
    uint64_t packed = 0;
    for (int i = 0; i < 8; i++) {
        packed |= (static_cast<uint64_t>(id[i] & 0xFF)) << (i * 8);
    }
    return packed;
}

// ============================================================
// XML property parsing (shared by TSX and TMX)
// ============================================================

static void parseXmlProperties(rapidxml::xml_node<>* parent, std::vector<RawProperty>& out) {
    auto* props_node = parent->first_node("properties");
    if (!props_node) return;
    for (auto* prop = props_node->first_node("property"); prop; prop = prop->next_sibling("property")) {
        RawProperty rp;
        rp.name = xmlAttr(prop, "name");
        rp.type = xmlAttr(prop, "type");
        rp.value = xmlAttr(prop, "value");
        // Some properties have value as node text instead of attribute
        if (rp.value.empty() && prop->value_size() > 0) {
            rp.value = std::string(prop->value(), prop->value_size());
        }
        out.push_back(std::move(rp));
    }
}

// ============================================================
// TSX parser (XML tileset)
// ============================================================

static RawTileSet parseTSX(const std::string& path) {
    std::string text = readFile(path);
    rapidxml::xml_document<> doc;
    doc.parse<0>(text.data());

    auto* tileset_node = doc.first_node("tileset");
    if (!tileset_node) {
        throw std::runtime_error("No <tileset> element in: " + path);
    }

    RawTileSet raw;
    raw.name = xmlAttr(tileset_node, "name");
    raw.tile_width = xmlAttrInt(tileset_node, "tilewidth");
    raw.tile_height = xmlAttrInt(tileset_node, "tileheight");
    raw.tile_count = xmlAttrInt(tileset_node, "tilecount");
    raw.columns = xmlAttrInt(tileset_node, "columns");
    raw.margin = xmlAttrInt(tileset_node, "margin");
    raw.spacing = xmlAttrInt(tileset_node, "spacing");

    // Image element
    auto* image_node = tileset_node->first_node("image");
    if (image_node) {
        raw.image_source = xmlAttr(image_node, "source");
        raw.image_width = xmlAttrInt(image_node, "width");
        raw.image_height = xmlAttrInt(image_node, "height");
    }

    // Properties
    parseXmlProperties(tileset_node, raw.properties);

    // Tile elements (for per-tile properties and animations)
    for (auto* tile = tileset_node->first_node("tile"); tile; tile = tile->next_sibling("tile")) {
        RawTile rt;
        rt.id = xmlAttrInt(tile, "id");
        parseXmlProperties(tile, rt.properties);

        // Animation frames
        auto* anim = tile->first_node("animation");
        if (anim) {
            for (auto* frame = anim->first_node("frame"); frame; frame = frame->next_sibling("frame")) {
                int tid = xmlAttrInt(frame, "tileid");
                int dur = xmlAttrInt(frame, "duration");
                rt.animation_frames.emplace_back(tid, dur);
            }
        }
        raw.tiles.push_back(std::move(rt));
    }

    // Wang sets
    auto* wangsets_node = tileset_node->first_node("wangsets");
    if (wangsets_node) {
        for (auto* ws = wangsets_node->first_node("wangset"); ws; ws = ws->next_sibling("wangset")) {
            RawWangSet rws;
            rws.name = xmlAttr(ws, "name");
            rws.type = xmlAttr(ws, "type");

            // Wang colors (1-indexed by position in list)
            int color_idx = 1;
            for (auto* wc = ws->first_node("wangcolor"); wc; wc = wc->next_sibling("wangcolor")) {
                RawWangColor rwc;
                rwc.name = xmlAttr(wc, "name");
                rwc.color_index = color_idx++;
                rwc.tile_id = xmlAttrInt(wc, "tile");
                rwc.probability = xmlAttrFloat(wc, "probability", 1.0f);
                rws.colors.push_back(std::move(rwc));
            }

            // Wang tiles
            for (auto* wt = ws->first_node("wangtile"); wt; wt = wt->next_sibling("wangtile")) {
                RawWangTile rwt;
                rwt.tile_id = xmlAttrInt(wt, "tileid");
                // Parse wangid: comma-separated 8 integers
                std::string wid_str = xmlAttr(wt, "wangid");
                std::array<int, 8> wid = {};
                std::istringstream iss(wid_str);
                std::string token;
                int idx = 0;
                while (std::getline(iss, token, ',') && idx < 8) {
                    wid[idx++] = std::stoi(token);
                }
                rwt.wang_id = wid;
                rws.tiles.push_back(std::move(rwt));
            }

            raw.wang_sets.push_back(std::move(rws));
        }
    }

    return raw;
}

// ============================================================
// TSJ parser (JSON tileset)
// ============================================================

static void parseJsonProperties(const nlohmann::json& j, std::vector<RawProperty>& out) {
    if (!j.contains("properties") || !j["properties"].is_array()) return;
    for (const auto& prop : j["properties"]) {
        RawProperty rp;
        rp.name = prop.value("name", "");
        rp.type = prop.value("type", "");
        // Value can be different JSON types
        if (prop.contains("value")) {
            const auto& val = prop["value"];
            if (val.is_boolean()) {
                rp.type = "bool";
                rp.value = val.get<bool>() ? "true" : "false";
            } else if (val.is_number_integer()) {
                rp.type = "int";
                rp.value = std::to_string(val.get<int>());
            } else if (val.is_number_float()) {
                rp.type = "float";
                rp.value = std::to_string(val.get<float>());
            } else if (val.is_string()) {
                rp.value = val.get<std::string>();
            }
        }
        out.push_back(std::move(rp));
    }
}

static RawTileSet parseTSJ(const std::string& path) {
    std::string text = readFile(path);
    nlohmann::json j = nlohmann::json::parse(text);

    RawTileSet raw;
    raw.name = j.value("name", "");
    raw.tile_width = j.value("tilewidth", 0);
    raw.tile_height = j.value("tileheight", 0);
    raw.tile_count = j.value("tilecount", 0);
    raw.columns = j.value("columns", 0);
    raw.margin = j.value("margin", 0);
    raw.spacing = j.value("spacing", 0);
    raw.image_source = j.value("image", "");
    raw.image_width = j.value("imagewidth", 0);
    raw.image_height = j.value("imageheight", 0);

    parseJsonProperties(j, raw.properties);

    // Tiles
    if (j.contains("tiles") && j["tiles"].is_array()) {
        for (const auto& tile : j["tiles"]) {
            RawTile rt;
            rt.id = tile.value("id", 0);
            parseJsonProperties(tile, rt.properties);
            if (tile.contains("animation") && tile["animation"].is_array()) {
                for (const auto& frame : tile["animation"]) {
                    int tid = frame.value("tileid", 0);
                    int dur = frame.value("duration", 0);
                    rt.animation_frames.emplace_back(tid, dur);
                }
            }
            raw.tiles.push_back(std::move(rt));
        }
    }

    // Wang sets
    if (j.contains("wangsets") && j["wangsets"].is_array()) {
        for (const auto& ws : j["wangsets"]) {
            RawWangSet rws;
            rws.name = ws.value("name", "");
            rws.type = ws.value("type", "");

            if (ws.contains("colors") && ws["colors"].is_array()) {
                int ci = 1; // Tiled wang colors are 1-indexed
                for (const auto& wc : ws["colors"]) {
                    RawWangColor rwc;
                    rwc.name = wc.value("name", "");
                    rwc.color_index = ci++;
                    rwc.tile_id = wc.value("tile", -1);
                    rwc.probability = wc.value("probability", 1.0f);
                    rws.colors.push_back(std::move(rwc));
                }
            }

            if (ws.contains("wangtiles") && ws["wangtiles"].is_array()) {
                for (const auto& wt : ws["wangtiles"]) {
                    RawWangTile rwt;
                    rwt.tile_id = wt.value("tileid", 0);
                    std::array<int, 8> wid = {};
                    if (wt.contains("wangid") && wt["wangid"].is_array()) {
                        for (int i = 0; i < 8 && i < (int)wt["wangid"].size(); i++) {
                            wid[i] = wt["wangid"][i].get<int>();
                        }
                    }
                    rwt.wang_id = wid;
                    rws.tiles.push_back(std::move(rwt));
                }
            }

            raw.wang_sets.push_back(std::move(rws));
        }
    }

    return raw;
}

// ============================================================
// Builder: RawTileSet → TileSetData
// ============================================================

static std::shared_ptr<TileSetData> buildTileSet(const RawTileSet& raw, const std::string& source_path) {
    auto ts = std::make_shared<TileSetData>();
    ts->source_path = source_path;
    ts->name = raw.name;
    ts->tile_width = raw.tile_width;
    ts->tile_height = raw.tile_height;
    ts->tile_count = raw.tile_count;
    ts->columns = raw.columns;
    ts->margin = raw.margin;
    ts->spacing = raw.spacing;
    ts->image_width = raw.image_width;
    ts->image_height = raw.image_height;

    // Resolve image path relative to tileset file
    std::string base_dir = parentDir(source_path);
    ts->image_source = resolvePath(base_dir, raw.image_source);

    // Convert properties
    ts->properties = convertProperties(raw.properties);

    // Convert tile info
    for (const auto& rt : raw.tiles) {
        TileInfo ti;
        ti.id = rt.id;
        ti.properties = convertProperties(rt.properties);
        for (const auto& [tid, dur] : rt.animation_frames) {
            ti.animation.push_back({tid, dur});
        }
        ts->tile_info[ti.id] = std::move(ti);
    }

    // Convert wang sets
    for (const auto& rws : raw.wang_sets) {
        WangSet ws;
        ws.name = rws.name;
        if (rws.type == "corner") ws.type = WangSetType::Corner;
        else if (rws.type == "edge") ws.type = WangSetType::Edge;
        else ws.type = WangSetType::Mixed;

        for (const auto& rwc : rws.colors) {
            WangColor wc;
            wc.name = rwc.name;
            wc.index = rwc.color_index;
            wc.tile_id = rwc.tile_id;
            wc.probability = rwc.probability;
            ws.colors.push_back(std::move(wc));
        }

        // Build lookup table
        for (const auto& rwt : rws.tiles) {
            uint64_t key = WangSet::packWangId(rwt.wang_id);
            ws.wang_lookup[key] = rwt.tile_id;
        }

        ts->wang_sets.push_back(std::move(ws));
    }

    return ts;
}

// ============================================================
// TMX parser (XML tilemap)
// ============================================================

static RawTileMap parseTMX(const std::string& path) {
    std::string text = readFile(path);
    rapidxml::xml_document<> doc;
    doc.parse<0>(text.data());

    auto* map_node = doc.first_node("map");
    if (!map_node) {
        throw std::runtime_error("No <map> element in: " + path);
    }

    RawTileMap raw;
    raw.width = xmlAttrInt(map_node, "width");
    raw.height = xmlAttrInt(map_node, "height");
    raw.tile_width = xmlAttrInt(map_node, "tilewidth");
    raw.tile_height = xmlAttrInt(map_node, "tileheight");
    raw.orientation = xmlAttr(map_node, "orientation");

    parseXmlProperties(map_node, raw.properties);

    // Tileset references
    for (auto* ts = map_node->first_node("tileset"); ts; ts = ts->next_sibling("tileset")) {
        RawTileSetRef ref;
        ref.firstgid = xmlAttrInt(ts, "firstgid");
        ref.source = xmlAttr(ts, "source");
        raw.tileset_refs.push_back(std::move(ref));
    }

    // Layers
    for (auto* child = map_node->first_node(); child; child = child->next_sibling()) {
        std::string node_name(child->name(), child->name_size());

        if (node_name == "layer") {
            RawLayer layer;
            layer.name = xmlAttr(child, "name");
            layer.type = "tilelayer";
            layer.width = xmlAttrInt(child, "width");
            layer.height = xmlAttrInt(child, "height");
            std::string vis = xmlAttr(child, "visible");
            layer.visible = vis.empty() || vis != "0";
            layer.opacity = xmlAttrFloat(child, "opacity", 1.0f);
            parseXmlProperties(child, layer.properties);

            // Parse CSV tile data
            auto* data_node = child->first_node("data");
            if (data_node) {
                std::string encoding = xmlAttr(data_node, "encoding");
                if (!encoding.empty() && encoding != "csv") {
                    throw std::runtime_error("Unsupported tile data encoding: " + encoding +
                        " (only CSV supported). File: " + path);
                }
                std::string csv(data_node->value(), data_node->value_size());
                std::istringstream iss(csv);
                std::string token;
                while (std::getline(iss, token, ',')) {
                    // Trim whitespace
                    auto start = token.find_first_not_of(" \t\r\n");
                    if (start == std::string::npos) continue;
                    auto end = token.find_last_not_of(" \t\r\n");
                    token = token.substr(start, end - start + 1);
                    if (!token.empty()) {
                        layer.tile_data.push_back(static_cast<uint32_t>(std::stoul(token)));
                    }
                }
            }

            raw.layers.push_back(std::move(layer));
        }
        else if (node_name == "objectgroup") {
            RawLayer layer;
            layer.name = xmlAttr(child, "name");
            layer.type = "objectgroup";
            std::string vis = xmlAttr(child, "visible");
            layer.visible = vis.empty() || vis != "0";
            layer.opacity = xmlAttrFloat(child, "opacity", 1.0f);
            parseXmlProperties(child, layer.properties);

            // Convert XML objects to JSON for uniform Python interface
            nlohmann::json objects_arr = nlohmann::json::array();
            for (auto* obj = child->first_node("object"); obj; obj = obj->next_sibling("object")) {
                nlohmann::json obj_json;
                std::string id_str = xmlAttr(obj, "id");
                if (!id_str.empty()) obj_json["id"] = std::stoi(id_str);
                std::string name = xmlAttr(obj, "name");
                if (!name.empty()) obj_json["name"] = name;
                std::string type = xmlAttr(obj, "type");
                if (!type.empty()) obj_json["type"] = type;
                std::string x_str = xmlAttr(obj, "x");
                if (!x_str.empty()) obj_json["x"] = std::stof(x_str);
                std::string y_str = xmlAttr(obj, "y");
                if (!y_str.empty()) obj_json["y"] = std::stof(y_str);
                std::string w_str = xmlAttr(obj, "width");
                if (!w_str.empty()) obj_json["width"] = std::stof(w_str);
                std::string h_str = xmlAttr(obj, "height");
                if (!h_str.empty()) obj_json["height"] = std::stof(h_str);
                std::string rot_str = xmlAttr(obj, "rotation");
                if (!rot_str.empty()) obj_json["rotation"] = std::stof(rot_str);
                std::string visible_str = xmlAttr(obj, "visible");
                if (!visible_str.empty()) obj_json["visible"] = (visible_str != "0");

                // Object properties
                std::vector<RawProperty> obj_props;
                parseXmlProperties(obj, obj_props);
                if (!obj_props.empty()) {
                    nlohmann::json props_json;
                    for (const auto& rp : obj_props) {
                        if (rp.type == "bool") props_json[rp.name] = (rp.value == "true");
                        else if (rp.type == "int") props_json[rp.name] = std::stoi(rp.value);
                        else if (rp.type == "float") props_json[rp.name] = std::stof(rp.value);
                        else props_json[rp.name] = rp.value;
                    }
                    obj_json["properties"] = props_json;
                }

                // Check for point/ellipse/polygon sub-elements
                if (obj->first_node("point")) {
                    obj_json["point"] = true;
                }
                if (obj->first_node("ellipse")) {
                    obj_json["ellipse"] = true;
                }
                auto* polygon_node = obj->first_node("polygon");
                if (polygon_node) {
                    std::string points_str = xmlAttr(polygon_node, "points");
                    nlohmann::json points_arr = nlohmann::json::array();
                    std::istringstream pss(points_str);
                    std::string pt;
                    while (pss >> pt) {
                        auto comma = pt.find(',');
                        if (comma != std::string::npos) {
                            nlohmann::json point;
                            point["x"] = std::stof(pt.substr(0, comma));
                            point["y"] = std::stof(pt.substr(comma + 1));
                            points_arr.push_back(point);
                        }
                    }
                    obj_json["polygon"] = points_arr;
                }

                objects_arr.push_back(std::move(obj_json));
            }
            layer.objects_json = objects_arr;

            raw.layers.push_back(std::move(layer));
        }
    }

    return raw;
}

// ============================================================
// TMJ parser (JSON tilemap)
// ============================================================

static RawTileMap parseTMJ(const std::string& path) {
    std::string text = readFile(path);
    nlohmann::json j = nlohmann::json::parse(text);

    RawTileMap raw;
    raw.width = j.value("width", 0);
    raw.height = j.value("height", 0);
    raw.tile_width = j.value("tilewidth", 0);
    raw.tile_height = j.value("tileheight", 0);
    raw.orientation = j.value("orientation", "orthogonal");

    parseJsonProperties(j, raw.properties);

    // Tileset references
    if (j.contains("tilesets") && j["tilesets"].is_array()) {
        for (const auto& ts : j["tilesets"]) {
            RawTileSetRef ref;
            ref.firstgid = ts.value("firstgid", 0);
            ref.source = ts.value("source", "");
            raw.tileset_refs.push_back(std::move(ref));
        }
    }

    // Layers
    if (j.contains("layers") && j["layers"].is_array()) {
        for (const auto& layer_json : j["layers"]) {
            RawLayer layer;
            layer.name = layer_json.value("name", "");
            layer.type = layer_json.value("type", "");
            layer.width = layer_json.value("width", 0);
            layer.height = layer_json.value("height", 0);
            layer.visible = layer_json.value("visible", true);
            layer.opacity = layer_json.value("opacity", 1.0f);

            parseJsonProperties(layer_json, layer.properties);

            if (layer.type == "tilelayer") {
                if (layer_json.contains("data") && layer_json["data"].is_array()) {
                    for (const auto& val : layer_json["data"]) {
                        layer.tile_data.push_back(val.get<uint32_t>());
                    }
                }
            }
            else if (layer.type == "objectgroup") {
                if (layer_json.contains("objects")) {
                    layer.objects_json = layer_json["objects"];
                }
            }

            raw.layers.push_back(std::move(layer));
        }
    }

    return raw;
}

// ============================================================
// Builder: RawTileMap → TileMapData
// ============================================================

static std::shared_ptr<TileMapData> buildTileMap(const RawTileMap& raw, const std::string& source_path) {
    auto tm = std::make_shared<TileMapData>();
    tm->source_path = source_path;
    tm->width = raw.width;
    tm->height = raw.height;
    tm->tile_width = raw.tile_width;
    tm->tile_height = raw.tile_height;
    tm->orientation = raw.orientation;
    tm->properties = convertProperties(raw.properties);

    // Load referenced tilesets
    std::string base_dir = parentDir(source_path);
    for (const auto& ref : raw.tileset_refs) {
        TileMapData::TileSetRef ts_ref;
        ts_ref.firstgid = ref.firstgid;
        std::string ts_path = resolvePath(base_dir, ref.source);
        ts_ref.tileset = loadTileSet(ts_path);
        tm->tilesets.push_back(std::move(ts_ref));
    }

    // Separate tile layers from object layers
    for (const auto& rl : raw.layers) {
        if (rl.type == "tilelayer") {
            TileLayerData tld;
            tld.name = rl.name;
            tld.width = rl.width;
            tld.height = rl.height;
            tld.visible = rl.visible;
            tld.opacity = rl.opacity;
            tld.global_gids = rl.tile_data;
            tm->tile_layers.push_back(std::move(tld));
        }
        else if (rl.type == "objectgroup") {
            ObjectLayerData old;
            old.name = rl.name;
            old.visible = rl.visible;
            old.opacity = rl.opacity;
            old.objects = rl.objects_json;
            old.properties = convertProperties(rl.properties);
            tm->object_layers.push_back(std::move(old));
        }
    }

    return tm;
}

// ============================================================
// Public API: auto-detect and load
// ============================================================

std::shared_ptr<TileSetData> loadTileSet(const std::string& path) {
    std::string abs_path = std::filesystem::absolute(path).string();
    RawTileSet raw;
    if (endsWith(abs_path, ".tsx")) {
        raw = parseTSX(abs_path);
    } else if (endsWith(abs_path, ".tsj") || endsWith(abs_path, ".json")) {
        raw = parseTSJ(abs_path);
    } else {
        throw std::runtime_error("Unknown tileset format (expected .tsx or .tsj): " + path);
    }
    return buildTileSet(raw, abs_path);
}

std::shared_ptr<TileMapData> loadTileMap(const std::string& path) {
    std::string abs_path = std::filesystem::absolute(path).string();
    RawTileMap raw;
    if (endsWith(abs_path, ".tmx")) {
        raw = parseTMX(abs_path);
    } else if (endsWith(abs_path, ".tmj") || endsWith(abs_path, ".json")) {
        raw = parseTMJ(abs_path);
    } else {
        throw std::runtime_error("Unknown tilemap format (expected .tmx or .tmj): " + path);
    }
    return buildTileMap(raw, abs_path);
}

// ============================================================
// JSON → Python conversion (for object layers)
// ============================================================

PyObject* jsonToPython(const nlohmann::json& j) {
    if (j.is_null()) {
        Py_RETURN_NONE;
    }
    if (j.is_boolean()) {
        return PyBool_FromLong(j.get<bool>());
    }
    if (j.is_number_integer()) {
        return PyLong_FromLongLong(j.get<long long>());
    }
    if (j.is_number_float()) {
        return PyFloat_FromDouble(j.get<double>());
    }
    if (j.is_string()) {
        const std::string& s = j.get_ref<const std::string&>();
        return PyUnicode_FromStringAndSize(s.c_str(), s.size());
    }
    if (j.is_array()) {
        PyObject* list = PyList_New(j.size());
        if (!list) return NULL;
        for (size_t i = 0; i < j.size(); i++) {
            PyObject* item = jsonToPython(j[i]);
            if (!item) {
                Py_DECREF(list);
                return NULL;
            }
            PyList_SET_ITEM(list, i, item); // steals ref
        }
        return list;
    }
    if (j.is_object()) {
        PyObject* dict = PyDict_New();
        if (!dict) return NULL;
        for (auto it = j.begin(); it != j.end(); ++it) {
            PyObject* val = jsonToPython(it.value());
            if (!val) {
                Py_DECREF(dict);
                return NULL;
            }
            if (PyDict_SetItemString(dict, it.key().c_str(), val) < 0) {
                Py_DECREF(val);
                Py_DECREF(dict);
                return NULL;
            }
            Py_DECREF(val);
        }
        return dict;
    }
    Py_RETURN_NONE;
}

// ============================================================
// PropertyValue → Python conversion
// ============================================================

PyObject* propertyValueToPython(const PropertyValue& val) {
    return std::visit([](auto&& arg) -> PyObject* {
        using T = std::decay_t<decltype(arg)>;
        if constexpr (std::is_same_v<T, bool>) {
            return PyBool_FromLong(arg);
        } else if constexpr (std::is_same_v<T, int>) {
            return PyLong_FromLong(arg);
        } else if constexpr (std::is_same_v<T, float>) {
            return PyFloat_FromDouble(arg);
        } else if constexpr (std::is_same_v<T, std::string>) {
            return PyUnicode_FromStringAndSize(arg.c_str(), arg.size());
        }
        Py_RETURN_NONE;
    }, val);
}

PyObject* propertiesToPython(const std::unordered_map<std::string, PropertyValue>& props) {
    PyObject* dict = PyDict_New();
    if (!dict) return NULL;
    for (const auto& [key, val] : props) {
        PyObject* py_val = propertyValueToPython(val);
        if (!py_val) {
            Py_DECREF(dict);
            return NULL;
        }
        if (PyDict_SetItemString(dict, key.c_str(), py_val) < 0) {
            Py_DECREF(py_val);
            Py_DECREF(dict);
            return NULL;
        }
        Py_DECREF(py_val);
    }
    return dict;
}

} // namespace tiled
} // namespace mcrf
