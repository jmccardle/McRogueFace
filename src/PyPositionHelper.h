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
    // `what` (every private function below): the argument being parsed, for error messages
    // (nullptr: unnamed). It is a plain parameter, not state, so a nested parse run from a
    // user's __len__ / __getitem__ / __index__ can never see or leave behind the wrong name.

    // OverflowError / ValueError for a bad component, naming the argument when there is one.
    static void set_error(PyObject* exc, const char* msg, const char* what) {
        if (what) PyErr_Format(exc, "%s: %s", what, msg);
        else PyErr_SetString(exc, msg);
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

    // The two items of a 2-element tuple, list or sequence, as NEW references the caller owns
    // (#543). Converting a component runs user code (__index__, __float__), which may mutate
    // the container; borrowed items would then be freed under us. Both are taken before any
    // user code runs (tuple/list: no call between the two reads; sequence: each __getitem__
    // returns a new reference). False WITHOUT an error: not a 2-element sequence of items;
    // false WITH an error: __len__ / __getitem__ raised (propagates).
    // bytes, bytearray, memoryview, range and str are sequences but not positions (#540 D).
    static bool fetch_pair(PyObject* obj, PyObject** x, PyObject** y) {
        if (PyTuple_Check(obj)) {
            if (PyTuple_GET_SIZE(obj) != 2) return false;
            *x = PyTuple_GET_ITEM(obj, 0);
            *y = PyTuple_GET_ITEM(obj, 1);
            Py_INCREF(*x);
            Py_INCREF(*y);
            return true;
        }
        if (PyList_Check(obj)) {
            if (PyList_GET_SIZE(obj) != 2) return false;
            *x = PyList_GET_ITEM(obj, 0);
            *y = PyList_GET_ITEM(obj, 1);
            Py_INCREF(*x);
            Py_INCREF(*y);
            return true;
        }
        if (PyBytes_Check(obj) || PyByteArray_Check(obj) || PyMemoryView_Check(obj) ||
            PyRange_Check(obj) || PyUnicode_Check(obj)) {
            return false;
        }
        if (!PySequence_Check(obj)) return false;
        if (!sequence_is_pair(obj)) return false;
        *x = PySequence_GetItem(obj, 0);
        if (!*x) return false;  // __getitem__ raised: the error propagates (#540 item 14)
        *y = PySequence_GetItem(obj, 1);
        if (!*y) { Py_DECREF(*x); return false; }
        return true;
    }

    // Extract two floats from a Vector or a 2-element tuple / list / sequence.
    // Returns true on success. On failure returns false: with an error set (OverflowError /
    // ValueError / an error from __index__) if a component was a bad number, without one if the
    // object is simply not a position. Callers check PyErr_Occurred() after a false return.
    static bool extract_from_iterable(PyObject* obj, float* out_x, float* out_y, const char* what) {
        // Vector (most specific). A type check, not isinstance: __class__ can lie or raise,
        // and the cast below must be of a real Vector (or subclass). Its data is plain C++
        // floats: no user code runs between the two reads.
        if (PyObject_TypeCheck(obj, &mcrfpydef::PyVectorType)) {
            PyVectorObject* vec = (PyVectorObject*)obj;
            return vector_to_float(vec->data.x, out_x, what) && vector_to_float(vec->data.y, out_y, what);
        }

        PyObject *x_obj, *y_obj;
        if (!fetch_pair(obj, &x_obj, &y_obj)) return false;
        bool ok = extract_number(x_obj, out_x, what) && extract_number(y_obj, out_y, what);
        Py_DECREF(x_obj);
        Py_DECREF(y_obj);
        return ok;
    }

    // Extract two ints from a Vector or a 2-element tuple / list / sequence. Fractional
    // components are floored (#540 item 3), the same for every input shape.
    static bool extract_from_iterable_int(PyObject* obj, int* out_x, int* out_y, const char* what) {
        // Vector: a type check, not isinstance (see extract_from_iterable).
        if (PyObject_TypeCheck(obj, &mcrfpydef::PyVectorType)) {
            PyVectorObject* vec = (PyVectorObject*)obj;
            return float_to_int(vec->data.x, out_x, what) && float_to_int(vec->data.y, out_y, what);
        }

        PyObject *x_obj, *y_obj;
        if (!fetch_pair(obj, &x_obj, &y_obj)) return false;
        bool ok = extract_int(x_obj, out_x, what) && extract_int(y_obj, out_y, what);
        Py_DECREF(x_obj);
        Py_DECREF(y_obj);
        return ok;
    }

    // A float Vector/tuple component for a position: nan/inf are not positions (ValueError),
    // and a finite double that does not fit a float is an OverflowError.
    static bool vector_to_float(double v, float* out, const char* what) {
        if (!std::isfinite(v)) {
            set_error(PyExc_ValueError, "position component must be finite", what);
            return false;
        }
        if (std::fabs(v) > static_cast<double>(FLT_MAX)) {
            set_error(PyExc_OverflowError, "position component out of range for a float", what);
            return false;
        }
        *out = static_cast<float>(v);
        return true;
    }

    // The int an int-like object stands for, as a NEW reference: ints (and subclasses: bool,
    // IntEnum) directly, anything else with __index__ (numpy integers) through it. nullptr with
    // *is_intlike false and NO error when obj is not int-like; nullptr with *is_intlike true
    // and an error set when __index__ raised.
    static PyObject* as_pylong(PyObject* obj, bool* is_intlike) {
        *is_intlike = true;
        if (PyLong_Check(obj)) { Py_INCREF(obj); return obj; }
        if (PyIndex_Check(obj)) return PyNumber_Index(obj);  // nullptr: __index__ raised
        *is_intlike = false;
        return nullptr;
    }

    // An int-like object as a C long. Returns false WITHOUT an error when obj is not int-like;
    // false WITH an error (OverflowError, or whatever __index__ raised).
    static bool as_long(PyObject* obj, long* out, bool* is_intlike, const char* what) {
        PyObject* idx = as_pylong(obj, is_intlike);
        if (!idx) return false;
        long v = PyLong_AsLong(idx);
        Py_DECREF(idx);
        if (v == -1 && PyErr_Occurred()) {
            // idx is an exact int, so the only failure is OverflowError: say it our way.
            PyErr_Clear();
            set_error(PyExc_OverflowError, "position component out of range for a C int", what);
            return false;
        }
        *out = v;
        return true;
    }

    // Extract a float from a numeric Python object (float, int, or __index__ object).
    // Returns false WITHOUT an error when obj is not a number; false WITH an error set
    // (OverflowError / ValueError) for a number that is not a usable position component.
    // Callers must check PyErr_Occurred() after a false return and propagate.
    static bool extract_number(PyObject* obj, float* out, const char* what) {
        if (PyFloat_Check(obj)) {
            return vector_to_float(PyFloat_AS_DOUBLE(obj), out, what);
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
            set_error(PyExc_OverflowError, "position component out of range for a float", what);
            return false;
        }
        return vector_to_float(d, out, what);
    }

    // Checked double -> int, FLOORED (toward negative infinity, not truncation; #540 item 3):
    // 2.7 -> 2, -0.5 -> -1. ValueError for nan/inf, OverflowError when the floored value is
    // outside int range. Sets the Python error and returns false on failure.
    static bool float_to_int(double v, int* out, const char* what) {
        if (!std::isfinite(v)) {
            set_error(PyExc_ValueError, "position component must be finite", what);
            return false;
        }
        double f = std::floor(v);
        if (!(f >= static_cast<double>(INT_MIN) && f <= static_cast<double>(INT_MAX))) {
            set_error(PyExc_OverflowError, "position component out of range for a C int", what);
            return false;
        }
        *out = static_cast<int>(f);
        return true;
    }

    // Extract an int from a numeric Python object: an int / __index__ object exactly, a float
    // floored. Returns false WITHOUT an error set when obj is not a number (caller may try
    // another interpretation); returns false WITH an error set (OverflowError / ValueError)
    // when it is a number that does not fit an int. Callers must check PyErr_Occurred() after
    // a false return and propagate.
    static bool extract_int(PyObject* obj, int* out, const char* what) {
        long v;
        bool intlike;
        if (as_long(obj, &v, &intlike, what)) {
            if (v < INT_MIN || v > INT_MAX) {
                set_error(PyExc_OverflowError, "position component out of range for a C int", what);
                return false;
            }
            *out = static_cast<int>(v);
            return true;
        }
        if (intlike) return false;  // error set (OverflowError, or from __index__)
        if (PyFloat_Check(obj)) return float_to_int(PyFloat_AS_DOUBLE(obj), out, what);
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
        if (extract_from_iterable(obj, out_x, out_y, what)) {
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

    // A single cell coordinate: an int / __index__ object exactly, a float floored (#540 item 3).
    // OverflowError / ValueError as for a position component; TypeError "<what> must be a
    // number" for anything else.
    static bool IntFromObject(PyObject* obj, int* out, const char* what) {
        if (extract_int(obj, out, what)) return true;
        if (PyErr_Occurred()) return false;
        PyErr_Format(PyExc_TypeError, "%s must be a number", what ? what : "value");
        return false;
    }

    // Extract integer position from any supported format
    // Sets Python error and returns false on failure
    // `what`: see FromObject.
    static bool FromObjectInt(PyObject* obj, int* out_x, int* out_y, const char* what = nullptr) {
        if (extract_from_iterable_int(obj, out_x, out_y, what)) {
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
        // First try keyword arguments
        if (kwds) {
            PyObject* x_obj = PyDict_GetItemString(kwds, "x");
            PyObject* y_obj = PyDict_GetItemString(kwds, "y");
            PyObject* pos_obj = PyDict_GetItemString(kwds, "pos");

            if (x_obj && y_obj) {
                if (extract_number(x_obj, out_x, nullptr) && extract_number(y_obj, out_y, nullptr)) {
                    return true;
                }
                if (PyErr_Occurred()) return false;
            }

            if (pos_obj) {
                if (extract_from_iterable(pos_obj, out_x, out_y, nullptr)) {
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

            if (extract_number(first, out_x, nullptr) && extract_number(second, out_y, nullptr)) {
                return true;
            }
            if (PyErr_Occurred()) return false;
        }

        // Try single iterable argument: func((x, y)) or func(Vector) or func([x, y])
        if (nargs == 1) {
            PyObject* first = PyTuple_GetItem(args, 0);
            if (extract_from_iterable(first, out_x, out_y, nullptr)) {
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
                if (extract_int(x_obj, out_x, nullptr) && extract_int(y_obj, out_y, nullptr)) {
                    return true;
                }
                if (PyErr_Occurred()) return false;
            }

            if (pos_obj) {
                if (extract_from_iterable_int(pos_obj, out_x, out_y, nullptr)) {
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

            if (extract_int(first, out_x, nullptr) && extract_int(second, out_y, nullptr)) {
                return true;
            }
            if (PyErr_Occurred()) return false;
        }

        // Try single iterable argument: func((x, y)) or func(Vector) or func([x, y])
        if (nargs == 1) {
            PyObject* first = PyTuple_GetItem(args, 0);
            if (extract_from_iterable_int(first, out_x, out_y, nullptr)) {
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

// A single cell coordinate (int, __index__ object, or a float, floored)
inline bool PyPosition_IntFromObject(PyObject* obj, int* out, const char* what) {
    return PyPositionHelper::IntFromObject(obj, out, what);
}

// Extract float position from a single Python object
// Usage: if (!PyPosition_FromObject(obj, &x, &y)) return NULL;
inline bool PyPosition_FromObject(PyObject* obj, float* x, float* y, const char* what = nullptr) {
    return PyPositionHelper::FromObject(obj, x, y, what);
}