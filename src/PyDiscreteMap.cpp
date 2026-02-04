#include "PyDiscreteMap.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"
#include "PyPositionHelper.h"
#include "PyHeightMap.h"
#include "MapOps.h"
#include <sstream>
#include <cstring>  // for memset
#include <algorithm>

// ============================================================================
// Helper: Parse an integer value from PyObject (handles int and IntEnum)
// ============================================================================
static bool parseIntValue(PyObject* value_obj, int* out_val) {
    if (PyLong_Check(value_obj)) {
        *out_val = (int)PyLong_AsLong(value_obj);
        return true;
    }

    // Try IntEnum (has .value attribute)
    PyObject* val_attr = PyObject_GetAttrString(value_obj, "value");
    if (val_attr) {
        if (PyLong_Check(val_attr)) {
            *out_val = (int)PyLong_AsLong(val_attr);
            Py_DECREF(val_attr);
            return true;
        }
        Py_DECREF(val_attr);
    }
    PyErr_Clear();

    PyErr_SetString(PyExc_TypeError, "value must be an integer or IntEnum member");
    return false;
}

// ============================================================================
// Helper: Convert uint8_t value to Python object (int or enum member)
// ============================================================================
static PyObject* valueToResult(uint8_t value, PyObject* enum_type) {
    if (enum_type && enum_type != Py_None) {
        // Try to get enum member by value
        PyObject* val_obj = PyLong_FromLong(value);
        PyObject* member = PyObject_Call(enum_type, PyTuple_Pack(1, val_obj), nullptr);
        Py_DECREF(val_obj);

        if (member) {
            return member;  // Return enum member
        }
        // If no matching enum member, fall through to return int
        PyErr_Clear();
    }
    return PyLong_FromLong(value);
}

// ============================================================================
// Helper: Create a new DiscreteMap object with given dimensions
// ============================================================================
static PyDiscreteMapObject* CreateNewDiscreteMap(int width, int height) {
    // Get the DiscreteMap type from the module
    PyObject* dmap_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "DiscreteMap");
    if (!dmap_type) {
        PyErr_SetString(PyExc_RuntimeError, "DiscreteMap type not found in module");
        return nullptr;
    }

    // Create size tuple
    PyObject* size_tuple = Py_BuildValue("(ii)", width, height);
    if (!size_tuple) {
        Py_DECREF(dmap_type);
        return nullptr;
    }

    // Create args tuple containing the size tuple
    PyObject* args = PyTuple_Pack(1, size_tuple);
    Py_DECREF(size_tuple);
    if (!args) {
        Py_DECREF(dmap_type);
        return nullptr;
    }

    // Create the new object
    PyDiscreteMapObject* new_dmap = (PyDiscreteMapObject*)PyObject_Call(dmap_type, args, nullptr);
    Py_DECREF(args);
    Py_DECREF(dmap_type);

    if (!new_dmap) {
        return nullptr;  // Python error already set
    }

    return new_dmap;
}

// ============================================================================
// Helper: Validate another DiscreteMap for binary operations
// ============================================================================
static PyDiscreteMapObject* validateOtherDiscreteMapType(PyObject* other_obj, const char* method_name) {
    // Get the DiscreteMap type from the module
    PyObject* dmap_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "DiscreteMap");
    if (!dmap_type) {
        PyErr_SetString(PyExc_RuntimeError, "DiscreteMap type not found in module");
        return nullptr;
    }

    // Check if other is a DiscreteMap
    int is_dmap = PyObject_IsInstance(other_obj, dmap_type);
    Py_DECREF(dmap_type);

    if (is_dmap < 0) {
        return nullptr;  // Error during check
    }

    if (!is_dmap) {
        PyErr_Format(PyExc_TypeError, "%s() requires a DiscreteMap argument", method_name);
        return nullptr;
    }

    PyDiscreteMapObject* other = (PyDiscreteMapObject*)other_obj;

    if (!other->values) {
        PyErr_SetString(PyExc_RuntimeError, "Other DiscreteMap not initialized");
        return nullptr;
    }

    return other;
}

// ============================================================================
// Property definitions
// ============================================================================
PyGetSetDef PyDiscreteMap::getsetters[] = {
    {"size", (getter)PyDiscreteMap::get_size, NULL,
     MCRF_PROPERTY(size, "Dimensions (width, height) of the map. Read-only."), NULL},
    {"enum_type", (getter)PyDiscreteMap::get_enum_type, (setter)PyDiscreteMap::set_enum_type,
     MCRF_PROPERTY(enum_type, "Optional IntEnum class for value interpretation."), NULL},
    {NULL}
};

// ============================================================================
// Mapping methods for subscript support (dmap[x, y])
// ============================================================================
PyMappingMethods PyDiscreteMap::mapping_methods = {
    .mp_length = nullptr,
    .mp_subscript = (binaryfunc)PyDiscreteMap::subscript,
    .mp_ass_subscript = (objobjargproc)PyDiscreteMap::subscript_assign
};

// ============================================================================
// Method definitions
// ============================================================================
PyMethodDef PyDiscreteMap::methods[] = {
    {"fill", (PyCFunction)PyDiscreteMap::fill, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(DiscreteMap, fill,
         MCRF_SIG("(value: int, *, pos=None, size=None)", "DiscreteMap"),
         MCRF_DESC("Set cells in region to the specified value."),
         MCRF_ARGS_START
         MCRF_ARG("value", "The value to set (0-255, or IntEnum member)")
         MCRF_ARG("pos", "Region start (x, y) in destination (default: (0, 0))")
         MCRF_ARG("size", "Region (width, height) to fill (default: remaining space)")
         MCRF_RETURNS("DiscreteMap: self, for method chaining")
     )},
    {"clear", (PyCFunction)PyDiscreteMap::clear, METH_NOARGS,
     MCRF_METHOD(DiscreteMap, clear,
         MCRF_SIG("()", "DiscreteMap"),
         MCRF_DESC("Set all cells to 0. Equivalent to fill(0)."),
         MCRF_RETURNS("DiscreteMap: self, for method chaining")
     )},
    {"get", (PyCFunction)PyDiscreteMap::get, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(DiscreteMap, get,
         MCRF_SIG("(x, y) or (pos)", "int | Enum"),
         MCRF_DESC("Get the value at integer coordinates."),
         MCRF_ARGS_START
         MCRF_ARG("x, y", "Position as two ints, tuple, list, or Vector")
         MCRF_RETURNS("int or enum member if enum_type is set")
         MCRF_RAISES("IndexError", "Position is out of bounds")
     )},
    {"set", (PyCFunction)PyDiscreteMap::set, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(DiscreteMap, set,
         MCRF_SIG("(x: int, y: int, value: int)", "None"),
         MCRF_DESC("Set the value at integer coordinates."),
         MCRF_ARGS_START
         MCRF_ARG("x", "X coordinate")
         MCRF_ARG("y", "Y coordinate")
         MCRF_ARG("value", "Value to set (0-255, or IntEnum member)")
         MCRF_RAISES("IndexError", "Position is out of bounds")
         MCRF_RAISES("ValueError", "Value out of range 0-255")
     )},
    // Combination operations
    {"add", (PyCFunction)PyDiscreteMap::add, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(DiscreteMap, add,
         MCRF_SIG("(other: DiscreteMap | int, *, pos=None, source_pos=None, size=None)", "DiscreteMap"),
         MCRF_DESC("Add values from another map or a scalar, with saturation to 0-255."),
         MCRF_ARGS_START
         MCRF_ARG("other", "DiscreteMap to add, or int scalar to add to all cells")
         MCRF_ARG("pos", "Destination start (x, y) in self (default: (0, 0))")
         MCRF_ARG("source_pos", "Source start (x, y) in other (default: (0, 0))")
         MCRF_ARG("size", "Region (width, height) (default: max overlapping area)")
         MCRF_RETURNS("DiscreteMap: self, for method chaining")
     )},
    {"subtract", (PyCFunction)PyDiscreteMap::subtract, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(DiscreteMap, subtract,
         MCRF_SIG("(other: DiscreteMap | int, *, pos=None, source_pos=None, size=None)", "DiscreteMap"),
         MCRF_DESC("Subtract values from another map or a scalar, with saturation to 0-255."),
         MCRF_ARGS_START
         MCRF_ARG("other", "DiscreteMap to subtract, or int scalar")
         MCRF_ARG("pos", "Destination start (x, y) in self (default: (0, 0))")
         MCRF_ARG("source_pos", "Source start (x, y) in other (default: (0, 0))")
         MCRF_ARG("size", "Region (width, height) (default: max overlapping area)")
         MCRF_RETURNS("DiscreteMap: self, for method chaining")
     )},
    {"multiply", (PyCFunction)PyDiscreteMap::multiply, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(DiscreteMap, multiply,
         MCRF_SIG("(factor: float, *, pos=None, size=None)", "DiscreteMap"),
         MCRF_DESC("Multiply values by a scalar factor, with saturation to 0-255."),
         MCRF_ARGS_START
         MCRF_ARG("factor", "Multiplier for each cell")
         MCRF_ARG("pos", "Region start (x, y) (default: (0, 0))")
         MCRF_ARG("size", "Region (width, height) (default: entire map)")
         MCRF_RETURNS("DiscreteMap: self, for method chaining")
     )},
    {"copy_from", (PyCFunction)PyDiscreteMap::copy_from, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(DiscreteMap, copy_from,
         MCRF_SIG("(other: DiscreteMap, *, pos=None, source_pos=None, size=None)", "DiscreteMap"),
         MCRF_DESC("Copy values from another DiscreteMap into the specified region."),
         MCRF_ARGS_START
         MCRF_ARG("other", "DiscreteMap to copy from")
         MCRF_ARG("pos", "Destination start (x, y) in self (default: (0, 0))")
         MCRF_ARG("source_pos", "Source start (x, y) in other (default: (0, 0))")
         MCRF_ARG("size", "Region (width, height) (default: max overlapping area)")
         MCRF_RETURNS("DiscreteMap: self, for method chaining")
     )},
    {"max", (PyCFunction)PyDiscreteMap::dmap_max, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(DiscreteMap, max,
         MCRF_SIG("(other: DiscreteMap, *, pos=None, source_pos=None, size=None)", "DiscreteMap"),
         MCRF_DESC("Set each cell to the maximum of this and another DiscreteMap."),
         MCRF_ARGS_START
         MCRF_ARG("other", "DiscreteMap to compare with")
         MCRF_ARG("pos", "Destination start (x, y) in self (default: (0, 0))")
         MCRF_ARG("source_pos", "Source start (x, y) in other (default: (0, 0))")
         MCRF_ARG("size", "Region (width, height) (default: max overlapping area)")
         MCRF_RETURNS("DiscreteMap: self, for method chaining")
     )},
    {"min", (PyCFunction)PyDiscreteMap::dmap_min, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(DiscreteMap, min,
         MCRF_SIG("(other: DiscreteMap, *, pos=None, source_pos=None, size=None)", "DiscreteMap"),
         MCRF_DESC("Set each cell to the minimum of this and another DiscreteMap."),
         MCRF_ARGS_START
         MCRF_ARG("other", "DiscreteMap to compare with")
         MCRF_ARG("pos", "Destination start (x, y) in self (default: (0, 0))")
         MCRF_ARG("source_pos", "Source start (x, y) in other (default: (0, 0))")
         MCRF_ARG("size", "Region (width, height) (default: max overlapping area)")
         MCRF_RETURNS("DiscreteMap: self, for method chaining")
     )},
    // Bitwise operations
    {"bitwise_and", (PyCFunction)PyDiscreteMap::bitwise_and, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(DiscreteMap, bitwise_and,
         MCRF_SIG("(other: DiscreteMap, *, pos=None, source_pos=None, size=None)", "DiscreteMap"),
         MCRF_DESC("Bitwise AND with another DiscreteMap."),
         MCRF_ARGS_START
         MCRF_ARG("other", "DiscreteMap for AND operation")
         MCRF_ARG("pos", "Destination start (x, y) in self (default: (0, 0))")
         MCRF_ARG("source_pos", "Source start (x, y) in other (default: (0, 0))")
         MCRF_ARG("size", "Region (width, height) (default: max overlapping area)")
         MCRF_RETURNS("DiscreteMap: self, for method chaining")
     )},
    {"bitwise_or", (PyCFunction)PyDiscreteMap::bitwise_or, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(DiscreteMap, bitwise_or,
         MCRF_SIG("(other: DiscreteMap, *, pos=None, source_pos=None, size=None)", "DiscreteMap"),
         MCRF_DESC("Bitwise OR with another DiscreteMap."),
         MCRF_ARGS_START
         MCRF_ARG("other", "DiscreteMap for OR operation")
         MCRF_ARG("pos", "Destination start (x, y) in self (default: (0, 0))")
         MCRF_ARG("source_pos", "Source start (x, y) in other (default: (0, 0))")
         MCRF_ARG("size", "Region (width, height) (default: max overlapping area)")
         MCRF_RETURNS("DiscreteMap: self, for method chaining")
     )},
    {"bitwise_xor", (PyCFunction)PyDiscreteMap::bitwise_xor, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(DiscreteMap, bitwise_xor,
         MCRF_SIG("(other: DiscreteMap, *, pos=None, source_pos=None, size=None)", "DiscreteMap"),
         MCRF_DESC("Bitwise XOR with another DiscreteMap."),
         MCRF_ARGS_START
         MCRF_ARG("other", "DiscreteMap for XOR operation")
         MCRF_ARG("pos", "Destination start (x, y) in self (default: (0, 0))")
         MCRF_ARG("source_pos", "Source start (x, y) in other (default: (0, 0))")
         MCRF_ARG("size", "Region (width, height) (default: max overlapping area)")
         MCRF_RETURNS("DiscreteMap: self, for method chaining")
     )},
    {"invert", (PyCFunction)PyDiscreteMap::invert, METH_NOARGS,
     MCRF_METHOD(DiscreteMap, invert,
         MCRF_SIG("()", "DiscreteMap"),
         MCRF_DESC("Return NEW DiscreteMap with (255 - value) for each cell."),
         MCRF_RETURNS("DiscreteMap: new inverted map (original unchanged)")
     )},
    // Query methods
    {"count", (PyCFunction)PyDiscreteMap::count, METH_VARARGS,
     MCRF_METHOD(DiscreteMap, count,
         MCRF_SIG("(value: int)", "int"),
         MCRF_DESC("Count cells with the specified value."),
         MCRF_ARGS_START
         MCRF_ARG("value", "Value to count (0-255)")
         MCRF_RETURNS("int: Number of cells with that value")
     )},
    {"count_range", (PyCFunction)PyDiscreteMap::count_range, METH_VARARGS,
     MCRF_METHOD(DiscreteMap, count_range,
         MCRF_SIG("(min_val: int, max_val: int)", "int"),
         MCRF_DESC("Count cells with values in the specified range (inclusive)."),
         MCRF_ARGS_START
         MCRF_ARG("min_val", "Minimum value (inclusive)")
         MCRF_ARG("max_val", "Maximum value (inclusive)")
         MCRF_RETURNS("int: Number of cells in range")
     )},
    {"min_max", (PyCFunction)PyDiscreteMap::min_max, METH_NOARGS,
     MCRF_METHOD(DiscreteMap, min_max,
         MCRF_SIG("()", "tuple[int, int]"),
         MCRF_DESC("Get the minimum and maximum values in the map."),
         MCRF_RETURNS("tuple[int, int]: (min_value, max_value)")
     )},
    {"histogram", (PyCFunction)PyDiscreteMap::histogram, METH_NOARGS,
     MCRF_METHOD(DiscreteMap, histogram,
         MCRF_SIG("()", "dict[int, int]"),
         MCRF_DESC("Get a histogram of value counts."),
         MCRF_RETURNS("dict: {value: count} for all values present in the map")
     )},
    // Boolean/mask operations
    {"bool", (PyCFunction)PyDiscreteMap::to_bool, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(DiscreteMap, bool,
         MCRF_SIG("(condition: int | set | callable)", "DiscreteMap"),
         MCRF_DESC("Create binary mask from condition. Returns NEW DiscreteMap."),
         MCRF_ARGS_START
         MCRF_ARG("condition", "int: match that value; set: match any in set; callable: predicate")
         MCRF_RETURNS("DiscreteMap: new map with 1 where condition true, 0 elsewhere")
     )},
    {"mask", (PyCFunction)PyDiscreteMap::mask, METH_NOARGS,
     MCRF_METHOD(DiscreteMap, mask,
         MCRF_SIG("()", "memoryview"),
         MCRF_DESC("Get raw uint8_t data as memoryview for libtcod compatibility."),
         MCRF_RETURNS("memoryview: Direct access to internal buffer (read/write)")
     )},
    // HeightMap integration
    {"from_heightmap", (PyCFunction)PyDiscreteMap::from_heightmap, METH_VARARGS | METH_KEYWORDS | METH_CLASS,
     MCRF_METHOD(DiscreteMap, from_heightmap,
         MCRF_SIG("(hmap: HeightMap, mapping: list[tuple[tuple[float,float], int]], *, enum=None)", "DiscreteMap"),
         MCRF_DESC("Create DiscreteMap from HeightMap using range-to-value mapping."),
         MCRF_ARGS_START
         MCRF_ARG("hmap", "HeightMap to convert")
         MCRF_ARG("mapping", "List of ((min, max), value) tuples")
         MCRF_ARG("enum", "Optional IntEnum class for value interpretation")
         MCRF_RETURNS("DiscreteMap: new map with mapped values")
     )},
    {"to_heightmap", (PyCFunction)PyDiscreteMap::to_heightmap, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(DiscreteMap, to_heightmap,
         MCRF_SIG("(mapping: dict[int, float] = None)", "HeightMap"),
         MCRF_DESC("Convert to HeightMap, optionally mapping values to floats."),
         MCRF_ARGS_START
         MCRF_ARG("mapping", "Optional {int: float} mapping (default: direct cast)")
         MCRF_RETURNS("HeightMap: new heightmap with converted values")
     )},
    {NULL}
};

// ============================================================================
// Constructor / Destructor
// ============================================================================

PyObject* PyDiscreteMap::pynew(PyTypeObject* type, PyObject* args, PyObject* kwds)
{
    PyDiscreteMapObject* self = (PyDiscreteMapObject*)type->tp_alloc(type, 0);
    if (self) {
        self->values = nullptr;
        self->w = 0;
        self->h = 0;
        self->enum_type = nullptr;
    }
    return (PyObject*)self;
}

int PyDiscreteMap::init(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"size", "fill", "enum", nullptr};
    PyObject* size_obj = nullptr;
    int fill_value = 0;
    PyObject* enum_obj = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|iO", const_cast<char**>(keywords),
                                     &size_obj, &fill_value, &enum_obj)) {
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
            "DiscreteMap dimensions cannot exceed %d (got %dx%d)",
            GRID_MAX, width, height);
        return -1;
    }

    // Validate fill value
    if (fill_value < 0 || fill_value > 255) {
        PyErr_SetString(PyExc_ValueError, "fill value must be in range 0-255");
        return -1;
    }

    // Clean up any existing data
    if (self->values) {
        delete[] self->values;
        self->values = nullptr;
    }
    Py_XDECREF(self->enum_type);
    self->enum_type = nullptr;

    // Allocate new array
    size_t total_size = static_cast<size_t>(width) * static_cast<size_t>(height);
    self->values = new (std::nothrow) uint8_t[total_size];
    if (!self->values) {
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate DiscreteMap");
        return -1;
    }

    self->w = width;
    self->h = height;

    // Fill with initial value
    memset(self->values, static_cast<uint8_t>(fill_value), total_size);

    // Store enum type if provided
    if (enum_obj && enum_obj != Py_None) {
        Py_INCREF(enum_obj);
        self->enum_type = enum_obj;
    }

    return 0;
}

void PyDiscreteMap::dealloc(PyDiscreteMapObject* self)
{
    if (self->values) {
        delete[] self->values;
        self->values = nullptr;
    }
    Py_XDECREF(self->enum_type);
    self->enum_type = nullptr;
    Py_TYPE(self)->tp_free((PyObject*)self);
}

PyObject* PyDiscreteMap::repr(PyObject* obj)
{
    PyDiscreteMapObject* self = (PyDiscreteMapObject*)obj;
    std::ostringstream ss;

    if (self->values) {
        ss << "<DiscreteMap (" << self->w << " x " << self->h << ")";
        if (self->enum_type && self->enum_type != Py_None) {
            PyObject* name = PyObject_GetAttrString(self->enum_type, "__name__");
            if (name) {
                ss << " enum=" << PyUnicode_AsUTF8(name);
                Py_DECREF(name);
            } else {
                PyErr_Clear();
            }
        }
        ss << ">";
    } else {
        ss << "<DiscreteMap (uninitialized)>";
    }

    return PyUnicode_FromString(ss.str().c_str());
}

// ============================================================================
// Properties
// ============================================================================

PyObject* PyDiscreteMap::get_size(PyDiscreteMapObject* self, void* closure)
{
    if (!self->values) {
        PyErr_SetString(PyExc_RuntimeError, "DiscreteMap not initialized");
        return nullptr;
    }
    return Py_BuildValue("(ii)", self->w, self->h);
}

PyObject* PyDiscreteMap::get_enum_type(PyDiscreteMapObject* self, void* closure)
{
    if (self->enum_type) {
        Py_INCREF(self->enum_type);
        return self->enum_type;
    }
    Py_RETURN_NONE;
}

int PyDiscreteMap::set_enum_type(PyDiscreteMapObject* self, PyObject* value, void* closure)
{
    Py_XDECREF(self->enum_type);
    if (value && value != Py_None) {
        Py_INCREF(value);
        self->enum_type = value;
    } else {
        self->enum_type = nullptr;
    }
    return 0;
}

// ============================================================================
// Basic Operations
// ============================================================================

PyObject* PyDiscreteMap::fill(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"value", "pos", "size", nullptr};
    PyObject* value_obj;
    PyObject* pos = nullptr;
    PyObject* size = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OO", const_cast<char**>(kwlist),
                                     &value_obj, &pos, &size)) {
        return nullptr;
    }

    if (!self->values) {
        PyErr_SetString(PyExc_RuntimeError, "DiscreteMap not initialized");
        return nullptr;
    }

    int value;
    if (!parseIntValue(value_obj, &value)) {
        return nullptr;
    }

    if (value < 0 || value > 255) {
        PyErr_SetString(PyExc_ValueError, "value must be in range 0-255");
        return nullptr;
    }

    // Parse region parameters
    MapRegion region;
    if (!parseMapRegionScalar(self->w, self->h, pos, size, region)) {
        return nullptr;
    }

    // Fill the region
    MapOps::fill<Uint8Policy>(self->values, self->w, self->h,
                              static_cast<uint8_t>(value), region);

    Py_INCREF(self);
    return (PyObject*)self;
}

PyObject* PyDiscreteMap::clear(PyDiscreteMapObject* self, PyObject* Py_UNUSED(args))
{
    if (!self->values) {
        PyErr_SetString(PyExc_RuntimeError, "DiscreteMap not initialized");
        return nullptr;
    }

    memset(self->values, 0, static_cast<size_t>(self->w) * static_cast<size_t>(self->h));

    Py_INCREF(self);
    return (PyObject*)self;
}

// ============================================================================
// Cell Access
// ============================================================================

PyObject* PyDiscreteMap::get(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds)
{
    if (!self->values) {
        PyErr_SetString(PyExc_RuntimeError, "DiscreteMap not initialized");
        return nullptr;
    }

    int x, y;
    if (!PyPosition_ParseInt(args, kwds, &x, &y)) {
        return nullptr;
    }

    // Bounds check
    if (x < 0 || x >= self->w || y < 0 || y >= self->h) {
        PyErr_Format(PyExc_IndexError,
            "Position (%d, %d) out of bounds for DiscreteMap of size (%d, %d)",
            x, y, self->w, self->h);
        return nullptr;
    }

    uint8_t value = self->values[y * self->w + x];
    return valueToResult(value, self->enum_type);
}

PyObject* PyDiscreteMap::set(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"x", "y", "value", nullptr};
    int x, y;
    PyObject* value_obj;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "iiO", const_cast<char**>(kwlist),
                                     &x, &y, &value_obj)) {
        return nullptr;
    }

    if (!self->values) {
        PyErr_SetString(PyExc_RuntimeError, "DiscreteMap not initialized");
        return nullptr;
    }

    // Bounds check
    if (x < 0 || x >= self->w || y < 0 || y >= self->h) {
        PyErr_Format(PyExc_IndexError,
            "Position (%d, %d) out of bounds for DiscreteMap of size (%d, %d)",
            x, y, self->w, self->h);
        return nullptr;
    }

    int value;
    if (!parseIntValue(value_obj, &value)) {
        return nullptr;
    }

    if (value < 0 || value > 255) {
        PyErr_SetString(PyExc_ValueError, "value must be in range 0-255");
        return nullptr;
    }

    self->values[y * self->w + x] = static_cast<uint8_t>(value);

    Py_RETURN_NONE;
}

PyObject* PyDiscreteMap::subscript(PyDiscreteMapObject* self, PyObject* key)
{
    if (!self->values) {
        PyErr_SetString(PyExc_RuntimeError, "DiscreteMap not initialized");
        return nullptr;
    }

    int x, y;
    if (!PyPosition_FromObjectInt(key, &x, &y)) {
        return nullptr;
    }

    // Bounds check
    if (x < 0 || x >= self->w || y < 0 || y >= self->h) {
        PyErr_Format(PyExc_IndexError,
            "Position (%d, %d) out of bounds for DiscreteMap of size (%d, %d)",
            x, y, self->w, self->h);
        return nullptr;
    }

    uint8_t value = self->values[y * self->w + x];
    return valueToResult(value, self->enum_type);
}

int PyDiscreteMap::subscript_assign(PyDiscreteMapObject* self, PyObject* key, PyObject* value)
{
    if (!self->values) {
        PyErr_SetString(PyExc_RuntimeError, "DiscreteMap not initialized");
        return -1;
    }

    // Handle deletion (not supported)
    if (value == nullptr) {
        PyErr_SetString(PyExc_TypeError, "cannot delete DiscreteMap elements");
        return -1;
    }

    int x, y;
    if (!PyPosition_FromObjectInt(key, &x, &y)) {
        return -1;
    }

    // Bounds check
    if (x < 0 || x >= self->w || y < 0 || y >= self->h) {
        PyErr_Format(PyExc_IndexError,
            "Position (%d, %d) out of bounds for DiscreteMap of size (%d, %d)",
            x, y, self->w, self->h);
        return -1;
    }

    int ival;
    if (!parseIntValue(value, &ival)) {
        return -1;
    }

    if (ival < 0 || ival > 255) {
        PyErr_SetString(PyExc_ValueError, "value must be in range 0-255");
        return -1;
    }

    self->values[y * self->w + x] = static_cast<uint8_t>(ival);
    return 0;
}

// ============================================================================
// Combination Operations
// ============================================================================

PyObject* PyDiscreteMap::add(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"other", "pos", "source_pos", "size", nullptr};
    PyObject* other_obj;
    PyObject* pos = nullptr;
    PyObject* source_pos = nullptr;
    PyObject* size = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OOO", const_cast<char**>(kwlist),
                                     &other_obj, &pos, &source_pos, &size)) {
        return nullptr;
    }

    if (!self->values) {
        PyErr_SetString(PyExc_RuntimeError, "DiscreteMap not initialized");
        return nullptr;
    }

    // Check if scalar or DiscreteMap
    int scalar_val;
    if (parseIntValue(other_obj, &scalar_val)) {
        // Scalar add
        MapRegion region;
        if (!parseMapRegionScalar(self->w, self->h, pos, size, region)) {
            return nullptr;
        }
        MapOps::add_scalar<Uint8Policy>(self->values, self->w, self->h,
                                        Uint8Policy::clamp(scalar_val), region);
    } else {
        PyErr_Clear();  // Clear the parseIntValue error

        PyDiscreteMapObject* other = validateOtherDiscreteMapType(other_obj, "add");
        if (!other) return nullptr;

        MapRegion region;
        if (!parseMapRegion(self->w, self->h, other->w, other->h,
                           pos, source_pos, size, region)) {
            return nullptr;
        }
        MapOps::add<Uint8Policy>(self->values, other->values, region);
    }

    Py_INCREF(self);
    return (PyObject*)self;
}

PyObject* PyDiscreteMap::subtract(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"other", "pos", "source_pos", "size", nullptr};
    PyObject* other_obj;
    PyObject* pos = nullptr;
    PyObject* source_pos = nullptr;
    PyObject* size = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OOO", const_cast<char**>(kwlist),
                                     &other_obj, &pos, &source_pos, &size)) {
        return nullptr;
    }

    if (!self->values) {
        PyErr_SetString(PyExc_RuntimeError, "DiscreteMap not initialized");
        return nullptr;
    }

    // Check if scalar or DiscreteMap
    int scalar_val;
    if (parseIntValue(other_obj, &scalar_val)) {
        // Scalar subtract (add negative)
        MapRegion region;
        if (!parseMapRegionScalar(self->w, self->h, pos, size, region)) {
            return nullptr;
        }
        // Subtract by adding negative (with saturation)
        for (int y = 0; y < region.height; y++) {
            for (int x = 0; x < region.width; x++) {
                int idx = region.dest_idx(x, y);
                int result = static_cast<int>(self->values[idx]) - scalar_val;
                self->values[idx] = Uint8Policy::clamp(result);
            }
        }
    } else {
        PyErr_Clear();

        PyDiscreteMapObject* other = validateOtherDiscreteMapType(other_obj, "subtract");
        if (!other) return nullptr;

        MapRegion region;
        if (!parseMapRegion(self->w, self->h, other->w, other->h,
                           pos, source_pos, size, region)) {
            return nullptr;
        }
        MapOps::subtract<Uint8Policy>(self->values, other->values, region);
    }

    Py_INCREF(self);
    return (PyObject*)self;
}

PyObject* PyDiscreteMap::multiply(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"factor", "pos", "size", nullptr};
    float factor;
    PyObject* pos = nullptr;
    PyObject* size = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "f|OO", const_cast<char**>(kwlist),
                                     &factor, &pos, &size)) {
        return nullptr;
    }

    if (!self->values) {
        PyErr_SetString(PyExc_RuntimeError, "DiscreteMap not initialized");
        return nullptr;
    }

    MapRegion region;
    if (!parseMapRegionScalar(self->w, self->h, pos, size, region)) {
        return nullptr;
    }

    MapOps::multiply_scalar<Uint8Policy>(self->values, self->w, self->h, factor, region);

    Py_INCREF(self);
    return (PyObject*)self;
}

PyObject* PyDiscreteMap::copy_from(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"other", "pos", "source_pos", "size", nullptr};
    PyObject* other_obj;
    PyObject* pos = nullptr;
    PyObject* source_pos = nullptr;
    PyObject* size = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OOO", const_cast<char**>(kwlist),
                                     &other_obj, &pos, &source_pos, &size)) {
        return nullptr;
    }

    if (!self->values) {
        PyErr_SetString(PyExc_RuntimeError, "DiscreteMap not initialized");
        return nullptr;
    }

    PyDiscreteMapObject* other = validateOtherDiscreteMapType(other_obj, "copy_from");
    if (!other) return nullptr;

    MapRegion region;
    if (!parseMapRegion(self->w, self->h, other->w, other->h,
                       pos, source_pos, size, region)) {
        return nullptr;
    }

    MapOps::copy<Uint8Policy>(self->values, other->values, region);

    Py_INCREF(self);
    return (PyObject*)self;
}

PyObject* PyDiscreteMap::dmap_max(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"other", "pos", "source_pos", "size", nullptr};
    PyObject* other_obj;
    PyObject* pos = nullptr;
    PyObject* source_pos = nullptr;
    PyObject* size = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OOO", const_cast<char**>(kwlist),
                                     &other_obj, &pos, &source_pos, &size)) {
        return nullptr;
    }

    if (!self->values) {
        PyErr_SetString(PyExc_RuntimeError, "DiscreteMap not initialized");
        return nullptr;
    }

    PyDiscreteMapObject* other = validateOtherDiscreteMapType(other_obj, "max");
    if (!other) return nullptr;

    MapRegion region;
    if (!parseMapRegion(self->w, self->h, other->w, other->h,
                       pos, source_pos, size, region)) {
        return nullptr;
    }

    MapOps::element_max<Uint8Policy>(self->values, other->values, region);

    Py_INCREF(self);
    return (PyObject*)self;
}

PyObject* PyDiscreteMap::dmap_min(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"other", "pos", "source_pos", "size", nullptr};
    PyObject* other_obj;
    PyObject* pos = nullptr;
    PyObject* source_pos = nullptr;
    PyObject* size = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OOO", const_cast<char**>(kwlist),
                                     &other_obj, &pos, &source_pos, &size)) {
        return nullptr;
    }

    if (!self->values) {
        PyErr_SetString(PyExc_RuntimeError, "DiscreteMap not initialized");
        return nullptr;
    }

    PyDiscreteMapObject* other = validateOtherDiscreteMapType(other_obj, "min");
    if (!other) return nullptr;

    MapRegion region;
    if (!parseMapRegion(self->w, self->h, other->w, other->h,
                       pos, source_pos, size, region)) {
        return nullptr;
    }

    MapOps::element_min<Uint8Policy>(self->values, other->values, region);

    Py_INCREF(self);
    return (PyObject*)self;
}

// ============================================================================
// Bitwise Operations
// ============================================================================

PyObject* PyDiscreteMap::bitwise_and(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"other", "pos", "source_pos", "size", nullptr};
    PyObject* other_obj;
    PyObject* pos = nullptr;
    PyObject* source_pos = nullptr;
    PyObject* size = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OOO", const_cast<char**>(kwlist),
                                     &other_obj, &pos, &source_pos, &size)) {
        return nullptr;
    }

    if (!self->values) {
        PyErr_SetString(PyExc_RuntimeError, "DiscreteMap not initialized");
        return nullptr;
    }

    PyDiscreteMapObject* other = validateOtherDiscreteMapType(other_obj, "bitwise_and");
    if (!other) return nullptr;

    MapRegion region;
    if (!parseMapRegion(self->w, self->h, other->w, other->h,
                       pos, source_pos, size, region)) {
        return nullptr;
    }

    MapBitwise::bitwise_and(self->values, other->values, region);

    Py_INCREF(self);
    return (PyObject*)self;
}

PyObject* PyDiscreteMap::bitwise_or(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"other", "pos", "source_pos", "size", nullptr};
    PyObject* other_obj;
    PyObject* pos = nullptr;
    PyObject* source_pos = nullptr;
    PyObject* size = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OOO", const_cast<char**>(kwlist),
                                     &other_obj, &pos, &source_pos, &size)) {
        return nullptr;
    }

    if (!self->values) {
        PyErr_SetString(PyExc_RuntimeError, "DiscreteMap not initialized");
        return nullptr;
    }

    PyDiscreteMapObject* other = validateOtherDiscreteMapType(other_obj, "bitwise_or");
    if (!other) return nullptr;

    MapRegion region;
    if (!parseMapRegion(self->w, self->h, other->w, other->h,
                       pos, source_pos, size, region)) {
        return nullptr;
    }

    MapBitwise::bitwise_or(self->values, other->values, region);

    Py_INCREF(self);
    return (PyObject*)self;
}

PyObject* PyDiscreteMap::bitwise_xor(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"other", "pos", "source_pos", "size", nullptr};
    PyObject* other_obj;
    PyObject* pos = nullptr;
    PyObject* source_pos = nullptr;
    PyObject* size = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OOO", const_cast<char**>(kwlist),
                                     &other_obj, &pos, &source_pos, &size)) {
        return nullptr;
    }

    if (!self->values) {
        PyErr_SetString(PyExc_RuntimeError, "DiscreteMap not initialized");
        return nullptr;
    }

    PyDiscreteMapObject* other = validateOtherDiscreteMapType(other_obj, "bitwise_xor");
    if (!other) return nullptr;

    MapRegion region;
    if (!parseMapRegion(self->w, self->h, other->w, other->h,
                       pos, source_pos, size, region)) {
        return nullptr;
    }

    MapBitwise::bitwise_xor(self->values, other->values, region);

    Py_INCREF(self);
    return (PyObject*)self;
}

PyObject* PyDiscreteMap::invert(PyDiscreteMapObject* self, PyObject* Py_UNUSED(args))
{
    if (!self->values) {
        PyErr_SetString(PyExc_RuntimeError, "DiscreteMap not initialized");
        return nullptr;
    }

    // Create new DiscreteMap with same dimensions
    PyDiscreteMapObject* result = CreateNewDiscreteMap(self->w, self->h);
    if (!result) {
        return nullptr;
    }

    // Copy enum type
    if (self->enum_type) {
        Py_INCREF(self->enum_type);
        result->enum_type = self->enum_type;
    }

    // Set (255 - value) for each cell
    size_t total = static_cast<size_t>(self->w) * static_cast<size_t>(self->h);
    for (size_t i = 0; i < total; i++) {
        result->values[i] = 255 - self->values[i];
    }

    return (PyObject*)result;
}

// ============================================================================
// Query Methods
// ============================================================================

PyObject* PyDiscreteMap::count(PyDiscreteMapObject* self, PyObject* args)
{
    PyObject* value_obj;
    if (!PyArg_ParseTuple(args, "O", &value_obj)) {
        return nullptr;
    }

    if (!self->values) {
        PyErr_SetString(PyExc_RuntimeError, "DiscreteMap not initialized");
        return nullptr;
    }

    int value;
    if (!parseIntValue(value_obj, &value)) {
        return nullptr;
    }

    if (value < 0 || value > 255) {
        PyErr_SetString(PyExc_ValueError, "value must be in range 0-255");
        return nullptr;
    }

    uint8_t target = static_cast<uint8_t>(value);
    long count = 0;
    size_t total = static_cast<size_t>(self->w) * static_cast<size_t>(self->h);
    for (size_t i = 0; i < total; i++) {
        if (self->values[i] == target) count++;
    }

    return PyLong_FromLong(count);
}

PyObject* PyDiscreteMap::count_range(PyDiscreteMapObject* self, PyObject* args)
{
    int min_val, max_val;
    if (!PyArg_ParseTuple(args, "ii", &min_val, &max_val)) {
        return nullptr;
    }

    if (!self->values) {
        PyErr_SetString(PyExc_RuntimeError, "DiscreteMap not initialized");
        return nullptr;
    }

    if (min_val > max_val) {
        PyErr_SetString(PyExc_ValueError, "min must be <= max");
        return nullptr;
    }

    // Clamp to valid range
    min_val = std::max(0, min_val);
    max_val = std::min(255, max_val);

    long count = 0;
    size_t total = static_cast<size_t>(self->w) * static_cast<size_t>(self->h);
    for (size_t i = 0; i < total; i++) {
        int v = self->values[i];
        if (v >= min_val && v <= max_val) count++;
    }

    return PyLong_FromLong(count);
}

PyObject* PyDiscreteMap::min_max(PyDiscreteMapObject* self, PyObject* Py_UNUSED(args))
{
    if (!self->values) {
        PyErr_SetString(PyExc_RuntimeError, "DiscreteMap not initialized");
        return nullptr;
    }

    size_t total = static_cast<size_t>(self->w) * static_cast<size_t>(self->h);
    if (total == 0) {
        return Py_BuildValue("(ii)", 0, 0);
    }

    uint8_t min_val = self->values[0];
    uint8_t max_val = self->values[0];

    for (size_t i = 1; i < total; i++) {
        if (self->values[i] < min_val) min_val = self->values[i];
        if (self->values[i] > max_val) max_val = self->values[i];
    }

    return Py_BuildValue("(ii)", min_val, max_val);
}

PyObject* PyDiscreteMap::histogram(PyDiscreteMapObject* self, PyObject* Py_UNUSED(args))
{
    if (!self->values) {
        PyErr_SetString(PyExc_RuntimeError, "DiscreteMap not initialized");
        return nullptr;
    }

    // Count occurrences of each value
    long counts[256] = {0};
    size_t total = static_cast<size_t>(self->w) * static_cast<size_t>(self->h);
    for (size_t i = 0; i < total; i++) {
        counts[self->values[i]]++;
    }

    // Build dict with only non-zero counts
    PyObject* result = PyDict_New();
    if (!result) return nullptr;

    for (int v = 0; v < 256; v++) {
        if (counts[v] > 0) {
            PyObject* key = PyLong_FromLong(v);
            PyObject* val = PyLong_FromLong(counts[v]);
            if (!key || !val || PyDict_SetItem(result, key, val) < 0) {
                Py_XDECREF(key);
                Py_XDECREF(val);
                Py_DECREF(result);
                return nullptr;
            }
            Py_DECREF(key);
            Py_DECREF(val);
        }
    }

    return result;
}

// ============================================================================
// Boolean/Mask Operations
// ============================================================================

PyObject* PyDiscreteMap::to_bool(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"condition", nullptr};
    PyObject* condition;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O", const_cast<char**>(kwlist),
                                     &condition)) {
        return nullptr;
    }

    if (!self->values) {
        PyErr_SetString(PyExc_RuntimeError, "DiscreteMap not initialized");
        return nullptr;
    }

    // Create new DiscreteMap
    PyDiscreteMapObject* result = CreateNewDiscreteMap(self->w, self->h);
    if (!result) {
        return nullptr;
    }

    size_t total = static_cast<size_t>(self->w) * static_cast<size_t>(self->h);

    // Case 1: Integer - match exactly
    int int_val;
    if (parseIntValue(condition, &int_val)) {
        if (int_val < 0 || int_val > 255) {
            Py_DECREF(result);
            PyErr_SetString(PyExc_ValueError, "condition value must be in range 0-255");
            return nullptr;
        }
        uint8_t target = static_cast<uint8_t>(int_val);
        for (size_t i = 0; i < total; i++) {
            result->values[i] = (self->values[i] == target) ? 1 : 0;
        }
        return (PyObject*)result;
    }
    PyErr_Clear();

    // Case 2: Set - match any value in set
    if (PySet_Check(condition) || PyFrozenSet_Check(condition)) {
        // Build quick lookup array
        bool match[256] = {false};
        PyObject* iter = PyObject_GetIter(condition);
        if (!iter) {
            Py_DECREF(result);
            return nullptr;
        }

        PyObject* item;
        while ((item = PyIter_Next(iter)) != nullptr) {
            int v;
            if (!parseIntValue(item, &v)) {
                Py_DECREF(item);
                Py_DECREF(iter);
                Py_DECREF(result);
                return nullptr;
            }
            Py_DECREF(item);
            if (v >= 0 && v <= 255) {
                match[v] = true;
            }
        }
        Py_DECREF(iter);

        if (PyErr_Occurred()) {
            Py_DECREF(result);
            return nullptr;
        }

        for (size_t i = 0; i < total; i++) {
            result->values[i] = match[self->values[i]] ? 1 : 0;
        }
        return (PyObject*)result;
    }

    // Case 3: Callable - predicate function
    if (PyCallable_Check(condition)) {
        for (size_t i = 0; i < total; i++) {
            PyObject* arg = PyLong_FromLong(self->values[i]);
            PyObject* res = PyObject_CallOneArg(condition, arg);
            Py_DECREF(arg);

            if (!res) {
                Py_DECREF(result);
                return nullptr;
            }

            int truth = PyObject_IsTrue(res);
            Py_DECREF(res);

            if (truth < 0) {
                Py_DECREF(result);
                return nullptr;
            }

            result->values[i] = truth ? 1 : 0;
        }
        return (PyObject*)result;
    }

    Py_DECREF(result);
    PyErr_SetString(PyExc_TypeError,
        "condition must be an int, set of ints, or callable");
    return nullptr;
}

PyObject* PyDiscreteMap::mask(PyDiscreteMapObject* self, PyObject* Py_UNUSED(args))
{
    if (!self->values) {
        PyErr_SetString(PyExc_RuntimeError, "DiscreteMap not initialized");
        return nullptr;
    }

    // Create memoryview of the internal buffer
    Py_ssize_t len = static_cast<Py_ssize_t>(self->w) * static_cast<Py_ssize_t>(self->h);
    return PyMemoryView_FromMemory(reinterpret_cast<char*>(self->values), len, PyBUF_WRITE);
}

// ============================================================================
// HeightMap Integration
// ============================================================================

PyObject* PyDiscreteMap::from_heightmap(PyTypeObject* type, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"hmap", "mapping", "enum", nullptr};
    PyObject* hmap_obj;
    PyObject* mapping_obj;
    PyObject* enum_obj = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO|O", const_cast<char**>(kwlist),
                                     &hmap_obj, &mapping_obj, &enum_obj)) {
        return nullptr;
    }

    // Validate HeightMap
    PyObject* hmap_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "HeightMap");
    if (!hmap_type) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap type not found in module");
        return nullptr;
    }

    int is_hmap = PyObject_IsInstance(hmap_obj, hmap_type);
    Py_DECREF(hmap_type);

    if (is_hmap < 0) {
        return nullptr;
    }
    if (!is_hmap) {
        PyErr_SetString(PyExc_TypeError, "First argument must be a HeightMap");
        return nullptr;
    }

    PyHeightMapObject* hmap = (PyHeightMapObject*)hmap_obj;
    if (!hmap->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    // Parse mapping list: [((min, max), value), ...]
    if (!PyList_Check(mapping_obj)) {
        PyErr_SetString(PyExc_TypeError, "mapping must be a list of ((min, max), value) tuples");
        return nullptr;
    }

    struct RangeMapping {
        float min_val, max_val;
        uint8_t target;
    };
    std::vector<RangeMapping> mappings;

    Py_ssize_t n_mappings = PyList_Size(mapping_obj);
    for (Py_ssize_t i = 0; i < n_mappings; i++) {
        PyObject* item = PyList_GetItem(mapping_obj, i);

        if (!PyTuple_Check(item) || PyTuple_Size(item) != 2) {
            PyErr_SetString(PyExc_TypeError, "each mapping must be a ((min, max), value) tuple");
            return nullptr;
        }

        PyObject* range_obj = PyTuple_GetItem(item, 0);
        PyObject* target_obj = PyTuple_GetItem(item, 1);

        if (!PyTuple_Check(range_obj) || PyTuple_Size(range_obj) != 2) {
            PyErr_SetString(PyExc_TypeError, "range must be a (min, max) tuple");
            return nullptr;
        }

        RangeMapping rm;
        PyObject* min_obj = PyTuple_GetItem(range_obj, 0);
        PyObject* max_obj = PyTuple_GetItem(range_obj, 1);

        if (PyFloat_Check(min_obj)) rm.min_val = (float)PyFloat_AsDouble(min_obj);
        else if (PyLong_Check(min_obj)) rm.min_val = (float)PyLong_AsLong(min_obj);
        else {
            PyErr_SetString(PyExc_TypeError, "range values must be numeric");
            return nullptr;
        }

        if (PyFloat_Check(max_obj)) rm.max_val = (float)PyFloat_AsDouble(max_obj);
        else if (PyLong_Check(max_obj)) rm.max_val = (float)PyLong_AsLong(max_obj);
        else {
            PyErr_SetString(PyExc_TypeError, "range values must be numeric");
            return nullptr;
        }

        int target_val;
        if (!parseIntValue(target_obj, &target_val)) {
            return nullptr;
        }
        if (target_val < 0 || target_val > 255) {
            PyErr_SetString(PyExc_ValueError, "target value must be in range 0-255");
            return nullptr;
        }
        rm.target = static_cast<uint8_t>(target_val);

        mappings.push_back(rm);
    }

    // Create new DiscreteMap
    int width = hmap->heightmap->w;
    int height = hmap->heightmap->h;

    PyDiscreteMapObject* result = CreateNewDiscreteMap(width, height);
    if (!result) {
        return nullptr;
    }

    // Store enum type if provided
    if (enum_obj && enum_obj != Py_None) {
        Py_INCREF(enum_obj);
        result->enum_type = enum_obj;
    }

    // Apply mappings
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            float val = hmap->heightmap->values[y * width + x];
            uint8_t mapped = 0;  // Default if no mapping matches

            for (const auto& rm : mappings) {
                if (val >= rm.min_val && val <= rm.max_val) {
                    mapped = rm.target;
                    break;  // First match wins
                }
            }

            result->values[y * width + x] = mapped;
        }
    }

    return (PyObject*)result;
}

PyObject* PyDiscreteMap::to_heightmap(PyDiscreteMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"mapping", nullptr};
    PyObject* mapping_obj = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|O", const_cast<char**>(kwlist),
                                     &mapping_obj)) {
        return nullptr;
    }

    if (!self->values) {
        PyErr_SetString(PyExc_RuntimeError, "DiscreteMap not initialized");
        return nullptr;
    }

    // Parse optional mapping dict
    float value_map[256];
    bool has_mapping = false;

    if (mapping_obj && mapping_obj != Py_None) {
        if (!PyDict_Check(mapping_obj)) {
            PyErr_SetString(PyExc_TypeError, "mapping must be a dict");
            return nullptr;
        }

        // Initialize to direct cast as default
        for (int i = 0; i < 256; i++) {
            value_map[i] = static_cast<float>(i);
        }

        // Override with mapping values
        PyObject* key;
        PyObject* value;
        Py_ssize_t pos = 0;
        while (PyDict_Next(mapping_obj, &pos, &key, &value)) {
            int k;
            if (!parseIntValue(key, &k)) {
                return nullptr;
            }
            if (k < 0 || k > 255) {
                PyErr_SetString(PyExc_ValueError, "mapping keys must be in range 0-255");
                return nullptr;
            }

            float v;
            if (PyFloat_Check(value)) v = (float)PyFloat_AsDouble(value);
            else if (PyLong_Check(value)) v = (float)PyLong_AsLong(value);
            else {
                PyErr_SetString(PyExc_TypeError, "mapping values must be numeric");
                return nullptr;
            }

            value_map[k] = v;
        }
        has_mapping = true;
    }

    // Get HeightMap type and create new instance
    PyObject* hmap_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "HeightMap");
    if (!hmap_type) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap type not found in module");
        return nullptr;
    }

    PyObject* size_tuple = Py_BuildValue("(ii)", self->w, self->h);
    if (!size_tuple) {
        Py_DECREF(hmap_type);
        return nullptr;
    }

    PyObject* hmap_args = PyTuple_Pack(1, size_tuple);
    Py_DECREF(size_tuple);
    if (!hmap_args) {
        Py_DECREF(hmap_type);
        return nullptr;
    }

    PyHeightMapObject* result = (PyHeightMapObject*)PyObject_Call(hmap_type, hmap_args, nullptr);
    Py_DECREF(hmap_args);
    Py_DECREF(hmap_type);

    if (!result) {
        return nullptr;
    }

    // Copy values with optional mapping
    size_t total = static_cast<size_t>(self->w) * static_cast<size_t>(self->h);
    for (size_t i = 0; i < total; i++) {
        if (has_mapping) {
            result->heightmap->values[i] = value_map[self->values[i]];
        } else {
            result->heightmap->values[i] = static_cast<float>(self->values[i]);
        }
    }

    return (PyObject*)result;
}
