#pragma once
#include "Python.h"
#include "PyVector.h"
#include "McRFPy_API.h"

// Helper class for standardized position argument parsing across UI classes
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
    
    // Parse position from multiple formats for UI class constructors
    // Supports: (x, y), x=x, y=y, ((x,y)), (pos=(x,y)), (Vector), pos=Vector
    static ParseResult parse_position(PyObject* args, PyObject* kwds, 
                                      int* arg_index = nullptr) 
    {
        ParseResult result;
        float x = 0.0f, y = 0.0f;
        PyObject* pos_obj = nullptr;
        int start_index = arg_index ? *arg_index : 0;
        
        // Check for positional tuple (x, y) first
        if (!kwds && PyTuple_Size(args) > start_index + 1) {
            PyObject* first = PyTuple_GetItem(args, start_index);
            PyObject* second = PyTuple_GetItem(args, start_index + 1);
            
            // Check if both are numbers
            if ((PyFloat_Check(first) || PyLong_Check(first)) &&
                (PyFloat_Check(second) || PyLong_Check(second))) {
                x = PyFloat_Check(first) ? PyFloat_AsDouble(first) : PyLong_AsLong(first);
                y = PyFloat_Check(second) ? PyFloat_AsDouble(second) : PyLong_AsLong(second);
                result.x = x;
                result.y = y;
                result.has_position = true;
                if (arg_index) *arg_index += 2;
                return result;
            }
        }
        
        // Check for single positional argument that might be tuple or Vector
        if (!kwds && PyTuple_Size(args) > start_index) {
            PyObject* first = PyTuple_GetItem(args, start_index);
            PyVectorObject* vec = PyVector::from_arg(first);
            if (vec) {
                result.x = vec->data.x;
                result.y = vec->data.y;
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
                if ((PyFloat_Check(x_obj) || PyLong_Check(x_obj)) &&
                    (PyFloat_Check(y_obj) || PyLong_Check(y_obj))) {
                    result.x = PyFloat_Check(x_obj) ? PyFloat_AsDouble(x_obj) : PyLong_AsLong(x_obj);
                    result.y = PyFloat_Check(y_obj) ? PyFloat_AsDouble(y_obj) : PyLong_AsLong(y_obj);
                    result.has_position = true;
                    return result;
                }
            }
            
            if (pos_kw) {
                PyVectorObject* vec = PyVector::from_arg(pos_kw);
                if (vec) {
                    result.x = vec->data.x;
                    result.y = vec->data.y;
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
        
        // Check for positional tuple (x, y) first
        if (!kwds && PyTuple_Size(args) >= 2) {
            PyObject* first = PyTuple_GetItem(args, 0);
            PyObject* second = PyTuple_GetItem(args, 1);
            
            if (PyLong_Check(first) && PyLong_Check(second)) {
                result.x = PyLong_AsLong(first);
                result.y = PyLong_AsLong(second);
                result.has_position = true;
                return result;
            }
        }
        
        // Check for single tuple argument
        if (!kwds && PyTuple_Size(args) == 1) {
            PyObject* first = PyTuple_GetItem(args, 0);
            if (PyTuple_Check(first) && PyTuple_Size(first) == 2) {
                PyObject* x_obj = PyTuple_GetItem(first, 0);
                PyObject* y_obj = PyTuple_GetItem(first, 1);
                if (PyLong_Check(x_obj) && PyLong_Check(y_obj)) {
                    result.x = PyLong_AsLong(x_obj);
                    result.y = PyLong_AsLong(y_obj);
                    result.has_position = true;
                    return result;
                }
            }
        }
        
        // Try keyword arguments
        if (kwds) {
            PyObject* x_obj = PyDict_GetItemString(kwds, "x");
            PyObject* y_obj = PyDict_GetItemString(kwds, "y");
            PyObject* pos_obj = PyDict_GetItemString(kwds, "pos");
            
            if (x_obj && y_obj && PyLong_Check(x_obj) && PyLong_Check(y_obj)) {
                result.x = PyLong_AsLong(x_obj);
                result.y = PyLong_AsLong(y_obj);
                result.has_position = true;
                return result;
            }
            
            if (pos_obj && PyTuple_Check(pos_obj) && PyTuple_Size(pos_obj) == 2) {
                PyObject* x_val = PyTuple_GetItem(pos_obj, 0);
                PyObject* y_val = PyTuple_GetItem(pos_obj, 1);
                if (PyLong_Check(x_val) && PyLong_Check(y_val)) {
                    result.x = PyLong_AsLong(x_val);
                    result.y = PyLong_AsLong(y_val);
                    result.has_position = true;
                    return result;
                }
            }
        }
        
        return result;
    }
    
    // Error message helper
    static void set_position_error() {
        PyErr_SetString(PyExc_TypeError,
            "Position can be specified as: (x, y), x=x, y=y, ((x,y)), pos=(x,y), or pos=Vector");
    }
    
    static void set_position_int_error() {
        PyErr_SetString(PyExc_TypeError,
            "Position must be specified as: (x, y), x=x, y=y, ((x,y)), or pos=(x,y) with integer values");
    }
};