// UIEntityCollection.cpp - Implementation of EntityCollection Python type
//
// Extracted from UIGrid.cpp as part of code organization cleanup.
// This file contains all EntityCollection and UIEntityCollectionIter methods.

#include "UIEntityCollection.h"
#include "UIEntity.h"
#include "UIGrid.h"
#include "McRFPy_API.h"
#include "PyTypeCache.h"
#include "PythonObjectCache.h"
#include <sstream>
#include <algorithm>

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

    // Check if we've reached the end
    if (self->current == self->end)
    {
        PyErr_SetNone(PyExc_StopIteration);
        return NULL;
    }

    // Get current element and advance iterator - O(1) operation
    auto target = *self->current;
    ++self->current;

    // Return the stored Python object if it exists (preserves derived types)
    if (target->self != nullptr) {
        Py_INCREF(target->self);
        return target->self;
    }

    // Otherwise create and return a new Python Entity object
    PyTypeObject* entity_type = PyTypeCache::Entity();
    if (!entity_type) {
        PyErr_SetString(PyExc_RuntimeError, "Entity type not initialized in cache");
        return NULL;
    }

    auto o = (PyUIEntityObject*)entity_type->tp_alloc(entity_type, 0);
    if (!o) return NULL;

    o->data = std::static_pointer_cast<UIEntity>(target);
    o->weakreflist = NULL;
    return (PyObject*)o;
}

PyObject* UIEntityCollectionIter::repr(PyUIEntityCollectionIterObject* self)
{
    std::ostringstream ss;
    if (!self->data) {
        ss << "<UIEntityCollectionIter (invalid internal object)>";
    } else {
        auto remaining = std::distance(self->current, self->end);
        auto total = self->data->size();
        ss << "<UIEntityCollectionIter (" << (total - remaining) << "/" << total << " entities)>";
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

    auto it = vec->begin();
    std::advance(it, index);
    auto target = *it;

    // Check cache first to preserve derived class
    if (target->serial_number != 0) {
        PyObject* cached = PythonObjectCache::getInstance().lookup(target->serial_number);
        if (cached) {
            return cached;  // Already INCREF'd by lookup
        }
    }

    // Legacy: If the entity has a stored Python object reference, return that
    if (target->self != nullptr) {
        Py_INCREF(target->self);
        return target->self;
    }

    // Otherwise, create a new base Entity object
    PyTypeObject* entity_type = PyTypeCache::Entity();
    if (!entity_type) {
        PyErr_SetString(PyExc_RuntimeError, "Entity type not initialized in cache");
        return NULL;
    }

    auto o = (PyUIEntityObject*)entity_type->tp_alloc(entity_type, 0);
    if (!o) return NULL;

    o->data = std::static_pointer_cast<UIEntity>(target);
    o->weakreflist = NULL;

    // Re-register in cache if the entity has a serial number
    // This handles the case where the original Python wrapper was GC'd
    // but the C++ object persists (e.g., inline-created objects added to collections)
    if (target->serial_number != 0) {
        PyObject* weakref = PyWeakref_NewRef((PyObject*)o, NULL);
        if (weakref) {
            PythonObjectCache::getInstance().registerObject(target->serial_number, weakref);
            Py_DECREF(weakref);
        }
    }

    return (PyObject*)o;
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
        (*it)->grid = nullptr;
        list->erase(it);
        return 0;
    }

    // Type checking using cached type
    PyTypeObject* entity_type = PyTypeCache::Entity();
    if (!entity_type) {
        PyErr_SetString(PyExc_RuntimeError, "Entity type not initialized in cache");
        return -1;
    }

    if (!PyObject_IsInstance(value, (PyObject*)entity_type)) {
        PyErr_SetString(PyExc_TypeError, "EntityCollection can only contain Entity objects");
        return -1;
    }

    PyUIEntityObject* entity = (PyUIEntityObject*)value;
    if (!entity->data) {
        PyErr_SetString(PyExc_RuntimeError, "Invalid Entity object");
        return -1;
    }

    // Update spatial hash
    if (self->grid) {
        self->grid->spatial_hash.remove(*it);
    }

    // Clear grid reference from the old entity
    (*it)->grid = nullptr;

    // Replace the element and set grid reference
    *it = entity->data;
    entity->data->grid = self->grid;

    // Add to spatial hash
    if (self->grid) {
        self->grid->spatial_hash.insert(entity->data);
    }

    return 0;
}

int UIEntityCollection::contains(PyUIEntityCollectionObject* self, PyObject* value) {
    auto list = self->data.get();
    if (!list) {
        PyErr_SetString(PyExc_RuntimeError, "EntityCollection data is null");
        return -1;
    }

    // Type checking using cached type
    PyTypeObject* entity_type = PyTypeCache::Entity();
    if (!entity_type || !PyObject_IsInstance(value, (PyObject*)entity_type)) {
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

    PyTypeObject* entity_type = PyTypeCache::Entity();
    if (!entity_type) {
        Py_DECREF(result_list);
        PyErr_SetString(PyExc_RuntimeError, "Entity type not initialized in cache");
        return NULL;
    }

    // Add all elements from self
    Py_ssize_t idx = 0;
    for (const auto& entity : *self->data) {
        auto obj = (PyUIEntityObject*)entity_type->tp_alloc(entity_type, 0);
        if (!obj) {
            Py_DECREF(result_list);
            return NULL;
        }
        obj->data = entity;
        obj->weakreflist = NULL;
        PyList_SET_ITEM(result_list, idx++, (PyObject*)obj);
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
    if (!PySequence_Check(other)) {
        PyErr_SetString(PyExc_TypeError, "can only concatenate sequence to EntityCollection");
        return NULL;
    }

    PyTypeObject* entity_type = PyTypeCache::Entity();
    if (!entity_type) {
        PyErr_SetString(PyExc_RuntimeError, "Entity type not initialized in cache");
        return NULL;
    }

    // First, validate ALL items before modifying anything
    Py_ssize_t other_len = PySequence_Length(other);
    if (other_len == -1) {
        return NULL;
    }

    for (Py_ssize_t i = 0; i < other_len; i++) {
        PyObject* item = PySequence_GetItem(other, i);
        if (!item) {
            return NULL;
        }

        if (!PyObject_IsInstance(item, (PyObject*)entity_type)) {
            Py_DECREF(item);
            PyErr_Format(PyExc_TypeError,
                "EntityCollection can only contain Entity objects; "
                "got %s at index %zd", Py_TYPE(item)->tp_name, i);
            return NULL;
        }
        Py_DECREF(item);
    }

    // All items validated, now safely add them
    for (Py_ssize_t i = 0; i < other_len; i++) {
        PyObject* item = PySequence_GetItem(other, i);
        if (!item) {
            return NULL;
        }

        PyObject* result = append(self, item);
        Py_DECREF(item);

        if (!result) {
            return NULL;
        }
        Py_DECREF(result);
    }

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

        PyTypeObject* entity_type = PyTypeCache::Entity();
        if (!entity_type) {
            Py_DECREF(result_list);
            PyErr_SetString(PyExc_RuntimeError, "Entity type not initialized in cache");
            return NULL;
        }

        auto it = self->data->begin();
        for (Py_ssize_t i = 0, cur = start; i < slicelength; i++, cur += step) {
            auto cur_it = it;
            std::advance(cur_it, cur);

            auto obj = (PyUIEntityObject*)entity_type->tp_alloc(entity_type, 0);
            if (!obj) {
                Py_DECREF(result_list);
                return NULL;
            }
            obj->data = *cur_it;
            obj->weakreflist = NULL;
            PyList_SET_ITEM(result_list, i, (PyObject*)obj);
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
                    (*it)->grid = nullptr;
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
                    (*it)->grid = nullptr;
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

        Py_ssize_t value_len = PySequence_Length(value);
        if (value_len == -1) {
            return -1;
        }

        PyTypeObject* entity_type = PyTypeCache::Entity();
        if (!entity_type) {
            PyErr_SetString(PyExc_RuntimeError, "Entity type not initialized in cache");
            return -1;
        }

        // Validate all items first
        std::vector<std::shared_ptr<UIEntity>> new_items;
        for (Py_ssize_t i = 0; i < value_len; i++) {
            PyObject* item = PySequence_GetItem(value, i);
            if (!item) {
                return -1;
            }

            if (!PyObject_IsInstance(item, (PyObject*)entity_type)) {
                Py_DECREF(item);
                PyErr_Format(PyExc_TypeError,
                    "EntityCollection can only contain Entity objects; got %s",
                    Py_TYPE(item)->tp_name);
                return -1;
            }

            PyUIEntityObject* entity_obj = (PyUIEntityObject*)item;
            new_items.push_back(entity_obj->data);
            Py_DECREF(item);
        }

        if (step == 1) {
            // Contiguous slice - can change size
            auto start_it = self->data->begin();
            std::advance(start_it, start);
            auto stop_it = self->data->begin();
            std::advance(stop_it, stop);

            // Clear old grid refs and remove from spatial hash
            for (auto it = start_it; it != stop_it; ++it) {
                if (self->grid) {
                    self->grid->spatial_hash.remove(*it);
                }
                (*it)->grid = nullptr;
            }

            // Erase old range
            auto insert_pos = self->data->erase(start_it, stop_it);

            // Insert new items
            for (const auto& entity : new_items) {
                self->data->insert(insert_pos, entity);
                entity->grid = self->grid;
                if (self->grid) {
                    self->grid->spatial_hash.insert(entity);
                }
            }
        } else {
            // Extended slice - must match size
            if (slicelength != value_len) {
                PyErr_Format(PyExc_ValueError,
                    "attempt to assign sequence of size %zd to extended slice of size %zd",
                    value_len, slicelength);
                return -1;
            }

            auto it = self->data->begin();
            size_t new_idx = 0;
            for (Py_ssize_t i = 0, cur = start; i < slicelength; i++, cur += step) {
                auto cur_it = it;
                std::advance(cur_it, cur);

                if (self->grid) {
                    self->grid->spatial_hash.remove(*cur_it);
                }
                (*cur_it)->grid = nullptr;

                *cur_it = new_items[new_idx++];
                (*cur_it)->grid = self->grid;

                if (self->grid) {
                    self->grid->spatial_hash.insert(*cur_it);
                }
            }
        }

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
    PyTypeObject* entity_type = PyTypeCache::Entity();
    if (!entity_type) {
        PyErr_SetString(PyExc_RuntimeError, "Entity type not initialized in cache");
        return NULL;
    }

    if (!PyObject_IsInstance(o, (PyObject*)entity_type)) {
        PyErr_SetString(PyExc_TypeError, "Only Entity objects can be added to EntityCollection");
        return NULL;
    }

    PyUIEntityObject* entity = (PyUIEntityObject*)o;

    // Remove from old grid first (if different from target grid)
    if (entity->data->grid && entity->data->grid != self->grid) {
        auto old_grid = entity->data->grid;
        auto& old_entities = old_grid->entities;
        auto it = std::find_if(old_entities->begin(), old_entities->end(),
            [entity](const std::shared_ptr<UIEntity>& e) {
                return e.get() == entity->data.get();
            });
        if (it != old_entities->end()) {
            old_entities->erase(it);
            old_grid->spatial_hash.remove(entity->data);
        }
    }

    // Add to this grid (if not already in it)
    if (entity->data->grid != self->grid) {
        self->data->push_back(entity->data);
        entity->data->grid = self->grid;
        if (self->grid) {
            self->grid->spatial_hash.insert(entity->data);
        }
    }

    // Initialize gridstate if not already done
    if (entity->data->gridstate.size() == 0 && self->grid) {
        entity->data->gridstate.resize(self->grid->grid_w * self->grid->grid_h);
        for (auto& state : entity->data->gridstate) {
            state.visible = false;
            state.discovered = false;
        }
    }

    Py_RETURN_NONE;
}

PyObject* UIEntityCollection::remove(PyUIEntityCollectionObject* self, PyObject* o)
{
    PyTypeObject* entity_type = PyTypeCache::Entity();
    if (!entity_type) {
        PyErr_SetString(PyExc_RuntimeError, "Entity type not initialized in cache");
        return NULL;
    }

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
            (*it)->grid = nullptr;
            list->erase(it);
            Py_RETURN_NONE;
        }
    }

    PyErr_SetString(PyExc_ValueError, "Entity not in EntityCollection");
    return NULL;
}

PyObject* UIEntityCollection::extend(PyUIEntityCollectionObject* self, PyObject* o)
{
    // Get iterator for the input
    PyObject* iterator = PyObject_GetIter(o);
    if (!iterator) {
        PyErr_SetString(PyExc_TypeError, "EntityCollection.extend requires an iterable");
        return NULL;
    }

    PyTypeObject* entity_type = PyTypeCache::Entity();
    if (!entity_type) {
        Py_DECREF(iterator);
        PyErr_SetString(PyExc_RuntimeError, "Entity type not initialized in cache");
        return NULL;
    }

    // FIXED: Validate ALL items first before modifying anything
    // (Following the pattern from inplace_concat)
    std::vector<PyUIEntityObject*> validated_entities;
    PyObject* item;
    while ((item = PyIter_Next(iterator)) != NULL) {
        if (!PyObject_IsInstance(item, (PyObject*)entity_type)) {
            // Cleanup on error
            Py_DECREF(item);
            Py_DECREF(iterator);
            PyErr_SetString(PyExc_TypeError, "All items in iterable must be Entity objects");
            return NULL;
        }

        PyUIEntityObject* entity = (PyUIEntityObject*)item;
        if (!entity->data) {
            Py_DECREF(item);
            Py_DECREF(iterator);
            PyErr_SetString(PyExc_RuntimeError, "Invalid Entity object in iterable");
            return NULL;
        }

        validated_entities.push_back(entity);
        // Note: We keep the reference to item until after we're done
    }

    Py_DECREF(iterator);

    // Check if iteration ended due to an error
    if (PyErr_Occurred()) {
        // Release all held references
        for (auto* ent : validated_entities) {
            Py_DECREF(ent);
        }
        return NULL;
    }

    // All items validated - now we can safely add them
    for (auto* entity : validated_entities) {
        self->data->push_back(entity->data);
        entity->data->grid = self->grid;

        if (self->grid) {
            self->grid->spatial_hash.insert(entity->data);
        }

        // Initialize gridstate if needed
        if (entity->data->gridstate.size() == 0 && self->grid) {
            entity->data->gridstate.resize(self->grid->grid_w * self->grid->grid_h);
            for (auto& state : entity->data->gridstate) {
                state.visible = false;
                state.discovered = false;
            }
        }

        Py_DECREF(entity);  // Release the reference we held during validation
    }

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
    entity->grid = nullptr;
    list->erase(it);

    // Create Python object for the entity
    PyTypeObject* entity_type = PyTypeCache::Entity();
    if (!entity_type) {
        PyErr_SetString(PyExc_RuntimeError, "Entity type not initialized in cache");
        return NULL;
    }

    PyUIEntityObject* py_entity = (PyUIEntityObject*)entity_type->tp_alloc(entity_type, 0);
    if (!py_entity) {
        return NULL;
    }

    py_entity->data = entity;
    py_entity->weakreflist = NULL;

    return (PyObject*)py_entity;
}

PyObject* UIEntityCollection::insert(PyUIEntityCollectionObject* self, PyObject* args)
{
    Py_ssize_t index;
    PyObject* o;

    if (!PyArg_ParseTuple(args, "nO", &index, &o)) {
        return NULL;
    }

    auto list = self->data.get();
    if (!list) {
        PyErr_SetString(PyExc_RuntimeError, "EntityCollection data is null");
        return NULL;
    }

    PyTypeObject* entity_type = PyTypeCache::Entity();
    if (!entity_type) {
        PyErr_SetString(PyExc_RuntimeError, "Entity type not initialized in cache");
        return NULL;
    }

    if (!PyObject_IsInstance(o, (PyObject*)entity_type)) {
        PyErr_SetString(PyExc_TypeError, "EntityCollection.insert requires an Entity object");
        return NULL;
    }

    PyUIEntityObject* entity = (PyUIEntityObject*)o;
    if (!entity->data) {
        PyErr_SetString(PyExc_RuntimeError, "Invalid Entity object");
        return NULL;
    }

    // Handle negative indexing and clamping (Python list.insert behavior)
    Py_ssize_t size = static_cast<Py_ssize_t>(list->size());
    if (index < 0) {
        index += size;
        if (index < 0) {
            index = 0;
        }
    } else if (index > size) {
        index = size;
    }

    auto it = list->begin();
    std::advance(it, index);

    list->insert(it, entity->data);
    entity->data->grid = self->grid;

    if (self->grid) {
        self->grid->spatial_hash.insert(entity->data);
    }

    // Initialize gridstate if needed
    if (entity->data->gridstate.size() == 0 && self->grid) {
        entity->data->gridstate.resize(self->grid->grid_w * self->grid->grid_h);
        for (auto& state : entity->data->gridstate) {
            state.visible = false;
            state.discovered = false;
        }
    }

    Py_RETURN_NONE;
}

PyObject* UIEntityCollection::index_method(PyUIEntityCollectionObject* self, PyObject* value) {
    auto list = self->data.get();
    if (!list) {
        PyErr_SetString(PyExc_RuntimeError, "EntityCollection data is null");
        return NULL;
    }

    PyTypeObject* entity_type = PyTypeCache::Entity();
    if (!entity_type) {
        PyErr_SetString(PyExc_RuntimeError, "Entity type not initialized in cache");
        return NULL;
    }

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

    PyTypeObject* entity_type = PyTypeCache::Entity();
    if (!entity_type || !PyObject_IsInstance(value, (PyObject*)entity_type)) {
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

    PyTypeObject* entity_type = PyTypeCache::Entity();
    if (!entity_type) {
        PyErr_SetString(PyExc_RuntimeError, "Entity type not initialized in cache");
        return NULL;
    }

    if (has_wildcard) {
        PyObject* results = PyList_New(0);
        if (!results) {
            return NULL;
        }

        for (auto& entity : *list) {
            if (matchEntityName(entity->sprite.name, pattern)) {
                PyUIEntityObject* py_entity = (PyUIEntityObject*)entity_type->tp_alloc(entity_type, 0);
                if (!py_entity) {
                    Py_DECREF(results);
                    return NULL;
                }
                py_entity->data = entity;
                py_entity->weakreflist = NULL;

                if (PyList_Append(results, (PyObject*)py_entity) < 0) {
                    Py_DECREF(py_entity);
                    Py_DECREF(results);
                    return NULL;
                }
                Py_DECREF(py_entity);
            }
        }

        return results;
    } else {
        for (auto& entity : *list) {
            if (entity->sprite.name == pattern) {
                PyUIEntityObject* py_entity = (PyUIEntityObject*)entity_type->tp_alloc(entity_type, 0);
                if (!py_entity) {
                    return NULL;
                }
                py_entity->data = entity;
                py_entity->weakreflist = NULL;
                return (PyObject*)py_entity;
            }
        }

        Py_RETURN_NONE;
    }
}

PyMethodDef UIEntityCollection::methods[] = {
    {"append", (PyCFunction)UIEntityCollection::append, METH_O,
     "append(entity)\n\n"
     "Add an entity to the end of the collection."},
    {"extend", (PyCFunction)UIEntityCollection::extend, METH_O,
     "extend(iterable)\n\n"
     "Add all entities from an iterable to the collection."},
    {"insert", (PyCFunction)UIEntityCollection::insert, METH_VARARGS,
     "insert(index, entity)\n\n"
     "Insert entity at index. Like list.insert(), indices past the end append."},
    {"remove", (PyCFunction)UIEntityCollection::remove, METH_O,
     "remove(entity)\n\n"
     "Remove first occurrence of entity. Raises ValueError if not found."},
    {"pop", (PyCFunction)UIEntityCollection::pop, METH_VARARGS,
     "pop([index]) -> entity\n\n"
     "Remove and return entity at index (default: last entity)."},
    {"index", (PyCFunction)UIEntityCollection::index_method, METH_O,
     "index(entity) -> int\n\n"
     "Return index of first occurrence of entity. Raises ValueError if not found."},
    {"count", (PyCFunction)UIEntityCollection::count, METH_O,
     "count(entity) -> int\n\n"
     "Count occurrences of entity in the collection."},
    {"find", (PyCFunction)UIEntityCollection::find, METH_VARARGS | METH_KEYWORDS,
     "find(name) -> entity or list\n\n"
     "Find entities by name.\n\n"
     "Args:\n"
     "    name (str): Name to search for. Supports wildcards:\n"
     "        - 'exact' for exact match (returns single entity or None)\n"
     "        - 'prefix*' for starts-with match (returns list)\n"
     "        - '*suffix' for ends-with match (returns list)\n"
     "        - '*substring*' for contains match (returns list)\n\n"
     "Returns:\n"
     "    Single entity if exact match, list if wildcard, None if not found."},
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
    iterObj->current = self->data->begin();
    iterObj->end = self->data->end();
    iterObj->start_size = self->data->size();

    return (PyObject*)iterObj;
}
