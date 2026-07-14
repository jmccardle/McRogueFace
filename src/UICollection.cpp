#include "UICollection.h"
#include "McRFPy_Doc.h"

#include "UIFrame.h"
#include "UICaption.h"
#include "UISprite.h"
#include "PyGridData.h"
#include "UIGridView.h"
#include "UILine.h"
#include "UICircle.h"
#include "UIArc.h"
#include "3d/Viewport3D.h"
#include "McRFPy_API.h"
#include "PythonObjectCache.h"
#include <climits>
#include <algorithm>

using namespace mcrfpydef;

// #369: promoted to UIDrawable::pyobject_for so .parent, find(), and collection
// indexing all hand back the same wrapper for the same C++ object.
static PyObject* convertDrawableToPython(std::shared_ptr<UIDrawable> drawable) {
    return UIDrawable::pyobject_for(drawable);
}

// #377: the parent link is the inverse of collection membership, so EVERY mutator
// has to maintain it -- not just append(), which was the only one that did. These
// two helpers are the single place that knows how: a scene collection parents via
// setParentScene() (it has no owner drawable, so owner.lock() is null and
// setParent() would silently unparent the child), a drawable-owned one via
// setParent().
//
// #373: they are also the pin points. setParent()/setParentScene() re-evaluate the
// strong ref that keeps a Python subclass wrapper alive while its C++ object is in
// a collection, so linking and unlinking here is what makes the pin correct.
static void link_child(PyUICollectionObject* self, std::shared_ptr<UIDrawable> drawable) {
    if (!self->scene_name.empty()) {
        drawable->setParentScene(self->scene_name);
    } else {
        drawable->setParent(self->owner.lock());
    }
}

// Call BEFORE erasing from the vector: setParent(nullptr) may drop the last strong
// ref to the wrapper, whose dealloc releases its shared_ptr to the drawable. While
// the vector still holds the element, `drawable` cannot be freed under us.
static void unlink_child(std::shared_ptr<UIDrawable> drawable) {
    drawable->setParent(nullptr);
}

// Helper to extract shared_ptr<UIDrawable> from any UIDrawable Python subclass.
// Returns nullptr without setting an error if the type doesn't match.
static std::shared_ptr<UIDrawable> extractDrawable(PyObject* o) {
    if (PyObject_IsInstance(o, (PyObject*)&PyUIFrameType))
        return ((PyUIFrameObject*)o)->data;
    if (PyObject_IsInstance(o, (PyObject*)&PyUICaptionType))
        return ((PyUICaptionObject*)o)->data;
    if (PyObject_IsInstance(o, (PyObject*)&PyUISpriteType))
        return ((PyUISpriteObject*)o)->data;
    // #361: a GridData is NOT a drawable and cannot be appended to a collection.
    // It falls through to the caller's TypeError -- appending a map to a scene used
    // to draw the whole grid a second time through a frozen, invisible camera.
    if (PyObject_IsInstance(o, (PyObject*)&PyUIGridViewType))
        return ((PyUIGridViewObject*)o)->data;
    if (PyObject_IsInstance(o, (PyObject*)&PyUILineType))
        return ((PyUILineObject*)o)->data;
    if (PyObject_IsInstance(o, (PyObject*)&PyUICircleType))
        return ((PyUICircleObject*)o)->data;
    if (PyObject_IsInstance(o, (PyObject*)&PyUIArcType))
        return ((PyUIArcObject*)o)->data;
    if (PyObject_IsInstance(o, (PyObject*)&PyViewport3DType))
        return ((PyViewport3DObject*)o)->data;
    return nullptr;
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
    // Same two traps as setitem(): the old `while (index < 0) index += size()` spun
    // forever on an empty collection, and `index > size() - 1` underflowed to SIZE_MAX
    // when size() was 0 -- so the bounds check passed and we indexed an empty vector.
    Py_ssize_t size = static_cast<Py_ssize_t>(vec->size());
    if (index < 0) index += size;
    if (index < 0 || index >= size)
    {
        PyErr_SetString(PyExc_IndexError, "UICollection index out of range");
        return NULL;
    }
    auto target = (*vec)[index];
    return convertDrawableToPython(target);


}

int UICollection::setitem(PyUICollectionObject* self, Py_ssize_t index, PyObject* value) {
    auto vec = self->data.get();
    if (!vec) {
        PyErr_SetString(PyExc_RuntimeError, "the collection store returned a null pointer");
        return -1;
    }
    
    // Handle negative indexing. NOT a `while (index < 0) index += size()` loop: on an
    // empty collection that adds zero forever, and `children[-1] = x` hung the engine.
    Py_ssize_t size = static_cast<Py_ssize_t>(self->data->size());
    if (index < 0) index += size;

    // Bounds check
    if (index < 0 || index >= size) {
        PyErr_SetString(PyExc_IndexError, "UICollection assignment index out of range");
        return -1;
    }

    // Handle deletion
    if (value == NULL) {
        // #122: Clear the parent before removing
        unlink_child((*self->data)[index]);
        self->data->erase(self->data->begin() + index);
        // #288: Invalidate parent Frame's render cache
        auto owner_ptr = self->owner.lock();
        if (owner_ptr) {
            owner_ptr->markContentDirty();
        }
        return 0;
    }
    
    // Extract drawable from Python object (type-checks internally)
    std::shared_ptr<UIDrawable> new_drawable = extractDrawable(value);
    if (!new_drawable) {
        PyErr_SetString(PyExc_TypeError, "UICollection can only contain Drawable objects");
        return -1;
    }
    // #183: Remove from old parent, which may be a scene rather than a drawable.
    // Do this BEFORE indexing: if the incoming drawable is already a member of THIS
    // collection, detaching it erases it from `vec` and shifts every later element,
    // so an index validated against the old size could write past the end.
    new_drawable->removeFromParent();

    if (index >= static_cast<Py_ssize_t>(vec->size())) {
        PyErr_SetString(PyExc_IndexError, "UICollection assignment index out of range");
        return -1;
    }

    // Hold a strong ref: unlinking may release the last ref to the old element's
    // Python wrapper, whose dealloc drops the wrapper's shared_ptr to it.
    std::shared_ptr<UIDrawable> old_drawable = (*vec)[index];
    int old_z_index = old_drawable->z_index;  // Preserve the z_index

    // #122: Clear parent of old element
    unlink_child(old_drawable);

    // Preserve the z_index of the replaced element
    new_drawable->z_index = old_z_index;

    // #377: parent to the scene, not to a null owner, when this is a scene collection
    link_child(self, new_drawable);

    // Replace the element
    (*vec)[index] = new_drawable;

    // Mark scene as needing resort after replacing element
    McRFPy_API::markSceneNeedsSort();

    // #288: Invalidate parent Frame's render cache
    auto owner_ptr = self->owner.lock();
    if (owner_ptr) {
        owner_ptr->markContentDirty();
    }

    return 0;
}

int UICollection::contains(PyUICollectionObject* self, PyObject* value) {
    auto vec = self->data.get();
    if (!vec) {
        PyErr_SetString(PyExc_RuntimeError, "the collection store returned a null pointer");
        return -1;
    }
    
    // Extract drawable (returns nullptr for non-drawable types)
    std::shared_ptr<UIDrawable> search_drawable = extractDrawable(value);
    if (!search_drawable) {
        return 0;
    }
    
    // Search for the object by comparing C++ pointers
    for (const auto& drawable : *vec) {
        if (drawable.get() == search_drawable.get()) {
            return 1;  // Found
        }
    }
    
    return 0;  // Not found
}

PyObject* UICollection::concat(PyUICollectionObject* self, PyObject* other) {
    // Create a new Python list containing elements from both collections
    if (!PySequence_Check(other)) {
        PyErr_SetString(PyExc_TypeError, "can only concatenate sequence to UICollection");
        return NULL;
    }
    
    Py_ssize_t self_len = self->data->size();
    Py_ssize_t other_len = PySequence_Length(other);
    if (other_len == -1) {
        return NULL;  // Error already set
    }
    
    PyObject* result_list = PyList_New(self_len + other_len);
    if (!result_list) {
        return NULL;
    }
    
    // Add all elements from self
    for (Py_ssize_t i = 0; i < self_len; i++) {
        PyObject* item = convertDrawableToPython((*self->data)[i]);
        if (!item) {
            Py_DECREF(result_list);
            return NULL;
        }
        PyList_SET_ITEM(result_list, i, item);  // Steals reference
    }
    
    // Add all elements from other
    for (Py_ssize_t i = 0; i < other_len; i++) {
        PyObject* item = PySequence_GetItem(other, i);
        if (!item) {
            Py_DECREF(result_list);
            return NULL;
        }
        PyList_SET_ITEM(result_list, self_len + i, item);  // Steals reference
    }
    
    return result_list;
}

PyObject* UICollection::inplace_concat(PyUICollectionObject* self, PyObject* other) {
    if (!PySequence_Check(other)) {
        PyErr_SetString(PyExc_TypeError, "can only concatenate sequence to UICollection");
        return NULL;
    }
    
    // First, validate ALL items in the sequence before modifying anything
    Py_ssize_t other_len = PySequence_Length(other);
    if (other_len == -1) {
        return NULL;  // Error already set
    }
    
    // Validate all items first
    for (Py_ssize_t i = 0; i < other_len; i++) {
        PyObject* item = PySequence_GetItem(other, i);
        if (!item) {
            return NULL;
        }
        
        // Type check - must be a UIDrawable subclass
        if (!PyObject_IsInstance(item, (PyObject*)&PyDrawableType)) {
            Py_DECREF(item);
            PyErr_Format(PyExc_TypeError,
                "UICollection can only contain Drawable objects; "
                "got %s at index %zd", Py_TYPE(item)->tp_name, i);
            return NULL;
        }
        Py_DECREF(item);
    }
    
    // All items validated, now we can safely add them
    for (Py_ssize_t i = 0; i < other_len; i++) {
        PyObject* item = PySequence_GetItem(other, i);
        if (!item) {
            return NULL;  // Shouldn't happen, but be safe
        }
        
        // Use the existing append method which handles z_index assignment
        PyObject* result = append(self, item);
        Py_DECREF(item);
        
        if (!result) {
            return NULL;  // append() failed
        }
        Py_DECREF(result);  // append returns Py_None
    }
    
    Py_INCREF(self);
    return (PyObject*)self;
}

PyObject* UICollection::subscript(PyUICollectionObject* self, PyObject* key) {
    if (PyLong_Check(key)) {
        // Single index - delegate to sq_item
        Py_ssize_t index = PyLong_AsSsize_t(key);
        if (index == -1 && PyErr_Occurred()) {
            return NULL;
        }
        return getitem(self, index);
    } else if (PySlice_Check(key)) {
        // Handle slice
        Py_ssize_t start, stop, step, slicelength;
        
        if (PySlice_GetIndicesEx(key, self->data->size(), &start, &stop, &step, &slicelength) < 0) {
            return NULL;
        }
        
        PyObject* result_list = PyList_New(slicelength);
        if (!result_list) {
            return NULL;
        }
        
        for (Py_ssize_t i = 0, cur = start; i < slicelength; i++, cur += step) {
            PyObject* item = convertDrawableToPython((*self->data)[cur]);
            if (!item) {
                Py_DECREF(result_list);
                return NULL;
            }
            PyList_SET_ITEM(result_list, i, item);  // Steals reference
        }
        
        return result_list;
    } else {
        PyErr_Format(PyExc_TypeError, "UICollection indices must be integers or slices, not %.200s",
                     Py_TYPE(key)->tp_name);
        return NULL;
    }
}

int UICollection::ass_subscript(PyUICollectionObject* self, PyObject* key, PyObject* value) {
    if (PyLong_Check(key)) {
        // Single index - delegate to sq_ass_item
        Py_ssize_t index = PyLong_AsSsize_t(key);
        if (index == -1 && PyErr_Occurred()) {
            return -1;
        }
        return setitem(self, index, value);
    } else if (PySlice_Check(key)) {
        // Handle slice assignment/deletion
        Py_ssize_t start, stop, step, slicelength;
        
        if (PySlice_GetIndicesEx(key, self->data->size(), &start, &stop, &step, &slicelength) < 0) {
            return -1;
        }
        
        if (value == NULL) {
            // Deletion
            if (step != 1) {
                // For non-contiguous slices, delete from highest to lowest to maintain indices
                std::vector<Py_ssize_t> indices;
                for (Py_ssize_t i = 0, cur = start; i < slicelength; i++, cur += step) {
                    indices.push_back(cur);
                }
                // Sort in descending order and delete
                std::sort(indices.begin(), indices.end(), std::greater<Py_ssize_t>());
                for (Py_ssize_t idx : indices) {
                    // #377: unlink before erasing -- a slice delete used to leave the
                    // removed child pointing at a parent that no longer contains it
                    unlink_child((*self->data)[idx]);
                    self->data->erase(self->data->begin() + idx);
                }
            } else {
                // Contiguous slice - can delete in one go
                for (Py_ssize_t i = start; i < stop; i++) {
                    unlink_child((*self->data)[i]);
                }
                self->data->erase(self->data->begin() + start, self->data->begin() + stop);
            }
            
            // Mark scene as needing resort after slice deletion
            McRFPy_API::markSceneNeedsSort();
            // #288: Invalidate parent Frame's render cache
            {
                auto owner_ptr = self->owner.lock();
                if (owner_ptr) {
                    owner_ptr->markContentDirty();
                }
            }

            return 0;
        } else {
            // Assignment
            if (!PySequence_Check(value)) {
                PyErr_SetString(PyExc_TypeError, "can only assign sequence to slice");
                return -1;
            }
            
            Py_ssize_t value_len = PySequence_Length(value);
            if (value_len == -1) {
                return -1;
            }
            
            // Validate all items first
            std::vector<std::shared_ptr<UIDrawable>> new_items;
            for (Py_ssize_t i = 0; i < value_len; i++) {
                PyObject* item = PySequence_GetItem(value, i);
                if (!item) {
                    return -1;
                }
                
                // Type check and extract C++ object
                std::shared_ptr<UIDrawable> drawable = extractDrawable(item);
                if (!drawable) {
                    Py_DECREF(item);
                    PyErr_Format(PyExc_TypeError,
                        "UICollection can only contain Drawable objects; "
                        "got %s at index %zd", Py_TYPE(item)->tp_name, i);
                    return -1;
                }
                
                Py_DECREF(item);
                new_items.push_back(drawable);
            }
            
            if (step != 1 && slicelength != value_len) {
                PyErr_Format(PyExc_ValueError,
                    "attempt to assign sequence of size %zd to extended slice of size %zd",
                    value_len, slicelength);
                return -1;
            }

            // #377: build the post-assignment contents as an independent vector before
            // touching anything. An incoming item may already be a member of THIS
            // collection, and detaching it from its old parent mutates the very vector
            // we would otherwise be indexing into -- shifting `start`/`stop` out from
            // under the erase. Assembling a copy first makes aliasing a non-issue.
            //
            // `previous` also holds a strong ref to every displaced element, so
            // unlinking one (which may release the last ref to its Python wrapper,
            // whose dealloc drops the wrapper's shared_ptr) cannot free it under us.
            std::vector<std::shared_ptr<UIDrawable>> previous = *self->data;
            std::vector<std::shared_ptr<UIDrawable>> result = previous;

            if (step == 1) {
                if (slicelength != value_len) {
                    result.erase(result.begin() + start, result.begin() + stop);
                    result.insert(result.begin() + start, new_items.begin(), new_items.end());
                } else {
                    for (Py_ssize_t i = 0; i < slicelength; i++) {
                        new_items[i]->z_index = previous[start + i]->z_index;  // Preserve z_index
                        result[start + i] = new_items[i];
                    }
                }
            } else {
                for (Py_ssize_t i = 0, cur = start; i < slicelength; i++, cur += step) {
                    new_items[i]->z_index = previous[cur]->z_index;  // Preserve z_index
                    result[cur] = new_items[i];
                }
            }

            auto contains_ptr = [](const std::vector<std::shared_ptr<UIDrawable>>& v,
                                   const UIDrawable* p) {
                return std::any_of(v.begin(), v.end(),
                                   [p](const std::shared_ptr<UIDrawable>& e) { return e.get() == p; });
            };

            // Detach incoming items from whatever parent they had. Safe to do now:
            // this can only mutate `*self->data`, which we are about to overwrite.
            for (auto& item : new_items) {
                item->removeFromParent();
            }

            *self->data = result;

            // Anything the slice displaced is no longer a member -- drop its parent link.
            for (auto& old_item : previous) {
                if (!contains_ptr(result, old_item.get())) {
                    unlink_child(old_item);
                }
            }
            for (auto& item : result) {
                link_child(self, item);
            }


            // Mark scene as needing resort after slice assignment
            McRFPy_API::markSceneNeedsSort();
            // #288: Invalidate parent Frame's render cache
            {
                auto owner_ptr = self->owner.lock();
                if (owner_ptr) {
                    owner_ptr->markContentDirty();
                }
            }

            return 0;
        }
    } else {
        PyErr_Format(PyExc_TypeError, "UICollection indices must be integers or slices, not %.200s",
                     Py_TYPE(key)->tp_name);
        return -1;
    }
}

PyMappingMethods UICollection::mpmethods = {
    .mp_length = (lenfunc)UICollection::len,
    .mp_subscript = (binaryfunc)UICollection::subscript,
    .mp_ass_subscript = (objobjargproc)UICollection::ass_subscript
};

PySequenceMethods UICollection::sqmethods = {
	.sq_length = (lenfunc)UICollection::len,
	.sq_concat = (binaryfunc)UICollection::concat,
	.sq_repeat = NULL,
	.sq_item = (ssizeargfunc)UICollection::getitem,
	.was_sq_slice = NULL,
	.sq_ass_item = (ssizeobjargproc)UICollection::setitem,
	.was_sq_ass_slice = NULL,
	.sq_contains = (objobjproc)UICollection::contains,
	.sq_inplace_concat = (binaryfunc)UICollection::inplace_concat,
	.sq_inplace_repeat = NULL
};


PyObject* UICollection::append(PyUICollectionObject* self, PyObject* o)
{
	// if not UIDrawable subclass, reject it
	// self->data->push_back( c++ object inside o );

    // Extract drawable from Python object
    std::shared_ptr<UIDrawable> drawable = extractDrawable(o);
    if (!drawable) {
        PyErr_SetString(PyExc_TypeError, "Only Drawable objects can be added to UICollection");
        return NULL;
    }

    // Calculate z_index for the new element
    int new_z_index = 0;
    if (!self->data->empty()) {
        int last_z = self->data->back()->z_index;
        if (last_z <= INT_MAX - 10) {
            new_z_index = last_z + 10;
        } else {
            new_z_index = INT_MAX;
        }
    }

    // #183: Remove from old parent (drawable or scene)
    drawable->removeFromParent();

    drawable->z_index = new_z_index;

    // #183: Set new parent - either scene or drawable
    link_child(self, drawable);

    self->data->push_back(drawable);

    // Mark scene as needing resort after adding element
    McRFPy_API::markSceneNeedsSort();

    // #288: Invalidate parent Frame's render cache
    auto owner_ptr = self->owner.lock();
    if (owner_ptr) {
        owner_ptr->markContentDirty();
    }

    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* UICollection::extend(PyUICollectionObject* self, PyObject* iterable)
{
    // Accept any iterable of UIDrawable objects
    PyObject* iterator = PyObject_GetIter(iterable);
    if (iterator == NULL) {
        PyErr_SetString(PyExc_TypeError, "UICollection.extend requires an iterable");
        return NULL;
    }
    
    // Get current highest z_index
    int current_z_index = 0;
    if (!self->data->empty()) {
        current_z_index = self->data->back()->z_index;
    }

    std::shared_ptr<UIDrawable> owner_ptr = self->owner.lock();

    PyObject* item;
    while ((item = PyIter_Next(iterator)) != NULL) {
        std::shared_ptr<UIDrawable> drawable = extractDrawable(item);
        if (!drawable) {
            Py_DECREF(item);
            Py_DECREF(iterator);
            PyErr_SetString(PyExc_TypeError, "All items must be Drawable objects");
            return NULL;
        }

        if (current_z_index <= INT_MAX - 10) {
            current_z_index += 10;
        } else {
            current_z_index = INT_MAX;
        }

        drawable->removeFromParent();
        drawable->z_index = current_z_index;
        // #377: was setParent(owner_ptr), which unparented the drawable outright on a
        // scene collection (no owner drawable => owner.lock() is null)
        link_child(self, drawable);
        self->data->push_back(drawable);

        Py_DECREF(item);
    }

    Py_DECREF(iterator);

    // Check if iteration ended due to an error
    if (PyErr_Occurred()) {
        return NULL;
    }
    
    // Mark scene as needing resort after adding elements
    McRFPy_API::markSceneNeedsSort();

    // #288: Invalidate parent Frame's render cache
    if (owner_ptr) {
        owner_ptr->markContentDirty();
    }

    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* UICollection::remove(PyUICollectionObject* self, PyObject* o)
{
    auto vec = self->data.get();
    if (!vec) {
        PyErr_SetString(PyExc_RuntimeError, "Collection data is null");
        return NULL;
    }

    // Extract drawable from Python object
    std::shared_ptr<UIDrawable> search_drawable = extractDrawable(o);
    if (!search_drawable) {
        PyErr_SetString(PyExc_TypeError,
            "UICollection.remove requires a Drawable object");
        return NULL;
    }

    // Search for the object and remove first occurrence
    for (auto it = vec->begin(); it != vec->end(); ++it) {
        if (it->get() == search_drawable.get()) {
            // #122: Clear the parent before removing
            unlink_child(*it);
            vec->erase(it);
            McRFPy_API::markSceneNeedsSort();
            // #288: Invalidate parent Frame's render cache
            auto owner_ptr = self->owner.lock();
            if (owner_ptr) {
                owner_ptr->markContentDirty();
            }
            Py_RETURN_NONE;
        }
    }

    PyErr_SetString(PyExc_ValueError, "element not in UICollection");
    return NULL;
}

PyObject* UICollection::pop(PyUICollectionObject* self, PyObject* args)
{
    Py_ssize_t index = -1;  // Default to last element

    if (!PyArg_ParseTuple(args, "|n", &index)) {
        return NULL;
    }

    auto vec = self->data.get();
    if (!vec) {
        PyErr_SetString(PyExc_RuntimeError, "Collection data is null");
        return NULL;
    }

    if (vec->empty()) {
        PyErr_SetString(PyExc_IndexError, "pop from empty UICollection");
        return NULL;
    }

    // Handle negative indexing
    Py_ssize_t size = static_cast<Py_ssize_t>(vec->size());
    if (index < 0) {
        index += size;
    }

    if (index < 0 || index >= size) {
        PyErr_SetString(PyExc_IndexError, "pop index out of range");
        return NULL;
    }

    // Get the element before removing
    std::shared_ptr<UIDrawable> drawable = (*vec)[index];

    // #122: Clear the parent before removing
    unlink_child(drawable);

    // Remove from vector
    vec->erase(vec->begin() + index);

    McRFPy_API::markSceneNeedsSort();

    // #288: Invalidate parent Frame's render cache
    auto owner_ptr = self->owner.lock();
    if (owner_ptr) {
        owner_ptr->markContentDirty();
    }

    // Convert to Python object and return
    return convertDrawableToPython(drawable);
}

PyObject* UICollection::insert(PyUICollectionObject* self, PyObject* args)
{
    Py_ssize_t index;
    PyObject* o;

    if (!PyArg_ParseTuple(args, "nO", &index, &o)) {
        return NULL;
    }

    auto vec = self->data.get();
    if (!vec) {
        PyErr_SetString(PyExc_RuntimeError, "Collection data is null");
        return NULL;
    }

    // Extract drawable from Python object
    std::shared_ptr<UIDrawable> drawable = extractDrawable(o);
    if (!drawable) {
        PyErr_SetString(PyExc_TypeError,
            "UICollection.insert requires a Drawable object");
        return NULL;
    }

    // #183: Remove from old parent, which may be a scene rather than a drawable.
    // Do this BEFORE resolving the index: if the drawable is already a member of
    // THIS collection, detaching it erases it from `vec`, and an index clamped
    // against the old size could then land one past the end.
    drawable->removeFromParent();

    // Handle negative indexing and clamping (Python list.insert behavior)
    Py_ssize_t size = static_cast<Py_ssize_t>(vec->size());
    if (index < 0) {
        index += size;
        if (index < 0) {
            index = 0;
        }
    } else if (index > size) {
        index = size;
    }

    // #377: parent to the scene, not to a null owner, when this is a scene collection
    link_child(self, drawable);

    // Insert at position
    vec->insert(vec->begin() + index, drawable);

    McRFPy_API::markSceneNeedsSort();

    // #288: Invalidate parent Frame's render cache
    auto owner_ptr2 = self->owner.lock();
    if (owner_ptr2) {
        owner_ptr2->markContentDirty();
    }

    Py_RETURN_NONE;
}

PyObject* UICollection::index_method(PyUICollectionObject* self, PyObject* value) {
    auto vec = self->data.get();
    if (!vec) {
        PyErr_SetString(PyExc_RuntimeError, "the collection store returned a null pointer");
        return NULL;
    }
    
    // Extract drawable from Python object
    std::shared_ptr<UIDrawable> search_drawable = extractDrawable(value);
    if (!search_drawable) {
        PyErr_SetString(PyExc_TypeError, "UICollection.index requires a Drawable object");
        return NULL;
    }
    
    // Search for the object
    for (size_t i = 0; i < vec->size(); i++) {
        if ((*vec)[i].get() == search_drawable.get()) {
            return PyLong_FromSsize_t(i);
        }
    }
    
    PyErr_SetString(PyExc_ValueError, "value not in UICollection");
    return NULL;
}

PyObject* UICollection::count(PyUICollectionObject* self, PyObject* value) {
    auto vec = self->data.get();
    if (!vec) {
        PyErr_SetString(PyExc_RuntimeError, "the collection store returned a null pointer");
        return NULL;
    }
    
    // Extract drawable (returns nullptr for non-drawable types)
    std::shared_ptr<UIDrawable> search_drawable = extractDrawable(value);
    if (!search_drawable) {
        return PyLong_FromLong(0);
    }
    
    // Count occurrences
    Py_ssize_t count = 0;
    for (const auto& drawable : *vec) {
        if (drawable.get() == search_drawable.get()) {
            count++;
        }
    }
    
    return PyLong_FromSsize_t(count);
}

// Helper function to match names with optional wildcard support
static bool matchName(const std::string& name, const std::string& pattern) {
    // Check for wildcard pattern
    if (pattern.find('*') != std::string::npos) {
        // Simple wildcard matching: only support * at start, end, or both
        if (pattern == "*") {
            return true;  // Match everything
        } else if (pattern.front() == '*' && pattern.back() == '*' && pattern.length() > 2) {
            // *substring* - contains match
            std::string substring = pattern.substr(1, pattern.length() - 2);
            return name.find(substring) != std::string::npos;
        } else if (pattern.front() == '*') {
            // *suffix - ends with
            std::string suffix = pattern.substr(1);
            return name.length() >= suffix.length() &&
                   name.compare(name.length() - suffix.length(), suffix.length(), suffix) == 0;
        } else if (pattern.back() == '*') {
            // prefix* - starts with
            std::string prefix = pattern.substr(0, pattern.length() - 1);
            return name.compare(0, prefix.length(), prefix) == 0;
        }
        // For more complex patterns, fall back to exact match
        return name == pattern;
    }
    // Exact match
    return name == pattern;
}

PyObject* UICollection::find(PyUICollectionObject* self, PyObject* args, PyObject* kwds) {
    const char* name = nullptr;
    int recursive = 0;

    static const char* kwlist[] = {"name", "recursive", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "s|p", const_cast<char**>(kwlist),
                                     &name, &recursive)) {
        return NULL;
    }

    auto vec = self->data.get();
    if (!vec) {
        PyErr_SetString(PyExc_RuntimeError, "Collection data is null");
        return NULL;
    }

    std::string pattern(name);
    bool has_wildcard = (pattern.find('*') != std::string::npos);

    if (has_wildcard) {
        // Return list of all matches
        PyObject* results = PyList_New(0);
        if (!results) return NULL;

        for (auto& drawable : *vec) {
            if (matchName(drawable->name, pattern)) {
                PyObject* py_drawable = convertDrawableToPython(drawable);
                if (!py_drawable) {
                    Py_DECREF(results);
                    return NULL;
                }
                if (PyList_Append(results, py_drawable) < 0) {
                    Py_DECREF(py_drawable);
                    Py_DECREF(results);
                    return NULL;
                }
                Py_DECREF(py_drawable);  // PyList_Append increfs
            }

            // Recursive search into Frame children
            if (recursive && drawable->derived_type() == PyObjectsEnum::UIFRAME) {
                auto frame = std::static_pointer_cast<UIFrame>(drawable);
                // Create temporary collection object for recursive call
                // Use the type directly from namespace (#189 - type not exported to module)
                PyTypeObject* collType = &PyUICollectionType;
                PyUICollectionObject* child_coll = (PyUICollectionObject*)collType->tp_alloc(collType, 0);
                if (child_coll) {
                    child_coll->data = frame->children;
                    PyObject* child_results = find(child_coll, args, kwds);
                    if (child_results && PyList_Check(child_results)) {
                        // Extend results with child results
                        for (Py_ssize_t i = 0; i < PyList_Size(child_results); i++) {
                            PyObject* item = PyList_GetItem(child_results, i);
                            Py_INCREF(item);
                            PyList_Append(results, item);
                            Py_DECREF(item);
                        }
                        Py_DECREF(child_results);
                    }
                    Py_DECREF(child_coll);
                }
            }
        }

        return results;
    } else {
        // Return first exact match or None
        for (auto& drawable : *vec) {
            if (drawable->name == pattern) {
                return convertDrawableToPython(drawable);
            }

            // Recursive search into Frame children
            if (recursive && drawable->derived_type() == PyObjectsEnum::UIFRAME) {
                auto frame = std::static_pointer_cast<UIFrame>(drawable);
                // Use the type directly from namespace (#189 - type not exported to module)
                PyTypeObject* collType = &PyUICollectionType;
                PyUICollectionObject* child_coll = (PyUICollectionObject*)collType->tp_alloc(collType, 0);
                if (child_coll) {
                    child_coll->data = frame->children;
                    PyObject* result = find(child_coll, args, kwds);
                    Py_DECREF(child_coll);
                    if (result && result != Py_None) {
                        return result;
                    }
                    Py_XDECREF(result);
                }
            }
        }

        Py_RETURN_NONE;
    }
}

PyMethodDef UICollection::methods[] = {
	{"append", (PyCFunction)UICollection::append, METH_O,
	 MCRF_METHOD(UICollection, append,
	     MCRF_SIG("(element: Drawable)", "None"),
	     MCRF_DESC("Add an element to the end of the collection.")
	     MCRF_ARGS_START
	     MCRF_ARG("element", "Drawable object to add")
	 )},
	{"extend", (PyCFunction)UICollection::extend, METH_O,
	 MCRF_METHOD(UICollection, extend,
	     MCRF_SIG("(iterable: Iterable[Drawable])", "None"),
	     MCRF_DESC("Add all elements from an iterable to the collection.")
	     MCRF_ARGS_START
	     MCRF_ARG("iterable", "Iterable of Drawable objects to add")
	 )},
	{"insert", (PyCFunction)UICollection::insert, METH_VARARGS,
	 MCRF_METHOD(UICollection, insert,
	     MCRF_SIG("(index: int, element: Drawable)", "None"),
	     MCRF_DESC("Insert element at index. Like list.insert(), indices past the end append.")
	     MCRF_ARGS_START
	     MCRF_ARG("index", "Position at which to insert the element")
	     MCRF_ARG("element", "Drawable object to insert")
	     MCRF_NOTE("If using z_index for sorting, insertion order may not persist after the next render. Use name-based .find() for stable element access.")
	 )},
	{"remove", (PyCFunction)UICollection::remove, METH_O,
	 MCRF_METHOD(UICollection, remove,
	     MCRF_SIG("(element: Drawable)", "None"),
	     MCRF_DESC("Remove first occurrence of element.")
	     MCRF_ARGS_START
	     MCRF_ARG("element", "Drawable object to remove")
	     MCRF_RAISES("ValueError", "If the element is not in the collection")
	 )},
	{"pop", (PyCFunction)UICollection::pop, METH_VARARGS,
	 MCRF_METHOD(UICollection, pop,
	     MCRF_SIG("(index: int = -1)", "Drawable"),
	     MCRF_DESC("Remove and return element at index (default: last element).")
	     MCRF_ARGS_START
	     MCRF_ARG("index", "Position of element to remove (default -1 = last)")
	     MCRF_RETURNS("Drawable: the removed element")
	     MCRF_RAISES("IndexError", "If the collection is empty or index is out of range")
	     MCRF_NOTE("If using z_index for sorting, indices may shift after render. Use name-based .find() for stable element access.")
	 )},
	{"index", (PyCFunction)UICollection::index_method, METH_O,
	 MCRF_METHOD(UICollection, index,
	     MCRF_SIG("(element: Drawable)", "int"),
	     MCRF_DESC("Return index of first occurrence of element.")
	     MCRF_ARGS_START
	     MCRF_ARG("element", "Drawable object to search for")
	     MCRF_RETURNS("int: index of the first occurrence")
	     MCRF_RAISES("ValueError", "If the element is not in the collection")
	 )},
	{"count", (PyCFunction)UICollection::count, METH_O,
	 MCRF_METHOD(UICollection, count,
	     MCRF_SIG("(element: Drawable)", "int"),
	     MCRF_DESC("Count occurrences of element in the collection.")
	     MCRF_ARGS_START
	     MCRF_ARG("element", "Drawable object to count")
	     MCRF_RETURNS("int: number of occurrences")
	 )},
	{"find", (PyCFunction)UICollection::find, METH_VARARGS | METH_KEYWORDS,
	 MCRF_METHOD(UICollection, find,
	     MCRF_SIG("(name: str, recursive: bool = False)", "Drawable | list | None"),
	     MCRF_DESC("Find elements by name. Supports wildcard patterns.")
	     MCRF_ARGS_START
	     MCRF_ARG("name", "Name to search for. Use 'exact' for exact match, 'prefix*', '*suffix', or '*substring*' for wildcard matches")
	     MCRF_ARG("recursive", "If True, search in Frame children recursively")
	     MCRF_RETURNS("Single Drawable for exact match, list for wildcard match, None if not found")
	 )},
	{NULL, NULL, 0, NULL}
};

PyObject* UICollection::repr(PyUICollectionObject* self)
{
	std::ostringstream ss;
	if (!self->data) ss << "<UICollection (invalid internal object)>";
	else {
	    ss << "<UICollection (" << self->data->size() << " objects: ";
	    
	    // Count each type
	    int frame_count = 0, caption_count = 0, sprite_count = 0, grid_count = 0, other_count = 0;
	    for (auto& item : *self->data) {
	        // #366: detect grid-ness with the asGridData() virtual (#355), not
	        // derived_type(). Every mcrfpy.Grid in a collection is a UIGRIDVIEW --
	        // the UIGRID arm this used to key on has not appeared in a scene graph
	        // since #252, so grids were tallied as "other".
	        if (item->asGridData()) { grid_count++; continue; }
	        switch(item->derived_type()) {
	            case PyObjectsEnum::UIFRAME: frame_count++; break;
	            case PyObjectsEnum::UICAPTION: caption_count++; break;
	            case PyObjectsEnum::UISPRITE: sprite_count++; break;
	            default: other_count++; break;
	        }
	    }
	    
	    // Build type summary
	    bool first = true;
	    if (frame_count > 0) {
	        ss << frame_count << " Frame" << (frame_count > 1 ? "s" : "");
	        first = false;
	    }
	    if (caption_count > 0) {
	        if (!first) ss << ", ";
	        ss << caption_count << " Caption" << (caption_count > 1 ? "s" : "");
	        first = false;
	    }
	    if (sprite_count > 0) {
	        if (!first) ss << ", ";
	        ss << sprite_count << " Sprite" << (sprite_count > 1 ? "s" : "");
	        first = false;
	    }
	    if (grid_count > 0) {
	        if (!first) ss << ", ";
	        ss << grid_count << " Grid" << (grid_count > 1 ? "s" : "");
	        first = false;
	    }
	    if (other_count > 0) {
	        if (!first) ss << ", ";
	        ss << other_count << " UIDrawable" << (other_count > 1 ? "s" : "");
	    }
	    
	    ss << ")>";
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
    // Use the iterator type directly from namespace (#189 - type not exported to module)
    PyTypeObject* iterType = &PyUICollectionIterType;

    // Allocate new iterator instance
    PyUICollectionIterObject* iterObj = (PyUICollectionIterObject*)iterType->tp_alloc(iterType, 0);

    if (iterObj == NULL) {
        return NULL;  // Failed to allocate memory for the iterator object
    }

    iterObj->data = self->data;
    iterObj->index = 0;
    iterObj->start_size = self->data->size();

    return (PyObject*)iterObj;
}
