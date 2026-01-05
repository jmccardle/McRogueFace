#pragma once
#include "Python.h"
#include "PyVector.h"
#include "McRFPy_API.h"

// ============================================================================
// PyPositionHelper - Reusable position argument parsing for McRogueFace API
// ============================================================================
//
// This helper provides standardized parsing for position arguments that can be
// specified in multiple formats:
//   - Two separate args: func(x, y)
//   - A tuple: func((x, y))
//   - A Vector object: func(Vector(x, y))
//   - Any iterable with len() == 2: func([x, y])
//   - Keyword args: func(x=x, y=y) or func(pos=(x,y))
//
// Usage patterns:
//   // For methods with only position args (like Grid.at()):
//   int x, y;
//   if (!PyPosition_ParseInt(args, kwds, &x, &y)) return NULL;
//
//   // For extracting position from a single PyObject:
//   float x, y;
//   if (!PyPosition_FromObject(obj, &x, &y)) return NULL;
//
//   // For more complex parsing with additional args:
//   auto result = PyPositionHelper::parse_position(args, kwds);
//   if (!result.has_position) { ... }
// ============================================================================

class PyPositionHelper {
public:
    // Template structure for parsing results
    struct ParseResult {
        float x = 0.0f;
        float y = 0.0f;
        bool has_position = false;
    };

    struct ParseResultInt {
        int x = 0;
        int y = 0;
        bool has_position = false;
    };

private:
    // Internal helper: extract two numeric values from a 2-element iterable
    // Returns true on success, false on failure (does NOT set Python error)
    static bool extract_from_iterable(PyObject* obj, float* out_x, float* out_y) {
        // First check if it's a Vector (most specific)
        PyTypeObject* vector_type = (PyTypeObject*)PyObject_GetAttrString(
            McRFPy_API::mcrf_module, "Vector");
        if (vector_type) {
            if (PyObject_IsInstance(obj, (PyObject*)vector_type)) {
                PyVectorObject* vec = (PyVectorObject*)obj;
                *out_x = vec->data.x;
                *out_y = vec->data.y;
                Py_DECREF(vector_type);
                return true;
            }
            Py_DECREF(vector_type);
        } else {
            PyErr_Clear();  // Clear any error from GetAttrString
        }

        // Check for tuple (common case, optimized)
        if (PyTuple_Check(obj)) {
            if (PyTuple_Size(obj) != 2) return false;
            PyObject* x_obj = PyTuple_GetItem(obj, 0);
            PyObject* y_obj = PyTuple_GetItem(obj, 1);
            if (!extract_number(x_obj, out_x) || !extract_number(y_obj, out_y)) {
                return false;
            }
            return true;
        }

        // Check for list (also common)
        if (PyList_Check(obj)) {
            if (PyList_Size(obj) != 2) return false;
            PyObject* x_obj = PyList_GetItem(obj, 0);
            PyObject* y_obj = PyList_GetItem(obj, 1);
            if (!extract_number(x_obj, out_x) || !extract_number(y_obj, out_y)) {
                return false;
            }
            return true;
        }

        // Generic iterable fallback: check __len__ and index
        // This handles any object that implements sequence protocol
        if (PySequence_Check(obj)) {
            Py_ssize_t len = PySequence_Size(obj);
            if (len != 2) {
                PyErr_Clear();  // Clear size error
                return false;
            }
            PyObject* x_obj = PySequence_GetItem(obj, 0);
            if (!x_obj) { PyErr_Clear(); return false; }
            PyObject* y_obj = PySequence_GetItem(obj, 1);
            if (!y_obj) { Py_DECREF(x_obj); PyErr_Clear(); return false; }

            bool success = extract_number(x_obj, out_x) && extract_number(y_obj, out_y);
            Py_DECREF(x_obj);
            Py_DECREF(y_obj);
            return success;
        }

        return false;
    }

    // Internal helper: extract integer values from a 2-element iterable
    static bool extract_from_iterable_int(PyObject* obj, int* out_x, int* out_y) {
        // First check if it's a Vector
        PyTypeObject* vector_type = (PyTypeObject*)PyObject_GetAttrString(
            McRFPy_API::mcrf_module, "Vector");
        if (vector_type) {
            if (PyObject_IsInstance(obj, (PyObject*)vector_type)) {
                PyVectorObject* vec = (PyVectorObject*)obj;
                *out_x = static_cast<int>(vec->data.x);
                *out_y = static_cast<int>(vec->data.y);
                Py_DECREF(vector_type);
                return true;
            }
            Py_DECREF(vector_type);
        } else {
            PyErr_Clear();
        }

        // Check for tuple
        if (PyTuple_Check(obj)) {
            if (PyTuple_Size(obj) != 2) return false;
            PyObject* x_obj = PyTuple_GetItem(obj, 0);
            PyObject* y_obj = PyTuple_GetItem(obj, 1);
            if (!extract_int(x_obj, out_x) || !extract_int(y_obj, out_y)) {
                return false;
            }
            return true;
        }

        // Check for list
        if (PyList_Check(obj)) {
            if (PyList_Size(obj) != 2) return false;
            PyObject* x_obj = PyList_GetItem(obj, 0);
            PyObject* y_obj = PyList_GetItem(obj, 1);
            if (!extract_int(x_obj, out_x) || !extract_int(y_obj, out_y)) {
                return false;
            }
            return true;
        }

        // Generic sequence fallback
        if (PySequence_Check(obj)) {
            Py_ssize_t len = PySequence_Size(obj);
            if (len != 2) {
                PyErr_Clear();
                return false;
            }
            PyObject* x_obj = PySequence_GetItem(obj, 0);
            if (!x_obj) { PyErr_Clear(); return false; }
            PyObject* y_obj = PySequence_GetItem(obj, 1);
            if (!y_obj) { Py_DECREF(x_obj); PyErr_Clear(); return false; }

            bool success = extract_int(x_obj, out_x) && extract_int(y_obj, out_y);
            Py_DECREF(x_obj);
            Py_DECREF(y_obj);
            return success;
        }

        return false;
    }

    // Extract a float from a numeric Python object
    static bool extract_number(PyObject* obj, float* out) {
        if (PyFloat_Check(obj)) {
            *out = static_cast<float>(PyFloat_AsDouble(obj));
            return true;
        }
        if (PyLong_Check(obj)) {
            *out = static_cast<float>(PyLong_AsLong(obj));
            return true;
        }
        return false;
    }

    // Extract an int from a numeric Python object (integers only)
    static bool extract_int(PyObject* obj, int* out) {
        if (PyLong_Check(obj)) {
            *out = static_cast<int>(PyLong_AsLong(obj));
            return true;
        }
        // Also accept float but only if it's a whole number
        if (PyFloat_Check(obj)) {
            double val = PyFloat_AsDouble(obj);
            if (val == static_cast<double>(static_cast<int>(val))) {
                *out = static_cast<int>(val);
                return true;
            }
        }
        return false;
    }

public:
    // ========================================================================
    // Simple API: Parse position from a single PyObject
    // ========================================================================

    // Extract float position from any supported format
    // Sets Python error and returns false on failure
    static bool FromObject(PyObject* obj, float* out_x, float* out_y) {
        if (extract_from_iterable(obj, out_x, out_y)) {
            return true;
        }
        PyErr_SetString(PyExc_TypeError,
            "Expected a position as (x, y) tuple, [x, y] list, Vector, or other 2-element sequence");
        return false;
    }

    // Extract integer position from any supported format
    // Sets Python error and returns false on failure
    static bool FromObjectInt(PyObject* obj, int* out_x, int* out_y) {
        if (extract_from_iterable_int(obj, out_x, out_y)) {
            return true;
        }
        PyErr_SetString(PyExc_TypeError,
            "Expected integer position as (x, y) tuple, [x, y] list, Vector, or other 2-element sequence");
        return false;
    }

    // ========================================================================
    // Method argument API: Parse position from args tuple
    // ========================================================================

    // Parse float position from method arguments
    // Supports: func(x, y) or func((x, y)) or func(Vector) or func(iterable)
    // Sets Python error and returns false on failure
    static bool ParseFloat(PyObject* args, PyObject* kwds, float* out_x, float* out_y) {
        // First try keyword arguments
        if (kwds) {
            PyObject* x_obj = PyDict_GetItemString(kwds, "x");
            PyObject* y_obj = PyDict_GetItemString(kwds, "y");
            PyObject* pos_obj = PyDict_GetItemString(kwds, "pos");

            if (x_obj && y_obj) {
                if (extract_number(x_obj, out_x) && extract_number(y_obj, out_y)) {
                    return true;
                }
            }

            if (pos_obj) {
                if (extract_from_iterable(pos_obj, out_x, out_y)) {
                    return true;
                }
            }
        }

        Py_ssize_t nargs = PyTuple_Size(args);

        // Try two separate numeric arguments: func(x, y)
        if (nargs >= 2) {
            PyObject* first = PyTuple_GetItem(args, 0);
            PyObject* second = PyTuple_GetItem(args, 1);

            if (extract_number(first, out_x) && extract_number(second, out_y)) {
                return true;
            }
        }

        // Try single iterable argument: func((x, y)) or func(Vector) or func([x, y])
        if (nargs == 1) {
            PyObject* first = PyTuple_GetItem(args, 0);
            if (extract_from_iterable(first, out_x, out_y)) {
                return true;
            }
        }

        PyErr_SetString(PyExc_TypeError,
            "Position can be specified as: (x, y), ((x,y)), pos=(x,y), Vector, or 2-element sequence");
        return false;
    }

    // Parse integer position from method arguments
    // Supports: func(x, y) or func((x, y)) or func(Vector) or func(iterable)
    // Sets Python error and returns false on failure
    static bool ParseInt(PyObject* args, PyObject* kwds, int* out_x, int* out_y) {
        // First try keyword arguments
        if (kwds) {
            PyObject* x_obj = PyDict_GetItemString(kwds, "x");
            PyObject* y_obj = PyDict_GetItemString(kwds, "y");
            PyObject* pos_obj = PyDict_GetItemString(kwds, "pos");

            if (x_obj && y_obj) {
                if (extract_int(x_obj, out_x) && extract_int(y_obj, out_y)) {
                    return true;
                }
            }

            if (pos_obj) {
                if (extract_from_iterable_int(pos_obj, out_x, out_y)) {
                    return true;
                }
            }
        }

        Py_ssize_t nargs = PyTuple_Size(args);

        // Try two separate integer arguments: func(x, y)
        if (nargs >= 2) {
            PyObject* first = PyTuple_GetItem(args, 0);
            PyObject* second = PyTuple_GetItem(args, 1);

            if (extract_int(first, out_x) && extract_int(second, out_y)) {
                return true;
            }
        }

        // Try single iterable argument: func((x, y)) or func(Vector) or func([x, y])
        if (nargs == 1) {
            PyObject* first = PyTuple_GetItem(args, 0);
            if (extract_from_iterable_int(first, out_x, out_y)) {
                return true;
            }
        }

        PyErr_SetString(PyExc_TypeError,
            "Position must be integers specified as: (x, y), ((x,y)), pos=(x,y), Vector, or 2-element sequence");
        return false;
    }

    // ========================================================================
    // Legacy struct-based API (for compatibility with existing code)
    // ========================================================================

    // Parse position from multiple formats for UI class constructors
    // Supports: (x, y), x=x, y=y, ((x,y)), (pos=(x,y)), (Vector), pos=Vector
    static ParseResult parse_position(PyObject* args, PyObject* kwds,
                                      int* arg_index = nullptr)
    {
        ParseResult result;
        float x = 0.0f, y = 0.0f;
        int start_index = arg_index ? *arg_index : 0;

        // Check for positional tuple (x, y) first
        if (PyTuple_Size(args) > start_index + 1) {
            PyObject* first = PyTuple_GetItem(args, start_index);
            PyObject* second = PyTuple_GetItem(args, start_index + 1);

            // Check if both are numbers
            if (extract_number(first, &x) && extract_number(second, &y)) {
                result.x = x;
                result.y = y;
                result.has_position = true;
                if (arg_index) *arg_index += 2;
                return result;
            }
        }

        // Check for single positional argument that might be tuple, list, or Vector
        if (PyTuple_Size(args) > start_index) {
            PyObject* first = PyTuple_GetItem(args, start_index);
            if (extract_from_iterable(first, &x, &y)) {
                result.x = x;
                result.y = y;
                result.has_position = true;
                if (arg_index) *arg_index += 1;
                return result;
            }
        }

        // Try keyword arguments
        if (kwds) {
            PyObject* x_obj = PyDict_GetItemString(kwds, "x");
            PyObject* y_obj = PyDict_GetItemString(kwds, "y");
            PyObject* pos_kw = PyDict_GetItemString(kwds, "pos");

            if (x_obj && y_obj) {
                if (extract_number(x_obj, &x) && extract_number(y_obj, &y)) {
                    result.x = x;
                    result.y = y;
                    result.has_position = true;
                    return result;
                }
            }

            if (pos_kw) {
                if (extract_from_iterable(pos_kw, &x, &y)) {
                    result.x = x;
                    result.y = y;
                    result.has_position = true;
                    return result;
                }
            }
        }

        return result;
    }

    // Parse integer position for Grid.at() and similar
    static ParseResultInt parse_position_int(PyObject* args, PyObject* kwds)
    {
        ParseResultInt result;
        int x = 0, y = 0;

        // Try the new simplified parser first
        if (ParseInt(args, kwds, &x, &y)) {
            result.x = x;
            result.y = y;
            result.has_position = true;
            PyErr_Clear();  // Clear any error set by ParseInt
        }

        return result;
    }

    // Error message helper
    static void set_position_error() {
        PyErr_SetString(PyExc_TypeError,
            "Position can be specified as: (x, y), x=x, y=y, ((x,y)), pos=(x,y), Vector, or 2-element sequence");
    }

    static void set_position_int_error() {
        PyErr_SetString(PyExc_TypeError,
            "Position must be integers specified as: (x, y), x=x, y=y, ((x,y)), pos=(x,y), Vector, or 2-element sequence");
    }
};

// ============================================================================
// Convenience macros/functions for common use patterns
// ============================================================================

// Parse integer position from method args - simplest API
// Usage: if (!PyPosition_ParseInt(args, kwds, &x, &y)) return NULL;
inline bool PyPosition_ParseInt(PyObject* args, PyObject* kwds, int* x, int* y) {
    return PyPositionHelper::ParseInt(args, kwds, x, y);
}

// Parse float position from method args
// Usage: if (!PyPosition_ParseFloat(args, kwds, &x, &y)) return NULL;
inline bool PyPosition_ParseFloat(PyObject* args, PyObject* kwds, float* x, float* y) {
    return PyPositionHelper::ParseFloat(args, kwds, x, y);
}

// Extract integer position from a single Python object
// Usage: if (!PyPosition_FromObjectInt(obj, &x, &y)) return NULL;
inline bool PyPosition_FromObjectInt(PyObject* obj, int* x, int* y) {
    return PyPositionHelper::FromObjectInt(obj, x, y);
}

// Extract float position from a single Python object
// Usage: if (!PyPosition_FromObject(obj, &x, &y)) return NULL;
inline bool PyPosition_FromObject(PyObject* obj, float* x, float* y) {
    return PyPositionHelper::FromObject(obj, x, y);
}