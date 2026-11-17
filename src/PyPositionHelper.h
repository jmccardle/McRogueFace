#pragma once
#include "Python.h"
#include <cmath>
#include <climits>
#include <cfloat>
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
        // Vector (most specific). A type check, not isinstance: __class__ can lie or raise,
        // and the cast below must be of a real Vector (or subclass).
        if (PyObject_TypeCheck(obj, &mcrfpydef::PyVectorType)) {
            PyVectorObject* vec = (PyVectorObject*)obj;
            return vector_to_float(vec->data.x, out_x) && vector_to_float(vec->data.y, out_y);
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
        // Vector: a type check, not isinstance (see extract_from_iterable).
        if (PyObject_TypeCheck(obj, &mcrfpydef::PyVectorType)) {
            PyVectorObject* vec = (PyVectorObject*)obj;
            // Fractional components truncate toward zero (#540 item 3 is undecided);
            // non-finite or out-of-range ones raise before the float->int cast.
            return float_to_int(vec->data.x, out_x) && float_to_int(vec->data.y, out_y);
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

    // A float Vector/tuple component for a position: nan/inf are not positions (ValueError),
    // and a finite double that does not fit a float is an OverflowError.
    static bool vector_to_float(double v, float* out) {
        if (!std::isfinite(v)) {
            PyErr_SetString(PyExc_ValueError, "position component must be finite");
            return false;
        }
        if (std::fabs(v) > static_cast<double>(FLT_MAX)) {
            PyErr_SetString(PyExc_OverflowError, "position component out of range for a float");
            return false;
        }
        *out = static_cast<float>(v);
        return true;
    }

    // An int-like object as a C long: ints (and subclasses: bool, IntEnum) directly, anything
    // else with __index__ (numpy integers) through it. Returns false WITHOUT an error when obj
    // is not int-like; false WITH an error (OverflowError, or whatever __index__ raised).
    static bool as_long(PyObject* obj, long* out, bool* is_intlike) {
        *is_intlike = true;
        PyObject* idx = nullptr;
        if (PyLong_Check(obj)) {
            idx = obj; Py_INCREF(idx);
        } else if (PyIndex_Check(obj)) {
            idx = PyNumber_Index(obj);
            if (!idx) return false;
        } else {
            *is_intlike = false;
            return false;
        }
        long v = PyLong_AsLong(idx);
        Py_DECREF(idx);
        if (v == -1 && PyErr_Occurred()) return false;
        *out = v;
        return true;
    }

    // Extract a float from a numeric Python object (float, int, or __index__ object).
    // Returns false WITHOUT an error when obj is not a number; false WITH an error set
    // (OverflowError / ValueError) for a number that is not a usable position component.
    // Callers must check PyErr_Occurred() after a false return and propagate.
    static bool extract_number(PyObject* obj, float* out) {
        if (PyFloat_Check(obj)) {
            return vector_to_float(PyFloat_AS_DOUBLE(obj), out);
        }
        long v;
        bool intlike;
        if (!as_long(obj, &v, &intlike)) return false;
        *out = static_cast<float>(v);
        return true;
    }

    // Checked double -> int: ValueError for nan/inf, OverflowError outside int range.
    // Truncates toward zero; sets the Python error and returns false on failure.
    static bool float_to_int(double v, int* out) {
        if (!std::isfinite(v)) {
            PyErr_SetString(PyExc_ValueError, "position component must be finite");
            return false;
        }
        if (!(v > static_cast<double>(INT_MIN) - 1.0 && v < static_cast<double>(INT_MAX) + 1.0)) {
            PyErr_SetString(PyExc_OverflowError, "position component out of range for a C int");
            return false;
        }
        *out = static_cast<int>(v);
        return true;
    }

    // Extract an int from a numeric Python object (integers, or whole-number floats).
    // Returns false WITHOUT an error set when obj is not an acceptable number (caller
    // may try another interpretation); returns false WITH an error set (OverflowError /
    // ValueError) when it is a number that does not fit an int. Callers must check
    // PyErr_Occurred() after a false return and propagate.
    static bool extract_int(PyObject* obj, int* out) {
        long v;
        bool intlike;
        if (as_long(obj, &v, &intlike)) {
            if (v < INT_MIN || v > INT_MAX) {
                PyErr_SetString(PyExc_OverflowError, "position component out of range for a C int");
                return false;
            }
            *out = static_cast<int>(v);
            return true;
        }
        if (intlike) return false;  // error set (OverflowError, or from __index__)
        // Also accept float but only if it's a whole number
        if (PyFloat_Check(obj)) {
            double val = PyFloat_AS_DOUBLE(obj);
            int iv;
            if (!float_to_int(val, &iv)) return false;
            if (val == static_cast<double>(iv)) {
                *out = iv;
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
        if (PyErr_Occurred()) return false;
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
        if (PyErr_Occurred()) return false;  // OverflowError / ValueError from a component
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
                if (PyErr_Occurred()) return false;
            }

            if (pos_obj) {
                if (extract_from_iterable(pos_obj, out_x, out_y)) {
                    return true;
                }
                if (PyErr_Occurred()) return false;
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
            if (PyErr_Occurred()) return false;
        }

        // Try single iterable argument: func((x, y)) or func(Vector) or func([x, y])
        if (nargs == 1) {
            PyObject* first = PyTuple_GetItem(args, 0);
            if (extract_from_iterable(first, out_x, out_y)) {
                return true;
            }
            if (PyErr_Occurred()) return false;
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
                if (PyErr_Occurred()) return false;
            }

            if (pos_obj) {
                if (extract_from_iterable_int(pos_obj, out_x, out_y)) {
                    return true;
                }
                if (PyErr_Occurred()) return false;
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
            if (PyErr_Occurred()) return false;
        }

        // Try single iterable argument: func((x, y)) or func(Vector) or func([x, y])
        if (nargs == 1) {
            PyObject* first = PyTuple_GetItem(args, 0);
            if (extract_from_iterable_int(first, out_x, out_y)) {
                return true;
            }
            if (PyErr_Occurred()) return false;
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
            if (PyErr_Occurred()) return result;  // has_position stays false, error set
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
            if (PyErr_Occurred()) return result;
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
                if (PyErr_Occurred()) return result;
            }

            if (pos_kw) {
                if (extract_from_iterable(pos_kw, &x, &y)) {
                    result.x = x;
                    result.y = y;
                    result.has_position = true;
                    return result;
                }
                if (PyErr_Occurred()) return result;
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