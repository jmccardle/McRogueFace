#pragma once
#include "Common.h"
#include "Python.h"
#include <cstdint>

// Module-level Perspective enum class (created at runtime using Python's IntEnum)
// Stored as a module attribute: mcrfpy.Perspective
//
// Values:
//   UNKNOWN    = 0   (never seen)
//   DISCOVERED = 1   (seen before, not currently visible)
//   VISIBLE    = 2   (in current FOV)
//
// Used as the value space for UIEntity.perspective_map (issue #294).
class PyPerspective {
public:
    // Create the Perspective enum class and add to module.
    // Returns the enum class (new reference), or NULL on error.
    static PyObject* create_enum_class(PyObject* module);

    // Helper to extract a Perspective value from a Python arg.
    // Accepts Perspective enum member, string (enum name), or int 0/1/2.
    // Returns 1 on success, 0 on error (with exception set).
    static int from_arg(PyObject* arg, uint8_t* out_value);

    // Cached reference to the Perspective enum class for fast type checking.
    static PyObject* perspective_enum_class;

    static const int NUM_PERSPECTIVE_STATES = 3;
    static const uint8_t UNKNOWN = 0;
    static const uint8_t DISCOVERED = 1;
    static const uint8_t VISIBLE = 2;
};
