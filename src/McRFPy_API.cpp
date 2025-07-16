#include "McRFPy_API.h"
#include "McRFPy_Automation.h"
#include "McRFPy_Libtcod.h"
#include "platform.h"
#include "PyAnimation.h"
#include "PyDrawable.h"
#include "PyTimer.h"
#include "PyWindow.h"
#include "PySceneObject.h"
#include "GameEngine.h"
#include "UI.h"
#include "Resources.h"
#include "PyScene.h"
#include <filesystem>
#include <cstring>
#include <libtcod.h>

std::vector<sf::SoundBuffer>* McRFPy_API::soundbuffers = nullptr;
sf::Music* McRFPy_API::music = nullptr;
sf::Sound* McRFPy_API::sfx = nullptr;

std::shared_ptr<PyFont> McRFPy_API::default_font;
std::shared_ptr<PyTexture> McRFPy_API::default_texture;
PyObject* McRFPy_API::mcrf_module;


static PyMethodDef mcrfpyMethods[] = {

    {"createSoundBuffer", McRFPy_API::_createSoundBuffer, METH_VARARGS,
     "createSoundBuffer(filename: str) -> int\n\n"
     "Load a sound effect from a file and return its buffer ID.\n\n"
     "Args:\n"
     "    filename: Path to the sound file (WAV, OGG, FLAC)\n\n"
     "Returns:\n"
     "    int: Buffer ID for use with playSound()\n\n"
     "Raises:\n"
     "    RuntimeError: If the file cannot be loaded"},
	{"loadMusic", McRFPy_API::_loadMusic, METH_VARARGS,
	 "loadMusic(filename: str) -> None\n\n"
	 "Load and immediately play background music from a file.\n\n"
	 "Args:\n"
	 "    filename: Path to the music file (WAV, OGG, FLAC)\n\n"
	 "Note:\n"
	 "    Only one music track can play at a time. Loading new music stops the current track."},
	{"setMusicVolume", McRFPy_API::_setMusicVolume, METH_VARARGS,
	 "setMusicVolume(volume: int) -> None\n\n"
	 "Set the global music volume.\n\n"
	 "Args:\n"
	 "    volume: Volume level from 0 (silent) to 100 (full volume)"},
	{"setSoundVolume", McRFPy_API::_setSoundVolume, METH_VARARGS,
	 "setSoundVolume(volume: int) -> None\n\n"
	 "Set the global sound effects volume.\n\n"
	 "Args:\n"
	 "    volume: Volume level from 0 (silent) to 100 (full volume)"},
	{"playSound", McRFPy_API::_playSound, METH_VARARGS,
	 "playSound(buffer_id: int) -> None\n\n"
	 "Play a sound effect using a previously loaded buffer.\n\n"
	 "Args:\n"
	 "    buffer_id: Sound buffer ID returned by createSoundBuffer()\n\n"
	 "Raises:\n"
	 "    RuntimeError: If the buffer ID is invalid"},
	{"getMusicVolume", McRFPy_API::_getMusicVolume, METH_NOARGS,
	 "getMusicVolume() -> int\n\n"
	 "Get the current music volume level.\n\n"
	 "Returns:\n"
	 "    int: Current volume (0-100)"},
	{"getSoundVolume", McRFPy_API::_getSoundVolume, METH_NOARGS,
	 "getSoundVolume() -> int\n\n"
	 "Get the current sound effects volume level.\n\n"
	 "Returns:\n"
	 "    int: Current volume (0-100)"},

    {"sceneUI", McRFPy_API::_sceneUI, METH_VARARGS,
     "sceneUI(scene: str = None) -> list\n\n"
     "Get all UI elements for a scene.\n\n"
     "Args:\n"
     "    scene: Scene name. If None, uses current scene\n\n"
     "Returns:\n"
     "    list: All UI elements (Frame, Caption, Sprite, Grid) in the scene\n\n"
     "Raises:\n"
     "    KeyError: If the specified scene doesn't exist"},

    {"currentScene", McRFPy_API::_currentScene, METH_NOARGS,
     "currentScene() -> str\n\n"
     "Get the name of the currently active scene.\n\n"
     "Returns:\n"
     "    str: Name of the current scene"},
    {"setScene", McRFPy_API::_setScene, METH_VARARGS,
     "setScene(scene: str, transition: str = None, duration: float = 0.0) -> None\n\n"
     "Switch to a different scene with optional transition effect.\n\n"
     "Args:\n"
     "    scene: Name of the scene to switch to\n"
     "    transition: Transition type ('fade', 'slide_left', 'slide_right', 'slide_up', 'slide_down')\n"
     "    duration: Transition duration in seconds (default: 0.0 for instant)\n\n"
     "Raises:\n"
     "    KeyError: If the scene doesn't exist\n"
     "    ValueError: If the transition type is invalid"},
    {"createScene", McRFPy_API::_createScene, METH_VARARGS,
     "createScene(name: str) -> None\n\n"
     "Create a new empty scene.\n\n"
     "Args:\n"
     "    name: Unique name for the new scene\n\n"
     "Raises:\n"
     "    ValueError: If a scene with this name already exists\n\n"
     "Note:\n"
     "    The scene is created but not made active. Use setScene() to switch to it."},
    {"keypressScene", McRFPy_API::_keypressScene, METH_VARARGS,
     "keypressScene(handler: callable) -> None\n\n"
     "Set the keyboard event handler for the current scene.\n\n"
     "Args:\n"
     "    handler: Callable that receives (key_name: str, is_pressed: bool)\n\n"
     "Example:\n"
     "    def on_key(key, pressed):\n"
     "        if key == 'A' and pressed:\n"
     "            print('A key pressed')\n"
     "    mcrfpy.keypressScene(on_key)"},

    {"setTimer", McRFPy_API::_setTimer, METH_VARARGS,
     "setTimer(name: str, handler: callable, interval: int) -> None\n\n"
     "Create or update a recurring timer.\n\n"
     "Args:\n"
     "    name: Unique identifier for the timer\n"
     "    handler: Function called with (runtime: float) parameter\n"
     "    interval: Time between calls in milliseconds\n\n"
     "Note:\n"
     "    If a timer with this name exists, it will be replaced.\n"
     "    The handler receives the total runtime in seconds as its argument."},
    {"delTimer", McRFPy_API::_delTimer, METH_VARARGS,
     "delTimer(name: str) -> None\n\n"
     "Stop and remove a timer.\n\n"
     "Args:\n"
     "    name: Timer identifier to remove\n\n"
     "Note:\n"
     "    No error is raised if the timer doesn't exist."}, 
    {"exit", McRFPy_API::_exit, METH_NOARGS,
     "exit() -> None\n\n"
     "Cleanly shut down the game engine and exit the application.\n\n"
     "Note:\n"
     "    This immediately closes the window and terminates the program."},
    {"setScale", McRFPy_API::_setScale, METH_VARARGS,
     "setScale(multiplier: float) -> None\n\n"
     "Scale the game window size.\n\n"
     "Args:\n"
     "    multiplier: Scale factor (e.g., 2.0 for double size)\n\n"
     "Note:\n"
     "    The internal resolution remains 1024x768, but the window is scaled.\n"
     "    This is deprecated - use Window.resolution instead."},
    
    {"find", McRFPy_API::_find, METH_VARARGS,
     "find(name: str, scene: str = None) -> UIDrawable | None\n\n"
     "Find the first UI element with the specified name.\n\n"
     "Args:\n"
     "    name: Exact name to search for\n"
     "    scene: Scene to search in (default: current scene)\n\n"
     "Returns:\n"
     "    Frame, Caption, Sprite, Grid, or Entity if found; None otherwise\n\n"
     "Note:\n"
     "    Searches scene UI elements and entities within grids."},
    {"findAll", McRFPy_API::_findAll, METH_VARARGS,
     "findAll(pattern: str, scene: str = None) -> list\n\n"
     "Find all UI elements matching a name pattern.\n\n"
     "Args:\n"
     "    pattern: Name pattern with optional wildcards (* matches any characters)\n"
     "    scene: Scene to search in (default: current scene)\n\n"
     "Returns:\n"
     "    list: All matching UI elements and entities\n\n"
     "Example:\n"
     "    findAll('enemy*')  # Find all elements starting with 'enemy'\n"
     "    findAll('*_button')  # Find all elements ending with '_button'"},
    
    {"getMetrics", McRFPy_API::_getMetrics, METH_NOARGS,
     "getMetrics() -> dict\n\n"
     "Get current performance metrics.\n\n"
     "Returns:\n"
     "    dict: Performance data with keys:\n"
     "        - frame_time: Last frame duration in seconds\n"
     "        - avg_frame_time: Average frame time\n"
     "        - fps: Frames per second\n"
     "        - draw_calls: Number of draw calls\n"
     "        - ui_elements: Total UI element count\n"
     "        - visible_elements: Visible element count\n"
     "        - current_frame: Frame counter\n"
     "        - runtime: Total runtime in seconds"},
    
    {NULL, NULL, 0, NULL}
};

static PyModuleDef mcrfpyModule = {
    PyModuleDef_HEAD_INIT, /* m_base - Always initialize this member to PyModuleDef_HEAD_INIT. */
    "mcrfpy",              /* m_name */
    PyDoc_STR("McRogueFace Python API\\n\\n"
              "Core game engine interface for creating roguelike games with Python.\\n\\n"
              "This module provides:\\n"
              "- Scene management (createScene, setScene, currentScene)\\n"
              "- UI components (Frame, Caption, Sprite, Grid)\\n"
              "- Entity system for game objects\\n"
              "- Audio playback (sound effects and music)\\n"
              "- Timer system for scheduled events\\n"
              "- Input handling\\n"
              "- Performance metrics\\n\\n"
              "Example:\\n"
              "    import mcrfpy\\n"
              "    \\n"
              "    # Create a new scene\\n"
              "    mcrfpy.createScene('game')\\n"
              "    mcrfpy.setScene('game')\\n"
              "    \\n"
              "    # Add UI elements\\n"
              "    frame = mcrfpy.Frame(10, 10, 200, 100)\\n"
              "    caption = mcrfpy.Caption('Hello World', 50, 50)\\n"
              "    mcrfpy.sceneUI().extend([frame, caption])\\n"),
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
    
    using namespace mcrfpydef;
    PyTypeObject* pytypes[] = {
        /*SFML exposed types*/
        &PyColorType, /*&PyLinkedColorType,*/ &PyFontType, &PyTextureType, &PyVectorType,

        /*Base classes*/
        &PyDrawableType,

        /*UI widgets*/
        &PyUICaptionType, &PyUISpriteType, &PyUIFrameType, &PyUIEntityType, &PyUIGridType,

        /*game map & perspective data*/
        &PyUIGridPointType, &PyUIGridPointStateType,

        /*collections & iterators*/
        &PyUICollectionType, &PyUICollectionIterType,
        &PyUIEntityCollectionType, &PyUIEntityCollectionIterType,
        
        /*animation*/
        &PyAnimationType,
        
        /*timer*/
        &PyTimerType,
        
        /*window singleton*/
        &PyWindowType,
        
        /*scene class*/
        &PySceneType,
        
        nullptr};
    
    // Set up PyWindowType methods and getsetters before PyType_Ready
    PyWindowType.tp_methods = PyWindow::methods;
    PyWindowType.tp_getset = PyWindow::getsetters;
    
    // Set up PySceneType methods and getsetters
    PySceneType.tp_methods = PySceneClass::methods;
    PySceneType.tp_getset = PySceneClass::getsetters;
    
    // Set up weakref support for all types that need it
    PyTimerType.tp_weaklistoffset = offsetof(PyTimerObject, weakreflist);
    PyUIFrameType.tp_weaklistoffset = offsetof(PyUIFrameObject, weakreflist);
    PyUICaptionType.tp_weaklistoffset = offsetof(PyUICaptionObject, weakreflist);
    PyUISpriteType.tp_weaklistoffset = offsetof(PyUISpriteObject, weakreflist);
    PyUIGridType.tp_weaklistoffset = offsetof(PyUIGridObject, weakreflist);
    PyUIEntityType.tp_weaklistoffset = offsetof(PyUIEntityObject, weakreflist);
    
    int i = 0;
    auto t = pytypes[i];
    while (t != nullptr)
    {
        //std::cout << "Registering type: " << t->tp_name << std::endl;
        if (PyType_Ready(t) < 0) {
            std::cout << "ERROR: PyType_Ready failed for " << t->tp_name << std::endl;
            return NULL;
        }
        //std::cout << "  tp_alloc after PyType_Ready: " << (void*)t->tp_alloc << std::endl;
        PyModule_AddType(m, t);
        i++;
        t = pytypes[i];
    }

    // Add default_font and default_texture to module
    McRFPy_API::default_font = std::make_shared<PyFont>("assets/JetbrainsMono.ttf");
    McRFPy_API::default_texture = std::make_shared<PyTexture>("assets/kenney_tinydungeon.png", 16, 16);
    // These will be set later when the window is created
    PyModule_AddObject(m, "default_font", Py_None);
    PyModule_AddObject(m, "default_texture", Py_None);
    
    // Add TCOD FOV algorithm constants
    PyModule_AddIntConstant(m, "FOV_BASIC", FOV_BASIC);
    PyModule_AddIntConstant(m, "FOV_DIAMOND", FOV_DIAMOND);
    PyModule_AddIntConstant(m, "FOV_SHADOW", FOV_SHADOW);
    PyModule_AddIntConstant(m, "FOV_PERMISSIVE_0", FOV_PERMISSIVE_0);
    PyModule_AddIntConstant(m, "FOV_PERMISSIVE_1", FOV_PERMISSIVE_1);
    PyModule_AddIntConstant(m, "FOV_PERMISSIVE_2", FOV_PERMISSIVE_2);
    PyModule_AddIntConstant(m, "FOV_PERMISSIVE_3", FOV_PERMISSIVE_3);
    PyModule_AddIntConstant(m, "FOV_PERMISSIVE_4", FOV_PERMISSIVE_4);
    PyModule_AddIntConstant(m, "FOV_PERMISSIVE_5", FOV_PERMISSIVE_5);
    PyModule_AddIntConstant(m, "FOV_PERMISSIVE_6", FOV_PERMISSIVE_6);
    PyModule_AddIntConstant(m, "FOV_PERMISSIVE_7", FOV_PERMISSIVE_7);
    PyModule_AddIntConstant(m, "FOV_PERMISSIVE_8", FOV_PERMISSIVE_8);
    PyModule_AddIntConstant(m, "FOV_RESTRICTIVE", FOV_RESTRICTIVE);
    
    // Add automation submodule
    PyObject* automation_module = McRFPy_Automation::init_automation_module();
    if (automation_module != NULL) {
        PyModule_AddObject(m, "automation", automation_module);
        
        // Also add to sys.modules for proper import behavior
        PyObject* sys_modules = PyImport_GetModuleDict();
        PyDict_SetItemString(sys_modules, "mcrfpy.automation", automation_module);
    }
    
    // Add libtcod submodule
    PyObject* libtcod_module = McRFPy_Libtcod::init_libtcod_module();
    if (libtcod_module != NULL) {
        PyModule_AddObject(m, "libtcod", libtcod_module);
        
        // Also add to sys.modules for proper import behavior
        PyObject* sys_modules = PyImport_GetModuleDict();
        PyDict_SetItemString(sys_modules, "mcrfpy.libtcod", libtcod_module);
    }
    
    //McRFPy_API::mcrf_module = m;
    return m;
}

// init_python - configure interpreter details here
PyStatus init_python(const char *program_name)
{
    PyStatus status;

	//**preconfig to establish locale**
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

	PyConfig_SetBytesString(&config, &config.home, 
        narrow_string(executable_path() + L"/lib/Python").c_str());

    status = PyConfig_SetBytesString(&config, &config.program_name,
                                     program_name);

    // under Windows, the search paths are correct; under Linux, they need manual insertion
#if __PLATFORM_SET_PYTHON_SEARCH_PATHS == 1
    config.module_search_paths_set = 1;
	
	// search paths for python libs/modules/scripts
    const wchar_t* str_arr[] = {
        L"/scripts",
        L"/lib/Python/lib.linux-x86_64-3.12",
	    L"/lib/Python",
        L"/lib/Python/Lib",
        L"/venv/lib/python3.12/site-packages"
    };
    

    for(auto s : str_arr) {
        status = PyWideStringList_Append(&config.module_search_paths, (executable_path() + s).c_str());
        if (PyStatus_Exception(status)) {
            continue;
        }
    }
#endif

    status = Py_InitializeFromConfig(&config);

    PyConfig_Clear(&config);

    return status;
}

PyStatus McRFPy_API::init_python_with_config(const McRogueFaceConfig& config, int argc, char** argv)
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
    
    // CRITICAL: Pass actual command line arguments to Python
    status = PyConfig_SetBytesArgv(&pyconfig, argc, argv);
    if (PyStatus_Exception(status)) {
        return status;
    }
    
    // Check if we're in a virtual environment
    auto exe_path = std::filesystem::path(argv[0]);
    auto exe_dir = exe_path.parent_path();
    auto venv_root = exe_dir.parent_path();
    
    if (std::filesystem::exists(venv_root / "pyvenv.cfg")) {
        // We're running from within a venv!
        // Add venv's site-packages to module search paths
        auto site_packages = venv_root / "lib" / "python3.12" / "site-packages";
        PyWideStringList_Append(&pyconfig.module_search_paths,
                               site_packages.wstring().c_str());
        pyconfig.module_search_paths_set = 1;
    }
    
    // Set Python home to our bundled Python
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
        L"/lib/Python/lib.linux-x86_64-3.12",
        L"/lib/Python",
        L"/lib/Python/Lib",
        L"/venv/lib/python3.12/site-packages"
    };
    
    for(auto s : str_arr) {
        status = PyWideStringList_Append(&pyconfig.module_search_paths, (executable_path() + s).c_str());
        if (PyStatus_Exception(status)) {
            continue;
        }
    }
#endif
    
    // Register mcrfpy module before initialization
    if (!Py_IsInitialized()) {
        PyImport_AppendInittab("mcrfpy", &PyInit_mcrfpy);
    }
    
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

void McRFPy_API::api_init(const McRogueFaceConfig& config, int argc, char** argv) {
    // Initialize Python with proper argv - this is CRITICAL
    PyStatus status = init_python_with_config(config, argc, argv);
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
    
    FILE* PScriptFile = fopen(script_path.string().c_str(), "r");
    if(PScriptFile) {
        PyRun_SimpleFile(PScriptFile, script_path.string().c_str());
        fclose(PScriptFile);
    } else {
        std::cout << "Failed to open script: " << script_path.string() << std::endl;
    }
}

void McRFPy_API::api_shutdown()
{
    // Clean up audio resources in correct order
    if (sfx) {
        sfx->stop();
        delete sfx;
        sfx = nullptr;
    }
    if (music) {
        music->stop();
        delete music;
        music = nullptr;
    }
    if (soundbuffers) {
        soundbuffers->clear();
        delete soundbuffers;
        soundbuffers = nullptr;
    }
    
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

PyObject* McRFPy_API::_createSoundBuffer(PyObject* self, PyObject* args) {
	const char *fn_cstr;
	if (!PyArg_ParseTuple(args, "s", &fn_cstr)) return NULL;
	// Initialize soundbuffers if needed
	if (!McRFPy_API::soundbuffers) {
		McRFPy_API::soundbuffers = new std::vector<sf::SoundBuffer>();
	}
	auto b = sf::SoundBuffer();
	b.loadFromFile(fn_cstr);
	McRFPy_API::soundbuffers->push_back(b);
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* McRFPy_API::_loadMusic(PyObject* self, PyObject* args) {
	const char *fn_cstr;
	PyObject* loop_obj = Py_False;
	if (!PyArg_ParseTuple(args, "s|O", &fn_cstr, &loop_obj)) return NULL;
	// Initialize music if needed
	if (!McRFPy_API::music) {
		McRFPy_API::music = new sf::Music();
	}
	McRFPy_API::music->stop();
	McRFPy_API::music->openFromFile(fn_cstr);
	McRFPy_API::music->setLoop(PyObject_IsTrue(loop_obj));
	McRFPy_API::music->play();
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* McRFPy_API::_setMusicVolume(PyObject* self, PyObject* args) {
	int vol;
	if (!PyArg_ParseTuple(args, "i", &vol)) return NULL;
	if (!McRFPy_API::music) {
		McRFPy_API::music = new sf::Music();
	}
	McRFPy_API::music->setVolume(vol);
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* McRFPy_API::_setSoundVolume(PyObject* self, PyObject* args) {
	float vol;
	if (!PyArg_ParseTuple(args, "f", &vol)) return NULL;
	if (!McRFPy_API::sfx) {
		McRFPy_API::sfx = new sf::Sound();
	}
	McRFPy_API::sfx->setVolume(vol);
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* McRFPy_API::_playSound(PyObject* self, PyObject* args) {
	float index;
	if (!PyArg_ParseTuple(args, "f", &index)) return NULL;
	if (!McRFPy_API::soundbuffers || index >= McRFPy_API::soundbuffers->size()) return NULL;
	if (!McRFPy_API::sfx) {
		McRFPy_API::sfx = new sf::Sound();
	}
	McRFPy_API::sfx->stop();
	McRFPy_API::sfx->setBuffer((*McRFPy_API::soundbuffers)[index]);
	McRFPy_API::sfx->play();
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* McRFPy_API::_getMusicVolume(PyObject* self, PyObject* args) {
	if (!McRFPy_API::music) {
		return Py_BuildValue("f", 0.0f);
	}
	return Py_BuildValue("f", McRFPy_API::music->getVolume());
}

PyObject* McRFPy_API::_getSoundVolume(PyObject* self, PyObject* args) {
	if (!McRFPy_API::sfx) {
		return Py_BuildValue("f", 0.0f);
	}
	return Py_BuildValue("f", McRFPy_API::sfx->getVolume());
}

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

//McRFPy_API::_sceneUI
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
        if (o)
            o->data = ui;
        return (PyObject*)o;
}

PyObject* McRFPy_API::_currentScene(PyObject* self, PyObject* args) {
	return Py_BuildValue("s", game->scene.c_str());
}

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

PyObject* McRFPy_API::_createScene(PyObject* self, PyObject* args) {
	const char* newscene;
	if (!PyArg_ParseTuple(args, "s", &newscene)) return NULL;
	game->createScene(newscene);
    Py_INCREF(Py_None);
    return Py_None;		
}

PyObject* McRFPy_API::_keypressScene(PyObject* self, PyObject* args) {
    PyObject* callable;
	if (!PyArg_ParseTuple(args, "O", &callable)) return NULL;
    
    // Validate that the argument is callable
    if (!PyCallable_Check(callable)) {
        PyErr_SetString(PyExc_TypeError, "keypressScene() argument must be callable");
        return NULL;
    }
    
    /*
    if (game->currentScene()->key_callable != NULL and game->currentScene()->key_callable != Py_None)
    {
        Py_DECREF(game->currentScene()->key_callable);
    }
    Py_INCREF(callable);
    game->currentScene()->key_callable = callable;
    Py_INCREF(Py_None);
    */
    game->currentScene()->key_callable = std::make_unique<PyKeyCallable>(callable);
    Py_INCREF(Py_None);
    return Py_None;		
}

PyObject* McRFPy_API::_setTimer(PyObject* self, PyObject* args) { // TODO - compare with UIDrawable mouse & Scene Keyboard methods - inconsistent responsibility for incref/decref around mcrogueface
    const char* name;
    PyObject* callable;
    int interval;
	if (!PyArg_ParseTuple(args, "sOi", &name, &callable, &interval)) return NULL;
    game->manageTimer(name, callable, interval);
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* McRFPy_API::_delTimer(PyObject* self, PyObject* args) {
	const char* name;
	if (!PyArg_ParseTuple(args, "s", &name)) return NULL;
    game->manageTimer(name, NULL, 0);
    Py_INCREF(Py_None);
    return Py_None;
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
    
    // Add general metrics
    PyDict_SetItemString(dict, "current_frame", PyLong_FromLong(game->getFrame()));
    PyDict_SetItemString(dict, "runtime", PyFloat_FromDouble(game->runtime.getElapsedTime().asSeconds()));
    
    return dict;
}
