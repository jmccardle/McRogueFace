#include "PyBehavior.h"
#include <sstream>

// Static storage for cached enum class reference
PyObject* PyBehavior::behavior_enum_class = nullptr;

struct BehaviorEntry {
    const char* name;
    int value;
    const char* description;
};

static const BehaviorEntry behavior_table[] = {
    {"IDLE",     0,  "No action each turn"},
    {"CUSTOM",   1,  "Calls step callback only, no built-in movement"},
    {"NOISE4",   2,  "Random movement in 4 cardinal directions"},
    {"NOISE8",   3,  "Random movement in 8 directions (incl. diagonals)"},
    {"PATH",     4,  "Follow a precomputed path to completion"},
    {"WAYPOINT", 5,  "Path through a sequence of waypoints in order"},
    {"PATROL",   6,  "Patrol waypoints back and forth (reversing at ends)"},
    {"LOOP",     7,  "Loop through waypoints cyclically"},
    {"SLEEP",    8,  "Wait for N turns, then trigger DONE"},
    {"SEEK",     9,  "Move toward target using Dijkstra map"},
    {"FLEE",    10,  "Move away from target using Dijkstra map"},
};

static const int NUM_BEHAVIOR_ENTRIES = sizeof(behavior_table) / sizeof(behavior_table[0]);

PyObject* PyBehavior::create_enum_class(PyObject* module) {
    std::ostringstream code;
    code << "from enum import IntEnum\n\n";

    code << "class Behavior(IntEnum):\n";
    code << "    \"\"\"Enum representing entity behavior types for grid.step() turn management.\n";
    code << "    \n";
    code << "    Values:\n";
    for (int i = 0; i < NUM_BEHAVIOR_ENTRIES; i++) {
        code << "        " << behavior_table[i].name << ": " << behavior_table[i].description << "\n";
    }
    code << "    \"\"\"\n";

    for (int i = 0; i < NUM_BEHAVIOR_ENTRIES; i++) {
        code << "    " << behavior_table[i].name << " = " << behavior_table[i].value << "\n";
    }

    code << R"(

def _Behavior_eq(self, other):
    if isinstance(other, str):
        if self.name == other:
            return True
        return False
    return int.__eq__(int(self), other)

Behavior.__eq__ = _Behavior_eq

def _Behavior_ne(self, other):
    result = type(self).__eq__(self, other)
    if result is NotImplemented:
        return result
    return not result

Behavior.__ne__ = _Behavior_ne
Behavior.__hash__ = lambda self: hash(int(self))
Behavior.__repr__ = lambda self: f"{type(self).__name__}.{self.name}"
Behavior.__str__ = lambda self: self.name
)";

    std::string code_str = code.str();

    PyObject* globals = PyDict_New();
    if (!globals) return NULL;

    PyObject* builtins = PyEval_GetBuiltins();
    PyDict_SetItemString(globals, "__builtins__", builtins);

    PyObject* locals = PyDict_New();
    if (!locals) {
        Py_DECREF(globals);
        return NULL;
    }

    PyObject* result = PyRun_String(code_str.c_str(), Py_file_input, globals, locals);
    if (!result) {
        Py_DECREF(globals);
        Py_DECREF(locals);
        return NULL;
    }
    Py_DECREF(result);

    PyObject* behavior_class = PyDict_GetItemString(locals, "Behavior");
    if (!behavior_class) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to create Behavior enum class");
        Py_DECREF(globals);
        Py_DECREF(locals);
        return NULL;
    }

    Py_INCREF(behavior_class);

    behavior_enum_class = behavior_class;
    Py_INCREF(behavior_enum_class);

    if (PyModule_AddObject(module, "Behavior", behavior_class) < 0) {
        Py_DECREF(behavior_class);
        Py_DECREF(globals);
        Py_DECREF(locals);
        behavior_enum_class = nullptr;
        return NULL;
    }

    Py_DECREF(globals);
    Py_DECREF(locals);

    return behavior_class;
}
