#pragma once
#include "Common.h"
#include "Python.h"
#include "structmember.h"
#include "IndexTexture.h"
#include "Resources.h"
#include <list>
#include <libtcod.h>
#include <mutex>
#include <optional>
#include <map>
#include <memory>

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
#include "GridLayers.h"
#include "GridChunk.h"
#include "SpatialHash.h"
#include "UIEntityCollection.h"  // EntityCollection types (extracted from UIGrid)

// Forward declaration for pathfinding
class DijkstraMap;

class UIGrid: public UIDrawable
{
private:
    std::shared_ptr<PyTexture> ptex;
    // Default cell dimensions when no texture is provided
    static constexpr int DEFAULT_CELL_WIDTH = 16;
    static constexpr int DEFAULT_CELL_HEIGHT = 16;
    TCODMap* tcod_map;  // TCOD map for FOV and pathfinding
    mutable std::mutex fov_mutex;  // Mutex for thread-safe FOV operations

public:
    // Dijkstra map cache - keyed by root position
    // Public so UIGridPathfinding can access it
    std::map<std::pair<int,int>, std::shared_ptr<DijkstraMap>> dijkstra_maps;

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
    TCODMap* getTCODMap() const { return tcod_map; }  // Access for pathfinding
    
    // Pathfinding - new API creates AStarPath/DijkstraMap objects
    // See UIGridPathfinding.h for the new pathfinding API
    // Grid.find_path() now returns AStarPath objects
    // Grid.get_dijkstra_map() returns DijkstraMap objects (cached by root position)
    
    // Phase 1 virtual method implementations
    sf::FloatRect get_bounds() const override;
    void move(float dx, float dy) override;
    void resize(float w, float h) override;
    void onPositionChanged() override;

    int grid_w, grid_h;
    //int grid_size; // grid sizes are implied by IndexTexture now
    sf::RectangleShape box;
    float center_x, center_y, zoom;
    //IndexTexture* itex;
    std::shared_ptr<PyTexture> getTexture();
    sf::Sprite sprite, output;
    sf::RenderTexture renderTexture;

    // #123 - Chunk-based storage for large grid support
    std::unique_ptr<ChunkManager> chunk_manager;
    // Legacy flat storage (kept for small grids or compatibility)
    std::vector<UIGridPoint> points;
    // Use chunks for grids larger than this threshold
    static constexpr int CHUNK_THRESHOLD = 64;
    bool use_chunks;

    std::shared_ptr<std::list<std::shared_ptr<UIEntity>>> entities;

    // Spatial hash for O(1) entity queries (#115)
    SpatialHash spatial_hash;

    // UIDrawable children collection (speech bubbles, effects, overlays, etc.)
    std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>> children;
    bool children_need_sort = true;  // Dirty flag for z_index sorting

    // Dynamic layer system (#147)
    std::vector<std::shared_ptr<GridLayer>> layers;
    bool layers_need_sort = true;  // Dirty flag for z_index sorting

    // Layer management (#150 - extended with names)
    std::shared_ptr<ColorLayer> addColorLayer(int z_index, const std::string& name = "");
    std::shared_ptr<TileLayer> addTileLayer(int z_index, std::shared_ptr<PyTexture> texture = nullptr, const std::string& name = "");
    void removeLayer(std::shared_ptr<GridLayer> layer);
    void sortLayers();
    std::shared_ptr<GridLayer> getLayerByName(const std::string& name);

    // #150 - Protected layer names (reserved for GridPoint properties)
    static bool isProtectedLayerName(const std::string& name);

    // Background rendering
    sf::Color fill_color;

    // Perspective system - entity whose view to render
    std::weak_ptr<UIEntity> perspective_entity;  // Weak reference to perspective entity
    bool perspective_enabled;                     // Whether to use perspective rendering

    // #114 - FOV algorithm and radius for this grid
    TCOD_fov_algorithm_t fov_algorithm;           // Default FOV algorithm (from mcrfpy.default_fov)
    int fov_radius;                               // Default FOV radius

    // #142 - Grid cell mouse events
    std::unique_ptr<PyClickCallable> on_cell_enter_callable;
    std::unique_ptr<PyClickCallable> on_cell_exit_callable;
    std::unique_ptr<PyClickCallable> on_cell_click_callable;
    std::optional<sf::Vector2i> hovered_cell;  // Currently hovered cell or nullopt

    // #142 - Cell coordinate conversion (screen pos -> cell coords)
    std::optional<sf::Vector2i> screenToCell(sf::Vector2f screen_pos) const;

    // #221 - Get effective cell size (texture size * zoom)
    sf::Vector2f getEffectiveCellSize() const;

    // #142 - Update cell hover state (called from PyScene)
    void updateCellHover(sf::Vector2f mousepos);
    
    // Property system for animations
    bool setProperty(const std::string& name, float value) override;
    bool setProperty(const std::string& name, const sf::Vector2f& value) override;
    bool getProperty(const std::string& name, float& value) const override;
    bool getProperty(const std::string& name, sf::Vector2f& value) const override;

    bool hasProperty(const std::string& name) const override;

    static int init(PyUIGridObject* self, PyObject* args, PyObject* kwds);
    static PyObject* get_grid_size(PyUIGridObject* self, void* closure);
    static PyObject* get_grid_w(PyUIGridObject* self, void* closure);
    static PyObject* get_grid_h(PyUIGridObject* self, void* closure);
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
    static PyObject* get_perspective_enabled(PyUIGridObject* self, void* closure);
    static int set_perspective_enabled(PyUIGridObject* self, PyObject* value, void* closure);
    static PyObject* get_fov(PyUIGridObject* self, void* closure);
    static int set_fov(PyUIGridObject* self, PyObject* value, void* closure);
    static PyObject* get_fov_radius(PyUIGridObject* self, void* closure);
    static int set_fov_radius(PyUIGridObject* self, PyObject* value, void* closure);
    static PyObject* py_at(PyUIGridObject* self, PyObject* args, PyObject* kwds);
    static PyObject* py_compute_fov(PyUIGridObject* self, PyObject* args, PyObject* kwds);
    static PyObject* py_is_in_fov(PyUIGridObject* self, PyObject* args, PyObject* kwds);
    // Pathfinding methods moved to UIGridPathfinding.cpp
    // py_find_path -> UIGridPathfinding::Grid_find_path (returns AStarPath)
    // py_get_dijkstra_map -> UIGridPathfinding::Grid_get_dijkstra_map (returns DijkstraMap)
    // py_clear_dijkstra_maps -> UIGridPathfinding::Grid_clear_dijkstra_maps
    static PyObject* py_entities_in_radius(PyUIGridObject* self, PyObject* args, PyObject* kwds);  // #115
    static PyObject* py_center_camera(PyUIGridObject* self, PyObject* args);  // #169

    // #199 - HeightMap application methods
    static PyObject* py_apply_threshold(PyUIGridObject* self, PyObject* args, PyObject* kwds);
    static PyObject* py_apply_ranges(PyUIGridObject* self, PyObject* args);

    // #169 - Camera positioning
    void center_camera();  // Center on grid's middle tile
    void center_camera(float tile_x, float tile_y);  // Center on specific tile

    static PyMethodDef methods[];
    static PyGetSetDef getsetters[];
    static PyMappingMethods mpmethods;  // For grid[x, y] subscript access
    static PyObject* subscript(PyUIGridObject* self, PyObject* key);  // __getitem__
    static PyObject* get_entities(PyUIGridObject* self, void* closure);
    static PyObject* get_children(PyUIGridObject* self, void* closure);
    static PyObject* repr(PyUIGridObject* self);

    // #142 - Grid cell mouse event Python API
    static PyObject* get_on_cell_enter(PyUIGridObject* self, void* closure);
    static int set_on_cell_enter(PyUIGridObject* self, PyObject* value, void* closure);
    static PyObject* get_on_cell_exit(PyUIGridObject* self, void* closure);
    static int set_on_cell_exit(PyUIGridObject* self, PyObject* value, void* closure);
    static PyObject* get_on_cell_click(PyUIGridObject* self, void* closure);
    static int set_on_cell_click(PyUIGridObject* self, PyObject* value, void* closure);
    static PyObject* get_hovered_cell(PyUIGridObject* self, void* closure);

    // #147 - Layer system Python API
    static PyObject* py_add_layer(PyUIGridObject* self, PyObject* args, PyObject* kwds);
    static PyObject* py_remove_layer(PyUIGridObject* self, PyObject* args);
    static PyObject* get_layers(PyUIGridObject* self, void* closure);
    static PyObject* py_layer(PyUIGridObject* self, PyObject* args);
};

// UIEntityCollection types are now in UIEntityCollection.h

// Forward declaration of methods array
extern PyMethodDef UIGrid_all_methods[];

namespace mcrfpydef {
    static PyTypeObject PyUIGridType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Grid",
        .tp_basicsize = sizeof(PyUIGridObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)[](PyObject* self)
        {
            PyUIGridObject* obj = (PyUIGridObject*)self;
            // Clear weak references
            if (obj->weakreflist != NULL) {
                PyObject_ClearWeakRefs(self);
            }
            obj->data.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)UIGrid::repr,
        .tp_as_mapping = &UIGrid::mpmethods,  // Enable grid[x, y] subscript access
        .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
        .tp_doc = PyDoc_STR("Grid(pos=None, size=None, grid_size=None, texture=None, **kwargs)\n\n"
                            "A grid-based UI element for tile-based rendering and entity management.\n\n"
                            "Args:\n"
                            "    pos (tuple, optional): Position as (x, y) tuple. Default: (0, 0)\n"
                            "    size (tuple, optional): Size as (width, height) tuple. Default: auto-calculated from grid_size\n"
                            "    grid_size (tuple, optional): Grid dimensions as (grid_w, grid_h) tuple. Default: (2, 2)\n"
                            "    texture (Texture, optional): Texture containing tile sprites. Default: default texture\n\n"
                            "Keyword Args:\n"
                            "    fill_color (Color): Background fill color. Default: None\n"
                            "    click (callable): Click event handler. Default: None\n"
                            "    center_x (float): X coordinate of center point. Default: 0\n"
                            "    center_y (float): Y coordinate of center point. Default: 0\n"
                            "    zoom (float): Zoom level for rendering. Default: 1.0\n"
                            "    perspective (int): Entity perspective index (-1 for omniscient). Default: -1\n"
                            "    visible (bool): Visibility state. Default: True\n"
                            "    opacity (float): Opacity (0.0-1.0). Default: 1.0\n"
                            "    z_index (int): Rendering order. Default: 0\n"
                            "    name (str): Element name for finding. Default: None\n"
                            "    x (float): X position override. Default: 0\n"
                            "    y (float): Y position override. Default: 0\n"
                            "    w (float): Width override. Default: auto-calculated\n"
                            "    h (float): Height override. Default: auto-calculated\n"
                            "    grid_w (int): Grid width override. Default: 2\n"
                            "    grid_h (int): Grid height override. Default: 2\n"
                            "    align (Alignment): Alignment relative to parent. Default: None\n"
                            "    margin (float): Margin from parent edge when aligned. Default: 0\n"
                            "    horiz_margin (float): Horizontal margin override. Default: 0 (use margin)\n"
                            "    vert_margin (float): Vertical margin override. Default: 0 (use margin)\n\n"
                            "Attributes:\n"
                            "    x, y (float): Position in pixels\n"
                            "    w, h (float): Size in pixels\n"
                            "    pos (Vector): Position as a Vector object\n"
                            "    size (Vector): Size as (width, height) Vector\n"
                            "    center (Vector): Center point as (x, y) Vector\n"
                            "    center_x, center_y (float): Center point coordinates\n"
                            "    zoom (float): Zoom level for rendering\n"
                            "    grid_size (Vector): Grid dimensions (width, height) in tiles\n"
                            "    grid_w, grid_h (int): Grid dimensions\n"
                            "    texture (Texture): Tile texture atlas\n"
                            "    fill_color (Color): Background color\n"
                            "    entities (EntityCollection): Collection of entities in the grid\n"
                            "    perspective (int): Entity perspective index\n"
                            "    click (callable): Click event handler\n"
                            "    visible (bool): Visibility state\n"
                            "    opacity (float): Opacity value\n"
                            "    z_index (int): Rendering order\n"
                            "    name (str): Element name\n"
                            "    align (Alignment): Alignment relative to parent (or None)\n"
                            "    margin (float): General margin for alignment\n"
                            "    horiz_margin (float): Horizontal margin override\n"
                            "    vert_margin (float): Vertical margin override"),
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

    // EntityCollection types moved to UIEntityCollection.h

}
