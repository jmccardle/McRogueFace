#pragma once
#include "Common.h"
#include "Python.h"

// Module-level Key enum class (created at runtime using Python's IntEnum)
// Stored as a module attribute: mcrfpy.Key
//
// Values map to sf::Keyboard::Key enum values.
//
// Naming convention:
//   - Letters: A, B, C, ... Z
//   - Numbers: NUM_0, NUM_1, ... NUM_9 (top row)
//   - Numpad: NUMPAD_0, NUMPAD_1, ... NUMPAD_9
//   - Function keys: F1, F2, ... F15
//   - Modifiers: LEFT_SHIFT, RIGHT_SHIFT, LEFT_CONTROL, RIGHT_CONTROL, etc.
//   - Navigation: LEFT, RIGHT, UP, DOWN, HOME, END, PAGE_UP, PAGE_DOWN
//   - Special: ESCAPE, ENTER, SPACE, TAB, BACKSPACE, DELETE, INSERT, PAUSE

class PyKey {
public:
    // Create the Key enum class and add to module
    // Returns the enum class (new reference), or NULL on error
    static PyObject* create_enum_class(PyObject* module);

    // Helper to extract key from Python arg
    // Accepts Key enum, string (enum name), or int
    // Returns 1 on success, 0 on error (with exception set)
    static int from_arg(PyObject* arg, sf::Keyboard::Key* out_key);

    // Convert string name to sf::Keyboard::Key (used by C++ event dispatch)
    // Returns sf::Keyboard::Unknown if not found
    static sf::Keyboard::Key from_legacy_string(const char* name);

    // Cached reference to the Key enum class for fast type checking
    static PyObject* key_enum_class;

    // Number of keys (matches sf::Keyboard::KeyCount)
    static const int NUM_KEYS = sf::Keyboard::KeyCount;
};
