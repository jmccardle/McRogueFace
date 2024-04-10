#pragma once
#include "Common.h"
#include "Python.h"
#include "structmember.h"
#include "IndexTexture.h"
#include "Resources.h"
#include <list>

#include "PyCallable.h"
#include "PyTexture.h"
#include "PyColor.h"
#include "PyVector.h"
#include "PyFont.h"

// UIGridPoint - revised grid data for each point
class UIGridPoint
{
public:
    sf::Color color, color_overlay;
    bool walkable, transparent;
    int tilesprite, tile_overlay, uisprite;
    UIGridPoint();
};

// UIGridPointState - entity-specific info for each cell
class UIGridPointState
{
public:
    bool visible, discovered;
};

class UIGrid;

typedef struct {
    PyObject_HEAD
    UIGridPoint* data;
    std::shared_ptr<UIGrid> grid;
} PyUIGridPointObject;

typedef struct {
    PyObject_HEAD
    UIGridPointState* data;
    std::shared_ptr<UIGrid> grid;
    std::shared_ptr<UIEntity> entity;
} PyUIGridPointStateObject;

namespace mcrfpydef {
// TODO: question: are sfColor_to_PyObject and PyObject_to_sfColor duplicitive? How does UIFrame get/set colors?

//TODO: add this method to class scope; move implementation to .cpp file; reconsider for moving to "UIBase.h/.cpp"
// Utility function to convert sf::Color to PyObject*
static PyObject* sfColor_to_PyObject(sf::Color color) {
    return Py_BuildValue("(iiii)", color.r, color.g, color.b, color.a);
}

//TODO: add this method to class scope; move implementation to .cpp file; reconsider for moving to "UIBase.h/.cpp"
// Utility function to convert PyObject* to sf::Color
static sf::Color PyObject_to_sfColor(PyObject* obj) {
    int r, g, b, a = 255; // Default alpha to fully opaque if not specified
    if (!PyArg_ParseTuple(obj, "iii|i", &r, &g, &b, &a)) {
        return sf::Color(); // Return default color on parse error
    }
    return sf::Color(r, g, b, a);
}

//TODO: add this method to class scope; move implementation to .cpp file
static PyObject* PyUIGridPoint_get_color(PyUIGridPointObject* self, void* closure) {
    if (reinterpret_cast<long>(closure) == 0) { // color
        return sfColor_to_PyObject(self->data->color);
    } else { // color_overlay
        return sfColor_to_PyObject(self->data->color_overlay);
    }
}

//TODO: add this method to class scope; move implementation to .cpp file
static int PyUIGridPoint_set_color(PyUIGridPointObject* self, PyObject* value, void* closure) {
    sf::Color color = PyObject_to_sfColor(value);
    if (reinterpret_cast<long>(closure) == 0) { // color
        self->data->color = color;
    } else { // color_overlay
        self->data->color_overlay = color;
    }
    return 0;
}

//TODO: add this method to class scope; move implementation to .cpp file
static PyObject* PyUIGridPoint_get_bool_member(PyUIGridPointObject* self, void* closure) {
    if (reinterpret_cast<long>(closure) == 0) { // walkable
        return PyBool_FromLong(self->data->walkable);
    } else { // transparent
        return PyBool_FromLong(self->data->transparent);
    }
}

//TODO: add this method to class scope; move implementation to .cpp file
static int PyUIGridPoint_set_bool_member(PyUIGridPointObject* self, PyObject* value, void* closure) {
    if (value == Py_True) {
        if (reinterpret_cast<long>(closure) == 0) { // walkable
            self->data->walkable = true;
        } else { // transparent
            self->data->transparent = true;
        }
    } else if (value == Py_False) {
        if (reinterpret_cast<long>(closure) == 0) { // walkable
            self->data->walkable = false;
        } else { // transparent
            self->data->transparent = false;
        }
    } else {
        PyErr_SetString(PyExc_ValueError, "Expected a boolean value");
        return -1;
    }
    return 0;
}

//TODO: add this method to class scope; move implementation to .cpp file
static PyObject* PyUIGridPoint_get_int_member(PyUIGridPointObject* self, void* closure) {
    switch(reinterpret_cast<long>(closure)) {
        case 0: return PyLong_FromLong(self->data->tilesprite);
        case 1: return PyLong_FromLong(self->data->tile_overlay);
        case 2: return PyLong_FromLong(self->data->uisprite);
        default: PyErr_SetString(PyExc_RuntimeError, "Invalid closure"); return nullptr;
    }
}

//TODO: add this method to class scope; move implementation to .cpp file
static int PyUIGridPoint_set_int_member(PyUIGridPointObject* self, PyObject* value, void* closure) {
    long val = PyLong_AsLong(value);
    if (PyErr_Occurred()) return -1;

    switch(reinterpret_cast<long>(closure)) {
        case 0: self->data->tilesprite = val; break;
        case 1: self->data->tile_overlay = val; break;
        case 2: self->data->uisprite = val; break;
        default: PyErr_SetString(PyExc_RuntimeError, "Invalid closure"); return -1;
    }
    return 0;
}

//TODO: add this static array to class scope; move implementation to .cpp file
static PyGetSetDef PyUIGridPoint_getsetters[] = {
    {"color", (getter)PyUIGridPoint_get_color, (setter)PyUIGridPoint_set_color, "GridPoint color", (void*)0},
    {"color_overlay", (getter)PyUIGridPoint_get_color, (setter)PyUIGridPoint_set_color, "GridPoint color overlay", (void*)1},
    {"walkable", (getter)PyUIGridPoint_get_bool_member, (setter)PyUIGridPoint_set_bool_member, "Is the GridPoint walkable", (void*)0},
    {"transparent", (getter)PyUIGridPoint_get_bool_member, (setter)PyUIGridPoint_set_bool_member, "Is the GridPoint transparent", (void*)1},
    {"tilesprite", (getter)PyUIGridPoint_get_int_member, (setter)PyUIGridPoint_set_int_member, "Tile sprite index", (void*)0},
    {"tile_overlay", (getter)PyUIGridPoint_get_int_member, (setter)PyUIGridPoint_set_int_member, "Tile overlay sprite index", (void*)1},
    {"uisprite", (getter)PyUIGridPoint_get_int_member, (setter)PyUIGridPoint_set_int_member, "UI sprite index", (void*)2},
    {NULL}  /* Sentinel */
};

static PyTypeObject PyUIGridPointType = {
    //PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "mcrfpy.GridPoint",
    .tp_basicsize = sizeof(PyUIGridPointObject),
    .tp_itemsize = 0,
    // Methods omitted for brevity
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_doc = "UIGridPoint objects",
    .tp_getset = PyUIGridPoint_getsetters,
    //.tp_init = (initproc)PyUIGridPoint_init, // TODO Define the init function
    .tp_new = PyType_GenericNew,
};

//TODO: add this method to class scope; move implementation to .cpp file
static PyObject* PyUIGridPointState_get_bool_member(PyUIGridPointStateObject* self, void* closure) {
    if (reinterpret_cast<long>(closure) == 0) { // visible
        return PyBool_FromLong(self->data->visible);
    } else { // discovered
        return PyBool_FromLong(self->data->discovered);
    }
}

//TODO: add this method to class scope; move implementation to .cpp file
static int PyUIGridPointState_set_bool_member(PyUIGridPointStateObject* self, PyObject* value, void* closure) {
    if (!PyBool_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "Value must be a boolean");
        return -1;
    }

    int truthValue = PyObject_IsTrue(value);
    if (truthValue < 0) {
        return -1; // PyObject_IsTrue returns -1 on error
    }

    if (reinterpret_cast<long>(closure) == 0) { // visible
        self->data->visible = truthValue;
    } else { // discovered
        self->data->discovered = truthValue;
    }

    return 0;
}

//TODO: add this static array to class scope; move implementation to .cpp file
static PyGetSetDef PyUIGridPointState_getsetters[] = {
    {"visible", (getter)PyUIGridPointState_get_bool_member, (setter)PyUIGridPointState_set_bool_member, "Is the GridPointState visible", (void*)0},
    {"discovered", (getter)PyUIGridPointState_get_bool_member, (setter)PyUIGridPointState_set_bool_member, "Has the GridPointState been discovered", (void*)1},
    {NULL}  /* Sentinel */
};

static PyTypeObject PyUIGridPointStateType = {
    //PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "mcrfpy.GridPointState",
    .tp_basicsize = sizeof(PyUIGridPointStateObject),
    .tp_itemsize = 0,
    // Methods omitted for brevity
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_doc = "UIGridPointState objects", // TODO: Add PyUIGridPointState tp_init
    .tp_getset = PyUIGridPointState_getsetters,
    .tp_new = PyType_GenericNew,
};

}
