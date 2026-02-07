#pragma once
#include "Python.h"
#include "TiledTypes.h"
#include <memory>

// Python object structure
// Holds a shared_ptr to the parent TileSetData (keeps it alive) + index into wang_sets
typedef struct PyWangSetObject {
    PyObject_HEAD
    std::shared_ptr<mcrf::tiled::TileSetData> parent;
    int wang_set_index;
} PyWangSetObject;

// Python binding class
class PyWangSet {
public:
    // Factory: create a PyWangSet from parent tileset + index
    static PyObject* create(std::shared_ptr<mcrf::tiled::TileSetData> parent, int index);

    static void dealloc(PyWangSetObject* self);
    static PyObject* repr(PyObject* obj);

    // Read-only properties
    static PyObject* get_name(PyWangSetObject* self, void* closure);
    static PyObject* get_type(PyWangSetObject* self, void* closure);
    static PyObject* get_color_count(PyWangSetObject* self, void* closure);
    static PyObject* get_colors(PyWangSetObject* self, void* closure);

    // Methods
    static PyObject* terrain_enum(PyWangSetObject* self, PyObject* args);
    static PyObject* resolve(PyWangSetObject* self, PyObject* args);
    static PyObject* apply(PyWangSetObject* self, PyObject* args, PyObject* kwds);

    static PyMethodDef methods[];
    static PyGetSetDef getsetters[];

private:
    // Helper: get the WangSet reference
    static const mcrf::tiled::WangSet& getWangSet(PyWangSetObject* self);
};

// Type definition in mcrfpydef namespace
namespace mcrfpydef {

inline PyTypeObject PyWangSetType = {
    .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
    .tp_name = "mcrfpy.WangSet",
    .tp_basicsize = sizeof(PyWangSetObject),
    .tp_itemsize = 0,
    .tp_dealloc = (destructor)PyWangSet::dealloc,
    .tp_repr = PyWangSet::repr,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_doc = PyDoc_STR(
        "WangSet - Wang terrain auto-tile set from a Tiled tileset.\n\n"
        "WangSets are obtained from TileSetFile.wang_sets or TileSetFile.wang_set().\n"
        "They map abstract terrain types to concrete sprite indices using Tiled's\n"
        "Wang tile algorithm.\n\n"
        "Properties:\n"
        "    name (str, read-only): Wang set name.\n"
        "    type (str, read-only): 'corner', 'edge', or 'mixed'.\n"
        "    color_count (int, read-only): Number of terrain colors.\n"
        "    colors (list, read-only): List of color dicts.\n\n"
        "Example:\n"
        "    ws = tileset.wang_set('overworld')\n"
        "    Terrain = ws.terrain_enum()\n"
        "    tiles = ws.resolve(discrete_map)\n"
    ),
    .tp_methods = nullptr,  // Set before PyType_Ready
    .tp_getset = nullptr,   // Set before PyType_Ready
};

} // namespace mcrfpydef
