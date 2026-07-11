#pragma once
#include "Common.h"
#include "Python.h"

// Module-level InputState enum class (created at runtime using Python's IntEnum)
// Stored as a module attribute: mcrfpy.InputState
//
// Values:
//   PRESSED = 0
//   RELEASED = 1

class PyInputState {
public:
    // Create the InputState enum class and add to module
    // Returns the enum class (new reference), or NULL on error
    static PyObject* create_enum_class(PyObject* module);

    // Helper to extract input state from Python arg
    // Accepts InputState enum, string (enum name), or int
    // Returns 1 on success, 0 on error (with exception set)
    // out_pressed is set to true for PRESSED, false for RELEASED
    static int from_arg(PyObject* arg, bool* out_pressed);

    // Cached reference to the InputState enum class for fast type checking
    static PyObject* input_state_enum_class;

    // #344 - Return the cached InputState enum member for a value (0=PRESSED,
    // 1=RELEASED) as a NEW reference. Members are memoized for the interpreter
    // lifetime so per-event dispatch avoids EnumMeta.__call__. Returns nullptr
    // with an exception set on failure. Caller owns the returned reference.
    static PyObject* get_enum_member(int value);

    // Number of input states
    static const int NUM_INPUT_STATES = 2;
};
