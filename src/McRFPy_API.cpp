#include "McRFPy_API.h"
#include "McRFPy_Automation.h"
#include "platform.h"
#include "PyAnimation.h"
#include "GameEngine.h"
#include "UI.h"
#include "Resources.h"
#include "PyScene.h"
#include <filesystem>
#include <cstring>

std::vector<sf::SoundBuffer> McRFPy_API::soundbuffers;
sf::Music McRFPy_API::music;
sf::Sound McRFPy_API::sfx;

std::shared_ptr<PyFont> McRFPy_API::default_font;
std::shared_ptr<PyTexture> McRFPy_API::default_texture;
PyObject* McRFPy_API::mcrf_module;


static PyMethodDef mcrfpyMethods[] = {

    {"createSoundBuffer", McRFPy_API::_createSoundBuffer, METH_VARARGS, "(filename)"},
	{"loadMusic", McRFPy_API::_loadMusic, METH_VARARGS, "(filename)"},
	{"setMusicVolume", McRFPy_API::_setMusicVolume, METH_VARARGS, "(int)"},
	{"setSoundVolume", McRFPy_API::_setSoundVolume, METH_VARARGS, "(int)"},
	{"playSound", McRFPy_API::_playSound, METH_VARARGS, "(int)"},
	{"getMusicVolume", McRFPy_API::_getMusicVolume, METH_VARARGS, ""},
	{"getSoundVolume", McRFPy_API::_getSoundVolume, METH_VARARGS, ""},

    {"sceneUI", McRFPy_API::_sceneUI, METH_VARARGS, "sceneUI(scene) - Returns a list of UI elements"},

    {"currentScene", McRFPy_API::_currentScene, METH_VARARGS, "currentScene() - Current scene's name. Returns a string"},
    {"setScene", McRFPy_API::_setScene, METH_VARARGS, "setScene(scene) - transition to a different scene"},
    {"createScene", McRFPy_API::_createScene, METH_VARARGS, "createScene(scene) - create a new blank scene with given name"},
    {"keypressScene", McRFPy_API::_keypressScene, METH_VARARGS, "keypressScene(callable) - assign a callable object to the current scene receive keypress events"},

    {"setTimer", McRFPy_API::_setTimer, METH_VARARGS, "setTimer(name:str, callable:object, interval:int) - callable will be called with args (runtime:float) every `interval` milliseconds"},
    {"delTimer", McRFPy_API::_delTimer, METH_VARARGS, "delTimer(name:str) - stop calling the timer labelled with `name`"},
    {"exit", McRFPy_API::_exit, METH_VARARGS, "exit() - close down the game engine"},
    {"setScale", McRFPy_API::_setScale, METH_VARARGS, "setScale(multiplier:float) - resize the window (still 1024x768, but bigger)"},
    {NULL, NULL, 0, NULL}
};

static PyModuleDef mcrfpyModule = {
    PyModuleDef_HEAD_INIT, /* m_base - Always initialize this member to PyModuleDef_HEAD_INIT. */
    "mcrfpy",              /* m_name */
    NULL,                  /* m_doc - Docstring for the module; usually a docstring variable created with PyDoc_STRVAR is used. */
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

        /*UI widgets*/
        &PyUICaptionType, &PyUISpriteType, &PyUIFrameType, &PyUIEntityType, &PyUIGridType,

        /*game map & perspective data*/
        &PyUIGridPointType, &PyUIGridPointStateType,

        /*collections & iterators*/
        &PyUICollectionType, &PyUICollectionIterType,
        &PyUIEntityCollectionType, &PyUIEntityCollectionIterType,
        
        /*animation*/
        &PyAnimationType,
        nullptr};
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
    //PyModule_AddObject(m, "default_font", McRFPy_API::default_font->pyObject());
    //PyModule_AddObject(m, "default_texture", McRFPy_API::default_texture->pyObject());
    PyModule_AddObject(m, "default_font", Py_None);
    PyModule_AddObject(m, "default_texture", Py_None);
    
    // Add automation submodule
    PyObject* automation_module = McRFPy_Automation::init_automation_module();
    if (automation_module != NULL) {
        PyModule_AddObject(m, "automation", automation_module);
        
        // Also add to sys.modules for proper import behavior
        PyObject* sys_modules = PyImport_GetModuleDict();
        PyDict_SetItemString(sys_modules, "mcrfpy.automation", automation_module);
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
    FILE* PScriptFile = fopen(filename.c_str(), "r");
    if(PScriptFile) {
        std::cout << "Before PyRun_SimpleFile" << std::endl;
        PyRun_SimpleFile(PScriptFile, filename.c_str());
        std::cout << "After PyRun_SimpleFile" << std::endl;
        fclose(PScriptFile);
    }
}

void McRFPy_API::api_shutdown()
{
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
	auto b = sf::SoundBuffer();
	b.loadFromFile(fn_cstr);
	McRFPy_API::soundbuffers.push_back(b);
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* McRFPy_API::_loadMusic(PyObject* self, PyObject* args) {
	const char *fn_cstr;
	PyObject* loop_obj;
	if (!PyArg_ParseTuple(args, "s|O", &fn_cstr, &loop_obj)) return NULL;
	McRFPy_API::music.stop();
	// get params for sf::Music initialization
	//sf::InputSoundFile file;
	//file.openFromFile(fn_cstr);
	McRFPy_API::music.openFromFile(fn_cstr);
	McRFPy_API::music.setLoop(PyObject_IsTrue(loop_obj));
	//McRFPy_API::music.initialize(file.getChannelCount(), file.getSampleRate());
	McRFPy_API::music.play();
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* McRFPy_API::_setMusicVolume(PyObject* self, PyObject* args) {
	int vol;
	if (!PyArg_ParseTuple(args, "i", &vol)) return NULL;
	McRFPy_API::music.setVolume(vol);
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* McRFPy_API::_setSoundVolume(PyObject* self, PyObject* args) {
	float vol;
	if (!PyArg_ParseTuple(args, "f", &vol)) return NULL;
	McRFPy_API::sfx.setVolume(vol);
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* McRFPy_API::_playSound(PyObject* self, PyObject* args) {
	float index;
	if (!PyArg_ParseTuple(args, "f", &index)) return NULL;
	if (index >= McRFPy_API::soundbuffers.size()) return NULL;
	McRFPy_API::sfx.stop();
	McRFPy_API::sfx.setBuffer(McRFPy_API::soundbuffers[index]);
	McRFPy_API::sfx.play();
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* McRFPy_API::_getMusicVolume(PyObject* self, PyObject* args) {
	return Py_BuildValue("f", McRFPy_API::music.getVolume());
}

PyObject* McRFPy_API::_getSoundVolume(PyObject* self, PyObject* args) {
	return Py_BuildValue("f", McRFPy_API::sfx.getVolume());
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
	if (!PyArg_ParseTuple(args, "s", &newscene)) return NULL;
	game->changeScene(newscene);
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
