#include "UICollection.h"

#include "UIFrame.h"
#include "UICaption.h"
#include "UISprite.h"
#include "UIGrid.h"
#include "McRFPy_API.h"

using namespace mcrfpydef;

int UICollectionIter::init(PyUICollectionIterObject* self, PyObject* args, PyObject* kwds)
{
    PyErr_SetString(PyExc_TypeError, "UICollection cannot be instantiated: a C++ data source is required.");
    return -1;
}

PyObject* UICollectionIter::next(PyUICollectionIterObject* self)
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

PyObject* UICollectionIter::repr(PyUICollectionIterObject* self)
{
	std::ostringstream ss;
	if (!self->data) ss << "<UICollectionIter (invalid internal object)>";
	else {
	    ss << "<UICollectionIter (" << self->data->size() << " child objects, @ index " << self->index  << ")>";
	}
	std::string repr_str = ss.str();
	return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

Py_ssize_t UICollection::len(PyUICollectionObject* self) {
	return self->data->size();
}

PyObject* UICollection::getitem(PyUICollectionObject* self, Py_ssize_t index) {
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

PySequenceMethods UICollection::sqmethods = {
	.sq_length = (lenfunc)UICollection::len,
	.sq_item = (ssizeargfunc)UICollection::getitem,
	//.sq_item_by_index = PyUICollection_getitem
	//.sq_slice - return a subset of the iterable
	//.sq_ass_item - called when `o[x] = y` is executed (x is any object type)
	//.sq_ass_slice - cool; no thanks, for now
	//.sq_contains - called when `x in o` is executed
	//.sq_ass_item_by_index - called when `o[x] = y` is executed (x is explictly an integer)
};

/* Idiomatic way to fetch complete types from the API rather than referencing their PyTypeObject struct

auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Texture");

I never identified why `using namespace mcrfpydef;` doesn't solve the segfault issue.
The horrible macro in UIDrawable was originally a workaround for this, but as I interact with the types outside of the monster UI.h, a more general (and less icky) solution is required.

*/

PyObject* UICollection::append(PyUICollectionObject* self, PyObject* o)
{
	// if not UIDrawable subclass, reject it
	// self->data->push_back( c++ object inside o );

    // this would be a great use case for .tp_base
    if (!PyObject_IsInstance(o, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Frame")) &&
        !PyObject_IsInstance(o, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Sprite")) &&
        !PyObject_IsInstance(o, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Caption")) &&
        !PyObject_IsInstance(o, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Grid"))
        )
    {
        PyErr_SetString(PyExc_TypeError, "Only Frame, Caption, Sprite, and Grid objects can be added to UICollection");
        return NULL;
    }

    if (PyObject_IsInstance(o, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Frame")))
    {
        PyUIFrameObject* frame = (PyUIFrameObject*)o;
        self->data->push_back(frame->data);
    }
    if (PyObject_IsInstance(o, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Caption")))
    {
        PyUICaptionObject* caption = (PyUICaptionObject*)o;
        self->data->push_back(caption->data);
    }
    if (PyObject_IsInstance(o, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Sprite")))
    {
        PyUISpriteObject* sprite = (PyUISpriteObject*)o;
        self->data->push_back(sprite->data);
    }
    if (PyObject_IsInstance(o, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Grid")))
    {
        PyUIGridObject* grid = (PyUIGridObject*)o;
        self->data->push_back(grid->data);
    }

    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* UICollection::remove(PyUICollectionObject* self, PyObject* o)
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

PyMethodDef UICollection::methods[] = {
	{"append", (PyCFunction)UICollection::append, METH_O},
    //{"extend", (PyCFunction)PyUICollection_extend, METH_O}, // TODO
	{"remove", (PyCFunction)UICollection::remove, METH_O},
	{NULL, NULL, 0, NULL}
};

PyObject* UICollection::repr(PyUICollectionObject* self)
{
	std::ostringstream ss;
	if (!self->data) ss << "<UICollection (invalid internal object)>";
	else {
	    ss << "<UICollection (" << self->data->size() << " child objects)>";
	}
	std::string repr_str = ss.str();
	return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

int UICollection::init(PyUICollectionObject* self, PyObject* args, PyObject* kwds)
{
    PyErr_SetString(PyExc_TypeError, "UICollection cannot be instantiated: a C++ data source is required.");
    return -1;
}

PyObject* UICollection::iter(PyUICollectionObject* self)
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
