#include "PyHeightMap.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"
#include "PyPositionHelper.h"  // Standardized position argument parsing
#include "PyNoiseSource.h"     // For direct noise sampling (#209)
#include "PyBSP.h"             // For direct BSP sampling (#209)
#include <sstream>
#include <cstdlib>  // For random seed handling
#include <ctime>    // For time-based seeds
#include <vector>   // For BSP node collection
#include <algorithm>  // For std::min
#include <cfloat>     // For FLT_MAX

// =============================================================================
// Region Parameter System - standardized handling of pos, source_pos, size
// =============================================================================

// Region parameters for HeightMap operations
struct HMRegion {
    // Validated region coordinates
    int dest_x, dest_y;       // Destination origin in self
    int src_x, src_y;         // Source origin (for binary ops, 0 for scalar)
    int width, height;        // Region dimensions

    // Full heightmap dimensions (for iteration)
    int dest_w, dest_h;
    int src_w, src_h;

    // Direct indexing helpers
    inline int dest_idx(int x, int y) const {
        return (dest_y + y) * dest_w + (dest_x + x);
    }
    inline int src_idx(int x, int y) const {
        return (src_y + y) * src_w + (src_x + x);
    }
};

// Parse optional position tuple, returning (0, 0) if None/not provided
static bool parseOptionalPos(PyObject* pos_obj, int* out_x, int* out_y, const char* param_name) {
    *out_x = 0;
    *out_y = 0;

    if (!pos_obj || pos_obj == Py_None) {
        return true;  // Default to (0, 0)
    }

    // Try to parse as tuple/list of 2 ints
    if (PyTuple_Check(pos_obj) && PyTuple_Size(pos_obj) == 2) {
        PyObject* x_obj = PyTuple_GetItem(pos_obj, 0);
        PyObject* y_obj = PyTuple_GetItem(pos_obj, 1);
        if (PyLong_Check(x_obj) && PyLong_Check(y_obj)) {
            *out_x = (int)PyLong_AsLong(x_obj);
            *out_y = (int)PyLong_AsLong(y_obj);
            return true;
        }
    } else if (PyList_Check(pos_obj) && PyList_Size(pos_obj) == 2) {
        PyObject* x_obj = PyList_GetItem(pos_obj, 0);
        PyObject* y_obj = PyList_GetItem(pos_obj, 1);
        if (PyLong_Check(x_obj) && PyLong_Check(y_obj)) {
            *out_x = (int)PyLong_AsLong(x_obj);
            *out_y = (int)PyLong_AsLong(y_obj);
            return true;
        }
    }

    // Try PyPositionHelper for Vector support
    if (PyPosition_FromObjectInt(pos_obj, out_x, out_y)) {
        return true;
    }

    // Clear any error from PyPosition_FromObjectInt and set our own
    PyErr_Clear();
    PyErr_Format(PyExc_TypeError, "%s must be a (x, y) tuple, list, or Vector", param_name);
    return false;
}

// Parse optional size tuple
static bool parseOptionalSize(PyObject* size_obj, int* out_w, int* out_h, const char* param_name) {
    *out_w = -1;  // -1 means "not specified"
    *out_h = -1;

    if (!size_obj || size_obj == Py_None) {
        return true;
    }

    if (PyTuple_Check(size_obj) && PyTuple_Size(size_obj) == 2) {
        PyObject* w_obj = PyTuple_GetItem(size_obj, 0);
        PyObject* h_obj = PyTuple_GetItem(size_obj, 1);
        if (PyLong_Check(w_obj) && PyLong_Check(h_obj)) {
            *out_w = (int)PyLong_AsLong(w_obj);
            *out_h = (int)PyLong_AsLong(h_obj);
            if (*out_w <= 0 || *out_h <= 0) {
                PyErr_Format(PyExc_ValueError, "%s dimensions must be positive", param_name);
                return false;
            }
            return true;
        }
    } else if (PyList_Check(size_obj) && PyList_Size(size_obj) == 2) {
        PyObject* w_obj = PyList_GetItem(size_obj, 0);
        PyObject* h_obj = PyList_GetItem(size_obj, 1);
        if (PyLong_Check(w_obj) && PyLong_Check(h_obj)) {
            *out_w = (int)PyLong_AsLong(w_obj);
            *out_h = (int)PyLong_AsLong(h_obj);
            if (*out_w <= 0 || *out_h <= 0) {
                PyErr_Format(PyExc_ValueError, "%s dimensions must be positive", param_name);
                return false;
            }
            return true;
        }
    }

    PyErr_Format(PyExc_TypeError, "%s must be a (width, height) tuple or list", param_name);
    return false;
}

// Parse region parameters for binary operations (two heightmaps)
// Returns true on success, sets Python error and returns false on failure
static bool parseHMRegion(
    TCOD_heightmap_t* dest,
    TCOD_heightmap_t* src,      // Can be nullptr for scalar operations
    PyObject* pos,              // (x, y) or None - destination position
    PyObject* source_pos,       // (x, y) or None - source position
    PyObject* size,             // (w, h) or None
    HMRegion& out
) {
    // Store full dimensions
    out.dest_w = dest->w;
    out.dest_h = dest->h;
    out.src_w = src ? src->w : dest->w;
    out.src_h = src ? src->h : dest->h;

    // Parse positions, default to (0, 0)
    if (!parseOptionalPos(pos, &out.dest_x, &out.dest_y, "pos")) {
        return false;
    }
    if (!parseOptionalPos(source_pos, &out.src_x, &out.src_y, "source_pos")) {
        return false;
    }

    // Validate positions are within bounds
    if (out.dest_x < 0 || out.dest_y < 0) {
        PyErr_SetString(PyExc_ValueError, "pos coordinates cannot be negative");
        return false;
    }
    if (out.dest_x >= out.dest_w || out.dest_y >= out.dest_h) {
        PyErr_Format(PyExc_ValueError,
            "pos (%d, %d) is out of bounds for destination of size (%d, %d)",
            out.dest_x, out.dest_y, out.dest_w, out.dest_h);
        return false;
    }
    if (src && (out.src_x < 0 || out.src_y < 0)) {
        PyErr_SetString(PyExc_ValueError, "source_pos coordinates cannot be negative");
        return false;
    }
    if (src && (out.src_x >= out.src_w || out.src_y >= out.src_h)) {
        PyErr_Format(PyExc_ValueError,
            "source_pos (%d, %d) is out of bounds for source of size (%d, %d)",
            out.src_x, out.src_y, out.src_w, out.src_h);
        return false;
    }

    // Calculate remaining space from each position
    int dest_remaining_w = out.dest_w - out.dest_x;
    int dest_remaining_h = out.dest_h - out.dest_y;
    int src_remaining_w = src ? (out.src_w - out.src_x) : dest_remaining_w;
    int src_remaining_h = src ? (out.src_h - out.src_y) : dest_remaining_h;

    // Parse or infer size
    int requested_w = -1, requested_h = -1;
    if (!parseOptionalSize(size, &requested_w, &requested_h, "size")) {
        return false;
    }

    if (requested_w > 0 && requested_h > 0) {
        // Explicit size - must fit in both
        if (requested_w > dest_remaining_w || requested_h > dest_remaining_h) {
            PyErr_Format(PyExc_ValueError,
                "size (%d, %d) exceeds available space in destination (%d, %d) from pos (%d, %d)",
                requested_w, requested_h, dest_remaining_w, dest_remaining_h,
                out.dest_x, out.dest_y);
            return false;
        }
        if (src && (requested_w > src_remaining_w || requested_h > src_remaining_h)) {
            PyErr_Format(PyExc_ValueError,
                "size (%d, %d) exceeds available space in source (%d, %d) from source_pos (%d, %d)",
                requested_w, requested_h, src_remaining_w, src_remaining_h,
                out.src_x, out.src_y);
            return false;
        }
        out.width = requested_w;
        out.height = requested_h;
    } else {
        // Infer size: smaller of remaining space in each
        out.width = std::min(dest_remaining_w, src_remaining_w);
        out.height = std::min(dest_remaining_h, src_remaining_h);
    }

    // Final validation: non-zero region
    if (out.width <= 0 || out.height <= 0) {
        PyErr_SetString(PyExc_ValueError, "computed region has zero size");
        return false;
    }

    return true;
}

// Parse region parameters for scalar operations (just destination region)
static bool parseHMRegionScalar(
    TCOD_heightmap_t* dest,
    PyObject* pos,
    PyObject* size,
    HMRegion& out
) {
    return parseHMRegion(dest, nullptr, pos, nullptr, size, out);
}

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
    .mp_ass_subscript = (objobjargproc)PyHeightMap::subscript_assign  // __setitem__
};

// Method definitions
PyMethodDef PyHeightMap::methods[] = {
    {"fill", (PyCFunction)PyHeightMap::fill, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, fill,
         MCRF_SIG("(value: float, *, pos=None, size=None)", "HeightMap"),
         MCRF_DESC("Set cells in region to the specified value."),
         MCRF_ARGS_START
         MCRF_ARG("value", "The value to set")
         MCRF_ARG("pos", "Region start (x, y) in destination (default: (0, 0))")
         MCRF_ARG("size", "Region (width, height) to fill (default: remaining space)")
         MCRF_RETURNS("HeightMap: self, for method chaining")
     )},
    {"clear", (PyCFunction)PyHeightMap::clear, METH_NOARGS,
     MCRF_METHOD(HeightMap, clear,
         MCRF_SIG("()", "HeightMap"),
         MCRF_DESC("Set all cells to 0.0. Equivalent to fill(0.0)."),
         MCRF_RETURNS("HeightMap: self, for method chaining")
     )},
    {"add_constant", (PyCFunction)PyHeightMap::add_constant, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, add_constant,
         MCRF_SIG("(value: float, *, pos=None, size=None)", "HeightMap"),
         MCRF_DESC("Add a constant value to cells in region."),
         MCRF_ARGS_START
         MCRF_ARG("value", "The value to add to each cell")
         MCRF_ARG("pos", "Region start (x, y) in destination (default: (0, 0))")
         MCRF_ARG("size", "Region (width, height) (default: remaining space)")
         MCRF_RETURNS("HeightMap: self, for method chaining")
     )},
    {"scale", (PyCFunction)PyHeightMap::scale, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, scale,
         MCRF_SIG("(factor: float, *, pos=None, size=None)", "HeightMap"),
         MCRF_DESC("Multiply cells in region by a factor."),
         MCRF_ARGS_START
         MCRF_ARG("factor", "The multiplier for each cell")
         MCRF_ARG("pos", "Region start (x, y) in destination (default: (0, 0))")
         MCRF_ARG("size", "Region (width, height) (default: remaining space)")
         MCRF_RETURNS("HeightMap: self, for method chaining")
     )},
    {"clamp", (PyCFunction)PyHeightMap::clamp, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, clamp,
         MCRF_SIG("(min: float = 0.0, max: float = 1.0, *, pos=None, size=None)", "HeightMap"),
         MCRF_DESC("Clamp values in region to the specified range."),
         MCRF_ARGS_START
         MCRF_ARG("min", "Minimum value (default 0.0)")
         MCRF_ARG("max", "Maximum value (default 1.0)")
         MCRF_ARG("pos", "Region start (x, y) in destination (default: (0, 0))")
         MCRF_ARG("size", "Region (width, height) (default: remaining space)")
         MCRF_RETURNS("HeightMap: self, for method chaining")
     )},
    {"normalize", (PyCFunction)PyHeightMap::normalize, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, normalize,
         MCRF_SIG("(min: float = 0.0, max: float = 1.0, *, pos=None, size=None)", "HeightMap"),
         MCRF_DESC("Linearly rescale values in region. Current min becomes new min, current max becomes new max."),
         MCRF_ARGS_START
         MCRF_ARG("min", "Target minimum value (default 0.0)")
         MCRF_ARG("max", "Target maximum value (default 1.0)")
         MCRF_ARG("pos", "Region start (x, y) in destination (default: (0, 0))")
         MCRF_ARG("size", "Region (width, height) (default: remaining space)")
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
    // Convolution methods (libtcod 2.2.2+)
    {"sparse_kernel", (PyCFunction)PyHeightMap::sparse_kernel, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, sparse_kernel,
         MCRF_SIG("(weights: dict[tuple[int, int], float])", "HeightMap"),
         MCRF_DESC("Apply sparse convolution kernel, returning a NEW HeightMap with results."),
         MCRF_ARGS_START
         MCRF_ARG("weights", "Dict mapping (dx, dy) offsets to weight values")
         MCRF_RETURNS("HeightMap: new heightmap with convolution result")
     )},
    {"sparse_kernel_from", (PyCFunction)PyHeightMap::sparse_kernel_from, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, sparse_kernel_from,
         MCRF_SIG("(source: HeightMap, weights: dict[tuple[int, int], float])", "None"),
         MCRF_DESC("Apply sparse convolution from source heightmap into self (for reusing destination buffers)."),
         MCRF_ARGS_START
         MCRF_ARG("source", "Source HeightMap to convolve from")
         MCRF_ARG("weights", "Dict mapping (dx, dy) offsets to weight values")
         MCRF_RETURNS("None")
     )},
    // NOTE: kernel3 and kernel3_from removed - TCOD_heightmap_convolve3x3 was removed from libtcod.
    // Use sparse_kernel/sparse_kernel_from with a 3x3 dict instead.

    // NOTE: gradients method waiting for jmccardle:feature/heightmap-gradients to be merged into libtcod:main
    // {"gradients", (PyCFunction)PyHeightMap::gradients, METH_VARARGS | METH_KEYWORDS,
    //  MCRF_METHOD(HeightMap, gradients,
    //      MCRF_SIG("(dx=True, dy=True)", "HeightMap | tuple[HeightMap, HeightMap] | None"),
    //      MCRF_DESC("Compute gradient (partial derivatives) of the heightmap."),
    //      MCRF_ARGS_START
    //      MCRF_ARG("dx", "HeightMap to write dx into, True to create new, False to skip")
    //      MCRF_ARG("dy", "HeightMap to write dy into, True to create new, False to skip")
    //      MCRF_RETURNS("Depends on args: (dx, dy) tuple, single HeightMap, or None")
    //      MCRF_NOTE("Pass existing HeightMaps for dx/dy to reuse buffers in hot loops")
    //  )},
    // Combination operations (#194) - with region support
    {"add", (PyCFunction)PyHeightMap::add, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, add,
         MCRF_SIG("(other: HeightMap, *, pos=None, source_pos=None, size=None)", "HeightMap"),
         MCRF_DESC("Add another heightmap's values to this one in the specified region."),
         MCRF_ARGS_START
         MCRF_ARG("other", "HeightMap to add values from")
         MCRF_ARG("pos", "Destination start (x, y) in self (default: (0, 0))")
         MCRF_ARG("source_pos", "Source start (x, y) in other (default: (0, 0))")
         MCRF_ARG("size", "Region (width, height) (default: max overlapping area)")
         MCRF_RETURNS("HeightMap: self, for method chaining")
     )},
    {"subtract", (PyCFunction)PyHeightMap::subtract, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, subtract,
         MCRF_SIG("(other: HeightMap, *, pos=None, source_pos=None, size=None)", "HeightMap"),
         MCRF_DESC("Subtract another heightmap's values from this one in the specified region."),
         MCRF_ARGS_START
         MCRF_ARG("other", "HeightMap to subtract values from")
         MCRF_ARG("pos", "Destination start (x, y) in self (default: (0, 0))")
         MCRF_ARG("source_pos", "Source start (x, y) in other (default: (0, 0))")
         MCRF_ARG("size", "Region (width, height) (default: max overlapping area)")
         MCRF_RETURNS("HeightMap: self, for method chaining")
     )},
    {"multiply", (PyCFunction)PyHeightMap::multiply, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, multiply,
         MCRF_SIG("(other: HeightMap, *, pos=None, source_pos=None, size=None)", "HeightMap"),
         MCRF_DESC("Multiply this heightmap by another in the specified region (useful for masking)."),
         MCRF_ARGS_START
         MCRF_ARG("other", "HeightMap to multiply by")
         MCRF_ARG("pos", "Destination start (x, y) in self (default: (0, 0))")
         MCRF_ARG("source_pos", "Source start (x, y) in other (default: (0, 0))")
         MCRF_ARG("size", "Region (width, height) (default: max overlapping area)")
         MCRF_RETURNS("HeightMap: self, for method chaining")
     )},
    {"lerp", (PyCFunction)PyHeightMap::lerp, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, lerp,
         MCRF_SIG("(other: HeightMap, t: float, *, pos=None, source_pos=None, size=None)", "HeightMap"),
         MCRF_DESC("Linear interpolation between this and another heightmap in the specified region."),
         MCRF_ARGS_START
         MCRF_ARG("other", "HeightMap to interpolate towards")
         MCRF_ARG("t", "Interpolation factor (0.0 = this, 1.0 = other)")
         MCRF_ARG("pos", "Destination start (x, y) in self (default: (0, 0))")
         MCRF_ARG("source_pos", "Source start (x, y) in other (default: (0, 0))")
         MCRF_ARG("size", "Region (width, height) (default: max overlapping area)")
         MCRF_RETURNS("HeightMap: self, for method chaining")
     )},
    {"copy_from", (PyCFunction)PyHeightMap::copy_from, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, copy_from,
         MCRF_SIG("(other: HeightMap, *, pos=None, source_pos=None, size=None)", "HeightMap"),
         MCRF_DESC("Copy values from another heightmap into the specified region."),
         MCRF_ARGS_START
         MCRF_ARG("other", "HeightMap to copy from")
         MCRF_ARG("pos", "Destination start (x, y) in self (default: (0, 0))")
         MCRF_ARG("source_pos", "Source start (x, y) in other (default: (0, 0))")
         MCRF_ARG("size", "Region (width, height) (default: max overlapping area)")
         MCRF_RETURNS("HeightMap: self, for method chaining")
     )},
    {"max", (PyCFunction)PyHeightMap::hmap_max, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, max,
         MCRF_SIG("(other: HeightMap, *, pos=None, source_pos=None, size=None)", "HeightMap"),
         MCRF_DESC("Set each cell in region to the maximum of this and another heightmap."),
         MCRF_ARGS_START
         MCRF_ARG("other", "HeightMap to compare with")
         MCRF_ARG("pos", "Destination start (x, y) in self (default: (0, 0))")
         MCRF_ARG("source_pos", "Source start (x, y) in other (default: (0, 0))")
         MCRF_ARG("size", "Region (width, height) (default: max overlapping area)")
         MCRF_RETURNS("HeightMap: self, for method chaining")
     )},
    {"min", (PyCFunction)PyHeightMap::hmap_min, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, min,
         MCRF_SIG("(other: HeightMap, *, pos=None, source_pos=None, size=None)", "HeightMap"),
         MCRF_DESC("Set each cell in region to the minimum of this and another heightmap."),
         MCRF_ARGS_START
         MCRF_ARG("other", "HeightMap to compare with")
         MCRF_ARG("pos", "Destination start (x, y) in self (default: (0, 0))")
         MCRF_ARG("source_pos", "Source start (x, y) in other (default: (0, 0))")
         MCRF_ARG("size", "Region (width, height) (default: max overlapping area)")
         MCRF_RETURNS("HeightMap: self, for method chaining")
     )},
    // Direct source sampling (#209)
    {"add_noise", (PyCFunction)PyHeightMap::add_noise, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, add_noise,
         MCRF_SIG("(source: NoiseSource, world_origin: tuple = (0.0, 0.0), world_size: tuple = None, "
                  "mode: str = 'fbm', octaves: int = 4, scale: float = 1.0)", "HeightMap"),
         MCRF_DESC("Sample noise and add to current values. More efficient than creating intermediate HeightMap."),
         MCRF_ARGS_START
         MCRF_ARG("source", "2D NoiseSource to sample from")
         MCRF_ARG("world_origin", "World coordinates of top-left (default: (0, 0))")
         MCRF_ARG("world_size", "World area to sample (default: HeightMap size)")
         MCRF_ARG("mode", "'flat', 'fbm', or 'turbulence' (default: 'fbm')")
         MCRF_ARG("octaves", "Octaves for fbm/turbulence (default: 4)")
         MCRF_ARG("scale", "Multiplier for sampled values (default: 1.0)")
         MCRF_RETURNS("HeightMap: self, for method chaining")
     )},
    {"multiply_noise", (PyCFunction)PyHeightMap::multiply_noise, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, multiply_noise,
         MCRF_SIG("(source: NoiseSource, world_origin: tuple = (0.0, 0.0), world_size: tuple = None, "
                  "mode: str = 'fbm', octaves: int = 4, scale: float = 1.0)", "HeightMap"),
         MCRF_DESC("Sample noise and multiply with current values. Useful for applying noise-based masks."),
         MCRF_ARGS_START
         MCRF_ARG("source", "2D NoiseSource to sample from")
         MCRF_ARG("world_origin", "World coordinates of top-left (default: (0, 0))")
         MCRF_ARG("world_size", "World area to sample (default: HeightMap size)")
         MCRF_ARG("mode", "'flat', 'fbm', or 'turbulence' (default: 'fbm')")
         MCRF_ARG("octaves", "Octaves for fbm/turbulence (default: 4)")
         MCRF_ARG("scale", "Multiplier for sampled values (default: 1.0)")
         MCRF_RETURNS("HeightMap: self, for method chaining")
     )},
    {"add_bsp", (PyCFunction)PyHeightMap::add_bsp, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, add_bsp,
         MCRF_SIG("(bsp: BSP, *, pos=None, select: str = 'leaves', nodes: list = None, "
                  "shrink: int = 0, value: float = 1.0)", "HeightMap"),
         MCRF_DESC("Add BSP node regions to heightmap. More efficient than creating intermediate HeightMap."),
         MCRF_ARGS_START
         MCRF_ARG("bsp", "BSP tree to sample from")
         MCRF_ARG("pos", "Where BSP origin maps to in HeightMap (default: origin-relative like to_heightmap)")
         MCRF_ARG("select", "'leaves', 'all', or 'internal' (default: 'leaves')")
         MCRF_ARG("nodes", "Override: specific BSPNodes only (default: None)")
         MCRF_ARG("shrink", "Pixels to shrink from node bounds (default: 0)")
         MCRF_ARG("value", "Value to add inside regions (default: 1.0)")
         MCRF_RETURNS("HeightMap: self, for method chaining")
     )},
    {"multiply_bsp", (PyCFunction)PyHeightMap::multiply_bsp, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(HeightMap, multiply_bsp,
         MCRF_SIG("(bsp: BSP, *, pos=None, select: str = 'leaves', nodes: list = None, "
                  "shrink: int = 0, value: float = 1.0)", "HeightMap"),
         MCRF_DESC("Multiply by BSP regions. Effectively masks the heightmap to node interiors."),
         MCRF_ARGS_START
         MCRF_ARG("bsp", "BSP tree to sample from")
         MCRF_ARG("pos", "Where BSP origin maps to in HeightMap (default: origin-relative like to_heightmap)")
         MCRF_ARG("select", "'leaves', 'all', or 'internal' (default: 'leaves')")
         MCRF_ARG("nodes", "Override: specific BSPNodes only (default: None)")
         MCRF_ARG("shrink", "Pixels to shrink from node bounds (default: 0)")
         MCRF_ARG("value", "Value to multiply inside regions (default: 1.0)")
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

// Method: fill(value, *, pos=None, size=None) -> HeightMap
PyObject* PyHeightMap::fill(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"value", "pos", "size", nullptr};
    float value;
    PyObject* pos = nullptr;
    PyObject* size = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "f|OO", const_cast<char**>(kwlist),
                                     &value, &pos, &size)) {
        return nullptr;
    }

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    // Parse region parameters
    HMRegion region;
    if (!parseHMRegionScalar(self->heightmap, pos, size, region)) {
        return nullptr;
    }

    // Fill the region
    for (int y = 0; y < region.height; y++) {
        for (int x = 0; x < region.width; x++) {
            self->heightmap->values[region.dest_idx(x, y)] = value;
        }
    }

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

// Method: add_constant(value, *, pos=None, size=None) -> HeightMap
PyObject* PyHeightMap::add_constant(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"value", "pos", "size", nullptr};
    float value;
    PyObject* pos = nullptr;
    PyObject* size = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "f|OO", const_cast<char**>(kwlist),
                                     &value, &pos, &size)) {
        return nullptr;
    }

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    // Parse region parameters
    HMRegion region;
    if (!parseHMRegionScalar(self->heightmap, pos, size, region)) {
        return nullptr;
    }

    // Add constant to region
    for (int y = 0; y < region.height; y++) {
        for (int x = 0; x < region.width; x++) {
            self->heightmap->values[region.dest_idx(x, y)] += value;
        }
    }

    Py_INCREF(self);
    return (PyObject*)self;
}

// Method: scale(factor, *, pos=None, size=None) -> HeightMap
PyObject* PyHeightMap::scale(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"factor", "pos", "size", nullptr};
    float factor;
    PyObject* pos = nullptr;
    PyObject* size = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "f|OO", const_cast<char**>(kwlist),
                                     &factor, &pos, &size)) {
        return nullptr;
    }

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    // Parse region parameters
    HMRegion region;
    if (!parseHMRegionScalar(self->heightmap, pos, size, region)) {
        return nullptr;
    }

    // Scale region
    for (int y = 0; y < region.height; y++) {
        for (int x = 0; x < region.width; x++) {
            self->heightmap->values[region.dest_idx(x, y)] *= factor;
        }
    }

    Py_INCREF(self);
    return (PyObject*)self;
}

// Method: clamp(min=0.0, max=1.0, *, pos=None, size=None) -> HeightMap
PyObject* PyHeightMap::clamp(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"min", "max", "pos", "size", nullptr};
    float min_val = 0.0f;
    float max_val = 1.0f;
    PyObject* pos = nullptr;
    PyObject* size = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|ffOO", const_cast<char**>(kwlist),
                                     &min_val, &max_val, &pos, &size)) {
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

    // Parse region parameters
    HMRegion region;
    if (!parseHMRegionScalar(self->heightmap, pos, size, region)) {
        return nullptr;
    }

    // Clamp values in region
    for (int y = 0; y < region.height; y++) {
        for (int x = 0; x < region.width; x++) {
            float& val = self->heightmap->values[region.dest_idx(x, y)];
            if (val < min_val) val = min_val;
            else if (val > max_val) val = max_val;
        }
    }

    Py_INCREF(self);
    return (PyObject*)self;
}

// Method: normalize(min=0.0, max=1.0, *, pos=None, size=None) -> HeightMap
PyObject* PyHeightMap::normalize(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"min", "max", "pos", "size", nullptr};
    float target_min = 0.0f;
    float target_max = 1.0f;
    PyObject* pos = nullptr;
    PyObject* size = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|ffOO", const_cast<char**>(kwlist),
                                     &target_min, &target_max, &pos, &size)) {
        return nullptr;
    }

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    if (target_min > target_max) {
        PyErr_SetString(PyExc_ValueError, "min must be less than or equal to max");
        return nullptr;
    }

    // Parse region parameters
    HMRegion region;
    if (!parseHMRegionScalar(self->heightmap, pos, size, region)) {
        return nullptr;
    }

    // Find min/max in region
    float current_min = self->heightmap->values[region.dest_idx(0, 0)];
    float current_max = current_min;
    for (int y = 0; y < region.height; y++) {
        for (int x = 0; x < region.width; x++) {
            float val = self->heightmap->values[region.dest_idx(x, y)];
            if (val < current_min) current_min = val;
            if (val > current_max) current_max = val;
        }
    }

    // Normalize values in region
    float range = current_max - current_min;
    if (range > 0.0f) {
        float scale = (target_max - target_min) / range;
        for (int y = 0; y < region.height; y++) {
            for (int x = 0; x < region.width; x++) {
                float& val = self->heightmap->values[region.dest_idx(x, y)];
                val = target_min + (val - current_min) * scale;
            }
        }
    } else {
        // All values are the same - set to midpoint
        float mid = (target_min + target_max) / 2.0f;
        for (int y = 0; y < region.height; y++) {
            for (int x = 0; x < region.width; x++) {
                self->heightmap->values[region.dest_idx(x, y)] = mid;
            }
        }
    }

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

// Subscript assign: hmap[x, y] = value (shorthand for set)
int PyHeightMap::subscript_assign(PyHeightMapObject* self, PyObject* key, PyObject* value)
{
    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return -1;
    }

    // Handle deletion (not supported)
    if (value == nullptr) {
        PyErr_SetString(PyExc_TypeError, "cannot delete HeightMap elements");
        return -1;
    }

    int x, y;
    if (!PyPosition_FromObjectInt(key, &x, &y)) {
        return -1;
    }

    // Bounds check
    if (x < 0 || x >= self->heightmap->w || y < 0 || y >= self->heightmap->h) {
        PyErr_Format(PyExc_IndexError,
            "Position (%d, %d) out of bounds for HeightMap of size (%d, %d)",
            x, y, self->heightmap->w, self->heightmap->h);
        return -1;
    }

    // Parse value as float
    float fval;
    if (PyFloat_Check(value)) {
        fval = static_cast<float>(PyFloat_AsDouble(value));
    } else if (PyLong_Check(value)) {
        fval = static_cast<float>(PyLong_AsLong(value));
    } else {
        PyErr_SetString(PyExc_TypeError, "value must be numeric (int or float)");
        return -1;
    }

    TCOD_heightmap_set_value(self->heightmap, x, y, fval);
    return 0;  // Success
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

// Forward declaration for helper used by convolution methods
static PyHeightMapObject* validateOtherHeightMapType(PyObject* other_obj, const char* method_name);

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

// =============================================================================
// Convolution methods (libtcod 2.2.2+)
// =============================================================================

// Helper: Parse weights dict into arrays for sparse kernel
// Returns kernel_size on success, -1 on error
static Py_ssize_t ParseWeightsDict(PyObject* weights_dict,
                                    std::vector<int>& dx,
                                    std::vector<int>& dy,
                                    std::vector<float>& weight)
{
    if (!PyDict_Check(weights_dict)) {
        PyErr_SetString(PyExc_TypeError, "weights must be a dict");
        return -1;
    }

    Py_ssize_t kernel_size = PyDict_Size(weights_dict);
    if (kernel_size <= 0) {
        PyErr_SetString(PyExc_ValueError, "weights dict cannot be empty");
        return -1;
    }

    dx.resize(kernel_size);
    dy.resize(kernel_size);
    weight.resize(kernel_size);

    PyObject* key;
    PyObject* value;
    Py_ssize_t pos = 0;
    Py_ssize_t idx = 0;

    while (PyDict_Next(weights_dict, &pos, &key, &value)) {
        int key_dx = 0, key_dy = 0;

        if (PyTuple_Check(key) && PyTuple_Size(key) == 2) {
            PyObject* x_obj = PyTuple_GetItem(key, 0);
            PyObject* y_obj = PyTuple_GetItem(key, 1);
            if (!PyLong_Check(x_obj) || !PyLong_Check(y_obj)) {
                PyErr_SetString(PyExc_TypeError, "weights keys must be (int, int) tuples");
                return -1;
            }
            key_dx = PyLong_AsLong(x_obj);
            key_dy = PyLong_AsLong(y_obj);
        } else if (PyList_Check(key) && PyList_Size(key) == 2) {
            PyObject* x_obj = PyList_GetItem(key, 0);
            PyObject* y_obj = PyList_GetItem(key, 1);
            if (!PyLong_Check(x_obj) || !PyLong_Check(y_obj)) {
                PyErr_SetString(PyExc_TypeError, "weights keys must be [int, int] lists");
                return -1;
            }
            key_dx = PyLong_AsLong(x_obj);
            key_dy = PyLong_AsLong(y_obj);
        } else if (PyObject_HasAttrString(key, "x") && PyObject_HasAttrString(key, "y")) {
            PyObject* x_attr = PyObject_GetAttrString(key, "x");
            PyObject* y_attr = PyObject_GetAttrString(key, "y");
            if (!x_attr || !y_attr) {
                Py_XDECREF(x_attr);
                Py_XDECREF(y_attr);
                PyErr_SetString(PyExc_TypeError, "weights keys must be (dx, dy) tuples, lists, or Vectors");
                return -1;
            }
            key_dx = static_cast<int>(PyFloat_Check(x_attr) ? PyFloat_AsDouble(x_attr) : PyLong_AsLong(x_attr));
            key_dy = static_cast<int>(PyFloat_Check(y_attr) ? PyFloat_AsDouble(y_attr) : PyLong_AsLong(y_attr));
            Py_DECREF(x_attr);
            Py_DECREF(y_attr);
        } else {
            PyErr_SetString(PyExc_TypeError, "weights keys must be (dx, dy) tuples, lists, or Vectors");
            return -1;
        }

        float w = 0.0f;
        if (PyFloat_Check(value)) {
            w = static_cast<float>(PyFloat_AsDouble(value));
        } else if (PyLong_Check(value)) {
            w = static_cast<float>(PyLong_AsLong(value));
        } else {
            PyErr_SetString(PyExc_TypeError, "weights values must be numeric (int or float)");
            return -1;
        }

        dx[idx] = key_dx;
        dy[idx] = key_dy;
        weight[idx] = w;
        idx++;
    }

    return kernel_size;
}

// sparse_kernel_from - apply sparse convolution from source into self
PyObject* PyHeightMap::sparse_kernel_from(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
{
    PyObject* source_obj = nullptr;
    PyObject* weights_dict = nullptr;

    static const char* kwlist[] = {"source", "weights", nullptr};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO", const_cast<char**>(kwlist),
                                     &source_obj, &weights_dict)) {
        return nullptr;
    }

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    // Validate source
    PyHeightMapObject* source = validateOtherHeightMapType(source_obj, "sparse_kernel_from");
    if (!source) return nullptr;

    // Check dimensions match
    if (source->heightmap->w != self->heightmap->w ||
        source->heightmap->h != self->heightmap->h) {
        PyErr_SetString(PyExc_ValueError, "source and destination HeightMaps must have same dimensions");
        return nullptr;
    }

    // Parse weights
    std::vector<int> dx, dy;
    std::vector<float> weight;
    Py_ssize_t kernel_size = ParseWeightsDict(weights_dict, dx, dy, weight);
    if (kernel_size < 0) return nullptr;

    // Apply the kernel transform
    // NOTE: mask parameter added in libtcod feature/heightmap-convolution, pass nullptr for now
    TCOD_heightmap_kernel_transform_out(source->heightmap, self->heightmap,
                                        static_cast<int>(kernel_size),
                                        dx.data(), dy.data(), weight.data(),
                                        nullptr);

    Py_RETURN_NONE;
}

// sparse_kernel - apply sparse convolution, return new HeightMap
PyObject* PyHeightMap::sparse_kernel(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
{
    PyObject* weights_dict = nullptr;

    static const char* kwlist[] = {"weights", nullptr};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O", const_cast<char**>(kwlist),
                                     &weights_dict)) {
        return nullptr;
    }

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    // Create new HeightMap for result
    PyHeightMapObject* result = CreateNewHeightMap(self->heightmap->w, self->heightmap->h);
    if (!result) return nullptr;

    // Parse weights
    std::vector<int> dx, dy;
    std::vector<float> weight;
    Py_ssize_t kernel_size = ParseWeightsDict(weights_dict, dx, dy, weight);
    if (kernel_size < 0) {
        Py_DECREF(result);
        return nullptr;
    }

    // Apply the kernel transform
    // NOTE: mask parameter added in libtcod feature/heightmap-convolution, pass nullptr for now
    TCOD_heightmap_kernel_transform_out(self->heightmap, result->heightmap,
                                        static_cast<int>(kernel_size),
                                        dx.data(), dy.data(), weight.data(),
                                        nullptr);

    return (PyObject*)result;
}

// NOTE: gradients method waiting for jmccardle:feature/heightmap-gradients to be merged into libtcod:main
/*
// gradients - compute partial derivatives
// Usage:
//   source.gradients(dx_hm, dy_hm) - write to existing HeightMaps, return None
//   dx, dy = source.gradients()   - create new HeightMaps, return tuple
//   dx = source.gradients(dy=False) - skip dy, return single HeightMap
PyObject* PyHeightMap::gradients(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
{
    PyObject* dx_arg = Py_True;
    PyObject* dy_arg = Py_True;

    static const char* kwlist[] = {"dx", "dy", nullptr};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OO", const_cast<char**>(kwlist),
                                     &dx_arg, &dy_arg)) {
        return nullptr;
    }

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    int w = self->heightmap->w;
    int h = self->heightmap->h;

    // Determine what to do with dx
    PyHeightMapObject* dx_hm = nullptr;
    bool dx_return_new = false;
    bool dx_skip = false;

    if (dx_arg == Py_True) {
        // Create new HeightMap for dx
        dx_hm = CreateNewHeightMap(w, h);
        if (!dx_hm) return nullptr;
        dx_return_new = true;
    } else if (dx_arg == Py_False || dx_arg == Py_None) {
        // Skip dx
        dx_skip = true;
    } else {
        // Should be a HeightMap to write into
        dx_hm = validateOtherHeightMapType(dx_arg, "gradients");
        if (!dx_hm) return nullptr;
        if (dx_hm->heightmap->w != w || dx_hm->heightmap->h != h) {
            PyErr_SetString(PyExc_ValueError, "dx HeightMap must have same dimensions as source");
            return nullptr;
        }
    }

    // Determine what to do with dy
    PyHeightMapObject* dy_hm = nullptr;
    bool dy_return_new = false;
    bool dy_skip = false;

    if (dy_arg == Py_True) {
        // Create new HeightMap for dy
        dy_hm = CreateNewHeightMap(w, h);
        if (!dy_hm) {
            if (dx_return_new) Py_DECREF(dx_hm);
            return nullptr;
        }
        dy_return_new = true;
    } else if (dy_arg == Py_False || dy_arg == Py_None) {
        // Skip dy
        dy_skip = true;
    } else {
        // Should be a HeightMap to write into
        dy_hm = validateOtherHeightMapType(dy_arg, "gradients");
        if (!dy_hm) {
            if (dx_return_new) Py_DECREF(dx_hm);
            return nullptr;
        }
        if (dy_hm->heightmap->w != w || dy_hm->heightmap->h != h) {
            if (dx_return_new) Py_DECREF(dx_hm);
            PyErr_SetString(PyExc_ValueError, "dy HeightMap must have same dimensions as source");
            return nullptr;
        }
    }

    // Call the gradient function
    TCOD_heightmap_gradient(self->heightmap,
                            dx_skip ? nullptr : dx_hm->heightmap,
                            dy_skip ? nullptr : dy_hm->heightmap);

    // Build return value
    if (dx_return_new && dy_return_new) {
        // Return tuple of (dx, dy)
        return Py_BuildValue("(OO)", dx_hm, dy_hm);
    } else if (dx_return_new) {
        // Return just dx
        return (PyObject*)dx_hm;
    } else if (dy_return_new) {
        // Return just dy
        return (PyObject*)dy_hm;
    } else {
        // Nothing to return
        Py_RETURN_NONE;
    }
}
*/

// =============================================================================
// Combination operations (#194) - with region support
// =============================================================================

// Helper: Validate other HeightMap (type check only, no dimension check)
static PyHeightMapObject* validateOtherHeightMapType(PyObject* other_obj, const char* method_name)
{
    // Check that other is a HeightMap
    PyObject* heightmap_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "HeightMap");
    if (!heightmap_type) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap type not found in module");
        return nullptr;
    }

    int is_hmap = PyObject_IsInstance(other_obj, heightmap_type);
    Py_DECREF(heightmap_type);

    if (is_hmap < 0) {
        return nullptr;  // Error in isinstance check
    }
    if (!is_hmap) {
        PyErr_Format(PyExc_TypeError, "%s() requires a HeightMap argument", method_name);
        return nullptr;
    }

    PyHeightMapObject* other = (PyHeightMapObject*)other_obj;

    if (!other->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "Other HeightMap not initialized");
        return nullptr;
    }

    return other;
}

// Method: add(other, *, pos=None, source_pos=None, size=None) -> HeightMap
PyObject* PyHeightMap::add(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
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

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    PyHeightMapObject* other = validateOtherHeightMapType(other_obj, "add");
    if (!other) return nullptr;

    // Parse region parameters
    HMRegion region;
    if (!parseHMRegion(self->heightmap, other->heightmap, pos, source_pos, size, region)) {
        return nullptr;
    }

    // Add values in region
    for (int y = 0; y < region.height; y++) {
        for (int x = 0; x < region.width; x++) {
            self->heightmap->values[region.dest_idx(x, y)] +=
                other->heightmap->values[region.src_idx(x, y)];
        }
    }

    Py_INCREF(self);
    return (PyObject*)self;
}

// Method: subtract(other, *, pos=None, source_pos=None, size=None) -> HeightMap
PyObject* PyHeightMap::subtract(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
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

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    PyHeightMapObject* other = validateOtherHeightMapType(other_obj, "subtract");
    if (!other) return nullptr;

    // Parse region parameters
    HMRegion region;
    if (!parseHMRegion(self->heightmap, other->heightmap, pos, source_pos, size, region)) {
        return nullptr;
    }

    // Subtract values in region
    for (int y = 0; y < region.height; y++) {
        for (int x = 0; x < region.width; x++) {
            self->heightmap->values[region.dest_idx(x, y)] -=
                other->heightmap->values[region.src_idx(x, y)];
        }
    }

    Py_INCREF(self);
    return (PyObject*)self;
}

// Method: multiply(other, *, pos=None, source_pos=None, size=None) -> HeightMap
PyObject* PyHeightMap::multiply(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
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

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    PyHeightMapObject* other = validateOtherHeightMapType(other_obj, "multiply");
    if (!other) return nullptr;

    // Parse region parameters
    HMRegion region;
    if (!parseHMRegion(self->heightmap, other->heightmap, pos, source_pos, size, region)) {
        return nullptr;
    }

    // Multiply values in region
    for (int y = 0; y < region.height; y++) {
        for (int x = 0; x < region.width; x++) {
            self->heightmap->values[region.dest_idx(x, y)] *=
                other->heightmap->values[region.src_idx(x, y)];
        }
    }

    Py_INCREF(self);
    return (PyObject*)self;
}

// Method: lerp(other, t, *, pos=None, source_pos=None, size=None) -> HeightMap
PyObject* PyHeightMap::lerp(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"other", "t", "pos", "source_pos", "size", nullptr};
    PyObject* other_obj;
    float t;
    PyObject* pos = nullptr;
    PyObject* source_pos = nullptr;
    PyObject* size = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "Of|OOO", const_cast<char**>(kwlist),
                                     &other_obj, &t, &pos, &source_pos, &size)) {
        return nullptr;
    }

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    PyHeightMapObject* other = validateOtherHeightMapType(other_obj, "lerp");
    if (!other) return nullptr;

    // Parse region parameters
    HMRegion region;
    if (!parseHMRegion(self->heightmap, other->heightmap, pos, source_pos, size, region)) {
        return nullptr;
    }

    // Lerp values in region: self = self * (1-t) + other * t
    float one_minus_t = 1.0f - t;
    for (int y = 0; y < region.height; y++) {
        for (int x = 0; x < region.width; x++) {
            float& dest = self->heightmap->values[region.dest_idx(x, y)];
            float src = other->heightmap->values[region.src_idx(x, y)];
            dest = dest * one_minus_t + src * t;
        }
    }

    Py_INCREF(self);
    return (PyObject*)self;
}

// Method: copy_from(other, *, pos=None, source_pos=None, size=None) -> HeightMap
PyObject* PyHeightMap::copy_from(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
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

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    PyHeightMapObject* other = validateOtherHeightMapType(other_obj, "copy_from");
    if (!other) return nullptr;

    // Parse region parameters
    HMRegion region;
    if (!parseHMRegion(self->heightmap, other->heightmap, pos, source_pos, size, region)) {
        return nullptr;
    }

    // Copy values in region
    for (int y = 0; y < region.height; y++) {
        for (int x = 0; x < region.width; x++) {
            self->heightmap->values[region.dest_idx(x, y)] =
                other->heightmap->values[region.src_idx(x, y)];
        }
    }

    Py_INCREF(self);
    return (PyObject*)self;
}

// Method: max(other, *, pos=None, source_pos=None, size=None) -> HeightMap
PyObject* PyHeightMap::hmap_max(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
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

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    PyHeightMapObject* other = validateOtherHeightMapType(other_obj, "max");
    if (!other) return nullptr;

    // Parse region parameters
    HMRegion region;
    if (!parseHMRegion(self->heightmap, other->heightmap, pos, source_pos, size, region)) {
        return nullptr;
    }

    // Max values in region
    for (int y = 0; y < region.height; y++) {
        for (int x = 0; x < region.width; x++) {
            float& dest = self->heightmap->values[region.dest_idx(x, y)];
            float src = other->heightmap->values[region.src_idx(x, y)];
            if (src > dest) dest = src;
        }
    }

    Py_INCREF(self);
    return (PyObject*)self;
}

// Method: min(other, *, pos=None, source_pos=None, size=None) -> HeightMap
PyObject* PyHeightMap::hmap_min(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
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

    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    PyHeightMapObject* other = validateOtherHeightMapType(other_obj, "min");
    if (!other) return nullptr;

    // Parse region parameters
    HMRegion region;
    if (!parseHMRegion(self->heightmap, other->heightmap, pos, source_pos, size, region)) {
        return nullptr;
    }

    // Min values in region
    for (int y = 0; y < region.height; y++) {
        for (int x = 0; x < region.width; x++) {
            float& dest = self->heightmap->values[region.dest_idx(x, y)];
            float src = other->heightmap->values[region.src_idx(x, y)];
            if (src < dest) dest = src;
        }
    }

    Py_INCREF(self);
    return (PyObject*)self;
}

// =============================================================================
// Direct source sampling (#209)
// =============================================================================

// Enum for noise sampling mode
enum class NoiseSampleMode { FLAT, FBM, TURBULENCE };

// Helper: Parse noise sampling parameters
static bool parseNoiseSampleParams(
    PyObject* args, PyObject* kwds,
    PyNoiseSourceObject** out_source,
    float* out_origin_x, float* out_origin_y,
    float* out_world_w, float* out_world_h,
    NoiseSampleMode* out_mode,
    int* out_octaves,
    float* out_scale,
    int hmap_w, int hmap_h,
    const char* method_name)
{
    static const char* keywords[] = {"source", "world_origin", "world_size", "mode", "octaves", "scale", nullptr};
    PyObject* source_obj = nullptr;
    PyObject* origin_obj = nullptr;
    PyObject* world_size_obj = nullptr;
    const char* mode_str = "fbm";
    int octaves = 4;
    float scale = 1.0f;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OOsif", const_cast<char**>(keywords),
                                     &source_obj, &origin_obj, &world_size_obj, &mode_str, &octaves, &scale)) {
        return false;
    }

    // Validate source is a NoiseSource
    PyObject* noise_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "NoiseSource");
    if (!noise_type) {
        PyErr_SetString(PyExc_RuntimeError, "NoiseSource type not found in module");
        return false;
    }
    int is_noise = PyObject_IsInstance(source_obj, noise_type);
    Py_DECREF(noise_type);

    if (is_noise < 0) return false;
    if (!is_noise) {
        PyErr_Format(PyExc_TypeError, "%s() requires a NoiseSource argument", method_name);
        return false;
    }

    PyNoiseSourceObject* source = (PyNoiseSourceObject*)source_obj;

    // Check NoiseSource is 2D
    if (source->dimensions != 2) {
        PyErr_Format(PyExc_ValueError,
            "%s() requires a 2D NoiseSource, but source has %d dimensions",
            method_name, source->dimensions);
        return false;
    }

    // Check NoiseSource is initialized
    if (!source->noise) {
        PyErr_SetString(PyExc_RuntimeError, "NoiseSource not initialized");
        return false;
    }

    // Parse world_origin (default: (0, 0))
    float origin_x = 0.0f, origin_y = 0.0f;
    if (origin_obj && origin_obj != Py_None) {
        if (!PyTuple_Check(origin_obj) || PyTuple_Size(origin_obj) != 2) {
            PyErr_SetString(PyExc_TypeError, "world_origin must be a tuple of (x, y)");
            return false;
        }
        PyObject* ox = PyTuple_GetItem(origin_obj, 0);
        PyObject* oy = PyTuple_GetItem(origin_obj, 1);
        if (PyFloat_Check(ox)) origin_x = (float)PyFloat_AsDouble(ox);
        else if (PyLong_Check(ox)) origin_x = (float)PyLong_AsLong(ox);
        else { PyErr_SetString(PyExc_TypeError, "world_origin values must be numeric"); return false; }
        if (PyFloat_Check(oy)) origin_y = (float)PyFloat_AsDouble(oy);
        else if (PyLong_Check(oy)) origin_y = (float)PyLong_AsLong(oy);
        else { PyErr_SetString(PyExc_TypeError, "world_origin values must be numeric"); return false; }
    }

    // Parse world_size (default: HeightMap size)
    float world_w = (float)hmap_w, world_h = (float)hmap_h;
    if (world_size_obj && world_size_obj != Py_None) {
        if (!PyTuple_Check(world_size_obj) || PyTuple_Size(world_size_obj) != 2) {
            PyErr_SetString(PyExc_TypeError, "world_size must be a tuple of (width, height)");
            return false;
        }
        PyObject* ww = PyTuple_GetItem(world_size_obj, 0);
        PyObject* wh = PyTuple_GetItem(world_size_obj, 1);
        if (PyFloat_Check(ww)) world_w = (float)PyFloat_AsDouble(ww);
        else if (PyLong_Check(ww)) world_w = (float)PyLong_AsLong(ww);
        else { PyErr_SetString(PyExc_TypeError, "world_size values must be numeric"); return false; }
        if (PyFloat_Check(wh)) world_h = (float)PyFloat_AsDouble(wh);
        else if (PyLong_Check(wh)) world_h = (float)PyLong_AsLong(wh);
        else { PyErr_SetString(PyExc_TypeError, "world_size values must be numeric"); return false; }
    }

    // Parse mode
    NoiseSampleMode mode;
    if (strcmp(mode_str, "flat") == 0) {
        mode = NoiseSampleMode::FLAT;
    } else if (strcmp(mode_str, "fbm") == 0) {
        mode = NoiseSampleMode::FBM;
    } else if (strcmp(mode_str, "turbulence") == 0) {
        mode = NoiseSampleMode::TURBULENCE;
    } else {
        PyErr_Format(PyExc_ValueError,
            "mode must be 'flat', 'fbm', or 'turbulence', got '%s'",
            mode_str);
        return false;
    }

    // Validate octaves
    if (octaves < 1 || octaves > TCOD_NOISE_MAX_OCTAVES) {
        PyErr_Format(PyExc_ValueError,
            "octaves must be between 1 and %d, got %d",
            TCOD_NOISE_MAX_OCTAVES, octaves);
        return false;
    }

    // Set outputs
    *out_source = source;
    *out_origin_x = origin_x;
    *out_origin_y = origin_y;
    *out_world_w = world_w;
    *out_world_h = world_h;
    *out_mode = mode;
    *out_octaves = octaves;
    *out_scale = scale;

    return true;
}

// Method: add_noise(source, ...) -> HeightMap
PyObject* PyHeightMap::add_noise(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
{
    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    PyNoiseSourceObject* source;
    float origin_x, origin_y, world_w, world_h, scale;
    NoiseSampleMode mode;
    int octaves;

    if (!parseNoiseSampleParams(args, kwds, &source,
                                 &origin_x, &origin_y, &world_w, &world_h,
                                 &mode, &octaves, &scale,
                                 self->heightmap->w, self->heightmap->h, "add_noise")) {
        return nullptr;
    }

    // Sample noise and add to heightmap
    float coords[2];
    for (int y = 0; y < self->heightmap->h; y++) {
        for (int x = 0; x < self->heightmap->w; x++) {
            coords[0] = origin_x + ((float)x / (float)self->heightmap->w) * world_w;
            coords[1] = origin_y + ((float)y / (float)self->heightmap->h) * world_h;

            float noise_value;
            switch (mode) {
                case NoiseSampleMode::FLAT:
                    noise_value = TCOD_noise_get(source->noise, coords);
                    break;
                case NoiseSampleMode::FBM:
                    noise_value = TCOD_noise_get_fbm(source->noise, coords, (float)octaves);
                    break;
                case NoiseSampleMode::TURBULENCE:
                    noise_value = TCOD_noise_get_turbulence(source->noise, coords, (float)octaves);
                    break;
            }

            float current = TCOD_heightmap_get_value(self->heightmap, x, y);
            TCOD_heightmap_set_value(self->heightmap, x, y, current + noise_value * scale);
        }
    }

    Py_INCREF(self);
    return (PyObject*)self;
}

// Method: multiply_noise(source, ...) -> HeightMap
PyObject* PyHeightMap::multiply_noise(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
{
    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    PyNoiseSourceObject* source;
    float origin_x, origin_y, world_w, world_h, scale;
    NoiseSampleMode mode;
    int octaves;

    if (!parseNoiseSampleParams(args, kwds, &source,
                                 &origin_x, &origin_y, &world_w, &world_h,
                                 &mode, &octaves, &scale,
                                 self->heightmap->w, self->heightmap->h, "multiply_noise")) {
        return nullptr;
    }

    // Sample noise and multiply with heightmap
    float coords[2];
    for (int y = 0; y < self->heightmap->h; y++) {
        for (int x = 0; x < self->heightmap->w; x++) {
            coords[0] = origin_x + ((float)x / (float)self->heightmap->w) * world_w;
            coords[1] = origin_y + ((float)y / (float)self->heightmap->h) * world_h;

            float noise_value;
            switch (mode) {
                case NoiseSampleMode::FLAT:
                    noise_value = TCOD_noise_get(source->noise, coords);
                    break;
                case NoiseSampleMode::FBM:
                    noise_value = TCOD_noise_get_fbm(source->noise, coords, (float)octaves);
                    break;
                case NoiseSampleMode::TURBULENCE:
                    noise_value = TCOD_noise_get_turbulence(source->noise, coords, (float)octaves);
                    break;
            }

            float current = TCOD_heightmap_get_value(self->heightmap, x, y);
            TCOD_heightmap_set_value(self->heightmap, x, y, current * (noise_value * scale));
        }
    }

    Py_INCREF(self);
    return (PyObject*)self;
}

// Helper: Collect BSP nodes based on select mode
static bool collectBSPNodes(
    PyBSPObject* bsp,
    const char* select_str,
    PyObject* nodes_list,
    std::vector<TCOD_bsp_t*>& out_nodes,
    const char* method_name)
{
    // If nodes list provided, use it directly
    if (nodes_list && nodes_list != Py_None) {
        if (!PyList_Check(nodes_list)) {
            PyErr_Format(PyExc_TypeError, "%s() nodes must be a list of BSPNode", method_name);
            return false;
        }

        PyObject* bspnode_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "BSPNode");
        if (!bspnode_type) {
            PyErr_SetString(PyExc_RuntimeError, "BSPNode type not found in module");
            return false;
        }

        Py_ssize_t count = PyList_Size(nodes_list);
        for (Py_ssize_t i = 0; i < count; i++) {
            PyObject* item = PyList_GetItem(nodes_list, i);
            int is_node = PyObject_IsInstance(item, bspnode_type);
            if (is_node < 0) {
                Py_DECREF(bspnode_type);
                return false;
            }
            if (!is_node) {
                Py_DECREF(bspnode_type);
                PyErr_Format(PyExc_TypeError, "%s() nodes[%zd] is not a BSPNode", method_name, i);
                return false;
            }

            PyBSPNodeObject* node = (PyBSPNodeObject*)item;
            if (!PyBSPNode::checkValid(node)) {
                Py_DECREF(bspnode_type);
                return false;  // Error already set
            }
            out_nodes.push_back(node->node);
        }
        Py_DECREF(bspnode_type);
        return true;
    }

    // Determine selection mode
    enum class SelectMode { LEAVES, ALL, INTERNAL };
    SelectMode select;
    if (strcmp(select_str, "leaves") == 0) {
        select = SelectMode::LEAVES;
    } else if (strcmp(select_str, "all") == 0) {
        select = SelectMode::ALL;
    } else if (strcmp(select_str, "internal") == 0) {
        select = SelectMode::INTERNAL;
    } else {
        PyErr_Format(PyExc_ValueError,
            "%s() select must be 'leaves', 'all', or 'internal', got '%s'",
            method_name, select_str);
        return false;
    }

    // Collect nodes from BSP tree
    // Use post-order traversal to collect all nodes
    std::vector<TCOD_bsp_t*> stack;
    stack.push_back(bsp->root);

    while (!stack.empty()) {
        TCOD_bsp_t* node = stack.back();
        stack.pop_back();

        bool is_leaf = TCOD_bsp_is_leaf(node);
        bool include = false;

        switch (select) {
            case SelectMode::LEAVES:
                include = is_leaf;
                break;
            case SelectMode::ALL:
                include = true;
                break;
            case SelectMode::INTERNAL:
                include = !is_leaf;
                break;
        }

        if (include) {
            out_nodes.push_back(node);
        }

        // Add children (if any) using libtcod functions
        TCOD_bsp_t* left = TCOD_bsp_left(node);
        TCOD_bsp_t* right = TCOD_bsp_right(node);
        if (left) stack.push_back(left);
        if (right) stack.push_back(right);
    }

    return true;
}

// Method: add_bsp(bsp, *, pos=None, select='leaves', nodes=None, shrink=0, value=1.0) -> HeightMap
PyObject* PyHeightMap::add_bsp(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
{
    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    static const char* keywords[] = {"bsp", "pos", "select", "nodes", "shrink", "value", nullptr};
    PyObject* bsp_obj = nullptr;
    PyObject* pos_obj = nullptr;
    const char* select_str = "leaves";
    PyObject* nodes_obj = nullptr;
    int shrink = 0;
    float value = 1.0f;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OsOif", const_cast<char**>(keywords),
                                     &bsp_obj, &pos_obj, &select_str, &nodes_obj, &shrink, &value)) {
        return nullptr;
    }

    // Validate bsp is a BSP
    PyObject* bsp_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "BSP");
    if (!bsp_type) {
        PyErr_SetString(PyExc_RuntimeError, "BSP type not found in module");
        return nullptr;
    }
    int is_bsp = PyObject_IsInstance(bsp_obj, bsp_type);
    Py_DECREF(bsp_type);

    if (is_bsp < 0) return nullptr;
    if (!is_bsp) {
        PyErr_SetString(PyExc_TypeError, "add_bsp() requires a BSP argument");
        return nullptr;
    }

    PyBSPObject* bsp = (PyBSPObject*)bsp_obj;
    if (!bsp->root) {
        PyErr_SetString(PyExc_RuntimeError, "BSP not initialized");
        return nullptr;
    }

    // Calculate offset for BSP coordinates
    // Default (pos=None): origin-relative like to_heightmap (-bsp.orig_x, -bsp.orig_y)
    // pos=(x, y): offset so BSP origin maps to (x, y) in heightmap
    int offset_x, offset_y;
    if (!pos_obj || pos_obj == Py_None) {
        // Origin-relative: translate BSP to (0, 0)
        offset_x = -bsp->orig_x;
        offset_y = -bsp->orig_y;
    } else {
        // Custom position
        int pos_x, pos_y;
        if (!parseOptionalPos(pos_obj, &pos_x, &pos_y, "pos")) {
            return nullptr;
        }
        offset_x = pos_x - bsp->orig_x;
        offset_y = pos_y - bsp->orig_y;
    }

    // Collect nodes
    std::vector<TCOD_bsp_t*> nodes;
    if (!collectBSPNodes(bsp, select_str, nodes_obj, nodes, "add_bsp")) {
        return nullptr;
    }

    // Add value to each node's region (with offset)
    for (TCOD_bsp_t* node : nodes) {
        int x1 = node->x + offset_x + shrink;
        int y1 = node->y + offset_y + shrink;
        int x2 = node->x + offset_x + node->w - shrink;
        int y2 = node->y + offset_y + node->h - shrink;

        // Clamp to heightmap bounds and skip if shrunk to nothing
        if (x1 >= x2 || y1 >= y2) continue;
        if (x1 < 0) x1 = 0;
        if (y1 < 0) y1 = 0;
        if (x2 > self->heightmap->w) x2 = self->heightmap->w;
        if (y2 > self->heightmap->h) y2 = self->heightmap->h;
        if (x1 >= self->heightmap->w || y1 >= self->heightmap->h) continue;
        if (x2 <= 0 || y2 <= 0) continue;

        for (int y = y1; y < y2; y++) {
            for (int x = x1; x < x2; x++) {
                float current = TCOD_heightmap_get_value(self->heightmap, x, y);
                TCOD_heightmap_set_value(self->heightmap, x, y, current + value);
            }
        }
    }

    Py_INCREF(self);
    return (PyObject*)self;
}

// Method: multiply_bsp(bsp, *, pos=None, select='leaves', nodes=None, shrink=0, value=1.0) -> HeightMap
PyObject* PyHeightMap::multiply_bsp(PyHeightMapObject* self, PyObject* args, PyObject* kwds)
{
    if (!self->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    static const char* keywords[] = {"bsp", "pos", "select", "nodes", "shrink", "value", nullptr};
    PyObject* bsp_obj = nullptr;
    PyObject* pos_obj = nullptr;
    const char* select_str = "leaves";
    PyObject* nodes_obj = nullptr;
    int shrink = 0;
    float value = 1.0f;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OsOif", const_cast<char**>(keywords),
                                     &bsp_obj, &pos_obj, &select_str, &nodes_obj, &shrink, &value)) {
        return nullptr;
    }

    // Validate bsp is a BSP
    PyObject* bsp_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "BSP");
    if (!bsp_type) {
        PyErr_SetString(PyExc_RuntimeError, "BSP type not found in module");
        return nullptr;
    }
    int is_bsp = PyObject_IsInstance(bsp_obj, bsp_type);
    Py_DECREF(bsp_type);

    if (is_bsp < 0) return nullptr;
    if (!is_bsp) {
        PyErr_SetString(PyExc_TypeError, "multiply_bsp() requires a BSP argument");
        return nullptr;
    }

    PyBSPObject* bsp = (PyBSPObject*)bsp_obj;
    if (!bsp->root) {
        PyErr_SetString(PyExc_RuntimeError, "BSP not initialized");
        return nullptr;
    }

    // Calculate offset for BSP coordinates
    int offset_x, offset_y;
    if (!pos_obj || pos_obj == Py_None) {
        // Origin-relative: translate BSP to (0, 0)
        offset_x = -bsp->orig_x;
        offset_y = -bsp->orig_y;
    } else {
        int pos_x, pos_y;
        if (!parseOptionalPos(pos_obj, &pos_x, &pos_y, "pos")) {
            return nullptr;
        }
        offset_x = pos_x - bsp->orig_x;
        offset_y = pos_y - bsp->orig_y;
    }

    // Collect nodes
    std::vector<TCOD_bsp_t*> nodes;
    if (!collectBSPNodes(bsp, select_str, nodes_obj, nodes, "multiply_bsp")) {
        return nullptr;
    }

    // Create a mask to track which cells are in regions
    std::vector<bool> in_region(self->heightmap->w * self->heightmap->h, false);

    for (TCOD_bsp_t* node : nodes) {
        int x1 = node->x + offset_x + shrink;
        int y1 = node->y + offset_y + shrink;
        int x2 = node->x + offset_x + node->w - shrink;
        int y2 = node->y + offset_y + node->h - shrink;

        // Clamp and skip if invalid
        if (x1 >= x2 || y1 >= y2) continue;
        if (x1 < 0) x1 = 0;
        if (y1 < 0) y1 = 0;
        if (x2 > self->heightmap->w) x2 = self->heightmap->w;
        if (y2 > self->heightmap->h) y2 = self->heightmap->h;
        if (x1 >= self->heightmap->w || y1 >= self->heightmap->h) continue;
        if (x2 <= 0 || y2 <= 0) continue;

        for (int y = y1; y < y2; y++) {
            for (int x = x1; x < x2; x++) {
                in_region[y * self->heightmap->w + x] = true;
            }
        }
    }

    // Apply: multiply by value inside regions, by 0 outside
    for (int y = 0; y < self->heightmap->h; y++) {
        for (int x = 0; x < self->heightmap->w; x++) {
            float current = TCOD_heightmap_get_value(self->heightmap, x, y);
            if (in_region[y * self->heightmap->w + x]) {
                TCOD_heightmap_set_value(self->heightmap, x, y, current * value);
            } else {
                TCOD_heightmap_set_value(self->heightmap, x, y, 0.0f);
            }
        }
    }

    Py_INCREF(self);
    return (PyObject*)self;
}
