#pragma once
#include "Common.h"
#include "Python.h"
#include <list>
#include <atomic>

#include "PyFont.h"
#include "PyTexture.h"
#include "McRogueFaceConfig.h"

class GameEngine; // forward declared (circular members)

class McRFPy_API
{
private:
    static const int texture_size = 16, // w & h (pixels) of one sprite in the tex
        texture_width = 12, texture_height = 11, // w & h sprite/frame count
        texture_sprite_count = 11 * 12; // t_width * t_height, minus blanks?

    McRFPy_API();


public:
    static PyObject* mcrf_module;
    static std::shared_ptr<PyFont> default_font;
    static std::shared_ptr<PyTexture> default_texture;
    // The default font, loaded on first use (#451).
    static std::shared_ptr<PyFont> defaultFont();
    // The default texture, loaded on first use (#451). nullptr with RuntimeError set when
    // there is no display to create it on.
    static std::shared_ptr<PyTexture> defaultTexture();
    // mcrfpy.TextureWarning (a UserWarning): developer education about which texture
    // a grid draws with (#453, #454). Switched off with the warnings module.
    static PyObject* texture_warning;
    //inline static sf::Sprite sprite;
    //inline static sf::Texture texture;
    //static void setSpriteTexture(int);
    inline static GameEngine* game;
    // Game path (no script/command): the config carries the interpreter flags (#505).
    static void api_init_game(const McRogueFaceConfig& config);
    static void api_init(const McRogueFaceConfig& config);
    static PyStatus init_python_with_config(const McRogueFaceConfig& config);
    static void api_shutdown();
    // #468: release every Python reference the engine holds -- scenes and their trees,
    // the scene registry, timers, animations, audio, the default font/texture, the
    // enum classes and other module statics -- while the interpreter is still whole.
    // Runs once, as the first-registered (so last-run) atexit callback, which every
    // exit path reaches: api_shutdown()'s Py_Finalize, and sys.exit(), which finalizes
    // inside PyErr_Print() without returning to main(). Finalization runs it after
    // joining non-daemon threads and before it clears anything. The engine runs no
    // frame afterwards.
    static void release_python_references();
    // Python API functionality - use mcrfpy.* in scripts
    //static PyObject* _drawSprite(PyObject*, PyObject*);
    static void REPL_device(FILE * fp, const char *filename);
    static void REPL();

    // Internal - used by PySceneClass_get_children()
    static PyObject* _sceneUI(PyObject*, PyObject*);

    // Internal - used by PySceneObject::activate()
    static PyObject* _setScene(PyObject*, PyObject*);

    // Note: setTimer/delTimer removed in #173 - use Timer objects instead

    // #153 - Headless simulation control
    static PyObject* _step(PyObject*, PyObject*);
    static PyObject* _advance(PyObject*, PyObject*);

    static PyObject* _exit(PyObject*, PyObject*);
    static PyObject* _setScale(PyObject*, PyObject*);

    // accept keyboard input from scene
    static sf::Vector2i cursor_position;
    

    // main_script: this is the program (game.py), so its directory becomes sys.path[0] (#452).
    static void executeScript(std::string, bool main_script = false);
    // Puts the main script's directory at sys.path[0], in place of <exe dir>/scripts, the
    // way `python dir/script.py` does (#452). Returns -1 with an exception set on failure.
    static int setMainScriptDir(const std::string& script_path);
    // Runs a script's source in __main__ with its real path as the code's filename (#422),
    // so tracebacks, linecache and profilers name the file. Same result and error handling
    // as PyRun_SimpleString: 0 on success, -1 after printing the error.
    static int runScriptSource(const std::string& source, const std::string& path);
    static void executePyString(std::string);
    
    // Helper to mark scenes as needing z_index resort
    static void markSceneNeedsSort();
    
    // Name-based finding methods
    static PyObject* _find(PyObject*, PyObject*);
    static PyObject* _findAll(PyObject*, PyObject*);
    
    // Profiling/metrics
    static PyObject* _getMetrics(PyObject*, PyObject*);

    // Engine-internal RNG seeding (#394)
    static PyObject* _setRandomSeed(PyObject*, PyObject*);
    static PyObject* _getRandomSeed(PyObject*, PyObject*);

    // Benchmark logging (#104)
    static PyObject* _startBenchmark(PyObject*, PyObject*);
    static PyObject* _endBenchmark(PyObject*, PyObject*);
    static PyObject* _logBenchmark(PyObject*, PyObject*);

    // Developer console
    static PyObject* _setDevConsole(PyObject*, PyObject*);

    // #215: Bresenham line algorithm (replaces mcrfpy.libtcod.line)
    static PyObject* _bresenham(PyObject*, PyObject*, PyObject*);

    // Scene lifecycle management for Python Scene objects
    static void triggerSceneChange(const std::string& from_scene, const std::string& to_scene);
    static void updatePythonScenes(float dt);
    static void triggerResize(sf::Vector2u new_size);
    static void triggerKeyEvent(const std::string& key, const std::string& action);
    static void triggerTextEvent(const std::string& utf8);  // #495

    // #151: Module-level scene property accessors
    static PyObject* api_get_current_scene();
    static int api_set_current_scene(PyObject* value);
    static PyObject* api_get_scenes();

    // #173: Module-level timer collection accessor
    static PyObject* api_get_timers();

    // Module-level animation collection accessor
    static PyObject* api_get_animations();

    // Exception handling - signal game loop to exit on unhandled Python exceptions
    static std::atomic<bool> exception_occurred;
    static std::atomic<int> exit_code;

    // #557: a SystemExit raised by a callback inside a frame is recorded here instead of
    // finalizing the interpreter under the frame. The frame code stops dispatching
    // callbacks (exitPending()), unwinds, and the exit happens at the top:
    // raisePendingExit() re-raises it, and PyErr_Print() (or the script's own top level)
    // exits with the code a top-level sys.exit() would give. GIL-protected.
    static bool deferSystemExit();   // true if the pending error was a SystemExit taken (or dropped)
    static bool exitPending();
    static void raisePendingExit();  // sets the recorded SystemExit as the current error
    // For a binding that dispatches callbacks synchronously for its Python caller
    // (Grid.step(), Scene.activate(), the current_scene setter, the Scene constructor, the
    // automation.* event injectors): call it FIRST (an exit already requested is raised before
    // the binding does anything) and again before returning (one the dispatch asked for comes
    // out of the call into the caller's own code like any raise). If it returns true, set the
    // error and the binding returns NULL / -1. On a thread that does not own the clock it
    // returns false and the exit stays pending for the owner.
    static bool propagatePendingExit();
    // #556: keep the frame-lock close hook the first threading-atexit hook to run. Called by
    // a thread about to wait in mcrfpy.lock(), because later registrations (a
    // ThreadPoolExecutor's) land after ours and would run before it. 0, or -1 with an error set.
    static int keepShutdownHookFirst();

    static void signalPythonException();  // Called by exception handlers
    static bool shouldExit();             // Checked by game loop
};
