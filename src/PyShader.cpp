#include "PyShader.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"
#include "GameEngine.h"
#include "Resources.h"
#include <sstream>

// Static clock for time uniform
static sf::Clock shader_engine_clock;
static sf::Clock shader_frame_clock;

// Python method and getset definitions
PyGetSetDef PyShader::getsetters[] = {
    {"dynamic", (getter)PyShader::get_dynamic, (setter)PyShader::set_dynamic,
     MCRF_PROPERTY(dynamic,
         "Whether this shader uses time-varying effects (bool). "
         "Dynamic shaders invalidate parent caches each frame."), NULL},
    {"source", (getter)PyShader::get_source, NULL,
     MCRF_PROPERTY(source,
         "The GLSL fragment shader source code (str, read-only)."), NULL},
    {"is_valid", (getter)PyShader::get_is_valid, NULL,
     MCRF_PROPERTY(is_valid,
         "True if the shader compiled successfully (bool, read-only)."), NULL},
    {NULL}
};

PyMethodDef PyShader::methods[] = {
    {"set_uniform", (PyCFunction)PyShader::set_uniform, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(Shader, set_uniform,
         MCRF_SIG("(name: str, value: float|tuple)", "None"),
         MCRF_DESC("Set a custom uniform value on this shader."),
         MCRF_ARGS_START
         MCRF_ARG("name", "Uniform variable name in the shader")
         MCRF_ARG("value", "Float, vec2 (2-tuple), vec3 (3-tuple), or vec4 (4-tuple)")
         MCRF_RAISES("ValueError", "If uniform type cannot be determined")
         MCRF_NOTE("Engine uniforms (time, resolution, etc.) are set automatically")
     )},
    {NULL}
};

// Constructor
PyObject* PyShader::pynew(PyTypeObject* type, PyObject* args, PyObject* kwds)
{
    PyShaderObject* self = (PyShaderObject*)type->tp_alloc(type, 0);
    if (self) {
        self->shader = nullptr;
        self->dynamic = false;
        self->weakreflist = NULL;
        new (&self->fragment_source) std::string();
    }
    return (PyObject*)self;
}

// Destructor
void PyShader::dealloc(PyShaderObject* self)
{
    // Clear weak references
    if (self->weakreflist) {
        PyObject_ClearWeakRefs((PyObject*)self);
    }

    // Destroy C++ objects
    self->shader.reset();
    self->fragment_source.~basic_string();

    // Free Python object
    Py_TYPE(self)->tp_free((PyObject*)self);
}

// Initializer
int PyShader::init(PyShaderObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"fragment_source", "dynamic", nullptr};
    const char* source = nullptr;
    int dynamic = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "s|p", const_cast<char**>(keywords),
                                     &source, &dynamic)) {
        return -1;
    }

    // Check if shaders are available
    if (!sf::Shader::isAvailable()) {
        PyErr_SetString(PyExc_RuntimeError,
            "Shaders are not available on this system (no GPU support or OpenGL too old)");
        return -1;
    }

    // Store source and dynamic flag
    self->fragment_source = source;
    self->dynamic = (bool)dynamic;

    // Create and compile the shader
    self->shader = std::make_shared<sf::Shader>();

    // Capture sf::err() output during shader compilation
    std::streambuf* oldBuf = sf::err().rdbuf();
    std::ostringstream errStream;
    sf::err().rdbuf(errStream.rdbuf());

    bool success = self->shader->loadFromMemory(source, sf::Shader::Fragment);

    // Restore sf::err() and check for errors
    sf::err().rdbuf(oldBuf);

    if (!success) {
        std::string error_msg = errStream.str();
        if (error_msg.empty()) {
            error_msg = "Shader compilation failed (unknown error)";
        }
        PyErr_Format(PyExc_ValueError, "Shader compilation failed: %s", error_msg.c_str());
        self->shader.reset();
        return -1;
    }

    return 0;
}

// Repr
PyObject* PyShader::repr(PyObject* obj)
{
    PyShaderObject* self = (PyShaderObject*)obj;
    std::ostringstream ss;
    ss << "<Shader";
    if (self->shader) {
        ss << " valid";
    } else {
        ss << " invalid";
    }
    if (self->dynamic) {
        ss << " dynamic";
    }
    ss << ">";
    return PyUnicode_FromString(ss.str().c_str());
}

// Property: dynamic
PyObject* PyShader::get_dynamic(PyShaderObject* self, void* closure)
{
    return PyBool_FromLong(self->dynamic);
}

int PyShader::set_dynamic(PyShaderObject* self, PyObject* value, void* closure)
{
    if (!PyBool_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "dynamic must be a boolean");
        return -1;
    }
    self->dynamic = PyObject_IsTrue(value);
    return 0;
}

// Property: source (read-only)
PyObject* PyShader::get_source(PyShaderObject* self, void* closure)
{
    return PyUnicode_FromString(self->fragment_source.c_str());
}

// Property: is_valid (read-only)
PyObject* PyShader::get_is_valid(PyShaderObject* self, void* closure)
{
    return PyBool_FromLong(self->shader != nullptr);
}

// Method: set_uniform
PyObject* PyShader::set_uniform(PyShaderObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"name", "value", nullptr};
    const char* name = nullptr;
    PyObject* value = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "sO", const_cast<char**>(keywords),
                                     &name, &value)) {
        return NULL;
    }

    if (!self->shader) {
        PyErr_SetString(PyExc_RuntimeError, "Shader is not valid");
        return NULL;
    }

    // Determine the type and set uniform
    if (PyFloat_Check(value) || PyLong_Check(value)) {
        // Single float
        float f = (float)PyFloat_AsDouble(value);
        if (PyErr_Occurred()) return NULL;
        self->shader->setUniform(name, f);
    }
    else if (PyTuple_Check(value)) {
        Py_ssize_t size = PyTuple_Size(value);
        if (size == 2) {
            // vec2
            float x = (float)PyFloat_AsDouble(PyTuple_GetItem(value, 0));
            float y = (float)PyFloat_AsDouble(PyTuple_GetItem(value, 1));
            if (PyErr_Occurred()) return NULL;
            self->shader->setUniform(name, sf::Glsl::Vec2(x, y));
        }
        else if (size == 3) {
            // vec3
            float x = (float)PyFloat_AsDouble(PyTuple_GetItem(value, 0));
            float y = (float)PyFloat_AsDouble(PyTuple_GetItem(value, 1));
            float z = (float)PyFloat_AsDouble(PyTuple_GetItem(value, 2));
            if (PyErr_Occurred()) return NULL;
            self->shader->setUniform(name, sf::Glsl::Vec3(x, y, z));
        }
        else if (size == 4) {
            // vec4
            float x = (float)PyFloat_AsDouble(PyTuple_GetItem(value, 0));
            float y = (float)PyFloat_AsDouble(PyTuple_GetItem(value, 1));
            float z = (float)PyFloat_AsDouble(PyTuple_GetItem(value, 2));
            float w = (float)PyFloat_AsDouble(PyTuple_GetItem(value, 3));
            if (PyErr_Occurred()) return NULL;
            self->shader->setUniform(name, sf::Glsl::Vec4(x, y, z, w));
        }
        else {
            PyErr_Format(PyExc_ValueError,
                "Tuple must have 2, 3, or 4 elements for vec2/vec3/vec4, got %zd", size);
            return NULL;
        }
    }
    else {
        PyErr_SetString(PyExc_TypeError,
            "Uniform value must be a float or tuple of 2-4 floats");
        return NULL;
    }

    Py_RETURN_NONE;
}

// Static helper: apply engine-provided uniforms
void PyShader::applyEngineUniforms(sf::Shader& shader, sf::Vector2f resolution)
{
    // Time uniforms
    shader.setUniform("time", shader_engine_clock.getElapsedTime().asSeconds());
    shader.setUniform("delta_time", shader_frame_clock.restart().asSeconds());

    // Resolution
    shader.setUniform("resolution", resolution);

    // Mouse position - get from GameEngine if available
    sf::Vector2f mouse(0.f, 0.f);
    if (Resources::game && !Resources::game->isHeadless()) {
        sf::Vector2i mousePos = sf::Mouse::getPosition(Resources::game->getWindow());
        mouse = sf::Vector2f(static_cast<float>(mousePos.x), static_cast<float>(mousePos.y));
    }
    shader.setUniform("mouse", mouse);

    // CurrentTexture is handled by SFML automatically when drawing
    shader.setUniform("texture", sf::Shader::CurrentTexture);
}

// Static helper: check availability
bool PyShader::isAvailable()
{
    return sf::Shader::isAvailable();
}
