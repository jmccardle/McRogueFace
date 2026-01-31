#pragma once
#include "Common.h"
#include "Python.h"

// Module-level MouseButton enum class (created at runtime using Python's IntEnum)
// Stored as a module attribute: mcrfpy.MouseButton
//
// Values map to sf::Mouse::Button:
//   LEFT = 0    (corresponds to "left" in legacy API)
//   RIGHT = 1   (corresponds to "right" in legacy API)
//   MIDDLE = 2  (corresponds to "middle" in legacy API)
//   X1 = 3      (extra button 1)
//   X2 = 4      (extra button 2)
//
// The enum compares equal to both its name ("LEFT") and legacy string ("left")

class PyMouseButton {
public:
    // Create the MouseButton enum class and add to module
    // Returns the enum class (new reference), or NULL on error
    static PyObject* create_enum_class(PyObject* module);

    // Helper to extract mouse button from Python arg
    // Accepts MouseButton enum, string (for backwards compatibility), int, or None
    // Returns 1 on success, 0 on error (with exception set)
    static int from_arg(PyObject* arg, sf::Mouse::Button* out_button);

    // Convert sf::Mouse::Button to legacy string name (for passing to callbacks)
    static const char* to_legacy_string(sf::Mouse::Button button);

    // Cached reference to the MouseButton enum class for fast type checking
    static PyObject* mouse_button_enum_class;

    // Number of mouse buttons
    static const int NUM_MOUSE_BUTTONS = 5;
};
