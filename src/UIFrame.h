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
};

// Forward declaration of methods array
extern PyMethodDef UIFrame_methods[];

namespace mcrfpydef {
    static PyTypeObject PyUIFrameType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Frame",
        .tp_basicsize = sizeof(PyUIFrameObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)[](PyObject* self)
        {
            PyUIFrameObject* obj = (PyUIFrameObject*)self;
            obj->data.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)UIFrame::repr,
        //.tp_hash = NULL,
        //.tp_iter
        //.tp_iternext
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("Frame(x=0, y=0, w=0, h=0, fill_color=None, outline_color=None, outline=0, click=None, children=None)\n\n"
                            "A rectangular frame UI element that can contain other drawable elements.\n\n"
                            "Args:\n"
                            "    x (float): X position in pixels. Default: 0\n"
                            "    y (float): Y position in pixels. Default: 0\n"
                            "    w (float): Width in pixels. Default: 0\n"
                            "    h (float): Height in pixels. Default: 0\n"
                            "    fill_color (Color): Background fill color. Default: (0, 0, 0, 128)\n"
                            "    outline_color (Color): Border outline color. Default: (255, 255, 255, 255)\n"
                            "    outline (float): Border outline thickness. Default: 0\n"
                            "    click (callable): Click event handler. Default: None\n"
                            "    children (list): Initial list of child drawable elements. Default: None\n\n"
                            "Attributes:\n"
                            "    x, y (float): Position in pixels\n"
                            "    w, h (float): Size in pixels\n"
                            "    fill_color, outline_color (Color): Visual appearance\n"
                            "    outline (float): Border thickness\n"
                            "    click (callable): Click event handler\n"
                            "    children (list): Collection of child drawable elements\n"
                            "    visible (bool): Visibility state\n"
                            "    z_index (int): Rendering order\n"
                            "    clip_children (bool): Whether to clip children to frame bounds"),
        .tp_methods = UIFrame_methods,
        //.tp_members = PyUIFrame_members,
        .tp_getset = UIFrame::getsetters,
        .tp_base = &mcrfpydef::PyDrawableType,
        .tp_init = (initproc)UIFrame::init,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            PyUIFrameObject* self = (PyUIFrameObject*)type->tp_alloc(type, 0);
            if (self) self->data = std::make_shared<UIFrame>();
            return (PyObject*)self;
        }
    };
}
