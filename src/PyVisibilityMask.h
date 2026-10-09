#pragma once
#include "Common.h"
#include "Python.h"
#include <vector>
#include <cstdint>

// PyVisibilityMask - mcrfpy.VisibilityMask
//
// An immutable, storable record of which cells were visible, from where, at
// which frame. Materialised: it holds the cell set, it does not recompute
// anything. Created ONLY by GridData.observe() (see PyGridDataMethods.cpp);
// tp_new raises TypeError so Python code cannot construct one directly.
//
// Storage: cells_set (frozenset) and cells_ordered (tuple, row-major) share
// the SAME (x, y) tuple objects -- building the ordered tuple first and then
// handing it to PyFrozenSet_New() costs one extra pointer array (the
// frozenset's hash table), not a second copy of the coordinate data.
//
// No GC support (Py_TPFLAGS_HAVE_GC is intentionally NOT set, and there is no
// tp_traverse/tp_clear): a VisibilityMask can only ever reference ints, tuples
// of ints, and frozensets of such tuples. None of those types can hold a
// reference back to a VisibilityMask, so a mask can never be part of a
// reference cycle. This is a deliberate omission, not an oversight.
struct PyVisibilityMaskObject {
    PyObject_HEAD
    PyObject* cells_set;      // frozenset[(int,int)] -- materialised visible cells
    PyObject* cells_ordered;  // tuple[(int,int)] -- same tuple objects, row-major order
    PyObject* origin;         // (int,int) tuple, or Py_None for an unbounded mask
    PyObject* fov_radius;     // int, or Py_None for unbounded/unlimited radius
    int tick;                 // engine current_frame when the mask was taken
    int grid_w, grid_h;       // dimensions of the grid this mask was taken from
    // #404 - fov_ran distinguishes "this parameter shaped the result" from "this
    // parameter was present and inert". An UNBOUNDED mask (origin=None) runs no FOV
    // computation at all -- every in-bounds cell is visible by construction -- so
    // light_walls and algorithm had no effect on it. Reporting them anyway makes a
    // stored belief-state record read as more specified than it is: anyone later
    // grouping runs by `algorithm` would pool masks that never ran an algorithm.
    // When fov_ran == 0, both properties answer None.
    int fov_ran;              // 1 if an FOV computation produced this mask, else 0
    int light_walls;          // 0/1, as passed to the FOV computation (fov_ran only)
    int algorithm;            // TCOD_fov_algorithm_t value used (matches mcrfpy.FOV.*)
};

class PyVisibilityMask {
public:
    // Internal factory used by GridData.observe(). Steals (takes ownership of)
    // all four PyObject* reference-counted arguments -- the caller must not
    // decref them afterward, and must not pass borrowed references. origin
    // must be either an (int,int) tuple or Py_None (with an owned reference,
    // i.e. Py_INCREF'd by the caller if it is Py_None); fov_radius must be
    // either a PyLong or Py_None, same ownership rule.
    // Returns a new reference to a fully-formed mcrfpy.VisibilityMask, or NULL
    // (with an exception set, and all four inputs already released) on failure.
    // #404: `fov_ran` says whether an FOV computation actually produced this mask.
    // light_walls/algorithm are recorded only when it did, and read back as None
    // otherwise -- a record must not report parameters that did not participate.
    static PyObject* create(PyObject* cells_set, PyObject* cells_ordered,
                            PyObject* origin, PyObject* fov_radius,
                            int tick, int grid_w, int grid_h,
                            bool fov_ran, bool light_walls, int algorithm);

    static void dealloc(PyVisibilityMaskObject* self);
    static PyObject* repr(PyVisibilityMaskObject* self);

    // Read-only properties
    static PyObject* get_origin(PyVisibilityMaskObject* self, void* closure);
    static PyObject* get_fov_radius(PyVisibilityMaskObject* self, void* closure);
    static PyObject* get_tick(PyVisibilityMaskObject* self, void* closure);
    static PyObject* get_cells(PyVisibilityMaskObject* self, void* closure);
    static PyObject* get_grid_size(PyVisibilityMaskObject* self, void* closure);
    static PyObject* get_light_walls(PyVisibilityMaskObject* self, void* closure);
    static PyObject* get_algorithm(PyVisibilityMaskObject* self, void* closure);

    // Protocol: len(mask), (x,y) in mask, iter(mask)
    static Py_ssize_t len(PyVisibilityMaskObject* self);
    static int contains(PyVisibilityMaskObject* self, PyObject* key);
    static PyObject* iter(PyVisibilityMaskObject* self);

    static PyGetSetDef getsetters[];
    static PySequenceMethods as_sequence;
};

namespace mcrfpydef {
    extern PyTypeObject PyVisibilityMaskType;
}
