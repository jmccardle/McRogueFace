#pragma once
#include "Common.h"
#include "Python.h"
#include "Animation.h"

// Module-level Easing enum class (created at runtime using Python's IntEnum)
// Stored as a module attribute: mcrfpy.Easing

class PyEasing {
public:
    // Create the Easing enum class and add to module
    // Returns the enum class (new reference), or NULL on error
    static PyObject* create_enum_class(PyObject* module);

    // Helper to extract easing function from Python arg
    // Accepts Easing enum, string (for backwards compatibility), int, or None
    // Returns 1 on success, 0 on error (with exception set)
    // If arg is None, sets *out_func to linear and sets *was_none to true
    static int from_arg(PyObject* arg, EasingFunction* out_func, bool* was_none = nullptr);

    // Convert easing enum value to string name
    static const char* easing_name(int value);

    // Cached reference to the Easing enum class for fast type checking
    static PyObject* easing_enum_class;

    // Number of easing functions
    static const int NUM_EASING_FUNCTIONS = 32;
};
