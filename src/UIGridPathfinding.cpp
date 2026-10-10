#include "UIGridPathfinding.h"
#include "PyGridData.h"
#include "UIEntity.h"
#include "PyVector.h"
#include "McRFPy_API.h"
#include "PyHeightMap.h"
#include "PyPositionHelper.h"
#include "PyHeuristic.h"
#include "MapOps.h"
#include "PyDiscreteMap.h"
#include "McRFPy_Doc.h"
#include "PyWrap.h"
#include <algorithm>
#include <climits>
#include <cstdlib>
#include <cstring>

//=============================================================================
// DijkstraMap Implementation
//=============================================================================

static constexpr unsigned int DIJKSTRA_INF = 0xFFFFFFFFu;  // libtcod's "no distance"

// libtcod's neighbour order; descent keeps it so ties break exactly as before (#445).
static const int DESCENT_DX[8] = {-1, 0, 1, 0, -1, 1, 1, -1};
static const int DESCENT_DY[8] = {0, -1, 0, 1, -1, -1, 1, 1};

DijkstraMap::DijkstraMap(const std::shared_ptr<GridData>& g, const std::vector<sf::Vector2i>& roots_in,
                         float diag_cost, int radius_in, int heuristic_in,
                         const std::vector<sf::Vector2i>& blocked)
    : tcod_dijkstra(nullptr)
    , root(roots_in.empty() ? sf::Vector2i(-1, -1) : roots_in.front())
    , roots(roots_in)
    , diagonal_cost(diag_cost)
    , radius(radius_in)
    , heuristic(heuristic_in)
    , grid(g)
{
    if (!g || roots.empty()) return;

    // The window: the roots' bounding box grown by `radius`, clipped to the grid. A
    // radius past the grid's own size changes nothing, so clamp it before the
    // arithmetic can overflow.
    const int r = std::min(radius, std::max(g->grid_w, g->grid_h));
    int minx = roots[0].x, maxx = roots[0].x, miny = roots[0].y, maxy = roots[0].y;
    for (const auto& p : roots) {
        minx = std::min(minx, p.x); maxx = std::max(maxx, p.x);
        miny = std::min(miny, p.y); maxy = std::max(maxy, p.y);
    }
    const MapRegion win = MapRegion::window(minx - r, miny - r, maxx + r + 1, maxy + r + 1,
                                            g->grid_w, g->grid_h);
    win_x = win.src_x; win_y = win.src_y; win_w = win.width; win_h = win.height;
    if (win_w <= 0 || win_h <= 0) return;

    // Exact threshold, in libtcod's integer hundredths: a path costing at most r steps'
    // worth never leaves the window, since every step costs at least min(cardinal,
    // diagonal) and moves the Chebyshev distance by at most 1.
    const int diag_units = static_cast<int>(diagonal_cost * 100.0f + 0.1f);  // as libtcod
    const unsigned int step_units = diag_units > 0 ? std::min(100, diag_units) : 100;
    const unsigned long long limit = static_cast<unsigned long long>(r) * step_units;
    threshold = static_cast<float>(limit) * 0.01f;

    // A window-sized copy of the walkable plane, with the collide= cells blocked. The
    // grid's own TCODMap is never touched (it used to be marked and restored).
    TCODMap window(win_w, win_h);
    for (int y = 0; y < win_h; y++) {
        for (int x = 0; x < win_w; x++) {
            window.setProperties(x, y, false, g->walkable_plane[win.src_idx(x, y)] != 0);
        }
    }
    for (const auto& c : blocked) {
        const int bx = c.x - win_x, by = c.y - win_y;
        if (bx >= 0 && by >= 0 && bx < win_w && by < win_h) window.setProperties(bx, by, false, false);
    }

    tcod_dijkstra = TCOD_dijkstra_new(window.data, diagonal_cost);
    if (roots.size() == 1) {
        TCOD_dijkstra_compute(tcod_dijkstra, roots[0].x - win_x, roots[0].y - win_y);
    } else {
        std::vector<int> xs, ys;
        xs.reserve(roots.size());
        ys.reserve(roots.size());
        for (auto& p : roots) { xs.push_back(p.x - win_x); ys.push_back(p.y - win_y); }
        TCOD_dijkstra_compute_multi(tcod_dijkstra,
            static_cast<int>(roots.size()), xs.data(), ys.data());
    }

    // Complete = the flood never reached a window edge that is not also a grid edge, so
    // the roots' whole reachable region is inside: every distance is exact (even past
    // the threshold) and every cell it missed is certainly unreachable.
    unsigned int* dist = tcod_dijkstra->distances;
    auto reached = [&](int wx, int wy) { return dist[wy * win_w + wx] != DIJKSTRA_INF; };
    complete = true;
    for (int wy = 0; wy < win_h && complete; wy++) {
        if ((win_x > 0 && reached(0, wy)) ||
            (win_x + win_w < g->grid_w && reached(win_w - 1, wy))) complete = false;
    }
    for (int wx = 0; wx < win_w && complete; wx++) {
        if ((win_y > 0 && reached(wx, 0)) ||
            (win_y + win_h < g->grid_h && reached(wx, win_h - 1))) complete = false;
    }
    if (!complete) {
        // Cut at the threshold (#445 decision): every value kept is exact.
        const size_t n = static_cast<size_t>(win_w) * win_h;
        for (size_t i = 0; i < n; i++) {
            if (dist[i] != DIJKSTRA_INF && dist[i] > limit) dist[i] = DIJKSTRA_INF;
        }
    }
    finish(tcod_dijkstra);
}

// #425: libtcod reads the map and the work queue (`nodes`) only while computing;
// path_set/walk, get_descent, get_distance and invert use `distances` alone. Dropping
// both leaves a finished field: 4 bytes per cell instead of 11, and no pointer into the
// grid -- that pointer was the use-after-free when a map outlived its grid.
void DijkstraMap::finish(TCOD_Dijkstra* d)
{
    free(d->nodes);  // libtcod's own malloc (same toolchain/CRT on every target)
    d->nodes = nullptr;
    d->map = nullptr;
}

DijkstraMap::DijkstraMap(const DijkstraMap& src, CopyField)
    : tcod_dijkstra(nullptr)
    , root(src.root)
    , roots(src.roots)
    , diagonal_cost(src.diagonal_cost)
    , radius(src.radius)
    , heuristic(src.heuristic)
    , win_x(src.win_x), win_y(src.win_y), win_w(src.win_w), win_h(src.win_h)
    , threshold(src.threshold)
    , complete(src.complete)
    , is_inverted(src.is_inverted)
    , inverted_max(src.inverted_max)
    , grid(src.grid)
{
    const TCOD_Dijkstra* from = src.tcod_dijkstra;
    if (!from) return;
    // Laid out exactly as TCOD_dijkstra_new() builds one, minus map and nodes, so
    // TCOD_dijkstra_delete() frees it the same way.
    auto* d = static_cast<TCOD_Dijkstra*>(malloc(sizeof(TCOD_Dijkstra)));
    if (!d) return;
    *d = *from;
    d->map = nullptr;
    d->nodes = nullptr;
    const size_t bytes = static_cast<size_t>(from->nodes_max) * sizeof(unsigned int);
    d->distances = static_cast<unsigned int*>(malloc(bytes));
    d->path = TCOD_list_new();
    if (!d->distances || !d->path) {
        free(d->distances);
        if (d->path) TCOD_list_delete(d->path);
        free(d);
        return;
    }
    memcpy(d->distances, from->distances, bytes);
    tcod_dijkstra = d;
}

DijkstraMap::~DijkstraMap() {
    if (serial_number != 0) mcrf::unregister_wrapper(serial_number);
    if (tcod_dijkstra) {
        TCOD_dijkstra_delete(tcod_dijkstra);
        tcod_dijkstra = nullptr;
    }
}

bool DijkstraMap::inField(int x, int y, float* d) const {
    const long long wx = (long long)x - win_x, wy = (long long)y - win_y;
    if (!tcod_dijkstra || wx < 0 || wy < 0 || wx >= win_w || wy >= win_h) return false;
    const unsigned int v = tcod_dijkstra->distances[wy * win_w + wx];
    if (v == DIJKSTRA_INF) return false;
    if (d) *d = static_cast<float>(v) * 0.01f;  // libtcod's own conversion
    return true;
}

float DijkstraMap::fieldAtWindow(int wx, int wy) const {
    float d;
    return inField(wx + win_x, wy + win_y, &d) ? d : -1.0f;
}

float DijkstraMap::estimateAt(int x, int y) const {
    // Nearest root, floored at the threshold: a cell beyond the exact field is, by
    // construction, farther than the threshold from every root.
    float best = -1.0f;
    for (const auto& p : roots) {
        const float e = PyHeuristic::estimate(heuristic, double(x) - p.x, double(y) - p.y,
                                              diagonal_cost);
        if (best < 0.0f || e < best) best = e;
    }
    return std::max(best, threshold);
}

DijkstraMap::Value DijkstraMap::valueAt(int x, int y) const {
    float d;
    if (inField(x, y, &d)) return {Kind::EXACT, d};
    if (complete) return {Kind::UNREACHABLE, 0.0f};
    if (heuristic == NO_HEURISTIC) return {Kind::UNKNOWN, 0.0f};
    const float e = estimateAt(x, y);
    return {Kind::ESTIMATE, is_inverted ? inverted_max - e : e};
}

bool DijkstraMap::isExact(int x, int y) const {
    const Kind k = valueAt(x, y).kind;
    return k == Kind::EXACT || k == Kind::UNREACHABLE;
}

// #375: emit the path in origin->destination order, matching find_path()'s convention
// (excludes the origin, includes the root).
//
// libtcod builds its internal list as [pos, ..., root_adjacent] and
// TCOD_dijkstra_path_walk() pops from the BACK, so walking yields
// [root_adjacent, ..., pos] -- the exact reverse of what path_from's docstring,
// AStarPath.origin/.destination, and step_from all promise. stepFrom() inherited the
// error and returned a cell adjacent to the ROOT rather than to the query position,
// i.e. an arbitrarily long teleport.
std::vector<sf::Vector2i> DijkstraMap::getPathFrom(int x, int y) const {
    std::vector<sf::Vector2i> path;
    if (!inField(x, y, nullptr)) return path;  // #445: no exact path beyond the field

    if (TCOD_dijkstra_path_set(tcod_dijkstra, x - win_x, y - win_y)) {
        int px, py;
        while (TCOD_dijkstra_path_walk(tcod_dijkstra, &px, &py)) {
            path.push_back(sf::Vector2i(px + win_x, py + win_y));
        }
    }
    if (path.empty()) return path;  // already at a root, or unreachable

    std::reverse(path.begin(), path.end());  // -> [pos, ..., root_adjacent]
    path.erase(path.begin());                // drop the origin

    // The walk stops one cell short of the root. Append the root this path descends
    // into -- via descentStep, so the multi-root case lands on the correct root.
    bool ok = false;
    sf::Vector2i last = path.empty() ? sf::Vector2i(x, y) : path.back();
    sf::Vector2i root_cell = descentStep(last.x, last.y, &ok);
    if (ok) path.push_back(root_cell);

    return path;
}

sf::Vector2i DijkstraMap::stepFrom(int x, int y, bool* valid) const {
    if (inField(x, y, nullptr)) {
        // #375: the first cell of the corrected path -- guaranteed adjacent to (x, y).
        std::vector<sf::Vector2i> path = getPathFrom(x, y);
        if (!path.empty()) {
            if (valid) *valid = true;
            return path.front();
        }
        if (valid) *valid = false;
        return sf::Vector2i(-1, -1);
    }
    return descentStep(x, y, valid);  // #445: greedy beyond the field
}

void DijkstraMap::invertInPlace() {
    if (!tcod_dijkstra) return;
    unsigned int max_d = 0;
    const size_t n = static_cast<size_t>(win_w) * win_h;
    for (size_t i = 0; i < n; i++) {
        const unsigned int v = tcod_dijkstra->distances[i];
        if (v != DIJKSTRA_INF && v > max_d) max_d = v;
    }
    TCOD_dijkstra_invert(tcod_dijkstra);  // the same max, so the field and estimate agree
    inverted_max = static_cast<float>(max_d) * 0.01f;
    is_inverted = true;
}

std::shared_ptr<DijkstraMap> DijkstraMap::inverted() const {
    // Copy the distance field and invert the copy; the original is unchanged. (#425:
    // this used to recompute from the grid's live map -- a full Dijkstra, against
    // walkability that may have changed since, without the collide= marks.)
    auto copy = std::make_shared<DijkstraMap>(*this, CopyField{});
    if (!copy->tcod_dijkstra) return nullptr;  // out of memory
    copy->invertInPlace();
    return copy;
}

// The lowest-valued neighbour strictly lower than (x, y). In the exact field this is
// libtcod's get_descent (same order, same ties; ordered on the raw distances). #445:
// a neighbour beyond the field is a candidate only while the grid is alive and the
// cell is walkable now -- in the field, walkability was settled when it was computed.
sf::Vector2i DijkstraMap::descentStep(int x, int y, bool* valid) const {
    if (valid) *valid = false;
    const Value here = valueAt(x, y);
    if (here.kind != Kind::EXACT && here.kind != Kind::ESTIMATE) return {-1, -1};

    // Order on doubles: an exact distance is raw * 0.01 without float32 rounding, so
    // ties and order match libtcod's integer comparison.
    auto key = [&](int px, int py, Kind* kind) -> double {
        const long long wx = (long long)px - win_x, wy = (long long)py - win_y;
        if (tcod_dijkstra && wx >= 0 && wy >= 0 && wx < win_w && wy < win_h) {
            const unsigned int v = tcod_dijkstra->distances[wy * win_w + wx];
            if (v != DIJKSTRA_INF) { *kind = Kind::EXACT; return v * 0.01; }
        }
        const Value val = valueAt(px, py);
        *kind = val.kind;
        return val.value;
    };

    Kind k;
    double best = key(x, y, &k);
    auto g = grid.lock();
    const int n_dirs = diag_dirs();
    int best_i = -1;
    for (int i = 0; i < n_dirs; i++) {
        // A neighbour past INT range can't be on the grid or in the field.
        if ((DESCENT_DX[i] > 0 && x == INT_MAX) || (DESCENT_DX[i] < 0 && x == INT_MIN) ||
            (DESCENT_DY[i] > 0 && y == INT_MAX) || (DESCENT_DY[i] < 0 && y == INT_MIN)) continue;
        const int nx = x + DESCENT_DX[i], ny = y + DESCENT_DY[i];
        Kind nk;
        const double v = key(nx, ny, &nk);
        if (nk == Kind::ESTIMATE) {
            if (!g || nx < 0 || ny < 0 || nx >= g->grid_w || ny >= g->grid_h ||
                !g->isWalkable(nx, ny)) continue;
        } else if (nk != Kind::EXACT) {
            continue;
        }
        if (v < best) { best = v; best_i = i; }
    }
    if (best_i < 0) return {-1, -1};  // at a root, or no lower neighbour
    if (valid) *valid = true;
    return {x + DESCENT_DX[best_i], y + DESCENT_DY[best_i]};
}

//=============================================================================
// Helper Functions
//=============================================================================

bool UIGridPathfinding::ExtractPosition(PyObject* obj, int* x, int* y,
                                        GridData* expected_grid,
                                        const char* arg_name) {
    // Check if it's an Entity
    if (PyObject_IsInstance(obj, (PyObject*)&mcrfpydef::PyUIEntityType)) {
        auto* entity = (PyUIEntityObject*)obj;
        if (!entity->data) {
            PyErr_Format(PyExc_RuntimeError,
                "%s: Entity has no data", arg_name);
            return false;
        }
        if (!entity->data->getGrid()) {
            PyErr_Format(PyExc_RuntimeError,
                "%s: Entity is not attached to any grid", arg_name);
            return false;
        }
        if (expected_grid && entity->data->getGrid().get() != expected_grid) {
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
        self->weakreflist = nullptr;
    }
    return (PyObject*)self;
}

PyObject* DijkstraMap::pyobject_for(const std::shared_ptr<DijkstraMap>& map) {
    if (!map) Py_RETURN_NONE;
    return mcrf::cached_wrapper<PyDijkstraMapObject>(map->serial_number, &mcrfpydef::PyDijkstraMapType,
        [&](PyDijkstraMapObject* o) {
            new (&o->data) std::shared_ptr<DijkstraMap>(map);
            o->weakreflist = nullptr;
        });
}

int UIGridPathfinding::DijkstraMap_init(PyDijkstraMapObject* self, PyObject* args, PyObject* kwds) {
    PyErr_SetString(PyExc_TypeError,
        "DijkstraMap cannot be instantiated directly. Use Grid.get_dijkstra_map() instead.");
    return -1;
}

void UIGridPathfinding::DijkstraMap_dealloc(PyDijkstraMapObject* self) {
    if (self->weakreflist != nullptr) {
        PyObject_ClearWeakRefs((PyObject*)self);
    }
    self->data.~shared_ptr();
    Py_TYPE(self)->tp_free((PyObject*)self);
}

PyObject* UIGridPathfinding::DijkstraMap_repr(PyDijkstraMapObject* self) {
    if (!self->data) {
        return PyUnicode_FromString("<DijkstraMap (invalid)>");
    }
    sf::Vector2i root = self->data->getRoot();
    sf::Vector2i o = self->data->getOrigin();
    return PyUnicode_FromFormat("<DijkstraMap root=(%d,%d) window=(%d,%d,%d,%d)%s>",
        root.x, root.y, o.x, o.y, self->data->getWidth(), self->data->getHeight(),
        self->data->isComplete() ? " complete" : "");
}

// #445 (was #311's IndexError for any coordinate off the map): every position is
// answered -- exact inside the field, an estimate beyond it. Only a map built with
// heuristic=None has no answer beyond its field, and says so.
static bool dijkstra_require_answer(DijkstraMap* dmap, int x, int y) {
    if (dmap->valueAt(x, y).kind != DijkstraMap::Kind::UNKNOWN) return true;
    sf::Vector2i o = dmap->getOrigin();
    PyErr_Format(PyExc_IndexError,
        "(%d, %d) is beyond this DijkstraMap's exact field (window (%d, %d, %d, %d), "
        "radius %d) and the map has no heuristic; pass heuristic= to get_dijkstra_map()",
        x, y, o.x, o.y, dmap->getWidth(), dmap->getHeight(), dmap->getRadius());
    return false;
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

    if (!dijkstra_require_answer(self->data.get(), x, y)) return NULL;

    const DijkstraMap::Value v = self->data->valueAt(x, y);
    if (v.kind == DijkstraMap::Kind::UNREACHABLE) {
        Py_RETURN_NONE;
    }
    return PyFloat_FromDouble(v.value);  // exact, or the estimate beyond the field
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

    if (!dijkstra_require_answer(self->data.get(), x, y)) return NULL;
    // #445: beyond the exact field there is no exact path to give.
    if (self->data->valueAt(x, y).kind == DijkstraMap::Kind::ESTIMATE) {
        Py_RETURN_NONE;
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

    if (!dijkstra_require_answer(self->data.get(), x, y)) return NULL;

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

// #445 properties
PyObject* UIGridPathfinding::DijkstraMap_get_radius(PyDijkstraMapObject* self, void*) {
    if (!self->data) Py_RETURN_NONE;
    return PyLong_FromLong(self->data->getRadius());
}

PyObject* UIGridPathfinding::DijkstraMap_get_window(PyDijkstraMapObject* self, void*) {
    if (!self->data) Py_RETURN_NONE;
    sf::Vector2i o = self->data->getOrigin();
    return Py_BuildValue("(iiii)", o.x, o.y, self->data->getWidth(), self->data->getHeight());
}

PyObject* UIGridPathfinding::DijkstraMap_get_complete(PyDijkstraMapObject* self, void*) {
    if (!self->data) Py_RETURN_NONE;
    return PyBool_FromLong(self->data->isComplete());
}

PyObject* UIGridPathfinding::DijkstraMap_get_heuristic(PyDijkstraMapObject* self, void*) {
    if (!self->data || self->data->getHeuristic() == DijkstraMap::NO_HEURISTIC) Py_RETURN_NONE;
    return PyHeuristic::enum_member(self->data->getHeuristic());
}

PyObject* UIGridPathfinding::DijkstraMap_is_exact(PyDijkstraMapObject* self, PyObject* args, PyObject* kwds) {
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
    if (!ExtractPosition(pos_obj, &x, &y, nullptr, "pos")) return nullptr;
    return PyBool_FromLong(self->data->isExact(x, y));
}

PyObject* UIGridPathfinding::DijkstraMap_invert(PyDijkstraMapObject* self, PyObject* args) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "DijkstraMap is invalid");
        return nullptr;
    }
    auto new_map = self->data->inverted();
    if (!new_map) return PyErr_NoMemory();  // the only failure: copying the field
    // A brand-new C++ map: serial 0, so this allocates and registers.
    return DijkstraMap::pyobject_for(new_map);
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
    if (!dijkstra_require_answer(self->data.get(), x, y)) return nullptr;

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

    // Determine output size (default: the window's size)
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

    // #445: window-sized and window-anchored -- cell (0, 0) is the grid cell at
    // dm.window[:2]. Cells not in the exact field (unreachable, or past the cut) and
    // cells outside the window get `unreachable`.
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            float dist = self->data->fieldAtWindow(x, y);
            TCOD_heightmap_set_value(hmap->heightmap, x, y, dist < 0 ? unreachable : dist);
        }
    }

    return (PyObject*)hmap;
}

//=============================================================================
// Grid Factory Methods
//=============================================================================

//=============================================================================
// GridData::DijkstraCache (#425)
//=============================================================================

void GridData::DijkstraCache::erase(std::map<Key, Entry>::iterator it)
{
    bytes -= it->second.map->fieldBytes();
    entries.erase(it);
}

void GridData::DijkstraCache::clear()
{
    entries.clear();
    bytes = 0;
}

std::shared_ptr<DijkstraMap> GridData::DijkstraCache::find(
    const Key& key, uint32_t generation, const std::vector<sf::Vector2i>& blocked)
{
    if (generation != swept_generation) {
        // The generation only rises, so an entry from an older one is dead for good.
        for (auto it = entries.begin(); it != entries.end();) {
            auto next = std::next(it);
            if (it->second.generation != generation) erase(it);
            it = next;
        }
        swept_generation = generation;
    }
    auto it = entries.find(key);
    if (it == entries.end()) return nullptr;
    if (it->second.blocked != blocked) {  // a labelled entity moved
        erase(it);
        return nullptr;
    }
    it->second.last_used = ++clock;
    return it->second.map;
}

void GridData::DijkstraCache::insert(const Key& key, std::shared_ptr<DijkstraMap> map,
                                     uint32_t generation, std::vector<sf::Vector2i> blocked)
{
    auto old = entries.find(key);
    if (old != entries.end()) erase(old);
    bytes += map->fieldBytes();
    entries[key] = Entry{std::move(map), generation, std::move(blocked), ++clock};
    trim();
}

void GridData::DijkstraCache::trim()
{
    // Least recently used first; the newest entry (highest clock) always stays.
    while (bytes > budget && entries.size() > 1) {
        auto lru = entries.begin();
        for (auto it = entries.begin(); it != entries.end(); ++it) {
            if (it->second.last_used < lru->second.last_used) lru = it;
        }
        erase(lru);
    }
}

// Helper: the in-bounds cells occupied by entities carrying `collide_label`, sorted and
// de-duplicated. Empty for an empty label. #425: this is also what a cached
// collide-label Dijkstra map is validated against, so it must be deterministic.
static std::vector<sf::Vector2i> labelledCells(GridData* grid, const std::string& collide_label)
{
    std::vector<sf::Vector2i> cells;
    if (!grid->entities || collide_label.empty()) return cells;
    for (auto& entity : *grid->entities) {
        if (!entity || !entity->labels.count(collide_label)) continue;
        int ex = entity->cell_position.x;
        int ey = entity->cell_position.y;
        if (ex >= 0 && ex < grid->grid_w && ey >= 0 && ey < grid->grid_h) {
            cells.emplace_back(ex, ey);
        }
    }
    auto less = [](const sf::Vector2i& a, const sf::Vector2i& b) {
        return a.y != b.y ? a.y < b.y : a.x < b.x;
    };
    std::sort(cells.begin(), cells.end(), less);
    cells.erase(std::unique(cells.begin(), cells.end()), cells.end());
    return cells;
}

// Helper: mark the given cells non-walkable on the grid's TCOD map.
// Returns the list of (x, y, was_walkable) for restoration.
static std::vector<std::tuple<int,int,bool>> markCells(
    GridData* grid, const std::vector<sf::Vector2i>& cells)
{
    std::vector<std::tuple<int,int,bool>> restore_list;
    TCODMap* tcod_map = grid->getTCODMap();
    if (!tcod_map) return restore_list;

    for (const auto& c : cells) {
        if (tcod_map->isWalkable(c.x, c.y)) {
            tcod_map->setProperties(c.x, c.y, tcod_map->isTransparent(c.x, c.y), false);
            restore_list.emplace_back(c.x, c.y, true);
        }
    }
    return restore_list;
}

// Helper: collect cells occupied by entities with a given label, mark non-walkable.
// Returns the list of (x, y, was_walkable) for restoration.
static std::vector<std::tuple<int,int,bool>> markCollisionLabel(
    GridData* grid, const std::string& collide_label)
{
    return markCells(grid, labelledCells(grid, collide_label));
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

PyObject* UIGridPathfinding::Grid_find_path(PyGridDataObject* self, PyObject* args, PyObject* kwds) {
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
        PyHeuristic::set_path_diagonal_cost(diagonal_cost);  // for OCTILE
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
static bool collectRoots(PyObject* root_obj, GridData* grid,
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

PyObject* UIGridPathfinding::Grid_get_dijkstra_map(PyGridDataObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"root", "diagonal_cost", "collide", "roots", "radius",
                                   "heuristic", NULL};
    PyObject* root_obj = NULL;
    PyObject* roots_obj = NULL;
    float diagonal_cost = 1.41f;
    const char* collide_label = NULL;
    PyObject* radius_obj = NULL;
    PyObject* heuristic_obj = NULL;  // NULL = not passed (OCTILE); Py_None = no estimate

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OfzOOO", const_cast<char**>(kwlist),
                                     &root_obj, &diagonal_cost, &collide_label, &roots_obj,
                                     &radius_obj, &heuristic_obj)) {
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

    GridData* grid = self->data.get();

    // #445: radius of the field's window. Default: the whole grid, up to 511 (a field
    // of at most 1023 x 1023), so grids up to 1023 on a side are unchanged.
    int radius = std::min(std::max(grid->grid_w, grid->grid_h), DijkstraMap::DEFAULT_MAX_RADIUS);
    if (radius_obj && radius_obj != Py_None) {
        if (!PyLong_Check(radius_obj)) {
            PyErr_SetString(PyExc_TypeError, "radius must be an int or None");
            return NULL;
        }
        long r = PyLong_AsLong(radius_obj);
        if (r == -1 && PyErr_Occurred()) return NULL;
        if (r < 0) {
            PyErr_SetString(PyExc_ValueError, "radius must be >= 0");
            return NULL;
        }
        radius = static_cast<int>(std::min<long>(r, INT32_MAX / 2));
    }

    // #445: the estimate beyond the exact field. None: such queries raise instead.
    int heuristic = PyHeuristic::OCTILE;
    if (heuristic_obj == Py_None) {
        heuristic = DijkstraMap::NO_HEURISTIC;
    } else if (heuristic_obj && !PyHeuristic::from_arg(heuristic_obj, &heuristic)) {
        return NULL;
    }

    std::vector<sf::Vector2i> roots;
    PyDiscreteMapObject* mask_obj = nullptr;
    if (!collectRoots(input_obj, grid, &roots, &mask_obj)) {
        return NULL;
    }
    if (mask_obj) {
        // A mask is an explicit root list for compute_multi (same distances as
        // compute_masked); its window is the set cells' bounding box grown by radius.
        const uint8_t* buf = mask_obj->data->data();
        const int w = mask_obj->data->width();
        const int h = mask_obj->data->height();
        for (int y = 0; y < h; y++) {
            for (int x = 0; x < w; x++) {
                if (buf[y * w + x] != 0) roots.push_back(sf::Vector2i(x, y));
            }
        }
        if (roots.empty()) {
            PyErr_SetString(PyExc_ValueError, "DiscreteMap mask has no non-zero cells");
            return NULL;
        }
    }

    std::string label_str = collide_label ? collide_label : "";

    // Single-root requests are cached (#425: see GridData::DijkstraCache -- a map is
    // returned only while it still describes the grid, and the cache bounds itself).
    const bool cacheable = !mask_obj && roots.size() == 1;
    const auto key = cacheable
        ? std::make_tuple(roots[0].x, roots[0].y, label_str, diagonal_cost, radius, heuristic)
        : std::make_tuple(0, 0, std::string(), 0.0f, 0, 0);
    std::vector<sf::Vector2i> blocked = labelledCells(grid, label_str);
    if (cacheable) {
        if (auto hit = grid->dijkstra_cache.find(key, grid->transparency_generation, blocked)) {
            return DijkstraMap::pyobject_for(hit);
        }
    }

    // #445: the map blocks the collide= cells in its own window copy; the grid's
    // TCODMap is no longer marked and restored around the computation.
    auto dijkstra = std::make_shared<DijkstraMap>(self->data, roots, diagonal_cost, radius,
                                                  heuristic, blocked);

    if (cacheable) {
        grid->dijkstra_cache.insert(key, dijkstra, grid->transparency_generation,
                                    std::move(blocked));
    }

    return DijkstraMap::pyobject_for(dijkstra);
}

//=============================================================================
// Python Type Definitions
//=============================================================================

namespace mcrfpydef {

// AStarPath methods
PyMethodDef PyAStarPath_methods[] = {
    {"walk", (PyCFunction)UIGridPathfinding::AStarPath_walk, METH_NOARGS,
     MCRF_METHOD(AStarPath, walk,
         MCRF_SIG("()", "Vector"),
         MCRF_DESC("Get and consume the next step in the path.")
         MCRF_RETURNS("Next position as Vector")
         MCRF_RAISES("IndexError", "If the path is exhausted")
     )},

    {"peek", (PyCFunction)UIGridPathfinding::AStarPath_peek, METH_NOARGS,
     MCRF_METHOD(AStarPath, peek,
         MCRF_SIG("()", "Vector"),
         MCRF_DESC("See the next step without consuming it.")
         MCRF_RETURNS("Next position as Vector")
         MCRF_RAISES("IndexError", "If the path is exhausted")
     )},

    {NULL}
};

// AStarPath getsetters
PyGetSetDef PyAStarPath_getsetters[] = {
    {"origin", (getter)UIGridPathfinding::AStarPath_get_origin, NULL,
     MCRF_PROPERTY(origin, "Starting position of the path (Vector, read-only)."), NULL},

    {"destination", (getter)UIGridPathfinding::AStarPath_get_destination, NULL,
     MCRF_PROPERTY(destination, "Ending position of the path (Vector, read-only)."), NULL},

    {"remaining", (getter)UIGridPathfinding::AStarPath_get_remaining, NULL,
     MCRF_PROPERTY(remaining, "Number of steps remaining in the path (int, read-only)."), NULL},

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
    .ob_base = PyVarObject_HEAD_INIT(NULL, 0)
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
    .ob_base = PyVarObject_HEAD_INIT(NULL, 0)
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
     MCRF_METHOD(DijkstraMap, distance,
         MCRF_SIG("(pos: Vector | tuple)", "float | None"),
         MCRF_DESC("Get distance from position to the nearest root. Any position is answered, on or off the grid: exact within the map's field, otherwise the map's heuristic estimate (a lower bound). is_exact(pos) tells which.")
         MCRF_ARGS_START
         MCRF_ARG("pos", "Position as Vector, Entity, or (x, y) tuple")
         MCRF_RETURNS("Float distance or estimate, or None if the position is certainly unreachable")
         MCRF_RAISES("IndexError", "pos is beyond the exact field and the map was built with heuristic=None")
     )},

    {"path_from", (PyCFunction)UIGridPathfinding::DijkstraMap_path_from, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(DijkstraMap, path_from,
         MCRF_SIG("(pos: Vector | tuple)", "AStarPath"),
         MCRF_DESC("Get full path from position to root, along the exact field.")
         MCRF_ARGS_START
         MCRF_ARG("pos", "Starting position as Vector, Entity, or (x, y) tuple")
         MCRF_RETURNS("AStarPath from pos toward root (empty at a root or if unreachable), or None if pos is beyond the exact field")
         MCRF_RAISES("IndexError", "pos is beyond the exact field and the map was built with heuristic=None")
     )},

    {"step_from", (PyCFunction)UIGridPathfinding::DijkstraMap_step_from, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(DijkstraMap, step_from,
         MCRF_SIG("(pos: Vector | tuple)", "Vector | None"),
         MCRF_DESC("Get single step from position toward root. Beyond the exact field this is a greedy step to the walkable neighbour with the lowest estimate (it needs the grid to still exist).")
         MCRF_ARGS_START
         MCRF_ARG("pos", "Current position as Vector, Entity, or (x, y) tuple")
         MCRF_RETURNS("Next position as Vector, or None if at root, unreachable, or no neighbour is closer")
         MCRF_RAISES("IndexError", "pos is beyond the exact field and the map was built with heuristic=None")
     )},

    {"to_heightmap", (PyCFunction)UIGridPathfinding::DijkstraMap_to_heightmap, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(DijkstraMap, to_heightmap,
         MCRF_SIG("(size=None, unreachable=-1.0)", "HeightMap"),
         MCRF_DESC("Convert the exact distance field to a HeightMap covering the map's window: cell (0, 0) is grid cell window[:2]. Each cell's height is its distance from the root; place it on a grid-sized HeightMap with copy_from(pos=window[:2]).")
         MCRF_ARGS_START
         MCRF_ARG("size", "Optional (width, height) tuple. Defaults to the window's size")
         MCRF_ARG("unreachable", "Value for cells not in the exact field: unreachable, or past the radius (default -1.0)")
         MCRF_RETURNS("HeightMap with distance values as heights")
     )},

    {"invert", (PyCFunction)UIGridPathfinding::DijkstraMap_invert, METH_NOARGS,
     MCRF_METHOD(DijkstraMap, invert,
         MCRF_SIG("()", "DijkstraMap"),
         MCRF_DESC("Return a new DijkstraMap whose distance field is inverted (safety field). Cells near a root become high values; descend to flee from original roots. The original DijkstraMap is unchanged.")
         MCRF_RETURNS("New DijkstraMap with inverted distances")
     )},

    {"descent_step", (PyCFunction)UIGridPathfinding::DijkstraMap_descent_step, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(DijkstraMap, descent_step,
         MCRF_SIG("(pos: Vector | tuple)", "Vector | None"),
         MCRF_DESC("Get the adjacent cell with the lowest distance (steepest descent). Unlike step_from, this always returns the best neighbor in a single hop without following a precomputed path.")
         MCRF_ARGS_START
         MCRF_ARG("pos", "Current position as Vector, Entity, or (x, y) tuple")
         MCRF_RETURNS("Next position as Vector, or None if pos is a local minimum")
         MCRF_RAISES("IndexError", "pos is beyond the exact field and the map was built with heuristic=None")
     )},

    {"is_exact", (PyCFunction)UIGridPathfinding::DijkstraMap_is_exact, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(DijkstraMap, is_exact,
         MCRF_SIG("(pos: Vector | tuple)", "bool"),
         MCRF_DESC("Whether distance(pos) is certain: an exact distance, or certainly unreachable. False where it is the heuristic's estimate.")
         MCRF_ARGS_START
         MCRF_ARG("pos", "Position as Vector, Entity, or (x, y) tuple (any position, on or off the grid)")
         MCRF_RETURNS("True if the answer for pos is exact")
     )},

    {NULL}
};

// DijkstraMap getsetters
PyGetSetDef PyDijkstraMap_getsetters[] = {
    {"root", (getter)UIGridPathfinding::DijkstraMap_get_root, NULL,
     MCRF_PROPERTY(root, "Root position that distances are measured from (Vector, read-only)."), NULL},
    {"radius", (getter)UIGridPathfinding::DijkstraMap_get_radius, NULL,
     MCRF_PROPERTY(radius, "Radius of the field's window around the roots (int, read-only). Distances up to radius are exact (radius * diagonal_cost, if that is below 1)."), NULL},
    {"window", (getter)UIGridPathfinding::DijkstraMap_get_window, NULL,
     MCRF_PROPERTY(window, "The grid rectangle the field covers, as (x, y, w, h) (tuple, read-only): the roots' bounding box grown by radius, clipped to the grid."), NULL},
    {"complete", (getter)UIGridPathfinding::DijkstraMap_get_complete, NULL,
     MCRF_PROPERTY(complete, "True if the field holds the roots' whole reachable region (bool, read-only): every distance is then exact and every other cell is unreachable. Always True when the window is the whole grid."), NULL},
    {"heuristic", (getter)UIGridPathfinding::DijkstraMap_get_heuristic, NULL,
     MCRF_PROPERTY(heuristic, "The estimate used beyond the exact field (Heuristic | None, read-only). None: such queries raise IndexError."), NULL},

    {NULL}
};

// DijkstraMap type
PyTypeObject PyDijkstraMapType = {
    .ob_base = PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "mcrfpy.DijkstraMap",
    .tp_basicsize = sizeof(PyDijkstraMapObject),
    .tp_itemsize = 0,
    .tp_dealloc = (destructor)UIGridPathfinding::DijkstraMap_dealloc,
    .tp_repr = (reprfunc)UIGridPathfinding::DijkstraMap_repr,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_doc = PyDoc_STR(
        "A Dijkstra distance map from a fixed root position.\n\n"
        "Created by Grid.get_dijkstra_map(). Cannot be instantiated directly.\n\n"
        "A DijkstraMap is a snapshot of the grid when it was computed: later\n"
        "walkability edits do not change it, and it stays usable after the grid\n"
        "is gone. Grid caches single-root maps, returning the same map while\n"
        "the grid is unchanged and a rebuilt one after it changes.\n\n"
        "Windowed (#445): the field covers `window`, the roots' bounding box grown\n"
        "by `radius` (default: the whole grid, up to 511) and clipped to the grid.\n"
        "Distances up to the radius are exact. Beyond that, and off the grid,\n"
        "distance() returns the map's heuristic estimate; is_exact(pos) tells\n"
        "which. A `complete` field (always, when the window is the whole grid)\n"
        "is exact everywhere.\n\n"
        "Properties:\n"
        "    root (Vector): Root position (read-only)\n"
        "    radius (int), window (x, y, w, h), complete (bool),\n"
        "    heuristic (Heuristic | None): the field's extent and estimate\n\n"
        "Methods:\n"
        "    distance(pos) -> float | None: Get distance to root\n"
        "    is_exact(pos) -> bool: Is distance(pos) exact\n"
        "    path_from(pos) -> AStarPath | None: Get full path to root\n"
        "    step_from(pos) -> Vector | None: Get single step toward root\n\n"
        "Example:\n"
        "    dijkstra = grid.get_dijkstra_map(player.pos)\n"
        "    for enemy in enemies:\n"
        "        dist = dijkstra.distance(enemy.pos)\n"
        "        if dist and dist < 10:\n"
        "            step = dijkstra.step_from(enemy.pos)\n"
        "            if step:\n"
        "                enemy.pos = step"),
    .tp_weaklistoffset = offsetof(PyDijkstraMapObject, weakreflist),  // #430
    .tp_methods = PyDijkstraMap_methods,
    .tp_getset = PyDijkstraMap_getsetters,
    .tp_init = (initproc)UIGridPathfinding::DijkstraMap_init,
    .tp_new = UIGridPathfinding::DijkstraMap_new,
};

} // namespace mcrfpydef
