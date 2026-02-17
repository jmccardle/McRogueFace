#pragma once
#include "Common.h"
#include "Python.h"
#include <cstdint>

// Forward declaration
class PyDiscreteMap;

// Python object structure
typedef struct {
    PyObject_HEAD
    uint8_t* values;           // Row-major array (width * height)
    int w, h;                  // Dimensions (max 8192x8192)
    PyObject* enum_type;       // Optional Python IntEnum for value interpretation
} PyDiscreteMapObject;

class PyDiscreteMap
{
public:
    // Python type interface
    static PyObject* pynew(PyTypeObject* type, PyObject* args, PyObject* kwds);
    static int init(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds);
    static void dealloc(PyDiscreteMapObject* self);
    static PyObject* repr(PyObject* obj);

    // Properties
    static PyObject* get_size(PyDiscreteMapObject* self, void* closure);
    static PyObject* get_enum_type(PyDiscreteMapObject* self, void* closure);
    static int set_enum_type(PyDiscreteMapObject* self, PyObject* value, void* closure);

    // Scalar operations (all return self for chaining, support region parameters)
    static PyObject* fill(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds);
    static PyObject* clear(PyDiscreteMapObject* self, PyObject* Py_UNUSED(args));

    // Cell access
    static PyObject* get(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds);
    static PyObject* set(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds);

    // Subscript support for dmap[x, y] syntax
    static PyObject* subscript(PyDiscreteMapObject* self, PyObject* key);
    static int subscript_assign(PyDiscreteMapObject* self, PyObject* key, PyObject* value);

    // Combination operations with region support
    static PyObject* add(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds);
    static PyObject* subtract(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds);
    static PyObject* multiply(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds);
    static PyObject* copy_from(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds);
    static PyObject* dmap_max(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds);
    static PyObject* dmap_min(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds);

    // Bitwise operations (DiscreteMap only)
    static PyObject* bitwise_and(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds);
    static PyObject* bitwise_or(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds);
    static PyObject* bitwise_xor(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds);
    static PyObject* invert(PyDiscreteMapObject* self, PyObject* Py_UNUSED(args));

    // Query methods
    static PyObject* count(PyDiscreteMapObject* self, PyObject* args);
    static PyObject* count_range(PyDiscreteMapObject* self, PyObject* args);
    static PyObject* min_max(PyDiscreteMapObject* self, PyObject* Py_UNUSED(args));
    static PyObject* histogram(PyDiscreteMapObject* self, PyObject* Py_UNUSED(args));

    // Boolean/mask operations
    static PyObject* to_bool(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds);
    static PyObject* mask(PyDiscreteMapObject* self, PyObject* Py_UNUSED(args));

    // HeightMap integration
    static PyObject* from_heightmap(PyTypeObject* type, PyObject* args, PyObject* kwds);
    static PyObject* to_heightmap(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds);

    // Mapping methods for subscript support
    static PyMappingMethods mapping_methods;

    // Method and property definitions
    static PyMethodDef methods[];
    static PyGetSetDef getsetters[];
};

namespace mcrfpydef {
    inline PyTypeObject PyDiscreteMapType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.DiscreteMap",
        .tp_basicsize = sizeof(PyDiscreteMapObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)PyDiscreteMap::dealloc,
        .tp_repr = PyDiscreteMap::repr,
        .tp_as_mapping = &PyDiscreteMap::mapping_methods,  // dmap[x, y] subscript
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR(
            "DiscreteMap(size: tuple[int, int], fill: int = 0, enum: type[IntEnum] = None)\n\n"
            "A 2D grid of uint8 values (0-255) for discrete/categorical data.\n\n"
            "DiscreteMap provides memory-efficient storage for terrain types, region IDs,\n"
            "walkability masks, and other categorical data. Uses 4x less memory than HeightMap\n"
            "for the same dimensions.\n\n"
            "Args:\n"
            "    size: (width, height) dimensions. Immutable after creation.\n"
            "    fill: Initial value for all cells (0-255). Default 0.\n"
            "    enum: Optional IntEnum class for value interpretation.\n\n"
            "Example:\n"
            "    from enum import IntEnum\n"
            "    class Terrain(IntEnum):\n"
            "        WATER = 0\n"
            "        GRASS = 1\n"
            "        MOUNTAIN = 2\n\n"
            "    dmap = mcrfpy.DiscreteMap((100, 100), fill=0, enum=Terrain)\n"
            "    dmap.fill(Terrain.GRASS, pos=(10, 10), size=(20, 20))\n"
            "    print(dmap[15, 15])  # Terrain.GRASS\n"
        ),
        .tp_methods = nullptr,  // Set in McRFPy_API.cpp before PyType_Ready
        .tp_getset = nullptr,   // Set in McRFPy_API.cpp before PyType_Ready
        .tp_init = (initproc)PyDiscreteMap::init,
        .tp_new = PyDiscreteMap::pynew,
    };
}
