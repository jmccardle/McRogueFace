#pragma once
#include "TiledTypes.h"
#include <Python.h>

namespace mcrf {
namespace tiled {

// Load a tileset from .tsx or .tsj (auto-detect by extension)
std::shared_ptr<TileSetData> loadTileSet(const std::string& path);

// Load a tilemap from .tmx or .tmj (auto-detect by extension)
std::shared_ptr<TileMapData> loadTileMap(const std::string& path);

// Convert nlohmann::json to Python object (for object layers)
PyObject* jsonToPython(const nlohmann::json& j);

// Convert PropertyValue to Python object
PyObject* propertyValueToPython(const PropertyValue& val);

// Convert a properties map to Python dict
PyObject* propertiesToPython(const std::unordered_map<std::string, PropertyValue>& props);

} // namespace tiled
} // namespace mcrf
