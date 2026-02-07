// VoxelPoint.cpp - Navigation grid cell implementation

#include "VoxelPoint.h"
#include "Viewport3D.h"
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
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelPoint data is null");
        return NULL;
    }

    intptr_t member = reinterpret_cast<intptr_t>(closure);
    bool value = false;

    switch (member) {
        case VOXEL_WALKABLE:
            value = self->data->walkable;
            break;
        case VOXEL_TRANSPARENT:
            value = self->data->transparent;
            break;
        default:
            PyErr_SetString(PyExc_AttributeError, "Invalid bool member");
            return NULL;
    }

    return PyBool_FromLong(value ? 1 : 0);
}

int VoxelPoint::set_bool_member(PyVoxelPointObject* self, PyObject* value, void* closure)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelPoint data is null");
        return -1;
    }

    if (!PyBool_Check(value) && !PyLong_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "Value must be a boolean");
        return -1;
    }

    bool newValue = PyObject_IsTrue(value);
    intptr_t member = reinterpret_cast<intptr_t>(closure);

    switch (member) {
        case VOXEL_WALKABLE:
            self->data->walkable = newValue;
            break;
        case VOXEL_TRANSPARENT:
            self->data->transparent = newValue;
            break;
        default:
            PyErr_SetString(PyExc_AttributeError, "Invalid bool member");
            return -1;
    }

    // Trigger TCOD synchronization
    if (self->data->parent_viewport) {
        self->data->parent_viewport->syncTCODCell(self->data->grid_x, self->data->grid_z);
    }

    return 0;
}

PyObject* VoxelPoint::get_float_member(PyVoxelPointObject* self, void* closure)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelPoint data is null");
        return NULL;
    }

    intptr_t member = reinterpret_cast<intptr_t>(closure);
    float value = 0.0f;

    switch (member) {
        case VOXEL_HEIGHT:
            value = self->data->height;
            break;
        case VOXEL_COST:
            value = self->data->cost;
            break;
        default:
            PyErr_SetString(PyExc_AttributeError, "Invalid float member");
            return NULL;
    }

    return PyFloat_FromDouble(value);
}

int VoxelPoint::set_float_member(PyVoxelPointObject* self, PyObject* value, void* closure)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelPoint data is null");
        return -1;
    }

    double newValue;
    if (PyFloat_Check(value)) {
        newValue = PyFloat_AsDouble(value);
    } else if (PyLong_Check(value)) {
        newValue = static_cast<double>(PyLong_AsLong(value));
    } else {
        PyErr_SetString(PyExc_TypeError, "Value must be a number");
        return -1;
    }

    intptr_t member = reinterpret_cast<intptr_t>(closure);

    switch (member) {
        case VOXEL_HEIGHT:
            self->data->height = static_cast<float>(newValue);
            break;
        case VOXEL_COST:
            if (newValue < 0.0) {
                PyErr_SetString(PyExc_ValueError, "Cost must be non-negative");
                return -1;
            }
            self->data->cost = static_cast<float>(newValue);
            break;
        default:
            PyErr_SetString(PyExc_AttributeError, "Invalid float member");
            return -1;
    }

    return 0;
}

PyObject* VoxelPoint::get_grid_pos(PyVoxelPointObject* self, void* closure)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelPoint data is null");
        return NULL;
    }

    return Py_BuildValue("(ii)", self->data->grid_x, self->data->grid_z);
}

PyObject* VoxelPoint::get_entities(PyVoxelPointObject* self, void* closure)
{
    // TODO: Implement when Entity3D is created
    // For now, return an empty list
    return PyList_New(0);
}

PyObject* VoxelPoint::repr(PyVoxelPointObject* self)
{
    if (!self->data) {
        return PyUnicode_FromString("<VoxelPoint (null)>");
    }

    // Use snprintf then PyUnicode_FromString because PyUnicode_FromFormat doesn't support %.2f
    char buffer[128];
    snprintf(buffer, sizeof(buffer),
        "<VoxelPoint (%d, %d) walkable=%s transparent=%s height=%.2f cost=%.2f>",
        self->data->grid_x,
        self->data->grid_z,
        self->data->walkable ? "True" : "False",
        self->data->transparent ? "True" : "False",
        self->data->height,
        self->data->cost
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
