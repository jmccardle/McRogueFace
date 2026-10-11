// UIEntityCollection.cpp - Implementation of EntityCollection Python type
//
// Extracted from UIGrid.cpp as part of code organization cleanup.
// This file contains all EntityCollection and UIEntityCollectionIter methods.

#include "UIEntityCollection.h"
#include "PyWrap.h"
#include "UIEntity.h"
#include "PyGridData.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"
#include "PythonObjectCache.h"
#include <sstream>
#include <algorithm>

// #369: single cache-aware conversion from a C++ entity to its Python wrapper.
// Raw tp_alloc here is not merely an identity bug as it is for drawables: a duplicate
// wrapper would carry neither the original's subclass nor its attributes. Every site
// must use this (#430: it is mcrf::to_python).
static PyObject* convertEntityToPython(std::shared_ptr<UIEntity> entity) {
    return mcrf::to_python(entity);
}

PyObject* UIEntityCollection::pyobject_for(const std::shared_ptr<GridData>& grid)
{
    if (!grid) {
        PyErr_SetString(PyExc_RuntimeError, "EntityCollection requires a grid");
        return nullptr;
    }
    return mcrf::cached_wrapper<PyUIEntityCollectionObject>(grid->entities_serial,
        &mcrfpydef::PyUIEntityCollectionType,
        [&](PyUIEntityCollectionObject* o) {
            // tp_alloc zero-fills; construct the C++ members in place (dealloc destroys them).
            new (&o->data) std::shared_ptr<std::vector<std::shared_ptr<UIEntity>>>(grid->entities);
            new (&o->grid) std::shared_ptr<GridData>(grid);
            o->weakreflist = nullptr;
        });
}

// ============================================================================
// UIEntityCollectionIter implementation
// ============================================================================

int UIEntityCollectionIter::init(PyUIEntityCollectionIterObject* self, PyObject* args, PyObject* kwds)
{
    PyErr_SetString(PyExc_TypeError, "UIEntityCollectionIter cannot be instantiated directly");
    return -1;
}

PyObject* UIEntityCollectionIter::next(PyUIEntityCollectionIterObject* self)
{
    // Check for collection modification during iteration
    if (static_cast<int>(self->data->size()) != self->start_size)
    {
        PyErr_SetString(PyExc_RuntimeError, "EntityCollection changed size during iteration");
        return NULL;
    }

    // Check if we've reached the end (bounds-checked against live size so a
    // shrink during iteration can never read past the vector even if the
    // size-change guard above were bypassed).
    if (self->index >= static_cast<Py_ssize_t>(self->data->size()))
    {
        PyErr_SetNone(PyExc_StopIteration);
        return NULL;
    }

    // Get current element and advance the index - O(1) random access
    auto target = (*self->data)[self->index];
    ++self->index;

    return convertEntityToPython(std::static_pointer_cast<UIEntity>(target));
}

PyObject* UIEntityCollectionIter::repr(PyUIEntityCollectionIterObject* self)
{
    std::ostringstream ss;
    if (!self->data) {
        ss << "<UIEntityCollectionIter (invalid internal object)>";
    } else {
        auto total = self->data->size();
        ss << "<UIEntityCollectionIter (" << self->index << "/" << total << " entities)>";
    }
    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

// ============================================================================
// UIEntityCollection - Sequence protocol
// ============================================================================

Py_ssize_t UIEntityCollection::len(PyUIEntityCollectionObject* self) {
    return self->data ? self->data->size() : 0;
}

PyObject* UIEntityCollection::getitem(PyUIEntityCollectionObject* self, Py_ssize_t index) {
    auto vec = self->data.get();
    if (!vec) {
        PyErr_SetString(PyExc_RuntimeError, "EntityCollection data is null");
        return NULL;
    }

    // Handle negative indexing
    Py_ssize_t size = static_cast<Py_ssize_t>(vec->size());
    if (index < 0) index += size;
    if (index < 0 || index >= size) {
        PyErr_SetString(PyExc_IndexError, "EntityCollection index out of range");
        return NULL;
    }

    // #329 - O(1) random access (was std::advance over a std::list, O(n))
    auto target = (*vec)[index];

    return convertEntityToPython(std::static_pointer_cast<UIEntity>(target));
}

// #447: the entity behind an EntityCollection argument, or nullptr with TypeError set.
static std::shared_ptr<UIEntity> entity_arg(PyObject* o, const char* what) {
    if (!PyObject_IsInstance(o, (PyObject*)&mcrfpydef::PyUIEntityType)) {
        PyErr_Format(PyExc_TypeError, "%s requires Entity objects, not %.200s", what, Py_TYPE(o)->tp_name);
        return nullptr;
    }
    auto entity = ((PyUIEntityObject*)o)->data;
    if (!entity) PyErr_SetString(PyExc_RuntimeError, "Invalid Entity object");
    return entity;
}

// #447: every item of `o`, validated before anything moves: Entities only, each at
// most once (one entity can't fill two slots).
static bool entity_items(PyObject* o, const char* what, std::vector<std::shared_ptr<UIEntity>>& out) {
    PyObject* iterator = PyObject_GetIter(o);
    if (!iterator) {
        PyErr_Format(PyExc_TypeError, "%s requires an iterable", what);
        return false;
    }
    PyObject* item;
    while ((item = PyIter_Next(iterator)) != NULL) {
        auto entity = entity_arg(item, what);
        Py_DECREF(item);
        if (!entity) { Py_DECREF(iterator); return false; }
        if (std::find(out.begin(), out.end(), entity) != out.end()) {
            Py_DECREF(iterator);
            PyErr_Format(PyExc_ValueError, "%s: the same Entity appears twice", what);
            return false;
        }
        out.push_back(entity);
    }
    Py_DECREF(iterator);
    return !PyErr_Occurred();
}

static bool has_grid(PyUIEntityCollectionObject* self) {
    if (self->data && self->grid) return true;
    PyErr_SetString(PyExc_RuntimeError, "EntityCollection requires a grid");
    return false;
}

int UIEntityCollection::setitem(PyUIEntityCollectionObject* self, Py_ssize_t index, PyObject* value) {
    auto list = self->data.get();
    if (!list) {
        PyErr_SetString(PyExc_RuntimeError, "EntityCollection data is null");
        return -1;
    }

    // Handle negative indexing
    Py_ssize_t size = static_cast<Py_ssize_t>(list->size());
    if (index < 0) index += size;
    if (index < 0 || index >= size) {
        PyErr_SetString(PyExc_IndexError, "EntityCollection assignment index out of range");
        return -1;
    }

    auto it = list->begin();
    std::advance(it, index);

    // Handle deletion
    if (value == NULL) {
        // Remove from spatial hash before removing from list
        if (self->grid) {
            self->grid->spatial_hash.remove(*it);
        }
        (*it)->setGrid(nullptr);
        list->erase(it);
        return 0;
    }

    auto entity = entity_arg(value, "EntityCollection assignment");
    if (!entity || !has_grid(self)) return -1;

    // #447: replace the entity that is at `index` NOW, wherever it ends up after the
    // incoming one leaves its old slot (which may be in this list, before it).
    std::shared_ptr<UIEntity> old = *it;
    if (old == entity) return 0;
    entity->removeFromGrid();
    auto pos = std::find(list->begin(), list->end(), old);
    self->grid->spatial_hash.remove(old);
    *pos = entity;
    self->grid->spatial_hash.insert(entity);
    entity->setGrid(self->grid);
    old->setGrid(nullptr);  // last: may release the old entity's wrapper (#436)
    return 0;
}

int UIEntityCollection::contains(PyUIEntityCollectionObject* self, PyObject* value) {
    auto list = self->data.get();
    if (!list) {
        PyErr_SetString(PyExc_RuntimeError, "EntityCollection data is null");
        return -1;
    }

    // Type checking
    PyTypeObject* entity_type = &mcrfpydef::PyUIEntityType;
    if (!PyObject_IsInstance(value, (PyObject*)entity_type)) {
        return 0;  // Not an Entity, can't be in collection
    }

    PyUIEntityObject* entity = (PyUIEntityObject*)value;
    if (!entity->data) {
        return 0;
    }

    // Search by comparing C++ pointers
    for (const auto& ent : *list) {
        if (ent.get() == entity->data.get()) {
            return 1;
        }
    }

    return 0;
}

PyObject* UIEntityCollection::concat(PyUIEntityCollectionObject* self, PyObject* other) {
    if (!PySequence_Check(other)) {
        PyErr_SetString(PyExc_TypeError, "can only concatenate sequence to EntityCollection");
        return NULL;
    }

    Py_ssize_t self_len = self->data->size();
    Py_ssize_t other_len = PySequence_Length(other);
    if (other_len == -1) {
        return NULL;
    }

    PyObject* result_list = PyList_New(self_len + other_len);
    if (!result_list) {
        return NULL;
    }

    // Add all elements from self
    Py_ssize_t idx = 0;
    for (const auto& entity : *self->data) {
        PyObject* obj = convertEntityToPython(entity);
        if (!obj) {
            Py_DECREF(result_list);
            return NULL;
        }
        PyList_SET_ITEM(result_list, idx++, obj);
    }

    // Add all elements from other
    for (Py_ssize_t i = 0; i < other_len; i++) {
        PyObject* item = PySequence_GetItem(other, i);
        if (!item) {
            Py_DECREF(result_list);
            return NULL;
        }
        PyList_SET_ITEM(result_list, self_len + i, item);
    }

    return result_list;
}

PyObject* UIEntityCollection::inplace_concat(PyUIEntityCollectionObject* self, PyObject* other) {
    PyObject* result = extend(self, other);
    if (!result) return NULL;
    Py_DECREF(result);
    Py_INCREF(self);
    return (PyObject*)self;
}

PySequenceMethods UIEntityCollection::sqmethods = {
    .sq_length = (lenfunc)UIEntityCollection::len,
    .sq_concat = (binaryfunc)UIEntityCollection::concat,
    .sq_repeat = NULL,
    .sq_item = (ssizeargfunc)UIEntityCollection::getitem,
    .was_sq_slice = NULL,
    .sq_ass_item = (ssizeobjargproc)UIEntityCollection::setitem,
    .was_sq_ass_slice = NULL,
    .sq_contains = (objobjproc)UIEntityCollection::contains,
    .sq_inplace_concat = (binaryfunc)UIEntityCollection::inplace_concat,
    .sq_inplace_repeat = NULL
};

// ============================================================================
// UIEntityCollection - Mapping protocol (for slice support)
// ============================================================================

PyObject* UIEntityCollection::subscript(PyUIEntityCollectionObject* self, PyObject* key) {
    if (PyLong_Check(key)) {
        Py_ssize_t index = PyLong_AsSsize_t(key);
        if (index == -1 && PyErr_Occurred()) {
            return NULL;
        }
        return getitem(self, index);
    } else if (PySlice_Check(key)) {
        Py_ssize_t start, stop, step, slicelength;

        if (PySlice_GetIndicesEx(key, self->data->size(), &start, &stop, &step, &slicelength) < 0) {
            return NULL;
        }

        PyObject* result_list = PyList_New(slicelength);
        if (!result_list) {
            return NULL;
        }

        for (Py_ssize_t i = 0, cur = start; i < slicelength; i++, cur += step) {
            PyObject* obj = convertEntityToPython((*self->data)[cur]);
            if (!obj) {
                Py_DECREF(result_list);
                return NULL;
            }
            PyList_SET_ITEM(result_list, i, obj);
        }

        return result_list;
    } else {
        PyErr_Format(PyExc_TypeError,
            "EntityCollection indices must be integers or slices, not %.200s",
            Py_TYPE(key)->tp_name);
        return NULL;
    }
}

int UIEntityCollection::ass_subscript(PyUIEntityCollectionObject* self, PyObject* key, PyObject* value) {
    if (PyLong_Check(key)) {
        Py_ssize_t index = PyLong_AsSsize_t(key);
        if (index == -1 && PyErr_Occurred()) {
            return -1;
        }
        return setitem(self, index, value);
    } else if (PySlice_Check(key)) {
        Py_ssize_t start, stop, step, slicelength;

        if (PySlice_GetIndicesEx(key, self->data->size(), &start, &stop, &step, &slicelength) < 0) {
            return -1;
        }

        // Handle deletion
        if (value == NULL) {
            if (step == 1) {
                // Contiguous slice deletion
                auto start_it = self->data->begin();
                std::advance(start_it, start);
                auto stop_it = self->data->begin();
                std::advance(stop_it, stop);

                // Clear grid refs and remove from spatial hash
                for (auto it = start_it; it != stop_it; ++it) {
                    if (self->grid) {
                        self->grid->spatial_hash.remove(*it);
                    }
                    (*it)->setGrid(nullptr);
                }
                self->data->erase(start_it, stop_it);
            } else {
                // Extended slice deletion - must delete in reverse to preserve indices
                std::vector<Py_ssize_t> indices;
                for (Py_ssize_t i = 0, cur = start; i < slicelength; i++, cur += step) {
                    indices.push_back(cur);
                }
                std::sort(indices.rbegin(), indices.rend());

                for (Py_ssize_t idx : indices) {
                    auto it = self->data->begin();
                    std::advance(it, idx);
                    if (self->grid) {
                        self->grid->spatial_hash.remove(*it);
                    }
                    (*it)->setGrid(nullptr);
                    self->data->erase(it);
                }
            }
            return 0;
        }

        // Handle assignment
        if (!PySequence_Check(value)) {
            PyErr_SetString(PyExc_TypeError, "can only assign sequence to slice");
            return -1;
        }
        if (!has_grid(self)) return -1;
        std::vector<std::shared_ptr<UIEntity>> new_items;
        if (!entity_items(value, "EntityCollection slice assignment", new_items)) return -1;
        Py_ssize_t value_len = static_cast<Py_ssize_t>(new_items.size());
        if (step != 1 && slicelength != value_len) {
            PyErr_Format(PyExc_ValueError,
                "attempt to assign sequence of size %zd to extended slice of size %zd",
                value_len, slicelength);
            return -1;
        }

        // #447: build the final list, then commit it. An incoming entity that is
        // already a member elsewhere in this list MOVES into the slice: its old slot
        // is dropped, never duplicated. `previous` keeps every entity alive until the
        // pins below are settled.
        const std::vector<std::shared_ptr<UIEntity>> previous = *self->data;
        auto incoming = [&](const std::shared_ptr<UIEntity>& e) {
            return std::find(new_items.begin(), new_items.end(), e) != new_items.end();
        };
        std::vector<std::shared_ptr<UIEntity>> result;
        if (step == 1) {
            for (Py_ssize_t k = 0; k < start; k++)
                if (!incoming(previous[k])) result.push_back(previous[k]);
            result.insert(result.end(), new_items.begin(), new_items.end());
            for (Py_ssize_t k = stop; k < static_cast<Py_ssize_t>(previous.size()); k++)
                if (!incoming(previous[k])) result.push_back(previous[k]);
        } else {
            std::vector<std::shared_ptr<UIEntity>> slots = previous;
            std::vector<bool> assigned(slots.size(), false);
            for (Py_ssize_t i = 0, cur = start; i < slicelength; i++, cur += step) {
                slots[cur] = new_items[i];
                assigned[cur] = true;
            }
            for (size_t k = 0; k < slots.size(); k++)
                if (assigned[k] || !incoming(slots[k])) result.push_back(slots[k]);
        }

        auto member = [](const std::vector<std::shared_ptr<UIEntity>>& v,
                         const std::shared_ptr<UIEntity>& e) {
            return std::find(v.begin(), v.end(), e) != v.end();
        };
        // Entities from other grids leave them first (their lists, their hashes).
        for (auto& e : new_items)
            if (!member(previous, e)) e->removeFromGrid();
        *self->data = result;
        for (auto& e : previous)
            if (!member(result, e)) self->grid->spatial_hash.remove(e);
        for (auto& e : new_items)
            if (!member(previous, e)) self->grid->spatial_hash.insert(e);
        self->grid->markDirty();  // order changed even if membership didn't
        for (auto& e : new_items) e->setGrid(self->grid);
        // Last: releasing a displaced entity's pin may free its wrapper (#436).
        for (auto& e : previous)
            if (!member(result, e)) e->setGrid(nullptr);

        return 0;
    } else {
        PyErr_Format(PyExc_TypeError,
            "EntityCollection indices must be integers or slices, not %.200s",
            Py_TYPE(key)->tp_name);
        return -1;
    }
}

PyMappingMethods UIEntityCollection::mpmethods = {
    .mp_length = (lenfunc)UIEntityCollection::len,
    .mp_subscript = (binaryfunc)UIEntityCollection::subscript,
    .mp_ass_subscript = (objobjargproc)UIEntityCollection::ass_subscript
};

// ============================================================================
// UIEntityCollection - Methods
// ============================================================================

PyObject* UIEntityCollection::append(PyUIEntityCollectionObject* self, PyObject* o)
{
    auto entity = entity_arg(o, "EntityCollection.append");
    if (!entity || !has_grid(self)) return NULL;
    entity->moveToGrid(self->grid);  // #447: from another grid, or to the end of this one
    // #294: perspective_map is lazy; sized on next update_visibility().
    Py_RETURN_NONE;
}

PyObject* UIEntityCollection::remove(PyUIEntityCollectionObject* self, PyObject* o)
{
    PyTypeObject* entity_type = &mcrfpydef::PyUIEntityType;

    if (!PyObject_IsInstance(o, (PyObject*)entity_type)) {
        PyErr_SetString(PyExc_TypeError, "EntityCollection.remove requires an Entity object");
        return NULL;
    }

    PyUIEntityObject* entity = (PyUIEntityObject*)o;
    if (!entity->data) {
        PyErr_SetString(PyExc_RuntimeError, "Invalid Entity object");
        return NULL;
    }

    auto list = self->data.get();
    if (!list) {
        PyErr_SetString(PyExc_RuntimeError, "EntityCollection data is null");
        return NULL;
    }

    // Search by comparing C++ pointers
    for (auto it = list->begin(); it != list->end(); ++it) {
        if (it->get() == entity->data.get()) {
            if (self->grid) {
                self->grid->spatial_hash.remove(*it);
            }
            (*it)->setGrid(nullptr);
            list->erase(it);
            Py_RETURN_NONE;
        }
    }

    PyErr_SetString(PyExc_ValueError, "Entity not in EntityCollection");
    return NULL;
}

PyObject* UIEntityCollection::extend(PyUIEntityCollectionObject* self, PyObject* o)
{
    if (!has_grid(self)) return NULL;
    // Validate ALL items before moving any.
    std::vector<std::shared_ptr<UIEntity>> items;
    if (!entity_items(o, "EntityCollection.extend", items)) return NULL;
    for (auto& entity : items) entity->moveToGrid(self->grid);  // #447
    Py_RETURN_NONE;
}

PyObject* UIEntityCollection::pop(PyUIEntityCollectionObject* self, PyObject* args)
{
    Py_ssize_t index = -1;

    if (!PyArg_ParseTuple(args, "|n", &index)) {
        return NULL;
    }

    auto list = self->data.get();
    if (!list) {
        PyErr_SetString(PyExc_RuntimeError, "EntityCollection data is null");
        return NULL;
    }

    if (list->empty()) {
        PyErr_SetString(PyExc_IndexError, "pop from empty EntityCollection");
        return NULL;
    }

    // Handle negative indexing
    Py_ssize_t size = static_cast<Py_ssize_t>(list->size());
    if (index < 0) {
        index += size;
    }

    if (index < 0 || index >= size) {
        PyErr_SetString(PyExc_IndexError, "pop index out of range");
        return NULL;
    }

    auto it = list->begin();
    std::advance(it, index);

    std::shared_ptr<UIEntity> entity = *it;

    // Remove from spatial hash and clear grid reference
    if (self->grid) {
        self->grid->spatial_hash.remove(entity);
    }
    list->erase(it);

    // Take the result BEFORE dropping ownership: the pin that setGrid(nullptr)
    // releases may be the only thing keeping a subclass wrapper alive (#436).
    PyObject* result = mcrf::to_python(entity);
    entity->setGrid(nullptr);
    return result;
}

// #418: the same per-entity teardown as remove()/pop(), for every member at once.
PyObject* UIEntityCollection::clear(PyUIEntityCollectionObject* self, PyObject* Py_UNUSED(ignored))
{
    auto list = self->data.get();
    if (!list) {
        PyErr_SetString(PyExc_RuntimeError, "EntityCollection data is null");
        return NULL;
    }
    if (list->empty()) Py_RETURN_NONE;

    // Take the members out first: detaching releases identity pins, and a freed
    // wrapper can run Python that edits this collection mid-loop. `removed` keeps
    // every entity alive until the loop is done.
    std::vector<std::shared_ptr<UIEntity>> removed;
    removed.swap(*list);
    if (self->grid) self->grid->spatial_hash.clear();
    for (auto& entity : removed) entity->setGrid(nullptr);  // #446: repaints the grid
    Py_RETURN_NONE;
}

PyObject* UIEntityCollection::insert(PyUIEntityCollectionObject* self, PyObject* args)
{
    Py_ssize_t index;
    PyObject* o;
    if (!PyArg_ParseTuple(args, "nO", &index, &o)) {
        return NULL;
    }
    auto entity = entity_arg(o, "EntityCollection.insert");
    if (!entity || !has_grid(self)) return NULL;
    // #447: list.insert() index semantics, resolved after the entity leaves its old
    // slot, so inserting a member moves it.
    entity->moveToGrid(self->grid, index);
    Py_RETURN_NONE;
}

PyObject* UIEntityCollection::index_method(PyUIEntityCollectionObject* self, PyObject* value) {
    auto list = self->data.get();
    if (!list) {
        PyErr_SetString(PyExc_RuntimeError, "EntityCollection data is null");
        return NULL;
    }

    PyTypeObject* entity_type = &mcrfpydef::PyUIEntityType;

    if (!PyObject_IsInstance(value, (PyObject*)entity_type)) {
        PyErr_SetString(PyExc_TypeError, "EntityCollection.index requires an Entity object");
        return NULL;
    }

    PyUIEntityObject* entity = (PyUIEntityObject*)value;
    if (!entity->data) {
        PyErr_SetString(PyExc_RuntimeError, "Invalid Entity object");
        return NULL;
    }

    Py_ssize_t idx = 0;
    for (const auto& ent : *list) {
        if (ent.get() == entity->data.get()) {
            return PyLong_FromSsize_t(idx);
        }
        idx++;
    }

    PyErr_SetString(PyExc_ValueError, "Entity not in EntityCollection");
    return NULL;
}

PyObject* UIEntityCollection::count(PyUIEntityCollectionObject* self, PyObject* value) {
    auto list = self->data.get();
    if (!list) {
        PyErr_SetString(PyExc_RuntimeError, "EntityCollection data is null");
        return NULL;
    }

    PyTypeObject* entity_type = &mcrfpydef::PyUIEntityType;
    if (!PyObject_IsInstance(value, (PyObject*)entity_type)) {
        return PyLong_FromLong(0);
    }

    PyUIEntityObject* entity = (PyUIEntityObject*)value;
    if (!entity->data) {
        return PyLong_FromLong(0);
    }

    Py_ssize_t cnt = 0;
    for (const auto& ent : *list) {
        if (ent.get() == entity->data.get()) {
            cnt++;
        }
    }

    return PyLong_FromSsize_t(cnt);
}

// Helper function for entity name matching with wildcards
static bool matchEntityName(const std::string& name, const std::string& pattern) {
    if (pattern.find('*') != std::string::npos) {
        if (pattern == "*") {
            return true;
        } else if (pattern.front() == '*' && pattern.back() == '*' && pattern.length() > 2) {
            std::string substring = pattern.substr(1, pattern.length() - 2);
            return name.find(substring) != std::string::npos;
        } else if (pattern.front() == '*') {
            std::string suffix = pattern.substr(1);
            return name.length() >= suffix.length() &&
                   name.compare(name.length() - suffix.length(), suffix.length(), suffix) == 0;
        } else if (pattern.back() == '*') {
            std::string prefix = pattern.substr(0, pattern.length() - 1);
            return name.compare(0, prefix.length(), prefix) == 0;
        }
        return name == pattern;
    }
    return name == pattern;
}

PyObject* UIEntityCollection::find(PyUIEntityCollectionObject* self, PyObject* args, PyObject* kwds) {
    const char* name = nullptr;

    static const char* kwlist[] = {"name", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "s", const_cast<char**>(kwlist), &name)) {
        return NULL;
    }

    auto list = self->data.get();
    if (!list) {
        PyErr_SetString(PyExc_RuntimeError, "EntityCollection data is null");
        return NULL;
    }

    std::string pattern(name);
    bool has_wildcard = (pattern.find('*') != std::string::npos);

    if (has_wildcard) {
        PyObject* results = PyList_New(0);
        if (!results) {
            return NULL;
        }

        for (auto& entity : *list) {
            if (matchEntityName(entity->sprite.name, pattern)) {
                mcrf::PyRef py_entity(mcrf::to_python(entity));
                if (!py_entity || PyList_Append(results, py_entity.get()) < 0) {
                    Py_DECREF(results);
                    return NULL;
                }
            }
        }

        return results;
    } else {
        for (auto& entity : *list) {
            if (entity->sprite.name == pattern) {
                return mcrf::to_python(entity);
            }
        }

        Py_RETURN_NONE;
    }
}

PyMethodDef UIEntityCollection::methods[] = {
    {"append", (PyCFunction)UIEntityCollection::append, METH_O,
     MCRF_METHOD(EntityCollection, append,
         MCRF_SIG("(entity: Entity)", "None"),
         MCRF_DESC("Add an entity to the end of the collection."),
         MCRF_ARGS_START
         MCRF_ARG("entity", "Entity object to append")
         MCRF_RETURNS("None")
     )},
    {"extend", (PyCFunction)UIEntityCollection::extend, METH_O,
     MCRF_METHOD(EntityCollection, extend,
         MCRF_SIG("(iterable)", "None"),
         MCRF_DESC("Add all entities from an iterable to the collection."),
         MCRF_ARGS_START
         MCRF_ARG("iterable", "Iterable of Entity objects to add")
         MCRF_RETURNS("None")
         MCRF_RAISES("TypeError", "If any item is not an Entity object")
         MCRF_RAISES("RuntimeError", "If an Entity object in the iterable has invalid (null) internal state")
     )},
    {"insert", (PyCFunction)UIEntityCollection::insert, METH_VARARGS,
     MCRF_METHOD(EntityCollection, insert,
         MCRF_SIG("(index: int, entity: Entity)", "None"),
         MCRF_DESC("Insert entity at index. Like list.insert(), indices past the end append."),
         MCRF_ARGS_START
         MCRF_ARG("index", "Position at which to insert the entity")
         MCRF_ARG("entity", "Entity object to insert")
         MCRF_RETURNS("None")
     )},
    {"remove", (PyCFunction)UIEntityCollection::remove, METH_O,
     MCRF_METHOD(EntityCollection, remove,
         MCRF_SIG("(entity: Entity)", "None"),
         MCRF_DESC("Remove first occurrence of entity from the collection."),
         MCRF_ARGS_START
         MCRF_ARG("entity", "Entity object to remove")
         MCRF_RETURNS("None")
         MCRF_RAISES("ValueError", "If the entity is not in the collection")
     )},
    {"pop", (PyCFunction)UIEntityCollection::pop, METH_VARARGS,
     MCRF_METHOD(EntityCollection, pop,
         MCRF_SIG("(index: int = -1)", "Entity"),
         MCRF_DESC("Remove and return entity at index (default: last entity)."),
         MCRF_ARGS_START
         MCRF_ARG("index", "Index of entity to remove; defaults to -1 (last entity)")
         MCRF_RETURNS("Entity: the removed entity")
         MCRF_RAISES("IndexError", "If the collection is empty or index is out of range")
     )},
    {"clear", (PyCFunction)UIEntityCollection::clear, METH_NOARGS,
     MCRF_METHOD(EntityCollection, clear,
         MCRF_SIG("()", "None"),
         MCRF_DESC("Remove every entity. Each one is detached from the grid, as with remove()."),
         MCRF_RETURNS("None")
     )},
    {"index", (PyCFunction)UIEntityCollection::index_method, METH_O,
     MCRF_METHOD(EntityCollection, index,
         MCRF_SIG("(entity: Entity)", "int"),
         MCRF_DESC("Return index of first occurrence of entity in the collection."),
         MCRF_ARGS_START
         MCRF_ARG("entity", "Entity object to find")
         MCRF_RETURNS("int: zero-based index of the entity")
         MCRF_RAISES("ValueError", "If the entity is not in the collection")
     )},
    {"count", (PyCFunction)UIEntityCollection::count, METH_O,
     MCRF_METHOD(EntityCollection, count,
         MCRF_SIG("(entity: Entity)", "int"),
         MCRF_DESC("Count occurrences of entity in the collection."),
         MCRF_ARGS_START
         MCRF_ARG("entity", "Entity object to count")
         MCRF_RETURNS("int: number of times entity appears in the collection")
     )},
    {"find", (PyCFunction)UIEntityCollection::find, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(EntityCollection, find,
         MCRF_SIG("(name: str)", "Entity | list[Entity] | None"),
         MCRF_DESC("Find entities by name. Returns a single entity for exact matches or a list for wildcard patterns."),
         MCRF_ARGS_START
         MCRF_ARG("name", "Name to search for; supports wildcards: 'exact', 'prefix*', '*suffix', '*substring*'")
         MCRF_RETURNS("Entity if exact match found, list of Entity if wildcard pattern, None if no exact match")
     )},
    {NULL, NULL, 0, NULL}
};

PyObject* UIEntityCollection::repr(PyUIEntityCollectionObject* self)
{
    std::ostringstream ss;
    if (!self->data) {
        ss << "<EntityCollection (invalid internal object)>";
    } else {
        ss << "<EntityCollection (" << self->data->size() << " entities)>";
    }
    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

int UIEntityCollection::init(PyUIEntityCollectionObject* self, PyObject* args, PyObject* kwds)
{
    PyErr_SetString(PyExc_TypeError, "EntityCollection cannot be instantiated: a C++ data source is required.");
    return -1;
}

PyObject* UIEntityCollection::iter(PyUIEntityCollectionObject* self)
{
    PyTypeObject* iterType = &mcrfpydef::PyUIEntityCollectionIterType;

    PyUIEntityCollectionIterObject* iterObj = (PyUIEntityCollectionIterObject*)iterType->tp_alloc(iterType, 0);
    if (!iterObj) {
        return NULL;
    }

    iterObj->data = self->data;
    iterObj->index = 0;
    iterObj->start_size = self->data->size();

    return (PyObject*)iterObj;
}
