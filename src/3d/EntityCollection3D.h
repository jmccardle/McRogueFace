// EntityCollection3D.h - Python collection type for Entity3D objects
// Manages entities belonging to a Viewport3D

#pragma once

#include "Common.h"
#include "Python.h"
#include "structmember.h"
#include <list>
#include <memory>

namespace mcrf {

// Forward declarations
class Entity3D;
class Viewport3D;

} // namespace mcrf

// Python object for EntityCollection3D
typedef struct {
    PyObject_HEAD
    std::shared_ptr<std::list<std::shared_ptr<mcrf::Entity3D>>> data;
    std::shared_ptr<mcrf::Viewport3D> viewport;
} PyEntityCollection3DObject;

// Python object for EntityCollection3D iterator
typedef struct {
    PyObject_HEAD
    std::shared_ptr<std::list<std::shared_ptr<mcrf::Entity3D>>> data;
    std::list<std::shared_ptr<mcrf::Entity3D>>::iterator current;
    std::list<std::shared_ptr<mcrf::Entity3D>>::iterator end;
    int start_size;
} PyEntityCollection3DIterObject;

// EntityCollection3D - Python collection wrapper
class EntityCollection3D {
public:
    // Python sequence protocol
    static PySequenceMethods sqmethods;

    // Collection methods
    static PyObject* append(PyEntityCollection3DObject* self, PyObject* o);
    static PyObject* remove(PyEntityCollection3DObject* self, PyObject* o);
    static PyObject* clear(PyEntityCollection3DObject* self, PyObject* args);
    static PyObject* pop(PyEntityCollection3DObject* self, PyObject* args, PyObject* kwds);
    static PyObject* extend(PyEntityCollection3DObject* self, PyObject* o);
    static PyObject* find(PyEntityCollection3DObject* self, PyObject* args, PyObject* kwds);
    static PyMethodDef methods[];

    // Python type slots
    static PyObject* repr(PyEntityCollection3DObject* self);
    static int init(PyEntityCollection3DObject* self, PyObject* args, PyObject* kwds);
    static PyObject* iter(PyEntityCollection3DObject* self);

    // Sequence methods
    static Py_ssize_t len(PyEntityCollection3DObject* self);
    static PyObject* getitem(PyEntityCollection3DObject* self, Py_ssize_t index);
    static int contains(PyEntityCollection3DObject* self, PyObject* value);
};

// EntityCollection3DIter - Iterator
class EntityCollection3DIter {
public:
    static int init(PyEntityCollection3DIterObject* self, PyObject* args, PyObject* kwds);
    static PyObject* next(PyEntityCollection3DIterObject* self);
    static PyObject* repr(PyEntityCollection3DIterObject* self);
};

namespace mcrfpydef {

// Iterator type
inline PyTypeObject PyEntityCollection3DIterType = {
    .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
    .tp_name = "mcrfpy.EntityCollection3DIter",
    .tp_basicsize = sizeof(PyEntityCollection3DIterObject),
    .tp_itemsize = 0,
    .tp_dealloc = (destructor)[](PyObject* self)
    {
        PyEntityCollection3DIterObject* obj = (PyEntityCollection3DIterObject*)self;
        obj->data.reset();
        Py_TYPE(self)->tp_free(self);
    },
    .tp_repr = (reprfunc)EntityCollection3DIter::repr,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_doc = PyDoc_STR("Iterator for EntityCollection3D"),
    .tp_iter = PyObject_SelfIter,
    .tp_iternext = (iternextfunc)EntityCollection3DIter::next,
    .tp_init = (initproc)EntityCollection3DIter::init,
    .tp_alloc = PyType_GenericAlloc,
    .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
    {
        PyErr_SetString(PyExc_TypeError, "EntityCollection3DIter cannot be instantiated directly");
        return NULL;
    }
};

// Collection type
inline PyTypeObject PyEntityCollection3DType = {
    .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
    .tp_name = "mcrfpy.EntityCollection3D",
    .tp_basicsize = sizeof(PyEntityCollection3DObject),
    .tp_itemsize = 0,
    .tp_dealloc = (destructor)[](PyObject* self)
    {
        PyEntityCollection3DObject* obj = (PyEntityCollection3DObject*)self;
        obj->data.reset();
        obj->viewport.reset();
        Py_TYPE(self)->tp_free(self);
    },
    .tp_repr = (reprfunc)EntityCollection3D::repr,
    .tp_as_sequence = &EntityCollection3D::sqmethods,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_doc = PyDoc_STR("Collection of Entity3D objects belonging to a Viewport3D.\n\n"
                        "Supports list-like operations: indexing, iteration, append, remove.\n\n"
                        "Example:\n"
                        "    viewport.entities.append(entity)\n"
                        "    for entity in viewport.entities:\n"
                        "        print(entity.pos)"),
    .tp_iter = (getiterfunc)EntityCollection3D::iter,
    .tp_methods = EntityCollection3D::methods,
    .tp_init = (initproc)EntityCollection3D::init,
    .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
    {
        PyErr_SetString(PyExc_TypeError, "EntityCollection3D cannot be instantiated directly");
        return NULL;
    }
};

} // namespace mcrfpydef
