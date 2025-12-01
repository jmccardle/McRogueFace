#pragma once
#include "Common.h"
#include "Python.h"
#include <libtcod.h>

// Module-level FOV enum class (created at runtime using Python's IntEnum)
// Stored as a module attribute: mcrfpy.FOV

class PyFOV {
public:
    // Create the FOV enum class and add to module
    // Returns the enum class (new reference), or NULL on error
    static PyObject* create_enum_class(PyObject* module);

    // Helper to extract algorithm from Python arg (accepts FOV enum, int, or None)
    // Returns 1 on success, 0 on error (with exception set)
    // If arg is None, sets *out_algo to the default (FOV_BASIC) and sets *was_none to true
    static int from_arg(PyObject* arg, TCOD_fov_algorithm_t* out_algo, bool* was_none = nullptr);

    // Cached reference to the FOV enum class for fast type checking
    static PyObject* fov_enum_class;
};
