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
        .tp_doc = PyDoc_STR("Sprite(x=0, y=0, texture=None, sprite_index=0, scale=1.0, click=None)\n\n"
                            "A sprite UI element that displays a texture or portion of a texture atlas.\n\n"
                            "Args:\n"
                            "    x (float): X position in pixels. Default: 0\n"
                            "    y (float): Y position in pixels. Default: 0\n"
                            "    texture (Texture): Texture object to display. Default: None\n"
                            "    sprite_index (int): Index into texture atlas (if applicable). Default: 0\n"
                            "    scale (float): Sprite scaling factor. Default: 1.0\n"
                            "    click (callable): Click event handler. Default: None\n\n"
                            "Attributes:\n"
                            "    x, y (float): Position in pixels\n"
                            "    texture (Texture): The texture being displayed\n"
                            "    sprite_index (int): Current sprite index in texture atlas\n"
                            "    scale (float): Scale multiplier\n"
                            "    click (callable): Click event handler\n"
                            "    visible (bool): Visibility state\n"
                            "    z_index (int): Rendering order\n"
                            "    w, h (float): Read-only computed size based on texture and scale"),
        .tp_methods = UISprite_methods,
        //.tp_members = PyUIFrame_members,
        .tp_getset = UISprite::getsetters,
        .tp_base = &mcrfpydef::PyDrawableType,
        .tp_init = (initproc)UISprite::init,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            PyUISpriteObject* self = (PyUISpriteObject*)type->tp_alloc(type, 0);
            //if (self) self->data = std::make_shared<UICaption>();
            return (PyObject*)self;
        }
    }; 
}
