#include "PyKey.h"
#include <sstream>
#include <cstring>

// Static storage for cached enum class reference
PyObject* PyKey::key_enum_class = nullptr;

// Key entries - maps enum name to SFML value and legacy string
struct KeyEntry {
    const char* name;       // Python enum name (UPPER_SNAKE_CASE)
    int value;              // Integer value (matches sf::Keyboard::Key)
    const char* legacy;     // Legacy string name for backwards compatibility
};

// Complete key table matching SFML's sf::Keyboard::Key enum
static const KeyEntry key_table[] = {
    // Letters (sf::Keyboard::A = 0 through sf::Keyboard::Z = 25)
    {"A", sf::Keyboard::A, "A"},
    {"B", sf::Keyboard::B, "B"},
    {"C", sf::Keyboard::C, "C"},
    {"D", sf::Keyboard::D, "D"},
    {"E", sf::Keyboard::E, "E"},
    {"F", sf::Keyboard::F, "F"},
    {"G", sf::Keyboard::G, "G"},
    {"H", sf::Keyboard::H, "H"},
    {"I", sf::Keyboard::I, "I"},
    {"J", sf::Keyboard::J, "J"},
    {"K", sf::Keyboard::K, "K"},
    {"L", sf::Keyboard::L, "L"},
    {"M", sf::Keyboard::M, "M"},
    {"N", sf::Keyboard::N, "N"},
    {"O", sf::Keyboard::O, "O"},
    {"P", sf::Keyboard::P, "P"},
    {"Q", sf::Keyboard::Q, "Q"},
    {"R", sf::Keyboard::R, "R"},
    {"S", sf::Keyboard::S, "S"},
    {"T", sf::Keyboard::T, "T"},
    {"U", sf::Keyboard::U, "U"},
    {"V", sf::Keyboard::V, "V"},
    {"W", sf::Keyboard::W, "W"},
    {"X", sf::Keyboard::X, "X"},
    {"Y", sf::Keyboard::Y, "Y"},
    {"Z", sf::Keyboard::Z, "Z"},

    // Number row (sf::Keyboard::Num0 = 26 through Num9 = 35)
    {"NUM_0", sf::Keyboard::Num0, "Num0"},
    {"NUM_1", sf::Keyboard::Num1, "Num1"},
    {"NUM_2", sf::Keyboard::Num2, "Num2"},
    {"NUM_3", sf::Keyboard::Num3, "Num3"},
    {"NUM_4", sf::Keyboard::Num4, "Num4"},
    {"NUM_5", sf::Keyboard::Num5, "Num5"},
    {"NUM_6", sf::Keyboard::Num6, "Num6"},
    {"NUM_7", sf::Keyboard::Num7, "Num7"},
    {"NUM_8", sf::Keyboard::Num8, "Num8"},
    {"NUM_9", sf::Keyboard::Num9, "Num9"},

    // Control keys
    {"ESCAPE", sf::Keyboard::Escape, "Escape"},
    {"LEFT_CONTROL", sf::Keyboard::LControl, "LControl"},
    {"LEFT_SHIFT", sf::Keyboard::LShift, "LShift"},
    {"LEFT_ALT", sf::Keyboard::LAlt, "LAlt"},
    {"LEFT_SYSTEM", sf::Keyboard::LSystem, "LSystem"},
    {"RIGHT_CONTROL", sf::Keyboard::RControl, "RControl"},
    {"RIGHT_SHIFT", sf::Keyboard::RShift, "RShift"},
    {"RIGHT_ALT", sf::Keyboard::RAlt, "RAlt"},
    {"RIGHT_SYSTEM", sf::Keyboard::RSystem, "RSystem"},
    {"MENU", sf::Keyboard::Menu, "Menu"},

    // Punctuation and symbols
    {"LEFT_BRACKET", sf::Keyboard::LBracket, "LBracket"},
    {"RIGHT_BRACKET", sf::Keyboard::RBracket, "RBracket"},
    {"SEMICOLON", sf::Keyboard::Semicolon, "Semicolon"},
    {"COMMA", sf::Keyboard::Comma, "Comma"},
    {"PERIOD", sf::Keyboard::Period, "Period"},
    {"APOSTROPHE", sf::Keyboard::Apostrophe, "Apostrophe"},
    {"SLASH", sf::Keyboard::Slash, "Slash"},
    {"BACKSLASH", sf::Keyboard::Backslash, "Backslash"},
    {"GRAVE", sf::Keyboard::Grave, "Grave"},
    {"EQUAL", sf::Keyboard::Equal, "Equal"},
    {"HYPHEN", sf::Keyboard::Hyphen, "Hyphen"},

    // Whitespace and editing
    {"SPACE", sf::Keyboard::Space, "Space"},
    {"ENTER", sf::Keyboard::Enter, "Enter"},
    {"BACKSPACE", sf::Keyboard::Backspace, "Backspace"},
    {"TAB", sf::Keyboard::Tab, "Tab"},

    // Navigation
    {"PAGE_UP", sf::Keyboard::PageUp, "PageUp"},
    {"PAGE_DOWN", sf::Keyboard::PageDown, "PageDown"},
    {"END", sf::Keyboard::End, "End"},
    {"HOME", sf::Keyboard::Home, "Home"},
    {"INSERT", sf::Keyboard::Insert, "Insert"},
    {"DELETE", sf::Keyboard::Delete, "Delete"},

    // Numpad operators
    {"ADD", sf::Keyboard::Add, "Add"},
    {"SUBTRACT", sf::Keyboard::Subtract, "Subtract"},
    {"MULTIPLY", sf::Keyboard::Multiply, "Multiply"},
    {"DIVIDE", sf::Keyboard::Divide, "Divide"},

    // Arrow keys
    {"LEFT", sf::Keyboard::Left, "Left"},
    {"RIGHT", sf::Keyboard::Right, "Right"},
    {"UP", sf::Keyboard::Up, "Up"},
    {"DOWN", sf::Keyboard::Down, "Down"},

    // Numpad numbers (sf::Keyboard::Numpad0 = 75 through Numpad9 = 84)
    {"NUMPAD_0", sf::Keyboard::Numpad0, "Numpad0"},
    {"NUMPAD_1", sf::Keyboard::Numpad1, "Numpad1"},
    {"NUMPAD_2", sf::Keyboard::Numpad2, "Numpad2"},
    {"NUMPAD_3", sf::Keyboard::Numpad3, "Numpad3"},
    {"NUMPAD_4", sf::Keyboard::Numpad4, "Numpad4"},
    {"NUMPAD_5", sf::Keyboard::Numpad5, "Numpad5"},
    {"NUMPAD_6", sf::Keyboard::Numpad6, "Numpad6"},
    {"NUMPAD_7", sf::Keyboard::Numpad7, "Numpad7"},
    {"NUMPAD_8", sf::Keyboard::Numpad8, "Numpad8"},
    {"NUMPAD_9", sf::Keyboard::Numpad9, "Numpad9"},

    // Function keys (sf::Keyboard::F1 = 85 through F15 = 99)
    {"F1", sf::Keyboard::F1, "F1"},
    {"F2", sf::Keyboard::F2, "F2"},
    {"F3", sf::Keyboard::F3, "F3"},
    {"F4", sf::Keyboard::F4, "F4"},
    {"F5", sf::Keyboard::F5, "F5"},
    {"F6", sf::Keyboard::F6, "F6"},
    {"F7", sf::Keyboard::F7, "F7"},
    {"F8", sf::Keyboard::F8, "F8"},
    {"F9", sf::Keyboard::F9, "F9"},
    {"F10", sf::Keyboard::F10, "F10"},
    {"F11", sf::Keyboard::F11, "F11"},
    {"F12", sf::Keyboard::F12, "F12"},
    {"F13", sf::Keyboard::F13, "F13"},
    {"F14", sf::Keyboard::F14, "F14"},
    {"F15", sf::Keyboard::F15, "F15"},

    // Misc
    {"PAUSE", sf::Keyboard::Pause, "Pause"},

    // Unknown key (for completeness)
    {"UNKNOWN", sf::Keyboard::Unknown, "Unknown"},
};

static const int NUM_KEY_ENTRIES = sizeof(key_table) / sizeof(key_table[0]);

const char* PyKey::to_legacy_string(sf::Keyboard::Key key) {
    for (int i = 0; i < NUM_KEY_ENTRIES; i++) {
        if (key_table[i].value == static_cast<int>(key)) {
            return key_table[i].legacy;
        }
    }
    return "Unknown";
}

sf::Keyboard::Key PyKey::from_legacy_string(const char* name) {
    for (int i = 0; i < NUM_KEY_ENTRIES; i++) {
        if (strcmp(key_table[i].legacy, name) == 0 ||
            strcmp(key_table[i].name, name) == 0) {
            return static_cast<sf::Keyboard::Key>(key_table[i].value);
        }
    }
    return sf::Keyboard::Unknown;
}

PyObject* PyKey::create_enum_class(PyObject* module) {
    // Build the enum definition dynamically from the table
    std::ostringstream code;
    code << "from enum import IntEnum\n\n";

    code << "class Key(IntEnum):\n";
    code << "    \"\"\"Enum representing keyboard keys.\n";
    code << "    \n";
    code << "    Values map to SFML's sf::Keyboard::Key enum.\n";
    code << "    \n";
    code << "    Categories:\n";
    code << "        Letters: A-Z\n";
    code << "        Numbers: NUM_0 through NUM_9 (top row)\n";
    code << "        Numpad: NUMPAD_0 through NUMPAD_9\n";
    code << "        Function: F1 through F15\n";
    code << "        Modifiers: LEFT_SHIFT, RIGHT_SHIFT, LEFT_CONTROL, etc.\n";
    code << "        Navigation: LEFT, RIGHT, UP, DOWN, HOME, END, PAGE_UP, PAGE_DOWN\n";
    code << "        Editing: ENTER, BACKSPACE, DELETE, INSERT, TAB, SPACE\n";
    code << "        Symbols: COMMA, PERIOD, SLASH, SEMICOLON, etc.\n";
    code << "    \n";
    code << "    These enum values compare equal to their legacy string equivalents\n";
    code << "    for backwards compatibility:\n";
    code << "        Key.ESCAPE == 'Escape'  # True\n";
    code << "        Key.LEFT_SHIFT == 'LShift'  # True\n";
    code << "    \"\"\"\n";

    // Add enum members
    for (int i = 0; i < NUM_KEY_ENTRIES; i++) {
        code << "    " << key_table[i].name << " = " << key_table[i].value << "\n";
    }

    // Add legacy names and custom methods AFTER class creation
    // (IntEnum doesn't allow dict attributes during class definition)
    code << "\n# Add legacy name mapping after class creation\n";
    code << "Key._legacy_names = {\n";
    for (int i = 0; i < NUM_KEY_ENTRIES; i++) {
        code << "    " << key_table[i].value << ": \"" << key_table[i].legacy << "\",\n";
    }
    code << "}\n\n";

    code << R"(
def _Key_eq(self, other):
    if isinstance(other, str):
        # Check enum name match (e.g., "ESCAPE")
        if self.name == other:
            return True
        # Check legacy name match (e.g., "Escape")
        legacy = type(self)._legacy_names.get(self.value)
        if legacy and legacy == other:
            return True
        return False
    # Fall back to int comparison for IntEnum
    return int.__eq__(int(self), other)

Key.__eq__ = _Key_eq
Key.__hash__ = lambda self: hash(int(self))
Key.__repr__ = lambda self: f"{type(self).__name__}.{self.name}"
Key.__str__ = lambda self: self.name
)";

    std::string code_str = code.str();

    // Create globals with builtins
    PyObject* globals = PyDict_New();
    if (!globals) return NULL;

    PyObject* builtins = PyEval_GetBuiltins();
    PyDict_SetItemString(globals, "__builtins__", builtins);

    PyObject* locals = PyDict_New();
    if (!locals) {
        Py_DECREF(globals);
        return NULL;
    }

    // Execute the code to create the enum
    PyObject* result = PyRun_String(code_str.c_str(), Py_file_input, globals, locals);
    if (!result) {
        Py_DECREF(globals);
        Py_DECREF(locals);
        return NULL;
    }
    Py_DECREF(result);

    // Get the Key class from locals
    PyObject* key_class = PyDict_GetItemString(locals, "Key");
    if (!key_class) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to create Key enum class");
        Py_DECREF(globals);
        Py_DECREF(locals);
        return NULL;
    }

    Py_INCREF(key_class);

    // Cache the reference for fast type checking
    key_enum_class = key_class;
    Py_INCREF(key_enum_class);

    // Add to module
    if (PyModule_AddObject(module, "Key", key_class) < 0) {
        Py_DECREF(key_class);
        Py_DECREF(globals);
        Py_DECREF(locals);
        key_enum_class = nullptr;
        return NULL;
    }

    Py_DECREF(globals);
    Py_DECREF(locals);

    return key_class;
}

int PyKey::from_arg(PyObject* arg, sf::Keyboard::Key* out_key) {
    // Accept Key enum member
    if (key_enum_class && PyObject_IsInstance(arg, key_enum_class)) {
        PyObject* value = PyObject_GetAttrString(arg, "value");
        if (!value) {
            return 0;
        }
        long val = PyLong_AsLong(value);
        Py_DECREF(value);
        if (val == -1 && PyErr_Occurred()) {
            return 0;
        }
        *out_key = static_cast<sf::Keyboard::Key>(val);
        return 1;
    }

    // Accept int
    if (PyLong_Check(arg)) {
        long val = PyLong_AsLong(arg);
        if (val == -1 && PyErr_Occurred()) {
            return 0;
        }
        if (val >= -1 && val < sf::Keyboard::KeyCount) {
            *out_key = static_cast<sf::Keyboard::Key>(val);
            return 1;
        }
        PyErr_Format(PyExc_ValueError,
            "Invalid Key value: %ld. Must be -1 (Unknown) to %d.", val, sf::Keyboard::KeyCount - 1);
        return 0;
    }

    // Accept string (both new and legacy names)
    if (PyUnicode_Check(arg)) {
        const char* name = PyUnicode_AsUTF8(arg);
        if (!name) {
            return 0;
        }

        // Check all entries for both name and legacy match
        for (int i = 0; i < NUM_KEY_ENTRIES; i++) {
            if (strcmp(name, key_table[i].name) == 0 ||
                strcmp(name, key_table[i].legacy) == 0) {
                *out_key = static_cast<sf::Keyboard::Key>(key_table[i].value);
                return 1;
            }
        }

        PyErr_Format(PyExc_ValueError,
            "Unknown Key: '%s'. Use Key enum members (e.g., Key.ESCAPE, Key.A) "
            "or legacy strings (e.g., 'Escape', 'A').", name);
        return 0;
    }

    PyErr_SetString(PyExc_TypeError,
        "Key must be mcrfpy.Key enum member, string, or int");
    return 0;
}
