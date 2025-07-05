#include "PyVector.h"
#include "PyObjectUtils.h"

PyGetSetDef PyVector::getsetters[] = {
    {"x", (getter)PyVector::get_member, (setter)PyVector::set_member, "X/horizontal component",   (void*)0},
    {"y", (getter)PyVector::get_member, (setter)PyVector::set_member, "Y/vertical component",     (void*)1},
    {NULL}
};

PyVector::PyVector(sf::Vector2f target)
:data(target) {}

PyObject* PyVector::pyObject()
{
    PyTypeObject* type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    if (!type) return nullptr;
    
    PyVectorObject* obj = (PyVectorObject*)type->tp_alloc(type, 0);
    Py_DECREF(type);
    
    if (obj) {
        obj->data = data;
    }
    return (PyObject*)obj;
}

sf::Vector2f PyVector::fromPy(PyObject* obj)
{
    PyVectorObject* self = (PyVectorObject*)obj;
    return self->data;
}

sf::Vector2f PyVector::fromPy(PyVectorObject* self)
{
    return self->data;
}

Py_hash_t PyVector::hash(PyObject* obj)
{
    auto self = (PyVectorObject*)obj;
    Py_hash_t value = 0;
    value += self->data.x;
    value << 8; value += self->data.y; 

    return value;
}

PyObject* PyVector::repr(PyObject* obj)
{
    PyVectorObject* self = (PyVectorObject*)obj;
    std::ostringstream ss;
    sf::Vector2f v = self->data;
    ss << "<Vector (" << v.x << ", " << v.y << ")>";

    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}


int PyVector::init(PyVectorObject* self, PyObject* args, PyObject* kwds)
{
    using namespace mcrfpydef;
    static const char* keywords[] = { "x", "y", nullptr };
    PyObject* leader = NULL;
    float x=0, y=0;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|Of", const_cast<char**>(keywords), &leader, &y))
    {
        //PyErr_SetString(PyExc_TypeError, "mcrfpy.Vector requires a 2-tuple or two numeric values");
        return -1;
    }
    if (leader == NULL || leader == Py_None)
    {
        self->data = sf::Vector2f();
        return 0;
    } 

    if (PyTuple_Check(leader))
    {
        if (PyTuple_Size(leader) != 2)
        {
            PyErr_SetString(PyExc_TypeError, "Invalid tuple length: mcrfpy.Vector requires a 2-tuple");
            return -1;
        }
        x = PyFloat_AsDouble(PyTuple_GetItem(leader, 0));
        y = PyFloat_AsDouble(PyTuple_GetItem(leader, 1));

        self->data = sf::Vector2f(x, y);
        return 0;
    }
    // else - 
    else if (!PyFloat_Check(leader) && !(PyLong_Check(leader)))
    {
        PyErr_SetString(PyExc_TypeError, "mcrfpy.Vector requires a 2-tuple or two numeric values");
        return -1;
    }
    if (PyFloat_Check(leader)) x = PyFloat_AsDouble(leader);
    else x = PyLong_AsDouble(leader);
    self->data = sf::Vector2f(x, y);
    return 0;
}

PyObject* PyVector::pynew(PyTypeObject* type, PyObject* args, PyObject* kwds)
{
    return (PyObject*)type->tp_alloc(type, 0);
}

PyObject* PyVector::get_member(PyObject* obj, void* closure)
{
    PyVectorObject* self = (PyVectorObject*)obj;
    if (reinterpret_cast<long>(closure) == 0) {
        // x
        return PyFloat_FromDouble(self->data.x);
    } else {
        // y
        return PyFloat_FromDouble(self->data.y);
    }
}

int PyVector::set_member(PyObject* obj, PyObject* value, void* closure)
{
    PyVectorObject* self = (PyVectorObject*)obj;
    float val;
    
    if (PyFloat_Check(value)) {
        val = PyFloat_AsDouble(value);
    } else if (PyLong_Check(value)) {
        val = PyLong_AsDouble(value);
    } else {
        PyErr_SetString(PyExc_TypeError, "Vector members must be numeric");
        return -1;
    }
    
    if (reinterpret_cast<long>(closure) == 0) {
        // x
        self->data.x = val;
    } else {
        // y
        self->data.y = val;
    }
    return 0;
}

PyVectorObject* PyVector::from_arg(PyObject* args)
{
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    if (PyObject_IsInstance(args, (PyObject*)type)) return (PyVectorObject*)args;
    
    auto obj = (PyVectorObject*)type->tp_alloc(type, 0);
    
    // Handle different input types
    if (PyTuple_Check(args)) {
        // It's already a tuple, pass it directly to init
        int err = init(obj, args, NULL);
        if (err) {
            Py_DECREF(obj);
            return NULL;
        }
    } else {
        // Wrap single argument in a tuple for init
        PyObject* tuple = PyTuple_Pack(1, args);
        if (!tuple) {
            Py_DECREF(obj);
            return NULL;
        }
        int err = init(obj, tuple, NULL);
        Py_DECREF(tuple);
        if (err) {
            Py_DECREF(obj);
            return NULL;
        }
    }
    
    return obj;
}
