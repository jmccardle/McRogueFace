#include "PyLdtkProject.h"
#include "LdtkParse.h"
#include "PyAutoRuleSet.h"
#include "PyTileSetFile.h"  // For PyTileSetFileObject
#include "McRFPy_Doc.h"
#include "TiledParse.h"    // For jsonToPython()
#include "PyTexture.h"
#include <cstring>

using namespace mcrf::ldtk;

// ============================================================
// Type lifecycle
// ============================================================

PyObject* PyLdtkProject::pynew(PyTypeObject* type, PyObject* args, PyObject* kwds) {
    auto* self = (PyLdtkProjectObject*)type->tp_alloc(type, 0);
    if (self) {
        new (&self->data) std::shared_ptr<LdtkProjectData>();
    }
    return (PyObject*)self;
}

int PyLdtkProject::init(PyLdtkProjectObject* self, PyObject* args, PyObject* kwds) {
    static const char* keywords[] = {"path", nullptr};
    const char* path = nullptr;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "s", const_cast<char**>(keywords), &path))
        return -1;

    try {
        self->data = loadLdtkProject(path);
    } catch (const std::exception& e) {
        PyErr_Format(PyExc_IOError, "Failed to load LDtk project: %s", e.what());
        return -1;
    }

    return 0;
}

void PyLdtkProject::dealloc(PyLdtkProjectObject* self) {
    self->data.~shared_ptr();
    Py_TYPE(self)->tp_free((PyObject*)self);
}

PyObject* PyLdtkProject::repr(PyObject* obj) {
    auto* self = (PyLdtkProjectObject*)obj;
    if (!self->data) {
        return PyUnicode_FromString("<LdtkProject (uninitialized)>");
    }
    return PyUnicode_FromFormat("<LdtkProject v%s tilesets=%d rulesets=%d levels=%d>",
        self->data->json_version.c_str(),
        (int)self->data->tilesets.size(),
        (int)self->data->rulesets.size(),
        (int)self->data->levels.size());
}

// ============================================================
// Properties (all read-only)
// ============================================================

PyObject* PyLdtkProject::get_version(PyLdtkProjectObject* self, void*) {
    return PyUnicode_FromString(self->data->json_version.c_str());
}

PyObject* PyLdtkProject::get_tileset_names(PyLdtkProjectObject* self, void*) {
    PyObject* list = PyList_New(self->data->tilesets.size());
    if (!list) return NULL;
    for (size_t i = 0; i < self->data->tilesets.size(); i++) {
        PyList_SET_ITEM(list, i, PyUnicode_FromString(self->data->tilesets[i]->name.c_str()));
    }
    return list;
}

PyObject* PyLdtkProject::get_ruleset_names(PyLdtkProjectObject* self, void*) {
    PyObject* list = PyList_New(self->data->rulesets.size());
    if (!list) return NULL;
    for (size_t i = 0; i < self->data->rulesets.size(); i++) {
        PyList_SET_ITEM(list, i, PyUnicode_FromString(self->data->rulesets[i].name.c_str()));
    }
    return list;
}

PyObject* PyLdtkProject::get_level_names(PyLdtkProjectObject* self, void*) {
    PyObject* list = PyList_New(self->data->levels.size());
    if (!list) return NULL;
    for (size_t i = 0; i < self->data->levels.size(); i++) {
        PyList_SET_ITEM(list, i, PyUnicode_FromString(self->data->levels[i].name.c_str()));
    }
    return list;
}

PyObject* PyLdtkProject::get_enums(PyLdtkProjectObject* self, void*) {
    return mcrf::tiled::jsonToPython(self->data->enums);
}

// ============================================================
// Methods
// ============================================================

PyObject* PyLdtkProject::tileset(PyLdtkProjectObject* self, PyObject* args) {
    const char* name = nullptr;
    if (!PyArg_ParseTuple(args, "s", &name))
        return NULL;

    for (size_t i = 0; i < self->data->tilesets.size(); i++) {
        if (self->data->tilesets[i]->name == name) {
            // Return a TileSetFile-compatible object
            // We create a PyTileSetFileObject wrapping our existing TileSetData
            PyObject* mcrfpy_module = PyImport_ImportModule("mcrfpy");
            if (!mcrfpy_module) return NULL;

            PyObject* tsf_type = PyObject_GetAttrString(mcrfpy_module, "TileSetFile");
            Py_DECREF(mcrfpy_module);
            if (!tsf_type) return NULL;

            // Allocate without calling init (we set data directly)
            PyObject* tsf_obj = ((PyTypeObject*)tsf_type)->tp_alloc((PyTypeObject*)tsf_type, 0);
            Py_DECREF(tsf_type);
            if (!tsf_obj) return NULL;

            // Construct the shared_ptr in place using the proper type
            auto* tsf = (PyTileSetFileObject*)tsf_obj;
            new (&tsf->data) std::shared_ptr<mcrf::tiled::TileSetData>(self->data->tilesets[i]);

            return tsf_obj;
        }
    }

    PyErr_Format(PyExc_KeyError, "No tileset named '%s'", name);
    return NULL;
}

PyObject* PyLdtkProject::ruleset(PyLdtkProjectObject* self, PyObject* args) {
    const char* name = nullptr;
    if (!PyArg_ParseTuple(args, "s", &name))
        return NULL;

    for (size_t i = 0; i < self->data->rulesets.size(); i++) {
        if (self->data->rulesets[i].name == name) {
            return PyAutoRuleSet::create(self->data, static_cast<int>(i));
        }
    }

    PyErr_Format(PyExc_KeyError, "No ruleset named '%s'", name);
    return NULL;
}

PyObject* PyLdtkProject::level(PyLdtkProjectObject* self, PyObject* args) {
    const char* name = nullptr;
    if (!PyArg_ParseTuple(args, "s", &name))
        return NULL;

    for (size_t i = 0; i < self->data->levels.size(); i++) {
        const auto& lvl = self->data->levels[i];
        if (lvl.name == name) {
            // Build Python dict representing the level
            PyObject* dict = PyDict_New();
            if (!dict) return NULL;

            PyObject* py_name = PyUnicode_FromString(lvl.name.c_str());
            PyDict_SetItemString(dict, "name", py_name);
            Py_DECREF(py_name);

            PyObject* py_w = PyLong_FromLong(lvl.width_px);
            PyDict_SetItemString(dict, "width_px", py_w);
            Py_DECREF(py_w);

            PyObject* py_h = PyLong_FromLong(lvl.height_px);
            PyDict_SetItemString(dict, "height_px", py_h);
            Py_DECREF(py_h);

            PyObject* py_wx = PyLong_FromLong(lvl.worldX);
            PyDict_SetItemString(dict, "world_x", py_wx);
            Py_DECREF(py_wx);

            PyObject* py_wy = PyLong_FromLong(lvl.worldY);
            PyDict_SetItemString(dict, "world_y", py_wy);
            Py_DECREF(py_wy);

            // Build layers list
            PyObject* layers_list = PyList_New(lvl.layers.size());
            if (!layers_list) { Py_DECREF(dict); return NULL; }

            for (size_t j = 0; j < lvl.layers.size(); j++) {
                const auto& layer = lvl.layers[j];
                PyObject* layer_dict = PyDict_New();
                if (!layer_dict) { Py_DECREF(layers_list); Py_DECREF(dict); return NULL; }

                PyObject* ln = PyUnicode_FromString(layer.name.c_str());
                PyDict_SetItemString(layer_dict, "name", ln);
                Py_DECREF(ln);

                PyObject* lt = PyUnicode_FromString(layer.type.c_str());
                PyDict_SetItemString(layer_dict, "type", lt);
                Py_DECREF(lt);

                PyObject* lw = PyLong_FromLong(layer.width);
                PyDict_SetItemString(layer_dict, "width", lw);
                Py_DECREF(lw);

                PyObject* lh = PyLong_FromLong(layer.height);
                PyDict_SetItemString(layer_dict, "height", lh);
                Py_DECREF(lh);

                // IntGrid data
                if (!layer.intgrid.empty()) {
                    PyObject* ig = PyList_New(layer.intgrid.size());
                    for (size_t k = 0; k < layer.intgrid.size(); k++) {
                        PyList_SET_ITEM(ig, k, PyLong_FromLong(layer.intgrid[k]));
                    }
                    PyDict_SetItemString(layer_dict, "intgrid", ig);
                    Py_DECREF(ig);
                } else {
                    PyObject* ig = PyList_New(0);
                    PyDict_SetItemString(layer_dict, "intgrid", ig);
                    Py_DECREF(ig);
                }

                // Auto tiles
                auto tile_to_dict = [](const PrecomputedTile& t) -> PyObject* {
                    return Py_BuildValue("{s:i, s:i, s:i, s:i, s:f}",
                        "tile_id", t.tile_id,
                        "x", t.grid_x,
                        "y", t.grid_y,
                        "flip", t.flip,
                        "alpha", (double)t.alpha);
                };

                PyObject* auto_list = PyList_New(layer.auto_tiles.size());
                for (size_t k = 0; k < layer.auto_tiles.size(); k++) {
                    PyList_SET_ITEM(auto_list, k, tile_to_dict(layer.auto_tiles[k]));
                }
                PyDict_SetItemString(layer_dict, "auto_tiles", auto_list);
                Py_DECREF(auto_list);

                PyObject* grid_list = PyList_New(layer.grid_tiles.size());
                for (size_t k = 0; k < layer.grid_tiles.size(); k++) {
                    PyList_SET_ITEM(grid_list, k, tile_to_dict(layer.grid_tiles[k]));
                }
                PyDict_SetItemString(layer_dict, "grid_tiles", grid_list);
                Py_DECREF(grid_list);

                // Entity instances
                if (!layer.entities.is_null()) {
                    PyObject* ents = mcrf::tiled::jsonToPython(layer.entities);
                    PyDict_SetItemString(layer_dict, "entities", ents);
                    Py_DECREF(ents);
                } else {
                    PyObject* ents = PyList_New(0);
                    PyDict_SetItemString(layer_dict, "entities", ents);
                    Py_DECREF(ents);
                }

                PyList_SET_ITEM(layers_list, j, layer_dict);
            }

            PyDict_SetItemString(dict, "layers", layers_list);
            Py_DECREF(layers_list);

            return dict;
        }
    }

    PyErr_Format(PyExc_KeyError, "No level named '%s'", name);
    return NULL;
}

// ============================================================
// Method/GetSet tables
// ============================================================

PyMethodDef PyLdtkProject::methods[] = {
    {"tileset", (PyCFunction)PyLdtkProject::tileset, METH_VARARGS,
     MCRF_METHOD(LdtkProject, tileset,
         MCRF_SIG("(name: str)", "TileSetFile"),
         MCRF_DESC("Get a tileset by name."),
         MCRF_ARGS_START
         MCRF_ARG("name", "Tileset identifier from the LDtk project")
         MCRF_RETURNS("A TileSetFile object for texture creation and tile metadata.")
         MCRF_RAISES("KeyError", "If no tileset with the given name exists")
     )},
    {"ruleset", (PyCFunction)PyLdtkProject::ruleset, METH_VARARGS,
     MCRF_METHOD(LdtkProject, ruleset,
         MCRF_SIG("(name: str)", "AutoRuleSet"),
         MCRF_DESC("Get an auto-rule set by layer name."),
         MCRF_ARGS_START
         MCRF_ARG("name", "Layer identifier from the LDtk project")
         MCRF_RETURNS("An AutoRuleSet for resolving IntGrid data to sprite tiles.")
         MCRF_RAISES("KeyError", "If no ruleset with the given name exists")
     )},
    {"level", (PyCFunction)PyLdtkProject::level, METH_VARARGS,
     MCRF_METHOD(LdtkProject, level,
         MCRF_SIG("(name: str)", "dict"),
         MCRF_DESC("Get level data by name."),
         MCRF_ARGS_START
         MCRF_ARG("name", "Level identifier from the LDtk project")
         MCRF_RETURNS("Dict with name, dimensions, world position, and layer data.")
         MCRF_RAISES("KeyError", "If no level with the given name exists")
     )},
    {NULL}
};

PyGetSetDef PyLdtkProject::getsetters[] = {
    {"version", (getter)PyLdtkProject::get_version, NULL,
     MCRF_PROPERTY(version, "LDtk JSON format version string (str, read-only)."), NULL},
    {"tileset_names", (getter)PyLdtkProject::get_tileset_names, NULL,
     MCRF_PROPERTY(tileset_names, "List of tileset identifier names (list[str], read-only)."), NULL},
    {"ruleset_names", (getter)PyLdtkProject::get_ruleset_names, NULL,
     MCRF_PROPERTY(ruleset_names, "List of rule set / layer names (list[str], read-only)."), NULL},
    {"level_names", (getter)PyLdtkProject::get_level_names, NULL,
     MCRF_PROPERTY(level_names, "List of level identifier names (list[str], read-only)."), NULL},
    {"enums", (getter)PyLdtkProject::get_enums, NULL,
     MCRF_PROPERTY(enums, "Enum definitions from the project as a list of dicts (read-only)."), NULL},
    {NULL}
};
