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
	static PySequenceMethods sqmethods;
	static PyObject* append(PyUICollectionObject* self, PyObject* o);
	static PyObject* remove(PyUICollectionObject* self, PyObject* o);
	static PyMethodDef methods[];
	static PyObject* repr(PyUICollectionObject* self);
    static int init(PyUICollectionObject* self, PyObject* args, PyObject* kwds);
    static PyObject* iter(PyUICollectionObject* self);
};

namespace mcrfpydef {
    static PyTypeObject PyUICollectionIterType = {
        //PyVarObject_HEAD_INIT(NULL, 0)
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
        .tp_iternext = (iternextfunc)UICollectionIter::next,
        //.tp_getset = PyUICollection_getset,
        .tp_init = (initproc)UICollectionIter::init, // just raise an exception
        //TODO - as static method, not inline lambda def, please
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            PyErr_SetString(PyExc_TypeError, "UICollection cannot be instantiated: a C++ data source is required.");
            return NULL;
        }
    };

	static PyTypeObject PyUICollectionType = {
		//PyVarObject_/HEAD_INIT(NULL, 0)
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
