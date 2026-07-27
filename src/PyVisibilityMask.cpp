// PyVisibilityMask.cpp - mcrfpy.VisibilityMask: an immutable, storable record
// of which cells were visible, from where, at which frame. See
// PyVisibilityMask.h for the storage/ownership contract and
// PyGridDataMethods.cpp (GridData.observe()) for the only code path that
// creates one.
#include "PyVisibilityMask.h"
#include "McRFPy_Doc.h"
#include "PyPositionHelper.h"

PyObject* PyVisibilityMask::create(PyObject* cells_set, PyObject* cells_ordered,
                                   PyObject* origin, PyObject* fov_radius,
                                   int tick, int grid_w, int grid_h,
                                   bool light_walls, int algorithm)
{
    PyVisibilityMaskObject* self = (PyVisibilityMaskObject*)
        mcrfpydef::PyVisibilityMaskType.tp_alloc(&mcrfpydef::PyVisibilityMaskType, 0);
    if (!self) {
        Py_DECREF(cells_set);
        Py_DECREF(cells_ordered);
        Py_DECREF(origin);
        Py_DECREF(fov_radius);
        return NULL;
    }

    // Ownership transfers in: these are already-owned references, not borrowed.
    self->cells_set = cells_set;
    self->cells_ordered = cells_ordered;
    self->origin = origin;
    self->fov_radius = fov_radius;
    self->tick = tick;
    self->grid_w = grid_w;
    self->grid_h = grid_h;
    self->light_walls = light_walls ? 1 : 0;
    self->algorithm = algorithm;

    return (PyObject*)self;
}

void PyVisibilityMask::dealloc(PyVisibilityMaskObject* self)
{
    Py_XDECREF(self->cells_set);
    Py_XDECREF(self->cells_ordered);
    Py_XDECREF(self->origin);
    Py_XDECREF(self->fov_radius);
    Py_TYPE(self)->tp_free((PyObject*)self);
}

PyObject* PyVisibilityMask::repr(PyVisibilityMaskObject* self)
{
    PyObject* origin_repr = PyObject_Repr(self->origin);
    if (!origin_repr) return NULL;
    PyObject* radius_repr = PyObject_Repr(self->fov_radius);
    if (!radius_repr) { Py_DECREF(origin_repr); return NULL; }

    Py_ssize_t ncells = PyTuple_GET_SIZE(self->cells_ordered);
    PyObject* result = PyUnicode_FromFormat(
        "<mcrfpy.VisibilityMask origin=%U fov_radius=%U tick=%d cells=%zd/%d>",
        origin_repr, radius_repr, self->tick, ncells, self->grid_w * self->grid_h);
    Py_DECREF(origin_repr);
    Py_DECREF(radius_repr);
    return result;
}

PyObject* PyVisibilityMask::get_origin(PyVisibilityMaskObject* self, void* closure)
{
    Py_INCREF(self->origin);
    return self->origin;
}

PyObject* PyVisibilityMask::get_fov_radius(PyVisibilityMaskObject* self, void* closure)
{
    Py_INCREF(self->fov_radius);
    return self->fov_radius;
}

PyObject* PyVisibilityMask::get_tick(PyVisibilityMaskObject* self, void* closure)
{
    return PyLong_FromLong(self->tick);
}

PyObject* PyVisibilityMask::get_cells(PyVisibilityMaskObject* self, void* closure)
{
    // Safe to hand out the stored frozenset directly (not a copy): frozensets
    // are immutable, so there is no aliasing hazard in returning it repeatedly.
    Py_INCREF(self->cells_set);
    return self->cells_set;
}

PyObject* PyVisibilityMask::get_grid_size(PyVisibilityMaskObject* self, void* closure)
{
    return Py_BuildValue("(ii)", self->grid_w, self->grid_h);
}

PyObject* PyVisibilityMask::get_light_walls(PyVisibilityMaskObject* self, void* closure)
{
    return PyBool_FromLong(self->light_walls);
}

PyObject* PyVisibilityMask::get_algorithm(PyVisibilityMaskObject* self, void* closure)
{
    return PyLong_FromLong(self->algorithm);
}

Py_ssize_t PyVisibilityMask::len(PyVisibilityMaskObject* self)
{
    return PyTuple_GET_SIZE(self->cells_ordered);
}

int PyVisibilityMask::contains(PyVisibilityMaskObject* self, PyObject* key)
{
    // (x, y) in mask -- O(1) via the frozenset. A key that is not a valid
    // position PROPAGATES the TypeError rather than answering False: asking
    // "is this entity in the mask" or "is this 3-tuple in the mask" is a
    // caller bug, and a silent False is a wrong answer that looks like a
    // right one. (Some older containers in this codebase swallow it; that is
    // not a precedent worth copying for a type whose whole job is to be a
    // trustworthy record of what was visible.)
    int x, y;
    if (!PyPosition_FromObjectInt(key, &x, &y)) {
        return -1;
    }
    PyObject* pos = Py_BuildValue("(ii)", x, y);
    if (!pos) return -1;
    int found = PySet_Contains(self->cells_set, pos);
    Py_DECREF(pos);
    return found;
}

PyObject* PyVisibilityMask::iter(PyVisibilityMaskObject* self)
{
    // The ordered tuple already holds cells in row-major order; reuse its
    // own iterator rather than building a second structure.
    return PyObject_GetIter(self->cells_ordered);
}

PyGetSetDef PyVisibilityMask::getsetters[] = {
    {"origin", (getter)PyVisibilityMask::get_origin, NULL,
     MCRF_PROPERTY(origin,
         "The observing cell as (x, y), or None for an unbounded mask "
         "(tuple | None, read-only)."), NULL},
    {"fov_radius", (getter)PyVisibilityMask::get_fov_radius, NULL,
     MCRF_PROPERTY(fov_radius,
         "Maximum view distance used to compute this mask, or None if the mask is "
         "unbounded or has an unlimited radius (int | None, read-only)."), NULL},
    {"tick", (getter)PyVisibilityMask::get_tick, NULL,
     MCRF_PROPERTY(tick,
         "Engine current_frame at the moment this mask was taken (int, read-only)."), NULL},
    {"cells", (getter)PyVisibilityMask::get_cells, NULL,
     MCRF_PROPERTY(cells,
         "The materialised set of visible cells, as (x, y) pairs "
         "(frozenset, read-only)."), NULL},
    {"grid_size", (getter)PyVisibilityMask::get_grid_size, NULL,
     MCRF_PROPERTY(grid_size,
         "Dimensions of the grid this mask was taken from, as (w, h) (tuple, read-only)."), NULL},
    {"light_walls", (getter)PyVisibilityMask::get_light_walls, NULL,
     MCRF_PROPERTY(light_walls,
         "Whether walls were lit when visible in the FOV computation that produced this "
         "mask (bool, read-only)."), NULL},
    {"algorithm", (getter)PyVisibilityMask::get_algorithm, NULL,
     MCRF_PROPERTY(algorithm,
         "FOV algorithm used to compute this mask, matching one of the mcrfpy.FOV.* "
         "values (int, read-only)."), NULL},
    {NULL}
};

PySequenceMethods PyVisibilityMask::as_sequence = {
    .sq_length = (lenfunc)PyVisibilityMask::len,
    .sq_contains = (objobjproc)PyVisibilityMask::contains,
};

namespace mcrfpydef {
    PyTypeObject PyVisibilityMaskType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.VisibilityMask",
        .tp_basicsize = sizeof(PyVisibilityMaskObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)PyVisibilityMask::dealloc,
        .tp_repr = (reprfunc)PyVisibilityMask::repr,
        .tp_as_sequence = &PyVisibilityMask::as_sequence,
        // No Py_TPFLAGS_HAVE_GC: see the comment on PyVisibilityMaskObject in
        // PyVisibilityMask.h for why this type can never be part of a cycle.
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR(
            "An immutable, storable record of which cells were visible, from where, "
            "at which frame.\n\n"
            "Created by GridData.observe(); cannot be instantiated directly. Use this "
            "for fog-of-war persistence, replaying an AI's past perception, or any "
            "case where 'what could this observer see' needs to be a value you can "
            "store, compare, and hand to other code -- rather than something you have "
            "to recompute from compute_fov()/is_in_fov() every time you need it.\n\n"
            "Properties:\n"
            "    origin (tuple | None, read-only): Observing cell, or None if unbounded\n"
            "    fov_radius (int | None, read-only): Radius used, or None if unlimited\n"
            "    tick (int, read-only): Engine current_frame when this mask was taken\n"
            "    cells (frozenset, read-only): The visible (x, y) cells\n"
            "    grid_size (tuple, read-only): (w, h) of the source grid\n"
            "    light_walls (bool, read-only): Whether walls were lit when visible\n"
            "    algorithm (int, read-only): FOV algorithm used (mcrfpy.FOV.*)\n\n"
            "Protocol:\n"
            "    (x, y) in mask   -- O(1) membership test; raises TypeError if the\n"
            "                        key is not a position (an entity, a 3-tuple, ...),\n"
            "                        rather than silently answering False\n"
            "    len(mask)        -- number of visible cells\n"
            "    iter(mask)       -- yields (x, y) in row-major order\n\n"
            "Example:\n"
            "    snap = grid_data.observe(origin=(5, 5), fov_radius=8)\n"
            "    if (5, 6) in snap['mask']:\n"
            "        ...\n"),
        .tp_iter = (getiterfunc)PyVisibilityMask::iter,
        .tp_getset = PyVisibilityMask::getsetters,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            (void)type; (void)args; (void)kwds;
            PyErr_SetString(PyExc_TypeError,
                "VisibilityMask is created by GridData.observe(); it cannot be constructed directly");
            return NULL;
        },
    };
}
