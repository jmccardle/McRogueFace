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
#include "UIEntity.h"
#include "UIDrawable.h"
#include "UIBase.h"

class UIGrid: public UIDrawable
{
private:
    std::shared_ptr<PyTexture> ptex;
public:
    UIGrid();
    //UIGrid(int, int, IndexTexture*, float, float, float, float);
    UIGrid(int, int, std::shared_ptr<PyTexture>, sf::Vector2f, sf::Vector2f);
    void update();
    void render(sf::Vector2f, sf::RenderTarget&) override final;
    UIGridPoint& at(int, int);
    PyObjectsEnum derived_type() override final;
    //void setSprite(int);
    virtual UIDrawable* click_at(sf::Vector2f point) override final;

    int grid_x, grid_y;
    //int grid_size; // grid sizes are implied by IndexTexture now
    sf::RectangleShape box;
    float center_x, center_y, zoom;
    //IndexTexture* itex;
    std::shared_ptr<PyTexture> getTexture();
    sf::Sprite sprite, output;
    sf::RenderTexture renderTexture;
    std::vector<UIGridPoint> points;
    std::shared_ptr<std::list<std::shared_ptr<UIEntity>>> entities;

    static int init(PyUIGridObject* self, PyObject* args, PyObject* kwds);
    static PyObject* get_grid_size(PyUIGridObject* self, void* closure);
    static PyObject* get_position(PyUIGridObject* self, void* closure);
    static int set_position(PyUIGridObject* self, PyObject* value, void* closure);
    static PyObject* get_size(PyUIGridObject* self, void* closure);
    static int set_size(PyUIGridObject* self, PyObject* value, void* closure);
    static PyObject* get_center(PyUIGridObject* self, void* closure);
    static int set_center(PyUIGridObject* self, PyObject* value, void* closure);
    static PyObject* get_float_member(PyUIGridObject* self, void* closure);
    static int set_float_member(PyUIGridObject* self, PyObject* value, void* closure);
    static PyObject* get_texture(PyUIGridObject* self, void* closure);
    static PyObject* py_at(PyUIGridObject* self, PyObject* o);
    static PyMethodDef methods[];
    static PyGetSetDef getsetters[];
    static PyObject* get_children(PyUIGridObject* self, void* closure);
    static PyObject* repr(PyUIGridObject* self);
    
};

typedef struct {
    PyObject_HEAD
    std::shared_ptr<std::list<std::shared_ptr<UIEntity>>> data;
    std::shared_ptr<UIGrid> grid;
} PyUIEntityCollectionObject;

class UIEntityCollection {
public:
    static PySequenceMethods sqmethods;
    static PyObject* append(PyUIEntityCollectionObject* self, PyObject* o);
    static PyObject* remove(PyUIEntityCollectionObject* self, PyObject* o);
    static PyMethodDef methods[];
    static PyObject* repr(PyUIEntityCollectionObject* self);
    static int init(PyUIEntityCollectionObject* self, PyObject* args, PyObject* kwds);
    static PyObject* iter(PyUIEntityCollectionObject* self);
    static Py_ssize_t len(PyUIEntityCollectionObject* self);
    static PyObject* getitem(PyUIEntityCollectionObject* self, Py_ssize_t index);
};

typedef struct {
    PyObject_HEAD
    std::shared_ptr<std::list<std::shared_ptr<UIEntity>>> data;
    int index;
    int start_size;
} PyUIEntityCollectionIterObject;

class UIEntityCollectionIter {
public:
    static int init(PyUIEntityCollectionIterObject* self, PyObject* args, PyObject* kwds);
    static PyObject* next(PyUIEntityCollectionIterObject* self);
    static PyObject* repr(PyUIEntityCollectionIterObject* self);
    static PyObject* getitem(PyUIEntityCollectionObject* self, Py_ssize_t index);
    
};

namespace mcrfpydef {
    static PyTypeObject PyUIGridType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Grid",
        .tp_basicsize = sizeof(PyUIGridObject),
        .tp_itemsize = 0,
        //.tp_dealloc = (destructor)[](PyObject* self)
        //{
        //    PyUIGridObject* obj = (PyUIGridObject*)self;
        //    obj->data.reset();
        //    Py_TYPE(self)->tp_free(self);
        //},
        //TODO - PyUIGrid REPR def:
        .tp_repr = (reprfunc)UIGrid::repr,
        //.tp_hash = NULL,
        //.tp_iter
        //.tp_iternext
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("docstring"),
        .tp_methods = UIGrid::methods,
        //.tp_members = UIGrid::members,
        .tp_getset = UIGrid::getsetters,
        //.tp_base = NULL,
        .tp_init = (initproc)UIGrid::init,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            PyUIGridObject* self = (PyUIGridObject*)type->tp_alloc(type, 0);
            if (self) self->data = std::make_shared<UIGrid>();
            return (PyObject*)self;
        }
    };

    static PyTypeObject PyUIEntityCollectionIterType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.UIEntityCollectionIter",
        .tp_basicsize = sizeof(PyUIEntityCollectionIterObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)[](PyObject* self)
        {
            PyUIEntityCollectionIterObject* obj = (PyUIEntityCollectionIterObject*)self;
            obj->data.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)UIEntityCollectionIter::repr,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("Iterator for a collection of UI objects"),
        .tp_iter = PyObject_SelfIter,
        .tp_iternext = (iternextfunc)UIEntityCollectionIter::next,
        //.tp_getset = UIEntityCollection::getset,
        .tp_init = (initproc)UIEntityCollectionIter::init, // just raise an exception
        .tp_alloc = PyType_GenericAlloc,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            PyErr_SetString(PyExc_TypeError, "UICollection cannot be instantiated: a C++ data source is required.");
            return NULL;
        }
    };

    static PyTypeObject PyUIEntityCollectionType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.EntityCollection",
        .tp_basicsize = sizeof(PyUIEntityCollectionObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)[](PyObject* self)
        {
            PyUIEntityCollectionObject* obj = (PyUIEntityCollectionObject*)self;
            obj->data.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)UIEntityCollection::repr,
        .tp_as_sequence = &UIEntityCollection::sqmethods,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("Iterable, indexable collection of Entities"),
        .tp_iter = (getiterfunc)UIEntityCollection::iter,
        .tp_methods = UIEntityCollection::methods, // append, remove
        //.tp_getset = UIEntityCollection::getset,
        .tp_init = (initproc)UIEntityCollection::init, // just raise an exception
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            // Does PyUIEntityCollectionType need __new__ if it's not supposed to be instantiable by the user?
            // Should I just raise an exception? Or is the uninitialized shared_ptr enough of a blocker?
            PyErr_SetString(PyExc_TypeError, "EntityCollection cannot be instantiated: a C++ data source is required.");
            return NULL;
        }
    };

}
