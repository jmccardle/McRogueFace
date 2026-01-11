#pragma once
#include "Common.h"
#include "Python.h"

// Module-level InputState enum class (created at runtime using Python's IntEnum)
// Stored as a module attribute: mcrfpy.InputState
//
// Values:
//   PRESSED = 0   (corresponds to "start" in legacy API)
//   RELEASED = 1  (corresponds to "end" in legacy API)
//
// The enum compares equal to both its name ("PRESSED") and legacy string ("start")

class PyInputState {
public:
    // Create the InputState enum class and add to module
    // Returns the enum class (new reference), or NULL on error
    static PyObject* create_enum_class(PyObject* module);

    // Helper to extract input state from Python arg
    // Accepts InputState enum, string (for backwards compatibility), int, or None
    // Returns 1 on success, 0 on error (with exception set)
    // out_pressed is set to true for PRESSED/start, false for RELEASED/end
    static int from_arg(PyObject* arg, bool* out_pressed);

    // Convert bool to legacy string name (for passing to callbacks)
    static const char* to_legacy_string(bool pressed);

    // Cached reference to the InputState enum class for fast type checking
    static PyObject* input_state_enum_class;

    // Number of input states
    static const int NUM_INPUT_STATES = 2;
};
