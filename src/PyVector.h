#pragma once
#include "Common.h"
#include "Python.h"
#include "McRFPy_API.h"

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
    static PyVectorObject* from_arg(PyObject*);
    
    // Arithmetic operations
    static PyObject* add(PyObject*, PyObject*);
    static PyObject* subtract(PyObject*, PyObject*);
    static PyObject* multiply(PyObject*, PyObject*);
    static PyObject* divide(PyObject*, PyObject*);
    static PyObject* negative(PyObject*);
    static PyObject* absolute(PyObject*);
    static int bool_check(PyObject*);
    
    // Comparison operations
    static PyObject* richcompare(PyObject*, PyObject*, int);
    
    // Vector operations
    static PyObject* magnitude(PyVectorObject*, PyObject*);
    static PyObject* magnitude_squared(PyVectorObject*, PyObject*);
    static PyObject* normalize(PyVectorObject*, PyObject*);
    static PyObject* dot(PyVectorObject*, PyObject*);
    static PyObject* distance_to(PyVectorObject*, PyObject*);
    static PyObject* angle(PyVectorObject*, PyObject*);
    static PyObject* copy(PyVectorObject*, PyObject*);
    static PyObject* floor(PyVectorObject*, PyObject*);

    // Sequence protocol
    static Py_ssize_t sequence_length(PyObject*);
    static PyObject* sequence_item(PyObject*, Py_ssize_t);

    // Additional properties
    static PyObject* get_int(PyObject*, void*);
    
    static PyGetSetDef getsetters[];
    static PyMethodDef methods[];
};

namespace mcrfpydef {
    // Forward declare the PyNumberMethods and PySequenceMethods structures
    extern PyNumberMethods PyVector_as_number;
    extern PySequenceMethods PyVector_as_sequence;

    inline PyTypeObject PyVectorType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Vector",
        .tp_basicsize = sizeof(PyVectorObject),
        .tp_itemsize = 0,
        .tp_repr = PyVector::repr,
        .tp_as_number = &PyVector_as_number,
        .tp_as_sequence = &PyVector_as_sequence,
        .tp_hash = PyVector::hash,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("SFML Vector Object"),
        .tp_richcompare = PyVector::richcompare,
        .tp_methods = PyVector::methods,
        .tp_getset = PyVector::getsetters,
        .tp_init = (initproc)PyVector::init,
        .tp_new = PyVector::pynew,
    };
}
