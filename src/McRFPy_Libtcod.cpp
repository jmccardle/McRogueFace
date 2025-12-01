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
    for (int gy = 0; gy < grid->grid_y; gy++) {
        for (int gx = 0; gx < grid->grid_x; gx++) {
            if (grid->isInFOV(gx, gy)) {
                PyObject* pos = Py_BuildValue("(ii)", gx, gy);
                PyList_Append(visible_list, pos);
                Py_DECREF(pos);
            }
        }
    }
    
    return visible_list;
}

// A* Pathfinding
static PyObject* McRFPy_Libtcod::find_path(PyObject* self, PyObject* args) {
    PyObject* grid_obj;
    int x1, y1, x2, y2;
    float diagonal_cost = 1.41f;
    
    if (!PyArg_ParseTuple(args, "Oiiii|f", &grid_obj, &x1, &y1, &x2, &y2, &diagonal_cost)) {
        return NULL;
    }
    
    UIGrid* grid = get_grid_from_pyobject(grid_obj);
    if (!grid) return NULL;
    
    // Get path from grid
    std::vector<std::pair<int, int>> path = grid->findPath(x1, y1, x2, y2, diagonal_cost);
    
    // Convert to Python list
    PyObject* path_list = PyList_New(path.size());
    for (size_t i = 0; i < path.size(); i++) {
        PyObject* pos = Py_BuildValue("(ii)", path[i].first, path[i].second);
        PyList_SetItem(path_list, i, pos);  // steals reference
    }
    
    return path_list;
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

// Dijkstra pathfinding
static PyObject* McRFPy_Libtcod::dijkstra_new(PyObject* self, PyObject* args) {
    PyObject* grid_obj;
    float diagonal_cost = 1.41f;
    
    if (!PyArg_ParseTuple(args, "O|f", &grid_obj, &diagonal_cost)) {
        return NULL;
    }
    
    UIGrid* grid = get_grid_from_pyobject(grid_obj);
    if (!grid) return NULL;
    
    // For now, just return the grid object since Dijkstra is part of the grid
    Py_INCREF(grid_obj);
    return grid_obj;
}

static PyObject* McRFPy_Libtcod::dijkstra_compute(PyObject* self, PyObject* args) {
    PyObject* grid_obj;
    int root_x, root_y;
    
    if (!PyArg_ParseTuple(args, "Oii", &grid_obj, &root_x, &root_y)) {
        return NULL;
    }
    
    UIGrid* grid = get_grid_from_pyobject(grid_obj);
    if (!grid) return NULL;
    
    grid->computeDijkstra(root_x, root_y);
    Py_RETURN_NONE;
}

static PyObject* McRFPy_Libtcod::dijkstra_get_distance(PyObject* self, PyObject* args) {
    PyObject* grid_obj;
    int x, y;
    
    if (!PyArg_ParseTuple(args, "Oii", &grid_obj, &x, &y)) {
        return NULL;
    }
    
    UIGrid* grid = get_grid_from_pyobject(grid_obj);
    if (!grid) return NULL;
    
    float distance = grid->getDijkstraDistance(x, y);
    if (distance < 0) {
        Py_RETURN_NONE;
    }
    
    return PyFloat_FromDouble(distance);
}

static PyObject* McRFPy_Libtcod::dijkstra_path_to(PyObject* self, PyObject* args) {
    PyObject* grid_obj;
    int x, y;
    
    if (!PyArg_ParseTuple(args, "Oii", &grid_obj, &x, &y)) {
        return NULL;
    }
    
    UIGrid* grid = get_grid_from_pyobject(grid_obj);
    if (!grid) return NULL;
    
    std::vector<std::pair<int, int>> path = grid->getDijkstraPath(x, y);
    
    PyObject* path_list = PyList_New(path.size());
    for (size_t i = 0; i < path.size(); i++) {
        PyObject* pos = Py_BuildValue("(ii)", path[i].first, path[i].second);
        PyList_SetItem(path_list, i, pos);  // steals reference
    }
    
    return path_list;
}

// FOV algorithm constants removed - use mcrfpy.FOV enum instead (#114)

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
     
    {"find_path", McRFPy_Libtcod::find_path, METH_VARARGS,
     "find_path(grid, x1, y1, x2, y2, diagonal_cost=1.41)\n\n"
     "Find shortest path between two points using A*.\n\n"
     "Args:\n"
     "    grid: Grid object to pathfind on\n"
     "    x1, y1: Starting position\n"
     "    x2, y2: Target position\n"
     "    diagonal_cost: Cost of diagonal movement\n\n"
     "Returns:\n"
     "    List of (x, y) tuples representing the path, or empty list if no path exists"},
     
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
     
    {"dijkstra_new", McRFPy_Libtcod::dijkstra_new, METH_VARARGS,
     "dijkstra_new(grid, diagonal_cost=1.41)\n\n"
     "Create a Dijkstra pathfinding context for a grid.\n\n"
     "Args:\n"
     "    grid: Grid object to use for pathfinding\n"
     "    diagonal_cost: Cost of diagonal movement\n\n"
     "Returns:\n"
     "    Grid object configured for Dijkstra pathfinding"},
     
    {"dijkstra_compute", McRFPy_Libtcod::dijkstra_compute, METH_VARARGS,
     "dijkstra_compute(grid, root_x, root_y)\n\n"
     "Compute Dijkstra distance map from root position.\n\n"
     "Args:\n"
     "    grid: Grid object with Dijkstra context\n"
     "    root_x, root_y: Root position to compute distances from"},
     
    {"dijkstra_get_distance", McRFPy_Libtcod::dijkstra_get_distance, METH_VARARGS,
     "dijkstra_get_distance(grid, x, y)\n\n"
     "Get distance from root to a position.\n\n"
     "Args:\n"
     "    grid: Grid object with computed Dijkstra map\n"
     "    x, y: Position to get distance for\n\n"
     "Returns:\n"
     "    Float distance or None if position is invalid/unreachable"},
     
    {"dijkstra_path_to", McRFPy_Libtcod::dijkstra_path_to, METH_VARARGS,
     "dijkstra_path_to(grid, x, y)\n\n"
     "Get shortest path from position to Dijkstra root.\n\n"
     "Args:\n"
     "    grid: Grid object with computed Dijkstra map\n"
     "    x, y: Starting position\n\n"
     "Returns:\n"
     "    List of (x, y) tuples representing the path to root"},
     
    {NULL, NULL, 0, NULL}
};

// Module definition
static PyModuleDef libtcodModule = {
    PyModuleDef_HEAD_INIT,
    "mcrfpy.libtcod",
    "TCOD-compatible algorithms for field of view, pathfinding, and line drawing.\n\n"
    "This module provides access to TCOD's algorithms integrated with McRogueFace grids.\n"
    "Unlike the original TCOD, these functions work directly with Grid objects.\n\n"
    "FOV Algorithms (use mcrfpy.FOV enum):\n"
    "    mcrfpy.FOV.BASIC - Basic circular FOV\n"
    "    mcrfpy.FOV.SHADOW - Shadow casting (recommended)\n"
    "    mcrfpy.FOV.DIAMOND - Diamond-shaped FOV\n"
    "    mcrfpy.FOV.PERMISSIVE_0 through PERMISSIVE_8 - Permissive variants\n"
    "    mcrfpy.FOV.RESTRICTIVE - Most restrictive FOV\n"
    "    mcrfpy.FOV.SYMMETRIC_SHADOWCAST - Symmetric shadow casting\n\n"
    "Example:\n"
    "    import mcrfpy\n"
    "    from mcrfpy import libtcod\n\n"
    "    grid = mcrfpy.Grid(50, 50)\n"
    "    visible = libtcod.compute_fov(grid, 25, 25, 10)\n"
    "    path = libtcod.find_path(grid, 0, 0, 49, 49)",
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