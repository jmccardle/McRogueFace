#pragma once
#include "PyPositionHelper.h"
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

    // #445: the intersect-mode companion to parseMapRegion(), which REJECTS a region
    // that leaves the map. This CLIPS instead: the half-open rectangle [x0, x1) x
    // [y0, y1) is intersected with a src_w x src_h map and becomes a region that copies
    // that window of the source to (0, 0) of a window-sized destination. width/height
    // are 0 when the rectangle misses the map entirely.
    static MapRegion window(int x0, int y0, int x1, int y1, int src_w, int src_h) {
        MapRegion r{};
        r.src_x = std::max(0, x0);
        r.src_y = std::max(0, y0);
        r.width = std::max(0, std::min(src_w, x1) - r.src_x);
        r.height = std::max(0, std::min(src_h, y1) - r.src_y);
        r.dest_x = r.dest_y = 0;
        r.dest_w = r.width;
        r.dest_h = r.height;
        r.src_w = src_w;
        r.src_h = src_h;
        return r;
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

// Parse optional position, returning (0, 0) if None/not provided. The integer position helper:
// a Vector, tuple, list or 2-sequence; floats floor; out of int range is OverflowError (the old
// (int)PyLong_AsLong wrapped 2**32 to 0 and left an error pending); user code in a conversion is
// fine here because the caller reads the maps AFTER this returns (#558).
inline bool parseOptionalPos(PyObject* pos_obj, int* out_x, int* out_y, const char* param_name) {
    *out_x = 0;
    *out_y = 0;

    if (!pos_obj || pos_obj == Py_None) {
        return true;  // Default to (0, 0)
    }
    return PyPosition_FromObjectInt(pos_obj, out_x, out_y, param_name);
}

// Parse optional size ((-1, -1) when not given); a given size must be positive
inline bool parseOptionalSize(PyObject* size_obj, int* out_w, int* out_h, const char* param_name) {
    *out_w = -1;  // -1 means "not specified"
    *out_h = -1;

    if (!size_obj || size_obj == Py_None) {
        return true;
    }

    int w, h;
    if (!PyPosition_FromObjectInt(size_obj, &w, &h, param_name)) {
        return false;
    }
    if (w <= 0 || h <= 0) {
        PyErr_Format(PyExc_ValueError, "%s dimensions must be positive", param_name);
        return false;
    }
    *out_w = w;
    *out_h = h;
    return true;
}

} // namespace MapOpsInternal

// ============================================================================
// parseMapRegion - Parse region parameters for binary operations
// ============================================================================

// For binary operations (two maps). `dest` / `src` are the map OBJECTS (anything with w, h, values):
// #558 -- the pos / source_pos / size conversions run user code (__index__, __float__) that can
// re-initialise either map, so the dimensions are read only AFTER they finish, never passed in.
template <typename D, typename S>
inline bool parseMapRegion(
    const D* dest_map,
    const S* src_map,
    PyObject* pos,              // (x, y) or None - destination position
    PyObject* source_pos,       // (x, y) or None - source position
    PyObject* size,             // (w, h) or None
    MapRegion& out
) {
    using namespace MapOpsInternal;

    // Phase 1: Python-capable conversions only
    if (!parseOptionalPos(pos, &out.dest_x, &out.dest_y, "pos")) {
        return false;
    }
    if (!parseOptionalPos(source_pos, &out.src_x, &out.src_y, "source_pos")) {
        return false;
    }
    int requested_w = -1, requested_h = -1;
    if (!parseOptionalSize(size, &requested_w, &requested_h, "size")) {
        return false;
    }

    // Phase 2: no Python from here on; read the maps as they are NOW
    if (!dest_map->values || !src_map->values) {
        PyErr_SetString(PyExc_RuntimeError, "DiscreteMap not initialized");
        return false;
    }
    out.dest_w = dest_map->w;
    out.dest_h = dest_map->h;
    out.src_w = src_map->w;
    out.src_h = src_map->h;

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

    // Infer size, or use the requested one
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
template <typename D>
inline bool parseMapRegionScalar(
    const D* dest_map,
    PyObject* pos,
    PyObject* size,
    MapRegion& out
) {
    return parseMapRegion(dest_map, dest_map, pos, nullptr, size, out);
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
