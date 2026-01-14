#include "PyAlignment.h"
#include "McRFPy_API.h"

// Static storage for cached enum class reference
PyObject* PyAlignment::alignment_enum_class = nullptr;

// Alignment table - maps enum value to name
struct AlignmentEntry {
    const char* name;
    int value;
    AlignmentType type;
};

static const AlignmentEntry alignment_table[] = {
    {"TOP_LEFT", 0, AlignmentType::TOP_LEFT},
    {"TOP_CENTER", 1, AlignmentType::TOP_CENTER},
    {"TOP_RIGHT", 2, AlignmentType::TOP_RIGHT},
    {"CENTER_LEFT", 3, AlignmentType::CENTER_LEFT},
    {"CENTER", 4, AlignmentType::CENTER},
    {"CENTER_RIGHT", 5, AlignmentType::CENTER_RIGHT},
    {"BOTTOM_LEFT", 6, AlignmentType::BOTTOM_LEFT},
    {"BOTTOM_CENTER", 7, AlignmentType::BOTTOM_CENTER},
    {"BOTTOM_RIGHT", 8, AlignmentType::BOTTOM_RIGHT},
};

// Legacy camelCase names (for backwards compatibility if desired)
static const char* legacy_names[] = {
    "topLeft", "topCenter", "topRight",
    "centerLeft", "center", "centerRight",
    "bottomLeft", "bottomCenter", "bottomRight"
};

static const int NUM_ALIGNMENT_ENTRIES = sizeof(alignment_table) / sizeof(alignment_table[0]);

const char* PyAlignment::alignment_name(AlignmentType value) {
    int idx = static_cast<int>(value);
    if (idx >= 0 && idx < NUM_ALIGNMENT_ENTRIES) {
        return alignment_table[idx].name;
    }
    return "NONE";
}

PyObject* PyAlignment::create_enum_class(PyObject* module) {
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

    // Add all alignment members
    for (int i = 0; i < NUM_ALIGNMENT_ENTRIES; i++) {
        PyObject* value = PyLong_FromLong(alignment_table[i].value);
        if (!value) {
            Py_DECREF(members);
            Py_DECREF(int_enum);
            return NULL;
        }
        if (PyDict_SetItemString(members, alignment_table[i].name, value) < 0) {
            Py_DECREF(value);
            Py_DECREF(members);
            Py_DECREF(int_enum);
            return NULL;
        }
        Py_DECREF(value);
    }

    // Call IntEnum("Alignment", members) to create the enum class
    PyObject* name = PyUnicode_FromString("Alignment");
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

    PyObject* alignment_class = PyObject_Call(int_enum, args, NULL);
    Py_DECREF(args);
    Py_DECREF(int_enum);

    if (!alignment_class) {
        return NULL;
    }

    // Cache the reference for fast type checking
    alignment_enum_class = alignment_class;
    Py_INCREF(alignment_enum_class);

    // Add docstring to the enum class
    static const char* alignment_doc =
        "Alignment enum for positioning UI elements relative to parent bounds.\n\n"
        "Values:\n"
        "    TOP_LEFT, TOP_CENTER, TOP_RIGHT\n"
        "    CENTER_LEFT, CENTER, CENTER_RIGHT\n"
        "    BOTTOM_LEFT, BOTTOM_CENTER, BOTTOM_RIGHT\n\n"
        "Margin Validation Rules:\n"
        "    Margins define distance from parent edge when aligned.\n\n"
        "    - CENTER: No margins allowed (raises ValueError if margin != 0)\n"
        "    - TOP_CENTER, BOTTOM_CENTER: Only vert_margin applies (horiz_margin raises ValueError)\n"
        "    - CENTER_LEFT, CENTER_RIGHT: Only horiz_margin applies (vert_margin raises ValueError)\n"
        "    - Corner alignments (TOP_LEFT, etc.): All margins valid\n\n"
        "Properties:\n"
        "    align: Alignment value or None to disable\n"
        "    margin: General margin for all applicable edges\n"
        "    horiz_margin: Override for horizontal edge (0 = use general margin)\n"
        "    vert_margin: Override for vertical edge (0 = use general margin)\n\n"
        "Example:\n"
        "    # Center a panel in the scene\n"
        "    panel = Frame(size=(200, 100), align=Alignment.CENTER)\n"
        "    scene.children.append(panel)\n\n"
        "    # Place button in bottom-right with 10px margin\n"
        "    button = Frame(size=(80, 30), align=Alignment.BOTTOM_RIGHT, margin=10)\n"
        "    panel.children.append(button)";
    PyObject* doc = PyUnicode_FromString(alignment_doc);
    if (doc) {
        PyObject_SetAttrString(alignment_class, "__doc__", doc);
        Py_DECREF(doc);
    }

    // Add to module
    if (PyModule_AddObject(module, "Alignment", alignment_class) < 0) {
        Py_DECREF(alignment_class);
        alignment_enum_class = nullptr;
        return NULL;
    }

    return alignment_class;
}

int PyAlignment::from_arg(PyObject* arg, AlignmentType* out_align, bool* was_none) {
    if (was_none) *was_none = false;

    // Accept None -> NONE alignment (no alignment)
    if (arg == Py_None) {
        if (was_none) *was_none = true;
        *out_align = AlignmentType::NONE;
        return 1;
    }

    // Accept Alignment enum member (check if it's an instance of our enum)
    if (alignment_enum_class && PyObject_IsInstance(arg, alignment_enum_class)) {
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
        if (val >= 0 && val < NUM_ALIGNMENT_ENTRIES) {
            *out_align = alignment_table[val].type;
            return 1;
        }
        PyErr_Format(PyExc_ValueError,
            "Invalid Alignment value: %ld. Must be 0-%d.", val, NUM_ALIGNMENT_ENTRIES - 1);
        return 0;
    }

    // Accept int (for direct enum value access)
    if (PyLong_Check(arg)) {
        long val = PyLong_AsLong(arg);
        if (val == -1 && PyErr_Occurred()) {
            return 0;
        }
        if (val >= 0 && val < NUM_ALIGNMENT_ENTRIES) {
            *out_align = alignment_table[val].type;
            return 1;
        }
        PyErr_Format(PyExc_ValueError,
            "Invalid alignment value: %ld. Must be 0-%d or use mcrfpy.Alignment enum.",
            val, NUM_ALIGNMENT_ENTRIES - 1);
        return 0;
    }

    // Accept string (for backwards compatibility)
    if (PyUnicode_Check(arg)) {
        const char* name = PyUnicode_AsUTF8(arg);
        if (!name) {
            return 0;
        }

        // Check legacy camelCase names first
        for (int i = 0; i < NUM_ALIGNMENT_ENTRIES; i++) {
            if (strcmp(name, legacy_names[i]) == 0) {
                *out_align = alignment_table[i].type;
                return 1;
            }
        }

        // Also check enum-style names (TOP_LEFT, CENTER, etc.)
        for (int i = 0; i < NUM_ALIGNMENT_ENTRIES; i++) {
            if (strcmp(name, alignment_table[i].name) == 0) {
                *out_align = alignment_table[i].type;
                return 1;
            }
        }

        // Build error message with available options
        PyErr_Format(PyExc_ValueError,
            "Unknown alignment: '%s'. Use mcrfpy.Alignment enum (e.g., Alignment.CENTER) "
            "or string names: 'topLeft', 'topCenter', 'topRight', 'centerLeft', 'center', "
            "'centerRight', 'bottomLeft', 'bottomCenter', 'bottomRight'.",
            name);
        return 0;
    }

    PyErr_SetString(PyExc_TypeError,
        "Alignment must be mcrfpy.Alignment enum member, string, int, or None");
    return 0;
}
