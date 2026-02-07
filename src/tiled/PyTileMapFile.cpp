#include "PyTileMapFile.h"
#include "PyTileSetFile.h"
#include "TiledParse.h"
#include "McRFPy_Doc.h"
#include "GridLayers.h"
#include <cstring>

using namespace mcrf::tiled;

// ============================================================
// Type lifecycle
// ============================================================

PyObject* PyTileMapFile::pynew(PyTypeObject* type, PyObject* args, PyObject* kwds) {
    auto* self = (PyTileMapFileObject*)type->tp_alloc(type, 0);
    if (self) {
        new (&self->data) std::shared_ptr<TileMapData>();
    }
    return (PyObject*)self;
}

int PyTileMapFile::init(PyTileMapFileObject* self, PyObject* args, PyObject* kwds) {
    static const char* keywords[] = {"path", nullptr};
    const char* path = nullptr;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "s", const_cast<char**>(keywords), &path))
        return -1;

    try {
        self->data = loadTileMap(path);
    } catch (const std::exception& e) {
        PyErr_Format(PyExc_IOError, "Failed to load tilemap: %s", e.what());
        return -1;
    }

    return 0;
}

void PyTileMapFile::dealloc(PyTileMapFileObject* self) {
    self->data.~shared_ptr();
    Py_TYPE(self)->tp_free((PyObject*)self);
}

PyObject* PyTileMapFile::repr(PyObject* obj) {
    auto* self = (PyTileMapFileObject*)obj;
    if (!self->data) {
        return PyUnicode_FromString("<TileMapFile (uninitialized)>");
    }
    return PyUnicode_FromFormat("<TileMapFile %dx%d, %d tilesets, %d tile layers, %d object layers>",
        self->data->width, self->data->height,
        (int)self->data->tilesets.size(),
        (int)self->data->tile_layers.size(),
        (int)self->data->object_layers.size());
}

// ============================================================
// Properties
// ============================================================

PyObject* PyTileMapFile::get_width(PyTileMapFileObject* self, void*) {
    return PyLong_FromLong(self->data->width);
}

PyObject* PyTileMapFile::get_height(PyTileMapFileObject* self, void*) {
    return PyLong_FromLong(self->data->height);
}

PyObject* PyTileMapFile::get_tile_width(PyTileMapFileObject* self, void*) {
    return PyLong_FromLong(self->data->tile_width);
}

PyObject* PyTileMapFile::get_tile_height(PyTileMapFileObject* self, void*) {
    return PyLong_FromLong(self->data->tile_height);
}

PyObject* PyTileMapFile::get_orientation(PyTileMapFileObject* self, void*) {
    return PyUnicode_FromString(self->data->orientation.c_str());
}

PyObject* PyTileMapFile::get_properties(PyTileMapFileObject* self, void*) {
    return propertiesToPython(self->data->properties);
}

PyObject* PyTileMapFile::get_tileset_count(PyTileMapFileObject* self, void*) {
    return PyLong_FromLong(self->data->tilesets.size());
}

PyObject* PyTileMapFile::get_tile_layer_names(PyTileMapFileObject* self, void*) {
    PyObject* list = PyList_New(self->data->tile_layers.size());
    if (!list) return NULL;
    for (size_t i = 0; i < self->data->tile_layers.size(); i++) {
        PyObject* name = PyUnicode_FromString(self->data->tile_layers[i].name.c_str());
        if (!name) { Py_DECREF(list); return NULL; }
        PyList_SET_ITEM(list, i, name);
    }
    return list;
}

PyObject* PyTileMapFile::get_object_layer_names(PyTileMapFileObject* self, void*) {
    PyObject* list = PyList_New(self->data->object_layers.size());
    if (!list) return NULL;
    for (size_t i = 0; i < self->data->object_layers.size(); i++) {
        PyObject* name = PyUnicode_FromString(self->data->object_layers[i].name.c_str());
        if (!name) { Py_DECREF(list); return NULL; }
        PyList_SET_ITEM(list, i, name);
    }
    return list;
}

// ============================================================
// Methods
// ============================================================

PyObject* PyTileMapFile::tileset(PyTileMapFileObject* self, PyObject* args) {
    int index;
    if (!PyArg_ParseTuple(args, "i", &index))
        return NULL;

    if (index < 0 || index >= (int)self->data->tilesets.size()) {
        PyErr_Format(PyExc_IndexError, "Tileset index %d out of range (0..%d)",
            index, (int)self->data->tilesets.size() - 1);
        return NULL;
    }

    const auto& ref = self->data->tilesets[index];

    // Create a TileSetFile wrapping the existing parsed data
    auto* ts_type = &mcrfpydef::PyTileSetFileType;
    auto* ts = (PyTileSetFileObject*)ts_type->tp_alloc(ts_type, 0);
    if (!ts) return NULL;
    new (&ts->data) std::shared_ptr<TileSetData>(ref.tileset);

    // Return (firstgid, TileSetFile)
    PyObject* result = Py_BuildValue("(iN)", ref.firstgid, (PyObject*)ts);
    return result;
}

PyObject* PyTileMapFile::tile_layer_data(PyTileMapFileObject* self, PyObject* args) {
    const char* name;
    if (!PyArg_ParseTuple(args, "s", &name))
        return NULL;

    for (const auto& tl : self->data->tile_layers) {
        if (tl.name == name) {
            PyObject* list = PyList_New(tl.global_gids.size());
            if (!list) return NULL;
            for (size_t i = 0; i < tl.global_gids.size(); i++) {
                PyList_SET_ITEM(list, i, PyLong_FromUnsignedLong(tl.global_gids[i]));
            }
            return list;
        }
    }

    PyErr_Format(PyExc_KeyError, "No tile layer named '%s'", name);
    return NULL;
}

PyObject* PyTileMapFile::resolve_gid(PyTileMapFileObject* self, PyObject* args) {
    unsigned int gid;
    if (!PyArg_ParseTuple(args, "I", &gid))
        return NULL;

    if (gid == 0) {
        // GID 0 = empty tile
        return Py_BuildValue("(ii)", -1, -1);
    }

    // Strip flip flags (top 3 bits of a 32-bit GID)
    uint32_t clean_gid = gid & 0x1FFFFFFF;

    // Find which tileset this GID belongs to (tilesets sorted by firstgid)
    int ts_index = -1;
    for (int i = (int)self->data->tilesets.size() - 1; i >= 0; i--) {
        if (clean_gid >= (uint32_t)self->data->tilesets[i].firstgid) {
            ts_index = i;
            break;
        }
    }

    if (ts_index < 0) {
        return Py_BuildValue("(ii)", -1, -1);
    }

    int local_id = clean_gid - self->data->tilesets[ts_index].firstgid;
    return Py_BuildValue("(ii)", ts_index, local_id);
}

PyObject* PyTileMapFile::object_layer(PyTileMapFileObject* self, PyObject* args) {
    const char* name;
    if (!PyArg_ParseTuple(args, "s", &name))
        return NULL;

    for (const auto& ol : self->data->object_layers) {
        if (ol.name == name) {
            return jsonToPython(ol.objects);
        }
    }

    PyErr_Format(PyExc_KeyError, "No object layer named '%s'", name);
    return NULL;
}

PyObject* PyTileMapFile::apply_to_tile_layer(PyTileMapFileObject* self, PyObject* args, PyObject* kwds) {
    static const char* keywords[] = {"tile_layer", "layer_name", "tileset_index", nullptr};
    PyObject* tlayer_obj;
    const char* layer_name;
    int tileset_index = 0;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "Os|i", const_cast<char**>(keywords),
                                      &tlayer_obj, &layer_name, &tileset_index))
        return NULL;

    // Validate TileLayer
    // Check type by name since PyTileLayerType is static-per-TU
    const char* type_name = Py_TYPE(tlayer_obj)->tp_name;
    if (!type_name || strcmp(type_name, "mcrfpy.TileLayer") != 0) {
        PyErr_SetString(PyExc_TypeError, "First argument must be a TileLayer");
        return NULL;
    }

    // Find the tile layer data
    const TileLayerData* tld = nullptr;
    for (const auto& tl : self->data->tile_layers) {
        if (tl.name == layer_name) {
            tld = &tl;
            break;
        }
    }
    if (!tld) {
        PyErr_Format(PyExc_KeyError, "No tile layer named '%s'", layer_name);
        return NULL;
    }

    if (tileset_index < 0 || tileset_index >= (int)self->data->tilesets.size()) {
        PyErr_Format(PyExc_IndexError, "Tileset index %d out of range", tileset_index);
        return NULL;
    }

    int firstgid = self->data->tilesets[tileset_index].firstgid;
    auto* tlayer = (PyTileLayerObject*)tlayer_obj;

    int w = tld->width;
    int h = tld->height;
    for (int y = 0; y < h && y < tlayer->data->grid_y; y++) {
        for (int x = 0; x < w && x < tlayer->data->grid_x; x++) {
            uint32_t gid = tld->global_gids[y * w + x];
            if (gid == 0) {
                tlayer->data->at(x, y) = -1; // empty
                continue;
            }
            uint32_t clean_gid = gid & 0x1FFFFFFF;
            int local_id = static_cast<int>(clean_gid) - firstgid;
            if (local_id >= 0) {
                tlayer->data->at(x, y) = local_id;
            }
        }
    }
    tlayer->data->markDirty();

    Py_RETURN_NONE;
}

// ============================================================
// Method/GetSet tables
// ============================================================

PyMethodDef PyTileMapFile::methods[] = {
    {"tileset", (PyCFunction)PyTileMapFile::tileset, METH_VARARGS,
     MCRF_METHOD(TileMapFile, tileset,
         MCRF_SIG("(index: int)", "tuple[int, TileSetFile]"),
         MCRF_DESC("Get a referenced tileset by index."),
         MCRF_ARGS_START
         MCRF_ARG("index", "Tileset index (0-based)")
         MCRF_RETURNS("Tuple of (firstgid, TileSetFile).")
     )},
    {"tile_layer_data", (PyCFunction)PyTileMapFile::tile_layer_data, METH_VARARGS,
     MCRF_METHOD(TileMapFile, tile_layer_data,
         MCRF_SIG("(name: str)", "list[int]"),
         MCRF_DESC("Get raw global GID data for a tile layer."),
         MCRF_ARGS_START
         MCRF_ARG("name", "Name of the tile layer")
         MCRF_RETURNS("Flat list of global GIDs (0 = empty tile).")
         MCRF_RAISES("KeyError", "If no tile layer with that name exists")
     )},
    {"resolve_gid", (PyCFunction)PyTileMapFile::resolve_gid, METH_VARARGS,
     MCRF_METHOD(TileMapFile, resolve_gid,
         MCRF_SIG("(gid: int)", "tuple[int, int]"),
         MCRF_DESC("Resolve a global tile ID to tileset index and local tile ID."),
         MCRF_ARGS_START
         MCRF_ARG("gid", "Global tile ID from tile_layer_data()")
         MCRF_RETURNS("Tuple of (tileset_index, local_tile_id). (-1, -1) for empty/invalid.")
     )},
    {"object_layer", (PyCFunction)PyTileMapFile::object_layer, METH_VARARGS,
     MCRF_METHOD(TileMapFile, object_layer,
         MCRF_SIG("(name: str)", "list[dict]"),
         MCRF_DESC("Get objects from an object layer as Python dicts."),
         MCRF_ARGS_START
         MCRF_ARG("name", "Name of the object layer")
         MCRF_RETURNS("List of dicts with object properties (id, name, x, y, width, height, etc.).")
         MCRF_RAISES("KeyError", "If no object layer with that name exists")
     )},
    {"apply_to_tile_layer", (PyCFunction)PyTileMapFile::apply_to_tile_layer, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(TileMapFile, apply_to_tile_layer,
         MCRF_SIG("(tile_layer: TileLayer, layer_name: str, tileset_index: int = 0)", "None"),
         MCRF_DESC("Resolve GIDs and write sprite indices into a TileLayer."),
         MCRF_ARGS_START
         MCRF_ARG("tile_layer", "Target TileLayer to write into")
         MCRF_ARG("layer_name", "Name of the tile layer in this map")
         MCRF_ARG("tileset_index", "Which tileset to resolve GIDs against (default 0)")
     )},
    {NULL}
};

PyGetSetDef PyTileMapFile::getsetters[] = {
    {"width", (getter)PyTileMapFile::get_width, NULL,
     MCRF_PROPERTY(width, "Map width in tiles (int, read-only)."), NULL},
    {"height", (getter)PyTileMapFile::get_height, NULL,
     MCRF_PROPERTY(height, "Map height in tiles (int, read-only)."), NULL},
    {"tile_width", (getter)PyTileMapFile::get_tile_width, NULL,
     MCRF_PROPERTY(tile_width, "Tile width in pixels (int, read-only)."), NULL},
    {"tile_height", (getter)PyTileMapFile::get_tile_height, NULL,
     MCRF_PROPERTY(tile_height, "Tile height in pixels (int, read-only)."), NULL},
    {"orientation", (getter)PyTileMapFile::get_orientation, NULL,
     MCRF_PROPERTY(orientation, "Map orientation, e.g. 'orthogonal' (str, read-only)."), NULL},
    {"properties", (getter)PyTileMapFile::get_properties, NULL,
     MCRF_PROPERTY(properties, "Custom map properties as a dict (read-only)."), NULL},
    {"tileset_count", (getter)PyTileMapFile::get_tileset_count, NULL,
     MCRF_PROPERTY(tileset_count, "Number of referenced tilesets (int, read-only)."), NULL},
    {"tile_layer_names", (getter)PyTileMapFile::get_tile_layer_names, NULL,
     MCRF_PROPERTY(tile_layer_names, "List of tile layer names (read-only)."), NULL},
    {"object_layer_names", (getter)PyTileMapFile::get_object_layer_names, NULL,
     MCRF_PROPERTY(object_layer_names, "List of object layer names (read-only)."), NULL},
    {NULL}
};
