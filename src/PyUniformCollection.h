#pragma once
#include "Common.h"
#include "Python.h"
#include "PyUniformBinding.h"
#include <map>
#include <variant>

// Forward declarations
class UIDrawable;

/**
 * @brief Entry in UniformCollection - can be static value or binding
 */
using UniformEntry = std::variant<
    UniformValue,                           // Static value (float, vec2, vec3, vec4)
    std::shared_ptr<PropertyBinding>,       // Property binding
    std::shared_ptr<CallableBinding>        // Callable binding
>;

/**
 * @brief Collection of shader uniforms for a UIDrawable
 *
 * Stores both static uniform values and dynamic bindings. When applying
 * uniforms to a shader, static values are used directly while bindings
 * are evaluated each frame.
 */
class UniformCollection {
public:
    UniformCollection() = default;

    /**
     * @brief Set a static uniform value
     */
    void setFloat(const std::string& name, float value);
    void setVec2(const std::string& name, float x, float y);
    void setVec3(const std::string& name, float x, float y, float z);
    void setVec4(const std::string& name, float x, float y, float z, float w);

    /**
     * @brief Set a property binding
     */
    void setPropertyBinding(const std::string& name, std::shared_ptr<PropertyBinding> binding);

    /**
     * @brief Set a callable binding
     */
    void setCallableBinding(const std::string& name, std::shared_ptr<CallableBinding> binding);

    /**
     * @brief Remove a uniform
     */
    void remove(const std::string& name);

    /**
     * @brief Check if a uniform exists
     */
    bool contains(const std::string& name) const;

    /**
     * @brief Get all uniform names
     */
    std::vector<std::string> getNames() const;

    /**
     * @brief Apply all uniforms to a shader
     */
    void applyTo(sf::Shader& shader) const;

    /**
     * @brief Check if any binding is dynamic (callable)
     */
    bool hasDynamicBindings() const;

    /**
     * @brief Get the entry for a uniform (for Python access)
     */
    const UniformEntry* getEntry(const std::string& name) const;

private:
    std::map<std::string, UniformEntry> entries;
};

// Python object structure for UniformCollection
typedef struct {
    PyObject_HEAD
    UniformCollection* collection;  // Owned by UIDrawable, not by this object
    std::weak_ptr<UIDrawable> owner;  // For checking validity
    PyObject* weakreflist;
} PyUniformCollectionObject;

/**
 * @brief Python type for UniformCollection
 *
 * Supports dict-like access: collection["name"] = value
 */
class PyUniformCollectionType {
public:
    static PyObject* repr(PyObject* self);
    static void dealloc(PyUniformCollectionObject* self);

    // Mapping protocol (dict-like access)
    static Py_ssize_t mp_length(PyObject* self);
    static PyObject* mp_subscript(PyObject* self, PyObject* key);
    static int mp_ass_subscript(PyObject* self, PyObject* key, PyObject* value);

    // Sequence protocol for 'in' operator
    static int sq_contains(PyObject* self, PyObject* key);

    // Methods
    static PyObject* keys(PyUniformCollectionObject* self, PyObject* Py_UNUSED(ignored));
    static PyObject* values(PyUniformCollectionObject* self, PyObject* Py_UNUSED(ignored));
    static PyObject* items(PyUniformCollectionObject* self, PyObject* Py_UNUSED(ignored));
    static PyObject* clear(PyUniformCollectionObject* self, PyObject* Py_UNUSED(ignored));

    static PyMethodDef methods[];
    static PyMappingMethods mapping_methods;
    static PySequenceMethods sequence_methods;
};

namespace mcrfpydef {
    // Using inline to ensure single definition across translation units (C++17)
    inline PyTypeObject PyUniformCollectionType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.UniformCollection",
        .tp_basicsize = sizeof(PyUniformCollectionObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)::PyUniformCollectionType::dealloc,
        .tp_repr = ::PyUniformCollectionType::repr,
        .tp_as_sequence = &::PyUniformCollectionType::sequence_methods,
        .tp_as_mapping = &::PyUniformCollectionType::mapping_methods,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR(
            "UniformCollection - dict-like container for shader uniforms.\n"
            "\n"
            "This object is accessed via drawable.uniforms and supports:\n"
            "- Getting: value = uniforms['name']\n"
            "- Setting: uniforms['name'] = value\n"
            "- Deleting: del uniforms['name']\n"
            "- Checking: 'name' in uniforms\n"
            "- Iterating: for name in uniforms.keys()\n"
            "\n"
            "Values can be:\n"
            "- float: Single value uniform\n"
            "- tuple: vec2 (2-tuple), vec3 (3-tuple), or vec4 (4-tuple)\n"
            "- PropertyBinding: Dynamic value from another drawable's property\n"
            "- CallableBinding: Dynamic value from a Python function\n"
            "\n"
            "Example:\n"
            "    frame.uniforms['intensity'] = 0.5\n"
            "    frame.uniforms['color'] = (1.0, 0.5, 0.0, 1.0)\n"
            "    frame.uniforms['offset'] = mcrfpy.PropertyBinding(other, 'x')\n"
            "    del frame.uniforms['intensity']\n"
        ),
        .tp_weaklistoffset = offsetof(PyUniformCollectionObject, weakreflist),
        .tp_methods = nullptr,  // Set in McRFPy_API.cpp
    };
}
