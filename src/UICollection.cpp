#include "UICollection.h"

#include "UIFrame.h"
#include "UICaption.h"
#include "UISprite.h"
#include "UIGrid.h"
#include "McRFPy_API.h"
#include "PyObjectUtils.h"
#include <climits>
#include <algorithm>

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

int UICollection::setitem(PyUICollectionObject* self, Py_ssize_t index, PyObject* value) {
    auto vec = self->data.get();
    if (!vec) {
        PyErr_SetString(PyExc_RuntimeError, "the collection store returned a null pointer");
        return -1;
    }
    
    // Handle negative indexing
    while (index < 0) index += self->data->size();
    
    // Bounds check
    if (index >= self->data->size()) {
        PyErr_SetString(PyExc_IndexError, "UICollection assignment index out of range");
        return -1;
    }
    
    // Handle deletion
    if (value == NULL) {
        self->data->erase(self->data->begin() + index);
        return 0;
    }
    
    // Type checking - must be a UIDrawable subclass
    if (!PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Frame")) &&
        !PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Sprite")) &&
        !PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Caption")) &&
        !PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Grid"))) {
        PyErr_SetString(PyExc_TypeError, "UICollection can only contain Frame, Caption, Sprite, and Grid objects");
        return -1;
    }
    
    // Get the C++ object from the Python object
    std::shared_ptr<UIDrawable> new_drawable = nullptr;
    int old_z_index = (*vec)[index]->z_index;  // Preserve the z_index
    
    if (PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Frame"))) {
        PyUIFrameObject* frame = (PyUIFrameObject*)value;
        new_drawable = frame->data;
    } else if (PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Caption"))) {
        PyUICaptionObject* caption = (PyUICaptionObject*)value;
        new_drawable = caption->data;
    } else if (PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Sprite"))) {
        PyUISpriteObject* sprite = (PyUISpriteObject*)value;
        new_drawable = sprite->data;
    } else if (PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Grid"))) {
        PyUIGridObject* grid = (PyUIGridObject*)value;
        new_drawable = grid->data;
    }
    
    if (!new_drawable) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to extract C++ object from Python object");
        return -1;
    }
    
    // Preserve the z_index of the replaced element
    new_drawable->z_index = old_z_index;
    
    // Replace the element
    (*vec)[index] = new_drawable;
    
    // Mark scene as needing resort after replacing element
    McRFPy_API::markSceneNeedsSort();
    
    return 0;
}

int UICollection::contains(PyUICollectionObject* self, PyObject* value) {
    auto vec = self->data.get();
    if (!vec) {
        PyErr_SetString(PyExc_RuntimeError, "the collection store returned a null pointer");
        return -1;
    }
    
    // Type checking - must be a UIDrawable subclass
    if (!PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Frame")) &&
        !PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Sprite")) &&
        !PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Caption")) &&
        !PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Grid"))) {
        // Not a valid type, so it can't be in the collection
        return 0;
    }
    
    // Get the C++ object from the Python object
    std::shared_ptr<UIDrawable> search_drawable = nullptr;
    
    if (PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Frame"))) {
        PyUIFrameObject* frame = (PyUIFrameObject*)value;
        search_drawable = frame->data;
    } else if (PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Caption"))) {
        PyUICaptionObject* caption = (PyUICaptionObject*)value;
        search_drawable = caption->data;
    } else if (PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Sprite"))) {
        PyUISpriteObject* sprite = (PyUISpriteObject*)value;
        search_drawable = sprite->data;
    } else if (PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Grid"))) {
        PyUIGridObject* grid = (PyUIGridObject*)value;
        search_drawable = grid->data;
    }
    
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
        
        // Type check
        if (!PyObject_IsInstance(item, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Frame")) &&
            !PyObject_IsInstance(item, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Sprite")) &&
            !PyObject_IsInstance(item, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Caption")) &&
            !PyObject_IsInstance(item, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Grid"))) {
            Py_DECREF(item);
            PyErr_Format(PyExc_TypeError, 
                "UICollection can only contain Frame, Caption, Sprite, and Grid objects; "
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
                    self->data->erase(self->data->begin() + idx);
                }
            } else {
                // Contiguous slice - can delete in one go
                self->data->erase(self->data->begin() + start, self->data->begin() + stop);
            }
            
            // Mark scene as needing resort after slice deletion
            McRFPy_API::markSceneNeedsSort();
            
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
                std::shared_ptr<UIDrawable> drawable = nullptr;
                
                if (PyObject_IsInstance(item, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Frame"))) {
                    drawable = ((PyUIFrameObject*)item)->data;
                } else if (PyObject_IsInstance(item, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Caption"))) {
                    drawable = ((PyUICaptionObject*)item)->data;
                } else if (PyObject_IsInstance(item, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Sprite"))) {
                    drawable = ((PyUISpriteObject*)item)->data;
                } else if (PyObject_IsInstance(item, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Grid"))) {
                    drawable = ((PyUIGridObject*)item)->data;
                } else {
                    Py_DECREF(item);
                    PyErr_Format(PyExc_TypeError, 
                        "UICollection can only contain Frame, Caption, Sprite, and Grid objects; "
                        "got %s at index %zd", Py_TYPE(item)->tp_name, i);
                    return -1;
                }
                
                Py_DECREF(item);
                new_items.push_back(drawable);
            }
            
            // Now perform the assignment
            if (step == 1) {
                // Contiguous slice
                if (slicelength != value_len) {
                    // Need to resize
                    auto it_start = self->data->begin() + start;
                    auto it_stop = self->data->begin() + stop;
                    self->data->erase(it_start, it_stop);
                    self->data->insert(self->data->begin() + start, new_items.begin(), new_items.end());
                } else {
                    // Same size, just replace
                    for (Py_ssize_t i = 0; i < slicelength; i++) {
                        // Preserve z_index
                        new_items[i]->z_index = (*self->data)[start + i]->z_index;
                        (*self->data)[start + i] = new_items[i];
                    }
                }
            } else {
                // Extended slice
                if (slicelength != value_len) {
                    PyErr_Format(PyExc_ValueError,
                        "attempt to assign sequence of size %zd to extended slice of size %zd",
                        value_len, slicelength);
                    return -1;
                }
                for (Py_ssize_t i = 0, cur = start; i < slicelength; i++, cur += step) {
                    // Preserve z_index
                    new_items[i]->z_index = (*self->data)[cur]->z_index;
                    (*self->data)[cur] = new_items[i];
                }
            }
            
            // Mark scene as needing resort after slice assignment
            McRFPy_API::markSceneNeedsSort();
            
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

/* Idiomatic way to fetch complete types from the API rather than referencing their PyTypeObject struct

auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Texture");

I never identified why `using namespace mcrfpydef;` doesn't solve the segfault issue.
The horrible macro in UIDrawable was originally a workaround for this, but as I interact with the types outside of the monster UI.h, a more general (and less icky) solution is required.

*/

PyObject* UICollection::append(PyUICollectionObject* self, PyObject* o)
{
	// if not UIDrawable subclass, reject it
	// self->data->push_back( c++ object inside o );

    // Ensure module is initialized
    if (!McRFPy_API::mcrf_module) {
        PyErr_SetString(PyExc_RuntimeError, "mcrfpy module not initialized");
        return NULL;
    }

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

    // Calculate z_index for the new element
    int new_z_index = 0;
    if (!self->data->empty()) {
        // Get the z_index of the last element and add 10
        int last_z = self->data->back()->z_index;
        if (last_z <= INT_MAX - 10) {
            new_z_index = last_z + 10;
        } else {
            new_z_index = INT_MAX;
        }
    }

    if (PyObject_IsInstance(o, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Frame")))
    {
        PyUIFrameObject* frame = (PyUIFrameObject*)o;
        frame->data->z_index = new_z_index;
        self->data->push_back(frame->data);
    }
    if (PyObject_IsInstance(o, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Caption")))
    {
        PyUICaptionObject* caption = (PyUICaptionObject*)o;
        caption->data->z_index = new_z_index;
        self->data->push_back(caption->data);
    }
    if (PyObject_IsInstance(o, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Sprite")))
    {
        PyUISpriteObject* sprite = (PyUISpriteObject*)o;
        sprite->data->z_index = new_z_index;
        self->data->push_back(sprite->data);
    }
    if (PyObject_IsInstance(o, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Grid")))
    {
        PyUIGridObject* grid = (PyUIGridObject*)o;
        grid->data->z_index = new_z_index;
        self->data->push_back(grid->data);
    }
    
    // Mark scene as needing resort after adding element
    McRFPy_API::markSceneNeedsSort();

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
    
    // Ensure module is initialized
    if (!McRFPy_API::mcrf_module) {
        Py_DECREF(iterator);
        PyErr_SetString(PyExc_RuntimeError, "mcrfpy module not initialized");
        return NULL;
    }
    
    // Get current highest z_index
    int current_z_index = 0;
    if (!self->data->empty()) {
        current_z_index = self->data->back()->z_index;
    }
    
    PyObject* item;
    while ((item = PyIter_Next(iterator)) != NULL) {
        // Check if item is a UIDrawable subclass
        if (!PyObject_IsInstance(item, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Frame")) &&
            !PyObject_IsInstance(item, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Sprite")) &&
            !PyObject_IsInstance(item, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Caption")) &&
            !PyObject_IsInstance(item, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Grid")))
        {
            Py_DECREF(item);
            Py_DECREF(iterator);
            PyErr_SetString(PyExc_TypeError, "All items must be Frame, Caption, Sprite, or Grid objects");
            return NULL;
        }
        
        // Increment z_index for each new element
        if (current_z_index <= INT_MAX - 10) {
            current_z_index += 10;
        } else {
            current_z_index = INT_MAX;
        }
        
        // Add the item based on its type
        if (PyObject_IsInstance(item, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Frame"))) {
            PyUIFrameObject* frame = (PyUIFrameObject*)item;
            frame->data->z_index = current_z_index;
            self->data->push_back(frame->data);
        }
        else if (PyObject_IsInstance(item, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Caption"))) {
            PyUICaptionObject* caption = (PyUICaptionObject*)item;
            caption->data->z_index = current_z_index;
            self->data->push_back(caption->data);
        }
        else if (PyObject_IsInstance(item, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Sprite"))) {
            PyUISpriteObject* sprite = (PyUISpriteObject*)item;
            sprite->data->z_index = current_z_index;
            self->data->push_back(sprite->data);
        }
        else if (PyObject_IsInstance(item, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Grid"))) {
            PyUIGridObject* grid = (PyUIGridObject*)item;
            grid->data->z_index = current_z_index;
            self->data->push_back(grid->data);
        }
        
        Py_DECREF(item);
    }
    
    Py_DECREF(iterator);
    
    // Check if iteration ended due to an error
    if (PyErr_Occurred()) {
        return NULL;
    }
    
    // Mark scene as needing resort after adding elements
    McRFPy_API::markSceneNeedsSort();
    
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
	
	// Handle negative indexing
	while (index < 0) index += self->data->size();
	
	if (index >= self->data->size())
    {
        PyErr_SetString(PyExc_ValueError, "Index out of range");
        return NULL;
    }

	// release the shared pointer at self->data[index];
    self->data->erase(self->data->begin() + index);
    
    // Mark scene as needing resort after removing element
    McRFPy_API::markSceneNeedsSort();
    
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* UICollection::index_method(PyUICollectionObject* self, PyObject* value) {
    auto vec = self->data.get();
    if (!vec) {
        PyErr_SetString(PyExc_RuntimeError, "the collection store returned a null pointer");
        return NULL;
    }
    
    // Type checking - must be a UIDrawable subclass
    if (!PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Frame")) &&
        !PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Sprite")) &&
        !PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Caption")) &&
        !PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Grid"))) {
        PyErr_SetString(PyExc_TypeError, "UICollection.index requires a Frame, Caption, Sprite, or Grid object");
        return NULL;
    }
    
    // Get the C++ object from the Python object
    std::shared_ptr<UIDrawable> search_drawable = nullptr;
    
    if (PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Frame"))) {
        search_drawable = ((PyUIFrameObject*)value)->data;
    } else if (PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Caption"))) {
        search_drawable = ((PyUICaptionObject*)value)->data;
    } else if (PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Sprite"))) {
        search_drawable = ((PyUISpriteObject*)value)->data;
    } else if (PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Grid"))) {
        search_drawable = ((PyUIGridObject*)value)->data;
    }
    
    if (!search_drawable) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to extract C++ object from Python object");
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
    
    // Type checking - must be a UIDrawable subclass
    if (!PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Frame")) &&
        !PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Sprite")) &&
        !PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Caption")) &&
        !PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Grid"))) {
        // Not a valid type, so count is 0
        return PyLong_FromLong(0);
    }
    
    // Get the C++ object from the Python object
    std::shared_ptr<UIDrawable> search_drawable = nullptr;
    
    if (PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Frame"))) {
        search_drawable = ((PyUIFrameObject*)value)->data;
    } else if (PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Caption"))) {
        search_drawable = ((PyUICaptionObject*)value)->data;
    } else if (PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Sprite"))) {
        search_drawable = ((PyUISpriteObject*)value)->data;
    } else if (PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Grid"))) {
        search_drawable = ((PyUIGridObject*)value)->data;
    }
    
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

PyMethodDef UICollection::methods[] = {
	{"append", (PyCFunction)UICollection::append, METH_O},
	{"extend", (PyCFunction)UICollection::extend, METH_O},
	{"remove", (PyCFunction)UICollection::remove, METH_O},
	{"index", (PyCFunction)UICollection::index_method, METH_O},
	{"count", (PyCFunction)UICollection::count, METH_O},
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
	        switch(item->derived_type()) {
	            case PyObjectsEnum::UIFRAME: frame_count++; break;
	            case PyObjectsEnum::UICAPTION: caption_count++; break;
	            case PyObjectsEnum::UISPRITE: sprite_count++; break;
	            case PyObjectsEnum::UIGRID: grid_count++; break;
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
