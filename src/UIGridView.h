#pragma once
// UIGridView.h - Rendering view for GridData (#252)
//
// GridView is a UIDrawable that renders a GridData object. Multiple GridViews
// can reference the same GridData for split-screen, minimap, etc.
// GridView holds rendering state (camera, zoom, perspective) independently.

#include "Common.h"
#include "Python.h"
#include "structmember.h"
#include "UIDrawable.h"
#include "UIBase.h"
#include "GridData.h"
#include "PyTexture.h"
#include "PyColor.h"
#include "PyVector.h"
#include "PyCallable.h"
#include "PyDrawable.h"

// Forward declarations
class UIGrid;
class UIGridView;

// Python object struct (UIGridView forward-declared above)
typedef struct {
    PyObject_HEAD
    std::shared_ptr<UIGridView> data;
    PyObject* weakreflist;
} PyUIGridViewObject;

class UIGridView : public UIDrawable
{
public:
    UIGridView();
    ~UIGridView();

    void render(sf::Vector2f offset, sf::RenderTarget& target) override final;
    PyObjectsEnum derived_type() override final;
    UIDrawable* click_at(sf::Vector2f point) override final;

    sf::FloatRect get_bounds() const override;
    void move(float dx, float dy) override;
    void resize(float w, float h) override;
    void onPositionChanged() override;   // #355: keep box in sync with position

    // The grid data this view renders
    std::shared_ptr<GridData> grid_data;

    // #348 - Persistent wrapper for the internal UIGrid, so that repeated
    // attribute delegation (grid.at(), grid.entities, etc.) reuses one Python
    // object instead of allocating a throwaway wrapper + weakref per access.
    // The view owns one strong ref for its lifetime; released in ~UIGridView.
    // No ownership cycle: this wrapper aliases the UIGrid control block, which
    // is a different object/control block than the view's own PyObject.
    PyObject* cached_grid_wrapper = nullptr;

    // =====================================================================
    // #364 - Overlay children (speech bubbles, markers, range indicators).
    // Owned by the VIEW, not GridData: a child is an annotation drawn over the
    // map through THIS camera, not world content. Two views over one GridData
    // therefore have independent children (a minimap does not want the main
    // view's speech bubbles) while sharing every entity.
    //
    // Positions are in GRID-WORLD PIXEL coordinates (#360) -- not view-local,
    // not screen -- so panning the camera does not move a child's logical
    // position. The view's camera maps them to screen at render/hit-test time.
    // =====================================================================
    std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>> children;
    bool children_need_sort = true;

    // Rendering state (independent per view)
    std::shared_ptr<PyTexture> ptex;
    sf::RectangleShape box;
    float center_x = 0, center_y = 0, zoom = 1.0f;
    float camera_rotation = 0.0f;
    sf::Color fill_color{8, 8, 8, 255};

    // Perspective (per-view)
    std::weak_ptr<UIEntity> perspective_entity;
    bool perspective_enabled = false;

    // =====================================================================
    // #355 - Cell input. Owned by the VIEW, not GridData: two views over one
    // GridData must each track their own hover cell (a shared hovered_cell
    // would ping-pong exit/enter between views), and the subclass-dispatch
    // path must resolve against the VIEW's serial_number, because the public
    // subclassable type (mcrfpy.Grid) IS UIGridView.
    // =====================================================================
    std::unique_ptr<PyCellHoverCallable> on_cell_enter_callable;
    std::unique_ptr<PyCellHoverCallable> on_cell_exit_callable;
    std::unique_ptr<PyClickCallable>     on_cell_click_callable;
    std::optional<sf::Vector2i> hovered_cell;       // Python-visible (read-only)
    std::optional<sf::Vector2i> last_clicked_cell;  // C++ only: click_at -> dispatchCellClick

    struct CellCallbackCache {
        uint32_t generation = 0;
        bool valid = false;
        bool has_on_cell_click = false;
        bool has_on_cell_enter = false;
        bool has_on_cell_exit = false;
    };
    CellCallbackCache cell_callback_cache;

    bool fireCellClick(sf::Vector2i cell, const std::string& button, const std::string& action);
    bool fireCellEnter(sf::Vector2i cell);
    bool fireCellExit(sf::Vector2i cell);
    void refreshCellCallbackCache(PyObject* pyObj);

    // UIDrawable input virtuals (#355)
    bool dispatchCellClick(const std::string& button, const std::string& action) override;
    void updateHover(sf::Vector2f point, bool hit_allowed) override;
    GridData* asGridData() override { return grid_data.get(); }

    // Cell math. local_point is relative to the widget's top-left.
    sf::Vector2f localToGridWorld(sf::Vector2f local_point) const;
    std::optional<sf::Vector2i> cellAtLocal(sf::Vector2f local_point) const;

    // #351 - clean-state render early-out cache. These record the inputs the
    // current RenderTexture was rasterized from; render() re-blits the cached
    // texture instead of clear+redraw when none changed. Camera params are
    // view-local (compared directly); grid content changes bump
    // GridData::content_generation. Perspective overlays and grid children are
    // dynamic sources not tracked precisely yet (#352) -> conservative full render.
    bool has_rendered_once = false;
    uint64_t last_content_gen = 0;
    float last_center_x = 0.f, last_center_y = 0.f, last_zoom = 0.f, last_camera_rotation = 0.f;
    sf::Vector2f last_box_size{-1.f, -1.f};
    sf::Color last_fill_color{0, 0, 0, 0};
    sf::Vector2u last_render_tex_size{0, 0};
    bool last_perspective_enabled = false;  // #355: fog baked into the cached raster

    // Render textures
    sf::Sprite sprite_proto, output;
    sf::RenderTexture renderTexture;
    sf::Vector2u renderTextureSize{0, 0};
    void ensureRenderTextureSize();
    std::unique_ptr<sf::RenderTexture> rotationTexture;  // #338 - lazy: only rotating grids allocate it
    unsigned int rotationTextureSize = 0;

    // Property system for animations
    bool setProperty(const std::string& name, float value) override;
    bool setProperty(const std::string& name, const sf::Vector2f& value) override;
    bool getProperty(const std::string& name, float& value) const override;
    bool getProperty(const std::string& name, sf::Vector2f& value) const override;
    bool hasProperty(const std::string& name) const override;

    // Camera positioning
    void center_camera();
    void center_camera(float tile_x, float tile_y);

    // #355: no screenToCell() -- hover/click both arrive in parent-local space and
    // go through cellAtLocal(). A global-coords helper would be a second, wrong
    // coordinate path for grids nested inside frames/grids.
    sf::Vector2f getEffectiveCellSize() const;

    static constexpr int DEFAULT_CELL_WIDTH = 16;
    static constexpr int DEFAULT_CELL_HEIGHT = 16;

    // =========================================================================
    // Python API
    // =========================================================================
    static int init(PyUIGridViewObject* self, PyObject* args, PyObject* kwds);
    // #361: one init() for both modes -- Grid(grid_size=...) creates its own
    // GridData, Grid(grid=data) attaches to an existing one.
    static PyObject* repr(PyUIGridViewObject* self);

    // #252 - Attribute delegation to underlying Grid
    static PyObject* getattro(PyObject* self, PyObject* name);
    static int setattro(PyObject* self, PyObject* name, PyObject* value);

    // Helper: get the underlying Grid as a Python object (borrowed-like via cache)
    static PyObject* get_grid_pyobj(PyUIGridViewObject* self);

    static PyObject* get_grid(PyUIGridViewObject* self, void* closure);
    static int set_grid(PyUIGridViewObject* self, PyObject* value, void* closure);
    static PyObject* get_center(PyUIGridViewObject* self, void* closure);
    static int set_center(PyUIGridViewObject* self, PyObject* value, void* closure);
    static PyObject* get_zoom(PyUIGridViewObject* self, void* closure);
    static int set_zoom(PyUIGridViewObject* self, PyObject* value, void* closure);
    // #361 - `size` and `center_camera()` used to delegate to the internal UIGrid's
    // ghost camera, making them silent no-ops on the widget being rendered.
    static PyObject* get_size(PyUIGridViewObject* self, void* closure);
    static int set_size(PyUIGridViewObject* self, PyObject* value, void* closure);
    static PyObject* py_center_camera(PyUIGridViewObject* self, PyObject* args);
    static PyObject* get_fill_color(PyUIGridViewObject* self, void* closure);
    static int set_fill_color(PyUIGridViewObject* self, PyObject* value, void* closure);
    static PyObject* get_texture(PyUIGridViewObject* self, void* closure);
    static PyObject* get_float_member_gv(PyUIGridViewObject* self, void* closure);
    static int set_float_member_gv(PyUIGridViewObject* self, PyObject* value, void* closure);

    // #364 - overlay children (moved from GridData)
    static PyObject* get_children(PyUIGridViewObject* self, void* closure);

    // #355 - cell callback properties (moved from UIGrid)
    static PyObject* get_on_cell_enter(PyUIGridViewObject* self, void* closure);
    static int set_on_cell_enter(PyUIGridViewObject* self, PyObject* value, void* closure);
    static PyObject* get_on_cell_exit(PyUIGridViewObject* self, void* closure);
    static int set_on_cell_exit(PyUIGridViewObject* self, PyObject* value, void* closure);
    static PyObject* get_on_cell_click(PyUIGridViewObject* self, void* closure);
    static int set_on_cell_click(PyUIGridViewObject* self, PyObject* value, void* closure);
    static PyObject* get_hovered_cell(PyUIGridViewObject* self, void* closure);

    // #355 - perspective properties (moved from UIGrid: the view renders the overlay)
    static PyObject* get_perspective(PyUIGridViewObject* self, void* closure);
    static int set_perspective(PyUIGridViewObject* self, PyObject* value, void* closure);
    static PyObject* get_perspective_enabled(PyUIGridViewObject* self, void* closure);
    static int set_perspective_enabled(PyUIGridViewObject* self, PyObject* value, void* closure);

    static PyMethodDef methods[];
    static PyGetSetDef getsetters[];

    // Subscript protocol: grid[x, y] (delegates to underlying GridData).
    // Setitem raises TypeError (GridPoints are views).
    static PyObject* subscript(PyUIGridViewObject* self, PyObject* key);
    static int subscript_assign(PyUIGridViewObject* self, PyObject* key, PyObject* value);
    static PyMappingMethods mpmethods;
};

// Forward declaration of methods array
extern PyMethodDef UIGridView_all_methods[];

namespace mcrfpydef {
    // #252: GridView is the primary user-facing type. "mcrfpy.Grid" is an alias.
    // Grid() auto-creates a GridData (UIGrid internally); GridView(grid=...) wraps existing data.
    // Attribute access delegates to underlying Grid for data properties/methods.
    inline PyTypeObject PyUIGridViewType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        // #361: the canonical name is GridView -- it IS the camera/widget. "Grid"
        // is bound to this same type object as an alias (see McRFPy_API.cpp).
        .tp_name = "mcrfpy.GridView",
        .tp_basicsize = sizeof(PyUIGridViewObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)[](PyObject* self)
        {
            PyUIGridViewObject* obj = (PyUIGridViewObject*)self;
            PyObject_GC_UnTrack(self);
            if (obj->weakreflist != NULL) {
                PyObject_ClearWeakRefs(self);
            }
            // #359: Unregister from the GridData's view list before releasing
            // grid_data -- but only when this wrapper is the LAST owner of the
            // view (#251 pattern, mirrors PyGridDataType). An ungated unregister
            // would sever the back-reference whenever ANY Python wrapper was
            // GC'd while the C++ view lived on (e.g. held by scene.children),
            // breaking entity.grid -> Grid identity and the #313 data-layer
            // dirty notifications. unregisterView matches by identity, so it's
            // harmless (a no-op) if this view was never registered.
            if (obj->data && obj->data->grid_data && obj->data.use_count() <= 1) {
                obj->data->grid_data->unregisterView(obj->data.get());
            }
            obj->data.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)UIGridView::repr,
        .tp_as_mapping = &UIGridView::mpmethods,  // grid[x, y] (delegates to GridData)
        .tp_getattro = UIGridView::getattro,  // #252: attribute delegation to Grid
        .tp_setattro = UIGridView::setattro,   // #252: attribute delegation to Grid
        .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC,
        .tp_doc = PyDoc_STR(
            "Grid(grid_size=None, pos=None, size=None, texture=None, **kwargs)\n\n"
            "A grid-based UI element for tile-based rendering and entity management.\n"
            "Creates and owns grid data (cells, entities, layers) with an integrated\n"
            "rendering view (camera, zoom, perspective).\n\n"
            "Can also be constructed as a view of existing grid data:\n"
            "    Grid(grid=existing_grid, pos=..., size=...)\n\n"
            "Args:\n"
            "    grid_size (tuple): Grid dimensions as (grid_w, grid_h). Default: (2, 2)\n"
            "    pos (tuple): Position as (x, y). Default: (0, 0)\n"
            "    size (tuple): Size as (w, h). Default: auto-calculated\n"
            "    texture (Texture): Tile texture atlas. Default: default texture\n\n"
            "Keyword Args:\n"
            "    grid (Grid): Existing Grid to view (creates view of shared data).\n"
            "    fill_color (Color): Background fill color.\n"
            "    on_click (callable): Click event handler.\n"
            "    center_x, center_y (float): Camera center coordinates.\n"
            "    zoom (float): Zoom level. Default: 1.0\n"
            "    visible (bool): Visibility. Default: True\n"
            "    opacity (float): Opacity (0.0-1.0). Default: 1.0\n"
            "    z_index (int): Rendering order. Default: 0\n"
            "    name (str): Element name.\n"
            "    layers (list): List of ColorLayer/TileLayer objects.\n"),
        .tp_traverse = [](PyObject* self, visitproc visit, void* arg) -> int {
            PyUIGridViewObject* obj = (PyUIGridViewObject*)self;
            if (obj->data && obj->data->click_callable) {
                PyObject* callback = obj->data->click_callable->borrow();
                if (callback && callback != Py_None) Py_VISIT(callback);
            }
            // #348: the view owns a strong ref to the internal Grid wrapper.
            if (obj->data && obj->data->cached_grid_wrapper) {
                Py_VISIT(obj->data->cached_grid_wrapper);
            }
            // #355: cell callbacks now live on the view.
            if (obj->data) {
                if (obj->data->on_cell_enter_callable) {
                    PyObject* cb = obj->data->on_cell_enter_callable->borrow();
                    if (cb && cb != Py_None) Py_VISIT(cb);
                }
                if (obj->data->on_cell_exit_callable) {
                    PyObject* cb = obj->data->on_cell_exit_callable->borrow();
                    if (cb && cb != Py_None) Py_VISIT(cb);
                }
                if (obj->data->on_cell_click_callable) {
                    PyObject* cb = obj->data->on_cell_click_callable->borrow();
                    if (cb && cb != Py_None) Py_VISIT(cb);
                }
            }
            return 0;
        },
        .tp_clear = [](PyObject* self) -> int {
            PyUIGridViewObject* obj = (PyUIGridViewObject*)self;
            if (obj->data) {
                obj->data->click_unregister();
                // #348: drop the persistent wrapper; get_grid rebuilds on demand.
                Py_CLEAR(obj->data->cached_grid_wrapper);
                // #355: release cell callbacks (breaks closure->grid cycles).
                obj->data->on_cell_enter_callable.reset();
                obj->data->on_cell_exit_callable.reset();
                obj->data->on_cell_click_callable.reset();
            }
            return 0;
        },
        .tp_methods = UIGridView_all_methods,
        .tp_getset = UIGridView::getsetters,
        .tp_base = &mcrfpydef::PyDrawableType,
        .tp_init = (initproc)UIGridView::init,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            PyUIGridViewObject* self = (PyUIGridViewObject*)type->tp_alloc(type, 0);
            if (self) {
                self->data = std::make_shared<UIGridView>();
                self->weakreflist = nullptr;
            }
            return (PyObject*)self;
        }
    };
}
