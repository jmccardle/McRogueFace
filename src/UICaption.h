#pragma once
#include "Common.h"
#include "Python.h"
#include "UIDrawable.h"
#include "PyDrawable.h"

class UICaption: public UIDrawable
{
public:
    sf::Text text;
    UICaption(); // Default constructor with safe initialization
    void render(sf::Vector2f, sf::RenderTarget&) override final;
    PyObjectsEnum derived_type() override final;
    virtual UIDrawable* click_at(sf::Vector2f point) override final;
    
    // Phase 1 virtual method implementations
    sf::FloatRect get_bounds() const override;
    void move(float dx, float dy) override;
    void resize(float w, float h) override;
    void onPositionChanged() override;
    
    // Property system for animations
    bool setProperty(const std::string& name, float value) override;
    bool setProperty(const std::string& name, const sf::Color& value) override;
    bool setProperty(const std::string& name, const std::string& value) override;
    
    bool getProperty(const std::string& name, float& value) const override;
    bool getProperty(const std::string& name, sf::Color& value) const override;
    bool getProperty(const std::string& name, std::string& value) const override;

    bool hasProperty(const std::string& name) const override;

    static PyObject* get_float_member(PyUICaptionObject* self, void* closure);
    static int set_float_member(PyUICaptionObject* self, PyObject* value, void* closure);
    static PyObject* get_vec_member(PyUICaptionObject* self, void* closure);
    static int set_vec_member(PyUICaptionObject* self, PyObject* value, void* closure);
    static PyObject* get_color_member(PyUICaptionObject* self, void* closure);
    static int set_color_member(PyUICaptionObject* self, PyObject* value, void* closure);
    static PyObject* get_text(PyUICaptionObject* self, void* closure);
    static int set_text(PyUICaptionObject* self, PyObject* value, void* closure);
    static PyObject* get_size(PyUICaptionObject* self, void* closure);
    static PyObject* get_w(PyUICaptionObject* self, void* closure);
    static PyObject* get_h(PyUICaptionObject* self, void* closure);
    static PyGetSetDef getsetters[];
    static PyObject* repr(PyUICaptionObject* self);
    static int init(PyUICaptionObject* self, PyObject* args, PyObject* kwds);

};

extern PyMethodDef UICaption_methods[];

namespace mcrfpydef {
    static PyTypeObject PyUICaptionType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Caption",
        .tp_basicsize = sizeof(PyUICaptionObject),
        .tp_itemsize = 0,
        // TODO - move tp_dealloc to .cpp file as static function (UICaption::dealloc)
        .tp_dealloc = (destructor)[](PyObject* self)
        {
            PyUICaptionObject* obj = (PyUICaptionObject*)self;
            // Clear weak references
            if (obj->weakreflist != NULL) {
                PyObject_ClearWeakRefs(self);
            }
            // TODO - reevaluate with PyFont usage; UICaption does not own the font
            // release reference to font object
            if (obj->font) Py_DECREF(obj->font);
            obj->data.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)UICaption::repr,
        //.tp_hash = NULL,
        //.tp_iter
        //.tp_iternext
        .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
        .tp_doc = PyDoc_STR("Caption(pos=None, font=None, text='', **kwargs)\n\n"
                            "A text display UI element with customizable font and styling.\n\n"
                            "Args:\n"
                            "    pos (tuple, optional): Position as (x, y) tuple. Default: (0, 0)\n"
                            "    font (Font, optional): Font object for text rendering. Default: engine default font\n"
                            "    text (str, optional): The text content to display. Default: ''\n\n"
                            "Keyword Args:\n"
                            "    fill_color (Color): Text fill color. Default: (255, 255, 255, 255)\n"
                            "    outline_color (Color): Text outline color. Default: (0, 0, 0, 255)\n"
                            "    outline (float): Text outline thickness. Default: 0\n"
                            "    font_size (float): Font size in points. Default: 16\n"
                            "    click (callable): Click event handler. Default: None\n"
                            "    visible (bool): Visibility state. Default: True\n"
                            "    opacity (float): Opacity (0.0-1.0). Default: 1.0\n"
                            "    z_index (int): Rendering order. Default: 0\n"
                            "    name (str): Element name for finding. Default: None\n"
                            "    x (float): X position override. Default: 0\n"
                            "    y (float): Y position override. Default: 0\n"
                            "    align (Alignment): Alignment relative to parent. Default: None\n"
                            "    margin (float): Margin from parent edge when aligned. Default: 0\n"
                            "    horiz_margin (float): Horizontal margin override. Default: 0 (use margin)\n"
                            "    vert_margin (float): Vertical margin override. Default: 0 (use margin)\n\n"
                            "Attributes:\n"
                            "    text (str): The displayed text content\n"
                            "    x, y (float): Position in pixels\n"
                            "    pos (Vector): Position as a Vector object\n"
                            "    font (Font): Font used for rendering\n"
                            "    font_size (float): Font size in points\n"
                            "    fill_color, outline_color (Color): Text appearance\n"
                            "    outline (float): Outline thickness\n"
                            "    click (callable): Click event handler\n"
                            "    visible (bool): Visibility state\n"
                            "    opacity (float): Opacity value\n"
                            "    z_index (int): Rendering order\n"
                            "    name (str): Element name\n"
                            "    w, h (float): Read-only computed size based on text and font\n"
                            "    align (Alignment): Alignment relative to parent (or None)\n"
                            "    margin (float): General margin for alignment\n"
                            "    horiz_margin (float): Horizontal margin override\n"
                            "    vert_margin (float): Vertical margin override"),
        .tp_methods = UICaption_methods,
        //.tp_members = PyUIFrame_members,
        .tp_getset = UICaption::getsetters,
        .tp_base = &mcrfpydef::PyDrawableType,
        .tp_init = (initproc)UICaption::init,
        // TODO - move tp_new to .cpp file as a static function (UICaption::new)
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            PyUICaptionObject* self = (PyUICaptionObject*)type->tp_alloc(type, 0);
            if (self) {
                self->data = std::make_shared<UICaption>();
                self->font = nullptr;
                self->weakreflist = nullptr;
            }
            return (PyObject*)self;
        }
    };
}
