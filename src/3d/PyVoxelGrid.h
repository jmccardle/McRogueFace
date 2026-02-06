// PyVoxelGrid.h - Python bindings for VoxelGrid
// Part of McRogueFace 3D Extension - Milestones 9, 11
#pragma once

#include "../Common.h"
#include "Python.h"
#include "VoxelGrid.h"
#include <memory>

// =============================================================================
// Python object structures
// =============================================================================

typedef struct PyVoxelGridObject {
    PyObject_HEAD
    std::shared_ptr<mcrf::VoxelGrid> data;
    PyObject* weakreflist;
} PyVoxelGridObject;

typedef struct PyVoxelRegionObject {
    PyObject_HEAD
    std::shared_ptr<mcrf::VoxelRegion> data;
} PyVoxelRegionObject;

// =============================================================================
// Python binding classes
// =============================================================================

class PyVoxelGrid {
public:
    // Python type interface
    static PyObject* pynew(PyTypeObject* type, PyObject* args, PyObject* kwds);
    static int init(PyVoxelGridObject* self, PyObject* args, PyObject* kwds);
    static void dealloc(PyVoxelGridObject* self);
    static PyObject* repr(PyObject* obj);

    // Properties - dimensions (read-only)
    static PyObject* get_size(PyVoxelGridObject* self, void* closure);
    static PyObject* get_width(PyVoxelGridObject* self, void* closure);
    static PyObject* get_height(PyVoxelGridObject* self, void* closure);
    static PyObject* get_depth(PyVoxelGridObject* self, void* closure);
    static PyObject* get_cell_size(PyVoxelGridObject* self, void* closure);
    static PyObject* get_material_count(PyVoxelGridObject* self, void* closure);

    // Properties - transform (read-write)
    static PyObject* get_offset(PyVoxelGridObject* self, void* closure);
    static int set_offset(PyVoxelGridObject* self, PyObject* value, void* closure);
    static PyObject* get_rotation(PyVoxelGridObject* self, void* closure);
    static int set_rotation(PyVoxelGridObject* self, PyObject* value, void* closure);

    // Properties - mesh generation (Milestone 13)
    static PyObject* get_greedy_meshing(PyVoxelGridObject* self, void* closure);
    static int set_greedy_meshing(PyVoxelGridObject* self, PyObject* value, void* closure);

    // Properties - visibility
    static PyObject* get_visible(PyVoxelGridObject* self, void* closure);
    static int set_visible(PyVoxelGridObject* self, PyObject* value, void* closure);

    // Voxel access methods
    static PyObject* get(PyVoxelGridObject* self, PyObject* args);
    static PyObject* set(PyVoxelGridObject* self, PyObject* args);

    // Material methods
    static PyObject* add_material(PyVoxelGridObject* self, PyObject* args, PyObject* kwds);
    static PyObject* get_material(PyVoxelGridObject* self, PyObject* args);

    // Bulk operations
    static PyObject* fill(PyVoxelGridObject* self, PyObject* args);
    static PyObject* fill_box(PyVoxelGridObject* self, PyObject* args);
    static PyObject* clear(PyVoxelGridObject* self, PyObject* Py_UNUSED(args));

    // Bulk operations - Milestone 11
    static PyObject* fill_box_hollow(PyVoxelGridObject* self, PyObject* args, PyObject* kwds);
    static PyObject* fill_sphere(PyVoxelGridObject* self, PyObject* args);
    static PyObject* fill_cylinder(PyVoxelGridObject* self, PyObject* args);
    static PyObject* fill_noise(PyVoxelGridObject* self, PyObject* args, PyObject* kwds);

    // Copy/paste operations - Milestone 11
    static PyObject* copy_region(PyVoxelGridObject* self, PyObject* args);
    static PyObject* paste_region(PyVoxelGridObject* self, PyObject* args, PyObject* kwds);

    // Mesh caching (Milestone 10)
    static PyObject* get_vertex_count(PyVoxelGridObject* self, void* closure);
    static PyObject* rebuild_mesh(PyVoxelGridObject* self, PyObject* Py_UNUSED(args));

    // Serialization (Milestone 14)
    static PyObject* save(PyVoxelGridObject* self, PyObject* args);
    static PyObject* load(PyVoxelGridObject* self, PyObject* args);
    static PyObject* to_bytes(PyVoxelGridObject* self, PyObject* Py_UNUSED(args));
    static PyObject* from_bytes(PyVoxelGridObject* self, PyObject* args);

    // Statistics
    static PyObject* count_non_air(PyVoxelGridObject* self, PyObject* Py_UNUSED(args));
    static PyObject* count_material(PyVoxelGridObject* self, PyObject* args);

    // Type registration
    static PyMethodDef methods[];
    static PyGetSetDef getsetters[];
};

class PyVoxelRegion {
public:
    static void dealloc(PyVoxelRegionObject* self);
    static PyObject* repr(PyObject* obj);
    static PyObject* get_size(PyVoxelRegionObject* self, void* closure);
    static PyObject* get_width(PyVoxelRegionObject* self, void* closure);
    static PyObject* get_height(PyVoxelRegionObject* self, void* closure);
    static PyObject* get_depth(PyVoxelRegionObject* self, void* closure);

    static PyGetSetDef getsetters[];
};

// =============================================================================
// Python type definitions (in mcrfpydef namespace)
// =============================================================================

namespace mcrfpydef {

inline PyTypeObject PyVoxelGridType = {
    .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
    .tp_name = "mcrfpy.VoxelGrid",
    .tp_basicsize = sizeof(PyVoxelGridObject),
    .tp_itemsize = 0,
    .tp_dealloc = (destructor)PyVoxelGrid::dealloc,
    .tp_repr = PyVoxelGrid::repr,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC,
    .tp_doc = PyDoc_STR(
        "VoxelGrid(size: tuple[int, int, int], cell_size: float = 1.0)\n\n"
        "A dense 3D grid of voxel material IDs with a material palette.\n\n"
        "VoxelGrids provide volumetric storage for 3D structures like buildings,\n"
        "caves, and dungeon walls. Each cell stores a uint8 material ID (0-255),\n"
        "where 0 is always air.\n\n"
        "Args:\n"
        "    size: (width, height, depth) dimensions. Immutable after creation.\n"
        "    cell_size: World units per voxel. Default 1.0.\n\n"
        "Properties:\n"
        "    size (tuple, read-only): Grid dimensions as (width, height, depth)\n"
        "    width, height, depth (int, read-only): Individual dimensions\n"
        "    cell_size (float, read-only): World units per voxel\n"
        "    offset (tuple): World-space position (x, y, z)\n"
        "    rotation (float): Y-axis rotation in degrees\n"
        "    material_count (int, read-only): Number of defined materials\n\n"
        "Example:\n"
        "    voxels = mcrfpy.VoxelGrid(size=(16, 8, 16), cell_size=1.0)\n"
        "    stone = voxels.add_material('stone', color=mcrfpy.Color(128, 128, 128))\n"
        "    voxels.set(5, 0, 5, stone)\n"
        "    assert voxels.get(5, 0, 5) == stone\n"
        "    print(f'Non-air voxels: {voxels.count_non_air()}')"
    ),
    .tp_traverse = [](PyObject* self, visitproc visit, void* arg) -> int {
        return 0;
    },
    .tp_clear = [](PyObject* self) -> int {
        return 0;
    },
    .tp_weaklistoffset = offsetof(PyVoxelGridObject, weakreflist),
    .tp_methods = nullptr,  // Set before PyType_Ready
    .tp_getset = nullptr,   // Set before PyType_Ready
    .tp_init = (initproc)PyVoxelGrid::init,
    .tp_new = PyVoxelGrid::pynew,
};

inline PyTypeObject PyVoxelRegionType = {
    .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
    .tp_name = "mcrfpy.VoxelRegion",
    .tp_basicsize = sizeof(PyVoxelRegionObject),
    .tp_itemsize = 0,
    .tp_dealloc = (destructor)PyVoxelRegion::dealloc,
    .tp_repr = PyVoxelRegion::repr,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_doc = PyDoc_STR(
        "VoxelRegion - Portable voxel data for copy/paste operations.\n\n"
        "Created by VoxelGrid.copy_region(), used with paste_region().\n"
        "Cannot be instantiated directly.\n\n"
        "Properties:\n"
        "    size (tuple, read-only): Dimensions as (width, height, depth)\n"
        "    width, height, depth (int, read-only): Individual dimensions"
    ),
    .tp_getset = nullptr,  // Set before PyType_Ready
    .tp_new = nullptr,  // Cannot instantiate directly
};

} // namespace mcrfpydef
