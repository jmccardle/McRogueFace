#include "PyAnimation.h"
#include "McRFPy_API.h"
#include "UIDrawable.h"
#include "UIFrame.h"
#include "UICaption.h"
#include "UISprite.h"
#include "UIGrid.h"
#include "UIEntity.h"
#include "UI.h"  // For the PyTypeObject definitions
#include <cstring>

PyObject* PyAnimation::create(PyTypeObject* type, PyObject* args, PyObject* kwds) {
    PyAnimationObject* self = (PyAnimationObject*)type->tp_alloc(type, 0);
    if (self != NULL) {
        // Will be initialized in init
    }
    return (PyObject*)self;
}

int PyAnimation::init(PyAnimationObject* self, PyObject* args, PyObject* kwds) {
    static const char* keywords[] = {"property", "target", "duration", "easing", "delta", "callback", nullptr};
    
    const char* property_name;
    PyObject* target_value;
    float duration;
    const char* easing_name = "linear";
    int delta = 0;
    PyObject* callback = nullptr;
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "sOf|spO", const_cast<char**>(keywords),
                                      &property_name, &target_value, &duration, &easing_name, &delta, &callback)) {
        return -1;
    }
    
    // Validate callback is callable if provided
    if (callback && callback != Py_None && !PyCallable_Check(callback)) {
        PyErr_SetString(PyExc_TypeError, "callback must be callable");
        return -1;
    }
    
    // Convert None to nullptr for C++
    if (callback == Py_None) {
        callback = nullptr;
    }
    
    // Convert Python target value to AnimationValue
    AnimationValue animValue;
    
    if (PyFloat_Check(target_value)) {
        animValue = static_cast<float>(PyFloat_AsDouble(target_value));
    }
    else if (PyLong_Check(target_value)) {
        animValue = static_cast<int>(PyLong_AsLong(target_value));
    }
    else if (PyList_Check(target_value)) {
        // List of integers for sprite animation
        std::vector<int> indices;
        Py_ssize_t size = PyList_Size(target_value);
        for (Py_ssize_t i = 0; i < size; i++) {
            PyObject* item = PyList_GetItem(target_value, i);
            if (PyLong_Check(item)) {
                indices.push_back(PyLong_AsLong(item));
            } else {
                PyErr_SetString(PyExc_TypeError, "Sprite animation list must contain only integers");
                return -1;
            }
        }
        animValue = indices;
    }
    else if (PyTuple_Check(target_value)) {
        Py_ssize_t size = PyTuple_Size(target_value);
        if (size == 2) {
            // Vector2f
            float x = PyFloat_AsDouble(PyTuple_GetItem(target_value, 0));
            float y = PyFloat_AsDouble(PyTuple_GetItem(target_value, 1));
            animValue = sf::Vector2f(x, y);
        }
        else if (size == 3 || size == 4) {
            // Color (RGB or RGBA)
            int r = PyLong_AsLong(PyTuple_GetItem(target_value, 0));
            int g = PyLong_AsLong(PyTuple_GetItem(target_value, 1));
            int b = PyLong_AsLong(PyTuple_GetItem(target_value, 2));
            int a = size == 4 ? PyLong_AsLong(PyTuple_GetItem(target_value, 3)) : 255;
            animValue = sf::Color(r, g, b, a);
        }
        else {
            PyErr_SetString(PyExc_ValueError, "Tuple must have 2 elements (vector) or 3-4 elements (color)");
            return -1;
        }
    }
    else if (PyUnicode_Check(target_value)) {
        // String for text animation
        const char* str = PyUnicode_AsUTF8(target_value);
        animValue = std::string(str);
    }
    else {
        PyErr_SetString(PyExc_TypeError, "Target value must be float, int, list, tuple, or string");
        return -1;
    }
    
    // Get easing function
    EasingFunction easingFunc = EasingFunctions::getByName(easing_name);
    
    // Create the Animation
    self->data = std::make_shared<Animation>(property_name, animValue, duration, easingFunc, delta != 0, callback);
    
    return 0;
}

void PyAnimation::dealloc(PyAnimationObject* self) {
    self->data.reset();
    Py_TYPE(self)->tp_free((PyObject*)self);
}

PyObject* PyAnimation::get_property(PyAnimationObject* self, void* closure) {
    return PyUnicode_FromString(self->data->getTargetProperty().c_str());
}

PyObject* PyAnimation::get_duration(PyAnimationObject* self, void* closure) {
    return PyFloat_FromDouble(self->data->getDuration());
}

PyObject* PyAnimation::get_elapsed(PyAnimationObject* self, void* closure) {
    return PyFloat_FromDouble(self->data->getElapsed());
}

PyObject* PyAnimation::get_is_complete(PyAnimationObject* self, void* closure) {
    return PyBool_FromLong(self->data->isComplete());
}

PyObject* PyAnimation::get_is_delta(PyAnimationObject* self, void* closure) {
    return PyBool_FromLong(self->data->isDelta());
}

PyObject* PyAnimation::start(PyAnimationObject* self, PyObject* args) {
    PyObject* target_obj;
    if (!PyArg_ParseTuple(args, "O", &target_obj)) {
        return NULL;
    }
    
    // Get type objects from the module to ensure they're initialized
    PyObject* frame_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "Frame");
    PyObject* caption_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "Caption");
    PyObject* sprite_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "Sprite");
    PyObject* grid_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "Grid");
    PyObject* entity_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity");
    
    bool handled = false;
    
    // Use PyObject_IsInstance to support inheritance
    if (frame_type && PyObject_IsInstance(target_obj, frame_type)) {
        PyUIFrameObject* frame = (PyUIFrameObject*)target_obj;
        if (frame->data) {
            self->data->start(frame->data);
            AnimationManager::getInstance().addAnimation(self->data);
            handled = true;
        }
    }
    else if (caption_type && PyObject_IsInstance(target_obj, caption_type)) {
        PyUICaptionObject* caption = (PyUICaptionObject*)target_obj;
        if (caption->data) {
            self->data->start(caption->data);
            AnimationManager::getInstance().addAnimation(self->data);
            handled = true;
        }
    }
    else if (sprite_type && PyObject_IsInstance(target_obj, sprite_type)) {
        PyUISpriteObject* sprite = (PyUISpriteObject*)target_obj;
        if (sprite->data) {
            self->data->start(sprite->data);
            AnimationManager::getInstance().addAnimation(self->data);
            handled = true;
        }
    }
    else if (grid_type && PyObject_IsInstance(target_obj, grid_type)) {
        PyUIGridObject* grid = (PyUIGridObject*)target_obj;
        if (grid->data) {
            self->data->start(grid->data);
            AnimationManager::getInstance().addAnimation(self->data);
            handled = true;
        }
    }
    else if (entity_type && PyObject_IsInstance(target_obj, entity_type)) {
        // Special handling for Entity since it doesn't inherit from UIDrawable
        PyUIEntityObject* entity = (PyUIEntityObject*)target_obj;
        if (entity->data) {
            self->data->startEntity(entity->data);
            AnimationManager::getInstance().addAnimation(self->data);
            handled = true;
        }
    }
    
    // Clean up references
    Py_XDECREF(frame_type);
    Py_XDECREF(caption_type);
    Py_XDECREF(sprite_type);
    Py_XDECREF(grid_type);
    Py_XDECREF(entity_type);
    
    if (!handled) {
        PyErr_SetString(PyExc_TypeError, "Target must be a Frame, Caption, Sprite, Grid, or Entity (or a subclass of these)");
        return NULL;
    }
    
    Py_RETURN_NONE;
}

PyObject* PyAnimation::update(PyAnimationObject* self, PyObject* args) {
    float deltaTime;
    if (!PyArg_ParseTuple(args, "f", &deltaTime)) {
        return NULL;
    }
    
    bool still_running = self->data->update(deltaTime);
    return PyBool_FromLong(still_running);
}

PyObject* PyAnimation::get_current_value(PyAnimationObject* self, PyObject* args) {
    AnimationValue value = self->data->getCurrentValue();
    
    // Convert AnimationValue back to Python
    return std::visit([](const auto& val) -> PyObject* {
        using T = std::decay_t<decltype(val)>;
        
        if constexpr (std::is_same_v<T, float>) {
            return PyFloat_FromDouble(val);
        }
        else if constexpr (std::is_same_v<T, int>) {
            return PyLong_FromLong(val);
        }
        else if constexpr (std::is_same_v<T, std::vector<int>>) {
            // This shouldn't happen as we interpolate to int
            return PyLong_FromLong(0);
        }
        else if constexpr (std::is_same_v<T, sf::Color>) {
            return Py_BuildValue("(iiii)", val.r, val.g, val.b, val.a);
        }
        else if constexpr (std::is_same_v<T, sf::Vector2f>) {
            return Py_BuildValue("(ff)", val.x, val.y);
        }
        else if constexpr (std::is_same_v<T, std::string>) {
            return PyUnicode_FromString(val.c_str());
        }
        
        Py_RETURN_NONE;
    }, value);
}

PyObject* PyAnimation::complete(PyAnimationObject* self, PyObject* args) {
    if (self->data) {
        self->data->complete();
    }
    Py_RETURN_NONE;
}

PyObject* PyAnimation::has_valid_target(PyAnimationObject* self, PyObject* args) {
    if (self->data && self->data->hasValidTarget()) {
        Py_RETURN_TRUE;
    }
    Py_RETURN_FALSE;
}

PyGetSetDef PyAnimation::getsetters[] = {
    {"property", (getter)get_property, NULL, "Target property name", NULL},
    {"duration", (getter)get_duration, NULL, "Animation duration in seconds", NULL},
    {"elapsed", (getter)get_elapsed, NULL, "Elapsed time in seconds", NULL},
    {"is_complete", (getter)get_is_complete, NULL, "Whether animation is complete", NULL},
    {"is_delta", (getter)get_is_delta, NULL, "Whether animation uses delta mode", NULL},
    {NULL}
};

PyMethodDef PyAnimation::methods[] = {
    {"start", (PyCFunction)start, METH_VARARGS,
     "start(target) -> None\n\n"
     "Start the animation on a target UI element.\n\n"
     "Args:\n"
     "    target: The UI element to animate (Frame, Caption, Sprite, Grid, or Entity)\n\n"
     "Note:\n"
     "    The animation will automatically stop if the target is destroyed."},
    {"update", (PyCFunction)update, METH_VARARGS,
     "Update the animation by deltaTime (returns True if still running)"},
    {"get_current_value", (PyCFunction)get_current_value, METH_NOARGS,
     "Get the current interpolated value"},
    {"complete", (PyCFunction)complete, METH_NOARGS,
     "complete() -> None\n\n"
     "Complete the animation immediately by jumping to the final value."},
    {"hasValidTarget", (PyCFunction)has_valid_target, METH_NOARGS,
     "hasValidTarget() -> bool\n\n"
     "Check if the animation still has a valid target.\n\n"
     "Returns:\n"
     "    True if the target still exists, False if it was destroyed."},
    {NULL}
};