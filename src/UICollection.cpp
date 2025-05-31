#include "UICollection.h"

#include "UIFrame.h"
#include "UICaption.h"
#include "UISprite.h"
#include "UIGrid.h"
#include "McRFPy_API.h"
#include "PyObjectUtils.h"

using namespace mcrfpydef;

// Local helper function to convert UIDrawable to appropriate Python object
static PyObject* convertDrawableToPython(std::shared_ptr<UIDrawable> drawable) {
    if (!drawable) {
        Py_RETURN_NONE;
    }
    
    PyTypeObject* type = nullptr;
    PyObject* obj = nullptr;
    
    switch (drawable->derived_type()) {
        case PyObjectsEnum::UIFRAME:
        {
            type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Frame");
            if (!type) return nullptr;
            auto pyObj = (PyUIFrameObject*)type->tp_alloc(type, 0);
            if (pyObj) {
                pyObj->data = std::static_pointer_cast<UIFrame>(drawable);
            }
            obj = (PyObject*)pyObj;
            break;
        }
        case PyObjectsEnum::UICAPTION:
        {
            type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Caption");
            if (!type) return nullptr;
            auto pyObj = (PyUICaptionObject*)type->tp_alloc(type, 0);
            if (pyObj) {
                pyObj->data = std::static_pointer_cast<UICaption>(drawable);
                pyObj->font = nullptr;
            }
            obj = (PyObject*)pyObj;
            break;
        }
        case PyObjectsEnum::UISPRITE:
        {
            type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Sprite");
            if (!type) return nullptr;
            auto pyObj = (PyUISpriteObject*)type->tp_alloc(type, 0);
            if (pyObj) {
                pyObj->data = std::static_pointer_cast<UISprite>(drawable);
            }
            obj = (PyObject*)pyObj;
            break;
        }
        case PyObjectsEnum::UIGRID:
        {
            type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Grid");
            if (!type) return nullptr;
            auto pyObj = (PyUIGridObject*)type->tp_alloc(type, 0);
            if (pyObj) {
                pyObj->data = std::static_pointer_cast<UIGrid>(drawable);
            }
            obj = (PyObject*)pyObj;
            break;
        }
        default:
            PyErr_SetString(PyExc_TypeError, "Unknown UIDrawable derived type");
            return nullptr;
    }
    
    if (type) {
        Py_DECREF(type);
    }
    return obj;
}

int UICollectionIter::init(PyUICollectionIterObject* self, PyObject* args, PyObject* kwds)
{
    PyErr_SetString(PyExc_TypeError, "UICollection cannot be instantiated: a C++ data source is required.");
    return -1;
}

PyObject* UICollectionIter::next(PyUICollectionIterObject* self)
{
    // Check if self and self->data are valid
    if (!self || !self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Iterator object or data is null");
        return NULL;
    }
    
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
    // Return the proper Python object for this UIDrawable
    return convertDrawableToPython(target);
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
    return convertDrawableToPython(target);


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
    // Get the iterator type from the module to ensure we have the registered version
    PyTypeObject* iterType = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "UICollectionIter");
    if (!iterType) {
        PyErr_SetString(PyExc_RuntimeError, "Could not find UICollectionIter type in module");
        return NULL;
    }
    
    // Allocate new iterator instance
    PyUICollectionIterObject* iterObj = (PyUICollectionIterObject*)iterType->tp_alloc(iterType, 0);
    
    if (iterObj == NULL) {
        Py_DECREF(iterType);
        return NULL;  // Failed to allocate memory for the iterator object
    }

    iterObj->data = self->data;
    iterObj->index = 0;
    iterObj->start_size = self->data->size();

    Py_DECREF(iterType);
    return (PyObject*)iterObj;
}
