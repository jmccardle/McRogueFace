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
    // #430: the one way to hand a children collection to Python. The collection has
    // no C++ object of its own, so its cache key (`serial`) lives on the owner:
    // UIDrawable::children_serial, or the Scene's. Same object every call.
    static PyObject* pyobject_for(uint64_t& serial,
                                  const std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>>& data,
                                  const std::shared_ptr<UIDrawable>& owner,
                                  const std::weak_ptr<Scene>& scene);
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
	static PyObject* clear(PyUICollectionObject* self, PyObject* Py_UNUSED(ignored));
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
        .ob_base = PyVarObject_HEAD_INIT(NULL, 0)
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
		.ob_base = PyVarObject_HEAD_INIT(NULL, 0)
		.tp_name = "mcrfpy.UICollection",
		.tp_basicsize = sizeof(PyUICollectionObject),
		.tp_itemsize = 0,
        //TODO - as static method, not inline lambda def, please
		.tp_dealloc = (destructor)[](PyObject* self)
		{
		    PyUICollectionObject* obj = (PyUICollectionObject*)self;
		    if (obj->weakreflist) PyObject_ClearWeakRefs(self);
		    // C++ members live in tp_alloc'd memory: destroy them explicitly.
		    obj->data.~shared_ptr();
		    obj->owner.~weak_ptr();
		    obj->scene.~weak_ptr();
		    Py_TYPE(self)->tp_free(self);
		},
		.tp_repr = (reprfunc)UICollection::repr,
		.tp_as_sequence = &UICollection::sqmethods,
		.tp_as_mapping = &UICollection::mpmethods,
		.tp_flags = Py_TPFLAGS_DEFAULT,
		.tp_doc = PyDoc_STR("Iterable, indexable collection of UI objects"),
		.tp_weaklistoffset = offsetof(PyUICollectionObject, weakreflist),
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
