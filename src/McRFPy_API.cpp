#include "McRFPy_API.h"
#include "platform.h"
#include "GameEngine.h"
#include "Grid.h"
#include "UI.h"
#include "Resources.h"

std::map<std::string, PyObject*> McRFPy_API::callbacks;
std::vector<sf::SoundBuffer> McRFPy_API::soundbuffers;
sf::Music McRFPy_API::music;
sf::Sound McRFPy_API::sfx;

static PyMethodDef mcrfpyMethods[] = {
    {"registerPyAction", McRFPy_API::_registerPyAction, METH_VARARGS,
        "Register a callable Python object to correspond to an action string. (actionstr, callable)"},
        
    {"registerInputAction", McRFPy_API::_registerInputAction, METH_VARARGS,
        "Register a SFML input code to correspond to an action string. (input_code, actionstr)"},

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

    {NULL, NULL, 0, NULL}
};

static PyModuleDef mcrfpyModule = {
    PyModuleDef_HEAD_INIT, "mcrfpy", NULL, -1, mcrfpyMethods,
    NULL, NULL, NULL, NULL
};

// Module initializer fn, passed to PyImport_AppendInittab
PyObject* PyInit_mcrfpy()
{
    PyObject* m = PyModule_Create(&mcrfpyModule);
    
    if (m == NULL) 
    {
        return NULL;
    }
    
    // This code runs, but Python segfaults when accessing the UIFrame type.
    //std::cout << "Adding UIFrame object to module\n";
    PyModule_AddType(m, &mcrfpydef::PyColorType);
    PyModule_AddType(m, &mcrfpydef::PyFontType);
    PyModule_AddType(m, &mcrfpydef::PyUICaptionType);
    PyModule_AddType(m, &mcrfpydef::PyTextureType);
    PyModule_AddType(m, &mcrfpydef::PyUISpriteType);
     
    if (PyModule_AddType(m, &mcrfpydef::PyUIFrameType) < 0)
    {
        std::cout << "Error adding UIFrame type to module; aborting" << std::endl;
        Py_DECREF(&mcrfpydef::PyUIFrameType);
        return NULL;
    }
    PyModule_AddType(m, &mcrfpydef::PyUICollectionType);
    PyModule_AddType(m, &mcrfpydef::PyUICollectionIterType);

    PyModule_AddType(m, &mcrfpydef::PyUIGridPointType);
    PyModule_AddType(m, &mcrfpydef::PyUIGridPointStateType);
    PyModule_AddType(m, &mcrfpydef::PyUIEntityType);

    PyModule_AddType(m, &mcrfpydef::PyUIEntityCollectionIterType);
    PyModule_AddType(m, &mcrfpydef::PyUIEntityCollectionType);

    PyModule_AddType(m, &mcrfpydef::PyUIGridType);

    

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
    return status;
}

void McRFPy_API::setSpriteTexture(int ti)
{
    int tx = ti % texture_width, ty = ti / texture_width;
    sprite.setTextureRect(sf::IntRect(
                tx * texture_size,
                ty * texture_size,
                texture_size, texture_size));
}

// functionality
//void McRFPy_API::

void McRFPy_API::api_init() {

    // build API exposure before python initialization
    PyImport_AppendInittab("mcrfpy", &PyInit_mcrfpy);
    // use full path version of argv[0] from OS to init python
    init_python(narrow_string(executable_filename()).c_str());

    //texture.loadFromFile("./assets/kenney_tinydungeon.png");
    //texture_size = 16, texture_width = 12, texture_height= 11;
    //texture_sprite_count = texture_width * texture_height;
    //texture.setSmooth(false);

    //sprite.setTexture(texture);
    //sprite.setScale(sf::Vector2f(4.0f, 4.0f));
    //setSpriteTexture(0);
}

void McRFPy_API::executeScript(std::string filename)
{
    FILE* PScriptFile = fopen(filename.c_str(), "r");
    if(PScriptFile) {
        PyRun_SimpleFile(PScriptFile, filename.c_str());
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
PyObject* McRFPy_API::_registerPyAction(PyObject *self, PyObject *args)
{
    PyObject* callable;
    const char * actionstr;
    if (!PyArg_ParseTuple(args, "sO", &actionstr, &callable)) return NULL;
    //TODO: if the string already exists in the callbacks map, 
    //  decrease our reference count so it can potentially be garbage collected
    callbacks[std::string(actionstr)] = callable;
    Py_INCREF(callable);

    // return None correctly
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* McRFPy_API::_registerInputAction(PyObject *self, PyObject *args)
{
    int action_code;
    const char * actionstr;
    if (!PyArg_ParseTuple(args, "iz", &action_code, &actionstr)) return NULL;
    
    bool success;
    
    if (actionstr == NULL) { // Action provided is None, i.e. unregister
        std::cout << "Unregistering\n";
        success = game->currentScene()->unregisterActionInjected(action_code, std::string(actionstr) + "_py");
    } else {
        std::cout << "Registering" << actionstr << "_py to " << action_code << "\n";
        success = game->currentScene()->registerActionInjected(action_code, std::string(actionstr) + "_py");
    }
    
    success ? Py_INCREF(Py_True) : Py_INCREF(Py_False);
    return success ? Py_True : Py_False;
    
}

void McRFPy_API::doAction(std::string actionstr) {
    // hard coded actions that require no registration
    //std::cout << "Calling Python Action: " << actionstr;
    if (!actionstr.compare("startrepl")) return McRFPy_API::REPL();
    if (callbacks.find(actionstr) == callbacks.end()) 
    {
        //std::cout << " (not found)" << std::endl;
        return;
    }
    //std::cout << " (" << PyUnicode_AsUTF8(PyObject_Repr(callbacks[actionstr])) << ")" << std::endl;
    PyObject_Call(callbacks[actionstr], PyTuple_New(0), NULL);
}

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

/*
void McRFPy_API::player_input(int dx, int dy) {
	//std::cout << "# entities tagged 'player': " << McRFPy_API::entities.getEntities("player").size() << std::endl;
	auto player_entity = McRFPy_API::entities.getEntities("player")[0];
	auto grid = player_entity->cGrid->grid;
	//std::cout << "Grid pointed to: " << (long)player_entity->cGrid->grid << std::endl;
	if (McRFPy_API::input_mode.compare("playerturn") != 0) {
		// no input accepted while computer moving
		//std::cout << "Can't move while it's not player's turn." << std::endl;
		return;
	}
	// TODO: selection cursor via keyboard
	// else if (!input_mode.compare("selectpoint") {}
	// else if (!input_mode.compare("selectentity") {}
	
	// grid bounds check
	if (player_entity->cGrid->x + dx < 0 ||
	    player_entity->cGrid->y + dy < 0 ||
	    player_entity->cGrid->x + dx > grid->grid_x - 1 ||
	    player_entity->cGrid->y + dy > grid->grid_y - 1) {
	    //std::cout << "(" << player_entity->cGrid->x << ", " << player_entity->cGrid->y <<
	    //  ") + (" << dx << ", " << dy << ") is OOB." << std::endl;
	    return;
	}
	//std::cout << PyUnicode_AsUTF8(PyObject_Repr(player_entity->cBehavior->object)) << std::endl;
	PyObject* move_fn = PyObject_GetAttrString(player_entity->cBehavior->object, "move");
	//std::cout << PyUnicode_AsUTF8(PyObject_Repr(move_fn)) << std::endl;
	if (move_fn) {
		//std::cout << "Calling `move`" << std::endl;
		PyObject* move_args = Py_BuildValue("(ii)", dx, dy);
		PyObject_CallObject((PyObject*) move_fn, move_args);
	} else {
		//std::cout << "player_input called on entity with no `move` method" << std::endl;
	}
}


void McRFPy_API::computerTurn() {
	McRFPy_API::input_mode = "computerturnrunning";
	for (auto e : McRFPy_API::grids[McRFPy_API::active_grid]->entities) {
		if (e->cBehavior) {
			PyObject_Call(PyObject_GetAttrString(e->cBehavior->object, "ai_act"), PyTuple_New(0), NULL);
		}
	}
}

void McRFPy_API::playerTurn() {
	McRFPy_API::input_mode = "playerturn";
	for (auto e : McRFPy_API::entities.getEntities("player")) {
		if (e->cBehavior) {
			PyObject_Call(PyObject_GetAttrString(e->cBehavior->object, "player_act"), PyTuple_New(0), NULL);
		}
	}
}

void McRFPy_API::camFollow() {
	if (!McRFPy_API::do_camfollow) return;
	auto& ag = McRFPy_API::grids[McRFPy_API::active_grid];
	for (auto e : McRFPy_API::entities.getEntities("player")) {
		//std::cout << "grid center: " << ag->center_x << ", " << ag->center_y << std::endl <<
		//             "player grid pos: " << e->cGrid->x << ", " << e->cGrid->y << std::endl <<
		//             "player sprite pos: " << e->cGrid->indexsprite.x << ", " << e->cGrid->indexsprite.y << std::endl;
		ag->center_x = e->cGrid->indexsprite.x * ag->grid_size + ag->grid_size * 0.5;
		ag->center_y = e->cGrid->indexsprite.y * ag->grid_size + ag->grid_size * 0.5;
	}
}

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
    if (game->currentScene()->key_callable != NULL and game->currentScene()->key_callable != Py_None)
    {
        Py_DECREF(game->currentScene()->key_callable);
    }
    Py_INCREF(callable);
    game->currentScene()->key_callable = callable;
    Py_INCREF(Py_None);
    return Py_None;		
}
