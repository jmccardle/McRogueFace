#pragma once
#include "Python.h"
#include "TiledTypes.h"
#include <memory>

// Python object structure
typedef struct PyTileMapFileObject {
    PyObject_HEAD
    std::shared_ptr<mcrf::tiled::TileMapData> data;
} PyTileMapFileObject;

// Python binding class
class PyTileMapFile {
public:
    static PyObject* pynew(PyTypeObject* type, PyObject* args, PyObject* kwds);
    static int init(PyTileMapFileObject* self, PyObject* args, PyObject* kwds);
    static void dealloc(PyTileMapFileObject* self);
    static PyObject* repr(PyObject* obj);

    // Read-only properties
    static PyObject* get_width(PyTileMapFileObject* self, void* closure);
    static PyObject* get_height(PyTileMapFileObject* self, void* closure);
    static PyObject* get_tile_width(PyTileMapFileObject* self, void* closure);
    static PyObject* get_tile_height(PyTileMapFileObject* self, void* closure);
    static PyObject* get_orientation(PyTileMapFileObject* self, void* closure);
    static PyObject* get_properties(PyTileMapFileObject* self, void* closure);
    static PyObject* get_tileset_count(PyTileMapFileObject* self, void* closure);
    static PyObject* get_tile_layer_names(PyTileMapFileObject* self, void* closure);
    static PyObject* get_object_layer_names(PyTileMapFileObject* self, void* closure);

    // Methods
    static PyObject* tileset(PyTileMapFileObject* self, PyObject* args);
    static PyObject* tile_layer_data(PyTileMapFileObject* self, PyObject* args);
    static PyObject* resolve_gid(PyTileMapFileObject* self, PyObject* args);
    static PyObject* object_layer(PyTileMapFileObject* self, PyObject* args);
    static PyObject* apply_to_tile_layer(PyTileMapFileObject* self, PyObject* args, PyObject* kwds);

    static PyMethodDef methods[];
    static PyGetSetDef getsetters[];
};

// Type definition in mcrfpydef namespace
namespace mcrfpydef {

inline PyTypeObject PyTileMapFileType = {
    .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
    .tp_name = "mcrfpy.TileMapFile",
    .tp_basicsize = sizeof(PyTileMapFileObject),
    .tp_itemsize = 0,
    .tp_dealloc = (destructor)PyTileMapFile::dealloc,
    .tp_repr = PyTileMapFile::repr,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_doc = PyDoc_STR(
        "TileMapFile(path: str)\n\n"
        "Load a Tiled map file (.tmx or .tmj).\n\n"
        "Parses the map and its referenced tilesets, providing access to tile layers,\n"
        "object layers, and GID resolution.\n\n"
        "Args:\n"
        "    path: Path to the .tmx or .tmj map file.\n\n"
        "Properties:\n"
        "    width (int, read-only): Map width in tiles.\n"
        "    height (int, read-only): Map height in tiles.\n"
        "    tile_width (int, read-only): Tile width in pixels.\n"
        "    tile_height (int, read-only): Tile height in pixels.\n"
        "    orientation (str, read-only): Map orientation (e.g. 'orthogonal').\n"
        "    properties (dict, read-only): Custom map properties.\n"
        "    tileset_count (int, read-only): Number of referenced tilesets.\n"
        "    tile_layer_names (list, read-only): Names of tile layers.\n"
        "    object_layer_names (list, read-only): Names of object layers.\n\n"
        "Example:\n"
        "    tm = mcrfpy.TileMapFile('map.tmx')\n"
        "    data = tm.tile_layer_data('Ground')\n"
        "    tm.apply_to_tile_layer(my_tile_layer, 'Ground')\n"
    ),
    .tp_methods = nullptr,  // Set before PyType_Ready
    .tp_getset = nullptr,   // Set before PyType_Ready
    .tp_init = (initproc)PyTileMapFile::init,
    .tp_new = PyTileMapFile::pynew,
};

} // namespace mcrfpydef
