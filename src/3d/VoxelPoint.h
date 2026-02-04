// VoxelPoint.h - Navigation grid cell for 3D terrain
// Provides walkability, transparency, and cost data for pathfinding and FOV

#pragma once

#include "Common.h"
#include "Python.h"
#include "structmember.h"
#include <vector>

// Forward declarations
namespace mcrf {
class Viewport3D;
class Entity3D;
}

class VoxelPoint;

// Python object struct for VoxelPoint
typedef struct {
    PyObject_HEAD
    VoxelPoint* data;
    std::shared_ptr<mcrf::Viewport3D> viewport;
} PyVoxelPointObject;

// VoxelPoint - navigation grid cell for 3D terrain
// Similar to UIGridPoint but with height and cost for 3D pathfinding
class VoxelPoint {
public:
    // Navigation properties
    bool walkable = true;       // Can entities walk through this cell?
    bool transparent = true;    // Can FOV see through this cell?
    float height = 0.0f;        // World-space Y coordinate from terrain
    float cost = 1.0f;          // Movement cost multiplier (1.0 = normal)

    // Position in parent grid
    int grid_x = 0;
    int grid_z = 0;

    // Parent viewport reference for TCOD synchronization
    mcrf::Viewport3D* parent_viewport = nullptr;

    // Default constructor
    VoxelPoint();

    // Constructor with position
    VoxelPoint(int x, int z, mcrf::Viewport3D* parent);

    // Python property accessors
    static PyGetSetDef getsetters[];

    // Bool property getter/setter (walkable, transparent)
    static PyObject* get_bool_member(PyVoxelPointObject* self, void* closure);
    static int set_bool_member(PyVoxelPointObject* self, PyObject* value, void* closure);

    // Float property getter/setter (height, cost)
    static PyObject* get_float_member(PyVoxelPointObject* self, void* closure);
    static int set_float_member(PyVoxelPointObject* self, PyObject* value, void* closure);

    // grid_pos property (read-only tuple)
    static PyObject* get_grid_pos(PyVoxelPointObject* self, void* closure);

    // entities property (read-only list of Entity3D at this cell)
    static PyObject* get_entities(PyVoxelPointObject* self, void* closure);

    // __repr__
    static PyObject* repr(PyVoxelPointObject* self);
};

namespace mcrfpydef {

// Python type definition for VoxelPoint
inline PyTypeObject PyVoxelPointType = {
    .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
    .tp_name = "mcrfpy.VoxelPoint",
    .tp_basicsize = sizeof(PyVoxelPointObject),
    .tp_itemsize = 0,
    .tp_repr = (reprfunc)VoxelPoint::repr,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_doc = PyDoc_STR("VoxelPoint - Navigation grid cell for 3D terrain.\n\n"
                        "VoxelPoints are accessed via Viewport3D.at(x, z) and cannot be\n"
                        "instantiated directly.\n\n"
                        "Properties:\n"
                        "    walkable (bool): Can entities walk through this cell?\n"
                        "    transparent (bool): Can FOV see through this cell?\n"
                        "    height (float): World-space Y coordinate from terrain.\n"
                        "    cost (float): Movement cost multiplier (1.0 = normal).\n"
                        "    grid_pos (tuple, read-only): (x, z) position in grid.\n"
                        "    entities (list, read-only): Entity3D objects at this cell."),
    .tp_getset = VoxelPoint::getsetters,
    .tp_new = NULL,  // Cannot instantiate from Python - access via viewport.at()
};

} // namespace mcrfpydef
