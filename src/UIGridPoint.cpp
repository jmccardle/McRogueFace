#include "UIGridPoint.h"

UIGridPoint::UIGridPoint()
: color(1.0f, 1.0f, 1.0f), color_overlay(0.0f, 0.0f, 0.0f), walkable(false), transparent(false),
 tilesprite(-1), tile_overlay(-1), uisprite(-1)
{}

// Utility function to convert sf::Color to PyObject*
PyObject* sfColor_to_PyObject(sf::Color color) {
    return Py_BuildValue("(iiii)", color.r, color.g, color.b, color.a);
}

// Utility function to convert PyObject* to sf::Color
sf::Color PyObject_to_sfColor(PyObject* obj) {
    int r, g, b, a = 255; // Default alpha to fully opaque if not specified
    if (!PyArg_ParseTuple(obj, "iii|i", &r, &g, &b, &a)) {
        return sf::Color(); // Return default color on parse error
    }
    return sf::Color(r, g, b, a);
}

PyObject* UIGridPoint::get_color(PyUIGridPointObject* self, void* closure) {
    if (reinterpret_cast<long>(closure) == 0) { // color
        return sfColor_to_PyObject(self->data->color);
    } else { // color_overlay
        return sfColor_to_PyObject(self->data->color_overlay);
    }
}

int UIGridPoint::set_color(PyUIGridPointObject* self, PyObject* value, void* closure) {
    sf::Color color = PyObject_to_sfColor(value);
    if (reinterpret_cast<long>(closure) == 0) { // color
        self->data->color = color;
    } else { // color_overlay
        self->data->color_overlay = color;
    }
    return 0;
}

PyObject* UIGridPoint::get_bool_member(PyUIGridPointObject* self, void* closure) {
    if (reinterpret_cast<long>(closure) == 0) { // walkable
        return PyBool_FromLong(self->data->walkable);
    } else { // transparent
        return PyBool_FromLong(self->data->transparent);
    }
}

int UIGridPoint::set_bool_member(PyUIGridPointObject* self, PyObject* value, void* closure) {
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

PyObject* UIGridPoint::get_int_member(PyUIGridPointObject* self, void* closure) {
    switch(reinterpret_cast<long>(closure)) {
        case 0: return PyLong_FromLong(self->data->tilesprite);
        case 1: return PyLong_FromLong(self->data->tile_overlay);
        case 2: return PyLong_FromLong(self->data->uisprite);
        default: PyErr_SetString(PyExc_RuntimeError, "Invalid closure"); return nullptr;
    }
}

int UIGridPoint::set_int_member(PyUIGridPointObject* self, PyObject* value, void* closure) {
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

PyGetSetDef UIGridPoint::getsetters[] = {
    {"color", (getter)UIGridPoint::get_color, (setter)UIGridPoint::set_color, "GridPoint color", (void*)0},
    {"color_overlay", (getter)UIGridPoint::get_color, (setter)UIGridPoint::set_color, "GridPoint color overlay", (void*)1},
    {"walkable", (getter)UIGridPoint::get_bool_member, (setter)UIGridPoint::set_bool_member, "Is the GridPoint walkable", (void*)0},
    {"transparent", (getter)UIGridPoint::get_bool_member, (setter)UIGridPoint::set_bool_member, "Is the GridPoint transparent", (void*)1},
    {"tilesprite", (getter)UIGridPoint::get_int_member, (setter)UIGridPoint::set_int_member, "Tile sprite index", (void*)0},
    {"tile_overlay", (getter)UIGridPoint::get_int_member, (setter)UIGridPoint::set_int_member, "Tile overlay sprite index", (void*)1},
    {"uisprite", (getter)UIGridPoint::get_int_member, (setter)UIGridPoint::set_int_member, "UI sprite index", (void*)2},
    {NULL}  /* Sentinel */
};

PyObject* UIGridPointState::get_bool_member(PyUIGridPointStateObject* self, void* closure) {
    if (reinterpret_cast<long>(closure) == 0) { // visible
        return PyBool_FromLong(self->data->visible);
    } else { // discovered
        return PyBool_FromLong(self->data->discovered);
    }
}

int UIGridPointState::set_bool_member(PyUIGridPointStateObject* self, PyObject* value, void* closure) {
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

PyGetSetDef UIGridPointState::getsetters[] = {
    {"visible", (getter)UIGridPointState::get_bool_member, (setter)UIGridPointState::set_bool_member, "Is the GridPointState visible", (void*)0},
    {"discovered", (getter)UIGridPointState::get_bool_member, (setter)UIGridPointState::set_bool_member, "Has the GridPointState been discovered", (void*)1},
    {NULL}  /* Sentinel */
};

