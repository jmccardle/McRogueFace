#pragma once
#include "Common.h"
#include "Python.h"
#include <string>
#include <memory>

// Forward declarations
class PyScene;

// Python object structure for Scene
typedef struct {
    PyObject_HEAD
    std::string name;
    std::shared_ptr<PyScene> scene;  // Reference to the C++ scene
    bool initialized;
} PySceneObject;

// C++ interface for Python Scene class
class PySceneClass
{
public:
    // Type methods
    static PyObject* __new__(PyTypeObject* type, PyObject* args, PyObject* kwds);
    static int __init__(PySceneObject* self, PyObject* args, PyObject* kwds);
    static void __dealloc(PyObject* self);
    static PyObject* __repr__(PySceneObject* self);
    
    // Scene methods
    static PyObject* activate(PySceneObject* self, PyObject* args);
    static PyObject* register_keyboard(PySceneObject* self, PyObject* args);
    
    // Properties
    static PyObject* get_name(PySceneObject* self, void* closure);
    static PyObject* get_active(PySceneObject* self, void* closure);
    
    // Lifecycle callbacks (called from C++)
    static void call_on_enter(PySceneObject* self);
    static void call_on_exit(PySceneObject* self);
    static void call_on_keypress(PySceneObject* self, std::string key, std::string action);
    static void call_update(PySceneObject* self, float dt);
    static void call_on_resize(PySceneObject* self, int width, int height);
    
    static PyGetSetDef getsetters[];
    static PyMethodDef methods[];
};

namespace mcrfpydef {
    static PyTypeObject PySceneType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Scene",
        .tp_basicsize = sizeof(PySceneObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)PySceneClass::__dealloc,
        .tp_repr = (reprfunc)PySceneClass::__repr__,
        .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,  // Allow subclassing
        .tp_doc = PyDoc_STR("Base class for object-oriented scenes"),
        .tp_methods = nullptr,  // Set in McRFPy_API.cpp
        .tp_getset = nullptr,   // Set in McRFPy_API.cpp
        .tp_init = (initproc)PySceneClass::__init__,
        .tp_new = PySceneClass::__new__,
    };
}