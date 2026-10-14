#include "PyTextBaseline.h"
#include <sstream>

PyObject* PyTextBaseline::text_baseline_enum_class = nullptr;
TextBaseline PyTextBaseline::default_baseline = PyTextBaseline::BUILTIN_DEFAULT;

struct TextBaselineEntry {
    const char* name;
    int value;
    const char* description;
};

static const TextBaselineEntry text_baseline_table[] = {
    {"TOP",      0, "pos.y is the top of the line (the font's ascent line); the baseline is at "
                    "pos.y + ascent. A caption at a grid cell's top-left draws over that cell."},
    {"BASELINE", 1, "pos.y is the baseline. Mixed fonts and sizes at one y share a baseline."},
    {"EM_TOP",   2, "The baseline is at pos.y + font_size, the placement before 0.3.3."},
};

static const int NUM_TEXT_BASELINE_ENTRIES =
    sizeof(text_baseline_table) / sizeof(text_baseline_table[0]);

PyObject* PyTextBaseline::create_enum_class(PyObject* module) {
    std::ostringstream code;
    code << "from enum import IntEnum\n\n";
    code << "class TextBaseline(IntEnum):\n";
    code << "    \"\"\"Vertical anchor of a Caption's text: which line of the first text line sits at pos.y.\n";
    code << "    \n";
    code << "    Named after HTML Canvas textBaseline / CSS text-box-edge. Set per Caption with\n";
    code << "    Caption(baseline=...) or caption.baseline; the default for new captions is\n";
    code << "    mcrfpy.default_text_baseline.\n";
    code << "    \n";
    code << "    Values:\n";
    for (int i = 0; i < NUM_TEXT_BASELINE_ENTRIES; i++) {
        code << "        " << text_baseline_table[i].name << ": " << text_baseline_table[i].description << "\n";
    }
    code << "    \"\"\"\n";
    for (int i = 0; i < NUM_TEXT_BASELINE_ENTRIES; i++) {
        code << "    " << text_baseline_table[i].name << " = " << text_baseline_table[i].value << "\n";
    }
    code << R"(

def _TextBaseline_eq(self, other):
    if isinstance(other, str):
        return self.name == other
    return int.__eq__(int(self), other)

TextBaseline.__eq__ = _TextBaseline_eq

def _TextBaseline_ne(self, other):
    result = type(self).__eq__(self, other)
    if result is NotImplemented:
        return result
    return not result

TextBaseline.__ne__ = _TextBaseline_ne
TextBaseline.__hash__ = lambda self: hash(int(self))
TextBaseline.__repr__ = lambda self: f"{type(self).__name__}.{self.name}"
TextBaseline.__str__ = lambda self: self.name
)";
    std::string code_str = code.str();

    PyObject* globals = PyDict_New();
    if (!globals) return NULL;
    PyDict_SetItemString(globals, "__builtins__", PyEval_GetBuiltins());
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

    PyObject* cls = PyDict_GetItemString(locals, "TextBaseline");
    if (!cls) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to create TextBaseline enum class");
        Py_DECREF(globals);
        Py_DECREF(locals);
        return NULL;
    }
    Py_INCREF(cls);
    text_baseline_enum_class = cls;
    Py_INCREF(text_baseline_enum_class);

    if (PyModule_AddObject(module, "TextBaseline", cls) < 0) {
        Py_DECREF(cls);
        Py_DECREF(globals);
        Py_DECREF(locals);
        Py_CLEAR(text_baseline_enum_class);
        return NULL;
    }
    Py_DECREF(globals);
    Py_DECREF(locals);
    return cls;
}

int PyTextBaseline::from_arg(PyObject* arg, TextBaseline* out) {
    // A member, or a plain int. Not a bool, a str, or another enum's member
    // (InputState.PRESSED == 0 is not TextBaseline.TOP).
    int is_member = text_baseline_enum_class
        ? PyObject_IsInstance(arg, text_baseline_enum_class) : 0;
    if (is_member < 0) return 0;
    if (!is_member && !PyLong_CheckExact(arg)) {
        PyErr_Format(PyExc_TypeError,
            "baseline must be a mcrfpy.TextBaseline member (TOP, BASELINE, EM_TOP), not %.200s",
            Py_TYPE(arg)->tp_name);
        return 0;
    }
    long val = PyLong_AsLong(arg);
    if (val == -1 && PyErr_Occurred()) return 0;
    if (val < 0 || val >= NUM_TEXT_BASELINE_ENTRIES) {
        PyErr_Format(PyExc_ValueError,
            "invalid TextBaseline value %ld; use mcrfpy.TextBaseline.TOP, BASELINE or EM_TOP", val);
        return 0;
    }
    *out = static_cast<TextBaseline>(val);
    return 1;
}

PyObject* PyTextBaseline::to_python(TextBaseline value) {
    if (!text_baseline_enum_class) {
        PyErr_SetString(PyExc_RuntimeError, "TextBaseline enum not initialized");
        return NULL;
    }
    return PyObject_CallFunction(text_baseline_enum_class, "i", static_cast<int>(value));
}
