#include "PyTrigger.h"
#include <sstream>

// Static storage for cached enum class reference
PyObject* PyTrigger::trigger_enum_class = nullptr;

struct TriggerEntry {
    const char* name;
    int value;
    const char* description;
};

static const TriggerEntry trigger_table[] = {
    {"DONE",    0, "Behavior completed (path exhausted, sleep finished, etc.)"},
    {"BLOCKED", 1, "Movement blocked by wall or collision"},
    {"TARGET",  2, "Target entity spotted in FOV"},
};

static const int NUM_TRIGGER_ENTRIES = sizeof(trigger_table) / sizeof(trigger_table[0]);

PyObject* PyTrigger::create_enum_class(PyObject* module) {
    std::ostringstream code;
    code << "from enum import IntEnum\n\n";

    code << "class Trigger(IntEnum):\n";
    code << "    \"\"\"Enum representing trigger types passed to entity step() callbacks.\n";
    code << "    \n";
    code << "    Values:\n";
    for (int i = 0; i < NUM_TRIGGER_ENTRIES; i++) {
        code << "        " << trigger_table[i].name << ": " << trigger_table[i].description << "\n";
    }
    code << "    \"\"\"\n";

    for (int i = 0; i < NUM_TRIGGER_ENTRIES; i++) {
        code << "    " << trigger_table[i].name << " = " << trigger_table[i].value << "\n";
    }

    code << R"(

def _Trigger_eq(self, other):
    if isinstance(other, str):
        if self.name == other:
            return True
        return False
    return int.__eq__(int(self), other)

Trigger.__eq__ = _Trigger_eq

def _Trigger_ne(self, other):
    result = type(self).__eq__(self, other)
    if result is NotImplemented:
        return result
    return not result

Trigger.__ne__ = _Trigger_ne
Trigger.__hash__ = lambda self: hash(int(self))
Trigger.__repr__ = lambda self: f"{type(self).__name__}.{self.name}"
Trigger.__str__ = lambda self: self.name
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

    PyObject* trigger_class = PyDict_GetItemString(locals, "Trigger");
    if (!trigger_class) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to create Trigger enum class");
        Py_DECREF(globals);
        Py_DECREF(locals);
        return NULL;
    }

    Py_INCREF(trigger_class);

    trigger_enum_class = trigger_class;
    Py_INCREF(trigger_enum_class);

    if (PyModule_AddObject(module, "Trigger", trigger_class) < 0) {
        Py_DECREF(trigger_class);
        Py_DECREF(globals);
        Py_DECREF(locals);
        trigger_enum_class = nullptr;
        return NULL;
    }

    Py_DECREF(globals);
    Py_DECREF(locals);

    return trigger_class;
}
