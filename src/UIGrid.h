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
#include "GridData.h"  // #252 - Data layer base class

// Forward declaration for pathfinding
class DijkstraMap;

// UIGrid inherits both UIDrawable (rendering) and GridData (state).
// This allows GridData to be shared with GridView for multi-view support (#252).
class UIGrid: public UIDrawable, public GridData
{
private:
    std::shared_ptr<PyTexture> ptex;
    // Default cell dimensions when no texture is provided
    static constexpr int DEFAULT_CELL_WIDTH = 16;
    static constexpr int DEFAULT_CELL_HEIGHT = 16;

public:
    UIGrid();
    UIGrid(int, int, std::shared_ptr<PyTexture>, sf::Vector2f, sf::Vector2f);
    ~UIGrid();
    void update();
    void render(sf::Vector2f, sf::RenderTarget&) override final;
    PyObjectsEnum derived_type() override final;
    virtual UIDrawable* click_at(sf::Vector2f point) override final;

    // Phase 1 virtual method implementations
    sf::FloatRect get_bounds() const override;
    void move(float dx, float dy) override;
    void resize(float w, float h) override;
    void onPositionChanged() override;

    // =========================================================================
    // Rendering-only members (NOT in GridData)
    // =========================================================================
    sf::RectangleShape box;
    float center_x, center_y, zoom;
    float camera_rotation = 0.0f;
    std::shared_ptr<PyTexture> getTexture();
    sf::Sprite sprite, output;
    sf::RenderTexture renderTexture;
    sf::Vector2u renderTextureSize{0, 0};
    void ensureRenderTextureSize();
    sf::RenderTexture rotationTexture;
    unsigned int rotationTextureSize = 0;

    // Background rendering
    sf::Color fill_color;

    // Perspective system
    std::weak_ptr<UIEntity> perspective_entity;
    bool perspective_enabled;

    // Cell callback firing (needs UIDrawable::is_python_subclass, serial_number)
    bool fireCellClick(sf::Vector2i cell, const std::string& button, const std::string& action);
    bool fireCellEnter(sf::Vector2i cell);
    bool fireCellExit(sf::Vector2i cell);
    void refreshCellCallbackCache(PyObject* pyObj);

    // #142 - Cell coordinate conversion (needs texture for cell size)
    std::optional<sf::Vector2i> screenToCell(sf::Vector2f screen_pos) const;
    sf::Vector2f getEffectiveCellSize() const;
    void updateCellHover(sf::Vector2f mousepos, const std::string& button, const std::string& action);

    // Property system for animations
    bool setProperty(const std::string& name, float value) override;
    bool setProperty(const std::string& name, const sf::Vector2f& value) override;
    bool getProperty(const std::string& name, float& value) const override;
    bool getProperty(const std::string& name, sf::Vector2f& value) const override;
    bool hasProperty(const std::string& name) const override;

    // #169 - Camera positioning
    void center_camera();
    void center_camera(float tile_x, float tile_y);

    // =========================================================================
    // Python API (static methods)
    // =========================================================================
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
    static PyObject* py_entities_in_radius(PyUIGridObject* self, PyObject* args, PyObject* kwds);
    static PyObject* py_center_camera(PyUIGridObject* self, PyObject* args);
    static PyObject* get_camera_rotation(PyUIGridObject* self, void* closure);
    static int set_camera_rotation(PyUIGridObject* self, PyObject* value, void* closure);
    static PyObject* py_apply_threshold(PyUIGridObject* self, PyObject* args, PyObject* kwds);
    static PyObject* py_apply_ranges(PyUIGridObject* self, PyObject* args);
    static PyObject* py_step(PyUIGridObject* self, PyObject* args, PyObject* kwds);

    static PyMethodDef methods[];
    static PyGetSetDef getsetters[];
    static PyMappingMethods mpmethods;
    static PyObject* subscript(PyUIGridObject* self, PyObject* key);
    static PyObject* get_entities(PyUIGridObject* self, void* closure);
    static PyObject* get_children(PyUIGridObject* self, void* closure);
    static PyObject* repr(PyUIGridObject* self);

    static PyObject* get_on_cell_enter(PyUIGridObject* self, void* closure);
    static int set_on_cell_enter(PyUIGridObject* self, PyObject* value, void* closure);
    static PyObject* get_on_cell_exit(PyUIGridObject* self, void* closure);
    static int set_on_cell_exit(PyUIGridObject* self, PyObject* value, void* closure);
    static PyObject* get_on_cell_click(PyUIGridObject* self, void* closure);
    static int set_on_cell_click(PyUIGridObject* self, PyObject* value, void* closure);
    static PyObject* get_hovered_cell(PyUIGridObject* self, void* closure);

    static PyObject* py_add_layer(PyUIGridObject* self, PyObject* args);
    static PyObject* py_remove_layer(PyUIGridObject* self, PyObject* args);
    static PyObject* get_layers(PyUIGridObject* self, void* closure);
    static PyObject* py_layer(PyUIGridObject* self, PyObject* args);
};

// UIEntityCollection types are now in UIEntityCollection.h

// Forward declaration of methods array
extern PyMethodDef UIGrid_all_methods[];

namespace mcrfpydef {
    inline PyTypeObject PyUIGridType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Grid",
        .tp_basicsize = sizeof(PyUIGridObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)[](PyObject* self)
        {
            PyUIGridObject* obj = (PyUIGridObject*)self;
            // Untrack from GC before destroying
            PyObject_GC_UnTrack(self);
            // Clear weak references
            if (obj->weakreflist != NULL) {
                PyObject_ClearWeakRefs(self);
            }
            // Only unregister callbacks if we're the last owner (#251)
            if (obj->data && obj->data.use_count() <= 1) {
                obj->data->click_unregister();
                obj->data->on_enter_unregister();
                obj->data->on_exit_unregister();
                obj->data->on_move_unregister();
                // Grid-specific cell callbacks (now on GridData base)
                obj->data->on_cell_enter_callable.reset();
                obj->data->on_cell_exit_callable.reset();
                obj->data->on_cell_click_callable.reset();
            }
            obj->data.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)UIGrid::repr,
        .tp_as_mapping = &UIGrid::mpmethods,
        .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC,
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
        .tp_traverse = [](PyObject* self, visitproc visit, void* arg) -> int {
            PyUIGridObject* obj = (PyUIGridObject*)self;
            if (obj->data) {
                if (obj->data->click_callable) {
                    PyObject* callback = obj->data->click_callable->borrow();
                    if (callback && callback != Py_None) Py_VISIT(callback);
                }
                if (obj->data->on_enter_callable) {
                    PyObject* callback = obj->data->on_enter_callable->borrow();
                    if (callback && callback != Py_None) Py_VISIT(callback);
                }
                if (obj->data->on_exit_callable) {
                    PyObject* callback = obj->data->on_exit_callable->borrow();
                    if (callback && callback != Py_None) Py_VISIT(callback);
                }
                if (obj->data->on_move_callable) {
                    PyObject* callback = obj->data->on_move_callable->borrow();
                    if (callback && callback != Py_None) Py_VISIT(callback);
                }
                if (obj->data->on_cell_enter_callable) {
                    PyObject* callback = obj->data->on_cell_enter_callable->borrow();
                    if (callback && callback != Py_None) Py_VISIT(callback);
                }
                if (obj->data->on_cell_exit_callable) {
                    PyObject* callback = obj->data->on_cell_exit_callable->borrow();
                    if (callback && callback != Py_None) Py_VISIT(callback);
                }
                if (obj->data->on_cell_click_callable) {
                    PyObject* callback = obj->data->on_cell_click_callable->borrow();
                    if (callback && callback != Py_None) Py_VISIT(callback);
                }
            }
            return 0;
        },
        .tp_clear = [](PyObject* self) -> int {
            PyUIGridObject* obj = (PyUIGridObject*)self;
            if (obj->data) {
                obj->data->click_unregister();
                obj->data->on_enter_unregister();
                obj->data->on_exit_unregister();
                obj->data->on_move_unregister();
                obj->data->on_cell_enter_callable.reset();
                obj->data->on_cell_exit_callable.reset();
                obj->data->on_cell_click_callable.reset();
            }
            return 0;
        },
        .tp_methods = UIGrid_all_methods,
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
}
