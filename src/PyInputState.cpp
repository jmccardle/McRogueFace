#include "PyInputState.h"
#include <sstream>

// Static storage for cached enum class reference
PyObject* PyInputState::input_state_enum_class = nullptr;

// InputState entries - maps enum name to value
struct InputStateEntry {
    const char* name;       // Python enum name (UPPER_SNAKE_CASE)
    int value;              // Integer value
};

static const InputStateEntry input_state_table[] = {
    {"PRESSED", 0},
    {"RELEASED", 1},
};

static const int NUM_INPUT_STATE_ENTRIES = sizeof(input_state_table) / sizeof(input_state_table[0]);

PyObject* PyInputState::create_enum_class(PyObject* module) {
    // Build the enum definition dynamically from the table
    std::ostringstream code;
    code << "from enum import IntEnum\n\n";

    code << "class InputState(IntEnum):\n";
    code << "    \"\"\"Enum representing input event states (pressed/released).\n";
    code << "    \n";
    code << "    Values:\n";
    code << "        PRESSED: Key or button was pressed\n";
    code << "        RELEASED: Key or button was released\n";
    code << "    \"\"\"\n";

    // Add enum members
    for (int i = 0; i < NUM_INPUT_STATE_ENTRIES; i++) {
        code << "    " << input_state_table[i].name << " = " << input_state_table[i].value << "\n";
    }

    code << "\n";
    code << "InputState.__hash__ = lambda self: hash(int(self))\n";
    code << "InputState.__repr__ = lambda self: f\"{type(self).__name__}.{self.name}\"\n";
    code << "InputState.__str__ = lambda self: self.name\n";

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

    // Accept string (enum name only)
    if (PyUnicode_Check(arg)) {
        const char* name = PyUnicode_AsUTF8(arg);
        if (!name) {
            return 0;
        }

        for (int i = 0; i < NUM_INPUT_STATE_ENTRIES; i++) {
            if (strcmp(name, input_state_table[i].name) == 0) {
                *out_pressed = (input_state_table[i].value == 0);
                return 1;
            }
        }

        PyErr_Format(PyExc_ValueError,
            "Unknown InputState: '%s'. Use InputState.PRESSED or InputState.RELEASED.", name);
        return 0;
    }

    PyErr_SetString(PyExc_TypeError,
        "InputState must be mcrfpy.InputState enum member, string, or int");
    return 0;
}
