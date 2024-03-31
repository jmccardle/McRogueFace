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


int PyColor::init(PyColorObject* self, PyObject* args, PyObject* kwds)
{
    using namespace mcrfpydef;
    static const char* keywords[] = { "r", "g", "b", "a", nullptr };
    PyObject* leader;
    int r = -1, g = -1, b = -1, a = 255;
    if (!PyArg_ParseTupleAndKeywords, args, kwds, "O|iii", leader, &g, &b, &a)
    {
        PyErr_SetString(PyExc_TypeError, "mcrfpy.Color requires a color object, 3-tuple, 4-tuple, color name, or integer values within 0-255 (r, g, b, optionally a)");
        return -1;
    }

    // if the "r" arg is already a color, yoink that color value
    if (PyObject_IsInstance(leader, (PyObject*)&PyColorType))
    {
        self->data = ((PyColorObject*)leader)->data;
        return 0;
    }
    // else if the "r" arg is a 3-tuple, initialize to (r, g, b, 255)
    //     (if the "r" arg is a 4-tuple, initialize to (r, g, b, a))
    else if (PyTuple_Check(leader))
    {
        if (PyTuple_Size(leader) < 3 && PyTuple_Size(leader) > 4)
        {
            PyErr_SetString(PyExc_TypeError, "Invalid tuple length: mcrfpy.Color requires a color object, 3-tuple, 4-tuple, color name, or integer values within 0-255 (r, g, b, optionally a)");
            return -1;
        }
        r = PyLong_AsLong(PyTuple_GetItem(leader, 0));
        g = PyLong_AsLong(PyTuple_GetItem(leader, 1));
        b = PyLong_AsLong(PyTuple_GetItem(leader, 2));
        //a = 255; //default value

        if (PyTuple_Size(leader) == 4)
        {
            a = PyLong_AsLong(PyTuple_GetItem(leader, 3));
        }

        // value validation
        if (r < 0 || r > 255 || g < 0 || g > 255 || b < 0 || b > 255 || a < 0 || a > 255)
        {
            PyErr_SetString(PyExc_ValueError, "Color values must be between 0 and 255.");
            return -1;
        }
        self->data = sf::Color(r, g, b, a);
    }
    // else if the "r" arg is a string, initialize to {color lookup function value}
    else if (PyUnicode_Check(leader))
    {
        PyErr_SetString(Py_NotImplemented, "Color names aren't ready yet");
        return -1;
    }
    // else - 
    else if (!PyLong_Check(leader))
    {
        PyErr_SetString(PyExc_TypeError, "mcrfpy.Color requires a color object, 3-tuple, 4-tuple, color name, or integer values within 0-255 (r, g, b, optionally a)");
        return -1;
    }
    r = PyLong_AsLong(leader);
    //   assert r, g, b are present and ints in range (0, 255) - if not enough ints were provided to the args/kwds parsed by init, g and/or b will still hold -1.
    if (r < 0 || r > 255 || g < 0 || g > 255 || b < 0 || b > 255 || a < 0 || a > 255)
    {
        PyErr_SetString(PyExc_ValueError, "R, G, B values are required, A value is optional; Color values must be between 0 and 255.");
        return -1;
    }
    self->data = sf::Color(r, g, b, a);
    return 0;
}

PyObject* PyColor::pynew(PyTypeObject* type, PyObject* args, PyObject* kwds)
{
    return (PyObject*)type->tp_alloc(type, 0);
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
