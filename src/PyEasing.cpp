#include "PyEasing.h"
#include "McRFPy_API.h"

// Static storage for cached enum class reference
PyObject* PyEasing::easing_enum_class = nullptr;

// Easing function table - maps enum value to function and name
struct EasingEntry {
    const char* name;
    int value;
    EasingFunction func;
};

static const EasingEntry easing_table[] = {
    {"LINEAR", 0, EasingFunctions::linear},
    {"EASE_IN", 1, EasingFunctions::easeIn},
    {"EASE_OUT", 2, EasingFunctions::easeOut},
    {"EASE_IN_OUT", 3, EasingFunctions::easeInOut},
    {"EASE_IN_QUAD", 4, EasingFunctions::easeInQuad},
    {"EASE_OUT_QUAD", 5, EasingFunctions::easeOutQuad},
    {"EASE_IN_OUT_QUAD", 6, EasingFunctions::easeInOutQuad},
    {"EASE_IN_CUBIC", 7, EasingFunctions::easeInCubic},
    {"EASE_OUT_CUBIC", 8, EasingFunctions::easeOutCubic},
    {"EASE_IN_OUT_CUBIC", 9, EasingFunctions::easeInOutCubic},
    {"EASE_IN_QUART", 10, EasingFunctions::easeInQuart},
    {"EASE_OUT_QUART", 11, EasingFunctions::easeOutQuart},
    {"EASE_IN_OUT_QUART", 12, EasingFunctions::easeInOutQuart},
    {"EASE_IN_SINE", 13, EasingFunctions::easeInSine},
    {"EASE_OUT_SINE", 14, EasingFunctions::easeOutSine},
    {"EASE_IN_OUT_SINE", 15, EasingFunctions::easeInOutSine},
    {"EASE_IN_EXPO", 16, EasingFunctions::easeInExpo},
    {"EASE_OUT_EXPO", 17, EasingFunctions::easeOutExpo},
    {"EASE_IN_OUT_EXPO", 18, EasingFunctions::easeInOutExpo},
    {"EASE_IN_CIRC", 19, EasingFunctions::easeInCirc},
    {"EASE_OUT_CIRC", 20, EasingFunctions::easeOutCirc},
    {"EASE_IN_OUT_CIRC", 21, EasingFunctions::easeInOutCirc},
    {"EASE_IN_ELASTIC", 22, EasingFunctions::easeInElastic},
    {"EASE_OUT_ELASTIC", 23, EasingFunctions::easeOutElastic},
    {"EASE_IN_OUT_ELASTIC", 24, EasingFunctions::easeInOutElastic},
    {"EASE_IN_BACK", 25, EasingFunctions::easeInBack},
    {"EASE_OUT_BACK", 26, EasingFunctions::easeOutBack},
    {"EASE_IN_OUT_BACK", 27, EasingFunctions::easeInOutBack},
    {"EASE_IN_BOUNCE", 28, EasingFunctions::easeInBounce},
    {"EASE_OUT_BOUNCE", 29, EasingFunctions::easeOutBounce},
    {"EASE_IN_OUT_BOUNCE", 30, EasingFunctions::easeInOutBounce},
};

// Old string names (for backwards compatibility)
static const char* legacy_names[] = {
    "linear", "easeIn", "easeOut", "easeInOut",
    "easeInQuad", "easeOutQuad", "easeInOutQuad",
    "easeInCubic", "easeOutCubic", "easeInOutCubic",
    "easeInQuart", "easeOutQuart", "easeInOutQuart",
    "easeInSine", "easeOutSine", "easeInOutSine",
    "easeInExpo", "easeOutExpo", "easeInOutExpo",
    "easeInCirc", "easeOutCirc", "easeInOutCirc",
    "easeInElastic", "easeOutElastic", "easeInOutElastic",
    "easeInBack", "easeOutBack", "easeInOutBack",
    "easeInBounce", "easeOutBounce", "easeInOutBounce"
};

static const int NUM_EASING_ENTRIES = sizeof(easing_table) / sizeof(easing_table[0]);

const char* PyEasing::easing_name(int value) {
    if (value >= 0 && value < NUM_EASING_ENTRIES) {
        return easing_table[value].name;
    }
    return "LINEAR";
}

PyObject* PyEasing::create_enum_class(PyObject* module) {
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

    // Add all easing function members
    for (int i = 0; i < NUM_EASING_ENTRIES; i++) {
        PyObject* value = PyLong_FromLong(easing_table[i].value);
        if (!value) {
            Py_DECREF(members);
            Py_DECREF(int_enum);
            return NULL;
        }
        if (PyDict_SetItemString(members, easing_table[i].name, value) < 0) {
            Py_DECREF(value);
            Py_DECREF(members);
            Py_DECREF(int_enum);
            return NULL;
        }
        Py_DECREF(value);
    }

    // Call IntEnum("Easing", members) to create the enum class
    PyObject* name = PyUnicode_FromString("Easing");
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

    PyObject* easing_class = PyObject_Call(int_enum, args, NULL);
    Py_DECREF(args);
    Py_DECREF(int_enum);

    if (!easing_class) {
        return NULL;
    }

    // Cache the reference for fast type checking
    easing_enum_class = easing_class;
    Py_INCREF(easing_enum_class);

    // Add to module
    if (PyModule_AddObject(module, "Easing", easing_class) < 0) {
        Py_DECREF(easing_class);
        easing_enum_class = nullptr;
        return NULL;
    }

    return easing_class;
}

int PyEasing::from_arg(PyObject* arg, EasingFunction* out_func, bool* was_none) {
    if (was_none) *was_none = false;

    // Accept None -> default to linear
    if (arg == Py_None) {
        if (was_none) *was_none = true;
        *out_func = EasingFunctions::linear;
        return 1;
    }

    // Accept Easing enum member (check if it's an instance of our enum)
    if (easing_enum_class && PyObject_IsInstance(arg, easing_enum_class)) {
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
        if (val >= 0 && val < NUM_EASING_ENTRIES) {
            *out_func = easing_table[val].func;
            return 1;
        }
        PyErr_Format(PyExc_ValueError,
            "Invalid Easing value: %ld. Must be 0-%d.", val, NUM_EASING_ENTRIES - 1);
        return 0;
    }

    // Accept int (for backwards compatibility and direct enum value access)
    if (PyLong_Check(arg)) {
        long val = PyLong_AsLong(arg);
        if (val == -1 && PyErr_Occurred()) {
            return 0;
        }
        if (val >= 0 && val < NUM_EASING_ENTRIES) {
            *out_func = easing_table[val].func;
            return 1;
        }
        PyErr_Format(PyExc_ValueError,
            "Invalid easing value: %ld. Must be 0-%d or use mcrfpy.Easing enum.",
            val, NUM_EASING_ENTRIES - 1);
        return 0;
    }

    // Accept string (for backwards compatibility)
    if (PyUnicode_Check(arg)) {
        const char* name = PyUnicode_AsUTF8(arg);
        if (!name) {
            return 0;
        }

        // Check legacy string names first
        for (int i = 0; i < NUM_EASING_ENTRIES; i++) {
            if (strcmp(name, legacy_names[i]) == 0) {
                *out_func = easing_table[i].func;
                return 1;
            }
        }

        // Also check enum-style names (EASE_IN_OUT, etc.)
        for (int i = 0; i < NUM_EASING_ENTRIES; i++) {
            if (strcmp(name, easing_table[i].name) == 0) {
                *out_func = easing_table[i].func;
                return 1;
            }
        }

        // Build error message with available options
        PyErr_Format(PyExc_ValueError,
            "Unknown easing function: '%s'. Use mcrfpy.Easing enum (e.g., Easing.EASE_IN_OUT) "
            "or legacy string names: 'linear', 'easeIn', 'easeOut', 'easeInOut', 'easeInQuad', etc.",
            name);
        return 0;
    }

    PyErr_SetString(PyExc_TypeError,
        "Easing must be mcrfpy.Easing enum member, string, int, or None");
    return 0;
}
