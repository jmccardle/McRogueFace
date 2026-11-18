// VoxelPoint.cpp - Navigation grid cell implementation

#include "VoxelPoint.h"
#include "Viewport3D.h"
#include "PyWrap.h"
#include <cstdio>

// Default constructor
VoxelPoint::VoxelPoint()
    : walkable(true)
    , transparent(true)
    , height(0.0f)
    , cost(1.0f)
    , grid_x(0)
    , grid_z(0)
    , parent_viewport(nullptr)
{
}

// Constructor with position
VoxelPoint::VoxelPoint(int x, int z, mcrf::Viewport3D* parent)
    : walkable(true)
    , transparent(true)
    , height(0.0f)
    , cost(1.0f)
    , grid_x(x)
    , grid_z(z)
    , parent_viewport(parent)
{
}

// =============================================================================
// Python Property Accessors
// =============================================================================

VoxelPoint* VoxelPoint::resolve(PyVoxelPointObject* self, std::shared_ptr<mcrf::Viewport3D>& keep)
{
    keep = self->viewport;
    if (!keep || !keep->isValidCell(self->x, self->z)) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelPoint data is no longer valid");
        return nullptr;
    }
    return &keep->at(self->x, self->z);
}

// Member offsets for bool properties
enum VoxelPointBoolMember {
    VOXEL_WALKABLE = 0,
    VOXEL_TRANSPARENT = 1
};

// Member offsets for float properties
enum VoxelPointFloatMember {
    VOXEL_HEIGHT = 0,
    VOXEL_COST = 1
};

PyObject* VoxelPoint::get_bool_member(PyVoxelPointObject* self, void* closure)
{
    std::shared_ptr<mcrf::Viewport3D> keep;
    VoxelPoint* data = resolve(self, keep);
    if (!data) return NULL;

    intptr_t member = reinterpret_cast<intptr_t>(closure);
    bool value = false;

    switch (member) {
        case VOXEL_WALKABLE:
            value = data->walkable;
            break;
        case VOXEL_TRANSPARENT:
            value = data->transparent;
            break;
        default:
            PyErr_SetString(PyExc_AttributeError, "Invalid bool member");
            return NULL;
    }

    return PyBool_FromLong(value ? 1 : 0);
}

int VoxelPoint::set_bool_member(PyVoxelPointObject* self, PyObject* value, void* closure)
{

    // Exact bool / int only: an int SUBCLASS's __bool__ is user code that could resize the grid and
    // free the VoxelPoint this wrapper points at (a raw pointer into the nav grid, #558)
    if (!PyBool_Check(value) && !PyLong_CheckExact(value)) {
        PyErr_SetString(PyExc_TypeError, "Value must be a boolean");
        return -1;
    }

    const int newValue_truth = PyObject_IsTrue(value);
    if (newValue_truth < 0) return -1;
    bool newValue = newValue_truth != 0;
    intptr_t member = reinterpret_cast<intptr_t>(closure);

    std::shared_ptr<mcrf::Viewport3D> keep;
    VoxelPoint* data = resolve(self, keep);
    if (!data) return -1;

    switch (member) {
        case VOXEL_WALKABLE:
            data->walkable = newValue;
            break;
        case VOXEL_TRANSPARENT:
            data->transparent = newValue;
            break;
        default:
            PyErr_SetString(PyExc_AttributeError, "Invalid bool member");
            return -1;
    }

    // Trigger TCOD synchronization
    if (data->parent_viewport) {
        data->parent_viewport->syncTCODCell(data->grid_x, data->grid_z);
    }

    return 0;
}

PyObject* VoxelPoint::get_float_member(PyVoxelPointObject* self, void* closure)
{
    std::shared_ptr<mcrf::Viewport3D> keep;
    VoxelPoint* data = resolve(self, keep);
    if (!data) return NULL;

    intptr_t member = reinterpret_cast<intptr_t>(closure);
    float value = 0.0f;

    switch (member) {
        case VOXEL_HEIGHT:
            value = data->height;
            break;
        case VOXEL_COST:
            value = data->cost;
            break;
        default:
            PyErr_SetString(PyExc_AttributeError, "Invalid float member");
            return NULL;
    }

    return PyFloat_FromDouble(value);
}

int VoxelPoint::set_float_member(PyVoxelPointObject* self, PyObject* value, void* closure)
{

    // The project's checked float converter: TypeError for a non-number, ValueError for nan/inf,
    // OverflowError for a value outside float range (an int too big for a double included).
    float newValue;
    if (!mcrf::to_float(value, newValue, "Value")) return -1;

    intptr_t member = reinterpret_cast<intptr_t>(closure);

    std::shared_ptr<mcrf::Viewport3D> keep;
    VoxelPoint* data = resolve(self, keep);
    if (!data) return -1;

    switch (member) {
        case VOXEL_HEIGHT:
            data->height = newValue;
            break;
        case VOXEL_COST:
            if (newValue < 0.0f) {
                PyErr_SetString(PyExc_ValueError, "Cost must be non-negative");
                return -1;
            }
            data->cost = newValue;
            break;
        default:
            PyErr_SetString(PyExc_AttributeError, "Invalid float member");
            return -1;
    }

    return 0;
}

PyObject* VoxelPoint::get_grid_pos(PyVoxelPointObject* self, void* closure)
{
    std::shared_ptr<mcrf::Viewport3D> keep;
    VoxelPoint* data = resolve(self, keep);
    if (!data) return NULL;

    return Py_BuildValue("(ii)", data->grid_x, data->grid_z);
}

PyObject* VoxelPoint::get_entities(PyVoxelPointObject* self, void* closure)
{
    // TODO: Implement when Entity3D is created
    // For now, return an empty list
    return PyList_New(0);
}

PyObject* VoxelPoint::repr(PyVoxelPointObject* self)
{
    std::shared_ptr<mcrf::Viewport3D> keep = self->viewport;
    if (!keep || !keep->isValidCell(self->x, self->z)) {
        return PyUnicode_FromFormat("<VoxelPoint (%d, %d) stale>", self->x, self->z);
    }
    VoxelPoint* data = &keep->at(self->x, self->z);

    // Use snprintf then PyUnicode_FromString because PyUnicode_FromFormat doesn't support %.2f
    char buffer[128];
    snprintf(buffer, sizeof(buffer),
        "<VoxelPoint (%d, %d) walkable=%s transparent=%s height=%.2f cost=%.2f>",
        data->grid_x,
        data->grid_z,
        data->walkable ? "True" : "False",
        data->transparent ? "True" : "False",
        data->height,
        data->cost
    );
    return PyUnicode_FromString(buffer);
}

// =============================================================================
// Python GetSetDef Table
// =============================================================================

PyGetSetDef VoxelPoint::getsetters[] = {
    {"walkable", (getter)VoxelPoint::get_bool_member, (setter)VoxelPoint::set_bool_member,
     "Whether entities can walk through this cell.", (void*)VOXEL_WALKABLE},
    {"transparent", (getter)VoxelPoint::get_bool_member, (setter)VoxelPoint::set_bool_member,
     "Whether FOV can see through this cell.", (void*)VOXEL_TRANSPARENT},
    {"height", (getter)VoxelPoint::get_float_member, (setter)VoxelPoint::set_float_member,
     "World-space Y coordinate from terrain.", (void*)VOXEL_HEIGHT},
    {"cost", (getter)VoxelPoint::get_float_member, (setter)VoxelPoint::set_float_member,
     "Movement cost multiplier (1.0 = normal).", (void*)VOXEL_COST},
    {"grid_pos", (getter)VoxelPoint::get_grid_pos, NULL,
     "Grid coordinates as (x, z) tuple (read-only).", NULL},
    {"entities", (getter)VoxelPoint::get_entities, NULL,
     "List of Entity3D objects at this cell (read-only).", NULL},
    {NULL}  // Sentinel
};
