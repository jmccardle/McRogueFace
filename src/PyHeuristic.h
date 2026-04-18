#pragma once
#include "Common.h"
#include "Python.h"
#include <libtcod.h>
#include <cstdint>

// Module-level Heuristic enum class (created at runtime using Python's IntEnum)
// Stored as a module attribute: mcrfpy.Heuristic
//
// Values:
//   EUCLIDEAN = 0   (admissible, default, slowest-optimal)
//   MANHATTAN = 1   (admissible on 4-connected)
//   CHEBYSHEV = 2   (admissible on 8-connected, diag cost 1)
//   DIAGONAL  = 3   (octile, admissible on 8-connected, diag cost sqrt(2))
//   ZERO      = 4   (A* degenerates to Dijkstra)
class PyHeuristic {
public:
    // Create the Heuristic enum class and add to module.
    static PyObject* create_enum_class(PyObject* module);

    // Helper to extract a Heuristic value from a Python arg.
    // Accepts Heuristic enum member, string (enum name), or int 0..4.
    // Returns 1 on success, 0 on error (with exception set).
    static int from_arg(PyObject* arg, int* out_value);

    // Returns the libtcod built-in heuristic function pointer for a given value.
    // Returns nullptr if value is invalid.
    static TCOD_heuristic_func_t get_function(int heuristic_value);

    // Cached reference to the Heuristic enum class for fast type checking.
    static PyObject* heuristic_enum_class;

    static const int NUM_HEURISTIC_VALUES = 5;
    static const int EUCLIDEAN = 0;
    static const int MANHATTAN = 1;
    static const int CHEBYSHEV = 2;
    static const int DIAGONAL  = 3;
    static const int ZERO      = 4;
};
