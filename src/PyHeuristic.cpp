#include "PyHeuristic.h"
#include <cstring>
#include <sstream>

PyObject* PyHeuristic::heuristic_enum_class = nullptr;

struct HeuristicEntry {
    const char* name;
    int value;
};

static const HeuristicEntry heuristic_table[] = {
    {"EUCLIDEAN", 0},
    {"MANHATTAN", 1},
    {"CHEBYSHEV", 2},
    {"DIAGONAL",  3},
    {"ZERO",      4},
};

static const int NUM_HEURISTIC_ENTRIES =
    sizeof(heuristic_table) / sizeof(heuristic_table[0]);

PyObject* PyHeuristic::create_enum_class(PyObject* module) {
    std::ostringstream code;
    code << "from enum import IntEnum\n\n";
    code << "class Heuristic(IntEnum):\n";
    code << "    \"\"\"Built-in A* heuristic function selector.\n";
    code << "    \n";
    code << "    Values:\n";
    code << "        EUCLIDEAN: sqrt((dx)^2 + (dy)^2). Admissible, default.\n";
    code << "        MANHATTAN: |dx| + |dy|. Admissible on 4-connected grids.\n";
    code << "        CHEBYSHEV: max(|dx|, |dy|). Admissible on 8-connected (diag=1).\n";
    code << "        DIAGONAL: Octile distance. Admissible on 8-connected (diag=sqrt(2)).\n";
    code << "        ZERO: Always returns 0. A* degenerates to Dijkstra.\n";
    code << "    \"\"\"\n";
    for (int i = 0; i < NUM_HEURISTIC_ENTRIES; i++) {
        code << "    " << heuristic_table[i].name
             << " = " << heuristic_table[i].value << "\n";
    }
    code << "\n";
    code << "Heuristic.__hash__ = lambda self: hash(int(self))\n";
    code << "Heuristic.__repr__ = lambda self: f\"{type(self).__name__}.{self.name}\"\n";
    code << "Heuristic.__str__ = lambda self: self.name\n";

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

    PyObject* enum_class = PyDict_GetItemString(locals, "Heuristic");
    if (!enum_class) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to create Heuristic enum class");
        Py_DECREF(globals);
        Py_DECREF(locals);
        return NULL;
    }
    Py_INCREF(enum_class);

    heuristic_enum_class = enum_class;
    Py_INCREF(heuristic_enum_class);

    if (PyModule_AddObject(module, "Heuristic", enum_class) < 0) {
        Py_DECREF(enum_class);
        Py_DECREF(globals);
        Py_DECREF(locals);
        heuristic_enum_class = nullptr;
        return NULL;
    }

    Py_DECREF(globals);
    Py_DECREF(locals);
    return enum_class;
}

int PyHeuristic::from_arg(PyObject* arg, int* out_value) {
    if (heuristic_enum_class && PyObject_IsInstance(arg, heuristic_enum_class)) {
        PyObject* value = PyObject_GetAttrString(arg, "value");
        if (!value) return 0;
        long val = PyLong_AsLong(value);
        Py_DECREF(value);
        if (val == -1 && PyErr_Occurred()) return 0;
        if (val < 0 || val >= NUM_HEURISTIC_VALUES) {
            PyErr_Format(PyExc_ValueError, "Invalid Heuristic value: %ld", val);
            return 0;
        }
        *out_value = static_cast<int>(val);
        return 1;
    }

    if (PyLong_Check(arg)) {
        long val = PyLong_AsLong(arg);
        if (val == -1 && PyErr_Occurred()) return 0;
        if (val < 0 || val >= NUM_HEURISTIC_VALUES) {
            PyErr_Format(PyExc_ValueError,
                "Invalid Heuristic value: %ld. Must be 0..4.", val);
            return 0;
        }
        *out_value = static_cast<int>(val);
        return 1;
    }

    if (PyUnicode_Check(arg)) {
        const char* name = PyUnicode_AsUTF8(arg);
        if (!name) return 0;
        for (int i = 0; i < NUM_HEURISTIC_ENTRIES; i++) {
            if (strcmp(name, heuristic_table[i].name) == 0) {
                *out_value = heuristic_table[i].value;
                return 1;
            }
        }
        PyErr_Format(PyExc_ValueError,
            "Unknown Heuristic: '%s'. Use EUCLIDEAN, MANHATTAN, CHEBYSHEV, DIAGONAL, or ZERO.", name);
        return 0;
    }

    PyErr_SetString(PyExc_TypeError,
        "Heuristic must be mcrfpy.Heuristic enum member, string, or int");
    return 0;
}

TCOD_heuristic_func_t PyHeuristic::get_function(int heuristic_value) {
    switch (heuristic_value) {
        case EUCLIDEAN: return TCOD_heuristic_euclidean;
        case MANHATTAN: return TCOD_heuristic_manhattan;
        case CHEBYSHEV: return TCOD_heuristic_chebyshev;
        case DIAGONAL:  return TCOD_heuristic_diagonal;
        case ZERO:      return TCOD_heuristic_zero;
        default:        return nullptr;
    }
}
