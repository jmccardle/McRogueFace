#include "PyMouseButton.h"
#include <sstream>

// Static storage for cached enum class reference
PyObject* PyMouseButton::mouse_button_enum_class = nullptr;

// MouseButton entries - maps enum name to value and legacy string
struct MouseButtonEntry {
    const char* name;       // Python enum name (UPPER_SNAKE_CASE)
    int value;              // Integer value (matches sf::Mouse::Button)
    const char* legacy;     // Legacy string name for backwards compatibility
};

// Custom values for scroll wheel (beyond sf::Mouse::Button range)
static const int SCROLL_UP_VALUE = 10;
static const int SCROLL_DOWN_VALUE = 11;

static const MouseButtonEntry mouse_button_table[] = {
    {"LEFT", sf::Mouse::Left, "left"},
    {"RIGHT", sf::Mouse::Right, "right"},
    {"MIDDLE", sf::Mouse::Middle, "middle"},
    {"X1", sf::Mouse::XButton1, "x1"},
    {"X2", sf::Mouse::XButton2, "x2"},
    {"SCROLL_UP", SCROLL_UP_VALUE, "wheel_up"},
    {"SCROLL_DOWN", SCROLL_DOWN_VALUE, "wheel_down"},
};

static const int NUM_MOUSE_BUTTON_ENTRIES = sizeof(mouse_button_table) / sizeof(mouse_button_table[0]);

const char* PyMouseButton::to_legacy_string(sf::Mouse::Button button) {
    for (int i = 0; i < NUM_MOUSE_BUTTON_ENTRIES; i++) {
        if (mouse_button_table[i].value == static_cast<int>(button)) {
            return mouse_button_table[i].legacy;
        }
    }
    return "left";  // Default fallback
}

PyObject* PyMouseButton::create_enum_class(PyObject* module) {
    // Build the enum definition dynamically from the table
    std::ostringstream code;
    code << "from enum import IntEnum\n\n";

    code << "class MouseButton(IntEnum):\n";
    code << "    \"\"\"Enum representing mouse buttons and scroll wheel.\n";
    code << "    \n";
    code << "    Values:\n";
    code << "        LEFT: Left mouse button (legacy: 'left')\n";
    code << "        RIGHT: Right mouse button (legacy: 'right')\n";
    code << "        MIDDLE: Middle mouse button / scroll wheel click (legacy: 'middle')\n";
    code << "        X1: Extra mouse button 1 (legacy: 'x1')\n";
    code << "        X2: Extra mouse button 2 (legacy: 'x2')\n";
    code << "        SCROLL_UP: Scroll wheel up (legacy: 'wheel_up')\n";
    code << "        SCROLL_DOWN: Scroll wheel down (legacy: 'wheel_down')\n";
    code << "    \n";
    code << "    These enum values compare equal to their legacy string equivalents\n";
    code << "    for backwards compatibility:\n";
    code << "        MouseButton.LEFT == 'left'  # True\n";
    code << "        MouseButton.RIGHT == 'right'  # True\n";
    code << "        MouseButton.SCROLL_UP == 'wheel_up'  # True\n";
    code << "    \"\"\"\n";

    // Add enum members
    for (int i = 0; i < NUM_MOUSE_BUTTON_ENTRIES; i++) {
        code << "    " << mouse_button_table[i].name << " = " << mouse_button_table[i].value << "\n";
    }

    // Add legacy names and custom methods AFTER class creation
    // (IntEnum doesn't allow dict attributes during class definition)
    code << "\n# Add legacy name mapping after class creation\n";
    code << "MouseButton._legacy_names = {\n";
    for (int i = 0; i < NUM_MOUSE_BUTTON_ENTRIES; i++) {
        code << "    " << mouse_button_table[i].value << ": \"" << mouse_button_table[i].legacy << "\",\n";
    }
    code << "}\n\n";

    code << R"(
def _MouseButton_eq(self, other):
    if isinstance(other, str):
        # Check enum name match (e.g., "LEFT")
        if self.name == other:
            return True
        # Check legacy name match (e.g., "left")
        legacy = type(self)._legacy_names.get(self.value)
        if legacy and legacy == other:
            return True
        return False
    # Fall back to int comparison for IntEnum
    return int.__eq__(int(self), other)

MouseButton.__eq__ = _MouseButton_eq

def _MouseButton_ne(self, other):
    result = type(self).__eq__(self, other)
    if result is NotImplemented:
        return result
    return not result

MouseButton.__ne__ = _MouseButton_ne
MouseButton.__hash__ = lambda self: hash(int(self))
MouseButton.__repr__ = lambda self: f"{type(self).__name__}.{self.name}"
MouseButton.__str__ = lambda self: self.name
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

    // Get the MouseButton class from locals
    PyObject* mouse_button_class = PyDict_GetItemString(locals, "MouseButton");
    if (!mouse_button_class) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to create MouseButton enum class");
        Py_DECREF(globals);
        Py_DECREF(locals);
        return NULL;
    }

    Py_INCREF(mouse_button_class);

    // Cache the reference for fast type checking
    mouse_button_enum_class = mouse_button_class;
    Py_INCREF(mouse_button_enum_class);

    // Add to module
    if (PyModule_AddObject(module, "MouseButton", mouse_button_class) < 0) {
        Py_DECREF(mouse_button_class);
        Py_DECREF(globals);
        Py_DECREF(locals);
        mouse_button_enum_class = nullptr;
        return NULL;
    }

    Py_DECREF(globals);
    Py_DECREF(locals);

    return mouse_button_class;
}

int PyMouseButton::from_arg(PyObject* arg, sf::Mouse::Button* out_button) {
    // Accept MouseButton enum member
    if (mouse_button_enum_class && PyObject_IsInstance(arg, mouse_button_enum_class)) {
        PyObject* value = PyObject_GetAttrString(arg, "value");
        if (!value) {
            return 0;
        }
        long val = PyLong_AsLong(value);
        Py_DECREF(value);
        if (val == -1 && PyErr_Occurred()) {
            return 0;
        }
        // Valid values: 0-4 (mouse buttons) or 10-11 (scroll wheel)
        if ((val >= 0 && val <= 4) || val == SCROLL_UP_VALUE || val == SCROLL_DOWN_VALUE) {
            *out_button = static_cast<sf::Mouse::Button>(val);
            return 1;
        }
        PyErr_Format(PyExc_ValueError,
            "Invalid MouseButton value: %ld.", val);
        return 0;
    }

    // Accept int
    if (PyLong_Check(arg)) {
        long val = PyLong_AsLong(arg);
        if (val == -1 && PyErr_Occurred()) {
            return 0;
        }
        // Check if it's a valid mouse button (0-4) or scroll value (10-11)
        if ((val >= 0 && val <= 4) || val == SCROLL_UP_VALUE || val == SCROLL_DOWN_VALUE) {
            *out_button = static_cast<sf::Mouse::Button>(val);
            return 1;
        }
        PyErr_Format(PyExc_ValueError,
            "Invalid MouseButton value: %ld. Must be 0 (LEFT), 1 (RIGHT), 2 (MIDDLE), "
            "3 (X1), 4 (X2), 10 (SCROLL_UP), or 11 (SCROLL_DOWN).", val);
        return 0;
    }

    // Accept string (both new and legacy names)
    if (PyUnicode_Check(arg)) {
        const char* name = PyUnicode_AsUTF8(arg);
        if (!name) {
            return 0;
        }

        // Check all entries for both name and legacy match
        for (int i = 0; i < NUM_MOUSE_BUTTON_ENTRIES; i++) {
            if (strcmp(name, mouse_button_table[i].name) == 0 ||
                strcmp(name, mouse_button_table[i].legacy) == 0) {
                *out_button = static_cast<sf::Mouse::Button>(mouse_button_table[i].value);
                return 1;
            }
        }

        PyErr_Format(PyExc_ValueError,
            "Unknown MouseButton: '%s'. Use MouseButton.LEFT, MouseButton.RIGHT, "
            "MouseButton.MIDDLE, MouseButton.X1, MouseButton.X2, "
            "or legacy strings 'left', 'right', 'middle', 'x1', 'x2'.", name);
        return 0;
    }

    PyErr_SetString(PyExc_TypeError,
        "MouseButton must be mcrfpy.MouseButton enum member, string, or int");
    return 0;
}
