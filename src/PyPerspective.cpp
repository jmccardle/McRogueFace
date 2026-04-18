#include "PyPerspective.h"
#include <cstring>
#include <sstream>

PyObject* PyPerspective::perspective_enum_class = nullptr;

struct PerspectiveEntry {
    const char* name;
    int value;
};

static const PerspectiveEntry perspective_table[] = {
    {"UNKNOWN",    0},
    {"DISCOVERED", 1},
    {"VISIBLE",    2},
};

static const int NUM_PERSPECTIVE_ENTRIES =
    sizeof(perspective_table) / sizeof(perspective_table[0]);

PyObject* PyPerspective::create_enum_class(PyObject* module) {
    std::ostringstream code;
    code << "from enum import IntEnum\n\n";
    code << "class Perspective(IntEnum):\n";
    code << "    \"\"\"Enum representing an entity's knowledge of a cell.\n";
    code << "    \n";
    code << "    Values:\n";
    code << "        UNKNOWN: Never seen (perspective_map value 0)\n";
    code << "        DISCOVERED: Seen before but not currently visible (value 1)\n";
    code << "        VISIBLE: In current FOV (value 2)\n";
    code << "    \"\"\"\n";
    for (int i = 0; i < NUM_PERSPECTIVE_ENTRIES; i++) {
        code << "    " << perspective_table[i].name
             << " = " << perspective_table[i].value << "\n";
    }
    code << "\n";
    code << "Perspective.__hash__ = lambda self: hash(int(self))\n";
    code << "Perspective.__repr__ = lambda self: f\"{type(self).__name__}.{self.name}\"\n";
    code << "Perspective.__str__ = lambda self: self.name\n";

    std::string code_str = code.str();

    PyObject* globals = PyDict_New();
    if (!globals) return NULL;
    PyDict_SetItemString(globals, "__builtins__", PyEval_GetBuiltins());

    PyObject* locals = PyDict_New();
    if (!locals) { Py_DECREF(globals); return NULL; }

    PyObject* result = PyRun_String(code_str.c_str(), Py_file_input, globals, locals);
    if (!result) {
        Py_DECREF(globals);
        Py_DECREF(locals);
        return NULL;
    }
    Py_DECREF(result);

    PyObject* enum_class = PyDict_GetItemString(locals, "Perspective");
    if (!enum_class) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to create Perspective enum class");
        Py_DECREF(globals);
        Py_DECREF(locals);
        return NULL;
    }
    Py_INCREF(enum_class);

    perspective_enum_class = enum_class;
    Py_INCREF(perspective_enum_class);

    if (PyModule_AddObject(module, "Perspective", enum_class) < 0) {
        Py_DECREF(enum_class);
        Py_DECREF(globals);
        Py_DECREF(locals);
        perspective_enum_class = nullptr;
        return NULL;
    }

    Py_DECREF(globals);
    Py_DECREF(locals);
    return enum_class;
}

int PyPerspective::from_arg(PyObject* arg, uint8_t* out_value) {
    if (perspective_enum_class && PyObject_IsInstance(arg, perspective_enum_class)) {
        PyObject* value = PyObject_GetAttrString(arg, "value");
        if (!value) return 0;
        long val = PyLong_AsLong(value);
        Py_DECREF(value);
        if (val == -1 && PyErr_Occurred()) return 0;
        if (val < 0 || val > 2) {
            PyErr_Format(PyExc_ValueError, "Invalid Perspective value: %ld", val);
            return 0;
        }
        *out_value = static_cast<uint8_t>(val);
        return 1;
    }

    if (PyLong_Check(arg)) {
        long val = PyLong_AsLong(arg);
        if (val == -1 && PyErr_Occurred()) return 0;
        if (val < 0 || val > 2) {
            PyErr_Format(PyExc_ValueError,
                "Invalid Perspective value: %ld. Must be 0, 1, or 2.", val);
            return 0;
        }
        *out_value = static_cast<uint8_t>(val);
        return 1;
    }

    if (PyUnicode_Check(arg)) {
        const char* name = PyUnicode_AsUTF8(arg);
        if (!name) return 0;
        for (int i = 0; i < NUM_PERSPECTIVE_ENTRIES; i++) {
            if (strcmp(name, perspective_table[i].name) == 0) {
                *out_value = static_cast<uint8_t>(perspective_table[i].value);
                return 1;
            }
        }
        PyErr_Format(PyExc_ValueError,
            "Unknown Perspective: '%s'. Use UNKNOWN, DISCOVERED, or VISIBLE.", name);
        return 0;
    }

    PyErr_SetString(PyExc_TypeError,
        "Perspective must be mcrfpy.Perspective enum member, string, or int");
    return 0;
}
