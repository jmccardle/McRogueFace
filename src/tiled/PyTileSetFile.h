#pragma once
#include "Python.h"
#include "TiledTypes.h"
#include <memory>

// Python object structure
typedef struct PyTileSetFileObject {
    PyObject_HEAD
    std::shared_ptr<mcrf::tiled::TileSetData> data;
} PyTileSetFileObject;

// Python binding class
class PyTileSetFile {
public:
    static PyObject* pynew(PyTypeObject* type, PyObject* args, PyObject* kwds);
    static int init(PyTileSetFileObject* self, PyObject* args, PyObject* kwds);
    static void dealloc(PyTileSetFileObject* self);
    static PyObject* repr(PyObject* obj);

    // Read-only properties
    static PyObject* get_name(PyTileSetFileObject* self, void* closure);
    static PyObject* get_tile_width(PyTileSetFileObject* self, void* closure);
    static PyObject* get_tile_height(PyTileSetFileObject* self, void* closure);
    static PyObject* get_tile_count(PyTileSetFileObject* self, void* closure);
    static PyObject* get_columns(PyTileSetFileObject* self, void* closure);
    static PyObject* get_margin(PyTileSetFileObject* self, void* closure);
    static PyObject* get_spacing(PyTileSetFileObject* self, void* closure);
    static PyObject* get_image_source(PyTileSetFileObject* self, void* closure);
    static PyObject* get_properties(PyTileSetFileObject* self, void* closure);
    static PyObject* get_wang_sets(PyTileSetFileObject* self, void* closure);

    // Methods
    static PyObject* to_texture(PyTileSetFileObject* self, PyObject* args);
    static PyObject* tile_info(PyTileSetFileObject* self, PyObject* args);
    static PyObject* wang_set(PyTileSetFileObject* self, PyObject* args);

    static PyMethodDef methods[];
    static PyGetSetDef getsetters[];
};

// Type definition in mcrfpydef namespace
namespace mcrfpydef {

inline PyTypeObject PyTileSetFileType = {
    .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
    .tp_name = "mcrfpy.TileSetFile",
    .tp_basicsize = sizeof(PyTileSetFileObject),
    .tp_itemsize = 0,
    .tp_dealloc = (destructor)PyTileSetFile::dealloc,
    .tp_repr = PyTileSetFile::repr,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_doc = PyDoc_STR(
        "TileSetFile(path: str)\n\n"
        "Load a Tiled tileset file (.tsx or .tsj).\n\n"
        "Parses the tileset and provides access to tile metadata, properties,\n"
        "Wang sets, and texture creation.\n\n"
        "Args:\n"
        "    path: Path to the .tsx or .tsj tileset file.\n\n"
        "Properties:\n"
        "    name (str, read-only): Tileset name.\n"
        "    tile_width (int, read-only): Width of each tile in pixels.\n"
        "    tile_height (int, read-only): Height of each tile in pixels.\n"
        "    tile_count (int, read-only): Total number of tiles.\n"
        "    columns (int, read-only): Number of columns in the tileset image.\n"
        "    image_source (str, read-only): Resolved path to the tileset image.\n"
        "    properties (dict, read-only): Custom properties from the tileset.\n"
        "    wang_sets (list, read-only): List of WangSet objects.\n\n"
        "Example:\n"
        "    ts = mcrfpy.TileSetFile('tileset.tsx')\n"
        "    texture = ts.to_texture()\n"
        "    print(f'{ts.name}: {ts.tile_count} tiles')\n"
    ),
    .tp_methods = nullptr,  // Set before PyType_Ready
    .tp_getset = nullptr,   // Set before PyType_Ready
    .tp_init = (initproc)PyTileSetFile::init,
    .tp_new = PyTileSetFile::pynew,
};

} // namespace mcrfpydef
