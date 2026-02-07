#include "PyTileSetFile.h"
#include "TiledParse.h"
#include "PyWangSet.h"
#include "McRFPy_Doc.h"

using namespace mcrf::tiled;

// ============================================================
// Type lifecycle
// ============================================================

PyObject* PyTileSetFile::pynew(PyTypeObject* type, PyObject* args, PyObject* kwds) {
    auto* self = (PyTileSetFileObject*)type->tp_alloc(type, 0);
    if (self) {
        new (&self->data) std::shared_ptr<TileSetData>();
    }
    return (PyObject*)self;
}

int PyTileSetFile::init(PyTileSetFileObject* self, PyObject* args, PyObject* kwds) {
    static const char* keywords[] = {"path", nullptr};
    const char* path = nullptr;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "s", const_cast<char**>(keywords), &path))
        return -1;

    try {
        self->data = loadTileSet(path);
    } catch (const std::exception& e) {
        PyErr_Format(PyExc_IOError, "Failed to load tileset: %s", e.what());
        return -1;
    }

    return 0;
}

void PyTileSetFile::dealloc(PyTileSetFileObject* self) {
    self->data.~shared_ptr();
    Py_TYPE(self)->tp_free((PyObject*)self);
}

PyObject* PyTileSetFile::repr(PyObject* obj) {
    auto* self = (PyTileSetFileObject*)obj;
    if (!self->data) {
        return PyUnicode_FromString("<TileSetFile (uninitialized)>");
    }
    return PyUnicode_FromFormat("<TileSetFile '%s' (%d tiles, %dx%d)>",
        self->data->name.c_str(), self->data->tile_count,
        self->data->tile_width, self->data->tile_height);
}

// ============================================================
// Properties (all read-only)
// ============================================================

PyObject* PyTileSetFile::get_name(PyTileSetFileObject* self, void*) {
    return PyUnicode_FromString(self->data->name.c_str());
}

PyObject* PyTileSetFile::get_tile_width(PyTileSetFileObject* self, void*) {
    return PyLong_FromLong(self->data->tile_width);
}

PyObject* PyTileSetFile::get_tile_height(PyTileSetFileObject* self, void*) {
    return PyLong_FromLong(self->data->tile_height);
}

PyObject* PyTileSetFile::get_tile_count(PyTileSetFileObject* self, void*) {
    return PyLong_FromLong(self->data->tile_count);
}

PyObject* PyTileSetFile::get_columns(PyTileSetFileObject* self, void*) {
    return PyLong_FromLong(self->data->columns);
}

PyObject* PyTileSetFile::get_margin(PyTileSetFileObject* self, void*) {
    return PyLong_FromLong(self->data->margin);
}

PyObject* PyTileSetFile::get_spacing(PyTileSetFileObject* self, void*) {
    return PyLong_FromLong(self->data->spacing);
}

PyObject* PyTileSetFile::get_image_source(PyTileSetFileObject* self, void*) {
    return PyUnicode_FromString(self->data->image_source.c_str());
}

PyObject* PyTileSetFile::get_properties(PyTileSetFileObject* self, void*) {
    return propertiesToPython(self->data->properties);
}

PyObject* PyTileSetFile::get_wang_sets(PyTileSetFileObject* self, void*) {
    PyObject* list = PyList_New(self->data->wang_sets.size());
    if (!list) return NULL;

    for (size_t i = 0; i < self->data->wang_sets.size(); i++) {
        PyObject* ws = PyWangSet::create(self->data, static_cast<int>(i));
        if (!ws) {
            Py_DECREF(list);
            return NULL;
        }
        PyList_SET_ITEM(list, i, ws);
    }
    return list;
}

// ============================================================
// Methods
// ============================================================

PyObject* PyTileSetFile::to_texture(PyTileSetFileObject* self, PyObject* args) {
    // Create a PyTexture using the image source and tile dimensions
    // Get the Texture type from the mcrfpy module (safe cross-compilation-unit access)
    PyObject* mcrfpy_module = PyImport_ImportModule("mcrfpy");
    if (!mcrfpy_module) return NULL;

    PyObject* tex_type = PyObject_GetAttrString(mcrfpy_module, "Texture");
    Py_DECREF(mcrfpy_module);
    if (!tex_type) return NULL;

    PyObject* tex_args = Py_BuildValue("(sii)",
        self->data->image_source.c_str(),
        self->data->tile_width,
        self->data->tile_height);
    if (!tex_args) { Py_DECREF(tex_type); return NULL; }

    PyObject* tex = PyObject_Call(tex_type, tex_args, NULL);
    Py_DECREF(tex_type);
    Py_DECREF(tex_args);
    return tex;
}

PyObject* PyTileSetFile::tile_info(PyTileSetFileObject* self, PyObject* args) {
    int tile_id;
    if (!PyArg_ParseTuple(args, "i", &tile_id))
        return NULL;

    auto it = self->data->tile_info.find(tile_id);
    if (it == self->data->tile_info.end()) {
        Py_RETURN_NONE;
    }

    const TileInfo& ti = it->second;
    PyObject* dict = PyDict_New();
    if (!dict) return NULL;

    // Properties
    PyObject* props = propertiesToPython(ti.properties);
    if (!props) { Py_DECREF(dict); return NULL; }
    PyDict_SetItemString(dict, "properties", props);
    Py_DECREF(props);

    // Animation
    PyObject* anim_list = PyList_New(ti.animation.size());
    if (!anim_list) { Py_DECREF(dict); return NULL; }
    for (size_t i = 0; i < ti.animation.size(); i++) {
        PyObject* frame = Py_BuildValue("(ii)", ti.animation[i].tile_id, ti.animation[i].duration_ms);
        if (!frame) { Py_DECREF(anim_list); Py_DECREF(dict); return NULL; }
        PyList_SET_ITEM(anim_list, i, frame);
    }
    PyDict_SetItemString(dict, "animation", anim_list);
    Py_DECREF(anim_list);

    return dict;
}

PyObject* PyTileSetFile::wang_set(PyTileSetFileObject* self, PyObject* args) {
    const char* name;
    if (!PyArg_ParseTuple(args, "s", &name))
        return NULL;

    for (size_t i = 0; i < self->data->wang_sets.size(); i++) {
        if (self->data->wang_sets[i].name == name) {
            return PyWangSet::create(self->data, static_cast<int>(i));
        }
    }

    PyErr_Format(PyExc_KeyError, "No WangSet named '%s'", name);
    return NULL;
}

// ============================================================
// Method/GetSet tables
// ============================================================

PyMethodDef PyTileSetFile::methods[] = {
    {"to_texture", (PyCFunction)PyTileSetFile::to_texture, METH_NOARGS,
     MCRF_METHOD(TileSetFile, to_texture,
         MCRF_SIG("()", "Texture"),
         MCRF_DESC("Create a Texture from the tileset image."),
         MCRF_RETURNS("A Texture object for use with TileLayer.")
     )},
    {"tile_info", (PyCFunction)PyTileSetFile::tile_info, METH_VARARGS,
     MCRF_METHOD(TileSetFile, tile_info,
         MCRF_SIG("(tile_id: int)", "dict | None"),
         MCRF_DESC("Get metadata for a specific tile."),
         MCRF_ARGS_START
         MCRF_ARG("tile_id", "Local tile ID (0-based)")
         MCRF_RETURNS("Dict with 'properties' and 'animation' keys, or None if no metadata.")
     )},
    {"wang_set", (PyCFunction)PyTileSetFile::wang_set, METH_VARARGS,
     MCRF_METHOD(TileSetFile, wang_set,
         MCRF_SIG("(name: str)", "WangSet"),
         MCRF_DESC("Look up a WangSet by name."),
         MCRF_ARGS_START
         MCRF_ARG("name", "Name of the Wang set")
         MCRF_RETURNS("The WangSet object.")
         MCRF_RAISES("KeyError", "If no WangSet with that name exists")
     )},
    {NULL}
};

PyGetSetDef PyTileSetFile::getsetters[] = {
    {"name", (getter)PyTileSetFile::get_name, NULL,
     MCRF_PROPERTY(name, "Tileset name (str, read-only)."), NULL},
    {"tile_width", (getter)PyTileSetFile::get_tile_width, NULL,
     MCRF_PROPERTY(tile_width, "Width of each tile in pixels (int, read-only)."), NULL},
    {"tile_height", (getter)PyTileSetFile::get_tile_height, NULL,
     MCRF_PROPERTY(tile_height, "Height of each tile in pixels (int, read-only)."), NULL},
    {"tile_count", (getter)PyTileSetFile::get_tile_count, NULL,
     MCRF_PROPERTY(tile_count, "Total number of tiles (int, read-only)."), NULL},
    {"columns", (getter)PyTileSetFile::get_columns, NULL,
     MCRF_PROPERTY(columns, "Number of columns in tileset image (int, read-only)."), NULL},
    {"margin", (getter)PyTileSetFile::get_margin, NULL,
     MCRF_PROPERTY(margin, "Margin around tiles in pixels (int, read-only)."), NULL},
    {"spacing", (getter)PyTileSetFile::get_spacing, NULL,
     MCRF_PROPERTY(spacing, "Spacing between tiles in pixels (int, read-only)."), NULL},
    {"image_source", (getter)PyTileSetFile::get_image_source, NULL,
     MCRF_PROPERTY(image_source, "Resolved path to the tileset image file (str, read-only)."), NULL},
    {"properties", (getter)PyTileSetFile::get_properties, NULL,
     MCRF_PROPERTY(properties, "Custom tileset properties as a dict (read-only)."), NULL},
    {"wang_sets", (getter)PyTileSetFile::get_wang_sets, NULL,
     MCRF_PROPERTY(wang_sets, "List of WangSet objects from this tileset (read-only)."), NULL},
    {NULL}
};
