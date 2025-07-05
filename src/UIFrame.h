#pragma once
#include "Common.h"
#include "Python.h"
#include "structmember.h"
#include "IndexTexture.h"
#include "Resources.h"
#include <list>

#include "PyCallable.h"
#include "PyColor.h"
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
    void render(sf::Vector2f, sf::RenderTarget&) override final;
    void move(sf::Vector2f);
    PyObjectsEnum derived_type() override final;
    virtual UIDrawable* click_at(sf::Vector2f point) override final;

    static PyObject* get_children(PyUIFrameObject* self, void* closure);

    static PyObject* get_float_member(PyUIFrameObject* self, void* closure);
    static int set_float_member(PyUIFrameObject* self, PyObject* value, void* closure);
    static PyObject* get_color_member(PyUIFrameObject* self, void* closure);
    static int set_color_member(PyUIFrameObject* self, PyObject* value, void* closure);
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
        .tp_doc = PyDoc_STR("docstring"),
        //.tp_methods = PyUIFrame_methods,
        //.tp_members = PyUIFrame_members,
        .tp_getset = UIFrame::getsetters,
        //.tp_base = NULL,
        .tp_init = (initproc)UIFrame::init,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            PyUIFrameObject* self = (PyUIFrameObject*)type->tp_alloc(type, 0);
            if (self) self->data = std::make_shared<UIFrame>();
            return (PyObject*)self;
        }
    };
}
