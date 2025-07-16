#pragma once
#include "Python.h"
#include <memory>

class UIEntity;
typedef struct {
    PyObject_HEAD
    std::shared_ptr<UIEntity> data;
    PyObject* weakreflist;  // Weak reference support
} PyUIEntityObject;

class UIFrame;
typedef struct {
    PyObject_HEAD
    std::shared_ptr<UIFrame> data;
    PyObject* weakreflist;  // Weak reference support
} PyUIFrameObject;

class UICaption;
typedef struct {
    PyObject_HEAD
    std::shared_ptr<UICaption> data;
    PyObject* font;
    PyObject* weakreflist;  // Weak reference support
} PyUICaptionObject;

class UIGrid;
typedef struct {
    PyObject_HEAD
    std::shared_ptr<UIGrid> data;
    PyObject* weakreflist;  // Weak reference support
} PyUIGridObject;

class UISprite;
typedef struct {
    PyObject_HEAD
    std::shared_ptr<UISprite> data;
    PyObject* weakreflist;  // Weak reference support
} PyUISpriteObject;

// Common Python method implementations for UIDrawable-derived classes
// These template functions provide shared functionality for Python bindings

// get_bounds method implementation (#89)
template<typename T>
static PyObject* UIDrawable_get_bounds(T* self, PyObject* Py_UNUSED(args))
{
    auto bounds = self->data->get_bounds();
    return Py_BuildValue("(ffff)", bounds.left, bounds.top, bounds.width, bounds.height);
}

// move method implementation (#98)
template<typename T>
static PyObject* UIDrawable_move(T* self, PyObject* args)
{
    float dx, dy;
    if (!PyArg_ParseTuple(args, "ff", &dx, &dy)) {
        return NULL;
    }
    
    self->data->move(dx, dy);
    Py_RETURN_NONE;
}

// resize method implementation (#98)
template<typename T>
static PyObject* UIDrawable_resize(T* self, PyObject* args)
{
    float w, h;
    if (!PyArg_ParseTuple(args, "ff", &w, &h)) {
        return NULL;
    }
    
    self->data->resize(w, h);
    Py_RETURN_NONE;
}

// Macro to add common UIDrawable methods to a method array
#define UIDRAWABLE_METHODS \
    {"get_bounds", (PyCFunction)UIDrawable_get_bounds<PyObjectType>, METH_NOARGS, \
     "Get bounding box as (x, y, width, height)"}, \
    {"move", (PyCFunction)UIDrawable_move<PyObjectType>, METH_VARARGS, \
     "Move by relative offset (dx, dy)"}, \
    {"resize", (PyCFunction)UIDrawable_resize<PyObjectType>, METH_VARARGS, \
     "Resize to new dimensions (width, height)"}

// Property getters/setters for visible and opacity
template<typename T>
static PyObject* UIDrawable_get_visible(T* self, void* closure)
{
    return PyBool_FromLong(self->data->visible);
}

template<typename T>
static int UIDrawable_set_visible(T* self, PyObject* value, void* closure)
{
    if (!PyBool_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "visible must be a boolean");
        return -1;
    }
    self->data->visible = PyObject_IsTrue(value);
    return 0;
}

template<typename T>
static PyObject* UIDrawable_get_opacity(T* self, void* closure)
{
    return PyFloat_FromDouble(self->data->opacity);
}

template<typename T>
static int UIDrawable_set_opacity(T* self, PyObject* value, void* closure)
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
    
    self->data->opacity = opacity;
    return 0;
}

// Macro to add common UIDrawable properties to a getsetters array
#define UIDRAWABLE_GETSETTERS \
    {"visible", (getter)UIDrawable_get_visible<PyObjectType>, (setter)UIDrawable_set_visible<PyObjectType>, \
     "Visibility flag", NULL}, \
    {"opacity", (getter)UIDrawable_get_opacity<PyObjectType>, (setter)UIDrawable_set_opacity<PyObjectType>, \
     "Opacity (0.0 = transparent, 1.0 = opaque)", NULL}

// UIEntity specializations are defined in UIEntity.cpp after UIEntity class is complete
