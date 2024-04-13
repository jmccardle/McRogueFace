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
    // asdf
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



    //TODO: add this method to class scope; move implementation to .cpp file
/*
    static int PyUICollectionIter_init(PyUICollectionIterObject* self, PyObject* args, PyObject* kwds)
    {
        PyErr_SetString(PyExc_TypeError, "UICollection cannot be instantiated: a C++ data source is required.");
        return -1;
    }
*/
    //TODO: add this method to class scope; move implementation to .cpp file
/*
    static PyObject* PyUICollectionIter_next(PyUICollectionIterObject* self)
    {
        if (self->data->size() != self->start_size)
        {
            PyErr_SetString(PyExc_RuntimeError, "collection changed size during iteration");
            return NULL;
        }

        if (self->index > self->start_size - 1)
        {
            PyErr_SetNone(PyExc_StopIteration);
            return NULL;
        }
		self->index++;
        auto vec = self->data.get();
        if (!vec)
        {
            PyErr_SetString(PyExc_RuntimeError, "the collection store returned a null pointer");
            return NULL;
        }
        auto target = (*vec)[self->index-1];
        // TODO build PyObject* of the correct UIDrawable subclass to return
        //return py_instance(target);
        return NULL;
    }
*/

    //TODO: add this method to class scope; move implementation to .cpp file
/*
	static PyObject* PyUICollectionIter_repr(PyUICollectionIterObject* self)
	{
		std::ostringstream ss;
		if (!self->data) ss << "<UICollectionIter (invalid internal object)>";
		else {
		    ss << "<UICollectionIter (" << self->data->size() << " child objects, @ index " << self->index  << ")>";
		}
		std::string repr_str = ss.str();
		return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
	}
*/

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
/*
    //TODO: add this method to class scope; move implementation to .cpp file
	static Py_ssize_t PyUICollection_len(PyUICollectionObject* self) {
		return self->data->size();
	}

    //TODO: add this method to class scope; move implementation to .cpp file
	static PyObject* PyUICollection_getitem(PyUICollectionObject* self, Py_ssize_t index) {
		// build a Python version of item at self->data[index]
        //  Copy pasted::
        auto vec = self->data.get();
        if (!vec)
        {
            PyErr_SetString(PyExc_RuntimeError, "the collection store returned a null pointer");
            return NULL;
        }
        while (index < 0) index += self->data->size();
        if (index > self->data->size() - 1)
        {
            PyErr_SetString(PyExc_IndexError, "UICollection index out of range");
            return NULL;
        }
        auto target = (*vec)[index];
        RET_PY_INSTANCE(target);
    return NULL;


	}

    //TODO: add this static array to class scope; move implementation to .cpp file
	static PySequenceMethods PyUICollection_sqmethods = {
		.sq_length = (lenfunc)PyUICollection_len,
		.sq_item = (ssizeargfunc)PyUICollection_getitem,
		//.sq_item_by_index = PyUICollection_getitem
		//.sq_slice - return a subset of the iterable
		//.sq_ass_item - called when `o[x] = y` is executed (x is any object type)
		//.sq_ass_slice - cool; no thanks, for now
		//.sq_contains - called when `x in o` is executed
		//.sq_ass_item_by_index - called when `o[x] = y` is executed (x is explictly an integer)
	};

    //TODO: add this method to class scope; move implementation to .cpp file
	static PyObject* PyUICollection_append(PyUICollectionObject* self, PyObject* o)
	{
		// if not UIDrawable subclass, reject it
		// self->data->push_back( c++ object inside o );

        // this would be a great use case for .tp_base
        if (!PyObject_IsInstance(o, (PyObject*)&PyUIFrameType) &&
            !PyObject_IsInstance(o, (PyObject*)&PyUISpriteType) &&
            !PyObject_IsInstance(o, (PyObject*)&PyUICaptionType) &&
            !PyObject_IsInstance(o, (PyObject*)&PyUIGridType)
            )
        {
            PyErr_SetString(PyExc_TypeError, "Only Frame, Caption, Sprite, and Grid objects can be added to UICollection");
            return NULL;
        }

        if (PyObject_IsInstance(o, (PyObject*)&PyUIFrameType))
        {
            PyUIFrameObject* frame = (PyUIFrameObject*)o;
            self->data->push_back(frame->data);
        }
        if (PyObject_IsInstance(o, (PyObject*)&PyUICaptionType))
        {
            PyUICaptionObject* caption = (PyUICaptionObject*)o;
            self->data->push_back(caption->data);
        }
        if (PyObject_IsInstance(o, (PyObject*)&PyUISpriteType))
        {
            PyUISpriteObject* sprite = (PyUISpriteObject*)o;
            self->data->push_back(sprite->data);
        }
        if (PyObject_IsInstance(o, (PyObject*)&PyUIGridType))
        {
            PyUIGridObject* grid = (PyUIGridObject*)o;
            self->data->push_back(grid->data);
        }

        Py_INCREF(Py_None);
        return Py_None;
	}

    //TODO: add this method to class scope; move implementation to .cpp file
	static PyObject* PyUICollection_remove(PyUICollectionObject* self, PyObject* o)
	{
		if (!PyLong_Check(o))
        {
            PyErr_SetString(PyExc_TypeError, "UICollection.remove requires an integer index to remove");
            return NULL;
        }
		long index = PyLong_AsLong(o);
		if (index >= self->data->size())
        {
            PyErr_SetString(PyExc_ValueError, "Index out of range");
            return NULL;
        }
        else if (index < 0)
        {
            PyErr_SetString(PyExc_NotImplementedError, "reverse indexing is not implemented.");
            return NULL;
        }

		// release the shared pointer at self->data[index];
        self->data->erase(self->data->begin() + index);
        Py_INCREF(Py_None);
        return Py_None;
	}

    //TODO: add this static array to class scope; move implementation to .cpp file

	static PyMethodDef PyUICollection_methods[] = {
		{"append", (PyCFunction)PyUICollection_append, METH_O},
        //{"extend", (PyCFunction)PyUICollection_extend, METH_O}, // TODO
		{"remove", (PyCFunction)PyUICollection_remove, METH_O},
		{NULL, NULL, 0, NULL}
	};

    //TODO: add this method to class scope; move implementation to .cpp file
	static PyObject* PyUICollection_repr(PyUICollectionObject* self)
	{
		std::ostringstream ss;
		if (!self->data) ss << "<UICollection (invalid internal object)>";
		else {
		    ss << "<UICollection (" << self->data->size() << " child objects)>";
		}
		std::string repr_str = ss.str();
		return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
	}

    //TODO: add this method to class scope; move implementation to .cpp file
    static int PyUICollection_init(PyUICollectionObject* self, PyObject* args, PyObject* kwds)
    {
        PyErr_SetString(PyExc_TypeError, "UICollection cannot be instantiated: a C++ data source is required.");
        return -1;
    }

    //TODO: add this method to class scope; move implementation to .cpp file
    static PyObject* PyUICollection_iter(PyUICollectionObject* self)
    {
        PyUICollectionIterObject* iterObj;
        iterObj = (PyUICollectionIterObject*)PyUICollectionIterType.tp_alloc(&PyUICollectionIterType, 0);
        if (iterObj == NULL) {
            return NULL;  // Failed to allocate memory for the iterator object
        }

        iterObj->data = self->data;
        iterObj->index = 0;
        iterObj->start_size = self->data->size();

        return (PyObject*)iterObj;
    }

*/

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
