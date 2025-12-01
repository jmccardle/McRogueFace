#pragma once
#include "Common.h"
#include "Python.h"
#include <libtcod.h>

namespace McRFPy_Libtcod
{
    // Field of View algorithms
    static PyObject* compute_fov(PyObject* self, PyObject* args);
    
    // Pathfinding  
    static PyObject* find_path(PyObject* self, PyObject* args);
    static PyObject* dijkstra_new(PyObject* self, PyObject* args);
    static PyObject* dijkstra_compute(PyObject* self, PyObject* args);
    static PyObject* dijkstra_get_distance(PyObject* self, PyObject* args);
    static PyObject* dijkstra_path_to(PyObject* self, PyObject* args);
    
    // Line algorithms
    static PyObject* line(PyObject* self, PyObject* args);
    static PyObject* line_iter(PyObject* self, PyObject* args);

    // Module initialization
    PyObject* init_libtcod_module();
}