#include "PyUniformBinding.h"
#include "UIDrawable.h"
#include "UIFrame.h"
#include "UICaption.h"
#include "UISprite.h"
#include "UIGrid.h"
#include "UILine.h"
#include "UICircle.h"
#include "UIArc.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"
#include <sstream>
#include <cstring>

// ============================================================================
// PropertyBinding Implementation
// ============================================================================

PropertyBinding::PropertyBinding(std::weak_ptr<UIDrawable> target, const std::string& property)
    : target(target), property_name(property) {}

std::optional<float> PropertyBinding::evaluate() const {
    auto ptr = target.lock();
    if (!ptr) return std::nullopt;

    float value = 0.0f;
    if (ptr->getProperty(property_name, value)) {
        return value;
    }
    return std::nullopt;
}

bool PropertyBinding::isValid() const {
    auto ptr = target.lock();
    if (!ptr) return false;
    return ptr->hasProperty(property_name);
}

// ============================================================================
// CallableBinding Implementation
// ============================================================================

CallableBinding::CallableBinding(PyObject* callable)
    : callable(callable) {
    if (callable) {
        Py_INCREF(callable);
    }
}

CallableBinding::~CallableBinding() {
    if (callable) {
        Py_DECREF(callable);
    }
}

CallableBinding::CallableBinding(CallableBinding&& other) noexcept
    : callable(other.callable) {
    other.callable = nullptr;
}

CallableBinding& CallableBinding::operator=(CallableBinding&& other) noexcept {
    if (this != &other) {
        if (callable) {
            Py_DECREF(callable);
        }
        callable = other.callable;
        other.callable = nullptr;
    }
    return *this;
}

std::optional<float> CallableBinding::evaluate() const {
    if (!callable || !PyCallable_Check(callable)) {
        return std::nullopt;
    }

    PyObject* result = PyObject_CallNoArgs(callable);
    if (!result) {
        // Python exception occurred - print and clear it
        PyErr_Print();
        return std::nullopt;
    }

    float value = 0.0f;
    if (PyFloat_Check(result)) {
        value = static_cast<float>(PyFloat_AsDouble(result));
    } else if (PyLong_Check(result)) {
        value = static_cast<float>(PyLong_AsDouble(result));
    } else {
        // Try to convert to float
        PyObject* float_result = PyNumber_Float(result);
        if (float_result) {
            value = static_cast<float>(PyFloat_AsDouble(float_result));
            Py_DECREF(float_result);
        } else {
            PyErr_Clear();
            Py_DECREF(result);
            return std::nullopt;
        }
    }

    Py_DECREF(result);
    return value;
}

bool CallableBinding::isValid() const {
    return callable && PyCallable_Check(callable);
}

// ============================================================================
// PyPropertyBindingType Python Interface
// ============================================================================

PyGetSetDef PyPropertyBindingType::getsetters[] = {
    {"target", (getter)PyPropertyBindingType::get_target, NULL,
     MCRF_PROPERTY(target, "The drawable this binding reads from (read-only)."), NULL},
    {"property", (getter)PyPropertyBindingType::get_property, NULL,
     MCRF_PROPERTY(property, "The property name being read (str, read-only)."), NULL},
    {"value", (getter)PyPropertyBindingType::get_value, NULL,
     MCRF_PROPERTY(value, "Current value of the binding (float, read-only). Returns None if invalid."), NULL},
    {"is_valid", (getter)PyPropertyBindingType::is_valid, NULL,
     MCRF_PROPERTY(is_valid, "True if the binding target still exists and property is valid (bool, read-only)."), NULL},
    {NULL}
};

PyObject* PyPropertyBindingType::pynew(PyTypeObject* type, PyObject* args, PyObject* kwds) {
    PyPropertyBindingObject* self = (PyPropertyBindingObject*)type->tp_alloc(type, 0);
    if (self) {
        self->binding = nullptr;
        self->weakreflist = NULL;
    }
    return (PyObject*)self;
}

void PyPropertyBindingType::dealloc(PyPropertyBindingObject* self) {
    if (self->weakreflist) {
        PyObject_ClearWeakRefs((PyObject*)self);
    }
    self->binding.reset();
    Py_TYPE(self)->tp_free((PyObject*)self);
}

int PyPropertyBindingType::init(PyPropertyBindingObject* self, PyObject* args, PyObject* kwds) {
    static const char* keywords[] = {"target", "property", nullptr};
    PyObject* target_obj = nullptr;
    const char* property = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "Os", const_cast<char**>(keywords),
                                     &target_obj, &property)) {
        return -1;
    }

    // Get the shared_ptr from the target drawable by checking the type name
    // We can't use PyObject_IsInstance with static type objects from other translation units
    // So we check the type name string instead
    std::shared_ptr<UIDrawable> target_ptr;
    const char* type_name = Py_TYPE(target_obj)->tp_name;

    if (strcmp(type_name, "mcrfpy.Frame") == 0) {
        target_ptr = ((PyUIFrameObject*)target_obj)->data;
    } else if (strcmp(type_name, "mcrfpy.Caption") == 0) {
        target_ptr = ((PyUICaptionObject*)target_obj)->data;
    } else if (strcmp(type_name, "mcrfpy.Sprite") == 0) {
        target_ptr = ((PyUISpriteObject*)target_obj)->data;
    } else if (strcmp(type_name, "mcrfpy.Grid") == 0) {
        target_ptr = ((PyUIGridObject*)target_obj)->data;
    } else if (strcmp(type_name, "mcrfpy.Line") == 0) {
        target_ptr = ((PyUILineObject*)target_obj)->data;
    } else if (strcmp(type_name, "mcrfpy.Circle") == 0) {
        target_ptr = ((PyUICircleObject*)target_obj)->data;
    } else if (strcmp(type_name, "mcrfpy.Arc") == 0) {
        target_ptr = ((PyUIArcObject*)target_obj)->data;
    }

    if (!target_ptr) {
        PyErr_SetString(PyExc_TypeError,
            "PropertyBinding requires a UIDrawable (Frame, Sprite, Caption, Grid, Line, Circle, or Arc)");
        return -1;
    }

    // Validate that the property exists
    if (!target_ptr->hasProperty(property)) {
        PyErr_Format(PyExc_ValueError,
            "Property '%s' is not a valid animatable property on this drawable", property);
        return -1;
    }

    self->binding = std::make_shared<PropertyBinding>(target_ptr, property);
    return 0;
}

PyObject* PyPropertyBindingType::repr(PyObject* obj) {
    PyPropertyBindingObject* self = (PyPropertyBindingObject*)obj;
    std::ostringstream ss;
    ss << "<PropertyBinding";
    if (self->binding) {
        ss << " property='" << self->binding->getPropertyName() << "'";
        if (self->binding->isValid()) {
            auto val = self->binding->evaluate();
            if (val) {
                ss << " value=" << *val;
            }
        } else {
            ss << " (invalid)";
        }
    }
    ss << ">";
    return PyUnicode_FromString(ss.str().c_str());
}

PyObject* PyPropertyBindingType::get_target(PyPropertyBindingObject* self, void* closure) {
    if (!self->binding) {
        Py_RETURN_NONE;
    }
    auto ptr = self->binding->getTarget().lock();
    if (!ptr) {
        Py_RETURN_NONE;
    }
    // TODO: Return the actual Python object for the drawable
    Py_RETURN_NONE;
}

PyObject* PyPropertyBindingType::get_property(PyPropertyBindingObject* self, void* closure) {
    if (!self->binding) {
        Py_RETURN_NONE;
    }
    return PyUnicode_FromString(self->binding->getPropertyName().c_str());
}

PyObject* PyPropertyBindingType::get_value(PyPropertyBindingObject* self, void* closure) {
    if (!self->binding) {
        Py_RETURN_NONE;
    }
    auto val = self->binding->evaluate();
    if (!val) {
        Py_RETURN_NONE;
    }
    return PyFloat_FromDouble(*val);
}

PyObject* PyPropertyBindingType::is_valid(PyPropertyBindingObject* self, void* closure) {
    if (!self->binding) {
        Py_RETURN_FALSE;
    }
    return PyBool_FromLong(self->binding->isValid());
}

// ============================================================================
// PyCallableBindingType Python Interface
// ============================================================================

PyGetSetDef PyCallableBindingType::getsetters[] = {
    {"callable", (getter)PyCallableBindingType::get_callable, NULL,
     MCRF_PROPERTY(callable, "The Python callable (read-only)."), NULL},
    {"value", (getter)PyCallableBindingType::get_value, NULL,
     MCRF_PROPERTY(value, "Current value from calling the callable (float, read-only). Returns None on error."), NULL},
    {"is_valid", (getter)PyCallableBindingType::is_valid, NULL,
     MCRF_PROPERTY(is_valid, "True if the callable is still valid (bool, read-only)."), NULL},
    {NULL}
};

PyObject* PyCallableBindingType::pynew(PyTypeObject* type, PyObject* args, PyObject* kwds) {
    PyCallableBindingObject* self = (PyCallableBindingObject*)type->tp_alloc(type, 0);
    if (self) {
        self->binding = nullptr;
        self->weakreflist = NULL;
    }
    return (PyObject*)self;
}

void PyCallableBindingType::dealloc(PyCallableBindingObject* self) {
    if (self->weakreflist) {
        PyObject_ClearWeakRefs((PyObject*)self);
    }
    self->binding.reset();
    Py_TYPE(self)->tp_free((PyObject*)self);
}

int PyCallableBindingType::init(PyCallableBindingObject* self, PyObject* args, PyObject* kwds) {
    static const char* keywords[] = {"callable", nullptr};
    PyObject* callable = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O", const_cast<char**>(keywords),
                                     &callable)) {
        return -1;
    }

    if (!PyCallable_Check(callable)) {
        PyErr_SetString(PyExc_TypeError, "Argument must be callable");
        return -1;
    }

    self->binding = std::make_shared<CallableBinding>(callable);
    return 0;
}

PyObject* PyCallableBindingType::repr(PyObject* obj) {
    PyCallableBindingObject* self = (PyCallableBindingObject*)obj;
    std::ostringstream ss;
    ss << "<CallableBinding";
    if (self->binding && self->binding->isValid()) {
        auto val = self->binding->evaluate();
        if (val) {
            ss << " value=" << *val;
        }
    } else {
        ss << " (invalid)";
    }
    ss << ">";
    return PyUnicode_FromString(ss.str().c_str());
}

PyObject* PyCallableBindingType::get_callable(PyCallableBindingObject* self, void* closure) {
    if (!self->binding) {
        Py_RETURN_NONE;
    }
    PyObject* callable = self->binding->getCallable();
    if (!callable) {
        Py_RETURN_NONE;
    }
    Py_INCREF(callable);
    return callable;
}

PyObject* PyCallableBindingType::get_value(PyCallableBindingObject* self, void* closure) {
    if (!self->binding) {
        Py_RETURN_NONE;
    }
    auto val = self->binding->evaluate();
    if (!val) {
        Py_RETURN_NONE;
    }
    return PyFloat_FromDouble(*val);
}

PyObject* PyCallableBindingType::is_valid(PyCallableBindingObject* self, void* closure) {
    if (!self->binding) {
        Py_RETURN_FALSE;
    }
    return PyBool_FromLong(self->binding->isValid());
}
