#include "PyInputState.h"
#include <sstream>

// Static storage for cached enum class reference
PyObject* PyInputState::input_state_enum_class = nullptr;

// InputState entries - maps enum name to value and legacy string
struct InputStateEntry {
    const char* name;       // Python enum name (UPPER_SNAKE_CASE)
    int value;              // Integer value
    const char* legacy;     // Legacy string name for backwards compatibility
};

static const InputStateEntry input_state_table[] = {
    {"PRESSED", 0, "start"},
    {"RELEASED", 1, "end"},
};

static const int NUM_INPUT_STATE_ENTRIES = sizeof(input_state_table) / sizeof(input_state_table[0]);

const char* PyInputState::to_legacy_string(bool pressed) {
    return pressed ? "start" : "end";
}

PyObject* PyInputState::create_enum_class(PyObject* module) {
    // Build the enum definition dynamically from the table
    std::ostringstream code;
    code << "from enum import IntEnum\n\n";

    code << "class InputState(IntEnum):\n";
    code << "    \"\"\"Enum representing input event states (pressed/released).\n";
    code << "    \n";
    code << "    Values:\n";
    code << "        PRESSED: Key or button was pressed (legacy: 'start')\n";
    code << "        RELEASED: Key or button was released (legacy: 'end')\n";
    code << "    \n";
    code << "    These enum values compare equal to their legacy string equivalents\n";
    code << "    for backwards compatibility:\n";
    code << "        InputState.PRESSED == 'start'  # True\n";
    code << "        InputState.RELEASED == 'end'   # True\n";
    code << "    \"\"\"\n";

    // Add enum members
    for (int i = 0; i < NUM_INPUT_STATE_ENTRIES; i++) {
        code << "    " << input_state_table[i].name << " = " << input_state_table[i].value << "\n";
    }

    // Add legacy names and custom methods AFTER class creation
    // (IntEnum doesn't allow dict attributes during class definition)
    code << "\n# Add legacy name mapping after class creation\n";
    code << "InputState._legacy_names = {\n";
    for (int i = 0; i < NUM_INPUT_STATE_ENTRIES; i++) {
        code << "    " << input_state_table[i].value << ": \"" << input_state_table[i].legacy << "\",\n";
    }
    code << "}\n\n";

    code << R"(
def _InputState_eq(self, other):
    if isinstance(other, str):
        # Check enum name match (e.g., "PRESSED")
        if self.name == other:
            return True
        # Check legacy name match (e.g., "start")
        legacy = type(self)._legacy_names.get(self.value)
        if legacy and legacy == other:
            return True
        return False
    # Fall back to int comparison for IntEnum
    return int.__eq__(int(self), other)

InputState.__eq__ = _InputState_eq

def _InputState_ne(self, other):
    result = type(self).__eq__(self, other)
    if result is NotImplemented:
        return result
    return not result

InputState.__ne__ = _InputState_ne
InputState.__hash__ = lambda self: hash(int(self))
InputState.__repr__ = lambda self: f"{type(self).__name__}.{self.name}"
InputState.__str__ = lambda self: self.name
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

    // Get the InputState class from locals
    PyObject* input_state_class = PyDict_GetItemString(locals, "InputState");
    if (!input_state_class) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to create InputState enum class");
        Py_DECREF(globals);
        Py_DECREF(locals);
        return NULL;
    }

    Py_INCREF(input_state_class);

    // Cache the reference for fast type checking
    input_state_enum_class = input_state_class;
    Py_INCREF(input_state_enum_class);

    // Add to module
    if (PyModule_AddObject(module, "InputState", input_state_class) < 0) {
        Py_DECREF(input_state_class);
        Py_DECREF(globals);
        Py_DECREF(locals);
        input_state_enum_class = nullptr;
        return NULL;
    }

    Py_DECREF(globals);
    Py_DECREF(locals);

    return input_state_class;
}

int PyInputState::from_arg(PyObject* arg, bool* out_pressed) {
    // Accept InputState enum member
    if (input_state_enum_class && PyObject_IsInstance(arg, input_state_enum_class)) {
        PyObject* value = PyObject_GetAttrString(arg, "value");
        if (!value) {
            return 0;
        }
        long val = PyLong_AsLong(value);
        Py_DECREF(value);
        if (val == -1 && PyErr_Occurred()) {
            return 0;
        }
        *out_pressed = (val == 0);  // PRESSED = 0
        return 1;
    }

    // Accept int
    if (PyLong_Check(arg)) {
        long val = PyLong_AsLong(arg);
        if (val == -1 && PyErr_Occurred()) {
            return 0;
        }
        if (val == 0 || val == 1) {
            *out_pressed = (val == 0);
            return 1;
        }
        PyErr_Format(PyExc_ValueError,
            "Invalid InputState value: %ld. Must be 0 (PRESSED) or 1 (RELEASED).", val);
        return 0;
    }

    // Accept string (both new and legacy names)
    if (PyUnicode_Check(arg)) {
        const char* name = PyUnicode_AsUTF8(arg);
        if (!name) {
            return 0;
        }

        // Check all entries for both name and legacy match
        for (int i = 0; i < NUM_INPUT_STATE_ENTRIES; i++) {
            if (strcmp(name, input_state_table[i].name) == 0 ||
                strcmp(name, input_state_table[i].legacy) == 0) {
                *out_pressed = (input_state_table[i].value == 0);
                return 1;
            }
        }

        PyErr_Format(PyExc_ValueError,
            "Unknown InputState: '%s'. Use InputState.PRESSED, InputState.RELEASED, "
            "or legacy strings 'start', 'end'.", name);
        return 0;
    }

    PyErr_SetString(PyExc_TypeError,
        "InputState must be mcrfpy.InputState enum member, string, or int");
    return 0;
}
