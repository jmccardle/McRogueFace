#include "PyColor.h"
#include "McRFPy_API.h"
#include "PyObjectUtils.h"
#include "PyRAII.h"
#include <string>
#include <cstdio>

PyGetSetDef PyColor::getsetters[] = {
    {"r", (getter)PyColor::get_member, (setter)PyColor::set_member, "Red component",   (void*)0},
    {"g", (getter)PyColor::get_member, (setter)PyColor::set_member, "Green component", (void*)1},
    {"b", (getter)PyColor::get_member, (setter)PyColor::set_member, "Blue component",  (void*)2},
    {"a", (getter)PyColor::get_member, (setter)PyColor::set_member, "Alpha component", (void*)3},
    {NULL}
};

PyMethodDef PyColor::methods[] = {
    {"from_hex", (PyCFunction)PyColor::from_hex, METH_VARARGS | METH_CLASS, "Create Color from hex string (e.g., '#FF0000' or 'FF0000')"},
    {"to_hex", (PyCFunction)PyColor::to_hex, METH_NOARGS, "Convert Color to hex string"},
    {"lerp", (PyCFunction)PyColor::lerp, METH_VARARGS, "Linearly interpolate between this color and another"},
    {NULL}
};

PyColor::PyColor(sf::Color target)
:data(target) {}

PyObject* PyColor::pyObject()
{
    PyTypeObject* type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Color");
    if (!type) return nullptr;
    
    PyColorObject* obj = (PyColorObject*)type->tp_alloc(type, 0);
    Py_DECREF(type);
    
    if (obj) {
        obj->data = data;
    }
    return (PyObject*)obj;
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
    PyColorObject* self = (PyColorObject*)obj;
    long member = (long)closure;
    
    switch (member) {
        case 0: // r
            return PyLong_FromLong(self->data.r);
        case 1: // g
            return PyLong_FromLong(self->data.g);
        case 2: // b
            return PyLong_FromLong(self->data.b);
        case 3: // a
            return PyLong_FromLong(self->data.a);
        default:
            PyErr_SetString(PyExc_AttributeError, "Invalid color member");
            return NULL;
    }
}

int PyColor::set_member(PyObject* obj, PyObject* value, void* closure)
{
    PyColorObject* self = (PyColorObject*)obj;
    long member = (long)closure;
    
    if (!PyLong_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "Color values must be integers");
        return -1;
    }
    
    long val = PyLong_AsLong(value);
    if (val < 0 || val > 255) {
        PyErr_SetString(PyExc_ValueError, "Color values must be between 0 and 255");
        return -1;
    }
    
    switch (member) {
        case 0: // r
            self->data.r = static_cast<sf::Uint8>(val);
            break;
        case 1: // g
            self->data.g = static_cast<sf::Uint8>(val);
            break;
        case 2: // b
            self->data.b = static_cast<sf::Uint8>(val);
            break;
        case 3: // a
            self->data.a = static_cast<sf::Uint8>(val);
            break;
        default:
            PyErr_SetString(PyExc_AttributeError, "Invalid color member");
            return -1;
    }
    
    return 0;
}

PyColorObject* PyColor::from_arg(PyObject* args)
{
    // Use RAII for type reference management
    PyRAII::PyTypeRef type("Color", McRFPy_API::mcrf_module);
    if (!type) {
        return NULL;
    }
    
    // Check if args is already a Color instance
    if (PyObject_IsInstance(args, (PyObject*)type.get())) {
        return (PyColorObject*)args;
    }
    
    // Create new Color object using RAII
    PyRAII::PyObjectRef obj(type->tp_alloc(type.get(), 0), true);
    if (!obj) {
        return NULL;
    }
    
    // Initialize the object
    int err = init((PyColorObject*)obj.get(), args, NULL);
    if (err) {
        // obj will be automatically cleaned up when it goes out of scope
        return NULL;
    }
    
    // Release ownership and return
    return (PyColorObject*)obj.release();
}

// Color helper method implementations
PyObject* PyColor::from_hex(PyObject* cls, PyObject* args)
{
    const char* hex_str;
    if (!PyArg_ParseTuple(args, "s", &hex_str)) {
        return NULL;
    }
    
    std::string hex(hex_str);
    
    // Remove # if present
    if (hex.length() > 0 && hex[0] == '#') {
        hex = hex.substr(1);
    }
    
    // Validate hex string
    if (hex.length() != 6 && hex.length() != 8) {
        PyErr_SetString(PyExc_ValueError, "Hex string must be 6 or 8 characters (RGB or RGBA)");
        return NULL;
    }
    
    // Parse hex values
    try {
        unsigned int r = std::stoul(hex.substr(0, 2), nullptr, 16);
        unsigned int g = std::stoul(hex.substr(2, 2), nullptr, 16);
        unsigned int b = std::stoul(hex.substr(4, 2), nullptr, 16);
        unsigned int a = 255;
        
        if (hex.length() == 8) {
            a = std::stoul(hex.substr(6, 2), nullptr, 16);
        }
        
        // Create new Color object
        PyTypeObject* type = (PyTypeObject*)cls;
        PyColorObject* color = (PyColorObject*)type->tp_alloc(type, 0);
        if (color) {
            color->data = sf::Color(r, g, b, a);
        }
        return (PyObject*)color;
        
    } catch (const std::exception& e) {
        PyErr_SetString(PyExc_ValueError, "Invalid hex string");
        return NULL;
    }
}

PyObject* PyColor::to_hex(PyColorObject* self, PyObject* Py_UNUSED(ignored))
{
    char hex[10];  // #RRGGBBAA + null terminator
    
    // Include alpha only if not fully opaque
    if (self->data.a < 255) {
        snprintf(hex, sizeof(hex), "#%02X%02X%02X%02X", 
                 self->data.r, self->data.g, self->data.b, self->data.a);
    } else {
        snprintf(hex, sizeof(hex), "#%02X%02X%02X", 
                 self->data.r, self->data.g, self->data.b);
    }
    
    return PyUnicode_FromString(hex);
}

PyObject* PyColor::lerp(PyColorObject* self, PyObject* args)
{
    PyObject* other_obj;
    float t;
    
    if (!PyArg_ParseTuple(args, "Of", &other_obj, &t)) {
        return NULL;
    }
    
    // Validate other color
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Color");
    if (!PyObject_IsInstance(other_obj, (PyObject*)type)) {
        Py_DECREF(type);
        PyErr_SetString(PyExc_TypeError, "First argument must be a Color");
        return NULL;
    }
    
    PyColorObject* other = (PyColorObject*)other_obj;
    
    // Clamp t to [0, 1]
    if (t < 0.0f) t = 0.0f;
    if (t > 1.0f) t = 1.0f;
    
    // Perform linear interpolation
    sf::Uint8 r = static_cast<sf::Uint8>(self->data.r + (other->data.r - self->data.r) * t);
    sf::Uint8 g = static_cast<sf::Uint8>(self->data.g + (other->data.g - self->data.g) * t);
    sf::Uint8 b = static_cast<sf::Uint8>(self->data.b + (other->data.b - self->data.b) * t);
    sf::Uint8 a = static_cast<sf::Uint8>(self->data.a + (other->data.a - self->data.a) * t);
    
    // Create new Color object
    PyColorObject* result = (PyColorObject*)type->tp_alloc(type, 0);
    Py_DECREF(type);
    
    if (result) {
        result->data = sf::Color(r, g, b, a);
    }
    
    return (PyObject*)result;
}
