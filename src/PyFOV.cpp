#include "PyFOV.h"
#include "McRFPy_API.h"

// Static storage for cached enum class reference
PyObject* PyFOV::fov_enum_class = nullptr;

PyObject* PyFOV::create_enum_class(PyObject* module) {
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

    // Add all FOV algorithm members
    struct {
        const char* name;
        int value;
    } fov_members[] = {
        {"BASIC", FOV_BASIC},
        {"DIAMOND", FOV_DIAMOND},
        {"SHADOW", FOV_SHADOW},
        {"PERMISSIVE_0", FOV_PERMISSIVE_0},
        {"PERMISSIVE_1", FOV_PERMISSIVE_1},
        {"PERMISSIVE_2", FOV_PERMISSIVE_2},
        {"PERMISSIVE_3", FOV_PERMISSIVE_3},
        {"PERMISSIVE_4", FOV_PERMISSIVE_4},
        {"PERMISSIVE_5", FOV_PERMISSIVE_5},
        {"PERMISSIVE_6", FOV_PERMISSIVE_6},
        {"PERMISSIVE_7", FOV_PERMISSIVE_7},
        {"PERMISSIVE_8", FOV_PERMISSIVE_8},
        {"RESTRICTIVE", FOV_RESTRICTIVE},
        {"SYMMETRIC_SHADOWCAST", FOV_SYMMETRIC_SHADOWCAST},
    };

    for (const auto& m : fov_members) {
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

    // Call IntEnum("FOV", members) to create the enum class
    PyObject* name = PyUnicode_FromString("FOV");
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

    PyObject* fov_class = PyObject_Call(int_enum, args, NULL);
    Py_DECREF(args);
    Py_DECREF(int_enum);

    if (!fov_class) {
        return NULL;
    }

    // Cache the reference for fast type checking
    fov_enum_class = fov_class;
    Py_INCREF(fov_enum_class);

    // Add to module
    if (PyModule_AddObject(module, "FOV", fov_class) < 0) {
        Py_DECREF(fov_class);
        fov_enum_class = nullptr;
        return NULL;
    }

    return fov_class;
}

int PyFOV::from_arg(PyObject* arg, TCOD_fov_algorithm_t* out_algo, bool* was_none) {
    if (was_none) *was_none = false;

    // Accept None -> caller should use default
    if (arg == Py_None) {
        if (was_none) *was_none = true;
        *out_algo = FOV_BASIC;
        return 1;
    }

    // Accept FOV enum member (check if it's an instance of our enum)
    if (fov_enum_class && PyObject_IsInstance(arg, fov_enum_class)) {
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
        *out_algo = (TCOD_fov_algorithm_t)val;
        return 1;
    }

    // Accept int (for backwards compatibility)
    if (PyLong_Check(arg)) {
        long val = PyLong_AsLong(arg);
        if (val == -1 && PyErr_Occurred()) {
            return 0;
        }
        if (val < 0 || val >= NB_FOV_ALGORITHMS) {
            PyErr_Format(PyExc_ValueError,
                "Invalid FOV algorithm value: %ld. Must be 0-%d or use mcrfpy.FOV enum.",
                val, NB_FOV_ALGORITHMS - 1);
            return 0;
        }
        *out_algo = (TCOD_fov_algorithm_t)val;
        return 1;
    }

    PyErr_SetString(PyExc_TypeError,
        "FOV algorithm must be mcrfpy.FOV enum member, int, or None");
    return 0;
}
