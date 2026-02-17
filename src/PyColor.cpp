#include "PyColor.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"
#include <string>
#include <cstdio>

PyGetSetDef PyColor::getsetters[] = {
    {"r", (getter)PyColor::get_member, (setter)PyColor::set_member,
     MCRF_PROPERTY(r, "Red component (0-255). Automatically clamped to valid range."), (void*)0},
    {"g", (getter)PyColor::get_member, (setter)PyColor::set_member,
     MCRF_PROPERTY(g, "Green component (0-255). Automatically clamped to valid range."), (void*)1},
    {"b", (getter)PyColor::get_member, (setter)PyColor::set_member,
     MCRF_PROPERTY(b, "Blue component (0-255). Automatically clamped to valid range."), (void*)2},
    {"a", (getter)PyColor::get_member, (setter)PyColor::set_member,
     MCRF_PROPERTY(a, "Alpha component (0-255, where 0=transparent, 255=opaque). Automatically clamped to valid range."), (void*)3},
    {NULL}
};

PyMethodDef PyColor::methods[] = {
    {"from_hex", (PyCFunction)PyColor::from_hex, METH_VARARGS | METH_CLASS,
     MCRF_METHOD(Color, from_hex,
         MCRF_SIG("(hex_string: str)", "Color"),
         MCRF_DESC("Create a Color from a hexadecimal string."),
         MCRF_ARGS_START
         MCRF_ARG("hex_string", "Hex color string (e.g., '#FF0000', 'FF0000', '#AABBCCDD' for RGBA)")
         MCRF_RETURNS("Color: New Color object with values from hex string")
         MCRF_RAISES("ValueError", "If hex string is not 6 or 8 characters (RGB or RGBA)")
         MCRF_NOTE("This is a class method. Call as Color.from_hex('#FF0000')")
     )},
    {"to_hex", (PyCFunction)PyColor::to_hex, METH_NOARGS,
     MCRF_METHOD(Color, to_hex,
         MCRF_SIG("()", "str"),
         MCRF_DESC("Convert this Color to a hexadecimal string."),
         MCRF_RETURNS("str: Hex string in format '#RRGGBB' or '#RRGGBBAA' (if alpha < 255)")
         MCRF_NOTE("Alpha component is only included if not fully opaque (< 255)")
     )},
    {"lerp", (PyCFunction)PyColor::lerp, METH_VARARGS,
     MCRF_METHOD(Color, lerp,
         MCRF_SIG("(other: Color, t: float)", "Color"),
         MCRF_DESC("Linearly interpolate between this color and another."),
         MCRF_ARGS_START
         MCRF_ARG("other", "The target Color to interpolate towards")
         MCRF_ARG("t", "Interpolation factor (0.0 = this color, 1.0 = other color). Automatically clamped to [0.0, 1.0]")
         MCRF_RETURNS("Color: New Color representing the interpolated value")
         MCRF_NOTE("All components (r, g, b, a) are interpolated independently")
     )},
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
    // Handle None or NULL
    if (!obj || obj == Py_None) {
        return sf::Color::White;
    }

    // Check if it's already a Color object
    PyTypeObject* color_type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Color");
    if (color_type) {
        bool is_color = PyObject_TypeCheck(obj, color_type);
        Py_DECREF(color_type);
        if (is_color) {
            PyColorObject* self = (PyColorObject*)obj;
            return self->data;
        }
    }

    // Handle tuple or list input
    if (PyTuple_Check(obj) || PyList_Check(obj)) {
        Py_ssize_t size = PySequence_Size(obj);
        if (size < 3 || size > 4) {
            PyErr_SetString(PyExc_TypeError, "Color tuple/list must have 3 or 4 elements (r, g, b[, a])");
            return sf::Color::White;
        }

        int r = 255, g = 255, b = 255, a = 255;

        PyObject* item0 = PySequence_GetItem(obj, 0);
        PyObject* item1 = PySequence_GetItem(obj, 1);
        PyObject* item2 = PySequence_GetItem(obj, 2);

        if (PyLong_Check(item0)) r = (int)PyLong_AsLong(item0);
        if (PyLong_Check(item1)) g = (int)PyLong_AsLong(item1);
        if (PyLong_Check(item2)) b = (int)PyLong_AsLong(item2);

        Py_DECREF(item0);
        Py_DECREF(item1);
        Py_DECREF(item2);

        if (size == 4) {
            PyObject* item3 = PySequence_GetItem(obj, 3);
            if (PyLong_Check(item3)) a = (int)PyLong_AsLong(item3);
            Py_DECREF(item3);
        }

        // Clamp values
        r = std::max(0, std::min(255, r));
        g = std::max(0, std::min(255, g));
        b = std::max(0, std::min(255, b));
        a = std::max(0, std::min(255, a));

        return sf::Color(r, g, b, a);
    }

    // Handle integer (grayscale)
    if (PyLong_Check(obj)) {
        int v = std::max(0, std::min(255, (int)PyLong_AsLong(obj)));
        return sf::Color(v, v, v, 255);
    }

    // Unknown type - set error and return white
    PyErr_SetString(PyExc_TypeError, "Color must be a Color object, tuple, list, or integer");
    return sf::Color::White;
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
    value <<= 8; value += self->data.g; 
    value <<= 8; value += self->data.b; 
    value <<= 8; value += self->data.a;

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
    intptr_t member = (intptr_t)closure;
    
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
    intptr_t member = (intptr_t)closure;
    
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
    PyTypeObject* type = &mcrfpydef::PyColorType;

    // Check if args is already a Color instance
    if (PyObject_IsInstance(args, (PyObject*)type)) {
        Py_INCREF(args);  // Return new reference so caller can safely DECREF
        return (PyColorObject*)args;
    }

    // Create new Color object
    PyObject* obj = type->tp_alloc(type, 0);
    if (!obj) {
        return NULL;
    }

    // Initialize the object
    int err = init((PyColorObject*)obj, args, NULL);
    if (err) {
        Py_DECREF(obj);
        return NULL;
    }

    return (PyColorObject*)obj;
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
