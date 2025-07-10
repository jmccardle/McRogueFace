#pragma once
#include "UIEntity.h"
#include "UIBase.h"

// UIEntity-specific property implementations
// These delegate to the wrapped sprite member

// Visible property
static PyObject* UIEntity_get_visible(PyUIEntityObject* self, void* closure)
{
    return PyBool_FromLong(self->data->sprite.visible);
}

static int UIEntity_set_visible(PyUIEntityObject* self, PyObject* value, void* closure)
{
    if (!PyBool_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "visible must be a boolean");
        return -1;
    }
    self->data->sprite.visible = PyObject_IsTrue(value);
    return 0;
}

// Opacity property
static PyObject* UIEntity_get_opacity(PyUIEntityObject* self, void* closure)
{
    return PyFloat_FromDouble(self->data->sprite.opacity);
}

static int UIEntity_set_opacity(PyUIEntityObject* self, PyObject* value, void* closure)
{
    float opacity;
    if (PyFloat_Check(value)) {
        opacity = PyFloat_AsDouble(value);
    } else if (PyLong_Check(value)) {
        opacity = PyLong_AsDouble(value);
    } else {
        PyErr_SetString(PyExc_TypeError, "opacity must be a number");
        return -1;
    }
    
    // Clamp to valid range
    if (opacity < 0.0f) opacity = 0.0f;
    if (opacity > 1.0f) opacity = 1.0f;
    
    self->data->sprite.opacity = opacity;
    return 0;
}

// Name property - delegate to sprite
static PyObject* UIEntity_get_name(PyUIEntityObject* self, void* closure)
{
    return PyUnicode_FromString(self->data->sprite.name.c_str());
}

static int UIEntity_set_name(PyUIEntityObject* self, PyObject* value, void* closure)
{
    if (value == NULL || value == Py_None) {
        self->data->sprite.name = "";
        return 0;
    }
    
    if (!PyUnicode_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "name must be a string");
        return -1;
    }
    
    const char* name_str = PyUnicode_AsUTF8(value);
    if (!name_str) {
        return -1;
    }
    
    self->data->sprite.name = name_str;
    return 0;
}