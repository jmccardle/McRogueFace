#pragma once
#include "Python.h"
#include <algorithm>
#include <cstdint>

// ============================================================================
// MapOps - Template abstractions for 2D grid map operations
// ============================================================================
//
// Provides common operations for HeightMap (float) and DiscreteMap (uint8_t).
// Uses policy-based design for type-specific behavior (clamping, conversion).
//
// Benefits:
// - Single implementation for fill, copy, region iteration
// - Type-appropriate clamping via saturation policies
// - Compile-time polymorphism (no virtual overhead)
// - Shared region parameter parsing from Python kwargs
// ============================================================================

// Forward declarations
class PyPositionHelper;

// ============================================================================
// Unified region struct for all map operations
// ============================================================================

struct MapRegion {
    // Validated region coordinates
    int dest_x, dest_y;       // Destination origin in target map
    int src_x, src_y;         // Source origin (for binary ops, 0 for scalar ops)
    int width, height;        // Region dimensions

    // Full map dimensions (for iteration)
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

// ============================================================================
// Saturation Policies - type-specific clamping behavior
// ============================================================================

struct FloatPolicy {
    using Type = float;

    static float clamp(float v) { return v; }  // No clamping for float
    static float clamp(int v) { return static_cast<float>(v); }
    static float from_int(int v) { return static_cast<float>(v); }
    static float from_float(float v) { return v; }
    static float zero() { return 0.0f; }
    static float one() { return 1.0f; }
};

struct Uint8Policy {
    using Type = uint8_t;

    static uint8_t clamp(int v) {
        return static_cast<uint8_t>(std::clamp(v, 0, 255));
    }
    static uint8_t clamp(float v) {
        return static_cast<uint8_t>(std::clamp(static_cast<int>(v), 0, 255));
    }
    static uint8_t from_int(int v) { return clamp(v); }
    static uint8_t from_float(float v) { return clamp(static_cast<int>(v)); }
    static uint8_t zero() { return 0; }
    static uint8_t one() { return 1; }
};

// ============================================================================
// Region Parameter Parsing - shared helpers
// ============================================================================

namespace MapOpsInternal {

// Parse optional position tuple, returning (0, 0) if None/not provided
inline bool parseOptionalPos(PyObject* pos_obj, int* out_x, int* out_y, const char* param_name) {
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

    PyErr_Format(PyExc_TypeError, "%s must be a (x, y) tuple or list", param_name);
    return false;
}

// Parse optional size tuple
inline bool parseOptionalSize(PyObject* size_obj, int* out_w, int* out_h, const char* param_name) {
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

} // namespace MapOpsInternal

// ============================================================================
// parseMapRegion - Parse region parameters for binary operations
// ============================================================================

// For binary operations (two maps)
inline bool parseMapRegion(
    int dest_w, int dest_h,
    int src_w, int src_h,
    PyObject* pos,              // (x, y) or None - destination position
    PyObject* source_pos,       // (x, y) or None - source position
    PyObject* size,             // (w, h) or None
    MapRegion& out
) {
    using namespace MapOpsInternal;

    // Store full dimensions
    out.dest_w = dest_w;
    out.dest_h = dest_h;
    out.src_w = src_w;
    out.src_h = src_h;

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
    if (out.src_x < 0 || out.src_y < 0) {
        PyErr_SetString(PyExc_ValueError, "source_pos coordinates cannot be negative");
        return false;
    }
    if (out.src_x >= out.src_w || out.src_y >= out.src_h) {
        PyErr_Format(PyExc_ValueError,
            "source_pos (%d, %d) is out of bounds for source of size (%d, %d)",
            out.src_x, out.src_y, out.src_w, out.src_h);
        return false;
    }

    // Calculate remaining space from each position
    int dest_remaining_w = out.dest_w - out.dest_x;
    int dest_remaining_h = out.dest_h - out.dest_y;
    int src_remaining_w = out.src_w - out.src_x;
    int src_remaining_h = out.src_h - out.src_y;

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
        if (requested_w > src_remaining_w || requested_h > src_remaining_h) {
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

// For scalar operations (single map, just destination region)
inline bool parseMapRegionScalar(
    int dest_w, int dest_h,
    PyObject* pos,
    PyObject* size,
    MapRegion& out
) {
    return parseMapRegion(dest_w, dest_h, dest_w, dest_h, pos, nullptr, size, out);
}

// ============================================================================
// Core map operations as free functions (used by both HeightMap and DiscreteMap)
// ============================================================================

namespace MapOps {

// Fill region with value
template<typename Policy>
void fill(typename Policy::Type* data, int w, int h,
          typename Policy::Type value, const MapRegion& region) {
    for (int y = 0; y < region.height; y++) {
        for (int x = 0; x < region.width; x++) {
            data[region.dest_idx(x, y)] = value;
        }
    }
}

// Clear (fill with zero)
template<typename Policy>
void clear(typename Policy::Type* data, int w, int h, const MapRegion& region) {
    fill<Policy>(data, w, h, Policy::zero(), region);
}

// Copy from source (same type)
template<typename Policy>
void copy(typename Policy::Type* dst, const typename Policy::Type* src,
          const MapRegion& region) {
    using T = typename Policy::Type;
    for (int y = 0; y < region.height; y++) {
        for (int x = 0; x < region.width; x++) {
            dst[region.dest_idx(x, y)] = src[region.src_idx(x, y)];
        }
    }
}

// Add with saturation
template<typename Policy>
void add(typename Policy::Type* dst, const typename Policy::Type* src,
         const MapRegion& region) {
    using T = typename Policy::Type;
    for (int y = 0; y < region.height; y++) {
        for (int x = 0; x < region.width; x++) {
            int idx = region.dest_idx(x, y);
            // Use int accumulator to detect overflow
            int result = static_cast<int>(dst[idx]) + static_cast<int>(src[region.src_idx(x, y)]);
            dst[idx] = Policy::clamp(result);
        }
    }
}

// Add scalar
template<typename Policy>
void add_scalar(typename Policy::Type* data, int w, int h,
                typename Policy::Type value, const MapRegion& region) {
    using T = typename Policy::Type;
    for (int y = 0; y < region.height; y++) {
        for (int x = 0; x < region.width; x++) {
            int idx = region.dest_idx(x, y);
            int result = static_cast<int>(data[idx]) + static_cast<int>(value);
            data[idx] = Policy::clamp(result);
        }
    }
}

// Subtract with saturation
template<typename Policy>
void subtract(typename Policy::Type* dst, const typename Policy::Type* src,
              const MapRegion& region) {
    using T = typename Policy::Type;
    for (int y = 0; y < region.height; y++) {
        for (int x = 0; x < region.width; x++) {
            int idx = region.dest_idx(x, y);
            int result = static_cast<int>(dst[idx]) - static_cast<int>(src[region.src_idx(x, y)]);
            dst[idx] = Policy::clamp(result);
        }
    }
}

// Multiply by scalar
template<typename Policy>
void multiply_scalar(typename Policy::Type* data, int w, int h,
                     float factor, const MapRegion& region) {
    using T = typename Policy::Type;
    for (int y = 0; y < region.height; y++) {
        for (int x = 0; x < region.width; x++) {
            int idx = region.dest_idx(x, y);
            float result = static_cast<float>(data[idx]) * factor;
            data[idx] = Policy::clamp(result);
        }
    }
}

// Element-wise max
template<typename Policy>
void element_max(typename Policy::Type* dst, const typename Policy::Type* src,
                 const MapRegion& region) {
    using T = typename Policy::Type;
    for (int y = 0; y < region.height; y++) {
        for (int x = 0; x < region.width; x++) {
            int idx = region.dest_idx(x, y);
            T src_val = src[region.src_idx(x, y)];
            if (src_val > dst[idx]) dst[idx] = src_val;
        }
    }
}

// Element-wise min
template<typename Policy>
void element_min(typename Policy::Type* dst, const typename Policy::Type* src,
                 const MapRegion& region) {
    using T = typename Policy::Type;
    for (int y = 0; y < region.height; y++) {
        for (int x = 0; x < region.width; x++) {
            int idx = region.dest_idx(x, y);
            T src_val = src[region.src_idx(x, y)];
            if (src_val < dst[idx]) dst[idx] = src_val;
        }
    }
}

} // namespace MapOps

// ============================================================================
// Cross-type operations (HeightMap <-> DiscreteMap conversion)
// ============================================================================

namespace MapConvert {

// Copy float to uint8_t (floors and clamps)
inline void float_to_uint8(uint8_t* dst, const float* src, const MapRegion& region) {
    for (int y = 0; y < region.height; y++) {
        for (int x = 0; x < region.width; x++) {
            float val = src[region.src_idx(x, y)];
            dst[region.dest_idx(x, y)] = Uint8Policy::clamp(val);
        }
    }
}

// Copy uint8_t to float (simple promotion)
inline void uint8_to_float(float* dst, const uint8_t* src, const MapRegion& region) {
    for (int y = 0; y < region.height; y++) {
        for (int x = 0; x < region.width; x++) {
            dst[region.dest_idx(x, y)] = static_cast<float>(src[region.src_idx(x, y)]);
        }
    }
}

// Add float to uint8_t (with clamping)
inline void add_float_to_uint8(uint8_t* dst, const float* src, const MapRegion& region) {
    for (int y = 0; y < region.height; y++) {
        for (int x = 0; x < region.width; x++) {
            int idx = region.dest_idx(x, y);
            float result = static_cast<float>(dst[idx]) + src[region.src_idx(x, y)];
            dst[idx] = Uint8Policy::clamp(result);
        }
    }
}

// Add uint8_t to float
inline void add_uint8_to_float(float* dst, const uint8_t* src, const MapRegion& region) {
    for (int y = 0; y < region.height; y++) {
        for (int x = 0; x < region.width; x++) {
            int idx = region.dest_idx(x, y);
            dst[idx] += static_cast<float>(src[region.src_idx(x, y)]);
        }
    }
}

} // namespace MapConvert

// ============================================================================
// Uint8-only bitwise operations
// ============================================================================

namespace MapBitwise {

inline void bitwise_and(uint8_t* dst, const uint8_t* src, const MapRegion& region) {
    for (int y = 0; y < region.height; y++) {
        for (int x = 0; x < region.width; x++) {
            dst[region.dest_idx(x, y)] &= src[region.src_idx(x, y)];
        }
    }
}

inline void bitwise_or(uint8_t* dst, const uint8_t* src, const MapRegion& region) {
    for (int y = 0; y < region.height; y++) {
        for (int x = 0; x < region.width; x++) {
            dst[region.dest_idx(x, y)] |= src[region.src_idx(x, y)];
        }
    }
}

inline void bitwise_xor(uint8_t* dst, const uint8_t* src, const MapRegion& region) {
    for (int y = 0; y < region.height; y++) {
        for (int x = 0; x < region.width; x++) {
            dst[region.dest_idx(x, y)] ^= src[region.src_idx(x, y)];
        }
    }
}

inline void invert(uint8_t* data, int w, int h, const MapRegion& region) {
    for (int y = 0; y < region.height; y++) {
        for (int x = 0; x < region.width; x++) {
            int idx = region.dest_idx(x, y);
            data[idx] = 255 - data[idx];
        }
    }
}

} // namespace MapBitwise
