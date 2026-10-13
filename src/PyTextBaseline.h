#pragma once
#include "Common.h"
#include "Python.h"

// #478: which line of a Caption's first text line sits at the Caption's pos.y.
// Named after HTML Canvas `textBaseline` / CSS `text-box-edge`.
enum class TextBaseline {
    TOP = 0,       // pos.y is the line top (the ascent line): baseline at pos.y + ascent
    BASELINE = 1,  // pos.y is the baseline itself (Canvas "alphabetic")
    EM_TOP = 2,    // baseline at pos.y + font_size: SFML's rule, the placement before #478
};

// Module-level TextBaseline enum class (created at runtime using Python's IntEnum),
// stored as mcrfpy.TextBaseline; plus the engine-wide default, mcrfpy.default_text_baseline.
class PyTextBaseline {
public:
    // The built-in default, and the one place to change it.
    static constexpr TextBaseline BUILTIN_DEFAULT = TextBaseline::TOP;

    // mcrfpy.default_text_baseline: what a Caption made without baseline= copies at
    // construction. Changing it does not move existing captions.
    static TextBaseline default_baseline;

    // Create the enum class and add it to the module. New reference, or NULL on error.
    static PyObject* create_enum_class(PyObject* module);

    // A TextBaseline member or its int value. 1 on success; 0 with TypeError (any
    // other type, including bool and str) or ValueError (an int out of range) set.
    static int from_arg(PyObject* arg, TextBaseline* out);

    // The enum member for `value`. New reference, or NULL with an exception set.
    static PyObject* to_python(TextBaseline value);

    static PyObject* text_baseline_enum_class;
};
