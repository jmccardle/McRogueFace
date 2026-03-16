#pragma once
#include "Common.h"
#include "Python.h"

// Module-level Behavior enum class (created at runtime using Python's IntEnum)
// Stored as a module attribute: mcrfpy.Behavior
//
// Values represent entity behavior types for grid.step() turn management.

class PyBehavior {
public:
    // Create the Behavior enum class and add to module
    // Returns the enum class (new reference), or NULL on error
    static PyObject* create_enum_class(PyObject* module);

    // Cached reference to the Behavior enum class for fast type checking
    static PyObject* behavior_enum_class;

    // Number of behavior types
    static const int NUM_BEHAVIORS = 11;
};
