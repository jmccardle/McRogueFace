#pragma once
#include "Common.h"
#include "Python.h"
#include <SFML/Window/Keyboard.hpp>

// Module-level Key enum class (created at runtime using Python's IntEnum)
// Stored as a module attribute: mcrfpy.Key
//
// Values map to sf::Keyboard::Key enum values.
// The enum compares equal to both its name ("ESCAPE") and legacy string ("Escape")
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
    // Accepts Key enum, string (for backwards compatibility), int, or None
    // Returns 1 on success, 0 on error (with exception set)
    static int from_arg(PyObject* arg, sf::Keyboard::Key* out_key);

    // Convert sf::Keyboard::Key to legacy string name (for passing to callbacks)
    static const char* to_legacy_string(sf::Keyboard::Key key);

    // Convert legacy string to sf::Keyboard::Key
    // Returns sf::Keyboard::Unknown if not found
    static sf::Keyboard::Key from_legacy_string(const char* name);

    // Cached reference to the Key enum class for fast type checking
    static PyObject* key_enum_class;

    // Number of keys (matches sf::Keyboard::KeyCount)
    static const int NUM_KEYS = sf::Keyboard::KeyCount;
};
