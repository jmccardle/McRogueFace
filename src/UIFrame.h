#pragma once
#include "Common.h"
#include "Python.h"
#include "structmember.h"
#include "IndexTexture.h"
#include "Resources.h"
#include <list>

#include "PyCallable.h"
#include "PyColor.h"
#include "PyDrawable.h"
#include "PyVector.h"
#include "UIDrawable.h"
#include "UIBase.h"

//class UIFrame;
//
//typedef struct {
//    PyObject_HEAD
//    std::shared_ptr<UIFrame> data;
//} PyUIFrameObject;

class UIFrame: public UIDrawable
{
public:
    UIFrame(float, float, float, float);
    UIFrame();
    ~UIFrame();
    sf::RectangleShape box;
    float outline;
    std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>> children;
    bool children_need_sort = true;  // Dirty flag for z_index sorting optimization
    bool clip_children = false;  // Whether to clip children to frame bounds
    bool cache_subtree = false;  // #144: Whether to cache subtree rendering to texture

    void render(sf::Vector2f, sf::RenderTarget&) override final;
    void move(sf::Vector2f);
    PyObjectsEnum derived_type() override final;
    virtual UIDrawable* click_at(sf::Vector2f point) override final;
    
    // Phase 1 virtual method implementations
    sf::FloatRect get_bounds() const override;
    void move(float dx, float dy) override;
    void resize(float w, float h) override;
    void onPositionChanged() override;

    static PyObject* get_children(PyUIFrameObject* self, void* closure);

    static PyObject* get_float_member(PyUIFrameObject* self, void* closure);
    static int set_float_member(PyUIFrameObject* self, PyObject* value, void* closure);
    static PyObject* get_color_member(PyUIFrameObject* self, void* closure);
    static int set_color_member(PyUIFrameObject* self, PyObject* value, void* closure);
    static PyObject* get_pos(PyUIFrameObject* self, void* closure);
    static int set_pos(PyUIFrameObject* self, PyObject* value, void* closure);
    static PyObject* get_clip_children(PyUIFrameObject* self, void* closure);
    static int set_clip_children(PyUIFrameObject* self, PyObject* value, void* closure);
    static PyObject* get_cache_subtree(PyUIFrameObject* self, void* closure);
    static int set_cache_subtree(PyUIFrameObject* self, PyObject* value, void* closure);
    static PyGetSetDef getsetters[];
    static PyObject* repr(PyUIFrameObject* self);
    static int init(PyUIFrameObject* self, PyObject* args, PyObject* kwds);
    
    // Animation property system
    bool setProperty(const std::string& name, float value) override;
    bool setProperty(const std::string& name, const sf::Color& value) override;
    bool setProperty(const std::string& name, const sf::Vector2f& value) override;
    
    bool getProperty(const std::string& name, float& value) const override;
    bool getProperty(const std::string& name, sf::Color& value) const override;
    bool getProperty(const std::string& name, sf::Vector2f& value) const override;

    bool hasProperty(const std::string& name) const override;
};

// Forward declaration of methods array
extern PyMethodDef UIFrame_methods[];

namespace mcrfpydef {
    inline PyTypeObject PyUIFrameType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Frame",
        .tp_basicsize = sizeof(PyUIFrameObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)[](PyObject* self)
        {
            PyUIFrameObject* obj = (PyUIFrameObject*)self;
            // Untrack from GC before destroying
            PyObject_GC_UnTrack(self);
            // Clear weak references
            if (obj->weakreflist != NULL) {
                PyObject_ClearWeakRefs(self);
            }
            // Only unregister callbacks if we're the last owner of the
            // C++ object. If other shared_ptr owners exist (e.g. parent's
            // children vector), the callbacks must survive. (#251)
            if (obj->data && obj->data.use_count() <= 1) {
                obj->data->click_unregister();
                obj->data->on_enter_unregister();
                obj->data->on_exit_unregister();
                obj->data->on_move_unregister();
            }
            obj->data.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)UIFrame::repr,
        //.tp_hash = NULL,
        //.tp_iter
        //.tp_iternext
        .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC,
        .tp_doc = PyDoc_STR("Frame(pos=None, size=None, **kwargs)\n\n"
                            "A rectangular frame UI element that can contain other drawable elements.\n\n"
                            "Args:\n"
                            "    pos (tuple, optional): Position as (x, y) tuple. Default: (0, 0)\n"
                            "    size (tuple, optional): Size as (width, height) tuple. Default: (0, 0)\n\n"
                            "Keyword Args:\n"
                            "    fill_color (Color): Background fill color. Default: (0, 0, 0, 128)\n"
                            "    outline_color (Color): Border outline color. Default: (255, 255, 255, 255)\n"
                            "    outline (float): Border outline thickness. Default: 0\n"
                            "    click (callable): Click event handler. Default: None\n"
                            "    children (list): Initial list of child drawable elements. Default: None\n"
                            "    visible (bool): Visibility state. Default: True\n"
                            "    opacity (float): Opacity (0.0-1.0). Default: 1.0\n"
                            "    z_index (int): Rendering order. Default: 0\n"
                            "    name (str): Element name for finding. Default: None\n"
                            "    x (float): X position override. Default: 0\n"
                            "    y (float): Y position override. Default: 0\n"
                            "    w (float): Width override. Default: 0\n"
                            "    h (float): Height override. Default: 0\n"
                            "    clip_children (bool): Whether to clip children to frame bounds. Default: False\n"
                            "    cache_subtree (bool): Cache rendering to texture for performance. Default: False\n"
                            "    align (Alignment): Alignment relative to parent. Default: None (manual positioning)\n"
                            "    margin (float): Margin from parent edge when aligned. Default: 0\n"
                            "    horiz_margin (float): Horizontal margin override. Default: 0 (use margin)\n"
                            "    vert_margin (float): Vertical margin override. Default: 0 (use margin)\n\n"
                            "Attributes:\n"
                            "    x, y (float): Position in pixels\n"
                            "    w, h (float): Size in pixels\n"
                            "    pos (Vector): Position as a Vector object\n"
                            "    fill_color, outline_color (Color): Visual appearance\n"
                            "    outline (float): Border thickness\n"
                            "    click (callable): Click event handler\n"
                            "    children (list): Collection of child drawable elements\n"
                            "    visible (bool): Visibility state\n"
                            "    opacity (float): Opacity value\n"
                            "    z_index (int): Rendering order\n"
                            "    name (str): Element name\n"
                            "    clip_children (bool): Whether to clip children to frame bounds\n"
                            "    cache_subtree (bool): Cache subtree rendering to texture\n"
                            "    align (Alignment): Alignment relative to parent (or None)\n"
                            "    margin (float): General margin for alignment\n"
                            "    horiz_margin (float): Horizontal margin override\n"
                            "    vert_margin (float): Vertical margin override"),
        // tp_traverse visits Python object references for GC cycle detection
        .tp_traverse = [](PyObject* self, visitproc visit, void* arg) -> int {
            PyUIFrameObject* obj = (PyUIFrameObject*)self;
            if (obj->data) {
                // Visit callback references
                if (obj->data->click_callable) {
                    PyObject* callback = obj->data->click_callable->borrow();
                    if (callback && callback != Py_None) {
                        Py_VISIT(callback);
                    }
                }
                if (obj->data->on_enter_callable) {
                    PyObject* callback = obj->data->on_enter_callable->borrow();
                    if (callback && callback != Py_None) {
                        Py_VISIT(callback);
                    }
                }
                if (obj->data->on_exit_callable) {
                    PyObject* callback = obj->data->on_exit_callable->borrow();
                    if (callback && callback != Py_None) {
                        Py_VISIT(callback);
                    }
                }
                if (obj->data->on_move_callable) {
                    PyObject* callback = obj->data->on_move_callable->borrow();
                    if (callback && callback != Py_None) {
                        Py_VISIT(callback);
                    }
                }
            }
            return 0;
        },
        // tp_clear breaks reference cycles by clearing Python references
        .tp_clear = [](PyObject* self) -> int {
            PyUIFrameObject* obj = (PyUIFrameObject*)self;
            if (obj->data) {
                obj->data->click_unregister();
                obj->data->on_enter_unregister();
                obj->data->on_exit_unregister();
                obj->data->on_move_unregister();
            }
            return 0;
        },
        .tp_methods = UIFrame_methods,
        //.tp_members = PyUIFrame_members,
        .tp_getset = UIFrame::getsetters,
        .tp_base = &mcrfpydef::PyDrawableType,
        .tp_init = (initproc)UIFrame::init,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            PyUIFrameObject* self = (PyUIFrameObject*)type->tp_alloc(type, 0);
            if (self) {
                self->data = std::make_shared<UIFrame>();
                self->weakreflist = nullptr;
                // Note: For GC types, tracking happens automatically via tp_alloc
                // when Py_TPFLAGS_HAVE_GC is set. Do NOT call PyObject_GC_Track here
                // as it would double-track and cause corruption.
            }
            return (PyObject*)self;
        }
    };
}
