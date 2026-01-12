#include "PyHeightMap.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"
#include "PyPositionHelper.h"  // Standardized position argument parsing
#include <sstream>
#include <cstdlib>  // For random seed handling
#include <ctime>    // For time-based seeds

// Property definitions
PyGetSetDef PyHeightMap::getsetters[] = {
    {"size", (getter)PyHeightMap::get_size, NULL,
     MCRF_PROPERTY(size, "Dimensions (width, height) of the heightmap. Read-only."), NULL},
    {NULL}
};

// Mapping methods for subscript support (hmap[x, y])
PyMappingMethods PyHeightMap::mapping_methods = {
    .mp_length = nullptr,  // __len__ not needed
    .mp_subscript = (binaryfunc)PyHeightMap::subscript,  // __getitem__
    .mp_ass_subscript = nullptr  // __setitem__ (read-only for now)
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
    // Query methods (#196)
    {"get", (PyCFunction)PyHeightMap::get, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, get,
         MCRF_SIG("(x, y) or (pos)", "float"),
         MCRF_DESC("Get the height value at integer coordinates."),
         MCRF_ARGS_START
         MCRF_ARG("x, y", "Position as two ints, tuple, list, or Vector")
         MCRF_RETURNS("float: Height value at that position")
         MCRF_RAISES("IndexError", "Position is out of bounds")
     )},
    {"get_interpolated", (PyCFunction)PyHeightMap::get_interpolated, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, get_interpolated,
         MCRF_SIG("(x, y) or (pos)", "float"),
         MCRF_DESC("Get interpolated height value at non-integer coordinates."),
         MCRF_ARGS_START
         MCRF_ARG("x, y", "Position as two floats, tuple, list, or Vector")
         MCRF_RETURNS("float: Bilinearly interpolated height value")
     )},
    {"get_slope", (PyCFunction)PyHeightMap::get_slope, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, get_slope,
         MCRF_SIG("(x, y) or (pos)", "float"),
         MCRF_DESC("Get the slope at integer coordinates, from 0 (flat) to pi/2 (vertical)."),
         MCRF_ARGS_START
         MCRF_ARG("x, y", "Position as two ints, tuple, list, or Vector")
         MCRF_RETURNS("float: Slope angle in radians (0 to pi/2)")
         MCRF_RAISES("IndexError", "Position is out of bounds")
     )},
    {"get_normal", (PyCFunction)PyHeightMap::get_normal, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, get_normal,
         MCRF_SIG("(x, y, water_level=0.0) or (pos, water_level=0.0)", "tuple[float, float, float]"),
         MCRF_DESC("Get the normal vector at given coordinates for lighting calculations."),
         MCRF_ARGS_START
         MCRF_ARG("x, y", "Position as two floats, tuple, list, or Vector")
         MCRF_ARG("water_level", "Water level below which terrain is considered flat (default 0.0)")
         MCRF_RETURNS("tuple[float, float, float]: Normal vector (nx, ny, nz)")
     )},
    {"min_max", (PyCFunction)PyHeightMap::min_max, METH_NOARGS,
     MCRF_METHOD(HeightMap, min_max,
         MCRF_SIG("()", "tuple[float, float]"),
         MCRF_DESC("Get the minimum and maximum height values in the map."),
         MCRF_RETURNS("tuple[float, float]: (min_value, max_value)")
     )},
    {"count_in_range", (PyCFunction)PyHeightMap::count_in_range, METH_VARARGS,
     MCRF_METHOD(HeightMap, count_in_range,
         MCRF_SIG("(range: tuple[float, float])", "int"),
         MCRF_DESC("Count cells with values in the specified range (inclusive)."),
         MCRF_ARGS_START
         MCRF_ARG("range", "Value range as (min, max) tuple or list")
         MCRF_RETURNS("int: Number of cells with values in range")
         MCRF_RAISES("ValueError", "min > max")
     )},
    // Threshold operations (#197) - return NEW HeightMaps
    {"threshold", (PyCFunction)PyHeightMap::threshold, METH_VARARGS,
     MCRF_METHOD(HeightMap, threshold,
         MCRF_SIG("(range: tuple[float, float])", "HeightMap"),
         MCRF_DESC("Return NEW HeightMap with original values where in range, 0.0 elsewhere."),
         MCRF_ARGS_START
         MCRF_ARG("range", "Value range as (min, max) tuple or list, inclusive")
         MCRF_RETURNS("HeightMap: New HeightMap (original is unchanged)")
         MCRF_RAISES("ValueError", "min > max")
     )},
    {"threshold_binary", (PyCFunction)PyHeightMap::threshold_binary, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, threshold_binary,
         MCRF_SIG("(range: tuple[float, float], value: float = 1.0)", "HeightMap"),
         MCRF_DESC("Return NEW HeightMap with uniform value where in range, 0.0 elsewhere."),
         MCRF_ARGS_START
         MCRF_ARG("range", "Value range as (min, max) tuple or list, inclusive")
         MCRF_ARG("value", "Value to set for cells in range (default 1.0)")
         MCRF_RETURNS("HeightMap: New HeightMap (original is unchanged)")
         MCRF_RAISES("ValueError", "min > max")
     )},
    {"inverse", (PyCFunction)PyHeightMap::inverse, METH_NOARGS,
     MCRF_METHOD(HeightMap, inverse,
         MCRF_SIG("()", "HeightMap"),
         MCRF_DESC("Return NEW HeightMap with (1.0 - value) for each cell."),
         MCRF_RETURNS("HeightMap: New inverted HeightMap (original is unchanged)")
     )},
    // Terrain generation methods (#195)
    {"add_hill", (PyCFunction)PyHeightMap::add_hill, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, add_hill,
         MCRF_SIG("(center, radius: float, height: float)", "HeightMap"),
         MCRF_DESC("Add a smooth hill at the specified position."),
         MCRF_ARGS_START
         MCRF_ARG("center", "Center position as (x, y) tuple, list, or Vector")
         MCRF_ARG("radius", "Radius of the hill in cells")
         MCRF_ARG("height", "Height of the hill peak")
         MCRF_RETURNS("HeightMap: self, for method chaining")
     )},
    {"dig_hill", (PyCFunction)PyHeightMap::dig_hill, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, dig_hill,
         MCRF_SIG("(center, radius: float, target_height: float)", "HeightMap"),
         MCRF_DESC("Construct a pit or crater with the specified center height."),
         MCRF_ARGS_START
         MCRF_ARG("center", "Center position as (x, y) tuple, list, or Vector")
         MCRF_ARG("radius", "Radius of the crater in cells")
         MCRF_ARG("target_height", "Height at the center of the pit")
         MCRF_RETURNS("HeightMap: self, for method chaining")
         MCRF_NOTE("Only lowers cells; cells below target_height are unchanged")
     )},
    {"add_voronoi", (PyCFunction)PyHeightMap::add_voronoi, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, add_voronoi,
         MCRF_SIG("(num_points: int, coefficients: tuple = (1.0, -0.5), seed: int = None)", "HeightMap"),
         MCRF_DESC("Add Voronoi-based terrain features."),
         MCRF_ARGS_START
         MCRF_ARG("num_points", "Number of Voronoi seed points")
         MCRF_ARG("coefficients", "Coefficients for distance calculations (default: (1.0, -0.5))")
         MCRF_ARG("seed", "Random seed (None for random)")
         MCRF_RETURNS("HeightMap: self, for method chaining")
     )},
    {"mid_point_displacement", (PyCFunction)PyHeightMap::mid_point_displacement, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, mid_point_displacement,
         MCRF_SIG("(roughness: float = 0.5, seed: int = None)", "HeightMap"),
         MCRF_DESC("Generate terrain using midpoint displacement algorithm (diamond-square)."),
         MCRF_ARGS_START
         MCRF_ARG("roughness", "Controls terrain roughness (0.0-1.0, default 0.5)")
         MCRF_ARG("seed", "Random seed (None for random)")
         MCRF_RETURNS("HeightMap: self, for method chaining")
         MCRF_NOTE("Works best with power-of-2+1 dimensions (e.g., 65x65, 129x129)")
     )},
    {"rain_erosion", (PyCFunction)PyHeightMap::rain_erosion, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, rain_erosion,
         MCRF_SIG("(drops: int, erosion: float = 0.1, sedimentation: float = 0.05, seed: int = None)", "HeightMap"),
         MCRF_DESC("Simulate rain erosion on the terrain."),
         MCRF_ARGS_START
         MCRF_ARG("drops", "Number of rain drops to simulate")
         MCRF_ARG("erosion", "Erosion coefficient (default 0.1)")
         MCRF_ARG("sedimentation", "Sedimentation coefficient (default 0.05)")
         MCRF_ARG("seed", "Random seed (None for random)")
         MCRF_RETURNS("HeightMap: self, for method chaining")
     )},
    {"dig_bezier", (PyCFunction)PyHeightMap::dig_bezier, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, dig_bezier,
         MCRF_SIG("(points: tuple, start_radius: float, end_radius: float, start_height: float, end_height: float)", "HeightMap"),
         MCRF_DESC("Construct a canal along a cubic Bezier curve with specified heights."),
         MCRF_ARGS_START
         MCRF_ARG("points", "Four control points as ((x0,y0), (x1,y1), (x2,y2), (x3,y3))")
         MCRF_ARG("start_radius", "Radius at start of path")
         MCRF_ARG("end_radius", "Radius at end of path")
         MCRF_ARG("start_height", "Target height at start of path")
         MCRF_ARG("end_height", "Target height at end of path")
         MCRF_RETURNS("HeightMap: self, for method chaining")
         MCRF_NOTE("Only lowers cells; cells below target height are unchanged")
     )},
    {"smooth", (PyCFunction)PyHeightMap::smooth, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, smooth,
         MCRF_SIG("(iterations: int = 1)", "HeightMap"),
         MCRF_DESC("Smooth the heightmap by averaging neighboring cells."),
         MCRF_ARGS_START
         MCRF_ARG("iterations", "Number of smoothing passes (default 1)")
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

// Query methods (#196)

// Method: get(x, y) or get(pos) -> float
PyObject* PyHeightMap::get(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
{
    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    int x, y;
    if (!PyPosition_ParseInt(args, kwds, &x, &y)) {
        return nullptr;
    }

    // Bounds check
    if (x < 0 || x >= self->heightmap->w || y < 0 || y >= self->heightmap->h) {
        PyErr_Format(PyExc_IndexError,
            "Position (%d, %d) out of bounds for HeightMap of size (%d, %d)",
            x, y, self->heightmap->w, self->heightmap->h);
        return nullptr;
    }

    float value = TCOD_heightmap_get_value(self->heightmap, x, y);
    return PyFloat_FromDouble(value);
}

// Method: get_interpolated(x, y) or get_interpolated(pos) -> float
PyObject* PyHeightMap::get_interpolated(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
{
    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    float x, y;
    if (!PyPosition_ParseFloat(args, kwds, &x, &y)) {
        return nullptr;
    }

    float value = TCOD_heightmap_get_interpolated_value(self->heightmap, x, y);
    return PyFloat_FromDouble(value);
}

// Method: get_slope(x, y) or get_slope(pos) -> float
PyObject* PyHeightMap::get_slope(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
{
    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    int x, y;
    if (!PyPosition_ParseInt(args, kwds, &x, &y)) {
        return nullptr;
    }

    // Bounds check
    if (x < 0 || x >= self->heightmap->w || y < 0 || y >= self->heightmap->h) {
        PyErr_Format(PyExc_IndexError,
            "Position (%d, %d) out of bounds for HeightMap of size (%d, %d)",
            x, y, self->heightmap->w, self->heightmap->h);
        return nullptr;
    }

    float slope = TCOD_heightmap_get_slope(self->heightmap, x, y);
    return PyFloat_FromDouble(slope);
}

// Method: get_normal(x, y, water_level=0.0) or get_normal(pos, water_level=0.0) -> tuple[float, float, float]
PyObject* PyHeightMap::get_normal(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
{
    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    // Check for water_level keyword argument
    float water_level = 0.0f;
    if (kwds) {
        PyObject* wl_obj = PyDict_GetItemString(kwds, "water_level");
        if (wl_obj) {
            if (PyFloat_Check(wl_obj)) {
                water_level = (float)PyFloat_AsDouble(wl_obj);
            } else if (PyLong_Check(wl_obj)) {
                water_level = (float)PyLong_AsLong(wl_obj);
            } else {
                PyErr_SetString(PyExc_TypeError, "water_level must be a number");
                return nullptr;
            }
        }
    }

    float x, y;
    if (!PyPosition_ParseFloat(args, kwds, &x, &y)) {
        return nullptr;
    }

    float n[3];
    TCOD_heightmap_get_normal(self->heightmap, x, y, n, water_level);

    return Py_BuildValue("(fff)", n[0], n[1], n[2]);
}

// Method: min_max() -> tuple[float, float]
PyObject* PyHeightMap::min_max(PyHeightMapObject* self, PyObject* Py_UNUSED(args))
{
    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    float min_val, max_val;
    TCOD_heightmap_get_minmax(self->heightmap, &min_val, &max_val);

    return Py_BuildValue("(ff)", min_val, max_val);
}

// Method: count_in_range(range) -> int
PyObject* PyHeightMap::count_in_range(PyHeightMapObject* self, PyObject* args)
{
    PyObject* range_obj = nullptr;
    if (!PyArg_ParseTuple(args, "O", &range_obj)) {
        return nullptr;
    }

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    // Parse range from tuple or list
    float min_val, max_val;
    if (PyTuple_Check(range_obj) && PyTuple_Size(range_obj) == 2) {
        PyObject* min_obj = PyTuple_GetItem(range_obj, 0);
        PyObject* max_obj = PyTuple_GetItem(range_obj, 1);
        if (PyFloat_Check(min_obj)) min_val = (float)PyFloat_AsDouble(min_obj);
        else if (PyLong_Check(min_obj)) min_val = (float)PyLong_AsLong(min_obj);
        else { PyErr_SetString(PyExc_TypeError, "range values must be numeric"); return nullptr; }
        if (PyFloat_Check(max_obj)) max_val = (float)PyFloat_AsDouble(max_obj);
        else if (PyLong_Check(max_obj)) max_val = (float)PyLong_AsLong(max_obj);
        else { PyErr_SetString(PyExc_TypeError, "range values must be numeric"); return nullptr; }
    } else if (PyList_Check(range_obj) && PyList_Size(range_obj) == 2) {
        PyObject* min_obj = PyList_GetItem(range_obj, 0);
        PyObject* max_obj = PyList_GetItem(range_obj, 1);
        if (PyFloat_Check(min_obj)) min_val = (float)PyFloat_AsDouble(min_obj);
        else if (PyLong_Check(min_obj)) min_val = (float)PyLong_AsLong(min_obj);
        else { PyErr_SetString(PyExc_TypeError, "range values must be numeric"); return nullptr; }
        if (PyFloat_Check(max_obj)) max_val = (float)PyFloat_AsDouble(max_obj);
        else if (PyLong_Check(max_obj)) max_val = (float)PyLong_AsLong(max_obj);
        else { PyErr_SetString(PyExc_TypeError, "range values must be numeric"); return nullptr; }
    } else {
        PyErr_SetString(PyExc_TypeError, "range must be a tuple or list of (min, max)");
        return nullptr;
    }

    if (PyErr_Occurred()) {
        return nullptr;
    }

    // Validate range
    if (min_val > max_val) {
        PyErr_SetString(PyExc_ValueError, "range min must be less than or equal to max");
        return nullptr;
    }

    int count = TCOD_heightmap_count_cells(self->heightmap, min_val, max_val);
    return PyLong_FromLong(count);
}

// Subscript: hmap[x, y] -> float (shorthand for get())
PyObject* PyHeightMap::subscript(PyHeightMapObject* self, PyObject* key)
{
    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    int x, y;
    if (!PyPosition_FromObjectInt(key, &x, &y)) {
        return nullptr;
    }

    // Bounds check
    if (x < 0 || x >= self->heightmap->w || y < 0 || y >= self->heightmap->h) {
        PyErr_Format(PyExc_IndexError,
            "Position (%d, %d) out of bounds for HeightMap of size (%d, %d)",
            x, y, self->heightmap->w, self->heightmap->h);
        return nullptr;
    }

    float value = TCOD_heightmap_get_value(self->heightmap, x, y);
    return PyFloat_FromDouble(value);
}

// Threshold operations (#197) - return NEW HeightMaps

// Helper: Parse range from tuple or list
static bool ParseRange(PyObject* range_obj, float* min_val, float* max_val)
{
    if (PyTuple_Check(range_obj) && PyTuple_Size(range_obj) == 2) {
        PyObject* min_obj = PyTuple_GetItem(range_obj, 0);
        PyObject* max_obj = PyTuple_GetItem(range_obj, 1);
        if (PyFloat_Check(min_obj)) *min_val = (float)PyFloat_AsDouble(min_obj);
        else if (PyLong_Check(min_obj)) *min_val = (float)PyLong_AsLong(min_obj);
        else { PyErr_SetString(PyExc_TypeError, "range values must be numeric"); return false; }
        if (PyFloat_Check(max_obj)) *max_val = (float)PyFloat_AsDouble(max_obj);
        else if (PyLong_Check(max_obj)) *max_val = (float)PyLong_AsLong(max_obj);
        else { PyErr_SetString(PyExc_TypeError, "range values must be numeric"); return false; }
    } else if (PyList_Check(range_obj) && PyList_Size(range_obj) == 2) {
        PyObject* min_obj = PyList_GetItem(range_obj, 0);
        PyObject* max_obj = PyList_GetItem(range_obj, 1);
        if (PyFloat_Check(min_obj)) *min_val = (float)PyFloat_AsDouble(min_obj);
        else if (PyLong_Check(min_obj)) *min_val = (float)PyLong_AsLong(min_obj);
        else { PyErr_SetString(PyExc_TypeError, "range values must be numeric"); return false; }
        if (PyFloat_Check(max_obj)) *max_val = (float)PyFloat_AsDouble(max_obj);
        else if (PyLong_Check(max_obj)) *max_val = (float)PyLong_AsLong(max_obj);
        else { PyErr_SetString(PyExc_TypeError, "range values must be numeric"); return false; }
    } else {
        PyErr_SetString(PyExc_TypeError, "range must be a tuple or list of (min, max)");
        return false;
    }

    if (*min_val > *max_val) {
        PyErr_SetString(PyExc_ValueError, "range min must be less than or equal to max");
        return false;
    }

    return !PyErr_Occurred();
}

// Helper: Create a new HeightMap object with same dimensions
static PyHeightMapObject* CreateNewHeightMap(int width, int height)
{
    // Get the HeightMap type from the module
    PyObject* heightmap_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "HeightMap");
    if (!heightmap_type) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap type not found in module");
        return nullptr;
    }

    // Create size tuple
    PyObject* size_tuple = Py_BuildValue("(ii)", width, height);
    if (!size_tuple) {
        Py_DECREF(heightmap_type);
        return nullptr;
    }

    // Create args tuple containing the size tuple
    PyObject* args = PyTuple_Pack(1, size_tuple);
    Py_DECREF(size_tuple);
    if (!args) {
        Py_DECREF(heightmap_type);
        return nullptr;
    }

    // Create the new object
    PyHeightMapObject* new_hmap = (PyHeightMapObject*)PyObject_Call(heightmap_type, args, nullptr);
    Py_DECREF(args);
    Py_DECREF(heightmap_type);

    if (!new_hmap) {
        return nullptr;  // Python error already set
    }

    return new_hmap;
}

// Method: threshold(range) -> HeightMap
PyObject* PyHeightMap::threshold(PyHeightMapObject* self, PyObject* args)
{
    PyObject* range_obj = nullptr;
    if (!PyArg_ParseTuple(args, "O", &range_obj)) {
        return nullptr;
    }

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    float min_val, max_val;
    if (!ParseRange(range_obj, &min_val, &max_val)) {
        return nullptr;
    }

    // Create new HeightMap with same dimensions
    PyHeightMapObject* result = CreateNewHeightMap(self->heightmap->w, self->heightmap->h);
    if (!result) {
        return nullptr;
    }

    // Copy values that are in range, leave others as 0.0
    for (int y = 0; y < self->heightmap->h; y++) {
        for (int x = 0; x < self->heightmap->w; x++) {
            float value = TCOD_heightmap_get_value(self->heightmap, x, y);
            if (value >= min_val && value <= max_val) {
                TCOD_heightmap_set_value(result->heightmap, x, y, value);
            }
            // else: already 0.0 from initialization
        }
    }

    return (PyObject*)result;
}

// Method: threshold_binary(range, value=1.0) -> HeightMap
PyObject* PyHeightMap::threshold_binary(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"range", "value", nullptr};
    PyObject* range_obj = nullptr;
    float set_value = 1.0f;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|f", const_cast<char**>(keywords),
                                     &range_obj, &set_value)) {
        return nullptr;
    }

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    float min_val, max_val;
    if (!ParseRange(range_obj, &min_val, &max_val)) {
        return nullptr;
    }

    // Create new HeightMap with same dimensions
    PyHeightMapObject* result = CreateNewHeightMap(self->heightmap->w, self->heightmap->h);
    if (!result) {
        return nullptr;
    }

    // Set uniform value where in range, leave others as 0.0
    for (int y = 0; y < self->heightmap->h; y++) {
        for (int x = 0; x < self->heightmap->w; x++) {
            float value = TCOD_heightmap_get_value(self->heightmap, x, y);
            if (value >= min_val && value <= max_val) {
                TCOD_heightmap_set_value(result->heightmap, x, y, set_value);
            }
            // else: already 0.0 from initialization
        }
    }

    return (PyObject*)result;
}

// Method: inverse() -> HeightMap
PyObject* PyHeightMap::inverse(PyHeightMapObject* self, PyObject* Py_UNUSED(args))
{
    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    // Create new HeightMap with same dimensions
    PyHeightMapObject* result = CreateNewHeightMap(self->heightmap->w, self->heightmap->h);
    if (!result) {
        return nullptr;
    }

    // Set (1.0 - value) for each cell
    for (int y = 0; y < self->heightmap->h; y++) {
        for (int x = 0; x < self->heightmap->w; x++) {
            float value = TCOD_heightmap_get_value(self->heightmap, x, y);
            TCOD_heightmap_set_value(result->heightmap, x, y, 1.0f - value);
        }
    }

    return (PyObject*)result;
}

// Terrain generation methods (#195)

// Helper: Create TCOD random generator with optional seed
static TCOD_Random* CreateTCODRandom(PyObject* seed_obj)
{
    if (seed_obj == nullptr || seed_obj == Py_None) {
        // Use default random - return nullptr to use libtcod's default
        return nullptr;
    }

    if (!PyLong_Check(seed_obj)) {
        PyErr_SetString(PyExc_TypeError, "seed must be an integer or None");
        return nullptr;
    }

    uint32_t seed = (uint32_t)PyLong_AsUnsignedLong(seed_obj);
    if (PyErr_Occurred()) {
        return nullptr;
    }

    return TCOD_random_new_from_seed(TCOD_RNG_MT, seed);
}

// Method: add_hill(center, radius, height) -> HeightMap
PyObject* PyHeightMap::add_hill(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"center", "radius", "height", nullptr};
    PyObject* center_obj = nullptr;
    float radius, height;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "Off", const_cast<char**>(keywords),
                                     &center_obj, &radius, &height)) {
        return nullptr;
    }

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    float cx, cy;
    if (!PyPosition_FromObject(center_obj, &cx, &cy)) {
        return nullptr;
    }

    // Warn on zero/negative radius (no-op but likely user error)
    if (radius <= 0) {
        if (PyErr_WarnEx(PyExc_UserWarning,
            "add_hill called with radius <= 0; no cells will be modified", 1) < 0) {
            return nullptr;
        }
    }

    TCOD_heightmap_add_hill(self->heightmap, cx, cy, radius, height);

    Py_INCREF(self);
    return (PyObject*)self;
}

// Method: dig_hill(center, radius, target_height) -> HeightMap
PyObject* PyHeightMap::dig_hill(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"center", "radius", "target_height", nullptr};
    PyObject* center_obj = nullptr;
    float radius, target_height;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "Off", const_cast<char**>(keywords),
                                     &center_obj, &radius, &target_height)) {
        return nullptr;
    }

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    float cx, cy;
    if (!PyPosition_FromObject(center_obj, &cx, &cy)) {
        return nullptr;
    }

    // Warn on zero/negative radius (no-op but likely user error)
    if (radius <= 0) {
        if (PyErr_WarnEx(PyExc_UserWarning,
            "dig_hill called with radius <= 0; no cells will be modified", 1) < 0) {
            return nullptr;
        }
    }

    TCOD_heightmap_dig_hill(self->heightmap, cx, cy, radius, target_height);

    Py_INCREF(self);
    return (PyObject*)self;
}

// Method: add_voronoi(num_points, coefficients=(1.0, -0.5), seed=None) -> HeightMap
PyObject* PyHeightMap::add_voronoi(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"num_points", "coefficients", "seed", nullptr};
    int num_points;
    PyObject* coef_obj = nullptr;
    PyObject* seed_obj = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "i|OO", const_cast<char**>(keywords),
                                     &num_points, &coef_obj, &seed_obj)) {
        return nullptr;
    }

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    if (num_points <= 0) {
        PyErr_SetString(PyExc_ValueError, "num_points must be positive");
        return nullptr;
    }

    // Parse coefficients - default to (1.0, -0.5)
    std::vector<float> coef;
    if (coef_obj == nullptr || coef_obj == Py_None) {
        coef = {1.0f, -0.5f};
    } else if (PyTuple_Check(coef_obj)) {
        Py_ssize_t size = PyTuple_Size(coef_obj);
        for (Py_ssize_t i = 0; i < size; i++) {
            PyObject* item = PyTuple_GetItem(coef_obj, i);
            if (PyFloat_Check(item)) {
                coef.push_back((float)PyFloat_AsDouble(item));
            } else if (PyLong_Check(item)) {
                coef.push_back((float)PyLong_AsLong(item));
            } else {
                PyErr_SetString(PyExc_TypeError, "coefficients must be numeric");
                return nullptr;
            }
        }
    } else if (PyList_Check(coef_obj)) {
        Py_ssize_t size = PyList_Size(coef_obj);
        for (Py_ssize_t i = 0; i < size; i++) {
            PyObject* item = PyList_GetItem(coef_obj, i);
            if (PyFloat_Check(item)) {
                coef.push_back((float)PyFloat_AsDouble(item));
            } else if (PyLong_Check(item)) {
                coef.push_back((float)PyLong_AsLong(item));
            } else {
                PyErr_SetString(PyExc_TypeError, "coefficients must be numeric");
                return nullptr;
            }
        }
    } else {
        PyErr_SetString(PyExc_TypeError, "coefficients must be a tuple or list");
        return nullptr;
    }

    if (coef.empty()) {
        PyErr_SetString(PyExc_ValueError, "coefficients cannot be empty");
        return nullptr;
    }

    // Create random generator if seed provided
    TCOD_Random* rnd = CreateTCODRandom(seed_obj);
    if (PyErr_Occurred()) {
        return nullptr;
    }

    TCOD_heightmap_add_voronoi(self->heightmap, num_points, (int)coef.size(), coef.data(), rnd);

    if (rnd) {
        TCOD_random_delete(rnd);
    }

    Py_INCREF(self);
    return (PyObject*)self;
}

// Method: mid_point_displacement(roughness=0.5, seed=None) -> HeightMap
PyObject* PyHeightMap::mid_point_displacement(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"roughness", "seed", nullptr};
    float roughness = 0.5f;
    PyObject* seed_obj = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|fO", const_cast<char**>(keywords),
                                     &roughness, &seed_obj)) {
        return nullptr;
    }

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    // Create random generator if seed provided
    TCOD_Random* rnd = CreateTCODRandom(seed_obj);
    if (PyErr_Occurred()) {
        return nullptr;
    }

    TCOD_heightmap_mid_point_displacement(self->heightmap, rnd, roughness);

    if (rnd) {
        TCOD_random_delete(rnd);
    }

    Py_INCREF(self);
    return (PyObject*)self;
}

// Method: rain_erosion(drops, erosion=0.1, sedimentation=0.05, seed=None) -> HeightMap
PyObject* PyHeightMap::rain_erosion(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"drops", "erosion", "sedimentation", "seed", nullptr};
    int drops;
    float erosion = 0.1f;
    float sedimentation = 0.05f;
    PyObject* seed_obj = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "i|ffO", const_cast<char**>(keywords),
                                     &drops, &erosion, &sedimentation, &seed_obj)) {
        return nullptr;
    }

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    if (drops <= 0) {
        PyErr_SetString(PyExc_ValueError, "drops must be positive");
        return nullptr;
    }

    // Create random generator if seed provided
    TCOD_Random* rnd = CreateTCODRandom(seed_obj);
    if (PyErr_Occurred()) {
        return nullptr;
    }

    TCOD_heightmap_rain_erosion(self->heightmap, drops, erosion, sedimentation, rnd);

    if (rnd) {
        TCOD_random_delete(rnd);
    }

    Py_INCREF(self);
    return (PyObject*)self;
}

// Method: dig_bezier(points, start_radius, end_radius, start_height, end_height) -> HeightMap
PyObject* PyHeightMap::dig_bezier(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"points", "start_radius", "end_radius", "start_height", "end_height", nullptr};
    PyObject* points_obj = nullptr;
    float start_radius, end_radius, start_height, end_height;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "Offff", const_cast<char**>(keywords),
                                     &points_obj, &start_radius, &end_radius, &start_height, &end_height)) {
        return nullptr;
    }

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    // Parse 4 control points
    if (!PyTuple_Check(points_obj) && !PyList_Check(points_obj)) {
        PyErr_SetString(PyExc_TypeError, "points must be a tuple or list of 4 control points");
        return nullptr;
    }

    Py_ssize_t size = PyTuple_Check(points_obj) ? PyTuple_Size(points_obj) : PyList_Size(points_obj);
    if (size != 4) {
        PyErr_Format(PyExc_ValueError, "points must contain exactly 4 control points, got %zd", size);
        return nullptr;
    }

    int px[4], py[4];
    for (int i = 0; i < 4; i++) {
        PyObject* point = PyTuple_Check(points_obj) ? PyTuple_GetItem(points_obj, i) : PyList_GetItem(points_obj, i);
        int x, y;
        if (!PyPosition_FromObjectInt(point, &x, &y)) {
            PyErr_Format(PyExc_TypeError, "control point %d must be a (x, y) position", i);
            return nullptr;
        }
        px[i] = x;
        py[i] = y;
    }

    // Warn on zero/negative radii (no-op but likely user error)
    if (start_radius <= 0 || end_radius <= 0) {
        if (PyErr_WarnEx(PyExc_UserWarning,
            "dig_bezier called with radius <= 0; some or all cells may not be modified", 1) < 0) {
            return nullptr;
        }
    }

    TCOD_heightmap_dig_bezier(self->heightmap, px, py, start_radius, start_height, end_radius, end_height);

    Py_INCREF(self);
    return (PyObject*)self;
}

// Method: smooth(iterations=1) -> HeightMap
PyObject* PyHeightMap::smooth(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"iterations", nullptr};
    int iterations = 1;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|i", const_cast<char**>(keywords),
                                     &iterations)) {
        return nullptr;
    }

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    if (iterations <= 0) {
        PyErr_SetString(PyExc_ValueError, "iterations must be positive");
        return nullptr;
    }

    // 3x3 averaging kernel
    static const int kernel_size = 9;
    static const int dx[9] = {-1, 0, 1, -1, 0, 1, -1, 0, 1};
    static const int dy[9] = {-1, -1, -1, 0, 0, 0, 1, 1, 1};
    static const float weight[9] = {1.0f/9.0f, 1.0f/9.0f, 1.0f/9.0f,
                                     1.0f/9.0f, 1.0f/9.0f, 1.0f/9.0f,
                                     1.0f/9.0f, 1.0f/9.0f, 1.0f/9.0f};

    for (int i = 0; i < iterations; i++) {
        // Apply to all heights (minLevel=0, maxLevel=very high)
        TCOD_heightmap_kernel_transform(self->heightmap, kernel_size, dx, dy, weight, 0.0f, 1000000.0f);
    }

    Py_INCREF(self);
    return (PyObject*)self;
}
