#pragma once
#include "Common.h"
#include "Python.h"
#include "UIBase.h"  // For PyUIGridObject typedef
#include <libtcod.h>
#include <SFML/System/Vector2.hpp>
#include <vector>
#include <memory>
#include <map>

// Forward declarations
class UIGrid;

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
    DijkstraMap(TCODMap* map, int root_x, int root_y, float diagonal_cost);
    ~DijkstraMap();

    // Non-copyable (owns TCODDijkstra)
    DijkstraMap(const DijkstraMap&) = delete;
    DijkstraMap& operator=(const DijkstraMap&) = delete;

    // Queries
    float getDistance(int x, int y) const;
    std::vector<sf::Vector2i> getPathFrom(int x, int y) const;
    sf::Vector2i stepFrom(int x, int y, bool* valid = nullptr) const;

    // Accessors
    sf::Vector2i getRoot() const { return root; }
    float getDiagonalCost() const { return diagonal_cost; }

private:
    TCODDijkstra* tcod_dijkstra;  // Owned by this object
    TCODMap* tcod_map;            // Borrowed from Grid
    sf::Vector2i root;
    float diagonal_cost;
};

struct PyDijkstraMapObject {
    PyObject_HEAD
    std::shared_ptr<DijkstraMap> data;  // Shared with Grid's collection
};

//=============================================================================
// Helper Functions
//=============================================================================

namespace UIGridPathfinding {
    // Extract grid position from Vector, Entity, or tuple
    // Sets Python error and returns false on failure
    // If expected_grid is provided and obj is Entity, validates grid membership
    bool ExtractPosition(PyObject* obj, int* x, int* y,
                         UIGrid* expected_grid = nullptr,
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

    // Properties
    PyObject* DijkstraMap_get_root(PyDijkstraMapObject* self, void* closure);

    //=========================================================================
    // Grid Factory Methods (called from UIGrid Python bindings)
    //=========================================================================

    // Grid.find_path() -> AStarPath | None
    PyObject* Grid_find_path(PyUIGridObject* self, PyObject* args, PyObject* kwds);

    // Grid.get_dijkstra_map() -> DijkstraMap
    PyObject* Grid_get_dijkstra_map(PyUIGridObject* self, PyObject* args, PyObject* kwds);

    // Grid.clear_dijkstra_maps() -> None
    PyObject* Grid_clear_dijkstra_maps(PyUIGridObject* self, PyObject* args);
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
