#pragma once
#include "Common.h"
#include "Python.h"

#include "UIDrawable.h"

class UICollectionIter
{
    // really more of a namespace: all the members are public and static. But being consistent with other UI objects
public:
    static int init(PyUICollectionIterObject* self, PyObject* args, PyObject* kwds);
    static PyObject* next(PyUICollectionIterObject* self);
    static PyObject* repr(PyUICollectionIterObject* self);
};

class UICollection
{
    // really more of a namespace: all the members are public and static. But being consistent with other UI objects
public:
    static Py_ssize_t len(PyUICollectionObject* self);
	static PyObject* getitem(PyUICollectionObject* self, Py_ssize_t index);
	static int setitem(PyUICollectionObject* self, Py_ssize_t index, PyObject* value);
	static int contains(PyUICollectionObject* self, PyObject* value);
	static PyObject* concat(PyUICollectionObject* self, PyObject* other);
	static PyObject* inplace_concat(PyUICollectionObject* self, PyObject* other);
	static PySequenceMethods sqmethods;
	static PyMappingMethods mpmethods;
	static PyObject* subscript(PyUICollectionObject* self, PyObject* key);
	static int ass_subscript(PyUICollectionObject* self, PyObject* key, PyObject* value);
	static PyObject* append(PyUICollectionObject* self, PyObject* o);
	static PyObject* extend(PyUICollectionObject* self, PyObject* iterable);
	static PyObject* remove(PyUICollectionObject* self, PyObject* o);
	static PyObject* pop(PyUICollectionObject* self, PyObject* args);
	static PyObject* insert(PyUICollectionObject* self, PyObject* args);
	static PyObject* index_method(PyUICollectionObject* self, PyObject* value);
	static PyObject* count(PyUICollectionObject* self, PyObject* value);
	static PyObject* find(PyUICollectionObject* self, PyObject* args, PyObject* kwds);
	static PyMethodDef methods[];
	static PyObject* repr(PyUICollectionObject* self);
    static int init(PyUICollectionObject* self, PyObject* args, PyObject* kwds);
    static PyObject* iter(PyUICollectionObject* self);
};

namespace mcrfpydef {
    // #189 - Use inline instead of static to ensure single instance across translation units
    inline PyTypeObject PyUICollectionIterType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.UICollectionIter",
        .tp_basicsize = sizeof(PyUICollectionIterObject),
        .tp_itemsize = 0,
        //TODO - as static method, not inline lambda def, please
        .tp_dealloc = (destructor)[](PyObject* self)
        {
            PyUICollectionIterObject* obj = (PyUICollectionIterObject*)self;
            obj->data.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)UICollectionIter::repr,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("Iterator for a collection of UI objects"),
        .tp_iter = PyObject_SelfIter,
        .tp_iternext = (iternextfunc)UICollectionIter::next,
        //.tp_getset = PyUICollection_getset,
        .tp_init = (initproc)UICollectionIter::init, // just raise an exception
        .tp_alloc = PyType_GenericAlloc,
        //TODO - as static method, not inline lambda def, please
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            PyErr_SetString(PyExc_TypeError, "UICollection cannot be instantiated: a C++ data source is required.");
            return NULL;
        }
    };

	// #189 - Use inline instead of static to ensure single instance across translation units
	inline PyTypeObject PyUICollectionType = {
		.ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
		.tp_name = "mcrfpy.UICollection",
		.tp_basicsize = sizeof(PyUICollectionObject),
		.tp_itemsize = 0,
        //TODO - as static method, not inline lambda def, please
		.tp_dealloc = (destructor)[](PyObject* self)
		{
		    PyUICollectionObject* obj = (PyUICollectionObject*)self;
		    obj->data.reset();
		    Py_TYPE(self)->tp_free(self);
		},
		.tp_repr = (reprfunc)UICollection::repr,
		.tp_as_sequence = &UICollection::sqmethods,
		.tp_as_mapping = &UICollection::mpmethods,
		.tp_flags = Py_TPFLAGS_DEFAULT,
		.tp_doc = PyDoc_STR("Iterable, indexable collection of UI objects"),
        .tp_iter = (getiterfunc)UICollection::iter,
		.tp_methods = UICollection::methods, // append, remove
        //.tp_getset = PyUICollection_getset,
		.tp_init = (initproc)UICollection::init, // just raise an exception
        //TODO - as static method, not inline lambda def, please
		.tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
		{
            // Does PyUICollectionType need __new__ if it's not supposed to be instantiable by the user? 
            // Should I just raise an exception? Or is the uninitialized shared_ptr enough of a blocker?
            PyErr_SetString(PyExc_TypeError, "UICollection cannot be instantiated: a C++ data source is required.");
		    return NULL;
		}
	};

}
