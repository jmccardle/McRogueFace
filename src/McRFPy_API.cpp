#include "Display.h"
#include "McRFPy_API.h"
#include "PyWrap.h"
#include "EngineRandom.h"
#include <climits>
#include <cmath>

// Embedded-interpreter version strings, derived from the CPython headers we
// compile against (patchlevel.h) so bumping the interpreter needs no edits here.
#define MCRF_STR2(x) #x
#define MCRF_STR(x) MCRF_STR2(x)
#define MCRF_WSTR2(x) L ## #x
#define MCRF_WSTR(x) MCRF_WSTR2(x)
#define MCRF_PY_VER MCRF_STR(PY_MAJOR_VERSION) "." MCRF_STR(PY_MINOR_VERSION)
#define MCRF_PY_VER_W MCRF_WSTR(PY_MAJOR_VERSION) L"." MCRF_WSTR(PY_MINOR_VERSION)
#define MCRF_PY_HOME_W L"/lib/python" MCRF_PY_VER_W
#ifdef Py_GIL_DISABLED
#define MCRF_PY_STDLIB_DIRNAME "python" MCRF_PY_VER "t"   // venv layout: lib/python3.Xt/
#else
#define MCRF_PY_STDLIB_DIRNAME "python" MCRF_PY_VER
#endif
// Extension modules (relative to the exe): CPython's own layout per platform.
// Windows .pyd files come from python.org's embeddable package (__lib_windows).
#ifdef _WIN32
#define MCRF_PY_EXT_DIR_W L"/lib/Python/DLLs"
#else
#define MCRF_PY_EXT_DIR_W L"/lib/Python/lib.linux-x86_64-" MCRF_PY_VER_W
#endif

#include "UIDrawable.h"
#include "McRFPy_Automation.h"
// Note: McRFPy_Libtcod.h removed in #215 - functionality moved to mcrfpy.bresenham()
#include "McRFPy_Doc.h"
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
#include "PyPerspective.h"
#include "PyHeuristic.h"
#include "PyBehavior.h"
#include "PyTrigger.h"
#include "UIGridView.h"
#include "PySound.h"
#include "PySoundBuffer.h"
#include "PyMusic.h"
#include "Audio.h"
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
#include "3d/Viewport3D.h"  // 3D rendering viewport
#include "3d/Entity3D.h"    // 3D game entities
#include "3d/EntityCollection3D.h"  // Entity3D collection
#include "3d/Model3D.h"     // 3D model resource
#include "3d/Billboard.h"   // Billboard sprites
#include "3d/PyVoxelGrid.h" // Voxel grid for 3D structures (Milestone 9)
#include "tiled/PyTileSetFile.h"  // Tiled tileset loading
#include "tiled/PyTileMapFile.h"  // Tiled tilemap loading
#include "tiled/PyWangSet.h"      // Wang auto-tile sets
#include "ldtk/PyLdtkProject.h"   // LDtk project loading
#include "ldtk/PyAutoRuleSet.h"   // LDtk auto-rule sets
#include "PyVisibilityMask.h"     // GridData.observe() result mask (fog-of-war/AI perception)
#include "McRogueFaceVersion.h"
#include "GameEngine.h"
#ifdef __EMSCRIPTEN__
#include <emscripten.h>
#endif
#include <sys/stat.h>  // mkdir
#include <unordered_set>  // #359 - dedupe shared GridData during find/findAll walk
// ImGui is only available for SFML builds
#if !defined(MCRF_HEADLESS) && !defined(MCRF_SDL2)
#include "ImGuiConsole.h"
#endif
#include "BenchmarkLogger.h"
#include "UI.h"
#include "UICollection.h"  // #430: UICollection::pyobject_for (Scene.children)
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

#ifdef __EMSCRIPTEN__
extern "C" void sync_storage();
#endif

// Flush persistent storage (IDBFS on WASM, no-op on desktop)
static PyObject* mcrfpy_sync_storage(PyObject* self, PyObject* args)
{
#ifdef __EMSCRIPTEN__
    sync_storage();
#endif
    // On desktop, writes go directly to disk -- nothing to sync
    Py_RETURN_NONE;
}

// #151/#356: the module's dynamic attributes, as real descriptors on the module type.
//
// These were originally a PEP-562 `__getattr__` plus a string-matching `tp_setattro`.
// That worked for getattr/setattr but left them invisible to `dir(mcrfpy)`, and every
// doc/stub/manifest generator discovers module symbols via dir() -- so the single most
// common idiom in the engine (`mcrfpy.current_scene = ...`) appeared in no generated
// documentation at all. Descriptors are introspectable and carry their own docstrings.

static PyObject* mcrfpy_get_current_scene(PyObject* self, void* closure)
{
    return McRFPy_API::api_get_current_scene();
}

static int mcrfpy_set_current_scene(PyObject* self, PyObject* value, void* closure)
{
    if (!value) {
        PyErr_SetString(PyExc_AttributeError, "cannot delete 'current_scene'");
        return -1;
    }
    return McRFPy_API::api_set_current_scene(value);
}

static PyObject* mcrfpy_get_scenes(PyObject* self, void* closure)
{
    return McRFPy_API::api_get_scenes();
}

static PyObject* mcrfpy_get_timers(PyObject* self, void* closure)
{
    return McRFPy_API::api_get_timers();
}

static PyObject* mcrfpy_get_animations(PyObject* self, void* closure)
{
    return McRFPy_API::api_get_animations();
}

static PyObject* mcrfpy_get_default_transition(PyObject* self, void* closure)
{
    return PyTransition::to_python(PyTransition::default_transition);
}

static int mcrfpy_set_default_transition(PyObject* self, PyObject* value, void* closure)
{
    if (!value) {
        PyErr_SetString(PyExc_AttributeError, "cannot delete 'default_transition'");
        return -1;
    }
    TransitionType trans;
    if (!PyTransition::from_arg(value, &trans, nullptr)) {
        return -1;
    }
    PyTransition::default_transition = trans;
    return 0;
}

static PyObject* mcrfpy_get_default_transition_duration(PyObject* self, void* closure)
{
    return PyFloat_FromDouble(PyTransition::default_duration);
}

static int mcrfpy_set_default_transition_duration(PyObject* self, PyObject* value, void* closure)
{
    if (!value) {
        PyErr_SetString(PyExc_AttributeError, "cannot delete 'default_transition_duration'");
        return -1;
    }
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

static PyObject* mcrfpy_get_save_dir(PyObject* self, void* closure)
{
#ifdef __EMSCRIPTEN__
    return PyUnicode_FromString("/save");
#else
    return PyUnicode_FromString("save");
#endif
}

// #451: the default texture is a GL resource, so it is created by its first use, not at
// import: a process that never draws a sprite never needs a display for it.
static PyObject* mcrfpy_get_default_texture(PyObject* self, void* closure)
{
    auto texture = McRFPy_API::defaultTexture();
    if (!texture) return NULL;
    return texture->pyObject();
}

static int mcrfpy_set_default_texture(PyObject* self, PyObject* value, void* closure)
{
    if (!value || !PyObject_TypeCheck(value, &mcrfpydef::PyTextureType)) {
        PyErr_SetString(PyExc_TypeError, "default_texture must be a Texture");
        return -1;
    }
    McRFPy_API::default_texture = ((PyTextureObject*)value)->data;
    return 0;
}

static PyGetSetDef mcrfpy_module_getset[] = {
    {"current_scene", mcrfpy_get_current_scene, mcrfpy_set_current_scene,
     MCRF_PROPERTY(current_scene,
         "The active scene (Scene). Assign a Scene object, or a scene name as a string, "
         "to switch scenes."
     ), NULL},
    {"scenes", mcrfpy_get_scenes, NULL,
     MCRF_PROPERTY(scenes,
         "Tuple of all registered Scene objects (tuple, read-only)."
     ), NULL},
    {"timers", mcrfpy_get_timers, NULL,
     MCRF_PROPERTY(timers,
         "Tuple of all active Timer objects (tuple, read-only)."
     ), NULL},
    {"animations", mcrfpy_get_animations, NULL,
     MCRF_PROPERTY(animations,
         "Tuple of all currently running Animation objects (tuple, read-only)."
     ), NULL},
    {"default_transition", mcrfpy_get_default_transition, mcrfpy_set_default_transition,
     MCRF_PROPERTY(default_transition,
         "Default transition (Transition) applied when switching scenes without an "
         "explicit transition."
     ), NULL},
    {"default_transition_duration", mcrfpy_get_default_transition_duration,
     mcrfpy_set_default_transition_duration,
     MCRF_PROPERTY(default_transition_duration,
         "Default scene-transition duration in seconds (float). Must be non-negative."
     ), NULL},
    {"default_texture", mcrfpy_get_default_texture, mcrfpy_set_default_texture,
     MCRF_PROPERTY(default_texture,
         "Texture used by Sprite, Entity and Grid when none is given (Texture). Loaded "
         "from assets/kenney_tinydungeon.png on first use; assign a Texture to replace it."
     ), NULL},
    {"save_dir", mcrfpy_get_save_dir, NULL,
     MCRF_PROPERTY(save_dir,
         "Directory used for persistent save data (str, read-only). '/save' under Emscripten."
     ), NULL},
    {NULL}  // Sentinel
};

// #356: PyModule_Type.__dir__ returns only the module __dict__ keys, so descriptors
// living on the module *type* would still be invisible to dir(). Override it to union
// the two -- this is what actually makes the generators (and tab-completion) see them.
static PyObject* mcrfpy_module_dir(PyObject* self, PyObject* Py_UNUSED(ignored))
{
    PyObject* dict = PyModule_GetDict(self);  // borrowed
    if (!dict) return NULL;

    PyObject* names = PyDict_Keys(dict);
    if (!names) return NULL;

    for (PyGetSetDef* gs = mcrfpy_module_getset; gs->name != NULL; gs++) {
        PyObject* name = PyUnicode_FromString(gs->name);
        if (!name || PyList_Append(names, name) < 0) {
            Py_XDECREF(name);
            Py_DECREF(names);
            return NULL;
        }
        Py_DECREF(name);
    }

    if (PyList_Sort(names) < 0) {
        Py_DECREF(names);
        return NULL;
    }
    return names;
}

static PyMethodDef mcrfpy_module_type_methods[] = {
    {"__dir__", mcrfpy_module_dir, METH_NOARGS,
     MCRF_METHOD(mcrfpy, __dir__,
         MCRF_SIG("()", "list"),
         MCRF_DESC("Names of the module's attributes, including the dynamic properties "
                   "(current_scene, scenes, timers, ...) that live as descriptors on the "
                   "module type rather than in the module dict."),
         MCRF_RETURNS("list: sorted attribute names")
     )},
    {NULL}  // Sentinel
};

// Custom module type: carries the dynamic properties as descriptors (#151, #356)
static PyTypeObject McRFPyModuleType = {
    .ob_base = PyVarObject_HEAD_INIT(NULL, 0)
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
    // tp_getattro/tp_setattro inherited from PyModule_Type: generic attribute access
    // finds the tp_getset data descriptors below before touching the module dict.
    .tp_getattro = NULL,
    .tp_setattro = NULL,
    .tp_as_buffer = NULL,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_doc = "McRogueFace module with property support",
    .tp_methods = mcrfpy_module_type_methods,
    .tp_getset = mcrfpy_module_getset,
};

static PyMethodDef mcrfpyMethods[] = {

    // Note: setTimer and delTimer removed in #173 - use Timer objects instead
    {"step", McRFPy_API::_step, METH_VARARGS,
     MCRF_METHOD(mcrfpy, step,
         MCRF_SIG("(dt: float = None)", "float"),
         MCRF_DESC("Run one full simulation frame (headless mode only). Advances the scene "
                   "update, timers, Python Scene.update() callbacks, animations, and scene "
                   "transitions (including their completion), records frame-time metrics, and "
                   "increments the frame counter -- everything a windowed frame does except "
                   "render and input.")
         MCRF_ARGS_START
         MCRF_ARG("dt", "Time to advance in seconds, finite and >= 0. If None, advances to the next scheduled event (timer/animation).")
         MCRF_RETURNS("float: Actual time advanced in seconds. Returns 0.0 in windowed mode.")
         MCRF_NOTE("Rendering is deliberately excluded: it is orthogonal to the clock and costs "
                   "zero simulation time, so a screenshot draws arbitrary state without time "
                   "passing. In windowed mode this is a no-op returning 0.0. Timers run on "
                   "simulation time -- explicit, deterministic time is the point of driving a "
                   "headless test with step().")
         MCRF_NOTE("A headless --exec script must end by calling sys.exit(), because step() is "
                   "the only headless clock: without it the engine cannot advance itself. "
                   "--run-forever keeps a headless process alive, but its loop does not move "
                   "the simulation clock, so timers and animations advance only through "
                   "step()/advance() (#448).")
         MCRF_NOTE("A wide step catches timers up: step(10.0) fires a 1000ms repeating timer "
                   "ten times within the one frame, each call receiving its own deadline as "
                   "runtime, and the timer keeps its phase. Animations receive the whole dt. "
                   "advance() differs only in running a separate frame per deadline.")
         MCRF_RAISES("ValueError", "dt is negative, NaN or infinite")
         MCRF_RAISES("OverflowError", "dt would carry the clock past its int-millisecond range")
         MCRF_RAISES("RuntimeError", "Called from a background thread that currently holds "
                   "mcrfpy.lock(). Advancing a frame from inside the lock re-enters the frame "
                   "the lock synchronises with, which cannot complete until the caller releases. "
                   "Inside the lock, mutate only. (lock() is a no-op on the thread that drives "
                   "the clock, so this cannot fire from script init or a timer callback.)")
         MCRF_RAISES("RuntimeError", "Called from a thread that does not drive the simulation "
                   "clock. The first thread to run a frame owns the clock until it exits (#411).")
         MCRF_LINK("docs/frame-lock.md", "The frame barrier: rules, budget, and failure modes")
     )},
    {"advance", McRFPy_API::_advance, METH_VARARGS,
     MCRF_METHOD(mcrfpy, advance,
         MCRF_SIG("(ms: int)", "int"),
         MCRF_DESC("Advance the simulation clock by exactly ms milliseconds (headless mode only), "
                   "running one simulation frame per timer deadline crossed so that every "
                   "repeating timer fires once per elapsed interval.")
         MCRF_ARGS_START
         MCRF_ARG("ms", "Milliseconds of simulated time to advance. Must be an int >= 0.")
         MCRF_RETURNS("int: Milliseconds actually advanced. Returns 0 in windowed mode, and 0 for advance(0).")
         MCRF_RAISES("TypeError", "ms is not an int (step() is the one that takes float seconds)")
         MCRF_RAISES("ValueError", "ms is negative -- the simulation clock does not run backwards")
         MCRF_NOTE("advance(10000) fires a 1000ms repeating timer exactly 10 times, as step(10.0) "
                   "does, but runs a separate frame at each deadline, so animations and "
                   "Scene.update() see the time between firings. Partial intervals are carried: "
                   "advance(10500) fires it 10 times and leaves it 500ms from its next deadline.")
         MCRF_NOTE("Each boundary is a full simulation frame, so current_frame advances once per "
                   "timer deadline crossed plus once for any residual. advance(0) does nothing at "
                   "all -- use step(0.0) to run a frame without moving the clock.")
         MCRF_NOTE("Read the resulting clock with get_metrics()['simulation_time_ms'] (milliseconds). "
                   "The 'runtime' key is wall clock and is unrelated to simulated time.")
         MCRF_RAISES("OverflowError", "ms would carry the clock past its int-millisecond range")
         MCRF_RAISES("RuntimeError", "Called from a background thread that currently holds "
                   "mcrfpy.lock(), or from a thread that does not drive the clock; see step().")
         MCRF_LINK("docs/frame-lock.md", "The frame barrier: rules, budget, and failure modes")
     )},
    {"exit", McRFPy_API::_exit, METH_NOARGS,
     MCRF_METHOD(mcrfpy, exit,
         MCRF_SIG("()", "None"),
         MCRF_DESC("Cleanly shut down the game engine and exit the application."),
         MCRF_RETURNS("None")
         MCRF_NOTE("This immediately closes the window and terminates the program.")
     )},
    {"set_scale", McRFPy_API::_setScale, METH_VARARGS,
     MCRF_METHOD(mcrfpy, set_scale,
         MCRF_SIG("(multiplier: float)", "None"),
         MCRF_DESC("Deprecated: use Window.resolution instead. Scale the game window size."),
         MCRF_ARGS_START
         MCRF_ARG("multiplier", "Scale factor (e.g., 2.0 for double size)")
         MCRF_RETURNS("None")
         MCRF_NOTE("The internal resolution remains 1024x768, but the window is scaled. This is deprecated - use Window.resolution instead.")
     )},

    {"find", McRFPy_API::_find, METH_VARARGS,
     MCRF_METHOD(mcrfpy, find,
         MCRF_SIG("(name: str, scene: str = None)", "UIDrawable | None"),
         MCRF_DESC("Find the first UI element with the specified name."),
         MCRF_ARGS_START
         MCRF_ARG("name", "Exact name to search for")
         MCRF_ARG("scene", "Scene to search in (default: current scene)")
         MCRF_RETURNS("Frame, Caption, Sprite, Grid, or Entity if found; None otherwise")
         MCRF_NOTE("Searches scene UI elements and entities within grids.")
     )},
    {"find_all", McRFPy_API::_findAll, METH_VARARGS,
     MCRF_METHOD(mcrfpy, find_all,
         MCRF_SIG("(pattern: str, scene: str = None)", "list"),
         MCRF_DESC("Find all UI elements matching a name pattern."),
         MCRF_ARGS_START
         MCRF_ARG("pattern", "Name pattern with optional wildcards (* matches any characters)")
         MCRF_ARG("scene", "Scene to search in (default: current scene)")
         MCRF_RETURNS("list: All matching UI elements and entities")
         MCRF_NOTE("Example: find_all('enemy*') finds all elements starting with 'enemy', find_all('*_button') finds all elements ending with '_button'")
     )},

    {"get_metrics", McRFPy_API::_getMetrics, METH_NOARGS,
     MCRF_METHOD(mcrfpy, get_metrics,
         MCRF_SIG("()", "dict"),
         MCRF_DESC("Get current performance metrics."),
         MCRF_RETURNS("dict: Performance data with keys: frame_time (last frame duration in MILLISECONDS), avg_frame_time (rolling mean frame time over the last 60 frames, in milliseconds), fps (frames per second, derived from avg_frame_time -- a rolling average, not an instantaneous rate), draw_calls (number of draw calls), ui_elements (total UI element count), visible_elements (visible element count), current_frame (frame counter), runtime (WALL-CLOCK seconds since engine start), simulation_time_ms (SIMULATED milliseconds, the deterministic counter advanced only by step()/advance() and the clock headless timers run on), grid_render_time (grid rendering time in ms), entity_render_time (entity rendering time in ms), fov_overlay_time (FOV overlay rendering time in ms), python_time (Python script execution time in ms), animation_time (animation processing time in ms), grid_cells_rendered (grid cell draws this frame, counted per layer), entities_rendered (number of entities drawn this frame), total_entities (total entity count across all rendered grids), audio_sources (Sound and Music objects alive), audio_playing (those the engine is keeping alive because they are playing)")
         MCRF_NOTE("All per-frame counters and timing breakdowns describe the last COMPLETED frame. "
                   "Python callbacks run before the frame is rendered, so the in-progress frame's "
                   "values are not available yet; frame_time, fps, runtime, simulation_time_ms and "
                   "current_frame are live.")
         MCRF_NOTE("'runtime' and 'simulation_time_ms' are DIFFERENT clocks: runtime is wall time in "
                   "seconds and advances on its own; simulation_time_ms is simulated MILLISECONDS and "
                   "moves only when step()/advance() is called, which is headless-only -- in "
                   "windowed mode it stays 0 and timers run on runtime instead. Rendering costs "
                   "zero simulation_time_ms, so a screenshot never moves it.")
     )},

    {"set_random_seed", McRFPy_API::_setRandomSeed, METH_VARARGS,
     MCRF_METHOD(mcrfpy, set_random_seed,
         MCRF_SIG("(seed: int)", "None"),
         MCRF_DESC("Seed the engine's internal random streams and reset them to their start. "
                   "Call this before anything consumes randomness to make a run reproducible."),
         MCRF_ARGS_START
         MCRF_ARG("seed", "Unsigned 32-bit integer, 0 to 4294967295 inclusive")
         MCRF_RETURNS("None")
         MCRF_RAISES("TypeError", "seed is not an integer")
         MCRF_RAISES("ValueError", "seed is negative or larger than 4294967295")
         MCRF_NOTE("Covers the randomness the engine generates on its own behalf: entity "
                   "behaviour selection (Behavior.NOISE4 / NOISE8) and Sound.play_varied(). "
                   "Objects that take their own seed -- NoiseSource, BSP.split_recursive, "
                   "SoundBuffer.sfxr -- are unaffected; seed those individually.")
         MCRF_NOTE("Each subsystem gets an independent stream derived from this one seed, so "
                   "playing sounds does not shift entity behaviour. Reordering or removing a "
                   "stream would change every sequence at a given seed.")
     )},

    {"get_random_seed", McRFPy_API::_getRandomSeed, METH_NOARGS,
     MCRF_METHOD(mcrfpy, get_random_seed,
         MCRF_SIG("()", "int"),
         MCRF_DESC("The seed the engine's internal random streams are using."),
         MCRF_RETURNS("int: the seed set by set_random_seed(), or -- if none was ever set -- "
                      "a seed generated from the system entropy source, recorded, and used "
                      "from then on. This never fails to answer, so a run that was not seeded "
                      "explicitly can still be replayed afterwards by passing this value to "
                      "set_random_seed().")
         MCRF_NOTE("Calling this before any randomness is consumed fixes the seed for the rest "
                   "of the process -- it materialises the value rather than reporting a "
                   "placeholder. Record it in a run log if reproducibility matters.")
     )},

    {"set_dev_console", McRFPy_API::_setDevConsole, METH_VARARGS,
     MCRF_METHOD(mcrfpy, set_dev_console,
         MCRF_SIG("(enabled: bool)", "None"),
         MCRF_DESC("Enable or disable the developer console overlay."),
         MCRF_ARGS_START
         MCRF_ARG("enabled", "True to enable the console (default), False to disable")
         MCRF_RETURNS("None")
         MCRF_NOTE("When disabled, the grave/tilde key will not open the console. Use this to ship games without debug features.")
     )},

    {"start_benchmark", McRFPy_API::_startBenchmark, METH_NOARGS,
     MCRF_METHOD(mcrfpy, start_benchmark,
         MCRF_SIG("()", "None"),
         MCRF_DESC("Start capturing benchmark data to a file."),
         MCRF_RETURNS("None")
         MCRF_RAISES("RuntimeError", "If a benchmark is already running")
         MCRF_NOTE("Benchmark filename is auto-generated from PID and timestamp. Use end_benchmark() to stop and get filename.")
     )},

    {"end_benchmark", McRFPy_API::_endBenchmark, METH_NOARGS,
     MCRF_METHOD(mcrfpy, end_benchmark,
         MCRF_SIG("()", "str"),
         MCRF_DESC("Stop benchmark capture and write data to JSON file."),
         MCRF_RETURNS("str: The filename of the written benchmark data")
         MCRF_RAISES("RuntimeError", "If no benchmark is currently running")
         MCRF_NOTE("Returns the auto-generated filename (e.g., 'benchmark_12345_20250528_143022.json')")
     )},

    {"log_benchmark", McRFPy_API::_logBenchmark, METH_VARARGS,
     MCRF_METHOD(mcrfpy, log_benchmark,
         MCRF_SIG("(message: str)", "None"),
         MCRF_DESC("Add a log message to the current benchmark frame."),
         MCRF_ARGS_START
         MCRF_ARG("message", "Text to associate with the current frame")
         MCRF_RETURNS("None")
         MCRF_RAISES("RuntimeError", "If no benchmark is currently running")
         MCRF_NOTE("Messages appear in the 'logs' array of each frame in the output JSON.")
     )},

    // #356: the module's dynamic attributes (current_scene, scenes, timers, ...) are
    // real descriptors on McRFPyModuleType now, not a PEP-562 __getattr__ shim.

    // #219: Thread synchronization
    {"lock", PyLock::lock, METH_NOARGS,
     MCRF_METHOD(mcrfpy, lock,
         MCRF_SIG("()", "_LockContext"),
         MCRF_DESC("Get a context manager for thread-safe access to mcrfpy objects from background threads."),
         MCRF_RETURNS("_LockContext: A context manager that blocks until safe to touch engine objects")
         MCRF_NOTE("Any access to mcrfpy objects from a non-main thread must happen inside "
                   "`with mcrfpy.lock():`; behavior outside the lock is undefined. On a worker "
                   "thread the context manager blocks (GIL released) until the render loop opens a "
                   "safe window between frames. On the thread that drives the clock (the main thread, "
                   "unless a background thread runs frames with step()/advance()) it is a no-op.")
         MCRF_NOTE("INSIDE THE LOCK, MUTATE ONLY. The main thread parks until every holder "
                   "releases, so hold time is added to frame time roughly 1:1 -- a 10 ms hold "
                   "costs the frame 10 ms, and presents as engine stutter rather than as a "
                   "misbehaving handler. Do I/O, waiting, and computation OUTSIDE the block and "
                   "apply the result inside it. Calling mcrfpy.step() or mcrfpy.advance() while "
                   "holding the lock raises RuntimeError rather than deadlocking.")
         MCRF_LINK("docs/frame-lock.md", "The frame barrier: rules, budget, and failure modes")
     )},

    // #215: Bresenham line algorithm (replaces mcrfpy.libtcod.line)
    {"bresenham", (PyCFunction)McRFPy_API::_bresenham, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(mcrfpy, bresenham,
         MCRF_SIG("(start, end, include_start=True, include_end=True)", "list[tuple[int, int]]"),
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

    {"_sync_storage", mcrfpy_sync_storage, METH_NOARGS,
     MCRF_METHOD(mcrfpy, _sync_storage,
         MCRF_SIG("()", "None"),
         MCRF_DESC("Flush save directory to persistent storage."),
         MCRF_RETURNS("None")
         MCRF_NOTE("On WebAssembly, flushes the /save/ directory to IndexedDB via IDBFS. "
                   "On desktop, this is a no-op since writes go directly to disk. "
                   "Call this after writing files to mcrfpy.save_dir to ensure persistence.")
     )},

    {NULL, NULL, 0, NULL}
};

static PyObject* mcrfpy_module_create(PyObject* spec, PyModuleDef* def);

// Multi-phase init, used only to declare the module's threading/interpreter
// contract; the real setup still happens once, in mcrfpy_module_create().
static PyModuleDef_Slot mcrfpySlots[] = {
    {Py_mod_create, (void*)mcrfpy_module_create},
    // The engine (GameEngine, static PyTypeObjects, PythonObjectCache) is
    // process-global. Refuse every subinterpreter -- including 'legacy' ones,
    // which would otherwise get a copy of the main interpreter's module dict.
    {Py_mod_multiple_interpreters, Py_MOD_MULTIPLE_INTERPRETERS_NOT_SUPPORTED},
    // Explicit: mcrfpy relies on the GIL (FrameLock/#219, borrowed refs). On a
    // free-threaded build this keeps the GIL enabled until that is audited.
    {Py_mod_gil, Py_MOD_GIL_USED},
    {0, NULL}
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
    0,                     /* m_size - no per-module state; engine state is process-global (see mcrfpySlots) */
    mcrfpyMethods,         /* m_methods - added by CPython after Py_mod_create */
    mcrfpySlots,           /* m_slots */
    NULL,                  /* traverseproc m_traverse - A traversal function to call during GC traversal of the module object */
    NULL,                  /* inquiry m_clear - A clear function to call during GC clearing of the module object */
    NULL                   /* freefunc m_free - A function to call during deallocation of the module object */
};

// Module initializer fn, passed to PyImport_AppendInittab
PyObject* PyInit_mcrfpy()
{
    return PyModuleDef_Init(&mcrfpyModule);
}

// Py_mod_create: builds the module once per process. Multi-phase modules are
// re-created if removed from sys.modules and imported again; returning the
// existing module keeps the static types and enum caches from being rebuilt.
static PyObject* mcrfpy_module_create(PyObject* spec, PyModuleDef* def)
{
    // Py_MOD_MULTIPLE_INTERPRETERS_NOT_SUPPORTED is only enforced for
    // interpreters with check_multi_interp_extensions set; 'legacy'
    // subinterpreters on a GIL build skip it. Unlike single-phase init,
    // Py_mod_create runs on every import in every interpreter, so check here.
    if (PyInterpreterState_Get() != PyInterpreterState_Main()) {
        PyErr_SetString(PyExc_ImportError,
            "mcrfpy does not support loading in subinterpreters: "
            "the game engine is process-global and lives in the main interpreter");
        return NULL;
    }

    static PyObject* created = nullptr;
    if (created) {
        return Py_NewRef(created);
    }

    PyObject* name = PyObject_GetAttrString(spec, "name");
    if (!name) {
        return NULL;
    }
    PyObject* m = PyModule_NewObject(name);
    Py_DECREF(name);

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
        &PyUIFrameType, &PyUICaptionType, &PyUISpriteType, &PyGridDataType,
        &PyUILineType, &PyUICircleType, &PyUIArcType, &PyViewport3DType,
        &mcrfpydef::PyUIGridViewType,
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
        &PyUICaptionType, &PyUISpriteType, &PyUIFrameType, &PyUIEntityType,
        &PyUILineType, &PyUICircleType, &PyUIArcType, &PyViewport3DType,
        &mcrfpydef::PyUIGridViewType,  // #252/#361: the widget. "Grid" is an alias.
        &PyGridDataType,               // #361: the map. Public, and NOT a drawable.

        /*3D entities*/
        &mcrfpydef::PyEntity3DType, &mcrfpydef::PyEntityCollection3DType,
        &mcrfpydef::PyEntityCollection3DIterType, &mcrfpydef::PyModel3DType,
        &mcrfpydef::PyBillboardType, &mcrfpydef::PyVoxelGridType,
        &mcrfpydef::PyVoxelRegionType,

        /*grid layers (#147)*/
        &PyColorLayerType, &PyTileLayerType,

        /*timer*/
        &PyTimerType,

        /*window singleton type (#184 - type exported for isinstance checks)*/
        &PyWindowType,

        /*scene class*/
        &PySceneType,

        /*audio (#66)*/
        &PySoundType,
        &PySoundBufferType,
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

        /*tiled map/tileset loading*/
        &mcrfpydef::PyTileSetFileType,
        &mcrfpydef::PyTileMapFileType,
        &mcrfpydef::PyWangSetType,

        /*LDtk project loading*/
        &mcrfpydef::PyLdtkProjectType,
        &mcrfpydef::PyAutoRuleSetType,

        /*masked observation - result of GridData.observe() (fog-of-war/AI perception)*/
        &mcrfpydef::PyVisibilityMaskType,

        nullptr};

    // Types that are used internally but NOT exported to module namespace (#189)
    // These still need PyType_Ready() but are not added to module
    PyTypeObject* internal_types[] = {
        /*game map data - returned by Grid.at() but not directly instantiable*/
        &PyUIGridPointType,

        /*#335: layer.edit() context manager - returned by ColorLayer/TileLayer.edit(), not instantiable*/
        &mcrfpydef::PyLayerEditType,

        /*3D navigation grid - returned by Viewport3D.at() but not directly instantiable*/
        &mcrfpydef::PyVoxelPointType,

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

        /*animation - constructed internally by drawable.animate() and returned by mcrfpy.animations,
          but not directly instantiable from Python (pre-1.0 API freeze)*/
        &PyAnimationType,

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

    // Set up PyVoxelGridType methods and getsetters (Milestone 9)
    mcrfpydef::PyVoxelGridType.tp_methods = PyVoxelGrid::methods;
    mcrfpydef::PyVoxelGridType.tp_getset = PyVoxelGrid::getsetters;

    // Set up PyVoxelRegionType getsetters (Milestone 11)
    mcrfpydef::PyVoxelRegionType.tp_getset = PyVoxelRegion::getsetters;

    // Set up PyShaderType methods and getsetters (#106)
    mcrfpydef::PyShaderType.tp_methods = PyShader::methods;
    mcrfpydef::PyShaderType.tp_getset = PyShader::getsetters;

    // Set up PyPropertyBindingType and PyCallableBindingType getsetters (#106)
    mcrfpydef::PyPropertyBindingType.tp_getset = PyPropertyBindingType::getsetters;
    mcrfpydef::PyCallableBindingType.tp_getset = PyCallableBindingType::getsetters;

    // Set up PyUniformCollectionType methods (#106)
    mcrfpydef::PyUniformCollectionType.tp_methods = ::PyUniformCollectionType::methods;

    // Set up Tiled types methods and getsetters
    mcrfpydef::PyTileSetFileType.tp_methods = PyTileSetFile::methods;
    mcrfpydef::PyTileSetFileType.tp_getset = PyTileSetFile::getsetters;
    mcrfpydef::PyTileMapFileType.tp_methods = PyTileMapFile::methods;
    mcrfpydef::PyTileMapFileType.tp_getset = PyTileMapFile::getsetters;
    mcrfpydef::PyWangSetType.tp_methods = PyWangSet::methods;
    mcrfpydef::PyWangSetType.tp_getset = PyWangSet::getsetters;

    // Texture methods (from_bytes, composite, hsl_shift)
    mcrfpydef::PyTextureType.tp_methods = PyTexture::methods;

    // LDtk types
    mcrfpydef::PyLdtkProjectType.tp_methods = PyLdtkProject::methods;
    mcrfpydef::PyLdtkProjectType.tp_getset = PyLdtkProject::getsetters;
    mcrfpydef::PyAutoRuleSetType.tp_methods = PyAutoRuleSet::methods;
    mcrfpydef::PyAutoRuleSetType.tp_getset = PyAutoRuleSet::getsetters;

    // Set up weakref support for all types that need it
    PyTimerType.tp_weaklistoffset = offsetof(PyTimerObject, weakreflist);
    PyUIFrameType.tp_weaklistoffset = offsetof(PyUIFrameObject, weakreflist);
    PyUICaptionType.tp_weaklistoffset = offsetof(PyUICaptionObject, weakreflist);
    PyUISpriteType.tp_weaklistoffset = offsetof(PyUISpriteObject, weakreflist);
    PyGridDataType.tp_weaklistoffset = offsetof(PyGridDataObject, weakreflist);
    mcrfpydef::PyUIGridViewType.tp_weaklistoffset = offsetof(PyUIGridViewObject, weakreflist);
    PyUIEntityType.tp_weaklistoffset = offsetof(PyUIEntityObject, weakreflist);
    PyUILineType.tp_weaklistoffset = offsetof(PyUILineObject, weakreflist);
    PyUICircleType.tp_weaklistoffset = offsetof(PyUICircleObject, weakreflist);
    PyUIArcType.tp_weaklistoffset = offsetof(PyUIArcObject, weakreflist);
    PyViewport3DType.tp_weaklistoffset = offsetof(PyViewport3DObject, weakreflist);
    mcrfpydef::PyEntity3DType.tp_weaklistoffset = offsetof(PyEntity3DObject, weakreflist);
    mcrfpydef::PyModel3DType.tp_weaklistoffset = offsetof(PyModel3DObject, weakreflist);
    mcrfpydef::PyBillboardType.tp_weaklistoffset = offsetof(PyBillboardObject, weakreflist);

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

    // #361: "Grid" is an alias for GridView -- the SAME type object, not a subclass,
    // so isinstance() works in both directions and there is no MRO to explain.
    // It is NOT deprecated: now that GridData is a separate public type,
    // Grid(grid_size=...) is simply "a GridView that creates its own GridData" --
    // a constructor overload, not legacy behavior.
    Py_INCREF(&mcrfpydef::PyUIGridViewType);
    PyModule_AddObject(m, "Grid", (PyObject*)&mcrfpydef::PyUIGridViewType);

    // Add default_font and default_texture to module
    McRFPy_API::default_font = std::make_shared<PyFont>("assets/JetbrainsMono.ttf");
    // Set later, once the engine exists. (default_texture is a module property, #451.)
    PyModule_AddObject(m, "default_font", Py_None);

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

    // Add window singleton (#184). The same object Window.get() returns (#430).
    PyObject* window_instance = PyWindow::instance();
    if (!window_instance || PyModule_AddObject(m, "window", window_instance) < 0) {
        Py_XDECREF(window_instance);
        Py_DECREF(m);
        return NULL;
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

    // Add Perspective enum class for entity perspective_map values (#294)
    PyObject* perspective_class = PyPerspective::create_enum_class(m);
    if (!perspective_class) {
        PyErr_Clear();
    }

    // Add Heuristic enum class for A* heuristic selection (#315)
    PyObject* heuristic_class = PyHeuristic::create_enum_class(m);
    if (!heuristic_class) {
        PyErr_Clear();
    }

    // Add Alignment enum class for automatic child positioning
    PyObject* alignment_class = PyAlignment::create_enum_class(m);
    if (!alignment_class) {
        // If enum creation fails, continue without it (non-fatal)
        PyErr_Clear();
    }

    // Add Behavior enum class for entity behavior types (#297)
    PyObject* behavior_class = PyBehavior::create_enum_class(m);
    if (!behavior_class) {
        PyErr_Clear();
    }

    // Add Trigger enum class for entity step callback triggers (#298)
    PyObject* trigger_class = PyTrigger::create_enum_class(m);
    if (!trigger_class) {
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

#ifdef __EMSCRIPTEN__
    // WASM: Monkeypatch builtins.open() so that writes to /save/ auto-sync IDBFS.
    // This makes `with open(path, 'w') as f: ...` persist transparently on web.
    PyRun_SimpleString(R"(
import builtins as _builtins
_mcrf_original_open = _builtins.open

class _McRF_SyncingFile:
    __slots__ = ('_file',)
    def __init__(self, f):
        object.__setattr__(self, '_file', f)
    def __getattr__(self, name):
        return getattr(self._file, name)
    def __enter__(self):
        self._file.__enter__()
        return self
    def __exit__(self, *args):
        result = self._file.__exit__(*args)
        import mcrfpy
        mcrfpy._sync_storage()
        return result
    def close(self):
        self._file.close()
        import mcrfpy
        mcrfpy._sync_storage()
    def __iter__(self):
        return iter(self._file)
    def __next__(self):
        return next(self._file)
    def writable(self):
        return self._file.writable()
    def readable(self):
        return self._file.readable()
    def seekable(self):
        return self._file.seekable()

def _mcrf_syncing_open(path, mode='r', *args, **kwargs):
    f = _mcrf_original_open(path, mode, *args, **kwargs)
    if any(c in mode for c in 'wxa+') and str(path).startswith('/save'):
        return _McRF_SyncingFile(f)
    return f

_builtins.open = _mcrf_syncing_open
del _builtins
)");
#endif

    //McRFPy_API::mcrf_module = m;
    created = Py_NewRef(m);
    return m;
}

// init_python - configure interpreter details here
#ifdef Py_GIL_DISABLED
// PyConfig.enable_gil for free-threaded builds: 1 (_PyConfig_GIL_ENABLE) unless
// MCRF_UNSAFE_NOGIL=1, which runs with the GIL disabled (0). mcrfpy is NOT
// audited for that -- the switch exists to measure what breaks (thread-safety
// stress tests, TSan), not for games. The isolated config ignores PYTHON_GIL.
static int mcrf_requested_gil_setting()
{
    const char* v = std::getenv("MCRF_UNSAFE_NOGIL");
    if (v && std::string(v) == "1") {
        std::cerr << "mcrogueface: MCRF_UNSAFE_NOGIL=1 -- running with the GIL DISABLED; "
                     "mcrfpy is not thread-safe without it (testing only)" << std::endl;
        return 0;  // _PyConfig_GIL_DISABLE
    }
    return 1;      // _PyConfig_GIL_ENABLE
}
#endif

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
#ifdef Py_GIL_DISABLED
    // mcrfpy declares Py_MOD_GIL_USED and is imported before any user code,
    // so the GIL would be re-enabled anyway; pin it explicitly instead of
    // emitting CPython's "GIL has been enabled" RuntimeWarning at startup.
    config.enable_gil = mcrf_requested_gil_setting();
#endif
    config.dev_mode = 0;

    // Configure UTF-8 for stdio
    PyConfig_SetString(&config, &config.stdio_encoding, L"UTF-8");
    PyConfig_SetString(&config, &config.stdio_errors, L"surrogateescape");
    config.configure_c_stdio = 1;

#ifdef __EMSCRIPTEN__
    // WASM: Use absolute paths in virtual filesystem
    PyConfig_SetString(&config, &config.executable, L"/mcrogueface");
    PyConfig_SetString(&config, &config.home, MCRF_PY_HOME_W);
    status = PyConfig_SetBytesString(&config, &config.program_name, "mcrogueface");

    // Set up module search paths for WASM
    config.module_search_paths_set = 1;
    const wchar_t* wasm_paths[] = {
        L"/scripts",
        MCRF_PY_HOME_W
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
        auto site_packages = sibling_venv / "lib" / MCRF_PY_STDLIB_DIRNAME / "site-packages";
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
        MCRF_PY_EXT_DIR_W,
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

    // #378: pre-initialize in UTF-8 mode. Without this, the filesystem encoding falls
    // back to ASCII -- so open() with no explicit encoding= cannot read a UTF-8 file,
    // even though sys.getdefaultencoding() and the locale both say UTF-8. This is the
    // init path main.cpp uses; init_python() above has always done this correctly.
    PyPreConfig preconfig;
    PyPreConfig_InitIsolatedConfig(&preconfig);
    preconfig.utf8_mode = 1;

    status = Py_PreInitialize(&preconfig);
    if (PyStatus_Exception(status)) {
        return status;
    }

    PyConfig pyconfig;
    PyConfig_InitIsolatedConfig(&pyconfig);
#ifdef Py_GIL_DISABLED
    // mcrfpy declares Py_MOD_GIL_USED and is imported before any user code,
    // so the GIL would be re-enabled anyway; pin it explicitly instead of
    // emitting CPython's "GIL has been enabled" RuntimeWarning at startup.
    pyconfig.enable_gil = mcrf_requested_gil_setting();
#endif

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
    } else if (!config.exec_scripts.empty()) {
        // --exec mode: argv[0] = last exec script path so sys.argv[0] matches the running
        // script, mirroring normal Python script-mode behavior. Any script_args populated
        // via the `--` passthrough marker (see CommandLineParser) become argv[1:] so
        // fuzzers/libFuzzer can receive their flags through atheris.Setup(sys.argv, ...).
        argv_storage.push_back(config.exec_scripts.back().wstring());
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
        auto site_packages = venv_root / "lib" / MCRF_PY_STDLIB_DIRNAME / "site-packages";
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
        auto site_packages = sibling_venv / "lib" / MCRF_PY_STDLIB_DIRNAME / "site-packages";
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
    PyConfig_SetString(&pyconfig, &pyconfig.home, MCRF_PY_HOME_W);

    // Set up module search paths for WASM
    pyconfig.module_search_paths_set = 1;
    const wchar_t* wasm_paths[] = {
        L"/scripts",
        MCRF_PY_HOME_W
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
        MCRF_PY_EXT_DIR_W,
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
    if (mcrf::PyRef repr{PyObject_Repr(McRFPy_API::mcrf_module)}) {
        std::cout << PyUnicode_AsUTF8(repr.get()) << std::endl;
    }

    PyObject_SetAttrString(McRFPy_API::mcrf_module, "default_font", mcrf::PyRef(McRFPy_API::default_font->pyObject()).get());

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
        PyObject_SetAttrString(McRFPy_API::mcrf_module, "default_font", mcrf::PyRef(McRFPy_API::default_font->pyObject()).get());
    }
}

void McRFPy_API::executeScript(std::string filename, bool main_script)
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

    // Read with std::ifstream instead of PyRun_SimpleFile: a FILE* can't cross the
    // MinGW/MSVC CRT boundary.
    std::ifstream file(script_path_str);
    if (!file.is_open()) {
        std::cout << "Failed to open script: " << script_path_str << std::endl;
        return;
    }

    std::string script_content((std::istreambuf_iterator<char>(file)),
                                std::istreambuf_iterator<char>());
    file.close();

    if (main_script && setMainScriptDir(script_path_str) < 0) {
        PyErr_Print();
        return;
    }
    runScriptSource(script_content, script_path_str);
}

int McRFPy_API::setMainScriptDir(const std::string& script_path)
{
#ifdef __EMSCRIPTEN__
    // The virtual filesystem has one scripts directory, /scripts, already on sys.path.
    (void)script_path;
    return 0;
#else
    // executable_path() is the canonical binary location (through any symlink), so this
    // entry is the engine's own scripts/, which is only right when the script is there.
    const std::filesystem::path dir =
        std::filesystem::absolute(std::filesystem::path(script_path)).lexically_normal().parent_path();
    const std::filesystem::path exe_scripts = std::filesystem::path(executable_path()) / "scripts";

    PyObject* sys_path = PySys_GetObject("path");  // borrowed
    if (!sys_path || !PyList_Check(sys_path)) {
        PyErr_SetString(PyExc_RuntimeError, "sys.path is not a list");
        return -1;
    }
    mcrf::PyRef dir_str(PyUnicode_DecodeFSDefault(dir.string().c_str()));
    mcrf::PyRef exe_scripts_str(PyUnicode_DecodeFSDefault(exe_scripts.string().c_str()));
    if (!dir_str || !exe_scripts_str) return -1;

    const Py_ssize_t at = PySequence_Index(sys_path, exe_scripts_str.get());
    if (at < 0) {
        PyErr_Clear();
        return PyList_Insert(sys_path, 0, dir_str.get());
    }
    if (PyList_SetItem(sys_path, at, dir_str.get()) < 0) return -1;  // steals
    dir_str.release();
    if (at == 0) return 0;
    // Keep it first, as Python does.
    mcrf::PyRef entry(PySequence_GetItem(sys_path, at));
    if (!entry || PySequence_DelItem(sys_path, at) < 0) return -1;
    return PyList_Insert(sys_path, 0, entry.get());
#endif
}

int McRFPy_API::runScriptSource(const std::string& source, const std::string& path)
{
    PyObject* main_module = PyImport_AddModule("__main__");
    if (!main_module) {
        PyErr_Print();
        return -1;
    }
    PyObject* main_dict = PyModule_GetDict(main_module);
    if (mcrf::dict_steal(main_dict, "__file__", PyUnicode_DecodeFSDefault(path.c_str())) < 0) {
        PyErr_Print();
        return -1;
    }
    // Compiling under the real path is what puts it in tracebacks (PyRun_SimpleString
    // compiles as "<string>").
    mcrf::PyRef code(Py_CompileString(source.c_str(), path.c_str(), Py_file_input));
    if (!code) {
        PyErr_Print();
        return -1;
    }
    mcrf::PyRef result(PyEval_EvalCode(code.get(), main_dict, main_dict));
    if (!result) {
        PyErr_Print();   // exits the process on SystemExit, as PyRun_SimpleString does
        return -1;
    }
    return 0;
}

std::shared_ptr<PyTexture> McRFPy_API::defaultTexture()
{
    if (!default_texture) {
        if (!mcrf::require_display_py("the default texture (mcrfpy.default_texture)")) return nullptr;
        default_texture = std::make_shared<PyTexture>("assets/kenney_tinydungeon.png", 16, 16);
    }
    return default_texture;
}

void McRFPy_API::api_shutdown()
{
    // Audio devices are closed by mcrf::audio::shutdown(), registered with Py_AtExit (#400).
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

    Scene* scene = Resources::game->getScene(scene_cstr);
    if (!scene || !scene->ui_elements)
    {
        PyErr_SetString(PyExc_RuntimeError, "No scene found by that name");
        return NULL;
    }
    // #430: one wrapper per scene, keyed on Scene::children_serial.
    // #183: scene_name tracks scene ownership (no owning drawable).
    return UICollection::pyobject_for(scene->children_serial, scene->ui_elements,
                                      nullptr, scene_cstr);
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
	
	try {
		game->changeScene(newscene, transition_type, duration);
	} catch (const mcrf::NoDisplayError& e) {  // #451
		PyErr_SetString(PyExc_RuntimeError, e.what());
		return NULL;
	}
    Py_INCREF(Py_None);
    return Py_None;		
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

        // The live wrapper, or (#180, orphaned timer) a new registered one
        PyObject* timer_obj = PyTimer::pyobject_for(timer);
        if (!timer_obj) {
            for (PyObject* o : timer_objs) Py_DECREF(o);
            return NULL;
        }
        timer_objs.push_back(timer_obj);
    }

    PyObject* tuple = PyTuple_New(timer_objs.size());
    if (!tuple) {
        for (PyObject* o : timer_objs) Py_DECREF(o);
        return NULL;
    }

    for (Py_ssize_t i = 0; i < static_cast<Py_ssize_t>(timer_objs.size()); i++) {
        // timer_objs already holds a new reference from PyTimer::pyobject_for()
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

// B7 (#395) - Driving a frame from inside mcrfpy.lock() is refused, loudly.
//
// A background thread holding the frame lock that calls step()/advance() re-enters
// runSimFrame(). If any other thread is waiting, the re-entered frame's closeWindow()
// waits for `active` to reach 0 -- and the caller's own hold is part of `active`, so
// it never can. The main thread is already parked in the outer frame's closeWindow()
// waiting on the same count. Nothing times out: FrameLock's condition variable has no
// deadline (that was #398). The process hangs with no error, no log line, and no
// stack to look at, and it presents as "the engine froze".
//
// Even in the one case that does NOT hang -- no other thread waiting, so hasWaiting()
// short-circuits the safe window -- the call still runs a whole simulation frame from
// a non-main thread while the main thread is parked mid-frame: timers, Scene.update(),
// animations, transitions, and currentFrame++ all execute off the clock's owner. That
// is the mutate-only rule (never drive a frame from inside the lock) violated in the
// exact way rule 1 exists to forbid, and its "success" is worse than the hang because
// it produces a plausible-looking trace with two frame bodies interleaved.
//
// So: raise. The two alternatives were both considered and both rejected.
//   * A silent no-op returns 0.0 to a caller that asked for time to pass. The world
//     does not advance, the trace merely looks sparse, and nothing says why -- the
//     same failure shape SimClock.advance() is explicitly contracted against.
//   * A re-entrancy guard that runs the frame but skips the safe window makes the
//     deadlock go away while leaving the off-thread frame body in place, i.e. it
//     hides the symptom of the thing that is actually wrong.
// A RuntimeError names the rule at the call site, in the offending thread, at the
// instant of the mistake. Fail Early.
//
// Note this cannot fire on the clock's owner (#411): mcrfpy.lock() is a no-op there, so
// the owner never becomes a holder and `with mcrfpy.lock(): mcrfpy.step()` in a script or
// a timer callback keeps working exactly as before.
//
// #411 - The second check: only the clock's owner may run a frame. Without it a thread
// that holds nothing could call step() while another thread (or the engine's own loop)
// was also running frames, and two frame bodies would run concurrently over one scene
// graph, timer map and animation manager -- a plausible return value and intermittent
// corruption. The lock check comes first so a holder is told about the lock, the rule it
// is actually breaking.
static bool frameAdvanceAllowed(const char* fname)
{
    if (Resources::game->getFrameLock().heldByCurrentThread()) {
        PyErr_Format(PyExc_RuntimeError,
            "mcrfpy.%s() cannot be called while this thread holds mcrfpy.lock(): it would "
            "re-enter the frame the lock is synchronising with, and the frame cannot complete "
            "until this thread releases. Inside the lock, mutate only -- no frame advance, no "
            "I/O, no blocking wait. Compute outside the lock and apply inside it.",
            fname);
        return false;
    }
    if (!Resources::game->claimClock()) {
        PyErr_Format(PyExc_RuntimeError,
            "mcrfpy.%s() was called from a thread that does not drive the simulation clock. "
            "Exactly one thread runs frames: the first to call step()/advance() (or the main "
            "thread, once the engine's own loop is running), until that thread exits. Run "
            "frames from that thread, and hand work to it -- from other threads, apply changes "
            "inside `with mcrfpy.lock():` instead.",
            fname);
        return false;
    }
    return true;
}

// #153 - Headless simulation control
PyObject* McRFPy_API::_step(PyObject* self, PyObject* args) {
    PyObject* dt_obj = Py_None;
    if (!PyArg_ParseTuple(args, "|O", &dt_obj)) return NULL;

    float dt;
    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "Game engine not initialized");
        return NULL;
    }
    if (dt_obj == Py_None) {
        // None means "advance to next event"
        dt = -1.0f;
    } else if (PyFloat_Check(dt_obj) || (PyLong_Check(dt_obj) && !PyBool_Check(dt_obj))) {
        double d = PyFloat_AsDouble(dt_obj);
        if (d == -1.0 && PyErr_Occurred()) return NULL;
        // Before this check a negative dt silently meant "next event" (the internal
        // sentinel), and NaN / inf / huge values hit an unchecked float->int cast that
        // wrapped the clock negative.
        if (!std::isfinite(d) || d < 0.0) {
            PyErr_SetString(PyExc_ValueError,
                "step() dt must be a finite number of seconds >= 0 (or None for the next event)");
            return NULL;
        }
        if (d * 1000.0 > static_cast<double>(INT_MAX - game->getSimulationTime())) {
            PyErr_SetString(PyExc_OverflowError,
                "step() dt would overflow the simulation clock (int milliseconds)");
            return NULL;
        }
        dt = static_cast<float>(d);
    } else {
        PyErr_SetString(PyExc_TypeError, "step() argument must be a float, int, or None");
        return NULL;
    }
    if (!frameAdvanceAllowed("step")) return NULL;

    float actual_dt = game->step(dt);
    return PyFloat_FromDouble(actual_dt);
}

// #396 - Bounded simulation advance with per-interval timer semantics
PyObject* McRFPy_API::_advance(PyObject* self, PyObject* args) {
    PyObject* ms_obj = nullptr;
    if (!PyArg_ParseTuple(args, "O", &ms_obj)) return NULL;

    // Milliseconds, integer only. Deliberately NOT accepting a float: step() takes float
    // seconds, and silently reinterpreting advance(1.0) as one millisecond would be a
    // trap. The simulation clock is integer milliseconds; keep the argument in its units.
    if (!PyLong_Check(ms_obj) || PyBool_Check(ms_obj)) {
        PyErr_SetString(PyExc_TypeError,
            "advance() argument must be an int number of MILLISECONDS "
            "(step() is the one that takes float seconds)");
        return NULL;
    }

    long ms = PyLong_AsLong(ms_obj);
    if (ms == -1 && PyErr_Occurred()) return NULL;

    if (ms < 0) {
        PyErr_SetString(PyExc_ValueError, "advance() milliseconds must be >= 0; the simulation clock does not run backwards");
        return NULL;
    }
    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "Game engine not initialized");
        return NULL;
    }
    if (ms > INT_MAX - game->getSimulationTime()) {
        PyErr_SetString(PyExc_OverflowError, "advance() milliseconds would overflow the simulation clock (int milliseconds)");
        return NULL;
    }
    if (!frameAdvanceAllowed("advance")) return NULL;

    return PyLong_FromLong(game->advance(static_cast<int>(ms)));
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

// Also search Grid entities (forward-declared: find_in_collection recurses
// into grid children via GridData, and the two helpers are mutually called).
static void find_in_grid_entities(GridData* grid, const std::string& pattern,
                                bool find_all, PyObject* results);

// Helper to recursively search a collection for named elements.
// visited_grids: #359 - N views can share ONE GridData (split-screen/minimap).
// asGridData() returns the same GridData* from each of them, so without this set
// the shared grid's entities and overlay children are walked (and appended) once
// per view -- findAll() would return N duplicate wrappers for the same object.
static void find_in_collection(std::vector<std::shared_ptr<UIDrawable>>* collection, const std::string& pattern,
                             bool find_all, PyObject* results,
                             std::unordered_set<GridData*>& visited_grids) {
    if (!collection) return;

    for (auto& drawable : *collection) {
        if (PyErr_Occurred()) return;  // a nested search failed
        if (!drawable) continue;
        
        // Check this element's name
        if (name_matches_pattern(drawable->name, pattern)) {
            // #369: go through the cache-aware converter so find() returns the caller's
            // existing wrapper (and Python subclass), not a fresh identity-less one.
            PyObject* py_obj = UIDrawable::pyobject_for(drawable);
            if (py_obj == Py_None) {
                Py_DECREF(py_obj);
                py_obj = nullptr;
            } else if (!py_obj) {
                return;  // conversion failed: leave the error set for the caller (#430)
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
            find_in_collection(frame->children.get(), pattern, find_all, results, visited_grids);
            if (!find_all && PyList_Size(results) > 0) {
                return;  // Found one, stop searching
            }
        }

        // #364 - A grid's overlay children belong to the VIEW, so they are searched
        // per view and NOT deduplicated: two views over one GridData hold different
        // children, and each must be visited.
        if (drawable->derived_type() == PyObjectsEnum::UIGRIDVIEW) {
            auto view = std::static_pointer_cast<UIGridView>(drawable);
            find_in_collection(view->children.get(), pattern, find_all, results, visited_grids);
            if (!find_all && PyList_Size(results) > 0) {
                return;
            }
        }

        // #357 - Recursively search a grid's entities. Dispatch via asGridData()
        // (#355), not derived_type(): a real mcrfpy.Grid() is a UIGridView
        // (PyObjectsEnum::UIGRIDVIEW), so gating on UIGRID here would be
        // structurally unreachable again.
        // #359 - entities are shared world content, so visit each GridData exactly
        // once per search: several views may point at the same data.
        if (GridData* gd = drawable->asGridData()) {
            if (visited_grids.insert(gd).second) {
                find_in_grid_entities(gd, pattern, find_all, results);
                if (!find_all && PyList_Size(results) > 0) {
                    return;
                }
            }
        }
    }
}

static void find_in_grid_entities(GridData* grid, const std::string& pattern,
                                bool find_all, PyObject* results) {
    if (!grid || !grid->entities) return;

    for (auto& entity : *grid->entities) {
        if (!entity) continue;

        // Entities delegate name to their sprite
        if (name_matches_pattern(entity->sprite.name, pattern)) {
            // #266/#430: the cache-aware converter returns the caller's existing
            // wrapper (and Python subclass), never a fresh identity-less one.
            mcrf::PyRef py_obj(mcrf::to_python(entity));
            if (!py_obj || PyList_Append(results, py_obj.get()) < 0) return;  // error set
            if (!find_all) return;
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
    
    // Search the scene's UI elements. find_in_collection recurses into a
    // grid's entities and overlay children via asGridData() (#355/#357).
    std::unordered_set<GridData*> visited_grids;  // #359 - shared GridData visited once
    find_in_collection(ui_elements.get(), name, false, results, visited_grids);
    if (PyErr_Occurred()) {
        Py_DECREF(results);
        return NULL;
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
    
    // Search the scene's UI elements. find_in_collection recurses into a
    // grid's entities and overlay children via asGridData() (#355/#357).
    std::unordered_set<GridData*> visited_grids;  // #359 - shared GridData visited once
    find_in_collection(ui_elements.get(), pattern, true, results, visited_grids);
    if (PyErr_Occurred()) {
        Py_DECREF(results);
        return NULL;
    }

    return results;
}

// #394 -- seed the engine's internal random streams from Python.
//
// Deliberately strict about range: std::mt19937 takes a 32-bit seed, so silently
// truncating 2**32 to 0 would make two "different" seeds produce identical runs and
// nothing would report it. An out-of-range seed raises instead.
PyObject* McRFPy_API::_setRandomSeed(PyObject* self, PyObject* args) {
    PyObject* seed_obj = nullptr;
    if (!PyArg_ParseTuple(args, "O", &seed_obj)) {
        return NULL;
    }
    // Reject bool explicitly: PyLong_Check(True) is true, and set_random_seed(True)
    // is far more likely to be a mistake than a request to seed with 1.
    if (PyBool_Check(seed_obj) || !PyLong_Check(seed_obj)) {
        PyErr_Format(PyExc_TypeError, "seed must be an integer, got %s",
                     Py_TYPE(seed_obj)->tp_name);
        return NULL;
    }

    int overflow = 0;
    long long value = PyLong_AsLongLongAndOverflow(seed_obj, &overflow);
    if (value == -1 && PyErr_Occurred()) {
        return NULL;
    }
    if (overflow != 0 || value < 0 || value > 0xFFFFFFFFLL) {
        PyErr_SetString(PyExc_ValueError,
            "seed must be in [0, 4294967295] (an unsigned 32-bit integer)");
        return NULL;
    }

    mcrf::EngineRandom::setSeed(static_cast<uint32_t>(value));
    Py_RETURN_NONE;
}

PyObject* McRFPy_API::_getRandomSeed(PyObject* self, PyObject* args) {
    // seed() materialises and records a seed if none was set, so this always
    // reports the number actually in use -- never a placeholder, never None.
    return PyLong_FromUnsignedLong(mcrf::EngineRandom::seed());
}

PyObject* McRFPy_API::_getMetrics(PyObject* self, PyObject* args) {
    // Create a dictionary with metrics
    PyObject* dict = PyDict_New();
    if (!dict) return NULL;
    bool ok = true;  // #413: dict_steal() owns each value

    // Add frame time metrics
    ok &= mcrf::dict_steal(dict, "frame_time", PyFloat_FromDouble(game->metrics.frameTime)) == 0;
    ok &= mcrf::dict_steal(dict, "avg_frame_time", PyFloat_FromDouble(game->metrics.avgFrameTime)) == 0;
    ok &= mcrf::dict_steal(dict, "fps", PyLong_FromLong(game->metrics.fps)) == 0;

    // #341: report the last COMPLETED frame's per-frame values, not the live
    // accumulators. Python callbacks run before render(), and the accumulators are
    // zeroed at the top of the frame -- so reading them live always returned 0.
    const auto& pub = game->metrics.published;

    // Add draw call metrics
    ok &= mcrf::dict_steal(dict, "draw_calls", PyLong_FromLong(pub.drawCalls)) == 0;
    ok &= mcrf::dict_steal(dict, "ui_elements", PyLong_FromLong(pub.uiElements)) == 0;
    ok &= mcrf::dict_steal(dict, "visible_elements", PyLong_FromLong(pub.visibleElements)) == 0;

    // #144 - Add detailed timing breakdown (in milliseconds)
    ok &= mcrf::dict_steal(dict, "grid_render_time", PyFloat_FromDouble(pub.gridRenderTime)) == 0;
    ok &= mcrf::dict_steal(dict, "entity_render_time", PyFloat_FromDouble(pub.entityRenderTime)) == 0;
    ok &= mcrf::dict_steal(dict, "fov_overlay_time", PyFloat_FromDouble(pub.fovOverlayTime)) == 0;
    ok &= mcrf::dict_steal(dict, "python_time", PyFloat_FromDouble(pub.pythonScriptTime)) == 0;
    ok &= mcrf::dict_steal(dict, "animation_time", PyFloat_FromDouble(pub.animationTime)) == 0;

    // #144 - Add grid-specific metrics
    ok &= mcrf::dict_steal(dict, "grid_cells_rendered", PyLong_FromLong(pub.gridCellsRendered)) == 0;
    ok &= mcrf::dict_steal(dict, "entities_rendered", PyLong_FromLong(pub.entitiesRendered)) == 0;
    ok &= mcrf::dict_steal(dict, "total_entities", PyLong_FromLong(pub.totalEntities)) == 0;

    // Add general metrics
    ok &= mcrf::dict_steal(dict, "current_frame", PyLong_FromLong(game->getFrame())) == 0;
    ok &= mcrf::dict_steal(dict, "runtime", PyFloat_FromDouble(game->runtime.getElapsedTime().asSeconds())) == 0;

    // #396 - The SIMULATION clock, in integer milliseconds. The _ms suffix is deliberate:
    // the sibling "runtime" key is float SECONDS, and mistaking one for the other is the
    // exact confusion this key exists to end. The two are different clocks, not different
    // units of one -- runtime is wall clock and keeps ticking while a headless script
    // thinks about its next move; simulation_time_ms is the
    // deterministic counter that only step()/advance() move, and the one timers run on in
    // headless mode. Exposed here rather than as a parallel API so there is one place to
    // ask the engine what time it is.
    ok &= mcrf::dict_steal(dict, "simulation_time_ms", PyLong_FromLong(game->getSimulationTime())) == 0;
    // #440: Sound/Music objects alive, and how many of them playback is keeping alive.
    ok &= mcrf::dict_steal(dict, "audio_sources", PyLong_FromSize_t(mcrf::audio::live_count())) == 0;
    ok &= mcrf::dict_steal(dict, "audio_playing", PyLong_FromSize_t(mcrf::audio::retained_count())) == 0;

    if (!ok) {
        Py_DECREF(dict);
        return NULL;
    }
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
    if (PyObject_IsInstance(obj, (PyObject*)&mcrfpydef::PyVectorType)) {
        PyVectorObject* vec = (PyVectorObject*)obj;
        *x = static_cast<int>(vec->data.x);
        *y = static_cast<int>(vec->data.y);
        return true;
    }

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
