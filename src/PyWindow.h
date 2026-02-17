#pragma once
#include "Common.h"
#include "Python.h"

// Forward declarations
class GameEngine;

// Python object structure for Window singleton
typedef struct {
    PyObject_HEAD
    // No data - Window is a singleton that accesses GameEngine
} PyWindowObject;

// C++ interface for the Window singleton
class PyWindow
{
public:
    // Static methods for Python type
    static PyObject* get(PyObject* cls, PyObject* args);
    static PyObject* repr(PyWindowObject* self);
    
    // Getters and setters for window properties
    static PyObject* get_resolution(PyWindowObject* self, void* closure);
    static int set_resolution(PyWindowObject* self, PyObject* value, void* closure);
    static PyObject* get_fullscreen(PyWindowObject* self, void* closure);
    static int set_fullscreen(PyWindowObject* self, PyObject* value, void* closure);
    static PyObject* get_vsync(PyWindowObject* self, void* closure);
    static int set_vsync(PyWindowObject* self, PyObject* value, void* closure);
    static PyObject* get_title(PyWindowObject* self, void* closure);
    static int set_title(PyWindowObject* self, PyObject* value, void* closure);
    static PyObject* get_visible(PyWindowObject* self, void* closure);
    static int set_visible(PyWindowObject* self, PyObject* value, void* closure);
    static PyObject* get_framerate_limit(PyWindowObject* self, void* closure);
    static int set_framerate_limit(PyWindowObject* self, PyObject* value, void* closure);
    static PyObject* get_game_resolution(PyWindowObject* self, void* closure);
    static int set_game_resolution(PyWindowObject* self, PyObject* value, void* closure);
    static PyObject* get_scaling_mode(PyWindowObject* self, void* closure);
    static int set_scaling_mode(PyWindowObject* self, PyObject* value, void* closure);
    
    // Methods
    static PyObject* center(PyWindowObject* self, PyObject* args);
    static PyObject* screenshot(PyWindowObject* self, PyObject* args, PyObject* kwds);
    
    static PyGetSetDef getsetters[];
    static PyMethodDef methods[];
    
};

namespace mcrfpydef {
    inline PyTypeObject PyWindowType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Window",
        .tp_basicsize = sizeof(PyWindowObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)[](PyObject* self) {
            // Don't delete the singleton instance
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)PyWindow::repr,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("Window singleton for accessing and modifying the game window properties"),
        .tp_methods = nullptr,  // Set in McRFPy_API.cpp after definition
        .tp_getset = nullptr,   // Set in McRFPy_API.cpp after definition
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject* {
            PyErr_SetString(PyExc_TypeError, "Cannot instantiate Window. Use Window.get() to access the singleton.");
            return NULL;
        }
    };
}