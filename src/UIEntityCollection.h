#pragma once
// UIEntityCollection.h - Collection type for managing entities on a grid
//
// Extracted from UIGrid.cpp as part of code organization cleanup.
// This is a Python sequence/mapping type that wraps std::list<std::shared_ptr<UIEntity>>
// with grid-aware semantics (entities can only belong to one grid at a time).

#include "Common.h"
#include "Python.h"
#include "structmember.h"
#include <list>
#include <memory>

// Forward declarations
class UIEntity;
class UIGrid;

// Python object for EntityCollection
typedef struct {
    PyObject_HEAD
    std::shared_ptr<std::list<std::shared_ptr<UIEntity>>> data;
    std::shared_ptr<UIGrid> grid;
} PyUIEntityCollectionObject;

// Python object for EntityCollection iterator
typedef struct {
    PyObject_HEAD
    std::shared_ptr<std::list<std::shared_ptr<UIEntity>>> data;
    std::list<std::shared_ptr<UIEntity>>::iterator current;  // Actual list iterator - O(1) increment
    std::list<std::shared_ptr<UIEntity>>::iterator end;      // End iterator for bounds check
    int start_size;  // For detecting modification during iteration
} PyUIEntityCollectionIterObject;

// UIEntityCollection - Python collection wrapper
class UIEntityCollection {
public:
    // Python sequence protocol
    static PySequenceMethods sqmethods;
    static PyMappingMethods mpmethods;

    // Collection methods
    static PyObject* append(PyUIEntityCollectionObject* self, PyObject* o);
    static PyObject* extend(PyUIEntityCollectionObject* self, PyObject* o);
    static PyObject* remove(PyUIEntityCollectionObject* self, PyObject* o);
    static PyObject* pop(PyUIEntityCollectionObject* self, PyObject* args);
    static PyObject* insert(PyUIEntityCollectionObject* self, PyObject* args);
    static PyObject* index_method(PyUIEntityCollectionObject* self, PyObject* value);
    static PyObject* count(PyUIEntityCollectionObject* self, PyObject* value);
    static PyObject* find(PyUIEntityCollectionObject* self, PyObject* args, PyObject* kwds);
    static PyMethodDef methods[];

    // Python type slots
    static PyObject* repr(PyUIEntityCollectionObject* self);
    static int init(PyUIEntityCollectionObject* self, PyObject* args, PyObject* kwds);
    static PyObject* iter(PyUIEntityCollectionObject* self);

    // Sequence methods
    static Py_ssize_t len(PyUIEntityCollectionObject* self);
    static PyObject* getitem(PyUIEntityCollectionObject* self, Py_ssize_t index);
    static int setitem(PyUIEntityCollectionObject* self, Py_ssize_t index, PyObject* value);
    static int contains(PyUIEntityCollectionObject* self, PyObject* value);
    static PyObject* concat(PyUIEntityCollectionObject* self, PyObject* other);
    static PyObject* inplace_concat(PyUIEntityCollectionObject* self, PyObject* other);

    // Mapping methods (for slice support)
    static PyObject* subscript(PyUIEntityCollectionObject* self, PyObject* key);
    static int ass_subscript(PyUIEntityCollectionObject* self, PyObject* key, PyObject* value);
};

// UIEntityCollectionIter - Iterator for EntityCollection
class UIEntityCollectionIter {
public:
    static int init(PyUIEntityCollectionIterObject* self, PyObject* args, PyObject* kwds);
    static PyObject* next(PyUIEntityCollectionIterObject* self);
    static PyObject* repr(PyUIEntityCollectionIterObject* self);
};

// Python type objects - defined in mcrfpydef namespace
namespace mcrfpydef {

    // Iterator type
    inline PyTypeObject PyUIEntityCollectionIterType = {
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
        .tp_doc = PyDoc_STR("Iterator for a collection of Entity objects"),
        .tp_iter = PyObject_SelfIter,
        .tp_iternext = (iternextfunc)UIEntityCollectionIter::next,
        .tp_init = (initproc)UIEntityCollectionIter::init,
        .tp_alloc = PyType_GenericAlloc,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            PyErr_SetString(PyExc_TypeError, "UIEntityCollectionIter cannot be instantiated directly");
            return NULL;
        }
    };

    // Collection type
    inline PyTypeObject PyUIEntityCollectionType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.EntityCollection",
        .tp_basicsize = sizeof(PyUIEntityCollectionObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)[](PyObject* self)
        {
            PyUIEntityCollectionObject* obj = (PyUIEntityCollectionObject*)self;
            obj->data.reset();
            obj->grid.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)UIEntityCollection::repr,
        .tp_as_sequence = &UIEntityCollection::sqmethods,
        .tp_as_mapping = &UIEntityCollection::mpmethods,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("Iterable, indexable collection of Entity objects.\n\n"
                            "EntityCollection manages entities that belong to a Grid. "
                            "Entities can only belong to one grid at a time - adding an entity "
                            "to a new grid automatically removes it from its previous grid.\n\n"
                            "Supports list-like operations: indexing, slicing, append, extend, "
                            "remove, pop, insert, index, count, and find.\n\n"
                            "Example:\n"
                            "    grid.entities.append(entity)\n"
                            "    player = grid.entities.find(name='player')\n"
                            "    for entity in grid.entities:\n"
                            "        print(entity.pos)"),
        .tp_iter = (getiterfunc)UIEntityCollection::iter,
        .tp_methods = UIEntityCollection::methods,
        .tp_init = (initproc)UIEntityCollection::init,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            PyErr_SetString(PyExc_TypeError, "EntityCollection cannot be instantiated: a C++ data source is required.");
            return NULL;
        }
    };

} // namespace mcrfpydef
