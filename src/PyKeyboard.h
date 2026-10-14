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
    // Python getters - report the modifiers of the key event being handled (#497)
    static PyObject* get_shift(PyObject* self, void* closure);
    static PyObject* get_ctrl(PyObject* self, void* closure);
    static PyObject* get_alt(PyObject* self, void* closure);
    static PyObject* get_system(PyObject* self, void* closure);

    static PyObject* repr(PyObject* obj);
    static PyGetSetDef getsetters[];
};

namespace mcrfpydef {
    inline PyTypeObject PyKeyboardType = {
        .ob_base = PyVarObject_HEAD_INIT(NULL, 0)
        .tp_name = "mcrfpy.Keyboard",
        .tp_basicsize = sizeof(PyKeyboardObject),
        .tp_itemsize = 0,
        .tp_repr = PyKeyboard::repr,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("Keyboard modifier state singleton: the modifiers (shift, ctrl, alt, system) carried by the key event being handled; they persist until the next key event."),
        .tp_getset = PyKeyboard::getsetters,
        .tp_new = PyType_GenericNew,
    };
}
