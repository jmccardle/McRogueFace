// EntityCollection3D.cpp - Python collection for Entity3D objects

#include "EntityCollection3D.h"
#include <algorithm>
#include "Entity3D.h"
#include "Viewport3D.h"
#include "PyWrap.h"

// =============================================================================
// Sequence Methods
// =============================================================================

PySequenceMethods EntityCollection3D::sqmethods = {
    .sq_length = (lenfunc)EntityCollection3D::len,
    .sq_item = (ssizeargfunc)EntityCollection3D::getitem,
    .sq_contains = (objobjproc)EntityCollection3D::contains,
};

// =============================================================================
// EntityCollection3D Implementation
// =============================================================================

PyObject* EntityCollection3D::pyobject_for(uint64_t& serial,
    const std::shared_ptr<std::list<std::shared_ptr<mcrf::Entity3D>>>& data,
    const std::shared_ptr<mcrf::Viewport3D>& viewport)
{
    return mcrf::cached_wrapper<PyEntityCollection3DObject>(serial,
        &mcrfpydef::PyEntityCollection3DType, [&](PyEntityCollection3DObject* o) {
            // tp_alloc zero-fills; construct the C++ members in place (dealloc destroys them).
            new (&o->data) std::shared_ptr<std::list<std::shared_ptr<mcrf::Entity3D>>>(data);
            new (&o->viewport) std::shared_ptr<mcrf::Viewport3D>(viewport);
            o->weakreflist = nullptr;
        });
}

PyObject* EntityCollection3D::repr(PyEntityCollection3DObject* self)
{
    if (!self->data) {
        return PyUnicode_FromString("<EntityCollection3D (null)>");
    }
    return PyUnicode_FromFormat("<EntityCollection3D with %zd entities>", self->data->size());
}

int EntityCollection3D::init(PyEntityCollection3DObject* self, PyObject* args, PyObject* kwds)
{
    PyErr_SetString(PyExc_TypeError, "EntityCollection3D cannot be instantiated directly");
    return -1;
}

PyObject* EntityCollection3D::iter(PyEntityCollection3DObject* self)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Collection has no data");
        return NULL;
    }

    // Create iterator
    auto iter_type = &mcrfpydef::PyEntityCollection3DIterType;
    auto iter_obj = (PyEntityCollection3DIterObject*)iter_type->tp_alloc(iter_type, 0);
    if (!iter_obj) return NULL;

    // Initialize with placement new for iterator members
    new (&iter_obj->data) std::shared_ptr<std::list<std::shared_ptr<mcrf::Entity3D>>>(self->data);
    new (&iter_obj->current) std::list<std::shared_ptr<mcrf::Entity3D>>::iterator(self->data->begin());
    new (&iter_obj->end) std::list<std::shared_ptr<mcrf::Entity3D>>::iterator(self->data->end());
    iter_obj->start_size = static_cast<int>(self->data->size());

    return (PyObject*)iter_obj;
}

Py_ssize_t EntityCollection3D::len(PyEntityCollection3DObject* self)
{
    if (!self->data) return 0;
    return static_cast<Py_ssize_t>(self->data->size());
}

PyObject* EntityCollection3D::getitem(PyEntityCollection3DObject* self, Py_ssize_t index)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Collection has no data");
        return NULL;
    }

    // Handle negative indices
    Py_ssize_t size = static_cast<Py_ssize_t>(self->data->size());
    if (index < 0) index += size;
    if (index < 0 || index >= size) {
        PyErr_SetString(PyExc_IndexError, "EntityCollection3D index out of range");
        return NULL;
    }

    // Iterate to the index (std::list doesn't have random access)
    auto it = self->data->begin();
    std::advance(it, index);

    return mcrf::Entity3D::pyobject_for(*it);
}

int EntityCollection3D::contains(PyEntityCollection3DObject* self, PyObject* value)
{
    if (!self->data) return 0;

    // Check if value is an Entity3D
    if (!PyObject_IsInstance(value, (PyObject*)&mcrfpydef::PyEntity3DType)) {
        return 0;
    }

    auto entity_obj = (PyEntity3DObject*)value;
    if (!entity_obj->data) return 0;

    // Search for the entity
    for (const auto& e : *self->data) {
        if (e.get() == entity_obj->data.get()) {
            return 1;
        }
    }
    return 0;
}

PyObject* EntityCollection3D::append(PyEntityCollection3DObject* self, PyObject* o)
{
    if (!self->data || !self->viewport) {
        PyErr_SetString(PyExc_RuntimeError, "Collection has no data");
        return NULL;
    }

    // Check if argument is an Entity3D
    if (!PyObject_IsInstance(o, (PyObject*)&mcrfpydef::PyEntity3DType)) {
        PyErr_SetString(PyExc_TypeError, "Can only append Entity3D objects");
        return NULL;
    }

    auto entity_obj = (PyEntity3DObject*)o;
    if (!entity_obj->data) {
        PyErr_SetString(PyExc_ValueError, "Entity3D has no data");
        return NULL;
    }

    if (!self->viewport) {
        PyErr_SetString(PyExc_RuntimeError, "EntityCollection3D has no viewport");
        return NULL;
    }
    // #438/#447: from another viewport, or to the end of this one -- never in two.
    entity_obj->data->moveToViewport(self->viewport);

    Py_RETURN_NONE;
}

PyObject* EntityCollection3D::remove(PyEntityCollection3DObject* self, PyObject* o)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Collection has no data");
        return NULL;
    }

    // Check if argument is an Entity3D
    if (!PyObject_IsInstance(o, (PyObject*)&mcrfpydef::PyEntity3DType)) {
        PyErr_SetString(PyExc_TypeError, "Can only remove Entity3D objects");
        return NULL;
    }

    auto entity_obj = (PyEntity3DObject*)o;
    if (!entity_obj->data) {
        PyErr_SetString(PyExc_ValueError, "Entity3D has no data");
        return NULL;
    }

    // Search and remove
    for (auto it = self->data->begin(); it != self->data->end(); ++it) {
        if (it->get() == entity_obj->data.get()) {
            // Clear viewport reference
            entity_obj->data->setViewport(nullptr);
            self->data->erase(it);
            Py_RETURN_NONE;
        }
    }

    PyErr_SetString(PyExc_ValueError, "Entity3D not in collection");
    return NULL;
}

PyObject* EntityCollection3D::clear(PyEntityCollection3DObject* self, PyObject* args)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Collection has no data");
        return NULL;
    }

    // Clear viewport references
    for (auto& entity : *self->data) {
        entity->setViewport(nullptr);
    }

    self->data->clear();
    Py_RETURN_NONE;
}

PyObject* EntityCollection3D::pop(PyEntityCollection3DObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"index", NULL};
    Py_ssize_t index = -1;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|n", const_cast<char**>(kwlist), &index)) {
        return NULL;
    }

    if (!self->data || self->data->empty()) {
        PyErr_SetString(PyExc_IndexError, "pop from empty EntityCollection3D");
        return NULL;
    }

    Py_ssize_t size = static_cast<Py_ssize_t>(self->data->size());
    if (index < 0) index += size;
    if (index < 0 || index >= size) {
        PyErr_SetString(PyExc_IndexError, "EntityCollection3D pop index out of range");
        return NULL;
    }

    // Iterate to the index
    auto it = self->data->begin();
    std::advance(it, index);

    auto entity = *it;

    // #430: take the wrapper BEFORE detaching. Detaching releases a subclass's identity
    // pin, which would otherwise let its wrapper die and come back as a base Entity3D.
    PyObject* result = mcrf::Entity3D::pyobject_for(entity);
    if (!result) return NULL;

    entity->setViewport(nullptr);
    self->data->erase(it);

    return result;
}

PyObject* EntityCollection3D::extend(PyEntityCollection3DObject* self, PyObject* o)
{
    if (!self->data || !self->viewport) {
        PyErr_SetString(PyExc_RuntimeError, "Collection has no data");
        return NULL;
    }

    PyObject* iterator = PyObject_GetIter(o);
    if (!iterator) {
        return NULL;
    }

    // First pass: validate all items are Entity3D
    std::vector<std::shared_ptr<mcrf::Entity3D>> to_add;
    PyObject* item;
    while ((item = PyIter_Next(iterator)) != NULL) {
        if (!PyObject_IsInstance(item, (PyObject*)&mcrfpydef::PyEntity3DType)) {
            Py_DECREF(item);
            Py_DECREF(iterator);
            PyErr_SetString(PyExc_TypeError, "extend() requires an iterable of Entity3D objects");
            return NULL;
        }
        auto entity_obj = (PyEntity3DObject*)item;
        if (!entity_obj->data) {
            Py_DECREF(item);
            Py_DECREF(iterator);
            PyErr_SetString(PyExc_ValueError, "Entity3D has no data");
            return NULL;
        }
        if (std::find(to_add.begin(), to_add.end(), entity_obj->data) != to_add.end()) {  // #447
            Py_DECREF(item);
            Py_DECREF(iterator);
            PyErr_SetString(PyExc_ValueError, "extend(): the same Entity3D appears twice");
            return NULL;
        }
        to_add.push_back(entity_obj->data);
        Py_DECREF(item);
    }
    Py_DECREF(iterator);

    if (PyErr_Occurred()) {
        return NULL;
    }

    if (!self->viewport) {
        PyErr_SetString(PyExc_RuntimeError, "EntityCollection3D has no viewport");
        return NULL;
    }
    // Second pass: move all validated entities (#438/#447)
    for (auto& entity : to_add) {
        entity->moveToViewport(self->viewport);
    }

    Py_RETURN_NONE;
}

PyObject* EntityCollection3D::find(PyEntityCollection3DObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"name", NULL};
    const char* name = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "s", const_cast<char**>(kwlist), &name)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Collection has no data");
        return NULL;
    }

    for (const auto& entity : *self->data) {
        if (entity->getName() == name) {
            return mcrf::Entity3D::pyobject_for(entity);
        }
    }

    Py_RETURN_NONE;
}

PyMethodDef EntityCollection3D::methods[] = {
    {"append", (PyCFunction)EntityCollection3D::append, METH_O,
     "append(entity)\n\n"
     "Add an Entity3D to the collection."},
    {"remove", (PyCFunction)EntityCollection3D::remove, METH_O,
     "remove(entity)\n\n"
     "Remove an Entity3D from the collection."},
    {"clear", (PyCFunction)EntityCollection3D::clear, METH_NOARGS,
     "clear()\n\n"
     "Remove all entities from the collection."},
    {"pop", (PyCFunction)EntityCollection3D::pop, METH_VARARGS | METH_KEYWORDS,
     "pop(index=-1) -> Entity3D\n\n"
     "Remove and return Entity3D at index (default: last)."},
    {"extend", (PyCFunction)EntityCollection3D::extend, METH_O,
     "extend(iterable)\n\n"
     "Add all Entity3D objects from iterable to the collection."},
    {"find", (PyCFunction)EntityCollection3D::find, METH_VARARGS | METH_KEYWORDS,
     "find(name) -> Entity3D or None\n\n"
     "Find an Entity3D by name. Returns None if not found."},
    {NULL}  // Sentinel
};

// =============================================================================
// EntityCollection3DIter Implementation
// =============================================================================

int EntityCollection3DIter::init(PyEntityCollection3DIterObject* self, PyObject* args, PyObject* kwds)
{
    PyErr_SetString(PyExc_TypeError, "EntityCollection3DIter cannot be instantiated directly");
    return -1;
}

PyObject* EntityCollection3DIter::next(PyEntityCollection3DIterObject* self)
{
    if (!self->data) {
        PyErr_SetNone(PyExc_StopIteration);
        return NULL;
    }

    // Check for modification during iteration
    if (static_cast<int>(self->data->size()) != self->start_size) {
        PyErr_SetString(PyExc_RuntimeError, "Collection modified during iteration");
        return NULL;
    }

    // Check if we've reached the end
    if (self->current == self->end) {
        PyErr_SetNone(PyExc_StopIteration);
        return NULL;
    }

    // Get current entity and advance
    auto entity = *(self->current);
    ++(self->current);

    return mcrf::Entity3D::pyobject_for(entity);
}

PyObject* EntityCollection3DIter::repr(PyEntityCollection3DIterObject* self)
{
    return PyUnicode_FromString("<EntityCollection3DIter>");
}
