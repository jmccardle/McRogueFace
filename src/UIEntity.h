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
static PyObject* sfVector2f_to_PyObject(sf::Vector2f vector);
static sf::Vector2f PyObject_to_sfVector2f(PyObject* obj);
static PyObject* UIGridPointState_to_PyObject(const UIGridPointState& state);
static PyObject* UIGridPointStateVector_to_PyList(const std::vector<UIGridPointState>& vec);

// TODO: make UIEntity a drawable
class UIEntity//: public UIDrawable
{
public:
    //PyObject* self;
    std::shared_ptr<UIGrid> grid;
    std::vector<UIGridPointState> gridstate;
    UISprite sprite;
    sf::Vector2f position; //(x,y) in grid coordinates; float for animation
    void render(sf::Vector2f); //override final;

    UIEntity();
    UIEntity(UIGrid&);
    
    static PyObject* at(PyUIEntityObject* self, PyObject* o);
    static int init(PyUIEntityObject* self, PyObject* args, PyObject* kwds);

    static PyObject* get_position(PyUIEntityObject* self, void* closure);
    static int set_position(PyUIEntityObject* self, PyObject* value, void* closure);
    static PyObject* get_gridstate(PyUIEntityObject* self, void* closure);
    static PyObject* get_spritenumber(PyUIEntityObject* self, void* closure);
    static int set_spritenumber(PyUIEntityObject* self, PyObject* value, void* closure);
    static PyMethodDef methods[];
    static PyGetSetDef getsetters[];
};

namespace mcrfpydef {
    static PyTypeObject PyUIEntityType = {
        //PyVarObject_HEAD_INIT(NULL, 0)
        .tp_name = "mcrfpy.Entity",
        .tp_basicsize = sizeof(PyUIEntityObject),
        .tp_itemsize = 0,
        // Methods omitted for brevity
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = "UIEntity objects",
        .tp_methods = UIEntity::methods,
        .tp_getset = UIEntity::getsetters,
        .tp_init = (initproc)UIEntity::init,
        .tp_new = PyType_GenericNew,
    };
}
