#include "PyColor.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"
#include <string>
#include <cstdio>

PyGetSetDef PyColor::getsetters[] = {
    {"r", (getter)PyColor::get_member, (setter)PyColor::set_member,
     MCRF_PROPERTY(r, "Red component, an int in 0-255; out of range raises ValueError."), (void*)0},
    {"g", (getter)PyColor::get_member, (setter)PyColor::set_member,
     MCRF_PROPERTY(g, "Green component, an int in 0-255; out of range raises ValueError."), (void*)1},
    {"b", (getter)PyColor::get_member, (setter)PyColor::set_member,
     MCRF_PROPERTY(b, "Blue component, an int in 0-255; out of range raises ValueError."), (void*)2},
    {"a", (getter)PyColor::get_member, (setter)PyColor::set_member,
     MCRF_PROPERTY(a, "Alpha component, an int in 0-255 (0=transparent, 255=opaque); out of range raises ValueError."), (void*)3},
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
    PyColorObject* obj = (PyColorObject*)mcrfpydef::PyColorType.tp_alloc(&mcrfpydef::PyColorType, 0);

    if (obj) {
        obj->data = data;
    }
    return (PyObject*)obj;
}

bool PyColor::to_color(PyObject* value, sf::Color& out)
{
    if (!value) {
        PyErr_SetString(PyExc_TypeError, "cannot delete a Color attribute");
        return false;
    }
    if (PyObject_TypeCheck(value, &mcrfpydef::PyColorType)) {
        out = ((PyColorObject*)value)->data;
        return true;
    }
    // Everything else is exactly Color(value): same accepted values, same exceptions.
    PyObject* color = PyObject_CallOneArg((PyObject*)&mcrfpydef::PyColorType, value);
    if (!color) return false;
    out = ((PyColorObject*)color)->data;
    Py_DECREF(color);
    return true;
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
        // #450: read into long and range-check before narrowing (an int cast wrapped
        // 2**32 + 5 to 5); a non-int or overflowing component reports the whole tuple.
        long c[4] = {0, 0, 0, 255};
        bool ok = true;
        for (Py_ssize_t i = 0; i < tupleSize; i++) {
            c[i] = PyLong_AsLong(PyTuple_GetItem(leader, i));
            if ((c[i] == -1 && PyErr_Occurred()) || c[i] < 0 || c[i] > 255) ok = false;
        }
        if (!ok) {
            PyErr_Clear();
            PyErr_Format(PyExc_ValueError, "Color components must be ints in 0-255, got %R", leader);
            return -1;
        }
        r = (int)c[0]; g = (int)c[1]; b = (int)c[2]; a = (int)c[3];
    }
    // Color name (not implemented yet)
    else if (PyUnicode_Check(leader)) {
        PyErr_SetString(PyExc_NotImplementedError, "Color names aren't ready yet");
        return -1;
    }
    // Check if the leader is actually an integer for the r value
    else if (PyLong_Check(leader)) {
        long lr = PyLong_AsLong(leader);
        if (lr == -1 && PyErr_Occurred()) PyErr_Clear();
        r = (lr < 0 || lr > 255) ? -1 : (int)lr;  // #450: no narrowing wrap; -1 fails below
    } else {
        PyErr_SetString(PyExc_TypeError, "mcrfpy.Color requires a 3-tuple, 4-tuple, color name, or integer values within 0-255 (r, g, b, optionally a)");
        return -1;
    }

    // Validate color values
    if (r < 0 || r > 255 || g < 0 || g > 255 || b < 0 || b > 255 || a < 0 || a > 255) {
        PyErr_Format(PyExc_ValueError, "Color components must be ints in 0-255, got %R", args);
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
    if (!PyObject_IsInstance(other_obj, (PyObject*)&mcrfpydef::PyColorType)) {
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
    auto type = &mcrfpydef::PyColorType;
    PyColorObject* result = (PyColorObject*)type->tp_alloc(type, 0);

    if (result) {
        result->data = sf::Color(r, g, b, a);
    }

    return (PyObject*)result;
}

PyObject* PyColor::richcompare(PyObject* left, PyObject* right, int op)
{
    // Only support == and !=
    if (op != Py_EQ && op != Py_NE) {
        Py_RETURN_NOTIMPLEMENTED;
    }

    // Extract RGBA from left operand
    sf::Color left_c, right_c;

    if (PyObject_IsInstance(left, (PyObject*)&mcrfpydef::PyColorType)) {
        left_c = ((PyColorObject*)left)->data;
    } else {
        Py_RETURN_NOTIMPLEMENTED;
    }

    // Extract RGBA from right operand - accept Color, tuple, or list
    if (PyObject_IsInstance(right, (PyObject*)&mcrfpydef::PyColorType)) {
        right_c = ((PyColorObject*)right)->data;
    } else if (PyTuple_Check(right) || PyList_Check(right)) {
        Py_ssize_t size = PySequence_Size(right);
        if (size < 3 || size > 4) {
            Py_RETURN_NOTIMPLEMENTED;
        }
        PyObject* r = PySequence_GetItem(right, 0);
        PyObject* g = PySequence_GetItem(right, 1);
        PyObject* b = PySequence_GetItem(right, 2);
        if (!PyLong_Check(r) || !PyLong_Check(g) || !PyLong_Check(b)) {
            Py_DECREF(r); Py_DECREF(g); Py_DECREF(b);
            Py_RETURN_NOTIMPLEMENTED;
        }
        right_c.r = (sf::Uint8)PyLong_AsLong(r);
        right_c.g = (sf::Uint8)PyLong_AsLong(g);
        right_c.b = (sf::Uint8)PyLong_AsLong(b);
        Py_DECREF(r); Py_DECREF(g); Py_DECREF(b);
        if (size == 4) {
            PyObject* a = PySequence_GetItem(right, 3);
            if (PyLong_Check(a)) right_c.a = (sf::Uint8)PyLong_AsLong(a);
            Py_DECREF(a);
        } else {
            right_c.a = 255;
        }
    } else {
        Py_RETURN_NOTIMPLEMENTED;
    }

    bool equal = (left_c.r == right_c.r && left_c.g == right_c.g &&
                  left_c.b == right_c.b && left_c.a == right_c.a);

    if (op == Py_EQ) {
        return PyBool_FromLong(equal);
    } else {
        return PyBool_FromLong(!equal);
    }
}
