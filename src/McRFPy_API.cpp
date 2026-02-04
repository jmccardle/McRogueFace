#include "McRFPy_API.h"
#include "UIDrawable.h"
#include "McRFPy_Automation.h"
// Note: McRFPy_Libtcod.h removed in #215 - functionality moved to mcrfpy.bresenham()
#include "McRFPy_Doc.h"
#include "PyTypeCache.h"  // Thread-safe cached Python types
#include "platform.h"
#include "PyAnimation.h"
#include "PyDrawable.h"
#include "PyTimer.h"
#include "PyWindow.h"
#include "PySceneObject.h"
#include "PyFOV.h"
#include "PyTransition.h"
#include "PyEasing.h"
#include "PyAlignment.h"
#include "PyKey.h"
#include "PyMouseButton.h"
#include "PyInputState.h"
#include "PySound.h"
#include "PyMusic.h"
#include "PyKeyboard.h"
#include "PyMouse.h"
#include "UIGridPathfinding.h"  // AStarPath and DijkstraMap types
#include "PyHeightMap.h"  // Procedural generation heightmap (#193)
#include "PyDiscreteMap.h"  // Procedural generation discrete map (#193)
#include "PyBSP.h"  // Procedural generation BSP (#202-206)
#include "PyNoiseSource.h"  // Procedural generation noise (#207-208)
#include "PyLock.h"  // Thread synchronization (#219)
#include "PyVector.h"  // For bresenham Vector support (#215)
#include "PyShader.h"  // Shader support (#106)
#include "PyUniformBinding.h"  // Shader uniform bindings (#106)
#include "PyUniformCollection.h"  // Shader uniform collection (#106)
#include "McRogueFaceVersion.h"
#include "GameEngine.h"
// ImGui is only available for SFML builds
#if !defined(MCRF_HEADLESS) && !defined(MCRF_SDL2)
#include "ImGuiConsole.h"
#endif
#include "BenchmarkLogger.h"
#include "UI.h"
#include "UILine.h"
#include "UICircle.h"
#include "UIArc.h"
#include "GridLayers.h"
#include "Resources.h"
#include "PyScene.h"
#include "PythonObjectCache.h"
#include <filesystem>
#include <fstream>
#include <cstring>
#include <libtcod.h>

std::shared_ptr<PyFont> McRFPy_API::default_font;
std::shared_ptr<PyTexture> McRFPy_API::default_texture;
PyObject* McRFPy_API::mcrf_module;

// Exception handling state
std::atomic<bool> McRFPy_API::exception_occurred{false};
std::atomic<int> McRFPy_API::exit_code{0};

// ============================================================================
// #184: Metaclass for UI types - tracks callback generation for cache invalidation
// ============================================================================

// tp_setattro for the metaclass - intercepts class attribute assignments
static int McRFPyMetaclass_setattro(PyObject* type, PyObject* name, PyObject* value) {
    // First, do the normal attribute set on the class
    int result = PyType_Type.tp_setattro(type, name, value);
    if (result < 0) return result;

    // Check if it's a callback attribute (on_click, on_enter, on_exit, on_move)
    const char* attr_name = PyUnicode_AsUTF8(name);
    if (attr_name && strncmp(attr_name, "on_", 3) == 0) {
        // Check if it's one of our callback names
        if (strcmp(attr_name, "on_click") == 0 ||
            strcmp(attr_name, "on_enter") == 0 ||
            strcmp(attr_name, "on_exit") == 0 ||
            strcmp(attr_name, "on_move") == 0) {
            // Increment the callback generation for this class
            UIDrawable::incrementCallbackGeneration(type);
        }
    }

    return 0;
}

// The metaclass type object - initialized in api_init() because
// designated initializers in C++ require declaration order
static PyTypeObject McRFPyMetaclassType = {PyVarObject_HEAD_INIT(&PyType_Type, 0)};
static bool McRFPyMetaclass_initialized = false;

// ============================================================================

// #151: Module-level __getattr__ for dynamic properties (current_scene, scenes)
static PyObject* mcrfpy_module_getattr(PyObject* self, PyObject* args)
{
    const char* name;
    if (!PyArg_ParseTuple(args, "s", &name)) {
        return NULL;
    }

    if (strcmp(name, "current_scene") == 0) {
        return McRFPy_API::api_get_current_scene();
    }

    if (strcmp(name, "scenes") == 0) {
        return McRFPy_API::api_get_scenes();
    }

    if (strcmp(name, "timers") == 0) {
        return McRFPy_API::api_get_timers();
    }

    if (strcmp(name, "animations") == 0) {
        return McRFPy_API::api_get_animations();
    }

    if (strcmp(name, "default_transition") == 0) {
        return PyTransition::to_python(PyTransition::default_transition);
    }

    if (strcmp(name, "default_transition_duration") == 0) {
        return PyFloat_FromDouble(PyTransition::default_duration);
    }

    // Attribute not found - raise AttributeError
    PyErr_Format(PyExc_AttributeError, "module 'mcrfpy' has no attribute '%s'", name);
    return NULL;
}

// #151: Custom module type with __setattr__ support for current_scene
static int mcrfpy_module_setattro(PyObject* self, PyObject* name, PyObject* value)
{
    const char* name_str = PyUnicode_AsUTF8(name);
    if (!name_str) return -1;

    if (strcmp(name_str, "current_scene") == 0) {
        return McRFPy_API::api_set_current_scene(value);
    }

    if (strcmp(name_str, "scenes") == 0) {
        PyErr_SetString(PyExc_AttributeError, "'scenes' is read-only");
        return -1;
    }

    if (strcmp(name_str, "timers") == 0) {
        PyErr_SetString(PyExc_AttributeError, "'timers' is read-only");
        return -1;
    }

    if (strcmp(name_str, "animations") == 0) {
        PyErr_SetString(PyExc_AttributeError, "'animations' is read-only");
        return -1;
    }

    if (strcmp(name_str, "default_transition") == 0) {
        TransitionType trans;
        if (!PyTransition::from_arg(value, &trans, nullptr)) {
            return -1;
        }
        PyTransition::default_transition = trans;
        return 0;
    }

    if (strcmp(name_str, "default_transition_duration") == 0) {
        double duration;
        if (PyFloat_Check(value)) {
            duration = PyFloat_AsDouble(value);
        } else if (PyLong_Check(value)) {
            duration = PyLong_AsDouble(value);
        } else {
            PyErr_SetString(PyExc_TypeError, "default_transition_duration must be a number");
            return -1;
        }
        if (duration < 0.0) {
            PyErr_SetString(PyExc_ValueError, "default_transition_duration must be non-negative");
            return -1;
        }
        PyTransition::default_duration = static_cast<float>(duration);
        return 0;
    }

    // For other attributes, use default module setattr
    return PyObject_GenericSetAttr(self, name, value);
}

// Custom module type that inherits from PyModule_Type but has our __setattr__
static PyTypeObject McRFPyModuleType = {
    .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
    .tp_name = "mcrfpy.module",
    .tp_basicsize = 0,  // Inherited from base
    .tp_itemsize = 0,
    .tp_dealloc = NULL,
    .tp_vectorcall_offset = 0,
    .tp_getattr = NULL,
    .tp_setattr = NULL,
    .tp_as_async = NULL,
    .tp_repr = NULL,
    .tp_as_number = NULL,
    .tp_as_sequence = NULL,
    .tp_as_mapping = NULL,
    .tp_hash = NULL,
    .tp_call = NULL,
    .tp_str = NULL,
    .tp_getattro = NULL,
    .tp_setattro = mcrfpy_module_setattro,
    .tp_as_buffer = NULL,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_doc = "McRogueFace module with property support",
};

static PyMethodDef mcrfpyMethods[] = {

    // Note: setTimer and delTimer removed in #173 - use Timer objects instead
    {"step", McRFPy_API::_step, METH_VARARGS,
     MCRF_FUNCTION(step,
         MCRF_SIG("(dt: float = None)", "float"),
         MCRF_DESC("Advance simulation time (headless mode only)."),
         MCRF_ARGS_START
         MCRF_ARG("dt", "Time to advance in seconds. If None, advances to the next scheduled event (timer/animation).")
         MCRF_RETURNS("float: Actual time advanced in seconds. Returns 0.0 in windowed mode.")
         MCRF_NOTE("In windowed mode, this is a no-op and returns 0.0. Use this for deterministic simulation control in headless/testing scenarios.")
     )},
    {"exit", McRFPy_API::_exit, METH_NOARGS,
     MCRF_FUNCTION(exit,
         MCRF_SIG("()", "None"),
         MCRF_DESC("Cleanly shut down the game engine and exit the application."),
         MCRF_RETURNS("None")
         MCRF_NOTE("This immediately closes the window and terminates the program.")
     )},
    {"setScale", McRFPy_API::_setScale, METH_VARARGS,
     MCRF_FUNCTION(setScale,
         MCRF_SIG("(multiplier: float)", "None"),
         MCRF_DESC("Scale the game window size."),
         MCRF_ARGS_START
         MCRF_ARG("multiplier", "Scale factor (e.g., 2.0 for double size)")
         MCRF_RETURNS("None")
         MCRF_NOTE("The internal resolution remains 1024x768, but the window is scaled. This is deprecated - use Window.resolution instead.")
     )},

    {"find", McRFPy_API::_find, METH_VARARGS,
     MCRF_FUNCTION(find,
         MCRF_SIG("(name: str, scene: str = None)", "UIDrawable | None"),
         MCRF_DESC("Find the first UI element with the specified name."),
         MCRF_ARGS_START
         MCRF_ARG("name", "Exact name to search for")
         MCRF_ARG("scene", "Scene to search in (default: current scene)")
         MCRF_RETURNS("Frame, Caption, Sprite, Grid, or Entity if found; None otherwise")
         MCRF_NOTE("Searches scene UI elements and entities within grids.")
     )},
    {"findAll", McRFPy_API::_findAll, METH_VARARGS,
     MCRF_FUNCTION(findAll,
         MCRF_SIG("(pattern: str, scene: str = None)", "list"),
         MCRF_DESC("Find all UI elements matching a name pattern."),
         MCRF_ARGS_START
         MCRF_ARG("pattern", "Name pattern with optional wildcards (* matches any characters)")
         MCRF_ARG("scene", "Scene to search in (default: current scene)")
         MCRF_RETURNS("list: All matching UI elements and entities")
         MCRF_NOTE("Example: findAll('enemy*') finds all elements starting with 'enemy', findAll('*_button') finds all elements ending with '_button'")
     )},

    {"getMetrics", McRFPy_API::_getMetrics, METH_NOARGS,
     MCRF_FUNCTION(getMetrics,
         MCRF_SIG("()", "dict"),
         MCRF_DESC("Get current performance metrics."),
         MCRF_RETURNS("dict: Performance data with keys: frame_time (last frame duration in seconds), avg_frame_time (average frame time), fps (frames per second), draw_calls (number of draw calls), ui_elements (total UI element count), visible_elements (visible element count), current_frame (frame counter), runtime (total runtime in seconds)")
     )},

    {"setDevConsole", McRFPy_API::_setDevConsole, METH_VARARGS,
     MCRF_FUNCTION(setDevConsole,
         MCRF_SIG("(enabled: bool)", "None"),
         MCRF_DESC("Enable or disable the developer console overlay."),
         MCRF_ARGS_START
         MCRF_ARG("enabled", "True to enable the console (default), False to disable")
         MCRF_RETURNS("None")
         MCRF_NOTE("When disabled, the grave/tilde key will not open the console. Use this to ship games without debug features.")
     )},

    {"start_benchmark", McRFPy_API::_startBenchmark, METH_NOARGS,
     MCRF_FUNCTION(start_benchmark,
         MCRF_SIG("()", "None"),
         MCRF_DESC("Start capturing benchmark data to a file."),
         MCRF_RETURNS("None")
         MCRF_RAISES("RuntimeError", "If a benchmark is already running")
         MCRF_NOTE("Benchmark filename is auto-generated from PID and timestamp. Use end_benchmark() to stop and get filename.")
     )},

    {"end_benchmark", McRFPy_API::_endBenchmark, METH_NOARGS,
     MCRF_FUNCTION(end_benchmark,
         MCRF_SIG("()", "str"),
         MCRF_DESC("Stop benchmark capture and write data to JSON file."),
         MCRF_RETURNS("str: The filename of the written benchmark data")
         MCRF_RAISES("RuntimeError", "If no benchmark is currently running")
         MCRF_NOTE("Returns the auto-generated filename (e.g., 'benchmark_12345_20250528_143022.json')")
     )},

    {"log_benchmark", McRFPy_API::_logBenchmark, METH_VARARGS,
     MCRF_FUNCTION(log_benchmark,
         MCRF_SIG("(message: str)", "None"),
         MCRF_DESC("Add a log message to the current benchmark frame."),
         MCRF_ARGS_START
         MCRF_ARG("message", "Text to associate with the current frame")
         MCRF_RETURNS("None")
         MCRF_RAISES("RuntimeError", "If no benchmark is currently running")
         MCRF_NOTE("Messages appear in the 'logs' array of each frame in the output JSON.")
     )},

    // #151: Module-level attribute access for current_scene and scenes
    {"__getattr__", mcrfpy_module_getattr, METH_VARARGS,
     "Module-level __getattr__ for dynamic properties (current_scene, scenes)"},

    // #219: Thread synchronization
    {"lock", PyLock::lock, METH_NOARGS,
     MCRF_FUNCTION(lock,
         MCRF_SIG("()", "_LockContext"),
         MCRF_DESC("Get a context manager for thread-safe UI updates from background threads."),
         MCRF_RETURNS("_LockContext: A context manager that blocks until safe to modify UI")
         MCRF_NOTE("Use with `with mcrfpy.lock():` to safely modify UI objects from a background thread. "
                   "The context manager blocks until the render loop reaches a safe point between frames. "
                   "Without this, modifying UI from threads may cause visual glitches or crashes.")
     )},

    // #215: Bresenham line algorithm (replaces mcrfpy.libtcod.line)
    {"bresenham", (PyCFunction)McRFPy_API::_bresenham, METH_VARARGS | METH_KEYWORDS,
     MCRF_FUNCTION(bresenham,
         MCRF_SIG("(start, end, *, include_start=True, include_end=True)", "list[tuple[int, int]]"),
         MCRF_DESC("Compute grid cells along a line using Bresenham's algorithm."),
         MCRF_ARGS_START
         MCRF_ARG("start", "(x, y) tuple or Vector - starting point")
         MCRF_ARG("end", "(x, y) tuple or Vector - ending point")
         MCRF_ARG("include_start", "Include the starting point in results (default: True)")
         MCRF_ARG("include_end", "Include the ending point in results (default: True)")
         MCRF_RETURNS("list[tuple[int, int]]: List of (x, y) grid coordinates along the line")
         MCRF_NOTE("Useful for line-of-sight checks, projectile paths, and drawing lines on grids. "
                   "The algorithm ensures minimal grid traversal between two points.")
     )},

    {NULL, NULL, 0, NULL}
};

static PyModuleDef mcrfpyModule = {
    PyModuleDef_HEAD_INIT, /* m_base - Always initialize this member to PyModuleDef_HEAD_INIT. */
    "mcrfpy",              /* m_name */
    PyDoc_STR("McRogueFace Python API\n\n"
              "Core game engine interface for creating roguelike games with Python.\n\n"
              "This module provides:\n"
              "- Scene management via Scene objects (mcrfpy.Scene, mcrfpy.current_scene)\n"
              "- UI components (Frame, Caption, Sprite, Grid)\n"
              "- Entity system for game objects\n"
              "- Audio playback (sound effects and music)\n"
              "- Timer system for scheduled events\n"
              "- Input handling\n"
              "- Performance metrics\n\n"
              "Example:\n"
              "    import mcrfpy\n"
              "    \n"
              "    # Create and activate a scene\n"
              "    scene = mcrfpy.Scene('game')\n"
              "    scene.activate()\n"
              "    \n"
              "    # Add UI elements\n"
              "    frame = mcrfpy.Frame(10, 10, 200, 100)\n"
              "    caption = mcrfpy.Caption('Hello World', 50, 50)\n"
              "    scene.children.extend([frame, caption])\n"
              "    \n"
              "    # Set keyboard handler\n"
              "    scene.on_key = lambda key, action: print(f'{key} {action}')\n"),
    -1,                    /* m_size - Setting m_size to -1 means that the module does not support sub-interpreters, because it has global state. */
    mcrfpyMethods,         /* m_methods */
    NULL,                  /* m_slots - An array of slot definitions ...  When using single-phase initialization, m_slots must be NULL. */
    NULL,                  /* traverseproc m_traverse - A traversal function to call during GC traversal of the module object */
    NULL,                  /* inquiry m_clear - A clear function to call during GC clearing of the module object */
    NULL                   /* freefunc m_free - A function to call during deallocation of the module object */
};

// Module initializer fn, passed to PyImport_AppendInittab
PyObject* PyInit_mcrfpy()
{
    PyObject* m = PyModule_Create(&mcrfpyModule);

    if (m == NULL)
    {
        return NULL;
    }

    // #151: Set up custom module type for current_scene/scenes property support
    // The custom type inherits from PyModule_Type and adds __setattr__ handling
    McRFPyModuleType.tp_base = &PyModule_Type;
    if (PyType_Ready(&McRFPyModuleType) < 0) {
        std::cout << "ERROR: PyType_Ready failed for McRFPyModuleType" << std::endl;
        return NULL;
    }
    // Change the module's type to our custom type
    Py_SET_TYPE(m, &McRFPyModuleType);

    // #184: Set up the UI metaclass for callback generation tracking
    if (!McRFPyMetaclass_initialized) {
        McRFPyMetaclassType.tp_name = "mcrfpy._UIMetaclass";
        McRFPyMetaclassType.tp_basicsize = sizeof(PyHeapTypeObject);
        McRFPyMetaclassType.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE;
        McRFPyMetaclassType.tp_doc = PyDoc_STR("Metaclass for UI types that tracks callback method changes");
        McRFPyMetaclassType.tp_setattro = McRFPyMetaclass_setattro;
        McRFPyMetaclassType.tp_base = &PyType_Type;
        McRFPyMetaclass_initialized = true;
    }
    if (PyType_Ready(&McRFPyMetaclassType) < 0) {
        std::cout << "ERROR: PyType_Ready failed for McRFPyMetaclassType" << std::endl;
        return NULL;
    }

    using namespace mcrfpydef;

    // #184: Set the metaclass for UI types that support callback methods
    // This must be done BEFORE PyType_Ready is called on these types
    PyTypeObject* ui_types_with_callbacks[] = {
        &PyUIFrameType, &PyUICaptionType, &PyUISpriteType, &PyUIGridType,
        &PyUILineType, &PyUICircleType, &PyUIArcType,
        nullptr
    };
    for (int i = 0; ui_types_with_callbacks[i] != nullptr; i++) {
        Py_SET_TYPE(ui_types_with_callbacks[i], &McRFPyMetaclassType);
    }

    // Types that are exported to Python (visible in module namespace)
    PyTypeObject* exported_types[] = {
        /*SFML exposed types*/
        &PyColorType, /*&PyLinkedColorType,*/ &PyFontType, &PyTextureType, &PyVectorType,

        /*Base classes*/
        &PyDrawableType,

        /*UI widgets*/
        &PyUICaptionType, &PyUISpriteType, &PyUIFrameType, &PyUIEntityType, &PyUIGridType,
        &PyUILineType, &PyUICircleType, &PyUIArcType,

        /*grid layers (#147)*/
        &PyColorLayerType, &PyTileLayerType,

        /*animation*/
        &PyAnimationType,

        /*timer*/
        &PyTimerType,

        /*window singleton type (#184 - type exported for isinstance checks)*/
        &PyWindowType,

        /*scene class*/
        &PySceneType,

        /*audio (#66)*/
        &PySoundType,
        &PyMusicType,

        /*keyboard state (#160)*/
        &PyKeyboardType,

        /*mouse state (#186)*/
        &PyMouseType,

        /*pathfinding result types*/
        &mcrfpydef::PyAStarPathType,
        &mcrfpydef::PyDijkstraMapType,

        /*procedural generation (#192)*/
        &mcrfpydef::PyHeightMapType,
        &mcrfpydef::PyDiscreteMapType,
        &mcrfpydef::PyBSPType,
        &mcrfpydef::PyNoiseSourceType,

        /*shaders (#106)*/
        &mcrfpydef::PyShaderType,
        &mcrfpydef::PyPropertyBindingType,
        &mcrfpydef::PyCallableBindingType,

        nullptr};

    // Types that are used internally but NOT exported to module namespace (#189)
    // These still need PyType_Ready() but are not added to module
    PyTypeObject* internal_types[] = {
        /*game map & perspective data - returned by Grid.at() but not directly instantiable*/
        &PyUIGridPointType, &PyUIGridPointStateType,

        /*collections & iterators - returned by .children/.entities but not directly instantiable*/
        &PyUICollectionType, &PyUICollectionIterType,
        &PyUIEntityCollectionType, &PyUIEntityCollectionIterType,

        /*pathfinding iterator - returned by AStarPath.__iter__() but not directly instantiable*/
        &mcrfpydef::PyAStarPathIterType,

        /*BSP internal types - returned by BSP methods but not directly instantiable*/
        &mcrfpydef::PyBSPNodeType,
        &mcrfpydef::PyBSPIterType,
        &mcrfpydef::PyBSPAdjacencyType,      // #210: BSP.adjacency wrapper
        &mcrfpydef::PyBSPAdjacentTilesType,  // #210: BSPNode.adjacent_tiles wrapper

        /*shader uniform collection - returned by drawable.uniforms but not directly instantiable (#106)*/
        &mcrfpydef::PyUniformCollectionType,

        nullptr};
    
    // Set up PyWindowType methods and getsetters before PyType_Ready
    PyWindowType.tp_methods = PyWindow::methods;
    PyWindowType.tp_getset = PyWindow::getsetters;
    
    // Set up PySceneType methods and getsetters
    PySceneType.tp_methods = PySceneClass::methods;
    PySceneType.tp_getset = PySceneClass::getsetters;

    // Set up PyHeightMapType methods and getsetters (#193)
    mcrfpydef::PyHeightMapType.tp_methods = PyHeightMap::methods;
    mcrfpydef::PyHeightMapType.tp_getset = PyHeightMap::getsetters;

    // Set up PyDiscreteMapType methods and getsetters (#193)
    mcrfpydef::PyDiscreteMapType.tp_methods = PyDiscreteMap::methods;
    mcrfpydef::PyDiscreteMapType.tp_getset = PyDiscreteMap::getsetters;

    // Set up PyBSPType and BSPNode methods and getsetters (#202-206)
    mcrfpydef::PyBSPType.tp_methods = PyBSP::methods;
    mcrfpydef::PyBSPType.tp_getset = PyBSP::getsetters;
    mcrfpydef::PyBSPNodeType.tp_methods = PyBSPNode::methods;
    mcrfpydef::PyBSPNodeType.tp_getset = PyBSPNode::getsetters;

    // Set up PyNoiseSourceType methods and getsetters (#207-208)
    mcrfpydef::PyNoiseSourceType.tp_methods = PyNoiseSource::methods;
    mcrfpydef::PyNoiseSourceType.tp_getset = PyNoiseSource::getsetters;

    // Set up PyShaderType methods and getsetters (#106)
    mcrfpydef::PyShaderType.tp_methods = PyShader::methods;
    mcrfpydef::PyShaderType.tp_getset = PyShader::getsetters;

    // Set up PyPropertyBindingType and PyCallableBindingType getsetters (#106)
    mcrfpydef::PyPropertyBindingType.tp_getset = PyPropertyBindingType::getsetters;
    mcrfpydef::PyCallableBindingType.tp_getset = PyCallableBindingType::getsetters;

    // Set up PyUniformCollectionType methods (#106)
    mcrfpydef::PyUniformCollectionType.tp_methods = ::PyUniformCollectionType::methods;

    // Set up weakref support for all types that need it
    PyTimerType.tp_weaklistoffset = offsetof(PyTimerObject, weakreflist);
    PyUIFrameType.tp_weaklistoffset = offsetof(PyUIFrameObject, weakreflist);
    PyUICaptionType.tp_weaklistoffset = offsetof(PyUICaptionObject, weakreflist);
    PyUISpriteType.tp_weaklistoffset = offsetof(PyUISpriteObject, weakreflist);
    PyUIGridType.tp_weaklistoffset = offsetof(PyUIGridObject, weakreflist);
    PyUIEntityType.tp_weaklistoffset = offsetof(PyUIEntityObject, weakreflist);
    PyUILineType.tp_weaklistoffset = offsetof(PyUILineObject, weakreflist);
    PyUICircleType.tp_weaklistoffset = offsetof(PyUICircleObject, weakreflist);
    PyUIArcType.tp_weaklistoffset = offsetof(PyUIArcObject, weakreflist);

    // #219 - Initialize PyLock context manager type
    if (PyLock::init() < 0) {
        std::cout << "ERROR: PyLock::init() failed" << std::endl;
        return NULL;
    }

    // Process exported types - PyType_Ready AND add to module
    int i = 0;
    auto t = exported_types[i];
    while (t != nullptr)
    {
        if (PyType_Ready(t) < 0) {
            std::cout << "ERROR: PyType_Ready failed for " << t->tp_name << std::endl;
            return NULL;
        }
        PyModule_AddType(m, t);
        i++;
        t = exported_types[i];
    }

    // Process internal types - PyType_Ready only, NOT added to module (#189)
    i = 0;
    t = internal_types[i];
    while (t != nullptr)
    {
        if (PyType_Ready(t) < 0) {
            std::cout << "ERROR: PyType_Ready failed for " << t->tp_name << std::endl;
            return NULL;
        }
        // Note: NOT calling PyModule_AddType - these are internal-only types
        i++;
        t = internal_types[i];
    }

    // Add default_font and default_texture to module
    McRFPy_API::default_font = std::make_shared<PyFont>("assets/JetbrainsMono.ttf");
    McRFPy_API::default_texture = std::make_shared<PyTexture>("assets/kenney_tinydungeon.png", 16, 16);
    // These will be set later when the window is created
    PyModule_AddObject(m, "default_font", Py_None);
    PyModule_AddObject(m, "default_texture", Py_None);

    // Add keyboard singleton (#160)
    PyObject* keyboard_instance = PyObject_CallObject((PyObject*)&PyKeyboardType, NULL);
    if (keyboard_instance) {
        PyModule_AddObject(m, "keyboard", keyboard_instance);
    }

    // Add mouse singleton (#186)
    PyObject* mouse_instance = PyObject_CallObject((PyObject*)&PyMouseType, NULL);
    if (mouse_instance) {
        PyModule_AddObject(m, "mouse", mouse_instance);
    }

    // Add window singleton (#184)
    // Use tp_alloc directly to bypass tp_new which blocks user instantiation
    PyObject* window_instance = PyWindowType.tp_alloc(&PyWindowType, 0);
    if (window_instance) {
        PyModule_AddObject(m, "window", window_instance);
    }

    // Add version string (#164)
    PyModule_AddStringConstant(m, "__version__", MCRFPY_VERSION);

    // Add FOV enum class (uses Python's IntEnum) (#114)
    PyObject* fov_class = PyFOV::create_enum_class(m);
    if (!fov_class) {
        // If enum creation fails, continue without it (non-fatal)
        PyErr_Clear();
    }

    // Add default_fov module property - defaults to FOV.BASIC
    // New grids copy this value at creation time
    if (fov_class) {
        PyObject* default_fov = PyObject_GetAttrString(fov_class, "BASIC");
        if (default_fov) {
            PyModule_AddObject(m, "default_fov", default_fov);
        } else {
            PyErr_Clear();
            // Fallback to integer
            PyModule_AddIntConstant(m, "default_fov", FOV_BASIC);
        }
    } else {
        // Fallback to integer if enum failed
        PyModule_AddIntConstant(m, "default_fov", FOV_BASIC);
    }

    // Add Transition enum class (uses Python's IntEnum)
    PyObject* transition_class = PyTransition::create_enum_class(m);
    if (!transition_class) {
        // If enum creation fails, continue without it (non-fatal)
        PyErr_Clear();
    }
    // Note: default_transition and default_transition_duration are handled via
    // mcrfpy_module_getattr/setattro using PyTransition::default_transition/default_duration

    // Add Easing enum class (uses Python's IntEnum)
    PyObject* easing_class = PyEasing::create_enum_class(m);
    if (!easing_class) {
        // If enum creation fails, continue without it (non-fatal)
        PyErr_Clear();
    }

    // Add Traversal enum class for BSP traversal (uses Python's IntEnum)
    PyObject* traversal_class = PyTraversal::create_enum_class(m);
    if (!traversal_class) {
        // If enum creation fails, continue without it (non-fatal)
        PyErr_Clear();
    }

    // Add Key enum class for keyboard input
    PyObject* key_class = PyKey::create_enum_class(m);
    if (!key_class) {
        // If enum creation fails, continue without it (non-fatal)
        PyErr_Clear();
    }

    // Add MouseButton enum class for mouse input
    PyObject* mouse_button_class = PyMouseButton::create_enum_class(m);
    if (!mouse_button_class) {
        // If enum creation fails, continue without it (non-fatal)
        PyErr_Clear();
    }

    // Add InputState enum class for input event states (pressed/released)
    PyObject* input_state_class = PyInputState::create_enum_class(m);
    if (!input_state_class) {
        // If enum creation fails, continue without it (non-fatal)
        PyErr_Clear();
    }

    // Add Alignment enum class for automatic child positioning
    PyObject* alignment_class = PyAlignment::create_enum_class(m);
    if (!alignment_class) {
        // If enum creation fails, continue without it (non-fatal)
        PyErr_Clear();
    }

    // Add automation submodule
    PyObject* automation_module = McRFPy_Automation::init_automation_module();
    if (automation_module != NULL) {
        PyModule_AddObject(m, "automation", automation_module);
        
        // Also add to sys.modules for proper import behavior
        PyObject* sys_modules = PyImport_GetModuleDict();
        PyDict_SetItemString(sys_modules, "mcrfpy.automation", automation_module);
    }

    // Note: mcrfpy.libtcod submodule removed in #215
    // - line() functionality replaced by mcrfpy.bresenham()
    // - compute_fov() redundant with Grid.compute_fov()

    // Initialize PyTypeCache for thread-safe type lookups
    // This must be done after all types are added to the module
    if (!PyTypeCache::initialize(m)) {
        // Failed to initialize type cache - this is a critical error
        // Error message already set by PyTypeCache::initialize
        return NULL;
    }

    //McRFPy_API::mcrf_module = m;
    return m;
}

// init_python - configure interpreter details here
PyStatus init_python(const char *program_name)
{
    PyStatus status;

    // Preconfig to establish locale
    PyPreConfig preconfig;
    PyPreConfig_InitIsolatedConfig(&preconfig);
    preconfig.utf8_mode = 1;

    status = Py_PreInitialize(&preconfig);
    if (PyStatus_Exception(status)) {
        Py_ExitStatusException(status);
    }

    PyConfig config;
    PyConfig_InitIsolatedConfig(&config);
    config.dev_mode = 0;

    // Configure UTF-8 for stdio
    PyConfig_SetString(&config, &config.stdio_encoding, L"UTF-8");
    PyConfig_SetString(&config, &config.stdio_errors, L"surrogateescape");
    config.configure_c_stdio = 1;

#ifdef __EMSCRIPTEN__
    // WASM: Use absolute paths in virtual filesystem
    PyConfig_SetString(&config, &config.executable, L"/mcrogueface");
    PyConfig_SetString(&config, &config.home, L"/lib/python3.14");
    status = PyConfig_SetBytesString(&config, &config.program_name, "mcrogueface");

    // Set up module search paths for WASM
    config.module_search_paths_set = 1;
    const wchar_t* wasm_paths[] = {
        L"/scripts",
        L"/lib/python3.14"
    };
    for (auto s : wasm_paths) {
        status = PyWideStringList_Append(&config.module_search_paths, s);
        if (PyStatus_Exception(status)) {
            continue;
        }
    }
#else
    // Set sys.executable to the McRogueFace binary path
    auto exe_filename = executable_filename();
    PyConfig_SetString(&config, &config.executable, exe_filename.c_str());

    PyConfig_SetBytesString(&config, &config.home,
        narrow_string(executable_path() + L"/lib/Python").c_str());

    status = PyConfig_SetBytesString(&config, &config.program_name,
                                     program_name);

    // Check for sibling venv/ directory (self-contained deployment)
    auto exe_dir = std::filesystem::path(executable_path());
    auto sibling_venv = exe_dir / "venv";
    if (std::filesystem::exists(sibling_venv)) {
        // Platform-specific site-packages path
#ifdef _WIN32
        auto site_packages = sibling_venv / "Lib" / "site-packages";
#else
        auto site_packages = sibling_venv / "lib" / "python3.14" / "site-packages";
#endif
        if (std::filesystem::exists(site_packages)) {
            // Prepend so venv packages take priority over bundled
            PyWideStringList_Insert(&config.module_search_paths, 0,
                                   site_packages.wstring().c_str());
            config.module_search_paths_set = 1;
        }
    }

    // under Windows, the search paths are correct; under Linux, they need manual insertion
#if __PLATFORM_SET_PYTHON_SEARCH_PATHS == 1
    if (!config.module_search_paths_set) {
        config.module_search_paths_set = 1;
    }

    // search paths for python libs/modules/scripts
    const wchar_t* str_arr[] = {
        L"/scripts",
        L"/lib/Python/lib.linux-x86_64-3.14",
        L"/lib/Python",
        L"/lib/Python/Lib"
        // Note: venv site-packages handled above via sibling_venv detection
    };


    for(auto s : str_arr) {
        status = PyWideStringList_Append(&config.module_search_paths, (executable_path() + s).c_str());
        if (PyStatus_Exception(status)) {
            continue;
        }
    }
#endif
#endif // __EMSCRIPTEN__

    status = Py_InitializeFromConfig(&config);

    PyConfig_Clear(&config);

    return status;
}

PyStatus McRFPy_API::init_python_with_config(const McRogueFaceConfig& config)
{
    // If Python is already initialized, just return success
    if (Py_IsInitialized()) {
        return PyStatus_Ok();
    }

    PyStatus status;
    PyConfig pyconfig;
    PyConfig_InitIsolatedConfig(&pyconfig);

    // Configure UTF-8 for stdio
    PyConfig_SetString(&pyconfig, &pyconfig.stdio_encoding, L"UTF-8");
    PyConfig_SetString(&pyconfig, &pyconfig.stdio_errors, L"surrogateescape");
    pyconfig.configure_c_stdio = 1;

    // Set sys.executable to the McRogueFace binary path
    auto exe_path = executable_filename();
    PyConfig_SetString(&pyconfig, &pyconfig.executable, exe_path.c_str());

    // Set interactive mode (replaces deprecated Py_InspectFlag)
    if (config.interactive_mode) {
        pyconfig.inspect = 1;
    }

    // Don't modify sys.path based on script location (replaces PySys_SetArgvEx updatepath=0)
    pyconfig.safe_path = 1;

    // Construct Python argv from config (replaces deprecated PySys_SetArgvEx)
    // Python convention:
    //   - Script mode: argv[0] = script_path, argv[1:] = script_args
    //   - -c mode: argv[0] = "-c"
    //   - -m mode: argv[0] = module_name, argv[1:] = script_args
    //   - Interactive only: argv[0] = ""
    std::vector<std::wstring> argv_storage;

    if (!config.script_path.empty()) {
        // Script execution: argv[0] = script path
        argv_storage.push_back(config.script_path.wstring());
        for (const auto& arg : config.script_args) {
            std::wstring warg(arg.begin(), arg.end());
            argv_storage.push_back(warg);
        }
    } else if (!config.python_command.empty()) {
        // -c command: argv[0] = "-c"
        argv_storage.push_back(L"-c");
    } else if (!config.python_module.empty()) {
        // -m module: argv[0] = module name
        std::wstring wmodule(config.python_module.begin(), config.python_module.end());
        argv_storage.push_back(wmodule);
        for (const auto& arg : config.script_args) {
            std::wstring warg(arg.begin(), arg.end());
            argv_storage.push_back(warg);
        }
    } else {
        // Interactive mode or no script: argv[0] = ""
        argv_storage.push_back(L"");
    }

    // Build wchar_t* array for PyConfig
    std::vector<wchar_t*> argv_ptrs;
    for (auto& ws : argv_storage) {
        argv_ptrs.push_back(const_cast<wchar_t*>(ws.c_str()));
    }

    status = PyConfig_SetWideStringList(&pyconfig, &pyconfig.argv,
                                         argv_ptrs.size(), argv_ptrs.data());
    if (PyStatus_Exception(status)) {
        return status;
    }

    // Set Python home to our bundled Python
#ifndef __EMSCRIPTEN__
    // Check if we're in a virtual environment (symlinked into a venv)
    // Skip for WASM builds - no filesystem access like this
    auto exe_wpath = executable_filename();
    auto exe_path_fs = std::filesystem::path(exe_wpath);
    auto exe_dir = exe_path_fs.parent_path();
    auto venv_root = exe_dir.parent_path();

    if (std::filesystem::exists(venv_root / "pyvenv.cfg")) {
        // We're running from within a venv!
        // Add venv's site-packages to module search paths
        auto site_packages = venv_root / "lib" / "python3.14" / "site-packages";
        PyWideStringList_Append(&pyconfig.module_search_paths,
                               site_packages.wstring().c_str());
        pyconfig.module_search_paths_set = 1;
    }

    // Check for sibling venv/ directory (self-contained deployment)
    auto sibling_venv = exe_dir / "venv";
    if (std::filesystem::exists(sibling_venv)) {
        // Platform-specific site-packages path
#ifdef _WIN32
        auto site_packages = sibling_venv / "Lib" / "site-packages";
#else
        auto site_packages = sibling_venv / "lib" / "python3.14" / "site-packages";
#endif
        if (std::filesystem::exists(site_packages)) {
            // Prepend so venv packages take priority over bundled
            PyWideStringList_Insert(&pyconfig.module_search_paths, 0,
                                   site_packages.wstring().c_str());
            pyconfig.module_search_paths_set = 1;
        }
    }
#endif // !__EMSCRIPTEN__
#ifdef __EMSCRIPTEN__
    // WASM: Use absolute paths in virtual filesystem
    PyConfig_SetString(&pyconfig, &pyconfig.home, L"/lib/python3.14");

    // Set up module search paths for WASM
    pyconfig.module_search_paths_set = 1;
    const wchar_t* wasm_paths[] = {
        L"/scripts",
        L"/lib/python3.14"
    };
    for (auto s : wasm_paths) {
        status = PyWideStringList_Append(&pyconfig.module_search_paths, s);
        if (PyStatus_Exception(status)) {
            continue;
        }
    }
#else
    auto python_home = executable_path() + L"/lib/Python";
    PyConfig_SetString(&pyconfig, &pyconfig.home, python_home.c_str());

    // Set up module search paths
#if __PLATFORM_SET_PYTHON_SEARCH_PATHS == 1
    if (!pyconfig.module_search_paths_set) {
        pyconfig.module_search_paths_set = 1;
    }

    // search paths for python libs/modules/scripts
    const wchar_t* str_arr[] = {
        L"/scripts",
        L"/lib/Python/lib.linux-x86_64-3.14",
        L"/lib/Python",
        L"/lib/Python/Lib"
        // Note: venv site-packages handled above via sibling_venv detection
    };

    for(auto s : str_arr) {
        status = PyWideStringList_Append(&pyconfig.module_search_paths, (executable_path() + s).c_str());
        if (PyStatus_Exception(status)) {
            continue;
        }
    }
#endif
#endif // __EMSCRIPTEN__

    // Register mcrfpy module before initialization
    PyImport_AppendInittab("mcrfpy", &PyInit_mcrfpy);

    status = Py_InitializeFromConfig(&pyconfig);
    PyConfig_Clear(&pyconfig);

    return status;
}

/*
void McRFPy_API::setSpriteTexture(int ti)
{
    int tx = ti % texture_width, ty = ti / texture_width;
    sprite.setTextureRect(sf::IntRect(
                tx * texture_size,
                ty * texture_size,
                texture_size, texture_size));
}
*/

// functionality
//void McRFPy_API::

void McRFPy_API::api_init() {

    // build API exposure before python initialization
    if (!Py_IsInitialized()) {
        PyImport_AppendInittab("mcrfpy", &PyInit_mcrfpy);
        // use full path version of argv[0] from OS to init python
        init_python(narrow_string(executable_filename()).c_str());
    }

    //texture.loadFromFile("./assets/kenney_tinydungeon.png");
    //texture_size = 16, texture_width = 12, texture_height= 11;
    //texture_sprite_count = texture_width * texture_height;
    //texture.setSmooth(false);

    // Add default_font and default_texture to module
    McRFPy_API::mcrf_module = PyImport_ImportModule("mcrfpy");
    std::cout << PyUnicode_AsUTF8(PyObject_Repr(McRFPy_API::mcrf_module)) << std::endl;

    //PyModule_AddObject(McRFPy_API::mcrf_module, "default_font", McRFPy_API::default_font->pyObject());
    PyObject_SetAttrString(McRFPy_API::mcrf_module, "default_font", McRFPy_API::default_font->pyObject());
    //PyModule_AddObject(McRFPy_API::mcrf_module, "default_texture", McRFPy_API::default_texture->pyObject());
    PyObject_SetAttrString(McRFPy_API::mcrf_module, "default_texture", McRFPy_API::default_texture->pyObject());

    //sprite.setTexture(texture);
    //sprite.setScale(sf::Vector2f(4.0f, 4.0f));
    //setSpriteTexture(0);
}

void McRFPy_API::api_init(const McRogueFaceConfig& config) {
    // Initialize Python with proper argv constructed from config
    PyStatus status = init_python_with_config(config);
    if (PyStatus_Exception(status)) {
        Py_ExitStatusException(status);
    }
    
    McRFPy_API::mcrf_module = PyImport_ImportModule("mcrfpy");
    
    // For -m module execution, let Python handle it
    if (!config.python_module.empty() && config.python_module != "venv") {
        // Py_RunMain() will handle -m execution
        return;
    }
    
    // Execute based on mode - this is handled in main.cpp now
    // The actual execution logic is in run_python_interpreter()
    
    // Set up default resources only if in game mode
    if (!config.python_mode) {
        //PyModule_AddObject(McRFPy_API::mcrf_module, "default_font", McRFPy_API::default_font->pyObject());
        PyObject_SetAttrString(McRFPy_API::mcrf_module, "default_font", McRFPy_API::default_font->pyObject());
        //PyModule_AddObject(McRFPy_API::mcrf_module, "default_texture", McRFPy_API::default_texture->pyObject());
        PyObject_SetAttrString(McRFPy_API::mcrf_module, "default_texture", McRFPy_API::default_texture->pyObject());
    }
}

void McRFPy_API::executeScript(std::string filename)
{
    std::string script_path_str;

#ifdef __EMSCRIPTEN__
    // WASM: Scripts are at /scripts/ in virtual filesystem
    if (filename.find('/') == std::string::npos) {
        // Simple filename - look in /scripts/
        script_path_str = "/scripts/" + filename;
    } else {
        script_path_str = filename;
    }
#else
    std::filesystem::path script_path(filename);

    // If the path is relative and the file doesn't exist, try resolving it relative to the executable
    if (script_path.is_relative() && !std::filesystem::exists(script_path)) {
        // Get the directory where the executable is located using platform-specific function
        std::wstring exe_dir_w = executable_path();
        std::filesystem::path exe_dir(exe_dir_w);

        // Try the script path relative to the executable directory
        std::filesystem::path resolved_path = exe_dir / script_path;
        if (std::filesystem::exists(resolved_path)) {
            script_path = resolved_path;
        }
    }
    script_path_str = script_path.string();
#endif

    // Use std::ifstream + PyRun_SimpleString instead of PyRun_SimpleFile
    // PyRun_SimpleFile has compatibility issues with MinGW-compiled code
    std::ifstream file(script_path_str);
    if (!file.is_open()) {
        std::cout << "Failed to open script: " << script_path_str << std::endl;
        return;
    }

    std::string script_content((std::istreambuf_iterator<char>(file)),
                                std::istreambuf_iterator<char>());
    file.close();

    // Set __file__ before execution
    PyObject* main_module = PyImport_AddModule("__main__");
    PyObject* main_dict = PyModule_GetDict(main_module);
    PyObject* py_filename = PyUnicode_FromString(script_path_str.c_str());
    PyDict_SetItemString(main_dict, "__file__", py_filename);
    Py_DECREF(py_filename);

    PyRun_SimpleString(script_content.c_str());
}

void McRFPy_API::api_shutdown()
{
    // Audio cleanup now handled by Python garbage collection (Sound/Music classes)
    Py_Finalize();
}

void McRFPy_API::executePyString(std::string pycode)
{
    PyRun_SimpleString(pycode.c_str());
}

void McRFPy_API::REPL()
{
    PyRun_InteractiveLoop(stdin, "<stdin>");
}

void McRFPy_API::REPL_device(FILE * fp, const char *filename)
{
    PyRun_InteractiveLoop(fp, filename);
}

// python connection


/*
PyObject* McRFPy_API::_refreshFov(PyObject* self, PyObject* args) {
	for (auto e : McRFPy_API::entities.getEntities("player")) {
		e->cGrid->grid->refreshTCODsight(e->cGrid->x, e->cGrid->y);
	}
	Py_INCREF(Py_None);
    return Py_None;
}
*/

// Removed deprecated audio functions - use mcrfpy.Sound and mcrfpy.Music classes instead (#66)
// Removed deprecated player_input, computerTurn, playerTurn functions
// These were part of the old turn-based system that is no longer used

/*
PyObject* McRFPy_API::_camFollow(PyObject* self, PyObject* args) {
	PyObject* set_camfollow = NULL;
	//std::cout << "camFollow Parse Args" << std::endl;
	if (!PyArg_ParseTuple(args, "|O", &set_camfollow)) return NULL;
	//std::cout << "Parsed" << std::endl;
	if (set_camfollow == NULL) {
		// return value
		//std::cout << "null; Returning value " << McRFPy_API::do_camfollow << std::endl;
		Py_INCREF(McRFPy_API::do_camfollow ? Py_True : Py_False);
		return McRFPy_API::do_camfollow ? Py_True : Py_False;
	}
	//std::cout << "non-null; setting value" << std::endl;
	
	McRFPy_API::do_camfollow = PyObject_IsTrue(set_camfollow);
	Py_INCREF(Py_None);
    return Py_None;
}
*/

// Internal use - called by PySceneClass_get_children()
PyObject* McRFPy_API::_sceneUI(PyObject* self, PyObject* args) {
    using namespace mcrfpydef;
	const char *scene_cstr;
	if (!PyArg_ParseTuple(args, "s", &scene_cstr)) return NULL;

    auto ui = Resources::game->scene_ui(scene_cstr);
    if(!ui) 
    {
        PyErr_SetString(PyExc_RuntimeError, "No scene found by that name");
        return NULL;
    }
    //std::cout << "vector returned has size=" << ui->size() << std::endl;
    //Py_INCREF(Py_None);
    //return Py_None;
    PyUICollectionObject* o = (PyUICollectionObject*)PyUICollectionType.tp_alloc(&PyUICollectionType, 0);
    if (o) {
        o->data = ui;
        o->scene_name = scene_cstr;  // #183: Track scene ownership
    }
    return (PyObject*)o;
}

// Internal use - called by PySceneObject::activate()
PyObject* McRFPy_API::_setScene(PyObject* self, PyObject* args) {
	const char* newscene;
	const char* transition_str = nullptr;
	float duration = 0.0f;
	
	// Parse arguments: scene name, optional transition type, optional duration
	if (!PyArg_ParseTuple(args, "s|sf", &newscene, &transition_str, &duration)) return NULL;
	
	// Map transition string to enum
	TransitionType transition_type = TransitionType::None;
	if (transition_str) {
		std::string trans(transition_str);
		if (trans == "fade") transition_type = TransitionType::Fade;
		else if (trans == "slide_left") transition_type = TransitionType::SlideLeft;
		else if (trans == "slide_right") transition_type = TransitionType::SlideRight;
		else if (trans == "slide_up") transition_type = TransitionType::SlideUp;
		else if (trans == "slide_down") transition_type = TransitionType::SlideDown;
	}
	
	game->changeScene(newscene, transition_type, duration);
    Py_INCREF(Py_None);
    return Py_None;		
}

// #180: Create a Python wrapper for an existing C++ Timer (for orphaned timers)
static PyObject* createTimerWrapper(std::shared_ptr<Timer> timer)
{
    // Allocate new PyTimerObject
    PyTypeObject* type = &mcrfpydef::PyTimerType;
    PyTimerObject* obj = (PyTimerObject*)type->tp_alloc(type, 0);
    if (!obj) return nullptr;

    // Initialize - use placement new for std::string
    new(&obj->name) std::string(timer->name);
    obj->data = timer;  // Share the existing C++ Timer
    obj->weakreflist = nullptr;

    // Register in cache for future lookups
    if (timer->serial_number == 0) {
        timer->serial_number = PythonObjectCache::getInstance().assignSerial();
    }
    PyObject* weakref = PyWeakref_NewRef((PyObject*)obj, NULL);
    if (weakref) {
        PythonObjectCache::getInstance().registerObject(timer->serial_number, weakref);
        Py_DECREF(weakref);
    }

    return (PyObject*)obj;
}

// #173: Get all timers as a tuple of Python Timer objects
PyObject* McRFPy_API::api_get_timers()
{
    if (!game) {
        return PyTuple_New(0);
    }

    std::vector<PyObject*> timer_objs;
    for (auto& pair : game->timers) {
        auto& timer = pair.second;
        if (!timer) continue;

        PyObject* timer_obj = nullptr;

        // Try to find existing Python wrapper
        if (timer->serial_number != 0) {
            timer_obj = PythonObjectCache::getInstance().lookup(timer->serial_number);
        }

        // #180: If no wrapper exists (orphaned timer), create a new one
        if (!timer_obj || timer_obj == Py_None) {
            timer_obj = createTimerWrapper(timer);
        }

        if (timer_obj && timer_obj != Py_None) {
            timer_objs.push_back(timer_obj);
        }
    }

    PyObject* tuple = PyTuple_New(timer_objs.size());
    if (!tuple) return NULL;

    for (Py_ssize_t i = 0; i < static_cast<Py_ssize_t>(timer_objs.size()); i++) {
        // timer_objs already has a reference from lookup() or createTimerWrapper()
        // PyTuple_SET_ITEM steals that reference, so no additional INCREF needed
        PyTuple_SET_ITEM(tuple, i, timer_objs[i]);
    }

    return tuple;
}

// Module-level animation collection accessor
PyObject* McRFPy_API::api_get_animations()
{
    auto& manager = AnimationManager::getInstance();
    const auto& animations = manager.getActiveAnimations();

    PyObject* tuple = PyTuple_New(animations.size());
    if (!tuple) return NULL;

    Py_ssize_t i = 0;
    for (const auto& anim : animations) {
        // Create a PyAnimation wrapper for each animation
        PyAnimationObject* pyAnim = (PyAnimationObject*)mcrfpydef::PyAnimationType.tp_alloc(&mcrfpydef::PyAnimationType, 0);
        if (pyAnim) {
            pyAnim->data = anim;
            PyTuple_SET_ITEM(tuple, i, (PyObject*)pyAnim);
        } else {
            // Failed to allocate - fill with None
            Py_INCREF(Py_None);
            PyTuple_SET_ITEM(tuple, i, Py_None);
        }
        i++;
    }

    return tuple;
}

// #153 - Headless simulation control
PyObject* McRFPy_API::_step(PyObject* self, PyObject* args) {
    PyObject* dt_obj = Py_None;
    if (!PyArg_ParseTuple(args, "|O", &dt_obj)) return NULL;

    float dt;
    if (dt_obj == Py_None) {
        // None means "advance to next event"
        dt = -1.0f;
    } else if (PyFloat_Check(dt_obj)) {
        dt = static_cast<float>(PyFloat_AsDouble(dt_obj));
    } else if (PyLong_Check(dt_obj)) {
        dt = static_cast<float>(PyLong_AsLong(dt_obj));
    } else {
        PyErr_SetString(PyExc_TypeError, "step() argument must be a float, int, or None");
        return NULL;
    }

    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "Game engine not initialized");
        return NULL;
    }

    float actual_dt = game->step(dt);
    return PyFloat_FromDouble(actual_dt);
}

PyObject* McRFPy_API::_exit(PyObject* self, PyObject* args) {
    game->quit();
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* McRFPy_API::_setScale(PyObject* self, PyObject* args) {
	float multiplier;
	if (!PyArg_ParseTuple(args, "f", &multiplier)) return NULL;
    if (multiplier < 0.2 || multiplier > 4)
    {
        PyErr_SetString(PyExc_ValueError, "Window scale must be between 0.2 and 4");
        return NULL;
    }
    game->setWindowScale(multiplier);
    Py_INCREF(Py_None);
    return Py_None;
}

void McRFPy_API::markSceneNeedsSort() {
    // Mark the current scene as needing a z_index sort
    auto scene = game->currentScene();
    if (scene && scene->ui_elements) {
        // Cast to PyScene to access ui_elements_need_sort
        PyScene* pyscene = dynamic_cast<PyScene*>(scene);
        if (pyscene) {
            pyscene->ui_elements_need_sort = true;
        }
    }
}

// Helper function to check if a name matches a pattern with wildcards
static bool name_matches_pattern(const std::string& name, const std::string& pattern) {
    if (pattern.find('*') == std::string::npos) {
        // No wildcards, exact match
        return name == pattern;
    }
    
    // Simple wildcard matching - * matches any sequence
    size_t name_pos = 0;
    size_t pattern_pos = 0;
    
    while (pattern_pos < pattern.length() && name_pos < name.length()) {
        if (pattern[pattern_pos] == '*') {
            // Skip consecutive stars
            while (pattern_pos < pattern.length() && pattern[pattern_pos] == '*') {
                pattern_pos++;
            }
            if (pattern_pos == pattern.length()) {
                // Pattern ends with *, matches rest of name
                return true;
            }
            
            // Find next non-star character in pattern
            char next_char = pattern[pattern_pos];
            while (name_pos < name.length() && name[name_pos] != next_char) {
                name_pos++;
            }
        } else if (pattern[pattern_pos] == name[name_pos]) {
            pattern_pos++;
            name_pos++;
        } else {
            return false;
        }
    }
    
    // Skip trailing stars in pattern
    while (pattern_pos < pattern.length() && pattern[pattern_pos] == '*') {
        pattern_pos++;
    }
    
    return pattern_pos == pattern.length() && name_pos == name.length();
}

// Helper to recursively search a collection for named elements
static void find_in_collection(std::vector<std::shared_ptr<UIDrawable>>* collection, const std::string& pattern, 
                             bool find_all, PyObject* results) {
    if (!collection) return;
    
    for (auto& drawable : *collection) {
        if (!drawable) continue;
        
        // Check this element's name
        if (name_matches_pattern(drawable->name, pattern)) {
            // Convert to Python object using RET_PY_INSTANCE logic
            PyObject* py_obj = nullptr;
            
            switch (drawable->derived_type()) {
                case PyObjectsEnum::UIFRAME: {
                    auto frame = std::static_pointer_cast<UIFrame>(drawable);
                    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Frame");
                    auto o = (PyUIFrameObject*)type->tp_alloc(type, 0);
                    if (o) {
                        o->data = frame;
                        py_obj = (PyObject*)o;
                    }
                    break;
                }
                case PyObjectsEnum::UICAPTION: {
                    auto caption = std::static_pointer_cast<UICaption>(drawable);
                    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Caption");
                    auto o = (PyUICaptionObject*)type->tp_alloc(type, 0);
                    if (o) {
                        o->data = caption;
                        py_obj = (PyObject*)o;
                    }
                    break;
                }
                case PyObjectsEnum::UISPRITE: {
                    auto sprite = std::static_pointer_cast<UISprite>(drawable);
                    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Sprite");
                    auto o = (PyUISpriteObject*)type->tp_alloc(type, 0);
                    if (o) {
                        o->data = sprite;
                        py_obj = (PyObject*)o;
                    }
                    break;
                }
                case PyObjectsEnum::UIGRID: {
                    auto grid = std::static_pointer_cast<UIGrid>(drawable);
                    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Grid");
                    auto o = (PyUIGridObject*)type->tp_alloc(type, 0);
                    if (o) {
                        o->data = grid;
                        py_obj = (PyObject*)o;
                    }
                    break;
                }
                default:
                    break;
            }
            
            if (py_obj) {
                if (find_all) {
                    PyList_Append(results, py_obj);
                    Py_DECREF(py_obj);
                } else {
                    // For find (not findAll), we store in results and return early
                    PyList_Append(results, py_obj);
                    Py_DECREF(py_obj);
                    return;
                }
            }
        }
        
        // Recursively search in Frame children
        if (drawable->derived_type() == PyObjectsEnum::UIFRAME) {
            auto frame = std::static_pointer_cast<UIFrame>(drawable);
            find_in_collection(frame->children.get(), pattern, find_all, results);
            if (!find_all && PyList_Size(results) > 0) {
                return;  // Found one, stop searching
            }
        }
    }
}

// Also search Grid entities
static void find_in_grid_entities(UIGrid* grid, const std::string& pattern, 
                                bool find_all, PyObject* results) {
    if (!grid || !grid->entities) return;
    
    for (auto& entity : *grid->entities) {
        if (!entity) continue;
        
        // Entities delegate name to their sprite
        if (name_matches_pattern(entity->sprite.name, pattern)) {
            auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity");
            auto o = (PyUIEntityObject*)type->tp_alloc(type, 0);
            if (o) {
                o->data = entity;
                PyObject* py_obj = (PyObject*)o;
                
                if (find_all) {
                    PyList_Append(results, py_obj);
                    Py_DECREF(py_obj);
                } else {
                    PyList_Append(results, py_obj);
                    Py_DECREF(py_obj);
                    return;
                }
            }
        }
    }
}

PyObject* McRFPy_API::_find(PyObject* self, PyObject* args) {
    const char* name;
    const char* scene_name = nullptr;
    
    if (!PyArg_ParseTuple(args, "s|s", &name, &scene_name)) {
        return NULL;
    }
    
    PyObject* results = PyList_New(0);
    
    // Get the UI elements to search
    std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>> ui_elements;
    if (scene_name) {
        // Search specific scene
        ui_elements = game->scene_ui(scene_name);
        if (!ui_elements) {
            PyErr_Format(PyExc_ValueError, "Scene '%s' not found", scene_name);
            Py_DECREF(results);
            return NULL;
        }
    } else {
        // Search current scene
        Scene* current = game->currentScene();
        if (!current) {
            PyErr_SetString(PyExc_RuntimeError, "No current scene");
            Py_DECREF(results);
            return NULL;
        }
        ui_elements = current->ui_elements;
    }
    
    // Search the scene's UI elements
    find_in_collection(ui_elements.get(), name, false, results);
    
    // Also search all grids in the scene for entities
    if (PyList_Size(results) == 0 && ui_elements) {
        for (auto& drawable : *ui_elements) {
            if (drawable && drawable->derived_type() == PyObjectsEnum::UIGRID) {
                auto grid = std::static_pointer_cast<UIGrid>(drawable);
                find_in_grid_entities(grid.get(), name, false, results);
                if (PyList_Size(results) > 0) break;
            }
        }
    }
    
    // Return the first result or None
    if (PyList_Size(results) > 0) {
        PyObject* result = PyList_GetItem(results, 0);
        Py_INCREF(result);
        Py_DECREF(results);
        return result;
    }
    
    Py_DECREF(results);
    Py_RETURN_NONE;
}

PyObject* McRFPy_API::_findAll(PyObject* self, PyObject* args) {
    const char* pattern;
    const char* scene_name = nullptr;
    
    if (!PyArg_ParseTuple(args, "s|s", &pattern, &scene_name)) {
        return NULL;
    }
    
    PyObject* results = PyList_New(0);
    
    // Get the UI elements to search
    std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>> ui_elements;
    if (scene_name) {
        // Search specific scene
        ui_elements = game->scene_ui(scene_name);
        if (!ui_elements) {
            PyErr_Format(PyExc_ValueError, "Scene '%s' not found", scene_name);
            Py_DECREF(results);
            return NULL;
        }
    } else {
        // Search current scene
        Scene* current = game->currentScene();
        if (!current) {
            PyErr_SetString(PyExc_RuntimeError, "No current scene");
            Py_DECREF(results);
            return NULL;
        }
        ui_elements = current->ui_elements;
    }
    
    // Search the scene's UI elements
    find_in_collection(ui_elements.get(), pattern, true, results);
    
    // Also search all grids in the scene for entities
    if (ui_elements) {
        for (auto& drawable : *ui_elements) {
            if (drawable && drawable->derived_type() == PyObjectsEnum::UIGRID) {
                auto grid = std::static_pointer_cast<UIGrid>(drawable);
                find_in_grid_entities(grid.get(), pattern, true, results);
            }
        }
    }
    
    return results;
}

PyObject* McRFPy_API::_getMetrics(PyObject* self, PyObject* args) {
    // Create a dictionary with metrics
    PyObject* dict = PyDict_New();
    if (!dict) return NULL;

    // Add frame time metrics
    PyDict_SetItemString(dict, "frame_time", PyFloat_FromDouble(game->metrics.frameTime));
    PyDict_SetItemString(dict, "avg_frame_time", PyFloat_FromDouble(game->metrics.avgFrameTime));
    PyDict_SetItemString(dict, "fps", PyLong_FromLong(game->metrics.fps));

    // Add draw call metrics
    PyDict_SetItemString(dict, "draw_calls", PyLong_FromLong(game->metrics.drawCalls));
    PyDict_SetItemString(dict, "ui_elements", PyLong_FromLong(game->metrics.uiElements));
    PyDict_SetItemString(dict, "visible_elements", PyLong_FromLong(game->metrics.visibleElements));

    // #144 - Add detailed timing breakdown (in milliseconds)
    PyDict_SetItemString(dict, "grid_render_time", PyFloat_FromDouble(game->metrics.gridRenderTime));
    PyDict_SetItemString(dict, "entity_render_time", PyFloat_FromDouble(game->metrics.entityRenderTime));
    PyDict_SetItemString(dict, "fov_overlay_time", PyFloat_FromDouble(game->metrics.fovOverlayTime));
    PyDict_SetItemString(dict, "python_time", PyFloat_FromDouble(game->metrics.pythonScriptTime));
    PyDict_SetItemString(dict, "animation_time", PyFloat_FromDouble(game->metrics.animationTime));

    // #144 - Add grid-specific metrics
    PyDict_SetItemString(dict, "grid_cells_rendered", PyLong_FromLong(game->metrics.gridCellsRendered));
    PyDict_SetItemString(dict, "entities_rendered", PyLong_FromLong(game->metrics.entitiesRendered));
    PyDict_SetItemString(dict, "total_entities", PyLong_FromLong(game->metrics.totalEntities));

    // Add general metrics
    PyDict_SetItemString(dict, "current_frame", PyLong_FromLong(game->getFrame()));
    PyDict_SetItemString(dict, "runtime", PyFloat_FromDouble(game->runtime.getElapsedTime().asSeconds()));

    return dict;
}

PyObject* McRFPy_API::_setDevConsole(PyObject* self, PyObject* args) {
    int enabled;
    if (!PyArg_ParseTuple(args, "p", &enabled)) {  // "p" for boolean predicate
        return NULL;
    }

#if !defined(MCRF_HEADLESS) && !defined(MCRF_SDL2)
    ImGuiConsole::setEnabled(enabled);
#endif
    Py_RETURN_NONE;
}

// #215: Bresenham line algorithm implementation
// Helper to extract (x, y) from tuple, list, or Vector
static bool extract_point(PyObject* obj, int* x, int* y, const char* arg_name) {
    // Try tuple/list first
    if (PySequence_Check(obj) && PySequence_Size(obj) == 2) {
        PyObject* x_obj = PySequence_GetItem(obj, 0);
        PyObject* y_obj = PySequence_GetItem(obj, 1);

        bool ok = false;
        if (x_obj && y_obj && PyNumber_Check(x_obj) && PyNumber_Check(y_obj)) {
            PyObject* x_long = PyNumber_Long(x_obj);
            PyObject* y_long = PyNumber_Long(y_obj);
            if (x_long && y_long) {
                *x = PyLong_AsLong(x_long);
                *y = PyLong_AsLong(y_long);
                ok = !PyErr_Occurred();
            }
            Py_XDECREF(x_long);
            Py_XDECREF(y_long);
        }

        Py_XDECREF(x_obj);
        Py_XDECREF(y_obj);

        if (ok) return true;
    }

    // Try Vector type
    PyObject* vector_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    if (vector_type && PyObject_IsInstance(obj, vector_type)) {
        Py_DECREF(vector_type);
        PyVectorObject* vec = (PyVectorObject*)obj;
        *x = static_cast<int>(vec->data.x);
        *y = static_cast<int>(vec->data.y);
        return true;
    }
    Py_XDECREF(vector_type);

    PyErr_Format(PyExc_TypeError,
        "%s: expected (x, y) tuple or Vector, got %s",
        arg_name, Py_TYPE(obj)->tp_name);
    return false;
}

PyObject* McRFPy_API::_bresenham(PyObject* self, PyObject* args, PyObject* kwargs) {
    static const char* kwlist[] = {"start", "end", "include_start", "include_end", NULL};
    PyObject* start_obj = NULL;
    PyObject* end_obj = NULL;
    int include_start = 1;  // Default: True
    int include_end = 1;    // Default: True

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "OO|pp",
                                     const_cast<char**>(kwlist),
                                     &start_obj, &end_obj,
                                     &include_start, &include_end)) {
        return NULL;
    }

    int x1, y1, x2, y2;
    if (!extract_point(start_obj, &x1, &y1, "start")) return NULL;
    if (!extract_point(end_obj, &x2, &y2, "end")) return NULL;

    // Build result list using TCOD's Bresenham implementation
    PyObject* result = PyList_New(0);
    if (!result) return NULL;

    // Add start point if requested
    if (include_start) {
        PyObject* pos = Py_BuildValue("(ii)", x1, y1);
        if (!pos) { Py_DECREF(result); return NULL; }
        PyList_Append(result, pos);
        Py_DECREF(pos);
    }

    // Use TCOD's line algorithm for intermediate points
    TCODLine::init(x1, y1, x2, y2);
    int x, y;

    // Step through the line - TCODLine::step returns false until reaching endpoint
    while (!TCODLine::step(&x, &y)) {
        // Skip start point (already handled above if include_start)
        if (x == x1 && y == y1) continue;
        // Skip end point (handle below based on include_end)
        if (x == x2 && y == y2) continue;

        PyObject* pos = Py_BuildValue("(ii)", x, y);
        if (!pos) { Py_DECREF(result); return NULL; }
        PyList_Append(result, pos);
        Py_DECREF(pos);
    }

    // Add end point if requested (and it's different from start)
    if (include_end && (x1 != x2 || y1 != y2)) {
        PyObject* pos = Py_BuildValue("(ii)", x2, y2);
        if (!pos) { Py_DECREF(result); return NULL; }
        PyList_Append(result, pos);
        Py_DECREF(pos);
    }

    return result;
}

// Benchmark logging implementation (#104)
PyObject* McRFPy_API::_startBenchmark(PyObject* self, PyObject* args) {
    try {
        // Warn if in headless mode - benchmark frames are only recorded by the game loop
        if (game && game->isHeadless()) {
            PyErr_WarnEx(PyExc_UserWarning,
                "Benchmark started in headless mode. Note: step() and screenshot() do not "
                "record benchmark frames. The benchmark API captures per-frame data from the "
                "game loop, which is bypassed when using step()-based simulation control. "
                "For headless performance measurement, use Python's time module instead.", 1);
        }
        g_benchmarkLogger.start();
        Py_RETURN_NONE;
    } catch (const std::runtime_error& e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return NULL;
    }
}

PyObject* McRFPy_API::_endBenchmark(PyObject* self, PyObject* args) {
    try {
        std::string filename = g_benchmarkLogger.end();
        return PyUnicode_FromString(filename.c_str());
    } catch (const std::runtime_error& e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return NULL;
    }
}

PyObject* McRFPy_API::_logBenchmark(PyObject* self, PyObject* args) {
    const char* message;
    if (!PyArg_ParseTuple(args, "s", &message)) {
        return NULL;
    }

    try {
        g_benchmarkLogger.log(message);
        Py_RETURN_NONE;
    } catch (const std::runtime_error& e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return NULL;
    }
}

// Exception handling implementation
void McRFPy_API::signalPythonException() {
    // Check if we should exit on exception (consult config via game)
    if (game && !game->isHeadless()) {
        // In windowed mode, respect the config setting
        // Access config through game engine - but we need to check the config
    }

    // For now, always signal - the game loop will check the config
    exception_occurred.store(true);
    exit_code.store(1);
}

bool McRFPy_API::shouldExit() {
    return exception_occurred.load();
}
