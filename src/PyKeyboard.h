#pragma once
#include "Common.h"
#include "Python.h"

// Singleton keyboard state object
typedef struct {
    PyObject_HEAD
} PyKeyboardObject;

class PyKeyboard
{
public:
    // Python getters - query real-time keyboard state via SFML
    static PyObject* get_shift(PyObject* self, void* closure);
    static PyObject* get_ctrl(PyObject* self, void* closure);
    static PyObject* get_alt(PyObject* self, void* closure);
    static PyObject* get_system(PyObject* self, void* closure);

    static PyObject* repr(PyObject* obj);
    static PyGetSetDef getsetters[];
};

namespace mcrfpydef {
    inline PyTypeObject PyKeyboardType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Keyboard",
        .tp_basicsize = sizeof(PyKeyboardObject),
        .tp_itemsize = 0,
        .tp_repr = PyKeyboard::repr,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("Keyboard state singleton for checking modifier keys"),
        .tp_getset = PyKeyboard::getsetters,
        .tp_new = PyType_GenericNew,
    };
}
