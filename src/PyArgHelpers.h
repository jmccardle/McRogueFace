#pragma once
#include "Python.h"
#include "PyVector.h"
#include "PyColor.h"
#include <SFML/Graphics.hpp>
#include <string>

// Unified argument parsing helpers for Python API consistency
namespace PyArgHelpers {
    
    // Position in pixels (float)
    struct PositionResult { 
        float x, y; 
        bool valid; 
        const char* error;
    };
    
    // Size in pixels (float)
    struct SizeResult { 
        float w, h; 
        bool valid;
        const char* error;
    };
    
    // Grid position in tiles (float - for animation)
    struct GridPositionResult { 
        float grid_x, grid_y; 
        bool valid;
        const char* error;
    };
    
    // Grid size in tiles (int - can't have fractional tiles)
    struct GridSizeResult { 
        int grid_w, grid_h; 
        bool valid;
        const char* error;
    };
    
    // Color parsing
    struct ColorResult { 
        sf::Color color; 
        bool valid;
        const char* error;
    };
    
    // Helper to check if a keyword conflicts with positional args
    static bool hasConflict(PyObject* kwds, const char* key, bool has_positional) {
        if (!kwds || !has_positional) return false;
        PyObject* value = PyDict_GetItemString(kwds, key);
        return value != nullptr;
    }
    
    // Parse position with conflict detection
    static PositionResult parsePosition(PyObject* args, PyObject* kwds, int* next_arg = nullptr) {
        PositionResult result = {0.0f, 0.0f, false, nullptr};
        int start_idx = next_arg ? *next_arg : 0;
        bool has_positional = false;
        
        // Check for positional tuple argument first
        if (args && PyTuple_Size(args) > start_idx) {
            PyObject* first = PyTuple_GetItem(args, start_idx);
            
            // Is it a tuple/Vector?
            if (PyTuple_Check(first) && PyTuple_Size(first) == 2) {
                // Extract from tuple
                PyObject* x_obj = PyTuple_GetItem(first, 0);
                PyObject* y_obj = PyTuple_GetItem(first, 1);
                
                if ((PyFloat_Check(x_obj) || PyLong_Check(x_obj)) &&
                    (PyFloat_Check(y_obj) || PyLong_Check(y_obj))) {
                    result.x = PyFloat_Check(x_obj) ? PyFloat_AsDouble(x_obj) : PyLong_AsLong(x_obj);
                    result.y = PyFloat_Check(y_obj) ? PyFloat_AsDouble(y_obj) : PyLong_AsLong(y_obj);
                    result.valid = true;
                    has_positional = true;
                    if (next_arg) (*next_arg)++;
                }
            } else if (PyObject_TypeCheck(first, (PyTypeObject*)PyObject_GetAttrString(PyImport_ImportModule("mcrfpy"), "Vector"))) {
                // It's a Vector object
                PyVectorObject* vec = (PyVectorObject*)first;
                result.x = vec->data.x;
                result.y = vec->data.y;
                result.valid = true;
                has_positional = true;
                if (next_arg) (*next_arg)++;
            }
        }
        
        // Check for keyword conflicts
        if (has_positional) {
            if (hasConflict(kwds, "pos", true) || hasConflict(kwds, "x", true) || hasConflict(kwds, "y", true)) {
                result.valid = false;
                result.error = "position specified both positionally and by keyword";
                return result;
            }
        }
        
        // If no positional, try keywords
        if (!has_positional && kwds) {
            PyObject* pos_obj = PyDict_GetItemString(kwds, "pos");
            PyObject* x_obj = PyDict_GetItemString(kwds, "x");
            PyObject* y_obj = PyDict_GetItemString(kwds, "y");
            
            // Check for conflicts between pos and x/y
            if (pos_obj && (x_obj || y_obj)) {
                result.valid = false;
                result.error = "pos and x/y cannot both be specified";
                return result;
            }
            
            if (pos_obj) {
                // Parse pos keyword
                if (PyTuple_Check(pos_obj) && PyTuple_Size(pos_obj) == 2) {
                    PyObject* x_val = PyTuple_GetItem(pos_obj, 0);
                    PyObject* y_val = PyTuple_GetItem(pos_obj, 1);
                    
                    if ((PyFloat_Check(x_val) || PyLong_Check(x_val)) &&
                        (PyFloat_Check(y_val) || PyLong_Check(y_val))) {
                        result.x = PyFloat_Check(x_val) ? PyFloat_AsDouble(x_val) : PyLong_AsLong(x_val);
                        result.y = PyFloat_Check(y_val) ? PyFloat_AsDouble(y_val) : PyLong_AsLong(y_val);
                        result.valid = true;
                    }
                } else if (PyObject_TypeCheck(pos_obj, (PyTypeObject*)PyObject_GetAttrString(PyImport_ImportModule("mcrfpy"), "Vector"))) {
                    PyVectorObject* vec = (PyVectorObject*)pos_obj;
                    result.x = vec->data.x;
                    result.y = vec->data.y;
                    result.valid = true;
                }
            } else if (x_obj && y_obj) {
                // Parse x, y keywords
                if ((PyFloat_Check(x_obj) || PyLong_Check(x_obj)) &&
                    (PyFloat_Check(y_obj) || PyLong_Check(y_obj))) {
                    result.x = PyFloat_Check(x_obj) ? PyFloat_AsDouble(x_obj) : PyLong_AsLong(x_obj);
                    result.y = PyFloat_Check(y_obj) ? PyFloat_AsDouble(y_obj) : PyLong_AsLong(y_obj);
                    result.valid = true;
                }
            }
        }
        
        return result;
    }
    
    // Parse size with conflict detection
    static SizeResult parseSize(PyObject* args, PyObject* kwds, int* next_arg = nullptr) {
        SizeResult result = {0.0f, 0.0f, false, nullptr};
        int start_idx = next_arg ? *next_arg : 0;
        bool has_positional = false;
        
        // Check for positional tuple argument
        if (args && PyTuple_Size(args) > start_idx) {
            PyObject* first = PyTuple_GetItem(args, start_idx);
            
            if (PyTuple_Check(first) && PyTuple_Size(first) == 2) {
                PyObject* w_obj = PyTuple_GetItem(first, 0);
                PyObject* h_obj = PyTuple_GetItem(first, 1);
                
                if ((PyFloat_Check(w_obj) || PyLong_Check(w_obj)) &&
                    (PyFloat_Check(h_obj) || PyLong_Check(h_obj))) {
                    result.w = PyFloat_Check(w_obj) ? PyFloat_AsDouble(w_obj) : PyLong_AsLong(w_obj);
                    result.h = PyFloat_Check(h_obj) ? PyFloat_AsDouble(h_obj) : PyLong_AsLong(h_obj);
                    result.valid = true;
                    has_positional = true;
                    if (next_arg) (*next_arg)++;
                }
            }
        }
        
        // Check for keyword conflicts
        if (has_positional) {
            if (hasConflict(kwds, "size", true) || hasConflict(kwds, "w", true) || hasConflict(kwds, "h", true)) {
                result.valid = false;
                result.error = "size specified both positionally and by keyword";
                return result;
            }
        }
        
        // If no positional, try keywords
        if (!has_positional && kwds) {
            PyObject* size_obj = PyDict_GetItemString(kwds, "size");
            PyObject* w_obj = PyDict_GetItemString(kwds, "w");
            PyObject* h_obj = PyDict_GetItemString(kwds, "h");
            
            // Check for conflicts between size and w/h
            if (size_obj && (w_obj || h_obj)) {
                result.valid = false;
                result.error = "size and w/h cannot both be specified";
                return result;
            }
            
            if (size_obj) {
                // Parse size keyword
                if (PyTuple_Check(size_obj) && PyTuple_Size(size_obj) == 2) {
                    PyObject* w_val = PyTuple_GetItem(size_obj, 0);
                    PyObject* h_val = PyTuple_GetItem(size_obj, 1);
                    
                    if ((PyFloat_Check(w_val) || PyLong_Check(w_val)) &&
                        (PyFloat_Check(h_val) || PyLong_Check(h_val))) {
                        result.w = PyFloat_Check(w_val) ? PyFloat_AsDouble(w_val) : PyLong_AsLong(w_val);
                        result.h = PyFloat_Check(h_val) ? PyFloat_AsDouble(h_val) : PyLong_AsLong(h_val);
                        result.valid = true;
                    }
                }
            } else if (w_obj && h_obj) {
                // Parse w, h keywords
                if ((PyFloat_Check(w_obj) || PyLong_Check(w_obj)) &&
                    (PyFloat_Check(h_obj) || PyLong_Check(h_obj))) {
                    result.w = PyFloat_Check(w_obj) ? PyFloat_AsDouble(w_obj) : PyLong_AsLong(w_obj);
                    result.h = PyFloat_Check(h_obj) ? PyFloat_AsDouble(h_obj) : PyLong_AsLong(h_obj);
                    result.valid = true;
                }
            }
        }
        
        return result;
    }
    
    // Parse grid position (float for smooth animation)
    static GridPositionResult parseGridPosition(PyObject* args, PyObject* kwds, int* next_arg = nullptr) {
        GridPositionResult result = {0.0f, 0.0f, false, nullptr};
        int start_idx = next_arg ? *next_arg : 0;
        bool has_positional = false;
        
        // Check for positional tuple argument
        if (args && PyTuple_Size(args) > start_idx) {
            PyObject* first = PyTuple_GetItem(args, start_idx);
            
            if (PyTuple_Check(first) && PyTuple_Size(first) == 2) {
                PyObject* x_obj = PyTuple_GetItem(first, 0);
                PyObject* y_obj = PyTuple_GetItem(first, 1);
                
                if ((PyFloat_Check(x_obj) || PyLong_Check(x_obj)) &&
                    (PyFloat_Check(y_obj) || PyLong_Check(y_obj))) {
                    result.grid_x = PyFloat_Check(x_obj) ? PyFloat_AsDouble(x_obj) : PyLong_AsLong(x_obj);
                    result.grid_y = PyFloat_Check(y_obj) ? PyFloat_AsDouble(y_obj) : PyLong_AsLong(y_obj);
                    result.valid = true;
                    has_positional = true;
                    if (next_arg) (*next_arg)++;
                }
            }
        }
        
        // Check for keyword conflicts
        if (has_positional) {
            if (hasConflict(kwds, "grid_pos", true) || hasConflict(kwds, "grid_x", true) || hasConflict(kwds, "grid_y", true)) {
                result.valid = false;
                result.error = "grid position specified both positionally and by keyword";
                return result;
            }
        }
        
        // If no positional, try keywords
        if (!has_positional && kwds) {
            PyObject* grid_pos_obj = PyDict_GetItemString(kwds, "grid_pos");
            PyObject* grid_x_obj = PyDict_GetItemString(kwds, "grid_x");
            PyObject* grid_y_obj = PyDict_GetItemString(kwds, "grid_y");
            
            // Check for conflicts between grid_pos and grid_x/grid_y
            if (grid_pos_obj && (grid_x_obj || grid_y_obj)) {
                result.valid = false;
                result.error = "grid_pos and grid_x/grid_y cannot both be specified";
                return result;
            }
            
            if (grid_pos_obj) {
                // Parse grid_pos keyword
                if (PyTuple_Check(grid_pos_obj) && PyTuple_Size(grid_pos_obj) == 2) {
                    PyObject* x_val = PyTuple_GetItem(grid_pos_obj, 0);
                    PyObject* y_val = PyTuple_GetItem(grid_pos_obj, 1);
                    
                    if ((PyFloat_Check(x_val) || PyLong_Check(x_val)) &&
                        (PyFloat_Check(y_val) || PyLong_Check(y_val))) {
                        result.grid_x = PyFloat_Check(x_val) ? PyFloat_AsDouble(x_val) : PyLong_AsLong(x_val);
                        result.grid_y = PyFloat_Check(y_val) ? PyFloat_AsDouble(y_val) : PyLong_AsLong(y_val);
                        result.valid = true;
                    }
                }
            } else if (grid_x_obj && grid_y_obj) {
                // Parse grid_x, grid_y keywords
                if ((PyFloat_Check(grid_x_obj) || PyLong_Check(grid_x_obj)) &&
                    (PyFloat_Check(grid_y_obj) || PyLong_Check(grid_y_obj))) {
                    result.grid_x = PyFloat_Check(grid_x_obj) ? PyFloat_AsDouble(grid_x_obj) : PyLong_AsLong(grid_x_obj);
                    result.grid_y = PyFloat_Check(grid_y_obj) ? PyFloat_AsDouble(grid_y_obj) : PyLong_AsLong(grid_y_obj);
                    result.valid = true;
                }
            }
        }
        
        return result;
    }
    
    // Parse grid size (int - no fractional tiles)
    static GridSizeResult parseGridSize(PyObject* args, PyObject* kwds, int* next_arg = nullptr) {
        GridSizeResult result = {0, 0, false, nullptr};
        int start_idx = next_arg ? *next_arg : 0;
        bool has_positional = false;
        
        // Check for positional tuple argument
        if (args && PyTuple_Size(args) > start_idx) {
            PyObject* first = PyTuple_GetItem(args, start_idx);
            
            if (PyTuple_Check(first) && PyTuple_Size(first) == 2) {
                PyObject* w_obj = PyTuple_GetItem(first, 0);
                PyObject* h_obj = PyTuple_GetItem(first, 1);
                
                if (PyLong_Check(w_obj) && PyLong_Check(h_obj)) {
                    result.grid_w = PyLong_AsLong(w_obj);
                    result.grid_h = PyLong_AsLong(h_obj);
                    result.valid = true;
                    has_positional = true;
                    if (next_arg) (*next_arg)++;
                } else {
                    result.valid = false;
                    result.error = "grid size must be specified with integers";
                    return result;
                }
            }
        }
        
        // Check for keyword conflicts
        if (has_positional) {
            if (hasConflict(kwds, "grid_size", true) || hasConflict(kwds, "grid_w", true) || hasConflict(kwds, "grid_h", true)) {
                result.valid = false;
                result.error = "grid size specified both positionally and by keyword";
                return result;
            }
        }
        
        // If no positional, try keywords
        if (!has_positional && kwds) {
            PyObject* grid_size_obj = PyDict_GetItemString(kwds, "grid_size");
            PyObject* grid_w_obj = PyDict_GetItemString(kwds, "grid_w");
            PyObject* grid_h_obj = PyDict_GetItemString(kwds, "grid_h");
            
            // Check for conflicts between grid_size and grid_w/grid_h
            if (grid_size_obj && (grid_w_obj || grid_h_obj)) {
                result.valid = false;
                result.error = "grid_size and grid_w/grid_h cannot both be specified";
                return result;
            }
            
            if (grid_size_obj) {
                // Parse grid_size keyword
                if (PyTuple_Check(grid_size_obj) && PyTuple_Size(grid_size_obj) == 2) {
                    PyObject* w_val = PyTuple_GetItem(grid_size_obj, 0);
                    PyObject* h_val = PyTuple_GetItem(grid_size_obj, 1);
                    
                    if (PyLong_Check(w_val) && PyLong_Check(h_val)) {
                        result.grid_w = PyLong_AsLong(w_val);
                        result.grid_h = PyLong_AsLong(h_val);
                        result.valid = true;
                    } else {
                        result.valid = false;
                        result.error = "grid size must be specified with integers";
                        return result;
                    }
                }
            } else if (grid_w_obj && grid_h_obj) {
                // Parse grid_w, grid_h keywords
                if (PyLong_Check(grid_w_obj) && PyLong_Check(grid_h_obj)) {
                    result.grid_w = PyLong_AsLong(grid_w_obj);
                    result.grid_h = PyLong_AsLong(grid_h_obj);
                    result.valid = true;
                } else {
                    result.valid = false;
                    result.error = "grid size must be specified with integers";
                    return result;
                }
            }
        }
        
        return result;
    }
    
    // Parse color using existing PyColor infrastructure
    static ColorResult parseColor(PyObject* obj, const char* param_name = nullptr) {
        ColorResult result = {sf::Color::White, false, nullptr};
        
        if (!obj) {
            return result;
        }
        
        // Use existing PyColor::from_arg which handles tuple/Color conversion
        auto py_color = PyColor::from_arg(obj);
        if (py_color) {
            result.color = py_color->data;
            result.valid = true;
        } else {
            result.valid = false;
            std::string error_msg = param_name 
                ? std::string(param_name) + " must be a color tuple (r,g,b) or (r,g,b,a)"
                : "Invalid color format - expected tuple (r,g,b) or (r,g,b,a)";
            result.error = error_msg.c_str();
        }
        
        return result;
    }
    
    // Helper to validate a texture object
    static bool isValidTexture(PyObject* obj) {
        if (!obj) return false;
        PyObject* texture_type = PyObject_GetAttrString(PyImport_ImportModule("mcrfpy"), "Texture");
        bool is_texture = PyObject_IsInstance(obj, texture_type);
        Py_DECREF(texture_type);
        return is_texture;
    }
    
    // Helper to validate a click handler
    static bool isValidClickHandler(PyObject* obj) {
        return obj && PyCallable_Check(obj);
    }
}