#pragma once
#include "Common.h"
#include "Python.h"

// Singleton mouse state object
typedef struct {
    PyObject_HEAD
    // Track state for properties without SFML getters
    bool cursor_visible;
    bool cursor_grabbed;
} PyMouseObject;

class PyMouse
{
public:
    // Python getters - query real-time mouse state via SFML
    static PyObject* get_x(PyObject* self, void* closure);
    static PyObject* get_y(PyObject* self, void* closure);
    static PyObject* get_pos(PyObject* self, void* closure);

    // Button state getters
    static PyObject* get_left(PyObject* self, void* closure);
    static PyObject* get_right(PyObject* self, void* closure);
    static PyObject* get_middle(PyObject* self, void* closure);

    // Cursor visibility/grab (read-write, tracked internally)
    static PyObject* get_visible(PyObject* self, void* closure);
    static int set_visible(PyObject* self, PyObject* value, void* closure);
    static PyObject* get_grabbed(PyObject* self, void* closure);
    static int set_grabbed(PyObject* self, PyObject* value, void* closure);

    static PyObject* repr(PyObject* obj);
    static int init(PyMouseObject* self, PyObject* args, PyObject* kwds);
    static PyGetSetDef getsetters[];
};

namespace mcrfpydef {
    static PyTypeObject PyMouseType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Mouse",
        .tp_basicsize = sizeof(PyMouseObject),
        .tp_itemsize = 0,
        .tp_repr = PyMouse::repr,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("Mouse state singleton for reading button/position state and controlling cursor visibility"),
        .tp_getset = PyMouse::getsetters,
        .tp_init = (initproc)PyMouse::init,
        .tp_new = PyType_GenericNew,
    };
}
