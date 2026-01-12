#include "PyHeightMap.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"
#include <sstream>

// Property definitions
PyGetSetDef PyHeightMap::getsetters[] = {
    {"size", (getter)PyHeightMap::get_size, NULL,
     MCRF_PROPERTY(size, "Dimensions (width, height) of the heightmap. Read-only."), NULL},
    {NULL}
};

// Method definitions
PyMethodDef PyHeightMap::methods[] = {
    {"fill", (PyCFunction)PyHeightMap::fill, METH_VARARGS,
     MCRF_METHOD(HeightMap, fill,
         MCRF_SIG("(value: float)", "HeightMap"),
         MCRF_DESC("Set all cells to the specified value."),
         MCRF_ARGS_START
         MCRF_ARG("value", "The value to set for all cells")
         MCRF_RETURNS("HeightMap: self, for method chaining")
     )},
    {"clear", (PyCFunction)PyHeightMap::clear, METH_NOARGS,
     MCRF_METHOD(HeightMap, clear,
         MCRF_SIG("()", "HeightMap"),
         MCRF_DESC("Set all cells to 0.0. Equivalent to fill(0.0)."),
         MCRF_RETURNS("HeightMap: self, for method chaining")
     )},
    {"add_constant", (PyCFunction)PyHeightMap::add_constant, METH_VARARGS,
     MCRF_METHOD(HeightMap, add_constant,
         MCRF_SIG("(value: float)", "HeightMap"),
         MCRF_DESC("Add a constant value to every cell."),
         MCRF_ARGS_START
         MCRF_ARG("value", "The value to add to each cell")
         MCRF_RETURNS("HeightMap: self, for method chaining")
     )},
    {"scale", (PyCFunction)PyHeightMap::scale, METH_VARARGS,
     MCRF_METHOD(HeightMap, scale,
         MCRF_SIG("(factor: float)", "HeightMap"),
         MCRF_DESC("Multiply every cell by a factor."),
         MCRF_ARGS_START
         MCRF_ARG("factor", "The multiplier for each cell")
         MCRF_RETURNS("HeightMap: self, for method chaining")
     )},
    {"clamp", (PyCFunction)PyHeightMap::clamp, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, clamp,
         MCRF_SIG("(min: float = 0.0, max: float = 1.0)", "HeightMap"),
         MCRF_DESC("Clamp all values to the specified range."),
         MCRF_ARGS_START
         MCRF_ARG("min", "Minimum value (default 0.0)")
         MCRF_ARG("max", "Maximum value (default 1.0)")
         MCRF_RETURNS("HeightMap: self, for method chaining")
     )},
    {"normalize", (PyCFunction)PyHeightMap::normalize, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, normalize,
         MCRF_SIG("(min: float = 0.0, max: float = 1.0)", "HeightMap"),
         MCRF_DESC("Linearly rescale values so the current minimum becomes min and current maximum becomes max."),
         MCRF_ARGS_START
         MCRF_ARG("min", "Target minimum value (default 0.0)")
         MCRF_ARG("max", "Target maximum value (default 1.0)")
         MCRF_RETURNS("HeightMap: self, for method chaining")
     )},
    {NULL}
};

// Constructor
PyObject* PyHeightMap::pynew(PyTypeObject* type, PyObject* args, PyObject* kwds)
{
    PyHeightMapObject* self = (PyHeightMapObject*)type->tp_alloc(type, 0);
    if (self) {
        self->heightmap = nullptr;
    }
    return (PyObject*)self;
}

int PyHeightMap::init(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"size", "fill", nullptr};
    PyObject* size_obj = nullptr;
    float fill_value = 0.0f;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|f", const_cast<char**>(keywords),
                                     &size_obj, &fill_value)) {
        return -1;
    }

    // Parse size tuple
    if (!PyTuple_Check(size_obj) || PyTuple_Size(size_obj) != 2) {
        PyErr_SetString(PyExc_TypeError, "size must be a tuple of (width, height)");
        return -1;
    }

    int width = (int)PyLong_AsLong(PyTuple_GetItem(size_obj, 0));
    int height = (int)PyLong_AsLong(PyTuple_GetItem(size_obj, 1));

    if (PyErr_Occurred()) {
        return -1;
    }

    if (width <= 0 || height <= 0) {
        PyErr_SetString(PyExc_ValueError, "width and height must be positive integers");
        return -1;
    }

    if (width > GRID_MAX || height > GRID_MAX) {
        PyErr_Format(PyExc_ValueError,
            "HeightMap dimensions cannot exceed %d (got %dx%d)",
            GRID_MAX, width, height);
        return -1;
    }

    // Clean up any existing heightmap
    if (self->heightmap) {
        TCOD_heightmap_delete(self->heightmap);
    }

    // Create new libtcod heightmap
    self->heightmap = TCOD_heightmap_new(width, height);
    if (!self->heightmap) {
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate heightmap");
        return -1;
    }

    // Fill with initial value if not zero
    if (fill_value != 0.0f) {
        // libtcod's TCOD_heightmap_add adds to all cells, so we use it after clear
        TCOD_heightmap_clear(self->heightmap);
        TCOD_heightmap_add(self->heightmap, fill_value);
    }

    return 0;
}

void PyHeightMap::dealloc(PyHeightMapObject* self)
{
    if (self->heightmap) {
        TCOD_heightmap_delete(self->heightmap);
        self->heightmap = nullptr;
    }
    Py_TYPE(self)->tp_free((PyObject*)self);
}

PyObject* PyHeightMap::repr(PyObject* obj)
{
    PyHeightMapObject* self = (PyHeightMapObject*)obj;
    std::ostringstream ss;

    if (self->heightmap) {
        ss << "<HeightMap (" << self->heightmap->w << " x " << self->heightmap->h << ")>";
    } else {
        ss << "<HeightMap (uninitialized)>";
    }

    return PyUnicode_FromString(ss.str().c_str());
}

// Property: size
PyObject* PyHeightMap::get_size(PyHeightMapObject* self, void* closure)
{
    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }
    return Py_BuildValue("(ii)", self->heightmap->w, self->heightmap->h);
}

// Method: fill(value) -> HeightMap
PyObject* PyHeightMap::fill(PyHeightMapObject* self, PyObject* args)
{
    float value;
    if (!PyArg_ParseTuple(args, "f", &value)) {
        return nullptr;
    }

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    // Clear and then add the value (libtcod doesn't have a direct "set all" function)
    TCOD_heightmap_clear(self->heightmap);
    if (value != 0.0f) {
        TCOD_heightmap_add(self->heightmap, value);
    }

    // Return self for chaining
    Py_INCREF(self);
    return (PyObject*)self;
}

// Method: clear() -> HeightMap
PyObject* PyHeightMap::clear(PyHeightMapObject* self, PyObject* Py_UNUSED(args))
{
    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    TCOD_heightmap_clear(self->heightmap);

    // Return self for chaining
    Py_INCREF(self);
    return (PyObject*)self;
}

// Method: add_constant(value) -> HeightMap
PyObject* PyHeightMap::add_constant(PyHeightMapObject* self, PyObject* args)
{
    float value;
    if (!PyArg_ParseTuple(args, "f", &value)) {
        return nullptr;
    }

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    TCOD_heightmap_add(self->heightmap, value);

    // Return self for chaining
    Py_INCREF(self);
    return (PyObject*)self;
}

// Method: scale(factor) -> HeightMap
PyObject* PyHeightMap::scale(PyHeightMapObject* self, PyObject* args)
{
    float factor;
    if (!PyArg_ParseTuple(args, "f", &factor)) {
        return nullptr;
    }

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    TCOD_heightmap_scale(self->heightmap, factor);

    // Return self for chaining
    Py_INCREF(self);
    return (PyObject*)self;
}

// Method: clamp(min=0.0, max=1.0) -> HeightMap
PyObject* PyHeightMap::clamp(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"min", "max", nullptr};
    float min_val = 0.0f;
    float max_val = 1.0f;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|ff", const_cast<char**>(keywords),
                                     &min_val, &max_val)) {
        return nullptr;
    }

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    if (min_val > max_val) {
        PyErr_SetString(PyExc_ValueError, "min must be less than or equal to max");
        return nullptr;
    }

    TCOD_heightmap_clamp(self->heightmap, min_val, max_val);

    // Return self for chaining
    Py_INCREF(self);
    return (PyObject*)self;
}

// Method: normalize(min=0.0, max=1.0) -> HeightMap
PyObject* PyHeightMap::normalize(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"min", "max", nullptr};
    float min_val = 0.0f;
    float max_val = 1.0f;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|ff", const_cast<char**>(keywords),
                                     &min_val, &max_val)) {
        return nullptr;
    }

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    if (min_val > max_val) {
        PyErr_SetString(PyExc_ValueError, "min must be less than or equal to max");
        return nullptr;
    }

    TCOD_heightmap_normalize(self->heightmap, min_val, max_val);

    // Return self for chaining
    Py_INCREF(self);
    return (PyObject*)self;
}
