#include "PyVector.h"
#include "PyObjectUtils.h"
#include "McRFPy_Doc.h"
#include "PyRAII.h"
#include <cmath>

PyGetSetDef PyVector::getsetters[] = {
    {"x", (getter)PyVector::get_member, (setter)PyVector::set_member,
     MCRF_PROPERTY(x, "X coordinate of the vector (float)"), (void*)0},
    {"y", (getter)PyVector::get_member, (setter)PyVector::set_member,
     MCRF_PROPERTY(y, "Y coordinate of the vector (float)"), (void*)1},
    {"int", (getter)PyVector::get_int, NULL,
     MCRF_PROPERTY(int, "Integer tuple (floor of x and y) for use as dict keys. Read-only."), NULL},
    {NULL}
};

PyMethodDef PyVector::methods[] = {
    {"magnitude", (PyCFunction)PyVector::magnitude, METH_NOARGS,
     MCRF_METHOD(Vector, magnitude,
         MCRF_SIG("()", "float"),
         MCRF_DESC("Calculate the length/magnitude of this vector."),
         MCRF_RETURNS("float: The magnitude of the vector")
     )},
    {"magnitude_squared", (PyCFunction)PyVector::magnitude_squared, METH_NOARGS,
     MCRF_METHOD(Vector, magnitude_squared,
         MCRF_SIG("()", "float"),
         MCRF_DESC("Calculate the squared magnitude of this vector."),
         MCRF_RETURNS("float: The squared magnitude (faster than magnitude())")
         MCRF_NOTE("Use this for comparisons to avoid expensive square root calculation.")
     )},
    {"normalize", (PyCFunction)PyVector::normalize, METH_NOARGS,
     MCRF_METHOD(Vector, normalize,
         MCRF_SIG("()", "Vector"),
         MCRF_DESC("Return a unit vector in the same direction."),
         MCRF_RETURNS("Vector: New normalized vector with magnitude 1.0")
         MCRF_NOTE("For zero vectors (magnitude 0.0), returns a zero vector rather than raising an exception")
     )},
    {"dot", (PyCFunction)PyVector::dot, METH_O,
     MCRF_METHOD(Vector, dot,
         MCRF_SIG("(other: Vector)", "float"),
         MCRF_DESC("Calculate the dot product with another vector."),
         MCRF_ARGS_START
         MCRF_ARG("other", "The other vector")
         MCRF_RETURNS("float: Dot product of the two vectors")
     )},
    {"distance_to", (PyCFunction)PyVector::distance_to, METH_O,
     MCRF_METHOD(Vector, distance_to,
         MCRF_SIG("(other: Vector)", "float"),
         MCRF_DESC("Calculate the distance to another vector."),
         MCRF_ARGS_START
         MCRF_ARG("other", "The other vector")
         MCRF_RETURNS("float: Distance between the two vectors")
     )},
    {"angle", (PyCFunction)PyVector::angle, METH_NOARGS,
     MCRF_METHOD(Vector, angle,
         MCRF_SIG("()", "float"),
         MCRF_DESC("Get the angle of this vector in radians."),
         MCRF_RETURNS("float: Angle in radians from positive x-axis")
     )},
    {"copy", (PyCFunction)PyVector::copy, METH_NOARGS,
     MCRF_METHOD(Vector, copy,
         MCRF_SIG("()", "Vector"),
         MCRF_DESC("Create a copy of this vector."),
         MCRF_RETURNS("Vector: New Vector object with same x and y values")
     )},
    {"floor", (PyCFunction)PyVector::floor, METH_NOARGS,
     MCRF_METHOD(Vector, floor,
         MCRF_SIG("()", "Vector"),
         MCRF_DESC("Return a new vector with floored (integer) coordinates."),
         MCRF_RETURNS("Vector: New Vector with floor(x) and floor(y)")
         MCRF_NOTE("Useful for grid-based positioning. For a hashable tuple, use the .int property instead.")
     )},
    {NULL}
};

namespace mcrfpydef {
    PyNumberMethods PyVector_as_number = {
        .nb_add = PyVector::add,
        .nb_subtract = PyVector::subtract,
        .nb_multiply = PyVector::multiply,
        .nb_remainder = 0,
        .nb_divmod = 0,
        .nb_power = 0,
        .nb_negative = PyVector::negative,
        .nb_positive = 0,
        .nb_absolute = PyVector::absolute,
        .nb_bool = PyVector::bool_check,
        .nb_invert = 0,
        .nb_lshift = 0,
        .nb_rshift = 0,
        .nb_and = 0,
        .nb_xor = 0,
        .nb_or = 0,
        .nb_int = 0,
        .nb_reserved = 0,
        .nb_float = 0,
        .nb_inplace_add = 0,
        .nb_inplace_subtract = 0,
        .nb_inplace_multiply = 0,
        .nb_inplace_remainder = 0,
        .nb_inplace_power = 0,
        .nb_inplace_lshift = 0,
        .nb_inplace_rshift = 0,
        .nb_inplace_and = 0,
        .nb_inplace_xor = 0,
        .nb_inplace_or = 0,
        .nb_floor_divide = 0,
        .nb_true_divide = PyVector::divide,
        .nb_inplace_floor_divide = 0,
        .nb_inplace_true_divide = 0,
        .nb_index = 0,
        .nb_matrix_multiply = 0,
        .nb_inplace_matrix_multiply = 0
    };

    PySequenceMethods PyVector_as_sequence = {
        .sq_length = PyVector::sequence_length,
        .sq_concat = 0,
        .sq_repeat = 0,
        .sq_item = PyVector::sequence_item,
        .was_sq_slice = 0,
        .sq_ass_item = 0,
        .was_sq_ass_slice = 0,
        .sq_contains = 0,
        .sq_inplace_concat = 0,
        .sq_inplace_repeat = 0
    };
}

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
    // Use RAII for type reference management
    PyRAII::PyTypeRef type("Vector", McRFPy_API::mcrf_module);
    if (!type) {
        return NULL;
    }

    // Check if args is already a Vector instance
    if (PyObject_IsInstance(args, (PyObject*)type.get())) {
        Py_INCREF(args);  // Return new reference so caller can safely DECREF
        return (PyVectorObject*)args;
    }

    // Create new Vector object using RAII
    PyRAII::PyObjectRef obj(type->tp_alloc(type.get(), 0), true);
    if (!obj) {
        return NULL;
    }

    // Handle different input types
    if (PyTuple_Check(args)) {
        // It's already a tuple, pass it directly to init
        int err = init((PyVectorObject*)obj.get(), args, NULL);
        if (err) {
            // obj will be automatically cleaned up when it goes out of scope
            return NULL;
        }
    } else {
        // Wrap single argument in a tuple for init
        PyRAII::PyObjectRef tuple(PyTuple_Pack(1, args), true);
        if (!tuple) {
            return NULL;
        }
        int err = init((PyVectorObject*)obj.get(), tuple.get(), NULL);
        if (err) {
            return NULL;
        }
    }

    // Release ownership and return
    return (PyVectorObject*)obj.release();
}

// Arithmetic operations
PyObject* PyVector::add(PyObject* left, PyObject* right)
{
    // Check if both operands are vectors
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    
    PyVectorObject* vec1 = nullptr;
    PyVectorObject* vec2 = nullptr;
    
    if (PyObject_IsInstance(left, (PyObject*)type) && PyObject_IsInstance(right, (PyObject*)type)) {
        vec1 = (PyVectorObject*)left;
        vec2 = (PyVectorObject*)right;
    } else {
        Py_INCREF(Py_NotImplemented);
        return Py_NotImplemented;
    }
    
    auto result = (PyVectorObject*)type->tp_alloc(type, 0);
    if (result) {
        result->data = sf::Vector2f(vec1->data.x + vec2->data.x, vec1->data.y + vec2->data.y);
    }
    return (PyObject*)result;
}

PyObject* PyVector::subtract(PyObject* left, PyObject* right)
{
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    
    PyVectorObject* vec1 = nullptr;
    PyVectorObject* vec2 = nullptr;
    
    if (PyObject_IsInstance(left, (PyObject*)type) && PyObject_IsInstance(right, (PyObject*)type)) {
        vec1 = (PyVectorObject*)left;
        vec2 = (PyVectorObject*)right;
    } else {
        Py_INCREF(Py_NotImplemented);
        return Py_NotImplemented;
    }
    
    auto result = (PyVectorObject*)type->tp_alloc(type, 0);
    if (result) {
        result->data = sf::Vector2f(vec1->data.x - vec2->data.x, vec1->data.y - vec2->data.y);
    }
    return (PyObject*)result;
}

PyObject* PyVector::multiply(PyObject* left, PyObject* right)
{
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    
    PyVectorObject* vec = nullptr;
    double scalar = 0.0;
    
    // Check for Vector * scalar
    if (PyObject_IsInstance(left, (PyObject*)type) && (PyFloat_Check(right) || PyLong_Check(right))) {
        vec = (PyVectorObject*)left;
        scalar = PyFloat_AsDouble(right);
    }
    // Check for scalar * Vector
    else if ((PyFloat_Check(left) || PyLong_Check(left)) && PyObject_IsInstance(right, (PyObject*)type)) {
        scalar = PyFloat_AsDouble(left);
        vec = (PyVectorObject*)right;
    }
    else {
        Py_INCREF(Py_NotImplemented);
        return Py_NotImplemented;
    }
    
    auto result = (PyVectorObject*)type->tp_alloc(type, 0);
    if (result) {
        result->data = sf::Vector2f(vec->data.x * scalar, vec->data.y * scalar);
    }
    return (PyObject*)result;
}

PyObject* PyVector::divide(PyObject* left, PyObject* right)
{
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    
    // Only support Vector / scalar
    if (!PyObject_IsInstance(left, (PyObject*)type) || (!PyFloat_Check(right) && !PyLong_Check(right))) {
        Py_INCREF(Py_NotImplemented);
        return Py_NotImplemented;
    }
    
    PyVectorObject* vec = (PyVectorObject*)left;
    double scalar = PyFloat_AsDouble(right);
    
    if (scalar == 0.0) {
        PyErr_SetString(PyExc_ZeroDivisionError, "Vector division by zero");
        return NULL;
    }
    
    auto result = (PyVectorObject*)type->tp_alloc(type, 0);
    if (result) {
        result->data = sf::Vector2f(vec->data.x / scalar, vec->data.y / scalar);
    }
    return (PyObject*)result;
}

PyObject* PyVector::negative(PyObject* self)
{
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    PyVectorObject* vec = (PyVectorObject*)self;
    
    auto result = (PyVectorObject*)type->tp_alloc(type, 0);
    if (result) {
        result->data = sf::Vector2f(-vec->data.x, -vec->data.y);
    }
    return (PyObject*)result;
}

PyObject* PyVector::absolute(PyObject* self)
{
    PyVectorObject* vec = (PyVectorObject*)self;
    return PyFloat_FromDouble(std::sqrt(vec->data.x * vec->data.x + vec->data.y * vec->data.y));
}

int PyVector::bool_check(PyObject* self)
{
    PyVectorObject* vec = (PyVectorObject*)self;
    return (vec->data.x != 0.0f || vec->data.y != 0.0f) ? 1 : 0;
}

PyObject* PyVector::richcompare(PyObject* left, PyObject* right, int op)
{
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");

    float left_x, left_y, right_x, right_y;

    // Extract left operand values
    if (PyObject_IsInstance(left, (PyObject*)type)) {
        PyVectorObject* vec = (PyVectorObject*)left;
        left_x = vec->data.x;
        left_y = vec->data.y;
    } else if (PyTuple_Check(left) && PyTuple_Size(left) == 2) {
        PyObject* x_obj = PyTuple_GetItem(left, 0);
        PyObject* y_obj = PyTuple_GetItem(left, 1);
        if ((PyFloat_Check(x_obj) || PyLong_Check(x_obj)) &&
            (PyFloat_Check(y_obj) || PyLong_Check(y_obj))) {
            left_x = (float)PyFloat_AsDouble(x_obj);
            left_y = (float)PyFloat_AsDouble(y_obj);
        } else {
            Py_INCREF(Py_NotImplemented);
            return Py_NotImplemented;
        }
    } else {
        Py_INCREF(Py_NotImplemented);
        return Py_NotImplemented;
    }

    // Extract right operand values
    if (PyObject_IsInstance(right, (PyObject*)type)) {
        PyVectorObject* vec = (PyVectorObject*)right;
        right_x = vec->data.x;
        right_y = vec->data.y;
    } else if (PyTuple_Check(right) && PyTuple_Size(right) == 2) {
        PyObject* x_obj = PyTuple_GetItem(right, 0);
        PyObject* y_obj = PyTuple_GetItem(right, 1);
        if ((PyFloat_Check(x_obj) || PyLong_Check(x_obj)) &&
            (PyFloat_Check(y_obj) || PyLong_Check(y_obj))) {
            right_x = (float)PyFloat_AsDouble(x_obj);
            right_y = (float)PyFloat_AsDouble(y_obj);
        } else {
            Py_INCREF(Py_NotImplemented);
            return Py_NotImplemented;
        }
    } else {
        Py_INCREF(Py_NotImplemented);
        return Py_NotImplemented;
    }

    bool result = false;

    switch (op) {
        case Py_EQ:
            result = (left_x == right_x && left_y == right_y);
            break;
        case Py_NE:
            result = (left_x != right_x || left_y != right_y);
            break;
        default:
            Py_INCREF(Py_NotImplemented);
            return Py_NotImplemented;
    }

    if (result)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

// Vector-specific methods
PyObject* PyVector::magnitude(PyVectorObject* self, PyObject* Py_UNUSED(ignored))
{
    float mag = std::sqrt(self->data.x * self->data.x + self->data.y * self->data.y);
    return PyFloat_FromDouble(mag);
}

PyObject* PyVector::magnitude_squared(PyVectorObject* self, PyObject* Py_UNUSED(ignored))
{
    float mag_sq = self->data.x * self->data.x + self->data.y * self->data.y;
    return PyFloat_FromDouble(mag_sq);
}

PyObject* PyVector::normalize(PyVectorObject* self, PyObject* Py_UNUSED(ignored))
{
    float mag = std::sqrt(self->data.x * self->data.x + self->data.y * self->data.y);
    
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    auto result = (PyVectorObject*)type->tp_alloc(type, 0);
    
    if (result) {
        if (mag > 0.0f) {
            result->data = sf::Vector2f(self->data.x / mag, self->data.y / mag);
        } else {
            // Zero vector remains zero
            result->data = sf::Vector2f(0.0f, 0.0f);
        }
    }
    
    return (PyObject*)result;
}

PyObject* PyVector::dot(PyVectorObject* self, PyObject* other)
{
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    
    if (!PyObject_IsInstance(other, (PyObject*)type)) {
        PyErr_SetString(PyExc_TypeError, "Argument must be a Vector");
        return NULL;
    }
    
    PyVectorObject* vec2 = (PyVectorObject*)other;
    float dot_product = self->data.x * vec2->data.x + self->data.y * vec2->data.y;
    
    return PyFloat_FromDouble(dot_product);
}

PyObject* PyVector::distance_to(PyVectorObject* self, PyObject* other)
{
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    
    if (!PyObject_IsInstance(other, (PyObject*)type)) {
        PyErr_SetString(PyExc_TypeError, "Argument must be a Vector");
        return NULL;
    }
    
    PyVectorObject* vec2 = (PyVectorObject*)other;
    float dx = self->data.x - vec2->data.x;
    float dy = self->data.y - vec2->data.y;
    float distance = std::sqrt(dx * dx + dy * dy);
    
    return PyFloat_FromDouble(distance);
}

PyObject* PyVector::angle(PyVectorObject* self, PyObject* Py_UNUSED(ignored))
{
    float angle_rad = std::atan2(self->data.y, self->data.x);
    return PyFloat_FromDouble(angle_rad);
}

PyObject* PyVector::copy(PyVectorObject* self, PyObject* Py_UNUSED(ignored))
{
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    auto result = (PyVectorObject*)type->tp_alloc(type, 0);

    if (result) {
        result->data = self->data;
    }

    return (PyObject*)result;
}

PyObject* PyVector::floor(PyVectorObject* self, PyObject* Py_UNUSED(ignored))
{
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    auto result = (PyVectorObject*)type->tp_alloc(type, 0);

    if (result) {
        result->data = sf::Vector2f(std::floor(self->data.x), std::floor(self->data.y));
    }

    return (PyObject*)result;
}

// Sequence protocol implementation
Py_ssize_t PyVector::sequence_length(PyObject* self)
{
    return 2;  // Vectors always have exactly 2 elements
}

PyObject* PyVector::sequence_item(PyObject* obj, Py_ssize_t index)
{
    PyVectorObject* self = (PyVectorObject*)obj;

    // Note: Python already handles negative index normalization when sq_length is defined
    // So v[-1] arrives here as index=1, v[-2] as index=0
    // Out-of-range negative indices (like v[-3]) arrive as negative values (e.g., -1)
    if (index == 0) {
        return PyFloat_FromDouble(self->data.x);
    } else if (index == 1) {
        return PyFloat_FromDouble(self->data.y);
    } else {
        PyErr_SetString(PyExc_IndexError, "Vector index out of range (must be 0 or 1)");
        return NULL;
    }
}

// Property: .int - returns integer tuple for use as dict keys
PyObject* PyVector::get_int(PyObject* obj, void* closure)
{
    PyVectorObject* self = (PyVectorObject*)obj;
    long ix = (long)std::floor(self->data.x);
    long iy = (long)std::floor(self->data.y);
    return Py_BuildValue("(ll)", ix, iy);
}
