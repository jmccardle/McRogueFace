#pragma once
#include "Common.h"
#include "Python.h"

typedef struct {
    PyObject_HEAD
    sf::Vector2f data;
} PyVectorObject;

class PyVector
{
public:
    sf::Vector2f data;
    PyVector(sf::Vector2f);
    PyVector();
    PyObject* pyObject();
    static sf::Vector2f fromPy(PyObject*);
    static sf::Vector2f fromPy(PyVectorObject*);
    static PyObject* repr(PyObject*);
    static Py_hash_t hash(PyObject*);
    static int init(PyVectorObject*, PyObject*, PyObject*);
    static PyObject* pynew(PyTypeObject* type, PyObject* args=NULL, PyObject* kwds=NULL);
    static PyObject* get_member(PyObject*, void*);
    static int set_member(PyObject*, PyObject*, void*);
    
    static PyGetSetDef getsetters[];
};

namespace mcrfpydef {
    static PyTypeObject PyVectorType = {
        .tp_name = "mcrfpy.Vector",
        .tp_basicsize = sizeof(PyVectorObject),
        .tp_itemsize = 0,
        .tp_repr = PyVector::repr,
        .tp_hash = PyVector::hash,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("SFML Vector Object"),
        .tp_getset = PyVector::getsetters,
        .tp_init = (initproc)PyVector::init,
        .tp_new = PyVector::pynew,
    };
}
