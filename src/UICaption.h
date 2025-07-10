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

    static PyObject* get_float_member(PyUICaptionObject* self, void* closure);
    static int set_float_member(PyUICaptionObject* self, PyObject* value, void* closure);
    static PyObject* get_vec_member(PyUICaptionObject* self, void* closure);
    static int set_vec_member(PyUICaptionObject* self, PyObject* value, void* closure);
    static PyObject* get_color_member(PyUICaptionObject* self, void* closure);
    static int set_color_member(PyUICaptionObject* self, PyObject* value, void* closure);
    static PyObject* get_text(PyUICaptionObject* self, void* closure);
    static int set_text(PyUICaptionObject* self, PyObject* value, void* closure);
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
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("Caption(text='', x=0, y=0, font=None, fill_color=None, outline_color=None, outline=0, click=None)\n\n"
                            "A text display UI element with customizable font and styling.\n\n"
                            "Args:\n"
                            "    text (str): The text content to display. Default: ''\n"
                            "    x (float): X position in pixels. Default: 0\n"
                            "    y (float): Y position in pixels. Default: 0\n"
                            "    font (Font): Font object for text rendering. Default: engine default font\n"
                            "    fill_color (Color): Text fill color. Default: (255, 255, 255, 255)\n"
                            "    outline_color (Color): Text outline color. Default: (0, 0, 0, 255)\n"
                            "    outline (float): Text outline thickness. Default: 0\n"
                            "    click (callable): Click event handler. Default: None\n\n"
                            "Attributes:\n"
                            "    text (str): The displayed text content\n"
                            "    x, y (float): Position in pixels\n"
                            "    font (Font): Font used for rendering\n"
                            "    fill_color, outline_color (Color): Text appearance\n"
                            "    outline (float): Outline thickness\n"
                            "    click (callable): Click event handler\n"
                            "    visible (bool): Visibility state\n"
                            "    z_index (int): Rendering order\n"
                            "    w, h (float): Read-only computed size based on text and font"),
        .tp_methods = UICaption_methods,
        //.tp_members = PyUIFrame_members,
        .tp_getset = UICaption::getsetters,
        .tp_base = &mcrfpydef::PyDrawableType,
        .tp_init = (initproc)UICaption::init,
        // TODO - move tp_new to .cpp file as a static function (UICaption::new)
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            PyUICaptionObject* self = (PyUICaptionObject*)type->tp_alloc(type, 0);
            if (self) self->data = std::make_shared<UICaption>();
            return (PyObject*)self;
        }
    };
}
