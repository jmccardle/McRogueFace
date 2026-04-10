#pragma once
#include "Common.h"
#include "Python.h"

// Module-level MouseButton enum class (created at runtime using Python's IntEnum)
// Stored as a module attribute: mcrfpy.MouseButton
//
// Values map to sf::Mouse::Button:
//   LEFT = 0
//   RIGHT = 1
//   MIDDLE = 2
//   X1 = 3
//   X2 = 4

class PyMouseButton {
public:
    // Create the MouseButton enum class and add to module
    // Returns the enum class (new reference), or NULL on error
    static PyObject* create_enum_class(PyObject* module);

    // Helper to extract mouse button from Python arg
    // Accepts MouseButton enum, string (enum name), or int
    // Returns 1 on success, 0 on error (with exception set)
    static int from_arg(PyObject* arg, sf::Mouse::Button* out_button);

    // Cached reference to the MouseButton enum class for fast type checking
    static PyObject* mouse_button_enum_class;

    // Number of mouse buttons
    static const int NUM_MOUSE_BUTTONS = 5;
};
