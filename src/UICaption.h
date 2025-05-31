#pragma once
#include "Common.h"
#include "Python.h"
#include "UIDrawable.h"

class UICaption: public UIDrawable
{
public:
    sf::Text text;
    void render(sf::Vector2f, sf::RenderTarget&) override final;
    PyObjectsEnum derived_type() override final;
    virtual UIDrawable* click_at(sf::Vector2f point) override final;

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
        .tp_doc = PyDoc_STR("docstring"),
        //.tp_methods = PyUIFrame_methods,
        //.tp_members = PyUIFrame_members,
        .tp_getset = UICaption::getsetters,
        //.tp_base = NULL,
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
