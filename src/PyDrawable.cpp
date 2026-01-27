#include "PyDrawable.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"
#include "PyPositionHelper.h"

// Click property getter
static PyObject* PyDrawable_get_click(PyDrawableObject* self, void* closure)
{
    if (!self->data->click_callable)
        Py_RETURN_NONE;

    PyObject* ptr = self->data->click_callable->borrow();
    if (ptr && ptr != Py_None) {
        Py_INCREF(ptr);  // Return new reference, not borrowed
        return ptr;
    }
    Py_RETURN_NONE;
}

// Click property setter
static int PyDrawable_set_click(PyDrawableObject* self, PyObject* value, void* closure)
{
    if (value == Py_None) {
        self->data->click_unregister();
    } else if (PyCallable_Check(value)) {
        self->data->click_register(value);
    } else {
        PyErr_SetString(PyExc_TypeError, "click must be callable or None");
        return -1;
    }
    return 0;
}

// Z-index property getter
static PyObject* PyDrawable_get_z_index(PyDrawableObject* self, void* closure)
{
    return PyLong_FromLong(self->data->z_index);
}

// Z-index property setter
static int PyDrawable_set_z_index(PyDrawableObject* self, PyObject* value, void* closure)
{
    if (!PyLong_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "z_index must be an integer");
        return -1;
    }

    int val = PyLong_AsLong(value);
    self->data->z_index = val;

    // Mark scene as needing resort
    self->data->notifyZIndexChanged();

    return 0;
}

// Visible property getter (new for #87)
static PyObject* PyDrawable_get_visible(PyDrawableObject* self, void* closure)
{
    return PyBool_FromLong(self->data->visible);
}

// Visible property setter (new for #87)
static int PyDrawable_set_visible(PyDrawableObject* self, PyObject* value, void* closure)
{
    if (!PyBool_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "visible must be a boolean");
        return -1;
    }

    self->data->visible = (value == Py_True);
    return 0;
}

// Opacity property getter (new for #88)
static PyObject* PyDrawable_get_opacity(PyDrawableObject* self, void* closure)
{
    return PyFloat_FromDouble(self->data->opacity);
}

// Opacity property setter (new for #88)
static int PyDrawable_set_opacity(PyDrawableObject* self, PyObject* value, void* closure)
{
    float val;
    if (PyFloat_Check(value)) {
        val = PyFloat_AsDouble(value);
    } else if (PyLong_Check(value)) {
        val = PyLong_AsLong(value);
    } else {
        PyErr_SetString(PyExc_TypeError, "opacity must be a number");
        return -1;
    }

    // Clamp to valid range
    if (val < 0.0f) val = 0.0f;
    if (val > 1.0f) val = 1.0f;

    self->data->opacity = val;
    return 0;
}

// GetSetDef array for properties
static PyGetSetDef PyDrawable_getsetters[] = {
    {"on_click", (getter)PyDrawable_get_click, (setter)PyDrawable_set_click,
     MCRF_PROPERTY(on_click,
         "Callable executed when object is clicked. "
         "Function receives (pos: Vector, button: str, action: str)."
     ), NULL},
    {"z_index", (getter)PyDrawable_get_z_index, (setter)PyDrawable_set_z_index,
     MCRF_PROPERTY(z_index,
         "Z-order for rendering (lower values rendered first). "
         "Automatically triggers scene resort when changed."
     ), NULL},
    {"visible", (getter)PyDrawable_get_visible, (setter)PyDrawable_set_visible,
     MCRF_PROPERTY(visible,
         "Whether the object is visible (bool). "
         "Invisible objects are not rendered or clickable."
     ), NULL},
    {"opacity", (getter)PyDrawable_get_opacity, (setter)PyDrawable_set_opacity,
     MCRF_PROPERTY(opacity,
         "Opacity level (0.0 = transparent, 1.0 = opaque). "
         "Automatically clamped to valid range [0.0, 1.0]."
     ), NULL},
    {NULL}  // Sentinel
};

// move method implementation (#98)
static PyObject* PyDrawable_move(PyDrawableObject* self, PyObject* args, PyObject* kwds)
{
    float dx, dy;
    if (!PyPosition_ParseFloat(args, kwds, &dx, &dy)) {
        return NULL;
    }

    self->data->move(dx, dy);
    Py_RETURN_NONE;
}

// resize method implementation (#98)
static PyObject* PyDrawable_resize(PyDrawableObject* self, PyObject* args, PyObject* kwds)
{
    float w, h;
    if (!PyPosition_ParseFloat(args, kwds, &w, &h)) {
        return NULL;
    }

    self->data->resize(w, h);
    Py_RETURN_NONE;
}

// Method definitions
static PyMethodDef PyDrawable_methods[] = {
    {"move", (PyCFunction)PyDrawable_move, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(Drawable, move,
         MCRF_SIG("(dx, dy) or (delta)", "None"),
         MCRF_DESC("Move the element by a relative offset."),
         MCRF_ARGS_START
         MCRF_ARG("dx", "Horizontal offset in pixels (or use delta)")
         MCRF_ARG("dy", "Vertical offset in pixels (or use delta)")
         MCRF_ARG("delta", "Offset as tuple, list, or Vector: (dx, dy)")
         MCRF_NOTE("This modifies the x and y position properties by the given amounts. "
                   "Accepts move(dx, dy), move((dx, dy)), move(Vector), or move(pos=(dx, dy)).")
     )},
    {"resize", (PyCFunction)PyDrawable_resize, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(Drawable, resize,
         MCRF_SIG("(width, height) or (size)", "None"),
         MCRF_DESC("Resize the element to new dimensions."),
         MCRF_ARGS_START
         MCRF_ARG("width", "New width in pixels (or use size)")
         MCRF_ARG("height", "New height in pixels (or use size)")
         MCRF_ARG("size", "Size as tuple, list, or Vector: (width, height)")
         MCRF_NOTE("For Caption and Sprite, this may not change actual size if determined by content. "
                   "Accepts resize(w, h), resize((w, h)), resize(Vector), or resize(pos=(w, h)).")
     )},
    {NULL}  // Sentinel
};

// Type initialization
static int PyDrawable_init(PyDrawableObject* self, PyObject* args, PyObject* kwds)
{
    PyErr_SetString(PyExc_TypeError, "Drawable is an abstract base class and cannot be instantiated directly");
    return -1;
}

namespace mcrfpydef {
    PyTypeObject PyDrawableType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Drawable",
        .tp_basicsize = sizeof(PyDrawableObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)[](PyObject* self) {
            PyDrawableObject* obj = (PyDrawableObject*)self;
            obj->data.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
        .tp_doc = PyDoc_STR("Base class for all drawable UI elements"),
        .tp_methods = PyDrawable_methods,
        .tp_getset = PyDrawable_getsetters,
        .tp_init = (initproc)PyDrawable_init,
        .tp_new = PyType_GenericNew,
    };
}
