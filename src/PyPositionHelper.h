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
// ============================================================================

class PyPositionHelper {
private:
    // Internal helper: extract two numeric values from a 2-element iterable
    // Returns true on success. On failure returns false: with an error set (OverflowError /
    // ValueError / an error from __index__) if a component was a bad number, without one if the
    // object is simply not a position. Callers check PyErr_Occurred() after a false return.
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
            if (!sequence_is_pair(obj)) return false;
            PyObject* x_obj = PySequence_GetItem(obj, 0);
            if (!x_obj) return false;  // __getitem__ raised: the error propagates (#540 item 14)
            PyObject* y_obj = PySequence_GetItem(obj, 1);
            if (!y_obj) { Py_DECREF(x_obj); return false; }

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
            if (!sequence_is_pair(obj)) return false;
            PyObject* x_obj = PySequence_GetItem(obj, 0);
            if (!x_obj) return false;  // __getitem__ raised: the error propagates (#540 item 14)
            PyObject* y_obj = PySequence_GetItem(obj, 1);
            if (!y_obj) { Py_DECREF(x_obj); return false; }

            bool success = extract_int(x_obj, out_x) && extract_int(y_obj, out_y);
            Py_DECREF(x_obj);
            Py_DECREF(y_obj);
            return success;
        }

        return false;
    }

    // For a generic sequence: true if it has exactly two items. False WITHOUT an error when it
    // is not a pair: a wrong length, or a type with no length slot at all (decided by the type
    // slots, so no len() call is made and no error is cleared). False WITH an error when
    // __len__ itself failed, whatever the exception: it propagates (#540 item 14).
    static bool sequence_is_pair(PyObject* obj) {
        PyTypeObject* t = Py_TYPE(obj);
        bool sized = (t->tp_as_sequence && t->tp_as_sequence->sq_length) ||
                     (t->tp_as_mapping && t->tp_as_mapping->mp_length);
        if (!sized) return false;
        Py_ssize_t len = PyObject_Length(obj);
        if (len < 0) return false;
        return len == 2;
    }

    // The argument being parsed, for error messages (nullptr: unnamed). Set by the named entry
    // points (FromObject / FromObjectInt) for the duration of the parse, so a nested parse from
    // a user's __len__ / __index__ restores the outer name on the way out.
    inline static thread_local const char* what_ = nullptr;
    struct WhatScope {
        const char* saved;
        explicit WhatScope(const char* w) : saved(what_) { what_ = w; }
        ~WhatScope() { what_ = saved; }
    };

    // OverflowError / ValueError for a bad component, naming the argument when there is one.
    static void set_error(PyObject* exc, const char* msg) {
        if (what_) PyErr_Format(exc, "%s: %s", what_, msg);
        else PyErr_SetString(exc, msg);
    }

    // A float Vector/tuple component for a position: nan/inf are not positions (ValueError),
    // and a finite double that does not fit a float is an OverflowError.
    static bool vector_to_float(double v, float* out) {
        if (!std::isfinite(v)) {
            set_error(PyExc_ValueError, "position component must be finite");
            return false;
        }
        if (std::fabs(v) > static_cast<double>(FLT_MAX)) {
            set_error(PyExc_OverflowError, "position component out of range for a float");
            return false;
        }
        *out = static_cast<float>(v);
        return true;
    }

    // An int-like object as a C long: ints (and subclasses: bool, IntEnum) directly, anything
    // else with __index__ (numpy integers) through it. Returns false WITHOUT an error when obj
    // is not int-like; false WITH an error (OverflowError, or whatever __index__ raised).
    // The int an int-like object stands for, as a NEW reference (nullptr: none).
    static PyObject* as_pylong(PyObject* obj, bool* is_intlike) {
        *is_intlike = true;
        if (PyLong_Check(obj)) { Py_INCREF(obj); return obj; }
        if (PyIndex_Check(obj)) return PyNumber_Index(obj);  // nullptr: __index__ raised
        *is_intlike = false;
        return nullptr;
    }

    static bool as_long(PyObject* obj, long* out, bool* is_intlike) {
        PyObject* idx = as_pylong(obj, is_intlike);
        if (!idx) return false;
        long v = PyLong_AsLong(idx);
        Py_DECREF(idx);
        if (v == -1 && PyErr_Occurred()) {
            // idx is an exact int, so the only failure is OverflowError: say it our way.
            PyErr_Clear();
            set_error(PyExc_OverflowError, "position component out of range for a C int");
            return false;
        }
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
        // Ints (and __index__ results) convert as doubles and get the same finite / FLT_MAX
        // check as floats, so 10**20 and 1e20 behave alike; 10**40 and 1e40 both overflow.
        bool intlike;
        PyObject* idx = as_pylong(obj, &intlike);
        if (!idx) return false;
        double d = PyLong_AsDouble(idx);
        Py_DECREF(idx);
        if (d == -1.0 && PyErr_Occurred()) {  // beyond even a double (exact int: OverflowError)
            PyErr_Clear();
            set_error(PyExc_OverflowError, "position component out of range for a float");
            return false;
        }
        return vector_to_float(d, out);
    }

    // Checked double -> int: ValueError for nan/inf, OverflowError outside int range.
    // Truncates toward zero; sets the Python error and returns false on failure.
    static bool float_to_int(double v, int* out) {
        if (!std::isfinite(v)) {
            set_error(PyExc_ValueError, "position component must be finite");
            return false;
        }
        if (!(v > static_cast<double>(INT_MIN) - 1.0 && v < static_cast<double>(INT_MAX) + 1.0)) {
            set_error(PyExc_OverflowError, "position component out of range for a C int");
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
                set_error(PyExc_OverflowError, "position component out of range for a C int");
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
    //
    // `what` names the argument for callers that have one ("size", "pos"): the TypeError for an
    // object that is not a position then says "<what> must be ...". A component that is a number
    // but unusable (OverflowError / ValueError) is never replaced: callers just propagate.
    static bool FromObject(PyObject* obj, float* out_x, float* out_y, const char* what = nullptr) {
        WhatScope scope(what);
        if (extract_from_iterable(obj, out_x, out_y)) {
            return true;
        }
        if (PyErr_Occurred()) return false;
        if (what) {
            PyErr_Format(PyExc_TypeError,
                "%s must be a position: (x, y) tuple, [x, y] list, Vector, or other 2-element sequence", what);
        } else {
            PyErr_SetString(PyExc_TypeError,
                "Expected a position as (x, y) tuple, [x, y] list, Vector, or other 2-element sequence");
        }
        return false;
    }

    // Extract integer position from any supported format
    // Sets Python error and returns false on failure
    // `what`: see FromObject.
    static bool FromObjectInt(PyObject* obj, int* out_x, int* out_y, const char* what = nullptr) {
        WhatScope scope(what);
        if (extract_from_iterable_int(obj, out_x, out_y)) {
            return true;
        }
        if (PyErr_Occurred()) return false;  // OverflowError / ValueError from a component
        if (what) {
            PyErr_Format(PyExc_TypeError,
                "%s must be an integer position: (x, y) tuple, [x, y] list, Vector, or other 2-element sequence", what);
        } else {
            PyErr_SetString(PyExc_TypeError,
                "Expected integer position as (x, y) tuple, [x, y] list, Vector, or other 2-element sequence");
        }
        return false;
    }

    // ========================================================================
    // Method argument API: Parse position from args tuple
    // ========================================================================

    // Parse float position from method arguments
    // Supports: func(x, y) or func((x, y)) or func(Vector) or func(iterable)
    // Sets Python error and returns false on failure
    static bool ParseFloat(PyObject* args, PyObject* kwds, float* out_x, float* out_y) {
        WhatScope scope(nullptr);
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
        WhatScope scope(nullptr);
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
inline bool PyPosition_FromObjectInt(PyObject* obj, int* x, int* y, const char* what = nullptr) {
    return PyPositionHelper::FromObjectInt(obj, x, y, what);
}

// Extract float position from a single Python object
// Usage: if (!PyPosition_FromObject(obj, &x, &y)) return NULL;
inline bool PyPosition_FromObject(PyObject* obj, float* x, float* y, const char* what = nullptr) {
    return PyPositionHelper::FromObject(obj, x, y, what);
}