#include "PyAutoRuleSet.h"
#include "AutoRuleResolve.h"
#include "McRFPy_Doc.h"
#include "PyDiscreteMap.h"
#include "GridLayers.h"
#include <cstring>

using namespace mcrf::ldtk;

// ============================================================
// Helper
// ============================================================

const AutoRuleSet& PyAutoRuleSet::getRuleSet(PyAutoRuleSetObject* self) {
    return self->parent->rulesets[self->ruleset_index];
}

// ============================================================
// Factory
// ============================================================

PyObject* PyAutoRuleSet::create(std::shared_ptr<LdtkProjectData> parent, int index) {
    auto* type = &mcrfpydef::PyAutoRuleSetType;
    auto* self = (PyAutoRuleSetObject*)type->tp_alloc(type, 0);
    if (!self) return NULL;
    new (&self->parent) std::shared_ptr<LdtkProjectData>(parent);
    self->ruleset_index = index;
    return (PyObject*)self;
}

// ============================================================
// Type lifecycle
// ============================================================

void PyAutoRuleSet::dealloc(PyAutoRuleSetObject* self) {
    self->parent.~shared_ptr();
    Py_TYPE(self)->tp_free((PyObject*)self);
}

PyObject* PyAutoRuleSet::repr(PyObject* obj) {
    auto* self = (PyAutoRuleSetObject*)obj;
    const auto& rs = getRuleSet(self);
    int total_rules = 0;
    for (const auto& g : rs.groups) total_rules += g.rules.size();
    return PyUnicode_FromFormat("<AutoRuleSet '%s' values=%d rules=%d groups=%d>",
        rs.name.c_str(), (int)rs.intgrid_values.size(),
        total_rules, (int)rs.groups.size());
}

// ============================================================
// Properties
// ============================================================

PyObject* PyAutoRuleSet::get_name(PyAutoRuleSetObject* self, void*) {
    return PyUnicode_FromString(getRuleSet(self).name.c_str());
}

PyObject* PyAutoRuleSet::get_grid_size(PyAutoRuleSetObject* self, void*) {
    return PyLong_FromLong(getRuleSet(self).gridSize);
}

PyObject* PyAutoRuleSet::get_value_count(PyAutoRuleSetObject* self, void*) {
    return PyLong_FromLong(getRuleSet(self).intgrid_values.size());
}

PyObject* PyAutoRuleSet::get_values(PyAutoRuleSetObject* self, void*) {
    const auto& rs = getRuleSet(self);
    PyObject* list = PyList_New(rs.intgrid_values.size());
    if (!list) return NULL;

    for (size_t i = 0; i < rs.intgrid_values.size(); i++) {
        const auto& v = rs.intgrid_values[i];
        PyObject* dict = Py_BuildValue("{s:i, s:s}",
            "value", v.value,
            "name", v.name.c_str());
        if (!dict) {
            Py_DECREF(list);
            return NULL;
        }
        PyList_SET_ITEM(list, i, dict);
    }
    return list;
}

PyObject* PyAutoRuleSet::get_rule_count(PyAutoRuleSetObject* self, void*) {
    const auto& rs = getRuleSet(self);
    int total = 0;
    for (const auto& g : rs.groups) total += g.rules.size();
    return PyLong_FromLong(total);
}

PyObject* PyAutoRuleSet::get_group_count(PyAutoRuleSetObject* self, void*) {
    return PyLong_FromLong(getRuleSet(self).groups.size());
}

// ============================================================
// Methods
// ============================================================

// Convert a name like "grass_terrain" or "Grass Terrain" to "GRASS_TERRAIN"
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

PyObject* PyAutoRuleSet::terrain_enum(PyAutoRuleSetObject* self, PyObject*) {
    const auto& rs = getRuleSet(self);

    // Import IntEnum from enum module
    PyObject* enum_module = PyImport_ImportModule("enum");
    if (!enum_module) return NULL;

    PyObject* int_enum = PyObject_GetAttrString(enum_module, "IntEnum");
    Py_DECREF(enum_module);
    if (!int_enum) return NULL;

    // Build members dict: NONE=0, then each IntGrid value
    PyObject* members = PyDict_New();
    if (!members) { Py_DECREF(int_enum); return NULL; }

    // NONE = 0 (empty terrain)
    PyObject* zero = PyLong_FromLong(0);
    PyDict_SetItemString(members, "NONE", zero);
    Py_DECREF(zero);

    for (const auto& v : rs.intgrid_values) {
        std::string key = toUpperSnakeCase(v.name);
        if (key.empty()) {
            // Fallback name for unnamed values
            key = "VALUE_" + std::to_string(v.value);
        }
        PyObject* val = PyLong_FromLong(v.value);
        PyDict_SetItemString(members, key.c_str(), val);
        Py_DECREF(val);
    }

    // Create enum class: IntEnum(rs.name, members)
    PyObject* name = PyUnicode_FromString(rs.name.c_str());
    PyObject* args = PyTuple_Pack(2, name, members);
    Py_DECREF(name);
    Py_DECREF(members);

    PyObject* enum_class = PyObject_Call(int_enum, args, NULL);
    Py_DECREF(args);
    Py_DECREF(int_enum);

    return enum_class;
}

PyObject* PyAutoRuleSet::resolve(PyAutoRuleSetObject* self, PyObject* args, PyObject* kwds) {
    static const char* keywords[] = {"discrete_map", "seed", nullptr};
    PyObject* dmap_obj;
    unsigned int seed = 0;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|I",
                                      const_cast<char**>(keywords),
                                      &dmap_obj, &seed))
        return NULL;

    // Validate DiscreteMap
    const char* dmap_type_name = Py_TYPE(dmap_obj)->tp_name;
    if (!dmap_type_name || strcmp(dmap_type_name, "mcrfpy.DiscreteMap") != 0) {
        PyErr_SetString(PyExc_TypeError, "Expected a DiscreteMap object");
        return NULL;
    }

    auto* dmap = (PyDiscreteMapObject*)dmap_obj;
    const auto& rs = getRuleSet(self);

    // Convert uint8 DiscreteMap to int array for resolution
    int w = dmap->w;
    int h = dmap->h;
    std::vector<int> intgrid(w * h);
    for (int i = 0; i < w * h; i++) {
        intgrid[i] = static_cast<int>(dmap->values[i]);
    }

    std::vector<AutoTileResult> results = resolveAutoRules(intgrid.data(), w, h, rs, seed);

    // Convert to Python list of tile IDs (last-wins for stacked, simple mode)
    PyObject* list = PyList_New(results.size());
    if (!list) return NULL;
    for (size_t i = 0; i < results.size(); i++) {
        PyList_SET_ITEM(list, i, PyLong_FromLong(results[i].tile_id));
    }
    return list;
}

PyObject* PyAutoRuleSet::apply(PyAutoRuleSetObject* self, PyObject* args, PyObject* kwds) {
    static const char* keywords[] = {"discrete_map", "tile_layer", "seed", nullptr};
    PyObject* dmap_obj;
    PyObject* tlayer_obj;
    unsigned int seed = 0;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO|I",
                                      const_cast<char**>(keywords),
                                      &dmap_obj, &tlayer_obj, &seed))
        return NULL;

    // Validate DiscreteMap
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
    const auto& rs = getRuleSet(self);

    // Convert uint8 DiscreteMap to int array
    int w = dmap->w;
    int h = dmap->h;
    std::vector<int> intgrid(w * h);
    for (int i = 0; i < w * h; i++) {
        intgrid[i] = static_cast<int>(dmap->values[i]);
    }

    std::vector<AutoTileResult> results = resolveAutoRules(intgrid.data(), w, h, rs, seed);

    // Write into TileLayer, applying flip mapping if available
    for (int y = 0; y < h && y < tlayer->data->grid_y; y++) {
        for (int x = 0; x < w && x < tlayer->data->grid_x; x++) {
            int idx = y * w + x;
            int tid = results[idx].tile_id;
            int flip = results[idx].flip;

            if (tid >= 0) {
                if (flip != 0 && !rs.flip_mapping.empty()) {
                    // Look up expanded tile ID for flipped variant
                    uint32_t key = (static_cast<uint32_t>(tid) << 2) | (flip & 3);
                    auto it = rs.flip_mapping.find(key);
                    if (it != rs.flip_mapping.end()) {
                        tid = it->second;
                    }
                    // If no mapping found, use original tile (no flip)
                }
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

PyMethodDef PyAutoRuleSet::methods[] = {
    {"terrain_enum", (PyCFunction)PyAutoRuleSet::terrain_enum, METH_NOARGS,
     MCRF_METHOD(AutoRuleSet, terrain_enum,
         MCRF_SIG("()", "IntEnum"),
         MCRF_DESC("Generate a Python IntEnum from this rule set's IntGrid values."),
         MCRF_RETURNS("IntEnum class with NONE=0 and one member per IntGrid value (UPPER_SNAKE_CASE).")
     )},
    {"resolve", (PyCFunction)PyAutoRuleSet::resolve, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(AutoRuleSet, resolve,
         MCRF_SIG("(discrete_map: DiscreteMap, seed: int = 0)", "list[int]"),
         MCRF_DESC("Resolve IntGrid data to tile indices using LDtk auto-rules."),
         MCRF_ARGS_START
         MCRF_ARG("discrete_map", "A DiscreteMap with IntGrid values matching this rule set")
         MCRF_ARG("seed", "Random seed for deterministic tile selection and probability (default: 0)")
         MCRF_RETURNS("List of tile IDs (one per cell). -1 means no matching rule.")
     )},
    {"apply", (PyCFunction)PyAutoRuleSet::apply, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(AutoRuleSet, apply,
         MCRF_SIG("(discrete_map: DiscreteMap, tile_layer: TileLayer, seed: int = 0)", "None"),
         MCRF_DESC("Resolve auto-rules and write tile indices directly into a TileLayer."),
         MCRF_ARGS_START
         MCRF_ARG("discrete_map", "A DiscreteMap with IntGrid values")
         MCRF_ARG("tile_layer", "Target TileLayer to write resolved tiles into")
         MCRF_ARG("seed", "Random seed for deterministic results (default: 0)")
     )},
    {NULL}
};

PyGetSetDef PyAutoRuleSet::getsetters[] = {
    {"name", (getter)PyAutoRuleSet::get_name, NULL,
     MCRF_PROPERTY(name, "Rule set name / layer identifier (str, read-only)."), NULL},
    {"grid_size", (getter)PyAutoRuleSet::get_grid_size, NULL,
     MCRF_PROPERTY(grid_size, "Cell size in pixels (int, read-only)."), NULL},
    {"value_count", (getter)PyAutoRuleSet::get_value_count, NULL,
     MCRF_PROPERTY(value_count, "Number of IntGrid terrain values (int, read-only)."), NULL},
    {"values", (getter)PyAutoRuleSet::get_values, NULL,
     MCRF_PROPERTY(values, "List of IntGrid value dicts with value and name (read-only)."), NULL},
    {"rule_count", (getter)PyAutoRuleSet::get_rule_count, NULL,
     MCRF_PROPERTY(rule_count, "Total number of rules across all groups (int, read-only)."), NULL},
    {"group_count", (getter)PyAutoRuleSet::get_group_count, NULL,
     MCRF_PROPERTY(group_count, "Number of rule groups (int, read-only)."), NULL},
    {NULL}
};
