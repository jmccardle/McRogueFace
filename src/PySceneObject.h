#pragma once
#include "Common.h"
#include "Python.h"
#include <string>
#include <memory>

// Forward declarations
class PyScene;

// Python object structure for Scene
typedef struct {
    PyObject_HEAD
    std::string name;
    std::shared_ptr<PyScene> scene;  // Reference to the C++ scene
    bool initialized;
} PySceneObject;

// C++ interface for Python Scene class
class PySceneClass
{
public:
    // Type methods
    static PyObject* __new__(PyTypeObject* type, PyObject* args, PyObject* kwds);
    static int __init__(PySceneObject* self, PyObject* args, PyObject* kwds);
    static void __dealloc(PyObject* self);
    static PyObject* __repr__(PySceneObject* self);
    
    // Scene methods
    static PyObject* activate(PySceneObject* self, PyObject* args);
    static PyObject* register_keyboard(PySceneObject* self, PyObject* args);
    
    // Properties
    static PyObject* get_name(PySceneObject* self, void* closure);
    static PyObject* get_active(PySceneObject* self, void* closure);
    
    // Lifecycle callbacks (called from C++)
    static void call_on_enter(PySceneObject* self);
    static void call_on_exit(PySceneObject* self);
    static void call_on_keypress(PySceneObject* self, std::string key, std::string action);
    static void call_update(PySceneObject* self, float dt);
    static void call_on_resize(PySceneObject* self, int width, int height);
    
    static PyGetSetDef getsetters[];
    static PyMethodDef methods[];
};

namespace mcrfpydef {
    static PyTypeObject PySceneType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Scene",
        .tp_basicsize = sizeof(PySceneObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)PySceneClass::__dealloc,
        .tp_repr = (reprfunc)PySceneClass::__repr__,
        .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,  // Allow subclassing
        .tp_doc = PyDoc_STR(
            "Scene(name: str)\n\n"
            "Object-oriented scene management with lifecycle callbacks.\n\n"
            "This is the recommended approach for scene management, replacing module-level\n"
            "functions like createScene(), setScene(), and sceneUI(). Key advantage: you can\n"
            "set on_key handlers on ANY scene, not just the currently active one.\n\n"
            "Args:\n"
            "    name: Unique identifier for this scene. Used for scene transitions.\n\n"
            "Properties:\n"
            "    name (str, read-only): Scene's unique identifier.\n"
            "    active (bool, read-only): Whether this scene is currently displayed.\n"
            "    children (UICollection, read-only): UI elements in this scene. Modify to add/remove elements.\n"
            "    on_key (callable): Keyboard handler. Set on ANY scene, regardless of which is active!\n"
            "    pos (Vector): Position offset for all UI elements.\n"
            "    visible (bool): Whether the scene renders.\n"
            "    opacity (float): Scene transparency (0.0-1.0).\n\n"
            "Lifecycle Callbacks (override in subclass):\n"
            "    on_enter(): Called when scene becomes active via activate().\n"
            "    on_exit(): Called when scene is deactivated (another scene activates).\n"
            "    on_keypress(key: str, action: str): Called for keyboard events. Alternative to on_key property.\n"
            "    update(dt: float): Called every frame with delta time in seconds.\n"
            "    on_resize(width: int, height: int): Called when window is resized.\n\n"
            "Example:\n"
            "    # Basic usage (replacing module functions):\n"
            "    scene = mcrfpy.Scene('main_menu')\n"
            "    scene.children.append(mcrfpy.Caption(text='Welcome', pos=(100, 100)))\n"
            "    scene.on_key = lambda key, action: print(f'Key: {key}')\n"
            "    scene.activate()  # Switch to this scene\n\n"
            "    # Subclassing for lifecycle:\n"
            "    class GameScene(mcrfpy.Scene):\n"
            "        def on_enter(self):\n"
            "            print('Game started!')\n"
            "        def update(self, dt):\n"
            "            self.player.move(dt)\n"
        ),
        .tp_methods = nullptr,  // Set in McRFPy_API.cpp
        .tp_getset = nullptr,   // Set in McRFPy_API.cpp
        .tp_init = (initproc)PySceneClass::__init__,
        .tp_new = PySceneClass::__new__,
    };
}