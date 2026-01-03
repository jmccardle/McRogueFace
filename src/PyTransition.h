#pragma once
#include "Common.h"
#include "Python.h"
#include "SceneTransition.h"

// Module-level Transition enum class (created at runtime using Python's IntEnum)
// Stored as a module attribute: mcrfpy.Transition

class PyTransition {
public:
    // Create the Transition enum class and add to module
    // Returns the enum class (new reference), or NULL on error
    static PyObject* create_enum_class(PyObject* module);

    // Helper to extract transition type from Python arg (accepts Transition enum, int, or None)
    // Returns 1 on success, 0 on error (with exception set)
    // If arg is None, sets *out_type to the default and sets *was_none to true
    static int from_arg(PyObject* arg, TransitionType* out_type, bool* was_none = nullptr);

    // Convert TransitionType to Python enum member
    static PyObject* to_python(TransitionType type);

    // Cached reference to the Transition enum class for fast type checking
    static PyObject* transition_enum_class;

    // Module-level defaults
    static TransitionType default_transition;
    static float default_duration;
};
