#include "McRFPy_Libtcod.h"
#include "McRFPy_API.h"
#include "UIGrid.h"
#include <vector>

// Helper function to get UIGrid from Python object
static UIGrid* get_grid_from_pyobject(PyObject* obj) {
    auto grid_type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Grid");
    if (!grid_type) {
        PyErr_SetString(PyExc_RuntimeError, "Could not find Grid type");
        return nullptr;
    }

    if (!PyObject_IsInstance(obj, (PyObject*)grid_type)) {
        Py_DECREF(grid_type);
        PyErr_SetString(PyExc_TypeError, "First argument must be a Grid object");
        return nullptr;
    }

    Py_DECREF(grid_type);
    PyUIGridObject* pygrid = (PyUIGridObject*)obj;
    return pygrid->data.get();
}

// Field of View computation
static PyObject* McRFPy_Libtcod::compute_fov(PyObject* self, PyObject* args) {
    PyObject* grid_obj;
    int x, y, radius;
    int light_walls = 1;
    int algorithm = FOV_BASIC;

    if (!PyArg_ParseTuple(args, "Oiii|ii", &grid_obj, &x, &y, &radius,
                         &light_walls, &algorithm)) {
        return NULL;
    }

    UIGrid* grid = get_grid_from_pyobject(grid_obj);
    if (!grid) return NULL;

    // Compute FOV using grid's method
    grid->computeFOV(x, y, radius, light_walls, (TCOD_fov_algorithm_t)algorithm);

    // Return list of visible cells
    PyObject* visible_list = PyList_New(0);
    for (int gy = 0; gy < grid->grid_h; gy++) {
        for (int gx = 0; gx < grid->grid_w; gx++) {
            if (grid->isInFOV(gx, gy)) {
                PyObject* pos = Py_BuildValue("(ii)", gx, gy);
                PyList_Append(visible_list, pos);
                Py_DECREF(pos);
            }
        }
    }

    return visible_list;
}

// Line drawing algorithm
static PyObject* McRFPy_Libtcod::line(PyObject* self, PyObject* args) {
    int x1, y1, x2, y2;

    if (!PyArg_ParseTuple(args, "iiii", &x1, &y1, &x2, &y2)) {
        return NULL;
    }

    // Use TCOD's line algorithm
    TCODLine::init(x1, y1, x2, y2);

    PyObject* line_list = PyList_New(0);
    int x, y;

    // Step through line
    while (!TCODLine::step(&x, &y)) {
        PyObject* pos = Py_BuildValue("(ii)", x, y);
        PyList_Append(line_list, pos);
        Py_DECREF(pos);
    }

    return line_list;
}

// Line iterator (generator-like function)
static PyObject* McRFPy_Libtcod::line_iter(PyObject* self, PyObject* args) {
    // For simplicity, just call line() for now
    // A proper implementation would create an iterator object
    return line(self, args);
}

// Pathfinding functions removed - use Grid.find_path() and Grid.get_dijkstra_map() instead
// These return AStarPath and DijkstraMap objects (see UIGridPathfinding.h)

// Method definitions
static PyMethodDef libtcodMethods[] = {
    {"compute_fov", McRFPy_Libtcod::compute_fov, METH_VARARGS,
     "compute_fov(grid, x, y, radius, light_walls=True, algorithm=mcrfpy.FOV.BASIC)\n\n"
     "Compute field of view from a position.\n\n"
     "Args:\n"
     "    grid: Grid object to compute FOV on\n"
     "    x, y: Origin position\n"
     "    radius: Maximum sight radius\n"
     "    light_walls: Whether walls are lit when in FOV\n"
     "    algorithm: FOV algorithm (mcrfpy.FOV.BASIC, mcrfpy.FOV.SHADOW, etc.)\n\n"
     "Returns:\n"
     "    List of (x, y) tuples for visible cells"},

    {"line", McRFPy_Libtcod::line, METH_VARARGS,
     "line(x1, y1, x2, y2)\n\n"
     "Get cells along a line using Bresenham's algorithm.\n\n"
     "Args:\n"
     "    x1, y1: Starting position\n"
     "    x2, y2: Ending position\n\n"
     "Returns:\n"
     "    List of (x, y) tuples along the line"},

    {"line_iter", McRFPy_Libtcod::line_iter, METH_VARARGS,
     "line_iter(x1, y1, x2, y2)\n\n"
     "Iterate over cells along a line.\n\n"
     "Args:\n"
     "    x1, y1: Starting position\n"
     "    x2, y2: Ending position\n\n"
     "Returns:\n"
     "    Iterator of (x, y) tuples along the line"},

    {NULL, NULL, 0, NULL}
};

// Module definition
static PyModuleDef libtcodModule = {
    PyModuleDef_HEAD_INIT,
    "mcrfpy.libtcod",
    "TCOD-compatible algorithms for field of view and line drawing.\n\n"
    "This module provides access to TCOD's algorithms integrated with McRogueFace grids.\n"
    "Unlike the original TCOD, these functions work directly with Grid objects.\n\n"
    "FOV Algorithms (use mcrfpy.FOV enum):\n"
    "    mcrfpy.FOV.BASIC - Basic circular FOV\n"
    "    mcrfpy.FOV.SHADOW - Shadow casting (recommended)\n"
    "    mcrfpy.FOV.DIAMOND - Diamond-shaped FOV\n"
    "    mcrfpy.FOV.PERMISSIVE_0 through PERMISSIVE_8 - Permissive variants\n"
    "    mcrfpy.FOV.RESTRICTIVE - Most restrictive FOV\n"
    "    mcrfpy.FOV.SYMMETRIC_SHADOWCAST - Symmetric shadow casting\n\n"
    "Pathfinding:\n"
    "    Use Grid.find_path() for A* pathfinding (returns AStarPath objects)\n"
    "    Use Grid.get_dijkstra_map() for Dijkstra pathfinding (returns DijkstraMap objects)\n\n"
    "Example:\n"
    "    import mcrfpy\n"
    "    from mcrfpy import libtcod\n\n"
    "    grid = mcrfpy.Grid(50, 50)\n"
    "    visible = libtcod.compute_fov(grid, 25, 25, 10)\n"
    "    path = grid.find_path((0, 0), (49, 49))  # Returns AStarPath",
    -1,
    libtcodMethods
};

// Module initialization
PyObject* McRFPy_Libtcod::init_libtcod_module() {
    PyObject* m = PyModule_Create(&libtcodModule);
    if (m == NULL) {
        return NULL;
    }

    // FOV algorithm constants now provided by mcrfpy.FOV enum (#114)

    return m;
}
