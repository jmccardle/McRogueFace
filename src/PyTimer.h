#pragma once
#include "Common.h"
#include "Python.h"
#include <memory>
#include <string>

class PyTimerCallable;

typedef struct {
    PyObject_HEAD
    std::shared_ptr<PyTimerCallable> data;
    std::string name;
} PyTimerObject;

class PyTimer
{
public:
    // Python type methods
    static PyObject* repr(PyObject* self);
    static int init(PyTimerObject* self, PyObject* args, PyObject* kwds);
    static PyObject* pynew(PyTypeObject* type, PyObject* args=NULL, PyObject* kwds=NULL);
    static void dealloc(PyTimerObject* self);
    
    // Timer control methods
    static PyObject* pause(PyTimerObject* self, PyObject* Py_UNUSED(ignored));
    static PyObject* resume(PyTimerObject* self, PyObject* Py_UNUSED(ignored));
    static PyObject* cancel(PyTimerObject* self, PyObject* Py_UNUSED(ignored));
    static PyObject* restart(PyTimerObject* self, PyObject* Py_UNUSED(ignored));
    
    // Timer property getters
    static PyObject* get_interval(PyTimerObject* self, void* closure);
    static int set_interval(PyTimerObject* self, PyObject* value, void* closure);
    static PyObject* get_remaining(PyTimerObject* self, void* closure);
    static PyObject* get_paused(PyTimerObject* self, void* closure);
    static PyObject* get_active(PyTimerObject* self, void* closure);
    static PyObject* get_callback(PyTimerObject* self, void* closure);
    static int set_callback(PyTimerObject* self, PyObject* value, void* closure);
    
    static PyGetSetDef getsetters[];
    static PyMethodDef methods[];
};

namespace mcrfpydef {
    static PyTypeObject PyTimerType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Timer",
        .tp_basicsize = sizeof(PyTimerObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)PyTimer::dealloc,
        .tp_repr = PyTimer::repr,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("Timer object for scheduled callbacks"),
        .tp_methods = PyTimer::methods,
        .tp_getset = PyTimer::getsetters,
        .tp_init = (initproc)PyTimer::init,
        .tp_new = PyTimer::pynew,
    };
}