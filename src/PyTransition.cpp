#include "PyTransition.h"
#include "McRFPy_API.h"

// Static storage
PyObject* PyTransition::transition_enum_class = nullptr;
TransitionType PyTransition::default_transition = TransitionType::None;
float PyTransition::default_duration = 1.0f;

PyObject* PyTransition::create_enum_class(PyObject* module) {
    // Import IntEnum from enum module
    PyObject* enum_module = PyImport_ImportModule("enum");
    if (!enum_module) {
        return NULL;
    }

    PyObject* int_enum = PyObject_GetAttrString(enum_module, "IntEnum");
    Py_DECREF(enum_module);
    if (!int_enum) {
        return NULL;
    }

    // Create dict of enum members
    PyObject* members = PyDict_New();
    if (!members) {
        Py_DECREF(int_enum);
        return NULL;
    }

    // Add all Transition type members
    // Values match the C++ TransitionType enum
    struct {
        const char* name;
        int value;
    } transition_members[] = {
        {"NONE", static_cast<int>(TransitionType::None)},
        {"FADE", static_cast<int>(TransitionType::Fade)},
        {"SLIDE_LEFT", static_cast<int>(TransitionType::SlideLeft)},
        {"SLIDE_RIGHT", static_cast<int>(TransitionType::SlideRight)},
        {"SLIDE_UP", static_cast<int>(TransitionType::SlideUp)},
        {"SLIDE_DOWN", static_cast<int>(TransitionType::SlideDown)},
    };

    for (const auto& m : transition_members) {
        PyObject* value = PyLong_FromLong(m.value);
        if (!value) {
            Py_DECREF(members);
            Py_DECREF(int_enum);
            return NULL;
        }
        if (PyDict_SetItemString(members, m.name, value) < 0) {
            Py_DECREF(value);
            Py_DECREF(members);
            Py_DECREF(int_enum);
            return NULL;
        }
        Py_DECREF(value);
    }

    // Call IntEnum("Transition", members) to create the enum class
    PyObject* name = PyUnicode_FromString("Transition");
    if (!name) {
        Py_DECREF(members);
        Py_DECREF(int_enum);
        return NULL;
    }

    // IntEnum(name, members) using functional API
    PyObject* args = PyTuple_Pack(2, name, members);
    Py_DECREF(name);
    Py_DECREF(members);
    if (!args) {
        Py_DECREF(int_enum);
        return NULL;
    }

    PyObject* transition_class = PyObject_Call(int_enum, args, NULL);
    Py_DECREF(args);
    Py_DECREF(int_enum);

    if (!transition_class) {
        return NULL;
    }

    // Cache the reference for fast type checking
    transition_enum_class = transition_class;
    Py_INCREF(transition_enum_class);

    // Add to module
    if (PyModule_AddObject(module, "Transition", transition_class) < 0) {
        Py_DECREF(transition_class);
        transition_enum_class = nullptr;
        return NULL;
    }

    return transition_class;
}

int PyTransition::from_arg(PyObject* arg, TransitionType* out_type, bool* was_none) {
    if (was_none) *was_none = false;

    // Accept None -> caller should use default
    if (arg == Py_None || arg == NULL) {
        if (was_none) *was_none = true;
        *out_type = default_transition;
        return 1;
    }

    // Accept Transition enum member (check if it's an instance of our enum)
    if (transition_enum_class && PyObject_IsInstance(arg, transition_enum_class)) {
        // IntEnum members have a 'value' attribute
        PyObject* value = PyObject_GetAttrString(arg, "value");
        if (!value) {
            return 0;
        }
        long val = PyLong_AsLong(value);
        Py_DECREF(value);
        if (val == -1 && PyErr_Occurred()) {
            return 0;
        }
        *out_type = static_cast<TransitionType>(val);
        return 1;
    }

    // Accept int (for flexibility)
    if (PyLong_Check(arg)) {
        long val = PyLong_AsLong(arg);
        if (val == -1 && PyErr_Occurred()) {
            return 0;
        }
        if (val < 0 || val > static_cast<int>(TransitionType::SlideDown)) {
            PyErr_Format(PyExc_ValueError,
                "Invalid Transition value: %ld. Must be 0-5 or use mcrfpy.Transition enum.",
                val);
            return 0;
        }
        *out_type = static_cast<TransitionType>(val);
        return 1;
    }

    PyErr_SetString(PyExc_TypeError,
        "transition must be mcrfpy.Transition enum member, int, or None");
    return 0;
}

PyObject* PyTransition::to_python(TransitionType type) {
    if (!transition_enum_class) {
        PyErr_SetString(PyExc_RuntimeError, "Transition enum not initialized");
        return NULL;
    }

    // Get the enum member by value
    PyObject* value = PyLong_FromLong(static_cast<int>(type));
    if (!value) return NULL;

    PyObject* result = PyObject_CallFunctionObjArgs(transition_enum_class, value, NULL);
    Py_DECREF(value);
    return result;
}
