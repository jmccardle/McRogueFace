#pragma once
#include "Python.h"
#include "McRFPy_Doc.h"
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
     MCRF_METHOD(Drawable, get_bounds, \
         MCRF_SIG("()", "tuple"), \
         MCRF_DESC("Get the bounding rectangle of this drawable element."), \
         MCRF_RETURNS("tuple: (x, y, width, height) representing the element's bounds") \
         MCRF_NOTE("The bounds are in screen coordinates and account for current position and size.") \
     )}, \
    {"move", (PyCFunction)UIDrawable_move<PyObjectType>, METH_VARARGS, \
     MCRF_METHOD(Drawable, move, \
         MCRF_SIG("(dx: float, dy: float)", "None"), \
         MCRF_DESC("Move the element by a relative offset."), \
         MCRF_ARGS_START \
         MCRF_ARG("dx", "Horizontal offset in pixels") \
         MCRF_ARG("dy", "Vertical offset in pixels") \
         MCRF_NOTE("This modifies the x and y position properties by the given amounts.") \
     )}, \
    {"resize", (PyCFunction)UIDrawable_resize<PyObjectType>, METH_VARARGS, \
     MCRF_METHOD(Drawable, resize, \
         MCRF_SIG("(width: float, height: float)", "None"), \
         MCRF_DESC("Resize the element to new dimensions."), \
         MCRF_ARGS_START \
         MCRF_ARG("width", "New width in pixels") \
         MCRF_ARG("height", "New height in pixels") \
         MCRF_NOTE("For Caption and Sprite, this may not change actual size if determined by content.") \
     )}

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
     MCRF_PROPERTY(visible, \
         "Whether the object is visible (bool). " \
         "Invisible objects are not rendered or clickable." \
     ), NULL}, \
    {"opacity", (getter)UIDrawable_get_opacity<PyObjectType>, (setter)UIDrawable_set_opacity<PyObjectType>, \
     MCRF_PROPERTY(opacity, \
         "Opacity level (0.0 = transparent, 1.0 = opaque). " \
         "Automatically clamped to valid range [0.0, 1.0]." \
     ), NULL}

// #122 & #102: Macro for parent/global_position properties (requires closure with type enum)
// These need the PyObjectsEnum value in closure, so they're added separately in each class
#define UIDRAWABLE_PARENT_GETSETTERS(type_enum) \
    {"parent", (getter)UIDrawable::get_parent, (setter)UIDrawable::set_parent, \
     MCRF_PROPERTY(parent, \
         "Parent drawable. " \
         "Get: Returns the parent Frame/Grid if nested, or None if at scene level. " \
         "Set: Assign a Frame/Grid to reparent, or None to remove from parent." \
     ), (void*)type_enum}, \
    {"global_position", (getter)UIDrawable::get_global_pos, NULL, \
     MCRF_PROPERTY(global_position, \
         "Global screen position (read-only). " \
         "Calculates absolute position by walking up the parent chain." \
     ), (void*)type_enum}, \
    {"bounds", (getter)UIDrawable::get_bounds_py, NULL, \
     MCRF_PROPERTY(bounds, \
         "Bounding rectangle (x, y, width, height) in local coordinates." \
     ), (void*)type_enum}, \
    {"global_bounds", (getter)UIDrawable::get_global_bounds_py, NULL, \
     MCRF_PROPERTY(global_bounds, \
         "Bounding rectangle (x, y, width, height) in screen coordinates." \
     ), (void*)type_enum}

// UIEntity specializations are defined in UIEntity.cpp after UIEntity class is complete
