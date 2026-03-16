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
    static PyObject* repr(PyUIGridViewObject* self);

    static PyObject* get_grid(PyUIGridViewObject* self, void* closure);
    static int set_grid(PyUIGridViewObject* self, PyObject* value, void* closure);
    static PyObject* get_center(PyUIGridViewObject* self, void* closure);
    static int set_center(PyUIGridViewObject* self, PyObject* value, void* closure);
    static PyObject* get_zoom(PyUIGridViewObject* self, void* closure);
    static int set_zoom(PyUIGridViewObject* self, PyObject* value, void* closure);
    static PyObject* get_fill_color(PyUIGridViewObject* self, void* closure);
    static int set_fill_color(PyUIGridViewObject* self, PyObject* value, void* closure);
    static PyObject* get_texture(PyUIGridViewObject* self, void* closure);

    static PyMethodDef methods[];
    static PyGetSetDef getsetters[];
};

// Forward declaration of methods array
extern PyMethodDef UIGridView_all_methods[];

namespace mcrfpydef {
    inline PyTypeObject PyUIGridViewType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
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
            obj->data.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)UIGridView::repr,
        .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC,
        .tp_doc = PyDoc_STR(
            "GridView(grid=None, pos=None, size=None, **kwargs)\n\n"
            "A rendering view for a Grid's data. Multiple GridViews can display\n"
            "the same Grid with different camera positions, zoom levels, etc.\n\n"
            "Args:\n"
            "    grid (Grid): The Grid to render. Required.\n"
            "    pos (tuple): Position as (x, y). Default: (0, 0)\n"
            "    size (tuple): Size as (w, h). Default: (256, 256)\n\n"
            "Keyword Args:\n"
            "    zoom (float): Zoom level. Default: 1.0\n"
            "    center (tuple): Camera center (x, y) in pixels. Default: grid center\n"
            "    fill_color (Color): Background color. Default: dark gray\n"),
        .tp_traverse = [](PyObject* self, visitproc visit, void* arg) -> int {
            return 0;
        },
        .tp_clear = [](PyObject* self) -> int {
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
