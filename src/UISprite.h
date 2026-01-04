#pragma once
#include "Common.h"
#include "Python.h"
#include "structmember.h"
#include "IndexTexture.h"
#include "Resources.h"
#include <list>

#include "PyCallable.h"
#include "PyTexture.h"
#include "PyDrawable.h"
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
    
    // Copy constructor and assignment operator
    UISprite(const UISprite& other);
    UISprite& operator=(const UISprite& other);
    
    // Move constructor and assignment operator  
    UISprite(UISprite&& other) noexcept;
    UISprite& operator=(UISprite&& other) noexcept;
    void update();
    void render(sf::Vector2f, sf::RenderTarget&) override final;
    virtual UIDrawable* click_at(sf::Vector2f point) override final;
    
    //void render(sf::Vector2f, sf::RenderTexture&);

    void setPosition(sf::Vector2f);
    sf::Vector2f getPosition();
    void setScale(sf::Vector2f);
    sf::Vector2f getScale() const;
    void setSpriteIndex(int);
    int getSpriteIndex();

    void setTexture(std::shared_ptr<PyTexture> _ptex, int _sprite_index=-1);
    std::shared_ptr<PyTexture> getTexture();

    PyObjectsEnum derived_type() override final;
    
    // Phase 1 virtual method implementations
    sf::FloatRect get_bounds() const override;
    void move(float dx, float dy) override;
    void resize(float w, float h) override;
    void onPositionChanged() override;
    
    // Property system for animations
    bool setProperty(const std::string& name, float value) override;
    bool setProperty(const std::string& name, int value) override;
    bool getProperty(const std::string& name, float& value) const override;
    bool getProperty(const std::string& name, int& value) const override;

    bool hasProperty(const std::string& name) const override;

    static PyObject* get_float_member(PyUISpriteObject* self, void* closure);
    static int set_float_member(PyUISpriteObject* self, PyObject* value, void* closure);
    static PyObject* get_int_member(PyUISpriteObject* self, void* closure);
    static int set_int_member(PyUISpriteObject* self, PyObject* value, void* closure);
    static PyObject* get_texture(PyUISpriteObject* self, void* closure);
    static int set_texture(PyUISpriteObject* self, PyObject* value, void* closure);
    static PyObject* get_pos(PyUISpriteObject* self, void* closure);
    static int set_pos(PyUISpriteObject* self, PyObject* value, void* closure);
    static PyGetSetDef getsetters[];
    static PyObject* repr(PyUISpriteObject* self);
    static int init(PyUISpriteObject* self, PyObject* args, PyObject* kwds);
    
};

// Forward declaration of methods array
extern PyMethodDef UISprite_methods[];

namespace mcrfpydef {
    static PyTypeObject PyUISpriteType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Sprite",
        .tp_basicsize = sizeof(PyUISpriteObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)[](PyObject* self)
        {
            PyUISpriteObject* obj = (PyUISpriteObject*)self;
            // Clear weak references
            if (obj->weakreflist != NULL) {
                PyObject_ClearWeakRefs(self);
            }
            // release reference to font object
            //if (obj->texture) Py_DECREF(obj->texture);
            obj->data.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)UISprite::repr,
        //.tp_hash = NULL,
        //.tp_iter
        //.tp_iternext
        .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
        .tp_doc = PyDoc_STR("Sprite(pos=None, texture=None, sprite_index=0, **kwargs)\n\n"
                            "A sprite UI element that displays a texture or portion of a texture atlas.\n\n"
                            "Args:\n"
                            "    pos (tuple, optional): Position as (x, y) tuple. Default: (0, 0)\n"
                            "    texture (Texture, optional): Texture object to display. Default: default texture\n"
                            "    sprite_index (int, optional): Index into texture atlas. Default: 0\n\n"
                            "Keyword Args:\n"
                            "    scale (float): Uniform scale factor. Default: 1.0\n"
                            "    scale_x (float): Horizontal scale factor. Default: 1.0\n"
                            "    scale_y (float): Vertical scale factor. Default: 1.0\n"
                            "    click (callable): Click event handler. Default: None\n"
                            "    visible (bool): Visibility state. Default: True\n"
                            "    opacity (float): Opacity (0.0-1.0). Default: 1.0\n"
                            "    z_index (int): Rendering order. Default: 0\n"
                            "    name (str): Element name for finding. Default: None\n"
                            "    x (float): X position override. Default: 0\n"
                            "    y (float): Y position override. Default: 0\n\n"
                            "Attributes:\n"
                            "    x, y (float): Position in pixels\n"
                            "    pos (Vector): Position as a Vector object\n"
                            "    texture (Texture): The texture being displayed\n"
                            "    sprite_index (int): Current sprite index in texture atlas\n"
                            "    scale (float): Uniform scale factor\n"
                            "    scale_x, scale_y (float): Individual scale factors\n"
                            "    click (callable): Click event handler\n"
                            "    visible (bool): Visibility state\n"
                            "    opacity (float): Opacity value\n"
                            "    z_index (int): Rendering order\n"
                            "    name (str): Element name\n"
                            "    w, h (float): Read-only computed size based on texture and scale"),
        .tp_methods = UISprite_methods,
        //.tp_members = PyUIFrame_members,
        .tp_getset = UISprite::getsetters,
        .tp_base = &mcrfpydef::PyDrawableType,
        .tp_init = (initproc)UISprite::init,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            PyUISpriteObject* self = (PyUISpriteObject*)type->tp_alloc(type, 0);
            if (self) {
                self->data = std::make_shared<UISprite>();
                self->weakreflist = nullptr;
            }
            return (PyObject*)self;
        }
    }; 
}
