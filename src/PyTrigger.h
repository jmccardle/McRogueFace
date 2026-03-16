#pragma once
#include "Common.h"
#include "Python.h"

// Module-level Trigger enum class (created at runtime using Python's IntEnum)
// Stored as a module attribute: mcrfpy.Trigger
//
// Values represent trigger types passed to entity step() callbacks.

class PyTrigger {
public:
    // Create the Trigger enum class and add to module
    // Returns the enum class (new reference), or NULL on error
    static PyObject* create_enum_class(PyObject* module);

    // Cached reference to the Trigger enum class for fast type checking
    static PyObject* trigger_enum_class;

    // Number of trigger types
    static const int NUM_TRIGGERS = 3;
};
