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
};

//typedef struct {
//    PyObject_HEAD
//    std::shared_ptr<UISprite> data;
//} PyUISpriteObject;

namespace mcrfpydef {
    //TODO: add this method to class scope; move implementation to .cpp file
    static PyObject* PyUISprite_get_float_member(PyUISpriteObject* self, void* closure)
    {
        auto member_ptr = reinterpret_cast<long>(closure);
        if (member_ptr == 0)
            return PyFloat_FromDouble(self->data->getPosition().x);
        else if (member_ptr == 1)
            return PyFloat_FromDouble(self->data->getPosition().y);
        else if (member_ptr == 2)
            return PyFloat_FromDouble(self->data->getScale().x); // scale X and Y are identical, presently
        else
        {
            PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
            return nullptr;
        }
    }

    //TODO: add this method to class scope; move implementation to .cpp file
    static int PyUISprite_set_float_member(PyUISpriteObject* self, PyObject* value, void* closure)
    {
        float val;
        auto member_ptr = reinterpret_cast<long>(closure);
        if (PyFloat_Check(value))
        {
            val = PyFloat_AsDouble(value);
        }
        else if (PyLong_Check(value))
        {
            val = PyLong_AsLong(value);
        }
        else
        {
            PyErr_SetString(PyExc_TypeError, "Value must be a floating point number.");
            return -1;
        }
        if (member_ptr == 0) //x
            self->data->setPosition(sf::Vector2f(val, self->data->getPosition().y));
        else if (member_ptr == 1) //y
            self->data->setPosition(sf::Vector2f(self->data->getPosition().x, val));
        else if (member_ptr == 2) // scale
            self->data->setScale(sf::Vector2f(val, val));
        return 0;
    }
    
    //TODO: add this method to class scope; move implementation to .cpp file
    static PyObject* PyUISprite_get_int_member(PyUISpriteObject* self, void* closure)
    {
        auto member_ptr = reinterpret_cast<long>(closure);
        if (true) {}
        else
        {
            PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
            return nullptr;
        }
        
        return PyLong_FromDouble(self->data->getSpriteIndex());
    }

    //TODO: add this method to class scope; move implementation to .cpp file
    static int PyUISprite_set_int_member(PyUISpriteObject* self, PyObject* value, void* closure)
    {
        int val;
        auto member_ptr = reinterpret_cast<long>(closure);
        if (PyLong_Check(value))
        {
            val = PyLong_AsLong(value);
        }
        else
        {
            PyErr_SetString(PyExc_TypeError, "Value must be an integer.");
            return -1;
        }
        self->data->setSpriteIndex(val);
        return 0;
    }
    
    //TODO: add this method to class scope; move implementation to .cpp file
    static PyObject* PyUISprite_get_texture(PyUISpriteObject* self, void* closure)
    {
        return self->data->getTexture()->pyObject();
    }
    
    //TODO: add this method to class scope; move implementation to .cpp file
    static int PyUISprite_set_texture(PyUISpriteObject* self, PyObject* value, void* closure)
    {
        return -1;
    }

    //TODO: add this method to static array scope; move implementation to .cpp file
    static PyGetSetDef PyUISprite_getsetters[] = {
        {"x", (getter)PyUISprite_get_float_member, (setter)PyUISprite_set_float_member, "X coordinate of top-left corner",   (void*)0},
        {"y", (getter)PyUISprite_get_float_member, (setter)PyUISprite_set_float_member, "Y coordinate of top-left corner",   (void*)1},
        {"scale", (getter)PyUISprite_get_float_member, (setter)PyUISprite_set_float_member, "Size factor",                   (void*)2},
        {"sprite_number", (getter)PyUISprite_get_int_member, (setter)PyUISprite_set_int_member, "Which sprite on the texture is shown", NULL},
        {"texture", (getter)PyUISprite_get_texture, (setter)PyUISprite_set_texture,     "Texture object",                    NULL},
        {"click", (getter)UIDrawable::get_click, (setter)UIDrawable::set_click, "Object called with (x, y, button) when clicked", (void*)PyObjectsEnum::UISPRITE},
        {NULL}
    };
    
    //TODO: add this method to class scope; move implementation to .cpp file
    static PyObject* PyUISprite_repr(PyUISpriteObject* self)
    {
        std::ostringstream ss;
        if (!self->data) ss << "<Sprite (invalid internal object)>";
        else {
            //auto sprite = self->data->sprite;
            ss << "<Sprite (x=" << self->data->getPosition().x << ", y=" << self->data->getPosition().y << ", " <<
                "scale=" << self->data->getScale().x << ", " <<
                "sprite_number=" << self->data->getSpriteIndex() << ")>";
        }
        std::string repr_str = ss.str();
        return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
    }

    //TODO: add this method to class scope; move implementation to .cpp file
    static int PyUISprite_init(PyUISpriteObject* self, PyObject* args, PyObject* kwds)
    {
        //std::cout << "Init called\n";
        static const char* keywords[] = { "x", "y", "texture", "sprite_index", "scale", nullptr };
        float x = 0.0f, y = 0.0f, scale = 1.0f;
        int sprite_index;
        PyObject* texture;

        if (!PyArg_ParseTupleAndKeywords(args, kwds, "|ffOif",
            const_cast<char**>(keywords), &x, &y, &texture, &sprite_index, &scale))
        {
            return -1;
        }

        // check types for texture
        if (texture != NULL && !PyObject_IsInstance(texture, (PyObject*)&PyTextureType)){
            PyErr_SetString(PyExc_TypeError, "texture must be a mcrfpy.Texture instance");
            return -1;
        }
        auto pytexture = (PyTextureObject*)texture;
        self->data = std::make_shared<UISprite>(pytexture->data, sprite_index, sf::Vector2f(x, y), scale);
        self->data->setPosition(sf::Vector2f(x, y));

        return 0;
    }
    
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
        .tp_repr = (reprfunc)PyUISprite_repr,
        //.tp_hash = NULL,
        //.tp_iter
        //.tp_iternext
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("docstring"),
        //.tp_methods = PyUIFrame_methods,
        //.tp_members = PyUIFrame_members,
        .tp_getset = PyUISprite_getsetters,
        //.tp_base = NULL,
        .tp_init = (initproc)PyUISprite_init,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            PyUISpriteObject* self = (PyUISpriteObject*)type->tp_alloc(type, 0);
            //if (self) self->data = std::make_shared<UICaption>();
            return (PyObject*)self;
        }
    }; 
}
