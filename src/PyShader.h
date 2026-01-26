#pragma once
#include "Common.h"
#include "Python.h"

// Forward declarations
class UIDrawable;

// Python object structure for Shader
typedef struct PyShaderObjectStruct {
    PyObject_HEAD
    std::shared_ptr<sf::Shader> shader;
    bool dynamic;                        // Time-varying shader (affects caching)
    std::string fragment_source;         // Source code for recompilation
    PyObject* weakreflist;               // Support weak references
} PyShaderObject;

class PyShader
{
public:
    // Python type methods
    static PyObject* repr(PyObject* self);
    static int init(PyShaderObject* self, PyObject* args, PyObject* kwds);
    static PyObject* pynew(PyTypeObject* type, PyObject* args, PyObject* kwds);
    static void dealloc(PyShaderObject* self);

    // Property getters/setters
    static PyObject* get_dynamic(PyShaderObject* self, void* closure);
    static int set_dynamic(PyShaderObject* self, PyObject* value, void* closure);
    static PyObject* get_source(PyShaderObject* self, void* closure);
    static PyObject* get_is_valid(PyShaderObject* self, void* closure);

    // Methods
    static PyObject* set_uniform(PyShaderObject* self, PyObject* args, PyObject* kwds);

    // Static helper: apply engine-provided uniforms (time, resolution, etc.)
    static void applyEngineUniforms(sf::Shader& shader, sf::Vector2f resolution);

    // Check if shaders are available on this system
    static bool isAvailable();

    // Arrays for Python type definition
    static PyGetSetDef getsetters[];
    static PyMethodDef methods[];
};

namespace mcrfpydef {
    // Using inline to ensure single definition across translation units (C++17)
    inline PyTypeObject PyShaderType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Shader",
        .tp_basicsize = sizeof(PyShaderObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)PyShader::dealloc,
        .tp_repr = PyShader::repr,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR(
            "Shader(fragment_source: str, dynamic: bool = False)\n"
            "\n"
            "A GPU shader program for visual effects.\n"
            "\n"
            "Args:\n"
            "    fragment_source: GLSL fragment shader source code\n"
            "    dynamic: If True, shader uses time-varying effects and will\n"
            "             invalidate parent caches each frame\n"
            "\n"
            "Shaders enable GPU-accelerated visual effects like glow, distortion,\n"
            "color manipulation, and more. Assign to drawable.shader to apply.\n"
            "\n"
            "Engine-provided uniforms (automatically available):\n"
            "    - float time: Seconds since engine start\n"
            "    - float delta_time: Seconds since last frame\n"
            "    - vec2 resolution: Texture size in pixels\n"
            "    - vec2 mouse: Mouse position in window coordinates\n"
            "\n"
            "Example:\n"
            "    shader = mcrfpy.Shader('''\n"
            "        uniform sampler2D texture;\n"
            "        uniform float time;\n"
            "        void main() {\n"
            "            vec2 uv = gl_TexCoord[0].xy;\n"
            "            vec4 color = texture2D(texture, uv);\n"
            "            color.rgb *= 0.5 + 0.5 * sin(time);\n"
            "            gl_FragColor = color;\n"
            "        }\n"
            "    ''', dynamic=True)\n"
            "    frame.shader = shader\n"
        ),
        .tp_weaklistoffset = offsetof(PyShaderObject, weakreflist),
        .tp_methods = nullptr,  // Set in McRFPy_API.cpp before PyType_Ready
        .tp_getset = nullptr,   // Set in McRFPy_API.cpp before PyType_Ready
        .tp_init = (initproc)PyShader::init,
        .tp_new = PyShader::pynew,
    };
}
