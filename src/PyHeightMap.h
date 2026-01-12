#pragma once
#include "Common.h"
#include "Python.h"
#include <libtcod.h>

// Forward declaration
class PyHeightMap;

// Python object structure
typedef struct {
    PyObject_HEAD
    TCOD_heightmap_t* heightmap;  // libtcod heightmap pointer
} PyHeightMapObject;

class PyHeightMap
{
public:
    // Python type interface
    static PyObject* pynew(PyTypeObject* type, PyObject* args, PyObject* kwds);
    static int init(PyHeightMapObject* self, PyObject* args, PyObject* kwds);
    static void dealloc(PyHeightMapObject* self);
    static PyObject* repr(PyObject* obj);

    // Properties
    static PyObject* get_size(PyHeightMapObject* self, void* closure);

    // Scalar operations (all return self for chaining)
    static PyObject* fill(PyHeightMapObject* self, PyObject* args);
    static PyObject* clear(PyHeightMapObject* self, PyObject* Py_UNUSED(args));
    static PyObject* add_constant(PyHeightMapObject* self, PyObject* args);
    static PyObject* scale(PyHeightMapObject* self, PyObject* args);
    static PyObject* clamp(PyHeightMapObject* self, PyObject* args, PyObject* kwds);
    static PyObject* normalize(PyHeightMapObject* self, PyObject* args, PyObject* kwds);

    // Query methods (#196)
    static PyObject* get(PyHeightMapObject* self, PyObject* args);
    static PyObject* get_interpolated(PyHeightMapObject* self, PyObject* args);
    static PyObject* get_slope(PyHeightMapObject* self, PyObject* args);
    static PyObject* get_normal(PyHeightMapObject* self, PyObject* args, PyObject* kwds);
    static PyObject* min_max(PyHeightMapObject* self, PyObject* Py_UNUSED(args));
    static PyObject* count_in_range(PyHeightMapObject* self, PyObject* args);

    // Method and property definitions
    static PyMethodDef methods[];
    static PyGetSetDef getsetters[];
};

namespace mcrfpydef {
    static PyTypeObject PyHeightMapType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.HeightMap",
        .tp_basicsize = sizeof(PyHeightMapObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)PyHeightMap::dealloc,
        .tp_repr = PyHeightMap::repr,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR(
            "HeightMap(size: tuple[int, int], fill: float = 0.0)\n\n"
            "A 2D grid of float values for procedural generation.\n\n"
            "HeightMap is the universal canvas for procedural generation. It stores "
            "float values that can be manipulated, combined, and applied to Grid and "
            "Layer objects.\n\n"
            "Args:\n"
            "    size: (width, height) dimensions of the heightmap. Immutable after creation.\n"
            "    fill: Initial value for all cells. Default 0.0.\n\n"
            "Example:\n"
            "    hmap = mcrfpy.HeightMap((100, 100))\n"
            "    hmap.fill(0.5).scale(2.0).clamp(0.0, 1.0)\n"
        ),
        .tp_methods = nullptr,  // Set in McRFPy_API.cpp before PyType_Ready
        .tp_getset = nullptr,   // Set in McRFPy_API.cpp before PyType_Ready
        .tp_init = (initproc)PyHeightMap::init,
        .tp_new = PyHeightMap::pynew,
    };
}
