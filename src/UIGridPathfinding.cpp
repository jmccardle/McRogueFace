#include "UIGridPathfinding.h"
#include "UIGrid.h"
#include "UIEntity.h"
#include "PyVector.h"
#include "McRFPy_API.h"
#include "PyHeightMap.h"
#include "PyPositionHelper.h"
#include "PyHeuristic.h"
#include "PyDiscreteMap.h"

//=============================================================================
// DijkstraMap Implementation
//=============================================================================

DijkstraMap::DijkstraMap(TCODMap* map, int root_x, int root_y, float diag_cost)
    : tcod_dijkstra(nullptr)
    , tcod_map(map)
    , root(root_x, root_y)
    , diagonal_cost(diag_cost)
    , map_width(map ? map->getWidth() : 0)
    , map_height(map ? map->getHeight() : 0)
{
    roots.push_back(sf::Vector2i(root_x, root_y));
    if (tcod_map) {
        tcod_dijkstra = TCOD_dijkstra_new(tcod_map->data, diagonal_cost);
        TCOD_dijkstra_compute(tcod_dijkstra, root_x, root_y);
    }
}

DijkstraMap::DijkstraMap(TCODMap* map, const std::vector<sf::Vector2i>& roots_in, float diag_cost)
    : tcod_dijkstra(nullptr)
    , tcod_map(map)
    , root(roots_in.empty() ? sf::Vector2i(-1, -1) : roots_in.front())
    , roots(roots_in)
    , diagonal_cost(diag_cost)
    , map_width(map ? map->getWidth() : 0)
    , map_height(map ? map->getHeight() : 0)
{
    if (!tcod_map || roots.empty()) return;

    tcod_dijkstra = TCOD_dijkstra_new(tcod_map->data, diagonal_cost);

    if (roots.size() == 1) {
        TCOD_dijkstra_compute(tcod_dijkstra, roots[0].x, roots[0].y);
    } else {
        std::vector<int> xs, ys;
        xs.reserve(roots.size());
        ys.reserve(roots.size());
        for (auto& r : roots) { xs.push_back(r.x); ys.push_back(r.y); }
        TCOD_dijkstra_compute_multi(tcod_dijkstra,
            static_cast<int>(roots.size()), xs.data(), ys.data());
    }
}

DijkstraMap::~DijkstraMap() {
    if (tcod_dijkstra) {
        TCOD_dijkstra_delete(tcod_dijkstra);
        tcod_dijkstra = nullptr;
    }
}

float DijkstraMap::getDistance(int x, int y) const {
    if (!tcod_dijkstra) return -1.0f;
    return TCOD_dijkstra_get_distance(tcod_dijkstra, x, y);
}

std::vector<sf::Vector2i> DijkstraMap::getPathFrom(int x, int y) const {
    std::vector<sf::Vector2i> path;
    if (!tcod_dijkstra) return path;

    if (TCOD_dijkstra_path_set(tcod_dijkstra, x, y)) {
        int px, py;
        while (TCOD_dijkstra_path_walk(tcod_dijkstra, &px, &py)) {
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

    if (!TCOD_dijkstra_path_set(tcod_dijkstra, x, y)) {
        if (valid) *valid = false;
        return sf::Vector2i(-1, -1);
    }

    int px, py;
    if (TCOD_dijkstra_path_walk(tcod_dijkstra, &px, &py)) {
        if (valid) *valid = true;
        return sf::Vector2i(px, py);
    }

    if (valid) *valid = false;
    return sf::Vector2i(-1, -1);
}

void DijkstraMap::invertInPlace() {
    if (tcod_dijkstra) {
        TCOD_dijkstra_invert(tcod_dijkstra);
    }
}

std::shared_ptr<DijkstraMap> DijkstraMap::inverted() const {
    // Recompute from the stored roots, then invert. This preserves the invariant that
    // the original's distance field is unchanged.
    auto copy = std::make_shared<DijkstraMap>(tcod_map, roots, diagonal_cost);
    copy->invertInPlace();
    return copy;
}

sf::Vector2i DijkstraMap::descentStep(int x, int y, bool* valid) const {
    if (!tcod_dijkstra) {
        if (valid) *valid = false;
        return sf::Vector2i(-1, -1);
    }
    int out_x = -1, out_y = -1;
    bool ok = TCOD_dijkstra_get_descent(tcod_dijkstra, x, y, &out_x, &out_y);
    if (valid) *valid = ok;
    if (!ok) return sf::Vector2i(-1, -1);
    return sf::Vector2i(out_x, out_y);
}

//=============================================================================
// Helper Functions
//=============================================================================

bool UIGridPathfinding::ExtractPosition(PyObject* obj, int* x, int* y,
                                        UIGrid* expected_grid,
                                        const char* arg_name) {
    // Check if it's an Entity
    if (PyObject_IsInstance(obj, (PyObject*)&mcrfpydef::PyUIEntityType)) {
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

    // Check if it's a Vector
    if (PyObject_IsInstance(obj, (PyObject*)&mcrfpydef::PyVectorType)) {
        auto* vec = (PyVectorObject*)obj;
        *x = static_cast<int>(vec->data.x);
        *y = static_cast<int>(vec->data.y);
        return true;
    }

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

// #311: Reject out-of-bounds coordinates at the Python boundary. TCOD's
// dijkstra routines assert and abort() the process for invalid coords, so
// catching them here turns a fatal crash into a recoverable IndexError.
static bool dijkstra_bounds_check(DijkstraMap* dmap, int x, int y) {
    int w = dmap->getWidth();
    int h = dmap->getHeight();
    if (x < 0 || y < 0 || x >= w || y >= h) {
        PyErr_Format(PyExc_IndexError,
            "coordinate (%d, %d) out of bounds for DijkstraMap of size %dx%d",
            x, y, w, h);
        return false;
    }
    return true;
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

    if (!dijkstra_bounds_check(self->data.get(), x, y)) return NULL;

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

    if (!dijkstra_bounds_check(self->data.get(), x, y)) return NULL;

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

    if (!dijkstra_bounds_check(self->data.get(), x, y)) return NULL;

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

PyObject* UIGridPathfinding::DijkstraMap_invert(PyDijkstraMapObject* self, PyObject* args) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "DijkstraMap is invalid");
        return nullptr;
    }
    auto new_map = self->data->inverted();
    if (!new_map) {
        PyErr_SetString(PyExc_RuntimeError, "invert() failed");
        return nullptr;
    }
    PyDijkstraMapObject* result = (PyDijkstraMapObject*)mcrfpydef::PyDijkstraMapType.tp_alloc(
        &mcrfpydef::PyDijkstraMapType, 0);
    if (!result) return nullptr;
    new (&result->data) std::shared_ptr<DijkstraMap>(new_map);
    return (PyObject*)result;
}

PyObject* UIGridPathfinding::DijkstraMap_descent_step(PyDijkstraMapObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"pos", nullptr};
    PyObject* pos_obj = nullptr;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O", const_cast<char**>(kwlist), &pos_obj)) {
        return nullptr;
    }
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "DijkstraMap is invalid");
        return nullptr;
    }
    int x, y;
    if (!ExtractPosition(pos_obj, &x, &y, nullptr, "pos")) {
        return nullptr;
    }
    if (!dijkstra_bounds_check(self->data.get(), x, y)) return nullptr;

    bool valid = false;
    sf::Vector2i step = self->data->descentStep(x, y, &valid);
    if (!valid) {
        Py_RETURN_NONE;
    }
    return PyVector(sf::Vector2f(static_cast<float>(step.x),
                                 static_cast<float>(step.y))).pyObject();
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

    // Create HeightMap via Python API
    PyObject* size_tuple = Py_BuildValue("(ii)", width, height);
    PyObject* hmap_args = PyTuple_Pack(1, size_tuple);
    Py_DECREF(size_tuple);

    PyHeightMapObject* hmap = (PyHeightMapObject*)PyObject_Call((PyObject*)&mcrfpydef::PyHeightMapType, hmap_args, nullptr);
    Py_DECREF(hmap_args);

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

// Helper: collect cells occupied by entities with a given label, mark non-walkable.
// Returns the list of (x, y, was_walkable) for restoration.
static std::vector<std::tuple<int,int,bool>> markCollisionLabel(
    GridData* grid, const std::string& collide_label)
{
    std::vector<std::tuple<int,int,bool>> restore_list;
    if (!grid->entities || collide_label.empty()) return restore_list;

    TCODMap* tcod_map = grid->getTCODMap();
    if (!tcod_map) return restore_list;

    for (auto& entity : *grid->entities) {
        if (!entity) continue;
        if (entity->labels.count(collide_label)) {
            int ex = entity->cell_position.x;
            int ey = entity->cell_position.y;
            if (ex >= 0 && ex < grid->grid_w && ey >= 0 && ey < grid->grid_h) {
                bool was_walkable = tcod_map->isWalkable(ex, ey);
                if (was_walkable) {
                    tcod_map->setProperties(ex, ey, tcod_map->isTransparent(ex, ey), false);
                    restore_list.emplace_back(ex, ey, true);
                }
            }
        }
    }
    return restore_list;
}

// Helper: restore walkability after pathfinding.
static void restoreCollisionLabel(GridData* grid,
    const std::vector<std::tuple<int,int,bool>>& restore_list)
{
    TCODMap* tcod_map = grid->getTCODMap();
    if (!tcod_map) return;

    for (auto& [x, y, was_walkable] : restore_list) {
        tcod_map->setProperties(x, y, tcod_map->isTransparent(x, y), was_walkable);
    }
}

PyObject* UIGridPathfinding::Grid_find_path(PyUIGridObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"start", "end", "diagonal_cost", "collide",
                                   "heuristic", "weight", NULL};
    PyObject* start_obj = NULL;
    PyObject* end_obj = NULL;
    float diagonal_cost = 1.41f;
    const char* collide_label = NULL;
    PyObject* heuristic_obj = NULL;
    float heuristic_weight = 1.0f;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO|fzOf", const_cast<char**>(kwlist),
                                     &start_obj, &end_obj, &diagonal_cost, &collide_label,
                                     &heuristic_obj, &heuristic_weight)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Grid is invalid");
        return NULL;
    }

    if (heuristic_weight <= 0.0f) {
        PyErr_SetString(PyExc_ValueError, "weight must be positive");
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

    // Resolve heuristic selection before any allocations so we fail fast on bad args.
    TCOD_heuristic_func_t heuristic_func = nullptr;
    if (heuristic_obj && heuristic_obj != Py_None) {
        int hval = 0;
        if (!PyHeuristic::from_arg(heuristic_obj, &hval)) {
            return NULL;
        }
        heuristic_func = PyHeuristic::get_function(hval);
    }

    // Mark-and-restore: temporarily block cells occupied by entities with collide label
    std::string label_str = collide_label ? collide_label : "";
    auto restore_list = markCollisionLabel(self->data.get(), label_str);

    TCODMap* tcmap = self->data->getTCODMap();

    // Build path handle. Use C API so we can set the heuristic/weight when requested.
    TCOD_path_t tcod_path = TCOD_path_new_using_map(tcmap->data, diagonal_cost);
    if (heuristic_func || heuristic_weight != 1.0f) {
        // Passing null heuristic_func keeps the default (Euclidean) while still allowing
        // weight override; non-null installs the chosen built-in.
        TCOD_path_set_heuristic(tcod_path, heuristic_func, heuristic_weight);
    }

    bool found = TCOD_path_compute(tcod_path, x1, y1, x2, y2);

    // Restore walkability before returning
    restoreCollisionLabel(self->data.get(), restore_list);

    if (!found) {
        TCOD_path_delete(tcod_path);
        Py_RETURN_NONE;
    }

    PyAStarPathObject* result = (PyAStarPathObject*)mcrfpydef::PyAStarPathType.tp_alloc(
        &mcrfpydef::PyAStarPathType, 0);
    if (!result) {
        TCOD_path_delete(tcod_path);
        return NULL;
    }

    new (&result->path) std::vector<sf::Vector2i>();
    result->current_index = 0;
    result->origin = sf::Vector2i(x1, y1);
    result->destination = sf::Vector2i(x2, y2);

    int size = TCOD_path_size(tcod_path);
    result->path.reserve(size);
    for (int i = 0; i < size; i++) {
        int px, py;
        TCOD_path_get(tcod_path, i, &px, &py);
        result->path.push_back(sf::Vector2i(px, py));
    }

    TCOD_path_delete(tcod_path);
    return (PyObject*)result;
}

// Collect roots from a Python object, which may be:
//   - a single (x,y) (tuple/list/Vector/Entity)
//   - a list/iterable of (x,y) positions
//   - a DiscreteMap mask (non-zero cells become roots)
// Returns true on success; populates `out_roots` and `out_mask_used`.
// If a DiscreteMap mask is used, caller should prefer the masked C path.
static bool collectRoots(PyObject* root_obj, UIGrid* grid,
                         std::vector<sf::Vector2i>* out_roots,
                         PyDiscreteMapObject** out_mask)
{
    out_roots->clear();
    if (out_mask) *out_mask = nullptr;

    // DiscreteMap mask path
    if (PyObject_IsInstance(root_obj, (PyObject*)&mcrfpydef::PyDiscreteMapType)) {
        auto* dmap = (PyDiscreteMapObject*)root_obj;
        if (!dmap->data) {
            PyErr_SetString(PyExc_RuntimeError, "DiscreteMap is invalid");
            return false;
        }
        if (dmap->data->width() != grid->grid_w || dmap->data->height() != grid->grid_h) {
            PyErr_Format(PyExc_ValueError,
                "DiscreteMap size (%dx%d) does not match grid size (%dx%d)",
                dmap->data->width(), dmap->data->height(),
                grid->grid_w, grid->grid_h);
            return false;
        }
        if (out_mask) *out_mask = dmap;
        return true;
    }

    // Single position path (Vector / Entity / (x,y) tuple): ExtractPosition accepts these.
    int x = 0, y = 0;
    if (UIGridPathfinding::ExtractPosition(root_obj, &x, &y, grid, "root")) {
        if (x < 0 || x >= grid->grid_w || y < 0 || y >= grid->grid_h) {
            PyErr_SetString(PyExc_ValueError, "Root position out of grid bounds");
            return false;
        }
        out_roots->push_back(sf::Vector2i(x, y));
        return true;
    }
    // ExtractPosition set an error - clear it only if we still have an iterable to try.
    if (!PyErr_ExceptionMatches(PyExc_TypeError)) {
        return false;
    }
    PyErr_Clear();

    // List/iterable of positions
    if (PySequence_Check(root_obj) || PyIter_Check(root_obj)) {
        PyObject* iter = PyObject_GetIter(root_obj);
        if (!iter) {
            PyErr_SetString(PyExc_TypeError,
                "roots must be (x,y), a sequence of (x,y), or a DiscreteMap mask");
            return false;
        }
        PyObject* item;
        while ((item = PyIter_Next(iter)) != NULL) {
            int rx = 0, ry = 0;
            if (!UIGridPathfinding::ExtractPosition(item, &rx, &ry, grid, "root")) {
                Py_DECREF(item);
                Py_DECREF(iter);
                return false;
            }
            Py_DECREF(item);
            if (rx < 0 || rx >= grid->grid_w || ry < 0 || ry >= grid->grid_h) {
                Py_DECREF(iter);
                PyErr_Format(PyExc_ValueError,
                    "Root (%d,%d) out of grid bounds", rx, ry);
                return false;
            }
            out_roots->push_back(sf::Vector2i(rx, ry));
        }
        Py_DECREF(iter);
        if (PyErr_Occurred()) return false;
        if (out_roots->empty()) {
            PyErr_SetString(PyExc_ValueError, "roots sequence is empty");
            return false;
        }
        return true;
    }

    PyErr_SetString(PyExc_TypeError,
        "roots must be (x,y), a sequence of (x,y), or a DiscreteMap mask");
    return false;
}

PyObject* UIGridPathfinding::Grid_get_dijkstra_map(PyUIGridObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"root", "diagonal_cost", "collide", "roots", NULL};
    PyObject* root_obj = NULL;
    PyObject* roots_obj = NULL;
    float diagonal_cost = 1.41f;
    const char* collide_label = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OfzO", const_cast<char**>(kwlist),
                                     &root_obj, &diagonal_cost, &collide_label, &roots_obj)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Grid is invalid");
        return NULL;
    }

    // Accept either `root=` (back-compat, also accepts multi-input now) or `roots=`.
    PyObject* input_obj = roots_obj ? roots_obj : root_obj;
    if (!input_obj) {
        PyErr_SetString(PyExc_TypeError,
            "get_dijkstra_map() requires 'root' or 'roots' argument");
        return NULL;
    }
    if (roots_obj && root_obj) {
        PyErr_SetString(PyExc_TypeError,
            "get_dijkstra_map(): pass 'root' or 'roots', not both");
        return NULL;
    }

    std::vector<sf::Vector2i> roots;
    PyDiscreteMapObject* mask_obj = nullptr;
    if (!collectRoots(input_obj, self->data.get(), &roots, &mask_obj)) {
        return NULL;
    }

    std::string label_str = collide_label ? collide_label : "";

    // Cache path for the common single-root case (preserves prior behavior).
    if (!mask_obj && roots.size() == 1) {
        auto key = std::make_tuple(roots[0].x, roots[0].y, label_str);
        auto it = self->data->dijkstra_maps.find(key);
        if (it != self->data->dijkstra_maps.end()) {
            if (std::abs(it->second->getDiagonalCost() - diagonal_cost) < 0.001f) {
                PyDijkstraMapObject* result = (PyDijkstraMapObject*)mcrfpydef::PyDijkstraMapType.tp_alloc(
                    &mcrfpydef::PyDijkstraMapType, 0);
                if (!result) return NULL;
                new (&result->data) std::shared_ptr<DijkstraMap>(it->second);
                return (PyObject*)result;
            }
            self->data->dijkstra_maps.erase(it);
        }
    }

    auto restore_list = markCollisionLabel(self->data.get(), label_str);

    std::shared_ptr<DijkstraMap> dijkstra;
    TCODMap* tcmap = self->data->getTCODMap();

    if (mask_obj) {
        // Translate mask -> explicit root list, then drive compute_multi. Distance-only
        // results are identical to compute_masked; this keeps DijkstraMap's invariant
        // that it always holds exactly one computed TCOD_Dijkstra handle.
        std::vector<sf::Vector2i> mask_roots;
        const uint8_t* buf = mask_obj->data->data();
        int w = mask_obj->data->width();
        int h = mask_obj->data->height();
        mask_roots.reserve(static_cast<size_t>(w) * 4);  // heuristic
        for (int y = 0; y < h; y++) {
            for (int x = 0; x < w; x++) {
                if (buf[y * w + x] != 0) {
                    mask_roots.push_back(sf::Vector2i(x, y));
                }
            }
        }
        if (mask_roots.empty()) {
            restoreCollisionLabel(self->data.get(), restore_list);
            PyErr_SetString(PyExc_ValueError, "DiscreteMap mask has no non-zero cells");
            return NULL;
        }
        dijkstra = std::make_shared<DijkstraMap>(tcmap, mask_roots, diagonal_cost);
    } else {
        dijkstra = std::make_shared<DijkstraMap>(tcmap, roots, diagonal_cost);
    }

    restoreCollisionLabel(self->data.get(), restore_list);

    // Cache only single-root case
    if (!mask_obj && roots.size() == 1) {
        auto key = std::make_tuple(roots[0].x, roots[0].y, label_str);
        self->data->dijkstra_maps[key] = dijkstra;
    }

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

    {"invert", (PyCFunction)UIGridPathfinding::DijkstraMap_invert, METH_NOARGS,
     "invert() -> DijkstraMap\n\n"
     "Return a NEW DijkstraMap whose distance field is the safety field.\n\n"
     "Cells near a root become high values and cells far from any root become\n"
     "low values. Combined with step_from or descent_step, this gives flee\n"
     "behavior: descend the inverted map to move away from the original roots.\n\n"
     "The original DijkstraMap is unchanged.\n\n"
     "Returns:\n"
     "    New DijkstraMap with inverted distances."},

    {"descent_step", (PyCFunction)UIGridPathfinding::DijkstraMap_descent_step, METH_VARARGS | METH_KEYWORDS,
     "descent_step(pos) -> Vector | None\n\n"
     "Get the adjacent cell with the lowest distance (steepest descent).\n\n"
     "Unlike step_from (which follows the path set by path_from), descent_step\n"
     "always returns the best neighbor in a single hop. Useful for AI that\n"
     "reacts to the current distance field rather than following a fixed path.\n\n"
     "Args:\n"
     "    pos: Current position as Vector, Entity, or (x, y) tuple.\n\n"
     "Returns:\n"
     "    Next position as Vector, or None if pos is a local minimum or off-grid."},

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
