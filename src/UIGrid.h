#pragma once
#include "Common.h"
#include "Python.h"
#include "structmember.h"
#include "IndexTexture.h"
#include "Resources.h"
#include <list>
#include <libtcod.h>

#include "PyCallable.h"
#include "PyTexture.h"
#include "PyDrawable.h"
#include "PyColor.h"
#include "PyVector.h"
#include "PyFont.h"

#include "UIGridPoint.h"
#include "UIEntity.h"
#include "UIDrawable.h"
#include "UIBase.h"

class UIGrid: public UIDrawable
{
private:
    std::shared_ptr<PyTexture> ptex;
    // Default cell dimensions when no texture is provided
    static constexpr int DEFAULT_CELL_WIDTH = 16;
    static constexpr int DEFAULT_CELL_HEIGHT = 16;
    TCODMap* tcod_map;  // TCOD map for FOV and pathfinding
    TCODDijkstra* tcod_dijkstra;  // Dijkstra pathfinding
    TCODPath* tcod_path;  // A* pathfinding
    
public:
    UIGrid();
    //UIGrid(int, int, IndexTexture*, float, float, float, float);
    UIGrid(int, int, std::shared_ptr<PyTexture>, sf::Vector2f, sf::Vector2f);
    ~UIGrid();  // Destructor to clean up TCOD map
    void update();
    void render(sf::Vector2f, sf::RenderTarget&) override final;
    UIGridPoint& at(int, int);
    PyObjectsEnum derived_type() override final;
    //void setSprite(int);
    virtual UIDrawable* click_at(sf::Vector2f point) override final;
    
    // TCOD integration methods
    void syncTCODMap();  // Sync entire map with current grid state
    void syncTCODMapCell(int x, int y);  // Sync a single cell to TCOD map
    void computeFOV(int x, int y, int radius, bool light_walls = true, TCOD_fov_algorithm_t algo = FOV_BASIC);
    bool isInFOV(int x, int y) const;
    
    // Pathfinding methods
    std::vector<std::pair<int, int>> findPath(int x1, int y1, int x2, int y2, float diagonalCost = 1.41f);
    void computeDijkstra(int rootX, int rootY, float diagonalCost = 1.41f);
    float getDijkstraDistance(int x, int y) const;
    std::vector<std::pair<int, int>> getDijkstraPath(int x, int y) const;
    
    // A* pathfinding methods
    std::vector<std::pair<int, int>> computeAStarPath(int x1, int y1, int x2, int y2, float diagonalCost = 1.41f);
    
    // Phase 1 virtual method implementations
    sf::FloatRect get_bounds() const override;
    void move(float dx, float dy) override;
    void resize(float w, float h) override;
    void onPositionChanged() override;

    int grid_x, grid_y;
    //int grid_size; // grid sizes are implied by IndexTexture now
    sf::RectangleShape box;
    float center_x, center_y, zoom;
    //IndexTexture* itex;
    std::shared_ptr<PyTexture> getTexture();
    sf::Sprite sprite, output;
    sf::RenderTexture renderTexture;
    std::vector<UIGridPoint> points;
    std::shared_ptr<std::list<std::shared_ptr<UIEntity>>> entities;
    
    // Background rendering
    sf::Color fill_color;
    
    // Perspective system - which entity's view to render (-1 = omniscient/default)
    int perspective;
    
    // Property system for animations
    bool setProperty(const std::string& name, float value) override;
    bool setProperty(const std::string& name, const sf::Vector2f& value) override;
    bool getProperty(const std::string& name, float& value) const override;
    bool getProperty(const std::string& name, sf::Vector2f& value) const override;

    static int init(PyUIGridObject* self, PyObject* args, PyObject* kwds);
    static PyObject* get_grid_size(PyUIGridObject* self, void* closure);
    static PyObject* get_grid_x(PyUIGridObject* self, void* closure);
    static PyObject* get_grid_y(PyUIGridObject* self, void* closure);
    static PyObject* get_position(PyUIGridObject* self, void* closure);
    static int set_position(PyUIGridObject* self, PyObject* value, void* closure);
    static PyObject* get_size(PyUIGridObject* self, void* closure);
    static int set_size(PyUIGridObject* self, PyObject* value, void* closure);
    static PyObject* get_center(PyUIGridObject* self, void* closure);
    static int set_center(PyUIGridObject* self, PyObject* value, void* closure);
    static PyObject* get_float_member(PyUIGridObject* self, void* closure);
    static int set_float_member(PyUIGridObject* self, PyObject* value, void* closure);
    static PyObject* get_texture(PyUIGridObject* self, void* closure);
    static PyObject* get_fill_color(PyUIGridObject* self, void* closure);
    static int set_fill_color(PyUIGridObject* self, PyObject* value, void* closure);
    static PyObject* get_perspective(PyUIGridObject* self, void* closure);
    static int set_perspective(PyUIGridObject* self, PyObject* value, void* closure);
    static PyObject* py_at(PyUIGridObject* self, PyObject* args, PyObject* kwds);
    static PyObject* py_compute_fov(PyUIGridObject* self, PyObject* args, PyObject* kwds);
    static PyObject* py_is_in_fov(PyUIGridObject* self, PyObject* args);
    static PyObject* py_find_path(PyUIGridObject* self, PyObject* args, PyObject* kwds);
    static PyObject* py_compute_dijkstra(PyUIGridObject* self, PyObject* args, PyObject* kwds);
    static PyObject* py_get_dijkstra_distance(PyUIGridObject* self, PyObject* args);
    static PyObject* py_get_dijkstra_path(PyUIGridObject* self, PyObject* args);
    static PyObject* py_compute_astar_path(PyUIGridObject* self, PyObject* args, PyObject* kwds);
    static PyMethodDef methods[];
    static PyGetSetDef getsetters[];
    static PyObject* get_children(PyUIGridObject* self, void* closure);
    static PyObject* repr(PyUIGridObject* self);
    
};

typedef struct {
    PyObject_HEAD
    std::shared_ptr<std::list<std::shared_ptr<UIEntity>>> data;
    std::shared_ptr<UIGrid> grid;
} PyUIEntityCollectionObject;

class UIEntityCollection {
public:
    static PySequenceMethods sqmethods;
    static PyMappingMethods mpmethods;
    static PyObject* append(PyUIEntityCollectionObject* self, PyObject* o);
    static PyObject* extend(PyUIEntityCollectionObject* self, PyObject* o);
    static PyObject* remove(PyUIEntityCollectionObject* self, PyObject* o);
    static PyObject* index_method(PyUIEntityCollectionObject* self, PyObject* value);
    static PyObject* count(PyUIEntityCollectionObject* self, PyObject* value);
    static PyMethodDef methods[];
    static PyObject* repr(PyUIEntityCollectionObject* self);
    static int init(PyUIEntityCollectionObject* self, PyObject* args, PyObject* kwds);
    static PyObject* iter(PyUIEntityCollectionObject* self);
    static Py_ssize_t len(PyUIEntityCollectionObject* self);
    static PyObject* getitem(PyUIEntityCollectionObject* self, Py_ssize_t index);
    static int setitem(PyUIEntityCollectionObject* self, Py_ssize_t index, PyObject* value);
    static int contains(PyUIEntityCollectionObject* self, PyObject* value);
    static PyObject* concat(PyUIEntityCollectionObject* self, PyObject* other);
    static PyObject* inplace_concat(PyUIEntityCollectionObject* self, PyObject* other);
    static PyObject* subscript(PyUIEntityCollectionObject* self, PyObject* key);
    static int ass_subscript(PyUIEntityCollectionObject* self, PyObject* key, PyObject* value);
};

typedef struct {
    PyObject_HEAD
    std::shared_ptr<std::list<std::shared_ptr<UIEntity>>> data;
    int index;
    int start_size;
} PyUIEntityCollectionIterObject;

class UIEntityCollectionIter {
public:
    static int init(PyUIEntityCollectionIterObject* self, PyObject* args, PyObject* kwds);
    static PyObject* next(PyUIEntityCollectionIterObject* self);
    static PyObject* repr(PyUIEntityCollectionIterObject* self);
    static PyObject* getitem(PyUIEntityCollectionObject* self, Py_ssize_t index);
    
};

// Forward declaration of methods array
extern PyMethodDef UIGrid_all_methods[];

namespace mcrfpydef {
    static PyTypeObject PyUIGridType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Grid",
        .tp_basicsize = sizeof(PyUIGridObject),
        .tp_itemsize = 0,
        //.tp_dealloc = (destructor)[](PyObject* self)
        //{
        //    PyUIGridObject* obj = (PyUIGridObject*)self;
        //    obj->data.reset();
        //    Py_TYPE(self)->tp_free(self);
        //},
        //TODO - PyUIGrid REPR def:
        .tp_repr = (reprfunc)UIGrid::repr,
        //.tp_hash = NULL,
        //.tp_iter
        //.tp_iternext
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("Grid(x=0, y=0, grid_size=(20, 20), texture=None, tile_width=16, tile_height=16, scale=1.0, click=None)\n\n"
                            "A grid-based tilemap UI element for rendering tile-based levels and game worlds.\n\n"
                            "Args:\n"
                            "    x (float): X position in pixels. Default: 0\n"
                            "    y (float): Y position in pixels. Default: 0\n"
                            "    grid_size (tuple): Grid dimensions as (width, height) in tiles. Default: (20, 20)\n"
                            "    texture (Texture): Texture atlas containing tile sprites. Default: None\n"
                            "    tile_width (int): Width of each tile in pixels. Default: 16\n"
                            "    tile_height (int): Height of each tile in pixels. Default: 16\n"
                            "    scale (float): Grid scaling factor. Default: 1.0\n"
                            "    click (callable): Click event handler. Default: None\n\n"
                            "Attributes:\n"
                            "    x, y (float): Position in pixels\n"
                            "    grid_size (tuple): Grid dimensions (width, height) in tiles\n"
                            "    tile_width, tile_height (int): Tile dimensions in pixels\n"
                            "    texture (Texture): Tile texture atlas\n"
                            "    scale (float): Scale multiplier\n"
                            "    points (list): 2D array of GridPoint objects for tile data\n"
                            "    entities (list): Collection of Entity objects in the grid\n"
                            "    background_color (Color): Grid background color\n"
                            "    click (callable): Click event handler\n"
                            "    visible (bool): Visibility state\n"
                            "    z_index (int): Rendering order"),
        .tp_methods = UIGrid_all_methods,
        //.tp_members = UIGrid::members,
        .tp_getset = UIGrid::getsetters,
        .tp_base = &mcrfpydef::PyDrawableType,
        .tp_init = (initproc)UIGrid::init,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            PyUIGridObject* self = (PyUIGridObject*)type->tp_alloc(type, 0);
            if (self) self->data = std::make_shared<UIGrid>();
            return (PyObject*)self;
        }
    };

    static PyTypeObject PyUIEntityCollectionIterType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.UIEntityCollectionIter",
        .tp_basicsize = sizeof(PyUIEntityCollectionIterObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)[](PyObject* self)
        {
            PyUIEntityCollectionIterObject* obj = (PyUIEntityCollectionIterObject*)self;
            obj->data.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)UIEntityCollectionIter::repr,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("Iterator for a collection of UI objects"),
        .tp_iter = PyObject_SelfIter,
        .tp_iternext = (iternextfunc)UIEntityCollectionIter::next,
        //.tp_getset = UIEntityCollection::getset,
        .tp_init = (initproc)UIEntityCollectionIter::init, // just raise an exception
        .tp_alloc = PyType_GenericAlloc,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            PyErr_SetString(PyExc_TypeError, "UICollection cannot be instantiated: a C++ data source is required.");
            return NULL;
        }
    };

    static PyTypeObject PyUIEntityCollectionType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.EntityCollection",
        .tp_basicsize = sizeof(PyUIEntityCollectionObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)[](PyObject* self)
        {
            PyUIEntityCollectionObject* obj = (PyUIEntityCollectionObject*)self;
            obj->data.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)UIEntityCollection::repr,
        .tp_as_sequence = &UIEntityCollection::sqmethods,
        .tp_as_mapping = &UIEntityCollection::mpmethods,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("Iterable, indexable collection of Entities"),
        .tp_iter = (getiterfunc)UIEntityCollection::iter,
        .tp_methods = UIEntityCollection::methods, // append, remove
        //.tp_getset = UIEntityCollection::getset,
        .tp_init = (initproc)UIEntityCollection::init, // just raise an exception
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            // Does PyUIEntityCollectionType need __new__ if it's not supposed to be instantiable by the user?
            // Should I just raise an exception? Or is the uninitialized shared_ptr enough of a blocker?
            PyErr_SetString(PyExc_TypeError, "EntityCollection cannot be instantiated: a C++ data source is required.");
            return NULL;
        }
    };

}
