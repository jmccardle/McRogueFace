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

    // The grid data this view renders
    std::shared_ptr<GridData> grid_data;

    // Rendering state (independent per view)
    std::shared_ptr<PyTexture> ptex;
    sf::RectangleShape box;
    float center_x = 0, center_y = 0, zoom = 1.0f;
    float camera_rotation = 0.0f;
    sf::Color fill_color{8, 8, 8, 255};

    // Perspective (per-view)
    std::weak_ptr<UIEntity> perspective_entity;
    bool perspective_enabled = false;

    // Render textures
    sf::Sprite sprite_proto, output;
    sf::RenderTexture renderTexture;
    sf::Vector2u renderTextureSize{0, 0};
    void ensureRenderTextureSize();
    sf::RenderTexture rotationTexture;
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

    // Cell coordinate conversion
    std::optional<sf::Vector2i> screenToCell(sf::Vector2f screen_pos) const;
    sf::Vector2f getEffectiveCellSize() const;

    static constexpr int DEFAULT_CELL_WIDTH = 16;
    static constexpr int DEFAULT_CELL_HEIGHT = 16;

    // =========================================================================
    // Python API
    // =========================================================================
    static int init(PyUIGridViewObject* self, PyObject* args, PyObject* kwds);
    static int init_with_data(PyUIGridViewObject* self, PyObject* args, PyObject* kwds);
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
    static PyObject* get_fill_color(PyUIGridViewObject* self, void* closure);
    static int set_fill_color(PyUIGridViewObject* self, PyObject* value, void* closure);
    static PyObject* get_texture(PyUIGridViewObject* self, void* closure);
    static PyObject* get_float_member_gv(PyUIGridViewObject* self, void* closure);
    static int set_float_member_gv(PyUIGridViewObject* self, PyObject* value, void* closure);

    static PyMethodDef methods[];
    static PyGetSetDef getsetters[];
};

// Forward declaration of methods array
extern PyMethodDef UIGridView_all_methods[];

namespace mcrfpydef {
    // #252: GridView is the primary user-facing type. "mcrfpy.Grid" is an alias.
    // Grid() auto-creates a GridData (UIGrid internally); GridView(grid=...) wraps existing data.
    // Attribute access delegates to underlying Grid for data properties/methods.
    inline PyTypeObject PyUIGridViewType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Grid",  // #252: primary name is Grid
        .tp_basicsize = sizeof(PyUIGridViewObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)[](PyObject* self)
        {
            PyUIGridViewObject* obj = (PyUIGridViewObject*)self;
            PyObject_GC_UnTrack(self);
            if (obj->weakreflist != NULL) {
                PyObject_ClearWeakRefs(self);
            }
            // Clear owning_view back-reference before releasing grid_data
            if (obj->data && obj->data->grid_data) {
                obj->data->grid_data->owning_view.reset();
            }
            obj->data.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)UIGridView::repr,
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
            return 0;
        },
        .tp_clear = [](PyObject* self) -> int {
            PyUIGridViewObject* obj = (PyUIGridViewObject*)self;
            if (obj->data) {
                obj->data->click_unregister();
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
