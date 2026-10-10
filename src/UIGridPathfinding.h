#pragma once
#include "Common.h"
#include "Python.h"
#include "UIBase.h"  // For PyGridDataObject typedef
#include <libtcod.h>
#include <vector>
#include <memory>
#include <map>

// Forward declarations
class GridData;

//=============================================================================
// AStarPath - A computed A* path result, consumed like an iterator
//=============================================================================

struct PyAStarPathObject {
    PyObject_HEAD
    std::vector<sf::Vector2i> path;  // Pre-computed path positions
    size_t current_index;            // Next step to return
    sf::Vector2i origin;             // Fixed at creation
    sf::Vector2i destination;        // Fixed at creation
};

//=============================================================================
// DijkstraMap - A Dijkstra distance field from a fixed root
//=============================================================================

class DijkstraMap {
public:
    // Default radius: a field is at most 1023 x 1023 cells (#445).
    static constexpr int DEFAULT_MAX_RADIUS = 511;
    // heuristic value meaning "no estimate": a query beyond the field raises.
    static constexpr int NO_HEURISTIC = -1;

    // #445: computes the field over a WINDOW of `grid` -- the bounding box of the
    // roots, expanded by `radius` and clipped to the grid -- from a window-sized copy
    // of the walkable plane with `blocked` cells (the collide= label's entities) made
    // unwalkable. The grid itself is not touched, and nothing of it is kept but a weak
    // reference for greedy steps beyond the field. roots must be non-empty (#315: more
    // than one is a multi-root field).
    DijkstraMap(const std::shared_ptr<GridData>& grid, const std::vector<sf::Vector2i>& roots,
                float diagonal_cost, int radius, int heuristic,
                const std::vector<sf::Vector2i>& blocked);

    // A copy of src's distance field (for inverted()). tcod_dijkstra is null if the
    // copy could not be allocated.
    struct CopyField {};
    DijkstraMap(const DijkstraMap& src, CopyField);

    // Bytes held by the distance field: what the grid's cache budget counts.
    size_t fieldBytes() const { return static_cast<size_t>(win_w) * win_h * sizeof(unsigned int); }

    ~DijkstraMap();

    // Non-copyable (owns TCOD_Dijkstra)
    DijkstraMap(const DijkstraMap&) = delete;
    DijkstraMap& operator=(const DijkstraMap&) = delete;

    // #445: what the map knows about a grid position (any int, on or off the grid).
    //   EXACT       -- in the exact field: `value` is the distance (inverted, if so)
    //   UNREACHABLE -- certainly unreachable: the field is complete and missed it
    //   ESTIMATE    -- beyond the exact field: `value` is the heuristic lower bound
    //   UNKNOWN     -- beyond the exact field, and the map has no heuristic
    enum class Kind { EXACT, UNREACHABLE, ESTIMATE, UNKNOWN };
    struct Value { Kind kind; float value; };
    Value valueAt(int x, int y) const;
    bool isExact(int x, int y) const;  // EXACT or UNREACHABLE: the answer is certain

    // All in grid coordinates.
    // Exact path to the root ([next, ..., root]); empty at a root or beyond the field.
    std::vector<sf::Vector2i> getPathFrom(int x, int y) const;
    // One step: along the exact field, or beyond it a greedy step to the walkable
    // neighbour with the lowest estimate (needs the grid alive).
    sf::Vector2i stepFrom(int x, int y, bool* valid = nullptr) const;
    // Lowest-valued neighbour lower than (x, y); same rules as stepFrom.
    sf::Vector2i descentStep(int x, int y, bool* valid = nullptr) const;

    // Phase B: FLEE primitives (#315)
    // invertInPlace() mutates this map's distance field. Prefer inverted() in new code —
    // the Python surface exposes the non-mutating form to keep maps immutable after
    // creation.
    void invertInPlace();
    // A copy of this map with its distance field inverted (max - d); beyond the field
    // the estimate inverts the same way, so descent keeps moving away from the roots.
    std::shared_ptr<DijkstraMap> inverted() const;

    // Accessors
    sf::Vector2i getRoot() const { return root; }  // First root for multi-root
    const std::vector<sf::Vector2i>& getRoots() const { return roots; }
    bool isMultiRoot() const { return roots.size() > 1; }
    float getDiagonalCost() const { return diagonal_cost; }
    int getRadius() const { return radius; }
    int getHeuristic() const { return heuristic; }
    bool isComplete() const { return complete; }
    sf::Vector2i getOrigin() const { return {win_x, win_y}; }  // window's top-left
    int getWidth() const { return win_w; }    // window size
    int getHeight() const { return win_h; }
    float fieldAtWindow(int wx, int wy) const;  // window coords; -1 if not in the field

    // #430: PythonObjectCache key (0 = no wrapper yet). Unregistered in ~DijkstraMap.
    uint64_t serial_number = 0;

    // #430: the one way to return a DijkstraMap to Python. Returns the live wrapper
    // if one exists (so grid.get_dijkstra_map(r) is grid.get_dijkstra_map(r) while the
    // grid caches the map), else allocates and registers one. nullptr -> None.
    static PyObject* pyobject_for(const std::shared_ptr<DijkstraMap>& map);

private:
    static void finish(TCOD_Dijkstra* d);
    // 4 or 8 neighbours, decided as libtcod decides it (diagonal cost rounds to 0).
    int diag_dirs() const { return static_cast<int>(diagonal_cost * 100.0f + 0.1f) == 0 ? 4 : 8; }
    bool inField(int x, int y, float* dist) const;
    float estimateAt(int x, int y) const;  // un-inverted heuristic lower bound

    TCOD_Dijkstra* tcod_dijkstra;  // Owned; a finished field (no map, no work queue)
    sf::Vector2i root;
    std::vector<sf::Vector2i> roots;  // grid coordinates
    float diagonal_cost;
    int radius = 0;
    int heuristic = NO_HEURISTIC;
    int win_x = 0, win_y = 0, win_w = 0, win_h = 0;  // the window, in grid coordinates
    float threshold = 0.0f;   // distances up to this are exact (#445)
    bool complete = false;    // the field holds the roots' whole reachable region
    bool is_inverted = false;
    float inverted_max = 0.0f;  // max finite distance before inversion
    std::weak_ptr<GridData> grid;  // for walkability on greedy steps beyond the field
};

struct PyDijkstraMapObject {
    PyObject_HEAD
    std::shared_ptr<DijkstraMap> data;  // Shared with Grid's collection
    PyObject* weakreflist;              // #430: required by the wrapper cache
};

//=============================================================================
// Helper Functions
//=============================================================================

namespace UIGridPathfinding {
    // Extract grid position from Vector, Entity, or tuple
    // Sets Python error and returns false on failure
    // If expected_grid is provided and obj is Entity, validates grid membership
    bool ExtractPosition(PyObject* obj, int* x, int* y,
                         GridData* expected_grid = nullptr,
                         const char* arg_name = "position");

    //=========================================================================
    // AStarPath Python Type Methods
    //=========================================================================

    PyObject* AStarPath_new(PyTypeObject* type, PyObject* args, PyObject* kwds);
    int AStarPath_init(PyAStarPathObject* self, PyObject* args, PyObject* kwds);
    void AStarPath_dealloc(PyAStarPathObject* self);
    PyObject* AStarPath_repr(PyAStarPathObject* self);

    // Methods
    PyObject* AStarPath_walk(PyAStarPathObject* self, PyObject* args);
    PyObject* AStarPath_peek(PyAStarPathObject* self, PyObject* args);

    // Properties
    PyObject* AStarPath_get_origin(PyAStarPathObject* self, void* closure);
    PyObject* AStarPath_get_destination(PyAStarPathObject* self, void* closure);
    PyObject* AStarPath_get_remaining(PyAStarPathObject* self, void* closure);

    // Sequence protocol
    Py_ssize_t AStarPath_len(PyAStarPathObject* self);
    int AStarPath_bool(PyObject* self);
    PyObject* AStarPath_iter(PyAStarPathObject* self);
    PyObject* AStarPath_iternext(PyAStarPathObject* self);

    //=========================================================================
    // DijkstraMap Python Type Methods
    //=========================================================================

    PyObject* DijkstraMap_new(PyTypeObject* type, PyObject* args, PyObject* kwds);
    int DijkstraMap_init(PyDijkstraMapObject* self, PyObject* args, PyObject* kwds);
    void DijkstraMap_dealloc(PyDijkstraMapObject* self);
    PyObject* DijkstraMap_repr(PyDijkstraMapObject* self);

    // Methods
    PyObject* DijkstraMap_distance(PyDijkstraMapObject* self, PyObject* args, PyObject* kwds);
    PyObject* DijkstraMap_path_from(PyDijkstraMapObject* self, PyObject* args, PyObject* kwds);
    PyObject* DijkstraMap_step_from(PyDijkstraMapObject* self, PyObject* args, PyObject* kwds);
    PyObject* DijkstraMap_to_heightmap(PyDijkstraMapObject* self, PyObject* args, PyObject* kwds);
    PyObject* DijkstraMap_invert(PyDijkstraMapObject* self, PyObject* args);
    PyObject* DijkstraMap_descent_step(PyDijkstraMapObject* self, PyObject* args, PyObject* kwds);

    // Properties
    PyObject* DijkstraMap_get_root(PyDijkstraMapObject* self, void* closure);
    PyObject* DijkstraMap_get_radius(PyDijkstraMapObject* self, void* closure);
    PyObject* DijkstraMap_get_window(PyDijkstraMapObject* self, void* closure);
    PyObject* DijkstraMap_get_complete(PyDijkstraMapObject* self, void* closure);
    PyObject* DijkstraMap_get_heuristic(PyDijkstraMapObject* self, void* closure);
    PyObject* DijkstraMap_is_exact(PyDijkstraMapObject* self, PyObject* args, PyObject* kwds);

    //=========================================================================
    // Grid Factory Methods (called from UIGrid Python bindings)
    //=========================================================================

    // Grid.find_path() -> AStarPath | None
    PyObject* Grid_find_path(PyGridDataObject* self, PyObject* args, PyObject* kwds);

    // Grid.get_dijkstra_map() -> DijkstraMap
    PyObject* Grid_get_dijkstra_map(PyGridDataObject* self, PyObject* args, PyObject* kwds);

}

//=============================================================================
// Python Type Definitions
//=============================================================================

namespace mcrfpydef {

    // AStarPath iterator type
    struct PyAStarPathIterObject {
        PyObject_HEAD
        PyAStarPathObject* path;  // Reference to path being iterated
        size_t iter_index;        // Current iteration position
    };

    extern PyNumberMethods PyAStarPath_as_number;
    extern PySequenceMethods PyAStarPath_as_sequence;
    extern PyMethodDef PyAStarPath_methods[];
    extern PyGetSetDef PyAStarPath_getsetters[];

    extern PyTypeObject PyAStarPathType;
    extern PyTypeObject PyAStarPathIterType;

    extern PyMethodDef PyDijkstraMap_methods[];
    extern PyGetSetDef PyDijkstraMap_getsetters[];

    extern PyTypeObject PyDijkstraMapType;
}
