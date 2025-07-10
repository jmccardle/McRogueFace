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

#include "UIGridPoint.h"
#include "UIDrawable.h"
#include "UIBase.h"
#include "UISprite.h"

class UIGrid;

//class UIEntity;
//typedef struct {
//    PyObject_HEAD
//    std::shared_ptr<UIEntity> data;
//} PyUIEntityObject;

// helper methods with no namespace requirement
PyObject* sfVector2f_to_PyObject(sf::Vector2f vector);
sf::Vector2f PyObject_to_sfVector2f(PyObject* obj);
PyObject* UIGridPointState_to_PyObject(const UIGridPointState& state);
PyObject* UIGridPointStateVector_to_PyList(const std::vector<UIGridPointState>& vec);

// TODO: make UIEntity a drawable
class UIEntity//: public UIDrawable
{
public:
    PyObject* self = nullptr;  // Reference to the Python object (if created from Python)
    std::shared_ptr<UIGrid> grid;
    std::vector<UIGridPointState> gridstate;
    UISprite sprite;
    sf::Vector2f position; //(x,y) in grid coordinates; float for animation
    //void render(sf::Vector2f); //override final;

    UIEntity();
    
    // Visibility methods
    void updateVisibility();  // Update gridstate from current FOV
    
    // Property system for animations
    bool setProperty(const std::string& name, float value);
    bool setProperty(const std::string& name, int value);
    bool getProperty(const std::string& name, float& value) const;
    
    // Methods that delegate to sprite
    sf::FloatRect get_bounds() const { return sprite.get_bounds(); }
    void move(float dx, float dy) { sprite.move(dx, dy); position.x += dx; position.y += dy; }
    void resize(float w, float h) { /* Entities don't support direct resizing */ }
    
    static PyObject* at(PyUIEntityObject* self, PyObject* o);
    static PyObject* index(PyUIEntityObject* self, PyObject* Py_UNUSED(ignored));
    static PyObject* die(PyUIEntityObject* self, PyObject* Py_UNUSED(ignored));
    static PyObject* path_to(PyUIEntityObject* self, PyObject* args, PyObject* kwds);
    static PyObject* update_visibility(PyUIEntityObject* self, PyObject* Py_UNUSED(ignored));
    static int init(PyUIEntityObject* self, PyObject* args, PyObject* kwds);

    static PyObject* get_position(PyUIEntityObject* self, void* closure);
    static int set_position(PyUIEntityObject* self, PyObject* value, void* closure);
    static PyObject* get_gridstate(PyUIEntityObject* self, void* closure);
    static PyObject* get_spritenumber(PyUIEntityObject* self, void* closure);
    static int set_spritenumber(PyUIEntityObject* self, PyObject* value, void* closure);
    static PyObject* get_float_member(PyUIEntityObject* self, void* closure);
    static int set_float_member(PyUIEntityObject* self, PyObject* value, void* closure);
    static PyMethodDef methods[];
    static PyGetSetDef getsetters[];
    static PyObject* repr(PyUIEntityObject* self);
};

// Forward declaration of methods array
extern PyMethodDef UIEntity_all_methods[];

namespace mcrfpydef {
    static PyTypeObject PyUIEntityType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Entity",
        .tp_basicsize = sizeof(PyUIEntityObject),
        .tp_itemsize = 0,
        .tp_repr = (reprfunc)UIEntity::repr,
        .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
        .tp_doc = "UIEntity objects",
        .tp_methods = UIEntity_all_methods,
        .tp_getset = UIEntity::getsetters,
        .tp_base = &mcrfpydef::PyDrawableType,
        .tp_init = (initproc)UIEntity::init,
        .tp_new = PyType_GenericNew,
    };
}
