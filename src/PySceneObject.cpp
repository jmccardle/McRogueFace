#include "PySceneObject.h"
#include "PyScene.h"
#include "GameEngine.h"
#include "McRFPy_API.h"
#include <iostream>

// Static map to store Python scene objects by name
static std::map<std::string, PySceneObject*> python_scenes;

PyObject* PySceneClass::__new__(PyTypeObject* type, PyObject* args, PyObject* kwds)
{
    PySceneObject* self = (PySceneObject*)type->tp_alloc(type, 0);
    if (self) {
        self->initialized = false;
        // Don't create C++ scene yet - wait for __init__
    }
    return (PyObject*)self;
}

int PySceneClass::__init__(PySceneObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"name", nullptr};
    const char* name = nullptr;
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "s", const_cast<char**>(keywords), &name)) {
        return -1;
    }
    
    // Check if scene with this name already exists
    if (python_scenes.count(name) > 0) {
        PyErr_Format(PyExc_ValueError, "Scene with name '%s' already exists", name);
        return -1;
    }
    
    self->name = name;
    
    // Create the C++ PyScene
    McRFPy_API::game->createScene(name);
    
    // Get reference to the created scene
    GameEngine* game = McRFPy_API::game;
    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "No game engine initialized");
        return -1;
    }
    
    // Store this Python object in our registry
    python_scenes[name] = self;
    Py_INCREF(self);  // Keep a reference
    
    // Create a Python function that routes to on_keypress
    // We'll register this after the object is fully initialized
    
    self->initialized = true;
    
    return 0;
}

void PySceneClass::__dealloc(PyObject* self_obj)
{
    PySceneObject* self = (PySceneObject*)self_obj;
    
    // Remove from registry
    if (python_scenes.count(self->name) > 0 && python_scenes[self->name] == self) {
        python_scenes.erase(self->name);
    }
    
    // Call Python object destructor
    Py_TYPE(self)->tp_free(self);
}

PyObject* PySceneClass::__repr__(PySceneObject* self)
{
    return PyUnicode_FromFormat("<Scene '%s'>", self->name.c_str());
}

PyObject* PySceneClass::activate(PySceneObject* self, PyObject* args)
{
    // Call the static method from McRFPy_API
    PyObject* py_args = Py_BuildValue("(s)", self->name.c_str());
    PyObject* result = McRFPy_API::_setScene(NULL, py_args);
    Py_DECREF(py_args);
    return result;
}

PyObject* PySceneClass::get_ui(PySceneObject* self, PyObject* args)
{
    // Call the static method from McRFPy_API
    PyObject* py_args = Py_BuildValue("(s)", self->name.c_str());
    PyObject* result = McRFPy_API::_sceneUI(NULL, py_args);
    Py_DECREF(py_args);
    return result;
}

PyObject* PySceneClass::register_keyboard(PySceneObject* self, PyObject* args)
{
    PyObject* callable;
    if (!PyArg_ParseTuple(args, "O", &callable)) {
        return NULL;
    }
    
    if (!PyCallable_Check(callable)) {
        PyErr_SetString(PyExc_TypeError, "Argument must be callable");
        return NULL;
    }
    
    // Store the callable
    Py_INCREF(callable);
    
    // Get the current scene and set its key_callable
    GameEngine* game = McRFPy_API::game;
    if (game) {
        // We need to be on the right scene first
        std::string old_scene = game->scene;
        game->scene = self->name;
        game->currentScene()->key_callable = std::make_unique<PyKeyCallable>(callable);
        game->scene = old_scene;
    }
    
    Py_DECREF(callable);
    Py_RETURN_NONE;
}

PyObject* PySceneClass::get_name(PySceneObject* self, void* closure)
{
    return PyUnicode_FromString(self->name.c_str());
}

PyObject* PySceneClass::get_active(PySceneObject* self, void* closure)
{
    GameEngine* game = McRFPy_API::game;
    if (!game) {
        Py_RETURN_FALSE;
    }
    
    return PyBool_FromLong(game->scene == self->name);
}

// Lifecycle callbacks
void PySceneClass::call_on_enter(PySceneObject* self)
{
    PyObject* method = PyObject_GetAttrString((PyObject*)self, "on_enter");
    if (method && PyCallable_Check(method)) {
        PyObject* result = PyObject_CallNoArgs(method);
        if (result) {
            Py_DECREF(result);
        } else {
            PyErr_Print();
        }
    }
    Py_XDECREF(method);
}

void PySceneClass::call_on_exit(PySceneObject* self)
{
    PyObject* method = PyObject_GetAttrString((PyObject*)self, "on_exit");
    if (method && PyCallable_Check(method)) {
        PyObject* result = PyObject_CallNoArgs(method);
        if (result) {
            Py_DECREF(result);
        } else {
            PyErr_Print();
        }
    }
    Py_XDECREF(method);
}

void PySceneClass::call_on_keypress(PySceneObject* self, std::string key, std::string action)
{
    PyGILState_STATE gstate = PyGILState_Ensure();
    
    PyObject* method = PyObject_GetAttrString((PyObject*)self, "on_keypress");
    if (method && PyCallable_Check(method)) {
        PyObject* result = PyObject_CallFunction(method, "ss", key.c_str(), action.c_str());
        if (result) {
            Py_DECREF(result);
        } else {
            PyErr_Print();
        }
    }
    Py_XDECREF(method);
    
    PyGILState_Release(gstate);
}

void PySceneClass::call_update(PySceneObject* self, float dt)
{
    PyObject* method = PyObject_GetAttrString((PyObject*)self, "update");
    if (method && PyCallable_Check(method)) {
        PyObject* result = PyObject_CallFunction(method, "f", dt);
        if (result) {
            Py_DECREF(result);
        } else {
            PyErr_Print();
        }
    }
    Py_XDECREF(method);
}

void PySceneClass::call_on_resize(PySceneObject* self, int width, int height)
{
    PyObject* method = PyObject_GetAttrString((PyObject*)self, "on_resize");
    if (method && PyCallable_Check(method)) {
        PyObject* result = PyObject_CallFunction(method, "ii", width, height);
        if (result) {
            Py_DECREF(result);
        } else {
            PyErr_Print();
        }
    }
    Py_XDECREF(method);
}

// Properties
PyGetSetDef PySceneClass::getsetters[] = {
    {"name", (getter)get_name, NULL, "Scene name", NULL},
    {"active", (getter)get_active, NULL, "Whether this scene is currently active", NULL},
    {NULL}
};

// Methods
PyMethodDef PySceneClass::methods[] = {
    {"activate", (PyCFunction)activate, METH_NOARGS,
     "Make this the active scene"},
    {"get_ui", (PyCFunction)get_ui, METH_NOARGS,
     "Get the UI element collection for this scene"},
    {"register_keyboard", (PyCFunction)register_keyboard, METH_VARARGS,
     "Register a keyboard handler function (alternative to overriding on_keypress)"},
    {NULL}
};

// Helper function to trigger lifecycle events
void McRFPy_API::triggerSceneChange(const std::string& from_scene, const std::string& to_scene)
{
    // Call on_exit for the old scene
    if (!from_scene.empty() && python_scenes.count(from_scene) > 0) {
        PySceneClass::call_on_exit(python_scenes[from_scene]);
    }
    
    // Call on_enter for the new scene
    if (!to_scene.empty() && python_scenes.count(to_scene) > 0) {
        PySceneClass::call_on_enter(python_scenes[to_scene]);
    }
}

// Helper function to update Python scenes
void McRFPy_API::updatePythonScenes(float dt)
{
    GameEngine* game = McRFPy_API::game;
    if (!game) return;
    
    // Only update the active scene
    if (python_scenes.count(game->scene) > 0) {
        PySceneClass::call_update(python_scenes[game->scene], dt);
    }
}

// Helper function to trigger resize events on Python scenes
void McRFPy_API::triggerResize(int width, int height)
{
    GameEngine* game = McRFPy_API::game;
    if (!game) return;
    
    // Only notify the active scene
    if (python_scenes.count(game->scene) > 0) {
        PySceneClass::call_on_resize(python_scenes[game->scene], width, height);
    }
}