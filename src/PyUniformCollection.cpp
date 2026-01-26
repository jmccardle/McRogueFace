#include "PyUniformCollection.h"
#include "UIDrawable.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"
#include <sstream>

// ============================================================================
// UniformCollection Implementation
// ============================================================================

void UniformCollection::setFloat(const std::string& name, float value) {
    entries[name] = UniformValue(value);
}

void UniformCollection::setVec2(const std::string& name, float x, float y) {
    entries[name] = UniformValue(sf::Glsl::Vec2(x, y));
}

void UniformCollection::setVec3(const std::string& name, float x, float y, float z) {
    entries[name] = UniformValue(sf::Glsl::Vec3(x, y, z));
}

void UniformCollection::setVec4(const std::string& name, float x, float y, float z, float w) {
    entries[name] = UniformValue(sf::Glsl::Vec4(x, y, z, w));
}

void UniformCollection::setPropertyBinding(const std::string& name, std::shared_ptr<PropertyBinding> binding) {
    entries[name] = binding;
}

void UniformCollection::setCallableBinding(const std::string& name, std::shared_ptr<CallableBinding> binding) {
    entries[name] = binding;
}

void UniformCollection::remove(const std::string& name) {
    entries.erase(name);
}

bool UniformCollection::contains(const std::string& name) const {
    return entries.find(name) != entries.end();
}

std::vector<std::string> UniformCollection::getNames() const {
    std::vector<std::string> names;
    names.reserve(entries.size());
    for (const auto& [name, _] : entries) {
        names.push_back(name);
    }
    return names;
}

void UniformCollection::applyTo(sf::Shader& shader) const {
    for (const auto& [name, entry] : entries) {
        std::visit([&shader, &name](auto&& arg) {
            using T = std::decay_t<decltype(arg)>;

            if constexpr (std::is_same_v<T, UniformValue>) {
                // Static value
                std::visit([&shader, &name](auto&& val) {
                    using V = std::decay_t<decltype(val)>;
                    if constexpr (std::is_same_v<V, float>) {
                        shader.setUniform(name, val);
                    } else if constexpr (std::is_same_v<V, sf::Glsl::Vec2>) {
                        shader.setUniform(name, val);
                    } else if constexpr (std::is_same_v<V, sf::Glsl::Vec3>) {
                        shader.setUniform(name, val);
                    } else if constexpr (std::is_same_v<V, sf::Glsl::Vec4>) {
                        shader.setUniform(name, val);
                    }
                }, arg);
            }
            else if constexpr (std::is_same_v<T, std::shared_ptr<PropertyBinding>>) {
                // Property binding - evaluate and apply
                if (arg && arg->isValid()) {
                    auto val = arg->evaluate();
                    if (val) {
                        shader.setUniform(name, *val);
                    }
                }
            }
            else if constexpr (std::is_same_v<T, std::shared_ptr<CallableBinding>>) {
                // Callable binding - evaluate and apply
                if (arg && arg->isValid()) {
                    auto val = arg->evaluate();
                    if (val) {
                        shader.setUniform(name, *val);
                    }
                }
            }
        }, entry);
    }
}

bool UniformCollection::hasDynamicBindings() const {
    for (const auto& [_, entry] : entries) {
        if (std::holds_alternative<std::shared_ptr<CallableBinding>>(entry)) {
            return true;
        }
    }
    return false;
}

const UniformEntry* UniformCollection::getEntry(const std::string& name) const {
    auto it = entries.find(name);
    if (it == entries.end()) return nullptr;
    return &it->second;
}

// ============================================================================
// PyUniformCollectionType Python Interface
// ============================================================================

PyMethodDef PyUniformCollectionType::methods[] = {
    {"keys", (PyCFunction)PyUniformCollectionType::keys, METH_NOARGS,
     "Return list of uniform names"},
    {"values", (PyCFunction)PyUniformCollectionType::values, METH_NOARGS,
     "Return list of uniform values"},
    {"items", (PyCFunction)PyUniformCollectionType::items, METH_NOARGS,
     "Return list of (name, value) tuples"},
    {"clear", (PyCFunction)PyUniformCollectionType::clear, METH_NOARGS,
     "Remove all uniforms"},
    {NULL}
};

PyMappingMethods PyUniformCollectionType::mapping_methods = {
    .mp_length = PyUniformCollectionType::mp_length,
    .mp_subscript = PyUniformCollectionType::mp_subscript,
    .mp_ass_subscript = PyUniformCollectionType::mp_ass_subscript,
};

PySequenceMethods PyUniformCollectionType::sequence_methods = {
    .sq_length = nullptr,
    .sq_concat = nullptr,
    .sq_repeat = nullptr,
    .sq_item = nullptr,
    .was_sq_slice = nullptr,
    .sq_ass_item = nullptr,
    .was_sq_ass_slice = nullptr,
    .sq_contains = PyUniformCollectionType::sq_contains,
};

void PyUniformCollectionType::dealloc(PyUniformCollectionObject* self) {
    if (self->weakreflist) {
        PyObject_ClearWeakRefs((PyObject*)self);
    }
    // Don't delete collection - it's owned by UIDrawable
    Py_TYPE(self)->tp_free((PyObject*)self);
}

PyObject* PyUniformCollectionType::repr(PyObject* obj) {
    PyUniformCollectionObject* self = (PyUniformCollectionObject*)obj;
    std::ostringstream ss;
    ss << "<UniformCollection";
    if (self->collection) {
        auto names = self->collection->getNames();
        ss << " [";
        for (size_t i = 0; i < names.size(); ++i) {
            if (i > 0) ss << ", ";
            ss << "'" << names[i] << "'";
        }
        ss << "]";
    }
    ss << ">";
    return PyUnicode_FromString(ss.str().c_str());
}

Py_ssize_t PyUniformCollectionType::mp_length(PyObject* obj) {
    PyUniformCollectionObject* self = (PyUniformCollectionObject*)obj;
    if (!self->collection) return 0;
    return static_cast<Py_ssize_t>(self->collection->getNames().size());
}

PyObject* PyUniformCollectionType::mp_subscript(PyObject* obj, PyObject* key) {
    PyUniformCollectionObject* self = (PyUniformCollectionObject*)obj;

    if (!self->collection) {
        PyErr_SetString(PyExc_RuntimeError, "UniformCollection is not valid");
        return NULL;
    }

    if (!PyUnicode_Check(key)) {
        PyErr_SetString(PyExc_TypeError, "Uniform name must be a string");
        return NULL;
    }

    const char* name = PyUnicode_AsUTF8(key);
    const UniformEntry* entry = self->collection->getEntry(name);

    if (!entry) {
        PyErr_Format(PyExc_KeyError, "'%s'", name);
        return NULL;
    }

    // Convert entry to Python object
    return std::visit([](auto&& arg) -> PyObject* {
        using T = std::decay_t<decltype(arg)>;

        if constexpr (std::is_same_v<T, UniformValue>) {
            return std::visit([](auto&& val) -> PyObject* {
                using V = std::decay_t<decltype(val)>;
                if constexpr (std::is_same_v<V, float>) {
                    return PyFloat_FromDouble(val);
                } else if constexpr (std::is_same_v<V, sf::Glsl::Vec2>) {
                    return Py_BuildValue("(ff)", val.x, val.y);
                } else if constexpr (std::is_same_v<V, sf::Glsl::Vec3>) {
                    return Py_BuildValue("(fff)", val.x, val.y, val.z);
                } else if constexpr (std::is_same_v<V, sf::Glsl::Vec4>) {
                    return Py_BuildValue("(ffff)", val.x, val.y, val.z, val.w);
                }
                Py_RETURN_NONE;
            }, arg);
        }
        else if constexpr (std::is_same_v<T, std::shared_ptr<PropertyBinding>>) {
            // Return the current value for now
            // TODO: Return the actual PropertyBinding object
            if (arg && arg->isValid()) {
                auto val = arg->evaluate();
                if (val) {
                    return PyFloat_FromDouble(*val);
                }
            }
            Py_RETURN_NONE;
        }
        else if constexpr (std::is_same_v<T, std::shared_ptr<CallableBinding>>) {
            // Return the current value for now
            // TODO: Return the actual CallableBinding object
            if (arg && arg->isValid()) {
                auto val = arg->evaluate();
                if (val) {
                    return PyFloat_FromDouble(*val);
                }
            }
            Py_RETURN_NONE;
        }
        Py_RETURN_NONE;
    }, *entry);
}

int PyUniformCollectionType::mp_ass_subscript(PyObject* obj, PyObject* key, PyObject* value) {
    PyUniformCollectionObject* self = (PyUniformCollectionObject*)obj;

    if (!self->collection) {
        PyErr_SetString(PyExc_RuntimeError, "UniformCollection is not valid");
        return -1;
    }

    if (!PyUnicode_Check(key)) {
        PyErr_SetString(PyExc_TypeError, "Uniform name must be a string");
        return -1;
    }

    const char* name = PyUnicode_AsUTF8(key);

    // Delete operation
    if (value == NULL) {
        self->collection->remove(name);
        return 0;
    }

    // Check for binding types first
    // PropertyBinding
    if (PyObject_IsInstance(value, (PyObject*)&mcrfpydef::PyPropertyBindingType)) {
        PyPropertyBindingObject* binding = (PyPropertyBindingObject*)value;
        if (binding->binding) {
            self->collection->setPropertyBinding(name, binding->binding);
            return 0;
        }
        PyErr_SetString(PyExc_ValueError, "PropertyBinding is not valid");
        return -1;
    }

    // CallableBinding
    if (PyObject_IsInstance(value, (PyObject*)&mcrfpydef::PyCallableBindingType)) {
        PyCallableBindingObject* binding = (PyCallableBindingObject*)value;
        if (binding->binding) {
            self->collection->setCallableBinding(name, binding->binding);
            return 0;
        }
        PyErr_SetString(PyExc_ValueError, "CallableBinding is not valid");
        return -1;
    }

    // Float value
    if (PyFloat_Check(value) || PyLong_Check(value)) {
        float f = static_cast<float>(PyFloat_AsDouble(value));
        if (PyErr_Occurred()) return -1;
        self->collection->setFloat(name, f);
        return 0;
    }

    // Tuple for vec2/vec3/vec4
    if (PyTuple_Check(value)) {
        Py_ssize_t size = PyTuple_Size(value);
        if (size == 2) {
            float x = static_cast<float>(PyFloat_AsDouble(PyTuple_GetItem(value, 0)));
            float y = static_cast<float>(PyFloat_AsDouble(PyTuple_GetItem(value, 1)));
            if (PyErr_Occurred()) return -1;
            self->collection->setVec2(name, x, y);
            return 0;
        }
        else if (size == 3) {
            float x = static_cast<float>(PyFloat_AsDouble(PyTuple_GetItem(value, 0)));
            float y = static_cast<float>(PyFloat_AsDouble(PyTuple_GetItem(value, 1)));
            float z = static_cast<float>(PyFloat_AsDouble(PyTuple_GetItem(value, 2)));
            if (PyErr_Occurred()) return -1;
            self->collection->setVec3(name, x, y, z);
            return 0;
        }
        else if (size == 4) {
            float x = static_cast<float>(PyFloat_AsDouble(PyTuple_GetItem(value, 0)));
            float y = static_cast<float>(PyFloat_AsDouble(PyTuple_GetItem(value, 1)));
            float z = static_cast<float>(PyFloat_AsDouble(PyTuple_GetItem(value, 2)));
            float w = static_cast<float>(PyFloat_AsDouble(PyTuple_GetItem(value, 3)));
            if (PyErr_Occurred()) return -1;
            self->collection->setVec4(name, x, y, z, w);
            return 0;
        }
        else {
            PyErr_Format(PyExc_ValueError,
                "Tuple must have 2, 3, or 4 elements for vec2/vec3/vec4, got %zd", size);
            return -1;
        }
    }

    PyErr_SetString(PyExc_TypeError,
        "Uniform value must be a float, tuple (vec2/vec3/vec4), PropertyBinding, or CallableBinding");
    return -1;
}

int PyUniformCollectionType::sq_contains(PyObject* obj, PyObject* key) {
    PyUniformCollectionObject* self = (PyUniformCollectionObject*)obj;

    if (!self->collection) return 0;

    if (!PyUnicode_Check(key)) return 0;

    const char* name = PyUnicode_AsUTF8(key);
    return self->collection->contains(name) ? 1 : 0;
}

PyObject* PyUniformCollectionType::keys(PyUniformCollectionObject* self, PyObject* Py_UNUSED(ignored)) {
    if (!self->collection) {
        return PyList_New(0);
    }

    auto names = self->collection->getNames();
    PyObject* list = PyList_New(names.size());
    for (size_t i = 0; i < names.size(); ++i) {
        PyList_SetItem(list, i, PyUnicode_FromString(names[i].c_str()));
    }
    return list;
}

PyObject* PyUniformCollectionType::values(PyUniformCollectionObject* self, PyObject* Py_UNUSED(ignored)) {
    if (!self->collection) {
        return PyList_New(0);
    }

    auto names = self->collection->getNames();
    PyObject* list = PyList_New(names.size());
    for (size_t i = 0; i < names.size(); ++i) {
        PyObject* key = PyUnicode_FromString(names[i].c_str());
        PyObject* val = mp_subscript((PyObject*)self, key);
        Py_DECREF(key);
        if (!val) {
            Py_DECREF(list);
            return NULL;
        }
        PyList_SetItem(list, i, val);
    }
    return list;
}

PyObject* PyUniformCollectionType::items(PyUniformCollectionObject* self, PyObject* Py_UNUSED(ignored)) {
    if (!self->collection) {
        return PyList_New(0);
    }

    auto names = self->collection->getNames();
    PyObject* list = PyList_New(names.size());
    for (size_t i = 0; i < names.size(); ++i) {
        PyObject* key = PyUnicode_FromString(names[i].c_str());
        PyObject* val = mp_subscript((PyObject*)self, key);
        if (!val) {
            Py_DECREF(key);
            Py_DECREF(list);
            return NULL;
        }
        PyObject* tuple = PyTuple_Pack(2, key, val);
        Py_DECREF(key);
        Py_DECREF(val);
        PyList_SetItem(list, i, tuple);
    }
    return list;
}

PyObject* PyUniformCollectionType::clear(PyUniformCollectionObject* self, PyObject* Py_UNUSED(ignored)) {
    if (self->collection) {
        auto names = self->collection->getNames();
        for (const auto& name : names) {
            self->collection->remove(name);
        }
    }
    Py_RETURN_NONE;
}
