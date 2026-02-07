#include "PyWangSet.h"
#include "TiledParse.h"
#include "WangResolve.h"
#include "McRFPy_Doc.h"
#include "PyDiscreteMap.h"
#include "GridLayers.h"
#include <cstring>

using namespace mcrf::tiled;

// ============================================================
// Helper
// ============================================================

const WangSet& PyWangSet::getWangSet(PyWangSetObject* self) {
    return self->parent->wang_sets[self->wang_set_index];
}

// ============================================================
// Factory
// ============================================================

PyObject* PyWangSet::create(std::shared_ptr<TileSetData> parent, int index) {
    auto* type = &mcrfpydef::PyWangSetType;
    auto* self = (PyWangSetObject*)type->tp_alloc(type, 0);
    if (!self) return NULL;
    new (&self->parent) std::shared_ptr<TileSetData>(parent);
    self->wang_set_index = index;
    return (PyObject*)self;
}

// ============================================================
// Type lifecycle
// ============================================================

void PyWangSet::dealloc(PyWangSetObject* self) {
    self->parent.~shared_ptr();
    Py_TYPE(self)->tp_free((PyObject*)self);
}

PyObject* PyWangSet::repr(PyObject* obj) {
    auto* self = (PyWangSetObject*)obj;
    const auto& ws = getWangSet(self);
    const char* type_str = "unknown";
    switch (ws.type) {
        case WangSetType::Corner: type_str = "corner"; break;
        case WangSetType::Edge:   type_str = "edge"; break;
        case WangSetType::Mixed:  type_str = "mixed"; break;
    }
    return PyUnicode_FromFormat("<WangSet '%s' type='%s' colors=%d>",
        ws.name.c_str(), type_str, (int)ws.colors.size());
}

// ============================================================
// Properties
// ============================================================

PyObject* PyWangSet::get_name(PyWangSetObject* self, void*) {
    return PyUnicode_FromString(getWangSet(self).name.c_str());
}

PyObject* PyWangSet::get_type(PyWangSetObject* self, void*) {
    switch (getWangSet(self).type) {
        case WangSetType::Corner: return PyUnicode_FromString("corner");
        case WangSetType::Edge:   return PyUnicode_FromString("edge");
        case WangSetType::Mixed:  return PyUnicode_FromString("mixed");
    }
    return PyUnicode_FromString("unknown");
}

PyObject* PyWangSet::get_color_count(PyWangSetObject* self, void*) {
    return PyLong_FromLong(getWangSet(self).colors.size());
}

PyObject* PyWangSet::get_colors(PyWangSetObject* self, void*) {
    const auto& ws = getWangSet(self);
    PyObject* list = PyList_New(ws.colors.size());
    if (!list) return NULL;

    for (size_t i = 0; i < ws.colors.size(); i++) {
        const auto& wc = ws.colors[i];
        PyObject* dict = Py_BuildValue("{s:s, s:i, s:i, s:f}",
            "name", wc.name.c_str(),
            "index", wc.index,
            "tile_id", wc.tile_id,
            "probability", (double)wc.probability);
        if (!dict) {
            Py_DECREF(list);
            return NULL;
        }
        PyList_SET_ITEM(list, i, dict);
    }
    return list;
}

// ============================================================
// Methods
// ============================================================

// Convert a name like "Grass Terrain" to "GRASS_TERRAIN"
static std::string toUpperSnakeCase(const std::string& s) {
    std::string result;
    result.reserve(s.size());
    for (size_t i = 0; i < s.size(); i++) {
        char c = s[i];
        if (c == ' ' || c == '-') {
            result += '_';
        } else {
            result += static_cast<char>(toupper(static_cast<unsigned char>(c)));
        }
    }
    return result;
}

PyObject* PyWangSet::terrain_enum(PyWangSetObject* self, PyObject*) {
    const auto& ws = getWangSet(self);

    // Import IntEnum from enum module
    PyObject* enum_module = PyImport_ImportModule("enum");
    if (!enum_module) return NULL;

    PyObject* int_enum = PyObject_GetAttrString(enum_module, "IntEnum");
    Py_DECREF(enum_module);
    if (!int_enum) return NULL;

    // Build members dict: NONE=0, then each color
    PyObject* members = PyDict_New();
    if (!members) { Py_DECREF(int_enum); return NULL; }

    // NONE = 0 (unset terrain)
    PyObject* zero = PyLong_FromLong(0);
    PyDict_SetItemString(members, "NONE", zero);
    Py_DECREF(zero);

    for (const auto& wc : ws.colors) {
        std::string key = toUpperSnakeCase(wc.name);
        PyObject* val = PyLong_FromLong(wc.index);
        PyDict_SetItemString(members, key.c_str(), val);
        Py_DECREF(val);
    }

    // Create enum class: IntEnum(ws.name, members)
    PyObject* name = PyUnicode_FromString(ws.name.c_str());
    PyObject* args = PyTuple_Pack(2, name, members);
    Py_DECREF(name);
    Py_DECREF(members);

    PyObject* enum_class = PyObject_Call(int_enum, args, NULL);
    Py_DECREF(args);
    Py_DECREF(int_enum);

    return enum_class;
}

PyObject* PyWangSet::resolve(PyWangSetObject* self, PyObject* args) {
    PyObject* dmap_obj;
    if (!PyArg_ParseTuple(args, "O", &dmap_obj))
        return NULL;

    // Check type by name since static types differ per translation unit
    const char* dmap_type_name = Py_TYPE(dmap_obj)->tp_name;
    if (!dmap_type_name || strcmp(dmap_type_name, "mcrfpy.DiscreteMap") != 0) {
        PyErr_SetString(PyExc_TypeError, "Expected a DiscreteMap object");
        return NULL;
    }

    auto* dmap = (PyDiscreteMapObject*)dmap_obj;
    const auto& ws = getWangSet(self);

    std::vector<int> result = resolveWangTerrain(dmap->values, dmap->w, dmap->h, ws);

    // Convert to Python list
    PyObject* list = PyList_New(result.size());
    if (!list) return NULL;
    for (size_t i = 0; i < result.size(); i++) {
        PyList_SET_ITEM(list, i, PyLong_FromLong(result[i]));
    }
    return list;
}

PyObject* PyWangSet::apply(PyWangSetObject* self, PyObject* args, PyObject* kwds) {
    static const char* keywords[] = {"discrete_map", "tile_layer", nullptr};
    PyObject* dmap_obj;
    PyObject* tlayer_obj;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO", const_cast<char**>(keywords),
                                      &dmap_obj, &tlayer_obj))
        return NULL;

    // Validate DiscreteMap (check by name since static types differ per TU)
    const char* dmap_tn = Py_TYPE(dmap_obj)->tp_name;
    if (!dmap_tn || strcmp(dmap_tn, "mcrfpy.DiscreteMap") != 0) {
        PyErr_SetString(PyExc_TypeError, "First argument must be a DiscreteMap");
        return NULL;
    }

    // Validate TileLayer
    const char* tl_tn = Py_TYPE(tlayer_obj)->tp_name;
    if (!tl_tn || strcmp(tl_tn, "mcrfpy.TileLayer") != 0) {
        PyErr_SetString(PyExc_TypeError, "Second argument must be a TileLayer");
        return NULL;
    }

    auto* dmap = (PyDiscreteMapObject*)dmap_obj;
    auto* tlayer = (PyTileLayerObject*)tlayer_obj;
    const auto& ws = getWangSet(self);

    // Resolve terrain to tile indices
    std::vector<int> tile_ids = resolveWangTerrain(dmap->values, dmap->w, dmap->h, ws);

    // Write into TileLayer
    int w = dmap->w;
    int h = dmap->h;
    for (int y = 0; y < h && y < tlayer->data->grid_y; y++) {
        for (int x = 0; x < w && x < tlayer->data->grid_x; x++) {
            int tid = tile_ids[y * w + x];
            if (tid >= 0) {
                tlayer->data->at(x, y) = tid;
            }
        }
    }
    tlayer->data->markDirty();

    Py_RETURN_NONE;
}

// ============================================================
// Method/GetSet tables
// ============================================================

PyMethodDef PyWangSet::methods[] = {
    {"terrain_enum", (PyCFunction)PyWangSet::terrain_enum, METH_NOARGS,
     MCRF_METHOD(WangSet, terrain_enum,
         MCRF_SIG("()", "IntEnum"),
         MCRF_DESC("Generate a Python IntEnum from this WangSet's terrain colors."),
         MCRF_RETURNS("IntEnum class with NONE=0 and one member per color (UPPER_SNAKE_CASE).")
     )},
    {"resolve", (PyCFunction)PyWangSet::resolve, METH_VARARGS,
     MCRF_METHOD(WangSet, resolve,
         MCRF_SIG("(discrete_map: DiscreteMap)", "list[int]"),
         MCRF_DESC("Resolve terrain data to tile indices using Wang tile rules."),
         MCRF_ARGS_START
         MCRF_ARG("discrete_map", "A DiscreteMap with terrain IDs matching this WangSet's colors")
         MCRF_RETURNS("List of tile IDs (one per cell). -1 means no matching Wang tile.")
     )},
    {"apply", (PyCFunction)PyWangSet::apply, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(WangSet, apply,
         MCRF_SIG("(discrete_map: DiscreteMap, tile_layer: TileLayer)", "None"),
         MCRF_DESC("Resolve terrain and write tile indices directly into a TileLayer."),
         MCRF_ARGS_START
         MCRF_ARG("discrete_map", "A DiscreteMap with terrain IDs")
         MCRF_ARG("tile_layer", "Target TileLayer to write resolved tiles into")
     )},
    {NULL}
};

PyGetSetDef PyWangSet::getsetters[] = {
    {"name", (getter)PyWangSet::get_name, NULL,
     MCRF_PROPERTY(name, "Wang set name (str, read-only)."), NULL},
    {"type", (getter)PyWangSet::get_type, NULL,
     MCRF_PROPERTY(type, "Wang set type: 'corner', 'edge', or 'mixed' (str, read-only)."), NULL},
    {"color_count", (getter)PyWangSet::get_color_count, NULL,
     MCRF_PROPERTY(color_count, "Number of terrain colors (int, read-only)."), NULL},
    {"colors", (getter)PyWangSet::get_colors, NULL,
     MCRF_PROPERTY(colors, "List of color dicts with name, index, tile_id, probability (read-only)."), NULL},
    {NULL}
};
