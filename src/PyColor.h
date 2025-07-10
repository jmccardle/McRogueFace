#pragma once
#include "Common.h"
#include "Python.h"

class PyColor;
class UIDrawable; // forward declare for pointer

typedef struct {
    PyObject_HEAD
    sf::Color data;
} PyColorObject;

class PyColor
{
private:
public:
    sf::Color data;
    PyColor(sf::Color);
    void set(sf::Color);
    sf::Color get();
    PyObject* pyObject();
    static sf::Color fromPy(PyObject*);
    static sf::Color fromPy(PyColorObject*);
    static PyObject* repr(PyObject*);
    static Py_hash_t hash(PyObject*);
    static int init(PyColorObject*, PyObject*, PyObject*);
    static PyObject* pynew(PyTypeObject* type, PyObject* args=NULL, PyObject* kwds=NULL);
    static PyObject* get_member(PyObject*, void*);
    static int set_member(PyObject*, PyObject*, void*);
    
    // Color helper methods
    static PyObject* from_hex(PyObject* cls, PyObject* args);
    static PyObject* to_hex(PyColorObject* self, PyObject* Py_UNUSED(ignored));
    static PyObject* lerp(PyColorObject* self, PyObject* args);
    
    static PyGetSetDef getsetters[];
    static PyMethodDef methods[];
    static PyColorObject* from_arg(PyObject*);
};

namespace mcrfpydef {
    static PyTypeObject PyColorType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Color",
        .tp_basicsize = sizeof(PyColorObject),
        .tp_itemsize = 0,
        .tp_repr = PyColor::repr,
        .tp_hash = PyColor::hash,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("SFML Color Object"),
        .tp_methods = PyColor::methods,
        .tp_getset = PyColor::getsetters,
        .tp_init = (initproc)PyColor::init,
        .tp_new = PyColor::pynew,
    };
}
