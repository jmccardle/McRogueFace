#pragma once
#include "Common.h"
#include "Python.h"
#include "structmember.h"
#include "IndexTexture.h"
#include "Resources.h"
#include <list>

#include "PyCallable.h"
#include "PyTexture.h"
#include "PyColor.h"
#include "PyVector.h"
#include "PyFont.h"
#include "UIDrawable.h"
#include "UIBase.h"

class UISprite: public UIDrawable
{
private:
    int sprite_index;
    sf::Sprite sprite;
protected:
    std::shared_ptr<PyTexture> ptex;
public:
    UISprite();
    UISprite(std::shared_ptr<PyTexture>, int, sf::Vector2f, float);
    void update();
    void render(sf::Vector2f) override final;
    virtual UIDrawable* click_at(sf::Vector2f point) override final;
    
    void render(sf::Vector2f, sf::RenderTexture&);

    void setPosition(sf::Vector2f);
    sf::Vector2f getPosition();
    void setScale(sf::Vector2f);
    sf::Vector2f getScale();
    void setSpriteIndex(int);
    int getSpriteIndex();

    void setTexture(std::shared_ptr<PyTexture> _ptex, int _sprite_index=-1);
    std::shared_ptr<PyTexture> getTexture();

    PyObjectsEnum derived_type() override final;


    static PyObject* get_float_member(PyUISpriteObject* self, void* closure);
    static int set_float_member(PyUISpriteObject* self, PyObject* value, void* closure);
    static PyObject* get_int_member(PyUISpriteObject* self, void* closure);
    static int set_int_member(PyUISpriteObject* self, PyObject* value, void* closure);
    static PyObject* get_texture(PyUISpriteObject* self, void* closure);
    static int set_texture(PyUISpriteObject* self, PyObject* value, void* closure);
    static PyGetSetDef getsetters[];
    static PyObject* repr(PyUISpriteObject* self);
    static int init(PyUISpriteObject* self, PyObject* args, PyObject* kwds);
    
};

namespace mcrfpydef {
    static PyTypeObject PyUISpriteType = {
        //PyVarObject_HEAD_INIT(NULL, 0)
        .tp_name = "mcrfpy.Sprite",
        .tp_basicsize = sizeof(PyUISpriteObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)[](PyObject* self)
        {
            PyUISpriteObject* obj = (PyUISpriteObject*)self;
            // release reference to font object
            //if (obj->texture) Py_DECREF(obj->texture);
            obj->data.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)UISprite::repr,
        //.tp_hash = NULL,
        //.tp_iter
        //.tp_iternext
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("docstring"),
        //.tp_methods = PyUIFrame_methods,
        //.tp_members = PyUIFrame_members,
        .tp_getset = UISprite::getsetters,
        //.tp_base = NULL,
        .tp_init = (initproc)UISprite::init,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            PyUISpriteObject* self = (PyUISpriteObject*)type->tp_alloc(type, 0);
            //if (self) self->data = std::make_shared<UICaption>();
            return (PyObject*)self;
        }
    }; 
}
