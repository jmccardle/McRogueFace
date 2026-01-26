#pragma once
#include "Common.h"
#include "Python.h"
#include <variant>
#include <map>
#include <memory>
#include <optional>

// Forward declarations
class UIDrawable;

/**
 * @brief Variant type for uniform values
 *
 * Supports float, vec2, vec3, and vec4 uniform types.
 */
using UniformValue = std::variant<
    float,
    sf::Glsl::Vec2,
    sf::Glsl::Vec3,
    sf::Glsl::Vec4
>;

/**
 * @brief Base class for uniform bindings
 *
 * Bindings provide dynamic uniform values that are evaluated each frame.
 */
class UniformBinding {
public:
    virtual ~UniformBinding() = default;

    /**
     * @brief Evaluate the binding and return its current value
     * @return The current uniform value, or std::nullopt if binding is invalid
     */
    virtual std::optional<float> evaluate() const = 0;

    /**
     * @brief Check if the binding is still valid
     */
    virtual bool isValid() const = 0;
};

/**
 * @brief Binding that reads a property from a UIDrawable
 *
 * Uses a weak_ptr to prevent dangling references if the target is destroyed.
 */
class PropertyBinding : public UniformBinding {
public:
    PropertyBinding(std::weak_ptr<UIDrawable> target, const std::string& property);

    std::optional<float> evaluate() const override;
    bool isValid() const override;

    // Accessors for Python
    std::weak_ptr<UIDrawable> getTarget() const { return target; }
    const std::string& getPropertyName() const { return property_name; }

private:
    std::weak_ptr<UIDrawable> target;
    std::string property_name;
};

/**
 * @brief Binding that calls a Python callable to get the value
 *
 * The callable should return a float value.
 */
class CallableBinding : public UniformBinding {
public:
    explicit CallableBinding(PyObject* callable);
    ~CallableBinding();

    // Non-copyable due to PyObject reference management
    CallableBinding(const CallableBinding&) = delete;
    CallableBinding& operator=(const CallableBinding&) = delete;

    // Move semantics
    CallableBinding(CallableBinding&& other) noexcept;
    CallableBinding& operator=(CallableBinding&& other) noexcept;

    std::optional<float> evaluate() const override;
    bool isValid() const override;

    // Accessor for Python
    PyObject* getCallable() const { return callable; }

private:
    PyObject* callable;  // Owned reference
};

// Python object structures for bindings
typedef struct {
    PyObject_HEAD
    std::shared_ptr<PropertyBinding> binding;
    PyObject* weakreflist;
} PyPropertyBindingObject;

typedef struct {
    PyObject_HEAD
    std::shared_ptr<CallableBinding> binding;
    PyObject* weakreflist;
} PyCallableBindingObject;

// Python type class for PropertyBinding
class PyPropertyBindingType {
public:
    static PyObject* repr(PyObject* self);
    static int init(PyPropertyBindingObject* self, PyObject* args, PyObject* kwds);
    static PyObject* pynew(PyTypeObject* type, PyObject* args, PyObject* kwds);
    static void dealloc(PyPropertyBindingObject* self);

    static PyObject* get_target(PyPropertyBindingObject* self, void* closure);
    static PyObject* get_property(PyPropertyBindingObject* self, void* closure);
    static PyObject* get_value(PyPropertyBindingObject* self, void* closure);
    static PyObject* is_valid(PyPropertyBindingObject* self, void* closure);

    static PyGetSetDef getsetters[];
};

// Python type class for CallableBinding
class PyCallableBindingType {
public:
    static PyObject* repr(PyObject* self);
    static int init(PyCallableBindingObject* self, PyObject* args, PyObject* kwds);
    static PyObject* pynew(PyTypeObject* type, PyObject* args, PyObject* kwds);
    static void dealloc(PyCallableBindingObject* self);

    static PyObject* get_callable(PyCallableBindingObject* self, void* closure);
    static PyObject* get_value(PyCallableBindingObject* self, void* closure);
    static PyObject* is_valid(PyCallableBindingObject* self, void* closure);

    static PyGetSetDef getsetters[];
};

namespace mcrfpydef {
    // Using inline to ensure single definition across translation units (C++17)
    inline PyTypeObject PyPropertyBindingType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.PropertyBinding",
        .tp_basicsize = sizeof(PyPropertyBindingObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)::PyPropertyBindingType::dealloc,
        .tp_repr = ::PyPropertyBindingType::repr,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR(
            "PropertyBinding(target: UIDrawable, property: str)\n"
            "\n"
            "A binding that reads a property value from a UI drawable.\n"
            "\n"
            "Args:\n"
            "    target: The drawable to read the property from\n"
            "    property: Name of the property to read (e.g., 'x', 'opacity')\n"
            "\n"
            "Use this to create dynamic shader uniforms that follow a drawable's\n"
            "properties. The binding automatically handles cases where the target\n"
            "is destroyed.\n"
            "\n"
            "Example:\n"
            "    other_frame = mcrfpy.Frame(pos=(100, 100))\n"
            "    frame.uniforms['offset_x'] = mcrfpy.PropertyBinding(other_frame, 'x')\n"
        ),
        .tp_weaklistoffset = offsetof(PyPropertyBindingObject, weakreflist),
        .tp_getset = nullptr,  // Set in McRFPy_API.cpp before PyType_Ready
        .tp_init = (initproc)::PyPropertyBindingType::init,
        .tp_new = ::PyPropertyBindingType::pynew,
    };

    inline PyTypeObject PyCallableBindingType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.CallableBinding",
        .tp_basicsize = sizeof(PyCallableBindingObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)::PyCallableBindingType::dealloc,
        .tp_repr = ::PyCallableBindingType::repr,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR(
            "CallableBinding(callable: Callable[[], float])\n"
            "\n"
            "A binding that calls a Python function to get its value.\n"
            "\n"
            "Args:\n"
            "    callable: A function that takes no arguments and returns a float\n"
            "\n"
            "The callable is invoked every frame when the shader is rendered.\n"
            "Keep the callable lightweight to avoid performance issues.\n"
            "\n"
            "Example:\n"
            "    player_health = 100\n"
            "    frame.uniforms['health_pct'] = mcrfpy.CallableBinding(\n"
            "        lambda: player_health / 100.0\n"
            "    )\n"
        ),
        .tp_weaklistoffset = offsetof(PyCallableBindingObject, weakreflist),
        .tp_getset = nullptr,  // Set in McRFPy_API.cpp before PyType_Ready
        .tp_init = (initproc)::PyCallableBindingType::init,
        .tp_new = ::PyCallableBindingType::pynew,
    };
}
