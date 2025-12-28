#pragma once

#include "Common.h"
#include "Python.h"
#include "structmember.h"
#include "Animation.h"
#include <memory>

typedef struct {
    PyObject_HEAD
    std::shared_ptr<Animation> data;
} PyAnimationObject;

class PyAnimation {
public:
    static PyObject* create(PyTypeObject* type, PyObject* args, PyObject* kwds);
    static int init(PyAnimationObject* self, PyObject* args, PyObject* kwds);
    static void dealloc(PyAnimationObject* self);
    
    // Properties
    static PyObject* get_property(PyAnimationObject* self, void* closure);
    static PyObject* get_duration(PyAnimationObject* self, void* closure);
    static PyObject* get_elapsed(PyAnimationObject* self, void* closure);
    static PyObject* get_is_complete(PyAnimationObject* self, void* closure);
    static PyObject* get_is_delta(PyAnimationObject* self, void* closure);
    
    // Methods
    static PyObject* start(PyAnimationObject* self, PyObject* args, PyObject* kwds);
    static PyObject* update(PyAnimationObject* self, PyObject* args);
    static PyObject* get_current_value(PyAnimationObject* self, PyObject* args);
    static PyObject* complete(PyAnimationObject* self, PyObject* args);
    static PyObject* has_valid_target(PyAnimationObject* self, PyObject* args);
    
    static PyGetSetDef getsetters[];
    static PyMethodDef methods[];
};

namespace mcrfpydef {
    static PyTypeObject PyAnimationType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Animation",
        .tp_basicsize = sizeof(PyAnimationObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)PyAnimation::dealloc,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("Animation object for animating UI properties"),
        .tp_methods = PyAnimation::methods,
        .tp_getset = PyAnimation::getsetters,
        .tp_init = (initproc)PyAnimation::init,
        .tp_new = PyAnimation::create,
    };
}