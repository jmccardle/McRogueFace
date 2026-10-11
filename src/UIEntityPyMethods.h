#pragma once
#include "UIEntity.h"
#include "UIBase.h"
#include "PyShader.h"  // #106: Shader support
#include "PyUniformCollection.h"  // #106: Uniform collection support
#include "PyWrap.h"  // #465: mcrf::py_shared

// UIEntity-specific property implementations
// These delegate to the wrapped sprite member

// Visible property
static PyObject* UIEntity_get_visible(PyUIEntityObject* self, void* closure)
{
    return PyBool_FromLong(self->data->sprite.visible);
}

static int UIEntity_set_visible(PyUIEntityObject* self, PyObject* value, void* closure)
{
    if (!PyBool_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "visible must be a boolean");
        return -1;
    }
    self->data->sprite.visible = PyObject_IsTrue(value);
    return 0;
}

// Opacity property
static PyObject* UIEntity_get_opacity(PyUIEntityObject* self, void* closure)
{
    return PyFloat_FromDouble(self->data->sprite.opacity);
}

static int UIEntity_set_opacity(PyUIEntityObject* self, PyObject* value, void* closure)
{
    float opacity;
    if (PyFloat_Check(value)) {
        opacity = PyFloat_AsDouble(value);
    } else if (PyLong_Check(value)) {
        opacity = PyLong_AsDouble(value);
    } else {
        PyErr_SetString(PyExc_TypeError, "opacity must be a number");
        return -1;
    }
    
    self->data->assignOpacity(opacity);  // #423: clamps; shared with animation
    return 0;
}

// Name property - delegate to sprite
static PyObject* UIEntity_get_name(PyUIEntityObject* self, void* closure)
{
    return PyUnicode_FromString(self->data->sprite.name.c_str());
}

static int UIEntity_set_name(PyUIEntityObject* self, PyObject* value, void* closure)
{
    if (value == NULL || value == Py_None) {
        self->data->sprite.name = "";
        return 0;
    }
    
    if (!PyUnicode_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "name must be a string");
        return -1;
    }
    
    const char* name_str = PyUnicode_AsUTF8(value);
    if (!name_str) {
        return -1;
    }
    
    self->data->sprite.name = name_str;
    return 0;
}

// #106: Shader property - delegate to sprite
static PyObject* UIEntity_get_shader(PyUIEntityObject* self, void* closure)
{
    auto& shader_ptr = self->data->sprite.shader;
    if (!shader_ptr) {
        Py_RETURN_NONE;
    }
    // Return the PyShaderObject (which is also a PyObject)
    Py_INCREF((PyObject*)shader_ptr.get());
    return (PyObject*)shader_ptr.get();
}

static int UIEntity_set_shader(PyUIEntityObject* self, PyObject* value, void* closure)
{
    if (value == Py_None || value == NULL) {
        self->data->sprite.shader.reset();
        self->data->sprite.shader_dynamic = false;
        return 0;
    }

    // Check if value is a Shader object
    if (!PyObject_IsInstance(value, (PyObject*)&mcrfpydef::PyShaderType)) {
        PyErr_SetString(PyExc_TypeError, "shader must be a Shader object or None");
        return -1;
    }

    PyShaderObject* shader_obj = (PyShaderObject*)value;

    self->data->sprite.shader = mcrf::py_shared(shader_obj);

    // Initialize uniforms collection if needed
    if (!self->data->sprite.uniforms) {
        self->data->sprite.uniforms = std::make_unique<UniformCollection>();
    }

    // Propagate dynamic flag
    if (shader_obj->dynamic) {
        self->data->sprite.markShaderDynamic();
    }

    return 0;
}

// #106: Uniforms property - delegate to sprite's uniforms collection
static PyObject* UIEntity_get_uniforms(PyUIEntityObject* self, void* closure)
{
    // Initialize uniforms collection if needed
    if (!self->data->sprite.uniforms) {
        self->data->sprite.uniforms = std::make_unique<UniformCollection>();
    }

    // A view of the sprite's collection, valid while the entity lives
    return PyUniformCollectionType::wrap(self->data->sprite.uniforms.get(), self->data);
}