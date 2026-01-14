#include "UIGridPathfinding.h"
#include "UIGrid.h"
#include "UIEntity.h"
#include "PyVector.h"
#include "McRFPy_API.h"
#include "PyHeightMap.h"
#include "PyPositionHelper.h"

//=============================================================================
// DijkstraMap Implementation
//=============================================================================

DijkstraMap::DijkstraMap(TCODMap* map, int root_x, int root_y, float diag_cost)
    : tcod_map(map)
    , root(root_x, root_y)
    , diagonal_cost(diag_cost)
    , map_width(map ? map->getWidth() : 0)
    , map_height(map ? map->getHeight() : 0)
{
    tcod_dijkstra = new TCODDijkstra(tcod_map, diagonal_cost);
    tcod_dijkstra->compute(root_x, root_y);  // Compute immediately at creation
}

DijkstraMap::~DijkstraMap() {
    if (tcod_dijkstra) {
        delete tcod_dijkstra;
        tcod_dijkstra = nullptr;
    }
}

float DijkstraMap::getDistance(int x, int y) const {
    if (!tcod_dijkstra) return -1.0f;
    return tcod_dijkstra->getDistance(x, y);
}

int DijkstraMap::getWidth() const {
    return map_width;
}

int DijkstraMap::getHeight() const {
    return map_height;
}

std::vector<sf::Vector2i> DijkstraMap::getPathFrom(int x, int y) const {
    std::vector<sf::Vector2i> path;
    if (!tcod_dijkstra) return path;

    if (tcod_dijkstra->setPath(x, y)) {
        int px, py;
        while (tcod_dijkstra->walk(&px, &py)) {
            path.push_back(sf::Vector2i(px, py));
        }
    }
    return path;
}

sf::Vector2i DijkstraMap::stepFrom(int x, int y, bool* valid) const {
    if (!tcod_dijkstra) {
        if (valid) *valid = false;
        return sf::Vector2i(-1, -1);
    }

    if (!tcod_dijkstra->setPath(x, y)) {
        if (valid) *valid = false;
        return sf::Vector2i(-1, -1);
    }

    int px, py;
    if (tcod_dijkstra->walk(&px, &py)) {
        if (valid) *valid = true;
        return sf::Vector2i(px, py);
    }

    // At root or no path
    if (valid) *valid = false;
    return sf::Vector2i(-1, -1);
}

//=============================================================================
// Helper Functions
//=============================================================================

bool UIGridPathfinding::ExtractPosition(PyObject* obj, int* x, int* y,
                                        UIGrid* expected_grid,
                                        const char* arg_name) {
    // Get types from module to avoid static type instance issues
    PyObject* entity_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity");
    PyObject* vector_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");

    // Check if it's an Entity
    if (entity_type && PyObject_IsInstance(obj, entity_type)) {
        Py_DECREF(entity_type);
        Py_XDECREF(vector_type);
        auto* entity = (PyUIEntityObject*)obj;
        if (!entity->data) {
            PyErr_Format(PyExc_RuntimeError,
                "%s: Entity has no data", arg_name);
            return false;
        }
        if (!entity->data->grid) {
            PyErr_Format(PyExc_RuntimeError,
                "%s: Entity is not attached to any grid", arg_name);
            return false;
        }
        if (expected_grid && entity->data->grid.get() != expected_grid) {
            PyErr_Format(PyExc_RuntimeError,
                "%s: Entity belongs to a different grid", arg_name);
            return false;
        }
        *x = static_cast<int>(entity->data->position.x);
        *y = static_cast<int>(entity->data->position.y);
        return true;
    }
    Py_XDECREF(entity_type);

    // Check if it's a Vector
    if (vector_type && PyObject_IsInstance(obj, vector_type)) {
        Py_DECREF(vector_type);
        auto* vec = (PyVectorObject*)obj;
        *x = static_cast<int>(vec->data.x);
        *y = static_cast<int>(vec->data.y);
        return true;
    }
    Py_XDECREF(vector_type);

    // Try tuple/list
    if (PySequence_Check(obj) && PySequence_Size(obj) == 2) {
        PyObject* x_obj = PySequence_GetItem(obj, 0);
        PyObject* y_obj = PySequence_GetItem(obj, 1);

        bool ok = false;
        if (x_obj && y_obj && PyNumber_Check(x_obj) && PyNumber_Check(y_obj)) {
            PyObject* x_long = PyNumber_Long(x_obj);
            PyObject* y_long = PyNumber_Long(y_obj);
            if (x_long && y_long) {
                *x = PyLong_AsLong(x_long);
                *y = PyLong_AsLong(y_long);
                ok = !PyErr_Occurred();
            }
            Py_XDECREF(x_long);
            Py_XDECREF(y_long);
        }

        Py_XDECREF(x_obj);
        Py_XDECREF(y_obj);

        if (ok) return true;
    }

    PyErr_Format(PyExc_TypeError,
        "%s: expected Vector, Entity, or (x, y) tuple", arg_name);
    return false;
}

//=============================================================================
// AStarPath Python Methods
//=============================================================================

PyObject* UIGridPathfinding::AStarPath_new(PyTypeObject* type, PyObject* args, PyObject* kwds) {
    PyAStarPathObject* self = (PyAStarPathObject*)type->tp_alloc(type, 0);
    if (self) {
        new (&self->path) std::vector<sf::Vector2i>();  // Placement new
        self->current_index = 0;
        self->origin = sf::Vector2i(0, 0);
        self->destination = sf::Vector2i(0, 0);
    }
    return (PyObject*)self;
}

int UIGridPathfinding::AStarPath_init(PyAStarPathObject* self, PyObject* args, PyObject* kwds) {
    // AStarPath should not be created directly from Python
    PyErr_SetString(PyExc_TypeError,
        "AStarPath cannot be instantiated directly. Use Grid.find_path() instead.");
    return -1;
}

void UIGridPathfinding::AStarPath_dealloc(PyAStarPathObject* self) {
    self->path.~vector();  // Explicitly destroy
    Py_TYPE(self)->tp_free((PyObject*)self);
}

PyObject* UIGridPathfinding::AStarPath_repr(PyAStarPathObject* self) {
    size_t remaining = self->path.size() - self->current_index;
    return PyUnicode_FromFormat("<AStarPath from (%d,%d) to (%d,%d), %zu steps remaining>",
        self->origin.x, self->origin.y,
        self->destination.x, self->destination.y,
        remaining);
}

PyObject* UIGridPathfinding::AStarPath_walk(PyAStarPathObject* self, PyObject* args) {
    if (self->current_index >= self->path.size()) {
        PyErr_SetString(PyExc_IndexError, "Path exhausted - no more steps");
        return NULL;
    }

    sf::Vector2i pos = self->path[self->current_index++];
    return PyVector(sf::Vector2f(static_cast<float>(pos.x), static_cast<float>(pos.y))).pyObject();
}

PyObject* UIGridPathfinding::AStarPath_peek(PyAStarPathObject* self, PyObject* args) {
    if (self->current_index >= self->path.size()) {
        PyErr_SetString(PyExc_IndexError, "Path exhausted - no more steps");
        return NULL;
    }

    sf::Vector2i pos = self->path[self->current_index];
    return PyVector(sf::Vector2f(static_cast<float>(pos.x), static_cast<float>(pos.y))).pyObject();
}

PyObject* UIGridPathfinding::AStarPath_get_origin(PyAStarPathObject* self, void* closure) {
    return PyVector(sf::Vector2f(static_cast<float>(self->origin.x),
                                  static_cast<float>(self->origin.y))).pyObject();
}

PyObject* UIGridPathfinding::AStarPath_get_destination(PyAStarPathObject* self, void* closure) {
    return PyVector(sf::Vector2f(static_cast<float>(self->destination.x),
                                  static_cast<float>(self->destination.y))).pyObject();
}

PyObject* UIGridPathfinding::AStarPath_get_remaining(PyAStarPathObject* self, void* closure) {
    size_t remaining = self->path.size() - self->current_index;
    return PyLong_FromSize_t(remaining);
}

Py_ssize_t UIGridPathfinding::AStarPath_len(PyAStarPathObject* self) {
    return static_cast<Py_ssize_t>(self->path.size() - self->current_index);
}

int UIGridPathfinding::AStarPath_bool(PyObject* obj) {
    PyAStarPathObject* self = (PyAStarPathObject*)obj;
    return self->current_index < self->path.size() ? 1 : 0;
}

PyObject* UIGridPathfinding::AStarPath_iter(PyAStarPathObject* self) {
    // Create iterator object
    mcrfpydef::PyAStarPathIterObject* iter = PyObject_New(
        mcrfpydef::PyAStarPathIterObject, &mcrfpydef::PyAStarPathIterType);
    if (!iter) return NULL;

    Py_INCREF(self);
    iter->path = self;
    iter->iter_index = self->current_index;

    return (PyObject*)iter;
}

// Iterator implementation
static void AStarPathIter_dealloc(mcrfpydef::PyAStarPathIterObject* self) {
    Py_XDECREF(self->path);
    Py_TYPE(self)->tp_free((PyObject*)self);
}

static PyObject* AStarPathIter_next(mcrfpydef::PyAStarPathIterObject* self) {
    if (!self->path || self->iter_index >= self->path->path.size()) {
        return NULL;  // StopIteration
    }

    sf::Vector2i pos = self->path->path[self->iter_index++];
    // Note: Iterating is consuming for this iterator
    self->path->current_index = self->iter_index;

    return PyVector(sf::Vector2f(static_cast<float>(pos.x), static_cast<float>(pos.y))).pyObject();
}

static PyObject* AStarPathIter_iter(mcrfpydef::PyAStarPathIterObject* self) {
    Py_INCREF(self);
    return (PyObject*)self;
}

//=============================================================================
// DijkstraMap Python Methods
//=============================================================================

PyObject* UIGridPathfinding::DijkstraMap_new(PyTypeObject* type, PyObject* args, PyObject* kwds) {
    PyDijkstraMapObject* self = (PyDijkstraMapObject*)type->tp_alloc(type, 0);
    if (self) {
        new (&self->data) std::shared_ptr<DijkstraMap>();
    }
    return (PyObject*)self;
}

int UIGridPathfinding::DijkstraMap_init(PyDijkstraMapObject* self, PyObject* args, PyObject* kwds) {
    PyErr_SetString(PyExc_TypeError,
        "DijkstraMap cannot be instantiated directly. Use Grid.get_dijkstra_map() instead.");
    return -1;
}

void UIGridPathfinding::DijkstraMap_dealloc(PyDijkstraMapObject* self) {
    self->data.~shared_ptr();
    Py_TYPE(self)->tp_free((PyObject*)self);
}

PyObject* UIGridPathfinding::DijkstraMap_repr(PyDijkstraMapObject* self) {
    if (!self->data) {
        return PyUnicode_FromString("<DijkstraMap (invalid)>");
    }
    sf::Vector2i root = self->data->getRoot();
    return PyUnicode_FromFormat("<DijkstraMap root=(%d,%d)>", root.x, root.y);
}

PyObject* UIGridPathfinding::DijkstraMap_distance(PyDijkstraMapObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"pos", NULL};
    PyObject* pos_obj = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O", const_cast<char**>(kwlist), &pos_obj)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "DijkstraMap is invalid");
        return NULL;
    }

    int x, y;
    if (!ExtractPosition(pos_obj, &x, &y, nullptr, "pos")) {
        return NULL;
    }

    float dist = self->data->getDistance(x, y);
    if (dist < 0) {
        Py_RETURN_NONE;  // Unreachable
    }

    return PyFloat_FromDouble(dist);
}

PyObject* UIGridPathfinding::DijkstraMap_path_from(PyDijkstraMapObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"pos", NULL};
    PyObject* pos_obj = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O", const_cast<char**>(kwlist), &pos_obj)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "DijkstraMap is invalid");
        return NULL;
    }

    int x, y;
    if (!ExtractPosition(pos_obj, &x, &y, nullptr, "pos")) {
        return NULL;
    }

    std::vector<sf::Vector2i> path = self->data->getPathFrom(x, y);

    // Create an AStarPath object to return
    PyAStarPathObject* result = (PyAStarPathObject*)mcrfpydef::PyAStarPathType.tp_alloc(
        &mcrfpydef::PyAStarPathType, 0);
    if (!result) return NULL;

    new (&result->path) std::vector<sf::Vector2i>(std::move(path));
    result->current_index = 0;
    result->origin = sf::Vector2i(x, y);
    result->destination = self->data->getRoot();

    return (PyObject*)result;
}

PyObject* UIGridPathfinding::DijkstraMap_step_from(PyDijkstraMapObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"pos", NULL};
    PyObject* pos_obj = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O", const_cast<char**>(kwlist), &pos_obj)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "DijkstraMap is invalid");
        return NULL;
    }

    int x, y;
    if (!ExtractPosition(pos_obj, &x, &y, nullptr, "pos")) {
        return NULL;
    }

    bool valid = false;
    sf::Vector2i step = self->data->stepFrom(x, y, &valid);

    if (!valid) {
        Py_RETURN_NONE;  // At root or unreachable
    }

    return PyVector(sf::Vector2f(static_cast<float>(step.x), static_cast<float>(step.y))).pyObject();
}

PyObject* UIGridPathfinding::DijkstraMap_get_root(PyDijkstraMapObject* self, void* closure) {
    if (!self->data) {
        Py_RETURN_NONE;
    }
    sf::Vector2i root = self->data->getRoot();
    return PyVector(sf::Vector2f(static_cast<float>(root.x), static_cast<float>(root.y))).pyObject();
}

PyObject* UIGridPathfinding::DijkstraMap_to_heightmap(PyDijkstraMapObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"size", "unreachable", nullptr};
    PyObject* size_obj = nullptr;
    float unreachable = -1.0f;  // Value for cells that can't reach root (distinct from 0 = root)

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|Of", const_cast<char**>(kwlist),
                                     &size_obj, &unreachable)) {
        return nullptr;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "DijkstraMap is invalid");
        return nullptr;
    }

    // Determine output size (default to dijkstra dimensions)
    int width = self->data->getWidth();
    int height = self->data->getHeight();

    if (width <= 0 || height <= 0) {
        PyErr_SetString(PyExc_RuntimeError, "DijkstraMap has invalid dimensions");
        return nullptr;
    }

    if (size_obj && size_obj != Py_None) {
        if (!PyPosition_FromObjectInt(size_obj, &width, &height)) {
            PyErr_SetString(PyExc_TypeError, "size must be (width, height) tuple, list, or Vector");
            return nullptr;
        }
        if (width <= 0 || height <= 0) {
            PyErr_SetString(PyExc_ValueError, "size values must be positive");
            return nullptr;
        }
    }

    // Create HeightMap via Python API (same pattern as BSP.to_heightmap)
    PyObject* hmap_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "HeightMap");
    if (!hmap_type) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap type not found");
        return nullptr;
    }

    PyObject* size_tuple = Py_BuildValue("(ii)", width, height);
    PyObject* hmap_args = PyTuple_Pack(1, size_tuple);
    Py_DECREF(size_tuple);

    PyHeightMapObject* hmap = (PyHeightMapObject*)PyObject_Call(hmap_type, hmap_args, nullptr);
    Py_DECREF(hmap_args);
    Py_DECREF(hmap_type);

    if (!hmap) {
        return nullptr;
    }

    // Get the dijkstra dimensions for bounds checking
    int dijkstra_w = self->data->getWidth();
    int dijkstra_h = self->data->getHeight();

    // Fill heightmap with distance values
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            float dist;
            if (x < dijkstra_w && y < dijkstra_h) {
                dist = self->data->getDistance(x, y);
                if (dist < 0) {
                    dist = unreachable;  // Unreachable cell
                }
            } else {
                dist = unreachable;  // Outside dijkstra bounds
            }
            TCOD_heightmap_set_value(hmap->heightmap, x, y, dist);
        }
    }

    return (PyObject*)hmap;
}

//=============================================================================
// Grid Factory Methods
//=============================================================================

PyObject* UIGridPathfinding::Grid_find_path(PyUIGridObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"start", "end", "diagonal_cost", NULL};
    PyObject* start_obj = NULL;
    PyObject* end_obj = NULL;
    float diagonal_cost = 1.41f;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO|f", const_cast<char**>(kwlist),
                                     &start_obj, &end_obj, &diagonal_cost)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Grid is invalid");
        return NULL;
    }

    int x1, y1, x2, y2;
    if (!ExtractPosition(start_obj, &x1, &y1, self->data.get(), "start")) {
        return NULL;
    }
    if (!ExtractPosition(end_obj, &x2, &y2, self->data.get(), "end")) {
        return NULL;
    }

    // Bounds check
    if (x1 < 0 || x1 >= self->data->grid_w || y1 < 0 || y1 >= self->data->grid_h ||
        x2 < 0 || x2 >= self->data->grid_w || y2 < 0 || y2 >= self->data->grid_h) {
        PyErr_SetString(PyExc_ValueError, "Position out of grid bounds");
        return NULL;
    }

    // Compute path using temporary TCODPath
    TCODPath tcod_path(self->data->getTCODMap(), diagonal_cost);
    if (!tcod_path.compute(x1, y1, x2, y2)) {
        Py_RETURN_NONE;  // No path exists
    }

    // Create AStarPath result object
    PyAStarPathObject* result = (PyAStarPathObject*)mcrfpydef::PyAStarPathType.tp_alloc(
        &mcrfpydef::PyAStarPathType, 0);
    if (!result) return NULL;

    // Initialize
    new (&result->path) std::vector<sf::Vector2i>();
    result->current_index = 0;
    result->origin = sf::Vector2i(x1, y1);
    result->destination = sf::Vector2i(x2, y2);

    // Copy path data
    result->path.reserve(tcod_path.size());
    for (int i = 0; i < tcod_path.size(); i++) {
        int px, py;
        tcod_path.get(i, &px, &py);
        result->path.push_back(sf::Vector2i(px, py));
    }

    return (PyObject*)result;
}

PyObject* UIGridPathfinding::Grid_get_dijkstra_map(PyUIGridObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"root", "diagonal_cost", NULL};
    PyObject* root_obj = NULL;
    float diagonal_cost = 1.41f;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|f", const_cast<char**>(kwlist),
                                     &root_obj, &diagonal_cost)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Grid is invalid");
        return NULL;
    }

    int root_x, root_y;
    if (!ExtractPosition(root_obj, &root_x, &root_y, self->data.get(), "root")) {
        return NULL;
    }

    // Bounds check
    if (root_x < 0 || root_x >= self->data->grid_w || root_y < 0 || root_y >= self->data->grid_h) {
        PyErr_SetString(PyExc_ValueError, "Root position out of grid bounds");
        return NULL;
    }

    auto key = std::make_pair(root_x, root_y);

    // Check cache
    auto it = self->data->dijkstra_maps.find(key);
    if (it != self->data->dijkstra_maps.end()) {
        // Check diagonal cost matches (or we could ignore this)
        if (std::abs(it->second->getDiagonalCost() - diagonal_cost) < 0.001f) {
            // Return existing
            PyDijkstraMapObject* result = (PyDijkstraMapObject*)mcrfpydef::PyDijkstraMapType.tp_alloc(
                &mcrfpydef::PyDijkstraMapType, 0);
            if (!result) return NULL;
            new (&result->data) std::shared_ptr<DijkstraMap>(it->second);
            return (PyObject*)result;
        }
        // Different diagonal cost - remove old one
        self->data->dijkstra_maps.erase(it);
    }

    // Create new DijkstraMap
    auto dijkstra = std::make_shared<DijkstraMap>(
        self->data->getTCODMap(), root_x, root_y, diagonal_cost);

    // Cache it
    self->data->dijkstra_maps[key] = dijkstra;

    // Return Python wrapper
    PyDijkstraMapObject* result = (PyDijkstraMapObject*)mcrfpydef::PyDijkstraMapType.tp_alloc(
        &mcrfpydef::PyDijkstraMapType, 0);
    if (!result) return NULL;

    new (&result->data) std::shared_ptr<DijkstraMap>(dijkstra);
    return (PyObject*)result;
}

PyObject* UIGridPathfinding::Grid_clear_dijkstra_maps(PyUIGridObject* self, PyObject* args) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Grid is invalid");
        return NULL;
    }

    self->data->dijkstra_maps.clear();
    Py_RETURN_NONE;
}

//=============================================================================
// Python Type Definitions
//=============================================================================

namespace mcrfpydef {

// AStarPath methods
PyMethodDef PyAStarPath_methods[] = {
    {"walk", (PyCFunction)UIGridPathfinding::AStarPath_walk, METH_NOARGS,
     "walk() -> Vector\n\n"
     "Get and consume next step in the path.\n\n"
     "Returns:\n"
     "    Next position as Vector.\n\n"
     "Raises:\n"
     "    IndexError: If path is exhausted."},

    {"peek", (PyCFunction)UIGridPathfinding::AStarPath_peek, METH_NOARGS,
     "peek() -> Vector\n\n"
     "See next step without consuming it.\n\n"
     "Returns:\n"
     "    Next position as Vector.\n\n"
     "Raises:\n"
     "    IndexError: If path is exhausted."},

    {NULL}
};

// AStarPath getsetters
PyGetSetDef PyAStarPath_getsetters[] = {
    {"origin", (getter)UIGridPathfinding::AStarPath_get_origin, NULL,
     "Starting position of the path (Vector, read-only).", NULL},

    {"destination", (getter)UIGridPathfinding::AStarPath_get_destination, NULL,
     "Ending position of the path (Vector, read-only).", NULL},

    {"remaining", (getter)UIGridPathfinding::AStarPath_get_remaining, NULL,
     "Number of steps remaining in the path (int, read-only).", NULL},

    {NULL}
};

// AStarPath number methods (for bool)
PyNumberMethods PyAStarPath_as_number = {
    .nb_bool = UIGridPathfinding::AStarPath_bool,
};

// AStarPath sequence methods (for len)
PySequenceMethods PyAStarPath_as_sequence = {
    .sq_length = (lenfunc)UIGridPathfinding::AStarPath_len,
};

// AStarPath type
PyTypeObject PyAStarPathType = {
    .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
    .tp_name = "mcrfpy.AStarPath",
    .tp_basicsize = sizeof(PyAStarPathObject),
    .tp_itemsize = 0,
    .tp_dealloc = (destructor)UIGridPathfinding::AStarPath_dealloc,
    .tp_repr = (reprfunc)UIGridPathfinding::AStarPath_repr,
    .tp_as_number = &PyAStarPath_as_number,
    .tp_as_sequence = &PyAStarPath_as_sequence,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_doc = PyDoc_STR(
        "A computed A* path result, consumed step by step.\n\n"
        "Created by Grid.find_path(). Cannot be instantiated directly.\n\n"
        "Use walk() to get and consume each step, or iterate directly.\n"
        "Use peek() to see the next step without consuming it.\n"
        "Use bool(path) or len(path) to check if steps remain.\n\n"
        "Properties:\n"
        "    origin (Vector): Starting position (read-only)\n"
        "    destination (Vector): Ending position (read-only)\n"
        "    remaining (int): Steps remaining (read-only)\n\n"
        "Example:\n"
        "    path = grid.find_path(start, end)\n"
        "    if path:\n"
        "        while path:\n"
        "            next_pos = path.walk()\n"
        "            entity.pos = next_pos"),
    .tp_iter = (getiterfunc)UIGridPathfinding::AStarPath_iter,
    .tp_methods = PyAStarPath_methods,
    .tp_getset = PyAStarPath_getsetters,
    .tp_init = (initproc)UIGridPathfinding::AStarPath_init,
    .tp_new = UIGridPathfinding::AStarPath_new,
};

// AStarPath iterator type
PyTypeObject PyAStarPathIterType = {
    .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
    .tp_name = "mcrfpy.AStarPathIterator",
    .tp_basicsize = sizeof(PyAStarPathIterObject),
    .tp_itemsize = 0,
    .tp_dealloc = (destructor)AStarPathIter_dealloc,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_iter = (getiterfunc)AStarPathIter_iter,
    .tp_iternext = (iternextfunc)AStarPathIter_next,
};

// DijkstraMap methods
PyMethodDef PyDijkstraMap_methods[] = {
    {"distance", (PyCFunction)UIGridPathfinding::DijkstraMap_distance, METH_VARARGS | METH_KEYWORDS,
     "distance(pos) -> float | None\n\n"
     "Get distance from position to root.\n\n"
     "Args:\n"
     "    pos: Position as Vector, Entity, or (x, y) tuple.\n\n"
     "Returns:\n"
     "    Float distance, or None if position is unreachable."},

    {"path_from", (PyCFunction)UIGridPathfinding::DijkstraMap_path_from, METH_VARARGS | METH_KEYWORDS,
     "path_from(pos) -> AStarPath\n\n"
     "Get full path from position to root.\n\n"
     "Args:\n"
     "    pos: Starting position as Vector, Entity, or (x, y) tuple.\n\n"
     "Returns:\n"
     "    AStarPath from pos toward root."},

    {"step_from", (PyCFunction)UIGridPathfinding::DijkstraMap_step_from, METH_VARARGS | METH_KEYWORDS,
     "step_from(pos) -> Vector | None\n\n"
     "Get single step from position toward root.\n\n"
     "Args:\n"
     "    pos: Current position as Vector, Entity, or (x, y) tuple.\n\n"
     "Returns:\n"
     "    Next position as Vector, or None if at root or unreachable."},

    {"to_heightmap", (PyCFunction)UIGridPathfinding::DijkstraMap_to_heightmap, METH_VARARGS | METH_KEYWORDS,
     "to_heightmap(size=None, unreachable=-1.0) -> HeightMap\n\n"
     "Convert distance field to a HeightMap.\n\n"
     "Each cell's height equals its pathfinding distance from the root.\n"
     "Useful for visualization, procedural terrain, or influence mapping.\n\n"
     "Args:\n"
     "    size: Optional (width, height) tuple. Defaults to dijkstra dimensions.\n"
     "    unreachable: Value for cells that cannot reach root (default -1.0).\n\n"
     "Returns:\n"
     "    HeightMap with distance values as heights."},

    {NULL}
};

// DijkstraMap getsetters
PyGetSetDef PyDijkstraMap_getsetters[] = {
    {"root", (getter)UIGridPathfinding::DijkstraMap_get_root, NULL,
     "Root position that distances are measured from (Vector, read-only).", NULL},

    {NULL}
};

// DijkstraMap type
PyTypeObject PyDijkstraMapType = {
    .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
    .tp_name = "mcrfpy.DijkstraMap",
    .tp_basicsize = sizeof(PyDijkstraMapObject),
    .tp_itemsize = 0,
    .tp_dealloc = (destructor)UIGridPathfinding::DijkstraMap_dealloc,
    .tp_repr = (reprfunc)UIGridPathfinding::DijkstraMap_repr,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_doc = PyDoc_STR(
        "A Dijkstra distance map from a fixed root position.\n\n"
        "Created by Grid.get_dijkstra_map(). Cannot be instantiated directly.\n\n"
        "Grid caches these maps - multiple requests for the same root return\n"
        "the same map. Call Grid.clear_dijkstra_maps() after changing grid\n"
        "walkability to invalidate the cache.\n\n"
        "Properties:\n"
        "    root (Vector): Root position (read-only)\n\n"
        "Methods:\n"
        "    distance(pos) -> float | None: Get distance to root\n"
        "    path_from(pos) -> AStarPath: Get full path to root\n"
        "    step_from(pos) -> Vector | None: Get single step toward root\n\n"
        "Example:\n"
        "    dijkstra = grid.get_dijkstra_map(player.pos)\n"
        "    for enemy in enemies:\n"
        "        dist = dijkstra.distance(enemy.pos)\n"
        "        if dist and dist < 10:\n"
        "            step = dijkstra.step_from(enemy.pos)\n"
        "            if step:\n"
        "                enemy.pos = step"),
    .tp_methods = PyDijkstraMap_methods,
    .tp_getset = PyDijkstraMap_getsetters,
    .tp_init = (initproc)UIGridPathfinding::DijkstraMap_init,
    .tp_new = UIGridPathfinding::DijkstraMap_new,
};

} // namespace mcrfpydef
