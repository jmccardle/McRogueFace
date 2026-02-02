#include "PySceneObject.h"
#include "PyScene.h"
#include "GameEngine.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"
#include "PyTransition.h"
#include "PyKey.h"
#include "PyInputState.h"
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

    GameEngine* game = McRFPy_API::game;
    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "No game engine initialized");
        return -1;
    }

    // If scene with this name already exists in python_scenes, unregister the old one
    if (python_scenes.count(name) > 0) {
        PySceneObject* old_scene = python_scenes[name];
        // Remove old scene from registries (but its shared_ptr keeps the C++ object alive)
        Py_DECREF(old_scene);
        python_scenes.erase(name);
        game->unregisterScene(name);
    }

    self->name = name;

    // Create the C++ PyScene with shared ownership
    self->scene = std::make_shared<PyScene>(game);

    // Register with the game engine (game engine also holds a reference)
    game->registerScene(name, self->scene);

    // Store this Python object in our registry for lifecycle callbacks
    python_scenes[name] = self;
    Py_INCREF(self);  // python_scenes holds a reference

    self->initialized = true;

    return 0;
}

void PySceneClass::__dealloc(PyObject* self_obj)
{
    PySceneObject* self = (PySceneObject*)self_obj;

    // Remove from python_scenes registry if we're the registered scene
    if (python_scenes.count(self->name) > 0 && python_scenes[self->name] == self) {
        python_scenes.erase(self->name);
    }

    // Release our shared_ptr reference to the C++ scene
    // If GameEngine still holds a reference, the scene survives
    // If not, this may be the last reference and the scene is deleted
    self->scene.reset();

    // Call Python object destructor
    Py_TYPE(self)->tp_free(self);
}

PyObject* PySceneClass::__repr__(PySceneObject* self)
{
    return PyUnicode_FromFormat("<Scene '%s'>", self->name.c_str());
}

PyObject* PySceneClass::activate(PySceneObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"transition", "duration", nullptr};
    PyObject* transition_arg = nullptr;
    PyObject* duration_arg = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OO", const_cast<char**>(keywords),
                                      &transition_arg, &duration_arg)) {
        return NULL;
    }

    // Get transition type (use default if not provided)
    TransitionType transition_type;
    bool trans_was_none = false;
    if (transition_arg) {
        if (!PyTransition::from_arg(transition_arg, &transition_type, &trans_was_none)) {
            return NULL;
        }
    } else {
        transition_type = PyTransition::default_transition;
    }

    // Get duration (use default if not provided)
    float duration;
    if (duration_arg && duration_arg != Py_None) {
        if (PyFloat_Check(duration_arg)) {
            duration = static_cast<float>(PyFloat_AsDouble(duration_arg));
        } else if (PyLong_Check(duration_arg)) {
            duration = static_cast<float>(PyLong_AsLong(duration_arg));
        } else {
            PyErr_SetString(PyExc_TypeError, "duration must be a number");
            return NULL;
        }
    } else {
        duration = PyTransition::default_duration;
    }

    // Build transition string for _setScene (or call game->changeScene directly)
    GameEngine* game = McRFPy_API::game;
    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "No game engine");
        return NULL;
    }

    // Auto-register if this scene is not currently registered
    if (!game->getScene(self->name)) {
        game->registerScene(self->name, self->scene);
        if (python_scenes.count(self->name) == 0 || python_scenes[self->name] != self) {
            python_scenes[self->name] = self;
            Py_INCREF(self);
        }
    }

    // Call game->changeScene directly with proper transition
    game->changeScene(self->name, transition_type, duration);

    Py_RETURN_NONE;
}

// children property getter (replaces get_ui method)
static PyObject* PySceneClass_get_children(PySceneObject* self, void* closure)
{
    // Call the static method from McRFPy_API
    PyObject* py_args = Py_BuildValue("(s)", self->name.c_str());
    PyObject* result = McRFPy_API::_sceneUI(NULL, py_args);
    Py_DECREF(py_args);
    return result;
}

// on_key property getter
static PyObject* PySceneClass_get_on_key(PySceneObject* self, void* closure)
{
    if (!self->scene || !self->scene->key_callable) {
        Py_RETURN_NONE;
    }

    PyObject* callable = self->scene->key_callable->borrow();
    if (callable && callable != Py_None) {
        Py_INCREF(callable);
        return callable;
    }
    Py_RETURN_NONE;
}

// on_key property setter
static int PySceneClass_set_on_key(PySceneObject* self, PyObject* value, void* closure)
{
    if (!self->scene) {
        PyErr_SetString(PyExc_RuntimeError, "Scene not initialized");
        return -1;
    }

    if (value == Py_None || value == NULL) {
        self->scene->key_unregister();
    } else if (PyCallable_Check(value)) {
        self->scene->key_register(value);
    } else {
        PyErr_SetString(PyExc_TypeError, "on_key must be callable or None");
        return -1;
    }
    return 0;
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

// #118: Scene position getter
static PyObject* PySceneClass_get_pos(PySceneObject* self, void* closure)
{
    if (!self->scene) {
        Py_RETURN_NONE;
    }

    // Create a Vector object
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    if (!type) return NULL;
    PyObject* args = Py_BuildValue("(ff)", self->scene->position.x, self->scene->position.y);
    PyObject* result = PyObject_CallObject((PyObject*)type, args);
    Py_DECREF(type);
    Py_DECREF(args);
    return result;
}

// #118: Scene position setter
static int PySceneClass_set_pos(PySceneObject* self, PyObject* value, void* closure)
{
    if (!self->scene) {
        PyErr_SetString(PyExc_RuntimeError, "Scene not initialized");
        return -1;
    }

    // Accept tuple or Vector
    float x, y;
    if (PyTuple_Check(value) && PyTuple_Size(value) == 2) {
        x = PyFloat_AsDouble(PyTuple_GetItem(value, 0));
        y = PyFloat_AsDouble(PyTuple_GetItem(value, 1));
    } else if (PyObject_HasAttrString(value, "x") && PyObject_HasAttrString(value, "y")) {
        PyObject* xobj = PyObject_GetAttrString(value, "x");
        PyObject* yobj = PyObject_GetAttrString(value, "y");
        x = PyFloat_AsDouble(xobj);
        y = PyFloat_AsDouble(yobj);
        Py_DECREF(xobj);
        Py_DECREF(yobj);
    } else {
        PyErr_SetString(PyExc_TypeError, "pos must be a tuple (x, y) or Vector");
        return -1;
    }

    self->scene->position = sf::Vector2f(x, y);
    return 0;
}

// #118: Scene visible getter
static PyObject* PySceneClass_get_visible(PySceneObject* self, void* closure)
{
    if (!self->scene) {
        Py_RETURN_TRUE;
    }

    return PyBool_FromLong(self->scene->visible);
}

// #118: Scene visible setter
static int PySceneClass_set_visible(PySceneObject* self, PyObject* value, void* closure)
{
    if (!self->scene) {
        PyErr_SetString(PyExc_RuntimeError, "Scene not initialized");
        return -1;
    }

    if (!PyBool_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "visible must be a boolean");
        return -1;
    }

    self->scene->visible = PyObject_IsTrue(value);
    return 0;
}

// #118: Scene opacity getter
static PyObject* PySceneClass_get_opacity(PySceneObject* self, void* closure)
{
    if (!self->scene) {
        return PyFloat_FromDouble(1.0);
    }

    return PyFloat_FromDouble(self->scene->opacity);
}

// #118: Scene opacity setter
static int PySceneClass_set_opacity(PySceneObject* self, PyObject* value, void* closure)
{
    if (!self->scene) {
        PyErr_SetString(PyExc_RuntimeError, "Scene not initialized");
        return -1;
    }

    double opacity;
    if (PyFloat_Check(value)) {
        opacity = PyFloat_AsDouble(value);
    } else if (PyLong_Check(value)) {
        opacity = PyLong_AsDouble(value);
    } else {
        PyErr_SetString(PyExc_TypeError, "opacity must be a number");
        return -1;
    }

    // Clamp to valid range
    if (opacity < 0.0) opacity = 0.0;
    if (opacity > 1.0) opacity = 1.0;

    self->scene->opacity = opacity;
    return 0;
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
        Py_DECREF(method);
    } else {
        // Clear AttributeError if method doesn't exist
        PyErr_Clear();
        Py_XDECREF(method);
    }
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
        Py_DECREF(method);
    } else {
        // Clear AttributeError if method doesn't exist
        PyErr_Clear();
        Py_XDECREF(method);
    }
}

void PySceneClass::call_on_key(PySceneObject* self, const std::string& key, const std::string& action)
{
    PyGILState_STATE gstate = PyGILState_Ensure();

    // Look for on_key attribute on the Python object
    // This handles both:
    // 1. Subclass methods: class MyScene(Scene): def on_key(self, key, action): ...
    // 2. Instance attributes: ts.on_key = lambda k, a: ...  (when subclass shadows property)
    PyObject* attr = PyObject_GetAttrString((PyObject*)self, "on_key");
    if (attr && PyCallable_Check(attr) && attr != Py_None) {
        // Convert key string to Key enum
        sf::Keyboard::Key sfml_key = PyKey::from_legacy_string(key.c_str());
        PyObject* key_enum = PyObject_CallFunction(PyKey::key_enum_class, "i", static_cast<int>(sfml_key));
        if (!key_enum) {
            std::cerr << "Failed to create Key enum for key: " << key << std::endl;
            PyErr_Print();
            Py_DECREF(attr);
            PyGILState_Release(gstate);
            return;
        }

        // Convert action string to InputState enum
        int action_val = (action == "start" || action == "pressed") ? 0 : 1;  // PRESSED = 0, RELEASED = 1
        PyObject* action_enum = PyObject_CallFunction(PyInputState::input_state_enum_class, "i", action_val);
        if (!action_enum) {
            std::cerr << "Failed to create InputState enum for action: " << action << std::endl;
            Py_DECREF(key_enum);
            PyErr_Print();
            Py_DECREF(attr);
            PyGILState_Release(gstate);
            return;
        }

        // Call it with typed args - works for both bound methods and regular callables
        PyObject* result = PyObject_CallFunctionObjArgs(attr, key_enum, action_enum, NULL);
        Py_DECREF(key_enum);
        Py_DECREF(action_enum);

        if (result) {
            Py_DECREF(result);
        } else {
            PyErr_Print();
        }
        Py_DECREF(attr);
    } else {
        // Not callable or is None - nothing to call
        PyErr_Clear();
        Py_XDECREF(attr);
    }

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
        Py_DECREF(method);
    } else {
        // Clear AttributeError if method doesn't exist
        PyErr_Clear();
        Py_XDECREF(method);
    }
}

void PySceneClass::call_on_resize(PySceneObject* self, sf::Vector2u new_size)
{
    PyObject* method = PyObject_GetAttrString((PyObject*)self, "on_resize");
    if (method && PyCallable_Check(method)) {
        // Create a Vector object to pass
        auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
        if (!type) {
            PyErr_Print();
            Py_DECREF(method);
            return;
        }
        PyObject* args = Py_BuildValue("(ff)", (float)new_size.x, (float)new_size.y);
        PyObject* vector = PyObject_CallObject((PyObject*)type, args);
        Py_DECREF(type);
        Py_DECREF(args);

        if (!vector) {
            PyErr_Print();
            Py_DECREF(method);
            return;
        }

        PyObject* result = PyObject_CallFunctionObjArgs(method, vector, NULL);
        Py_DECREF(vector);
        if (result) {
            Py_DECREF(result);
        } else {
            PyErr_Print();
        }
        Py_DECREF(method);
    } else {
        // Clear AttributeError if method doesn't exist
        PyErr_Clear();
        Py_XDECREF(method);
    }
}

// registered property getter
static PyObject* PySceneClass_get_registered(PySceneObject* self, void* closure)
{
    GameEngine* game = McRFPy_API::game;
    if (!game || !self->scene) {
        Py_RETURN_FALSE;
    }

    // Check if THIS scene object is the one registered under this name
    // (not just that a scene with this name exists)
    Scene* registered_scene = game->getScene(self->name);
    return PyBool_FromLong(registered_scene == self->scene.get());
}

// Properties
PyGetSetDef PySceneClass::getsetters[] = {
    {"name", (getter)get_name, NULL,
     MCRF_PROPERTY(name, "Scene name (str, read-only). Unique identifier for this scene."), NULL},
    {"active", (getter)get_active, NULL,
     MCRF_PROPERTY(active, "Whether this scene is currently active (bool, read-only). Only one scene can be active at a time."), NULL},
    {"registered", (getter)PySceneClass_get_registered, NULL,
     MCRF_PROPERTY(registered, "Whether this scene is registered with the game engine (bool, read-only). "
         "Unregistered scenes still exist but won't receive lifecycle callbacks."), NULL},
    // #118: Scene-level UIDrawable-like properties
    {"pos", (getter)PySceneClass_get_pos, (setter)PySceneClass_set_pos,
     MCRF_PROPERTY(pos, "Scene position offset (Vector). Applied to all UI elements during rendering."), NULL},
    {"visible", (getter)PySceneClass_get_visible, (setter)PySceneClass_set_visible,
     MCRF_PROPERTY(visible, "Scene visibility (bool). If False, scene is not rendered."), NULL},
    {"opacity", (getter)PySceneClass_get_opacity, (setter)PySceneClass_set_opacity,
     MCRF_PROPERTY(opacity, "Scene opacity (0.0-1.0). Applied to all UI elements during rendering."), NULL},
    // #151: Consistent Scene API
    {"children", (getter)PySceneClass_get_children, NULL,
     MCRF_PROPERTY(children, "UI element collection for this scene (UICollection, read-only). "
         "Use to add, remove, or iterate over UI elements. Changes are reflected immediately."), NULL},
    {"on_key", (getter)PySceneClass_get_on_key, (setter)PySceneClass_set_on_key,
     MCRF_PROPERTY(on_key, "Keyboard event handler (callable or None). "
         "Function receives (key: Key, action: InputState) for keyboard events. "
         "Set to None to remove the handler."), NULL},
    {NULL}
};

// Scene.realign() - recalculate alignment for all children
static PyObject* PySceneClass_realign(PySceneObject* self, PyObject* args)
{
    if (!self->scene || !self->scene->ui_elements) {
        Py_RETURN_NONE;
    }

    // Iterate through all UI elements and realign those with alignment set
    for (auto& drawable : *self->scene->ui_elements) {
        if (drawable && drawable->align_type != AlignmentType::NONE) {
            drawable->applyAlignment();
        }
    }

    Py_RETURN_NONE;
}

// Scene.register() - add scene to GameEngine's registry
static PyObject* PySceneClass_register(PySceneObject* self, PyObject* args)
{
    GameEngine* game = McRFPy_API::game;
    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "No game engine");
        return NULL;
    }

    if (!self->scene) {
        PyErr_SetString(PyExc_RuntimeError, "Scene not initialized");
        return NULL;
    }

    // If another scene with this name is registered, unregister it first
    if (python_scenes.count(self->name) > 0 && python_scenes[self->name] != self) {
        PySceneObject* old = python_scenes[self->name];
        Py_DECREF(old);
        python_scenes.erase(self->name);
    }

    // Unregister from GameEngine (removes old reference if any)
    game->unregisterScene(self->name);

    // Register this scene with GameEngine
    game->registerScene(self->name, self->scene);

    // Register in python_scenes if not already
    if (python_scenes.count(self->name) == 0 || python_scenes[self->name] != self) {
        python_scenes[self->name] = self;
        Py_INCREF(self);
    }

    Py_RETURN_NONE;
}

// Scene.unregister() - remove scene from GameEngine's registry (but keep Python object alive)
static PyObject* PySceneClass_unregister(PySceneObject* self, PyObject* args)
{
    GameEngine* game = McRFPy_API::game;
    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "No game engine");
        return NULL;
    }

    // Remove from GameEngine's scenes map
    game->unregisterScene(self->name);

    // Remove from python_scenes callback registry
    if (python_scenes.count(self->name) > 0 && python_scenes[self->name] == self) {
        Py_DECREF(self);
        python_scenes.erase(self->name);
    }

    // Note: self->scene shared_ptr still holds the C++ object!
    // The scene survives because this PySceneObject still has a reference

    Py_RETURN_NONE;
}

// Methods
PyMethodDef PySceneClass::methods[] = {
    {"activate", (PyCFunction)activate, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(SceneClass, activate,
         MCRF_SIG("(transition: Transition = None, duration: float = None)", "None"),
         MCRF_DESC("Make this the active scene with optional transition effect."),
         MCRF_ARGS_START
         MCRF_ARG("transition", "Transition type (mcrfpy.Transition enum). Defaults to mcrfpy.default_transition")
         MCRF_ARG("duration", "Transition duration in seconds. Defaults to mcrfpy.default_transition_duration")
         MCRF_RETURNS("None")
         MCRF_NOTE("Deactivates the current scene and activates this one. Lifecycle callbacks (on_exit, on_enter) are triggered.")
     )},
    {"realign", (PyCFunction)PySceneClass_realign, METH_NOARGS,
     MCRF_METHOD(SceneClass, realign,
         MCRF_SIG("()", "None"),
         MCRF_DESC("Recalculate alignment for all children with alignment set."),
         MCRF_NOTE("Call this after window resize or when game_resolution changes. "
                   "For responsive layouts, connect this to on_resize callback.")
     )},
    {"register", (PyCFunction)PySceneClass_register, METH_NOARGS,
     MCRF_METHOD(SceneClass, register,
         MCRF_SIG("()", "None"),
         MCRF_DESC("Register this scene with the game engine."),
         MCRF_NOTE("Makes the scene available for activation and receives lifecycle callbacks. "
                   "If another scene with the same name exists, it will be unregistered first. "
                   "Called automatically by activate() if needed.")
     )},
    {"unregister", (PyCFunction)PySceneClass_unregister, METH_NOARGS,
     MCRF_METHOD(SceneClass, unregister,
         MCRF_SIG("()", "None"),
         MCRF_DESC("Unregister this scene from the game engine."),
         MCRF_NOTE("Removes the scene from the engine's registry but keeps the Python object alive. "
                   "The scene's UI elements and state are preserved. Call register() to re-add it. "
                   "Useful for temporary scenes or scene pooling.")
     )},
    {NULL}
};

// #183: Lookup scene by name (returns new reference or nullptr)
PyObject* PySceneClass::get_scene_by_name(const std::string& name)
{
    if (name.empty()) return nullptr;

    if (python_scenes.count(name) > 0) {
        PyObject* scene_obj = (PyObject*)python_scenes[name];
        Py_INCREF(scene_obj);
        return scene_obj;
    }

    return nullptr;
}

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
void McRFPy_API::triggerResize(sf::Vector2u new_size)
{
    GameEngine* game = McRFPy_API::game;
    if (!game) return;

    // Only notify the active scene
    if (python_scenes.count(game->scene) > 0) {
        PySceneClass::call_on_resize(python_scenes[game->scene], new_size);
    }
}

// Helper function to trigger key events on Python scene subclasses
void McRFPy_API::triggerKeyEvent(const std::string& key, const std::string& action)
{
    GameEngine* game = McRFPy_API::game;
    if (!game) return;

    // Only notify the active scene if it has an on_key method (subclass)
    if (python_scenes.count(game->scene) > 0) {
        PySceneClass::call_on_key(python_scenes[game->scene], key, action);
    }
}

// #151: Get the current scene as a Python Scene object
PyObject* McRFPy_API::api_get_current_scene()
{
    GameEngine* game = McRFPy_API::game;
    if (!game) {
        Py_RETURN_NONE;
    }

    const std::string& current_name = game->scene;
    if (python_scenes.count(current_name) > 0) {
        PyObject* scene_obj = (PyObject*)python_scenes[current_name];
        Py_INCREF(scene_obj);
        return scene_obj;
    }

    // Scene exists but wasn't created via Python Scene class
    Py_RETURN_NONE;
}

// #151: Set the current scene from a Python Scene object
int McRFPy_API::api_set_current_scene(PyObject* value)
{
    GameEngine* game = McRFPy_API::game;
    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "No game engine");
        return -1;
    }

    if (!value) {
        PyErr_SetString(PyExc_ValueError, "value is NULL");
        return -1;
    }

    // Accept Scene object or string name
    const char* scene_name = nullptr;

    if (PyUnicode_Check(value)) {
        scene_name = PyUnicode_AsUTF8(value);
    } else {
        // Check if value is a Scene or Scene subclass - use same pattern as rest of codebase
        PyObject* scene_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "Scene");
        if (scene_type && PyObject_IsInstance(value, scene_type)) {
            Py_DECREF(scene_type);
            PySceneObject* scene_obj = (PySceneObject*)value;
            scene_name = scene_obj->name.c_str();
        } else {
            Py_XDECREF(scene_type);
            PyErr_SetString(PyExc_TypeError, "current_scene must be a Scene object or scene name string");
            return -1;
        }
    }

    if (!scene_name) {
        PyErr_SetString(PyExc_ValueError, "Invalid scene name");
        return -1;
    }

    // Verify scene exists
    if (!game->getScene(scene_name)) {
        PyErr_Format(PyExc_KeyError, "Scene '%s' does not exist", scene_name);
        return -1;
    }

    // Use changeScene with default transition settings
    game->changeScene(scene_name, PyTransition::default_transition, PyTransition::default_duration);

    return 0;
}

// #151: Get all scenes as a tuple of Python Scene objects
PyObject* McRFPy_API::api_get_scenes()
{
    PyObject* tuple = PyTuple_New(python_scenes.size());
    if (!tuple) return NULL;

    Py_ssize_t i = 0;
    for (auto& pair : python_scenes) {
        PyObject* scene_obj = (PyObject*)pair.second;
        Py_INCREF(scene_obj);
        PyTuple_SET_ITEM(tuple, i, scene_obj);
        i++;
    }

    return tuple;
}