#include "PyColor.h"

PyGetSetDef PyColor::getsetters[] = {
    {"r", (getter)PyColor::get_member, (setter)PyColor::set_member, "Red component",   (void*)0},
    {"g", (getter)PyColor::get_member, (setter)PyColor::set_member, "Green component", (void*)1},
    {"b", (getter)PyColor::get_member, (setter)PyColor::set_member, "Blue component",  (void*)2},
    {"a", (getter)PyColor::get_member, (setter)PyColor::set_member, "Alpha component", (void*)3},
    {NULL}
};

PyColor::PyColor(sf::Color target)
:data(target) {}

PyObject* PyColor::pyObject()
{
    PyObject* obj = PyType_GenericAlloc(&mcrfpydef::PyColorType, 0);
    Py_INCREF(obj);
    PyColorObject* self = (PyColorObject*)obj;
    self->data = data;
    return obj;
}

sf::Color PyColor::fromPy(PyObject* obj)
{
    PyColorObject* self = (PyColorObject*)obj;
    return self->data;
}

sf::Color PyColor::fromPy(PyColorObject* self)
{
    return self->data;
}

void PyColor::set(sf::Color color)
{
    data = color;
}

sf::Color PyColor::get()
{
    return data;
}

Py_hash_t PyColor::hash(PyObject* obj)
{
    auto self = (PyColorObject*)obj;
    Py_hash_t value = 0;
    value += self->data.r;
    value << 8; value += self->data.g; 
    value << 8; value += self->data.b; 
    value << 8; value += self->data.a;

    return value;
}

PyObject* PyColor::repr(PyObject* obj)
{
    PyColorObject* self = (PyColorObject*)obj;
    std::ostringstream ss;
    sf::Color c = self->data;
    ss << "<Color (" << int(c.r) << ", " << int(c.g) << ", " << int(c.b) << ", " << int(c.a) << ")>";

    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}


int PyColor::init(PyColorObject* self, PyObject* args, PyObject* kwds) {
    //using namespace mcrfpydef;
    static const char* keywords[] = { "r", "g", "b", "a", nullptr };
    PyObject* leader;
    int r = -1, g = -1, b = -1, a = 255;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|iii", const_cast<char**>(keywords), &leader, &g, &b, &a)) {
        PyErr_SetString(PyExc_TypeError, "mcrfpy.Color requires a 3-tuple, 4-tuple, color name, or integer values within 0-255 (r, g, b, optionally a)");
        return -1;
    }

    //std::cout << "Arg parsing succeeded. Values: " << r << " " << g << " " << b << " " << a <<std::endl;
    //std::cout << PyUnicode_AsUTF8(PyObject_Repr(leader)) << std::endl;
    // Tuple cases
    if (PyTuple_Check(leader)) {
        Py_ssize_t tupleSize = PyTuple_Size(leader);
        if (tupleSize < 3 || tupleSize > 4) {
            PyErr_SetString(PyExc_TypeError, "Invalid tuple length: mcrfpy.Color requires a 3-tuple, 4-tuple, color name, or integer values within 0-255 (r, g, b, optionally a)");
            return -1;
        }
        r = PyLong_AsLong(PyTuple_GetItem(leader, 0));
        g = PyLong_AsLong(PyTuple_GetItem(leader, 1));
        b = PyLong_AsLong(PyTuple_GetItem(leader, 2));
        if (tupleSize == 4) {
            a = PyLong_AsLong(PyTuple_GetItem(leader, 3));
        }
    }
    // Color name (not implemented yet)
    else if (PyUnicode_Check(leader)) {
        PyErr_SetString(PyExc_NotImplementedError, "Color names aren't ready yet");
        return -1;
    }
    // Check if the leader is actually an integer for the r value
    else if (PyLong_Check(leader)) {
        r = PyLong_AsLong(leader);
        // Additional validation not shown; g, b are required to be parsed
    } else {
        PyErr_SetString(PyExc_TypeError, "mcrfpy.Color requires a 3-tuple, 4-tuple, color name, or integer values within 0-255 (r, g, b, optionally a)");
        return -1;
    }

    // Validate color values
    if (r < 0 || r > 255 || g < 0 || g > 255 || b < 0 || b > 255 || a < 0 || a > 255) {
        PyErr_SetString(PyExc_ValueError, "Color values must be between 0 and 255.");
        return -1;
    }

    self->data = sf::Color(r, g, b, a);
    return 0;
}

PyObject* PyColor::pynew(PyTypeObject* type, PyObject* args, PyObject* kwds)
{
    auto obj = (PyObject*)type->tp_alloc(type, 0);
    //Py_INCREF(obj);
    return obj;
}

PyObject* PyColor::get_member(PyObject* obj, void* closure)
{
    // TODO
    return Py_None;
}

int PyColor::set_member(PyObject* obj, PyObject* value, void* closure)
{
    // TODO
    return 0;
}
