#pragma once
#include "Common.h"
#include "Python.h"

// Alignment type enum - used internally in C++
enum class AlignmentType {
    NONE = -1,  // No alignment (static positioning)
    TOP_LEFT = 0,
    TOP_CENTER = 1,
    TOP_RIGHT = 2,
    CENTER_LEFT = 3,
    CENTER = 4,
    CENTER_RIGHT = 5,
    BOTTOM_LEFT = 6,
    BOTTOM_CENTER = 7,
    BOTTOM_RIGHT = 8
};

// Module-level Alignment enum class (created at runtime using Python's IntEnum)
// Stored as a module attribute: mcrfpy.Alignment

class PyAlignment {
public:
    // Create the Alignment enum class and add to module
    // Returns the enum class (new reference), or NULL on error
    static PyObject* create_enum_class(PyObject* module);

    // Helper to extract alignment from Python arg
    // Accepts Alignment enum, string, int, or None
    // Returns 1 on success, 0 on error (with exception set)
    // If arg is None, sets *out_align to NONE and sets *was_none to true
    static int from_arg(PyObject* arg, AlignmentType* out_align, bool* was_none = nullptr);

    // Convert alignment enum value to string name
    static const char* alignment_name(AlignmentType value);

    // Cached reference to the Alignment enum class for fast type checking
    static PyObject* alignment_enum_class;

    // Number of alignment options (excluding NONE)
    static const int NUM_ALIGNMENTS = 9;
};
