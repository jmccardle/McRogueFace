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

    // #428 - The one conversion from an engine mouse action name ("left", "right",
    // "middle", "x1", "x2", "wheel_up", "wheel_down", as registered by PyScene) to
    // a MouseButton member. NEW reference, or nullptr with ValueError set for an
    // unknown name. Every dispatcher uses this; a private copy of the table is how
    // grid cells came to report scrolling as X1/X2.
    static PyObject* from_action_name(const std::string& name);

    // #428 - The reverse, for automation's button="..." strings: a physical button
    // ("left", "right", "middle", "x1", "x2"). Returns 1, or 0 with ValueError set
    // for anything else (a wheel name included: scrolling is automation.scroll()).
    static int button_from_action_name(const char* name, sf::Mouse::Button* out_button);

    // Cached reference to the MouseButton enum class for fast type checking
    static PyObject* mouse_button_enum_class;
    // #468: drop mouse_button_enum_class and the memoized members.
    static void release_statics();

    // Number of mouse buttons
    static const int NUM_MOUSE_BUTTONS = 5;
};
