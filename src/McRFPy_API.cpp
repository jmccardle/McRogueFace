#include "McRFPy_API.h"
#include "platform.h"
#include "GameEngine.h"
#include "Grid.h"
#include "UI.h"
#include "Resources.h"

// static class members...?
std::map<std::string, UIMenu*> McRFPy_API::menus;
std::map<std::string, Grid*> McRFPy_API::grids;
std::map<std::string, PyObject*> McRFPy_API::callbacks;
std::list<Animation*> McRFPy_API::animations;
std::vector<sf::SoundBuffer> McRFPy_API::soundbuffers;
sf::Music McRFPy_API::music;
sf::Sound McRFPy_API::sfx;
std::string McRFPy_API::input_mode;
int McRFPy_API::turn_number;
std::string McRFPy_API::active_grid;
bool McRFPy_API::do_camfollow;

EntityManager McRFPy_API::entities;

static PyMethodDef mcrfpyMethods[] = {

    {"createMenu", McRFPy_API::_createMenu, METH_VARARGS,
        "Create a new uimenu (name_str, x, y, w, h)"},

    {"listMenus", McRFPy_API::_listMenus, METH_VARARGS,
        "return a list of existing menus"},

    {"modMenu", McRFPy_API::_modMenu, METH_VARARGS,
        "call with a UIMenu object to update all fields"},

    {"createCaption", McRFPy_API::_createCaption, METH_VARARGS,
        "Create a new text caption (menu_str, text_str, fontsize, r, g, b)"},

    {"createButton", McRFPy_API::_createButton, METH_VARARGS,
        "Create a new button (menu_str, x, y, w, h, (bg r, g, b), (text r, g, b), caption, action_code)"},

    {"createSprite", McRFPy_API::_createSprite, METH_VARARGS,
        "Create a new sprite (menu_str, texture_index, sprite_index, x, y, scale)"},

    {"createTexture", McRFPy_API::_createTexture, METH_VARARGS,
        "Create a new texture (filename_str, grid_size, width, height) - grid_size is in pixels (only square sprites for now), width and height are in tiles"},

    {"registerPyAction", McRFPy_API::_registerPyAction, METH_VARARGS,
        "Register a callable Python object to correspond to an action string. (actionstr, callable)"},
        
    {"registerInputAction", McRFPy_API::_registerInputAction, METH_VARARGS,
        "Register a SFML input code to correspond to an action string. (input_code, actionstr)"},

    {"createGrid", McRFPy_API::_createGrid, METH_VARARGS,
        "create a new grid (title, grid_x, grid_y, grid_size, x, y, w, h). grid_x and grid_y are the width and height in squares. grid_size is the pixel w/h of sprites on the grid. x,y are the grid's screen position. w,h are the grid's screen size" },

    {"listGrids", McRFPy_API::_listGrids, METH_VARARGS,
        "return grid objects and all points" },

    {"modGrid", McRFPy_API::_modGrid, METH_VARARGS,
        "call with a Grid object to update all fields"},

    {"createAnimation", McRFPy_API::_createAnimation, METH_VARARGS,
        "Create a new animation:\n"
        "createAnimation(duration:float, parent:string, target_type:string, target_id:string or int, field:string, callback:function, loop:bool, frames:list)\n"
        "duration: total animation time in seconds\n"
        "parent: the name of a UI menu or grid\n"
        "target_type: 'caption', 'button', 'sprite', or 'entity'\n"
        "target_id: integer index of the caption or button, or string ID of entity\n"
        "field: what to animate. 'position', 'size', 'bgcolor', 'textcolor' or 'sprite'\n"
        "callback: called when the animation completes\n"
        "loop: if True, animation repeats; if False, animation is deleted\n"
        "frames: if animating a sprite, list the frames. For other data types, the value will change in discrete steps at a rate of duration/len(frames).\n"},

/*
    static PyObject* _createSoundBuffer(PyObject*, PyObject*);
    static PyObject* _loadMusic(PyObject*, PyObject*);
    static PyObject* _setMusicVolume(PyObject*, PyObject*);
    static PyObject* _setSoundVolume(PyObject*, PyObject*);
    static PyObject* _playSound(PyObject*, PyObject*);
    static PyObject* _getMusicVolume(PyObject*, PyObject*);
    static PyObject* _getSoundVolume(PyObject*, PyObject*);
*/
	{"createSoundBuffer", McRFPy_API::_createSoundBuffer, METH_VARARGS, "(filename)"},
	{"loadMusic", McRFPy_API::_loadMusic, METH_VARARGS, "(filename)"},
	{"setMusicVolume", McRFPy_API::_setMusicVolume, METH_VARARGS, "(int)"},
	{"setSoundVolume", McRFPy_API::_setSoundVolume, METH_VARARGS, "(int)"},
	{"playSound", McRFPy_API::_playSound, METH_VARARGS, "(int)"},
	{"getMusicVolume", McRFPy_API::_getMusicVolume, METH_VARARGS, ""},
	{"getSoundVolume", McRFPy_API::_getSoundVolume, METH_VARARGS, ""},
	
	{"unlockPlayerInput", McRFPy_API::_unlockPlayerInput, METH_VARARGS, ""},
	{"lockPlayerInput", McRFPy_API::_lockPlayerInput, METH_VARARGS, ""},
	{"requestGridTarget", McRFPy_API::_requestGridTarget, METH_VARARGS, ""},
	{"activeGrid", McRFPy_API::_activeGrid, METH_VARARGS, ""},
	{"setActiveGrid", McRFPy_API::_setActiveGrid, METH_VARARGS, ""},
	{"inputMode", McRFPy_API::_inputMode, METH_VARARGS, ""},
	{"turnNumber", McRFPy_API::_turnNumber, METH_VARARGS, ""},
	{"createEntity", McRFPy_API::_createEntity, METH_VARARGS, ""},
	//{"listEntities", McRFPy_API::_listEntities, METH_VARARGS, ""},
	{"refreshFov", McRFPy_API::_refreshFov, METH_VARARGS, ""},
	
	{"camFollow", McRFPy_API::_camFollow, METH_VARARGS, ""},

    {"sceneUI", McRFPy_API::_sceneUI, METH_VARARGS, "sceneUI(scene) - Returns a list of UI elements"},

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

/*
    // Create Python translations of types
    PyTypeObject * gridpoint_pytype = new PyTypeObject;
    gridpoint_pytype->tp_name = "GridPoint";
    gridpoint_pytype->tp_basicsize = sizeof(GridPoint);
    gridpoint_pytype->tp_dealloc = [](PyObject* obj) {
        delete ((GridPoint*) obj);
    };
    gridpoint_pytype->tp_flags = Py_TPFLAGS_DEFAULT;
    gridpoint_pytype->tp_doc = "GridPoint";
    gridpoint_pytype->tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) {
        return (PyObject*) new GridPoint();
    };
    PyType_Ready(gridpoint_pytype);
    PyModule_AddObject(
            PyImport_AddModule("__main__"), "GridPoint", (PyObject*) gridpoint_pytype);
*/



    texture.loadFromFile("./assets/kenney_tinydungeon.png");
    //texture_size = 16, texture_width = 12, texture_height= 11;
    //texture_sprite_count = texture_width * texture_height;
    texture.setSmooth(false);

    sprite.setTexture(texture);
    sprite.setScale(sf::Vector2f(4.0f, 4.0f));
    setSpriteTexture(0);
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

PyObject* McRFPy_API::_createMenu(PyObject *self, PyObject *args) {
    const char* title_cstr;
    int posx, posy, sizex, sizey;
    if (!PyArg_ParseTuple(args, "siiii", &title_cstr, &posx, &posy, &sizex, &sizey)) return NULL;
    std::string title = title_cstr;
    //TODO (Bug 2) check for and free existing key before overwriting ptr
    menus[title] = createMenu(posx, posy, sizex, sizey);
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* McRFPy_API::_listMenus(PyObject*, PyObject*) {
    // todo - get the (Py) classes UIMenu, Button, Caption, Sprite
    // and call BuildValue (tuples) -> their constructors
    PyObject* uimodule = PyImport_AddModule("UIMenu"); //already imported
    PyObject* uimenu_type = PyObject_GetAttrString(uimodule, "UIMenu");
    PyObject* btn_type = PyObject_GetAttrString(uimodule, "Button");
    PyObject* cap_type = PyObject_GetAttrString(uimodule, "Caption");
    PyObject* spr_type = PyObject_GetAttrString(uimodule, "Sprite");

    PyObject* menulist = PyList_New(menus.size());
    std::map<std::string, UIMenu*>::iterator it = menus.begin();
    //for (int i = 0; i < menus.size(); i++) {
    int i = 0;
    for (auto it = menus.begin(); it != menus.end(); it++) {
        std::string title = it->first;
        auto menu = it->second;
        auto p = menu->box.getPosition();
        auto s = menu->box.getSize();
        auto g = menu->box.getFillColor();
        PyObject* menu_args = Py_BuildValue("(siiii(iii)O)",
            title.c_str(),
            (int)p.x, (int)p.y, (int)s.x, (int)s.y,
            (int)g.r, (int)g.g, (int)g.b, 
            menu->visible ? Py_True: Py_False);
        menu->visible ? Py_INCREF(Py_True) : Py_INCREF(Py_False);
        PyObject* menuobj = PyObject_CallObject((PyObject*) uimenu_type, menu_args);

        // Loop: Convert Button objects to Python Objects
        PyObject* button_list = PyObject_GetAttrString(menuobj, "buttons");
        for(auto& b : menu->buttons) {
            auto bp = b.rect.getPosition();
            auto bs = b.rect.getSize();
            auto bg = b.rect.getFillColor();
            auto bf = b.caption.getFillColor();
            PyObject* btn_args = Py_BuildValue("(iiii(iii)(iii)ss)",
                (int)bp.x, (int)bp.y, (int)bs.x, (int)bs.y,
                (int)bg.r, (int)bg.g, (int)bg.b,
                (int)bf.r, (int)bf.g, (int)bf.b,
                b.caption.getString().toAnsiString().c_str(),
                b.action.c_str());
            PyObject* buttonobj = PyObject_CallObject((PyObject*) btn_type, btn_args);
            PyList_Append(button_list, buttonobj);
        }

        // Loop: Convert Caption objects to Python Objects
        PyObject* caption_list = PyObject_GetAttrString(menuobj, "captions");
        for (auto& c : menu->captions) {
            auto cc = c.getFillColor();
            PyObject* cap_args = Py_BuildValue("si(iii)",
               c.getString().toAnsiString().c_str(),
               c.getCharacterSize(),
               cc.r, cc.g, cc.b);
            PyObject* capobj = PyObject_CallObject((PyObject*) cap_type, cap_args);
            PyList_Append(caption_list, capobj);
        }

        // Loop: Convert Sprite objects to Python Objects
        PyObject* sprite_list = PyObject_GetAttrString(menuobj, "sprites");
        for (auto& s : menu->sprites) {
            PyObject* spr_args = Py_BuildValue("(iiff)",
                s.texture_index, s.sprite_index, s.x, s.y);

            PyObject* sprobj = PyObject_CallObject((PyObject*) spr_type, spr_args);
            PyList_Append(sprite_list, sprobj);
        }

        PyList_SET_ITEM(menulist, i, menuobj);
        i++; // count iterator steps
    }
    return menulist;
}

PyObject* McRFPy_API::_modMenu(PyObject* self, PyObject* args) {
    PyObject* o;
    if (!PyArg_ParseTuple(args, "O", &o)) return NULL;
    std::string title = PyUnicode_AsUTF8(PyObject_GetAttrString(o, "title"));
    int x = PyLong_AsLong(PyObject_GetAttrString(o, "x"));
    int y = PyLong_AsLong(PyObject_GetAttrString(o, "y"));
    int w = PyLong_AsLong(PyObject_GetAttrString(o, "w"));
    int h = PyLong_AsLong(PyObject_GetAttrString(o, "h"));
    PyObject* bgtuple = PyObject_GetAttrString(o, "bgcolor");
    auto bgcolor = sf::Color(
        PyLong_AsLong(PyTuple_GetItem(bgtuple, 0)),
        PyLong_AsLong(PyTuple_GetItem(bgtuple, 1)),
        PyLong_AsLong(PyTuple_GetItem(bgtuple, 2))
        );
    bool visible = PyObject_IsTrue(PyObject_GetAttrString(o, "visible"));

    auto menu = menus[title];
    if (menu == NULL) return NULL;
    menu->box.setPosition(sf::Vector2f(x, y));
    menu->box.setSize(sf::Vector2f(w, h));
    menu->box.setFillColor(bgcolor);
    menu->visible = visible;

    // jank, or dank? iterate over .captions, .buttons, .sprites to modify them
    // captions
    PyObject* captionlist = PyObject_GetAttrString(o, "captions");
    //std::cout << PyUnicode_AsUTF8(PyObject_Repr(captionlist)) << std::endl;
    for (int i = 0; i < menu->captions.size(); i++) {
        PyObject* captionobj = PyList_GetItem(captionlist, i);
        menu->captions[i].setString(
            PyUnicode_AsUTF8(PyObject_GetAttrString(captionobj, "text")));
        //menu->captions[i].setCharacterSize(
        //    PyLong_AsLong(PyObject_GetAttrString(captionobj, "textsize")));
        PyObject* fgtuple = PyObject_GetAttrString(captionobj, "color");
        menu->captions[i].setFillColor(
            sf::Color(
                PyLong_AsLong(PyTuple_GetItem(fgtuple, 0)),
                PyLong_AsLong(PyTuple_GetItem(fgtuple, 1)),
                PyLong_AsLong(PyTuple_GetItem(fgtuple, 2))
                ));
    }

    // buttons
    PyObject* buttonlist = PyObject_GetAttrString(o, "buttons");
    //std::cout << PyUnicode_AsUTF8(PyObject_Repr(buttonlist)) << std::endl;
    for (int i = 0; i < menu->buttons.size(); i++) {
        PyObject* buttonobj = PyList_GetItem(buttonlist, i);
        menu->buttons[i].setPosition(sf::Vector2f(
            PyLong_AsLong(PyObject_GetAttrString(buttonobj, "x")),
            PyLong_AsLong(PyObject_GetAttrString(buttonobj, "y"))
            ));
        auto sizevec = sf::Vector2f(
            PyLong_AsLong(PyObject_GetAttrString(buttonobj, "w")),
            PyLong_AsLong(PyObject_GetAttrString(buttonobj, "h"))
            );
        menu->buttons[i].setSize(sizevec);
        PyObject* btncolor = PyObject_GetAttrString(buttonobj, "bgcolor");
        //std::cout << PyUnicode_AsUTF8(PyObject_Repr(btncolor)) << std::endl;
        menu->buttons[i].setBackground(
            sf::Color(
                PyLong_AsLong(PyTuple_GetItem(btncolor, 0)),
                PyLong_AsLong(PyTuple_GetItem(btncolor, 1)),
                PyLong_AsLong(PyTuple_GetItem(btncolor, 2))
                ));
        PyObject* btxtcolor = PyObject_GetAttrString(buttonobj, "textcolor");
        //std::cout << PyUnicode_AsUTF8(PyObject_Repr(btxtcolor)) << std::endl;
        menu->buttons[i].setTextColor(
            sf::Color(
                PyLong_AsLong(PyTuple_GetItem(btxtcolor, 0)),
                PyLong_AsLong(PyTuple_GetItem(btxtcolor, 1)),
                PyLong_AsLong(PyTuple_GetItem(btxtcolor, 2))
                ));
        //std::cout << PyObject_Repr(PyObject_GetAttrString(buttonobj, "text")) << std::endl;
        menu->buttons[i].caption.setString(
        PyUnicode_AsUTF8(PyObject_GetAttrString(buttonobj, "text")));
        //std::cout << PyObject_Repr(PyObject_GetAttrString(buttonobj, "actioncode")) << std::endl;
        menu->buttons[i].action = 
        PyUnicode_AsUTF8(PyObject_GetAttrString(buttonobj, "actioncode"));
    }

    // sprites
    PyObject* spriteslist = PyObject_GetAttrString(o, "sprites");
    //std::cout << PyUnicode_AsUTF8(PyObject_Repr(spriteslist)) << std::endl;
    for (int i = 0; i < menu->sprites.size(); i++) {
        PyObject* spriteobj = PyList_GetItem(spriteslist, i);
        menu->sprites[i].texture_index = 
            PyLong_AsLong(PyObject_GetAttrString(spriteobj, "tex_index"));
        menu->sprites[i].sprite_index = 
            PyLong_AsLong(PyObject_GetAttrString(spriteobj, "sprite_index"));
        menu->sprites[i].x = 
            PyFloat_AsDouble(PyObject_GetAttrString(spriteobj, "x"));
        menu->sprites[i].y = 
            PyFloat_AsDouble(PyObject_GetAttrString(spriteobj, "y"));
    }

    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* McRFPy_API::_createCaption(PyObject* self, PyObject* args) {
    const char* menukey_cstr, *text_cstr;
    int fontsize, cr, cg, cb;
    if (!PyArg_ParseTuple(args, "ssi(iii)", 
        &menukey_cstr, &text_cstr,
        &fontsize, &cr, &cg, &cb)) return NULL;
    createCaption(std::string(menukey_cstr), std::string(text_cstr), fontsize, sf::Color(cr, cg, cb));
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* McRFPy_API::_createButton(PyObject* self, PyObject* args) {
    const char *menukey_cstr, *caption_cstr, *action_cstr;
    int x, y, w, h, bgr, bgg, bgb, fgr, fgg, fgb;
    if (!PyArg_ParseTuple(args, "siiii(iii)(iii)ss",
        &menukey_cstr, &x, &y, &w, &h, 
        &bgr, &bgg, &bgb, &fgr, &fgg, &fgb,
        &caption_cstr, &action_cstr
        )) return NULL;
    createButton(std::string(menukey_cstr), x, y, w, h, sf::Color(bgr, bgg, bgb), sf::Color(fgr, fgg, fgb), std::string(caption_cstr), std::string(action_cstr));
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* McRFPy_API::_createTexture(PyObject* self, PyObject* args) {
    const char *fn_cstr;
    int gs, gw, gh;
    if (!PyArg_ParseTuple(args, "siii", &fn_cstr, &gs, &gw, &gh)) return NULL;
    createTexture(std::string(fn_cstr), gs, gw, gh);
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* McRFPy_API::_listTextures(PyObject*, PyObject*) {
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* McRFPy_API::_createSprite(PyObject* self, PyObject* args) {
    const char * menu_cstr;
    int ti, si;
    float x, y;
    float s;
    if (!PyArg_ParseTuple(args, "siifff", &menu_cstr, &ti, &si, &x, &y, &s)) return NULL;
    //std::cout << "Creating uisprite " << ti << " " << si << " " << x << " " << y << " " << s << " " << std::endl;
    createSprite(std::string(menu_cstr), ti, si, x, y, s);
    Py_INCREF(Py_None);
    return Py_None;
}

UIMenu *McRFPy_API::createMenu(int posx, int posy, int sizex, int sizey) {
    auto m = new UIMenu(game->getFont());
    m->box.setPosition(sf::Vector2f(posx, posy));
    m->box.setSize(sf::Vector2f(sizex, sizey));
    return m;
}

void McRFPy_API::createCaption(std::string menukey, std::string text, int fontsize, sf::Color textcolor) {
    auto menu = menus[menukey];
    menu->add_caption(text.c_str(), fontsize, textcolor);
}

void McRFPy_API::createButton(std::string menukey, int x, int y, int w, int h, sf::Color bgcolor, sf::Color textcolor, std::string caption, std::string action) {
    auto menu = menus[menukey];
    auto b = Button(x, y, w, h, bgcolor, textcolor, caption.c_str(), game->getFont(), action.c_str());
    menu->add_button(b);
}

void McRFPy_API::createSprite(std::string menukey, int ti, int si, float x, float y, float scale) {
    auto menu = menus[menukey];
    auto s = IndexSprite(ti, si, x, y, scale);
    menu->add_sprite(s);
    //std::cout << "indexsprite just created has values x,y " << s.x << ", " << s.y << std::endl;
}

int McRFPy_API::createTexture(std::string filename, int grid_size, int grid_width, int grid_height) {
    sf::Texture t;
    t.loadFromFile(filename.c_str());
    t.setSmooth(false);
    auto indextex = IndexTexture(t, grid_size, grid_width, grid_height);
    game->textures.push_back(indextex);

    return game->textures.size() - 1;
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

PyObject* McRFPy_API::_createGrid(PyObject *self, PyObject *args) {
    const char* title_cstr;
    int gx, gy, gs, x, y, w, h;
    if (!PyArg_ParseTuple(args, "siiiiiii", &title_cstr, &gx, &gy, &gs, &x, &y, &w, &h)) return NULL;
    std::string title = title_cstr;
    //TODO - (Bug 2) check for key existing, and free if overwriting
    grids[title] = new Grid(gx, gy, gs, x, y, w, h);
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* McRFPy_API::_listGrids(PyObject*, PyObject*) {
    PyObject* gridmodule = PyImport_AddModule("Grid"); //already imported
    PyObject* grid_type = PyObject_GetAttrString(gridmodule, "Grid");
    PyObject* gridpoint_type = PyObject_GetAttrString(gridmodule, "GridPoint");
    PyObject* entity_type = PyObject_GetAttrString(gridmodule, "Entity");

    //std::cout << PyUnicode_AsUTF8(PyObject_Repr(gridmodule)) << std::endl;
    //std::cout << PyUnicode_AsUTF8(PyObject_Repr(grid_type)) << std::endl;
    //std::cout << PyUnicode_AsUTF8(PyObject_Repr(gridpoint_type)) << std::endl;
    //std::cout << PyUnicode_AsUTF8(PyObject_Repr(entity_type)) << std::endl;
        
    PyObject* gridlist = PyList_New(grids.size());
    std::map<std::string, Grid*>::iterator it = grids.begin();
    int i = 0;
    for (auto it = grids.begin(); it != grids.end(); it++) {
        std::string title = it->first;
        auto grid = it->second;
        auto p = grid->box.getPosition();
        auto s = grid->box.getSize();
        PyObject* grid_args = Py_BuildValue("(siiiiiiiO)",
            title.c_str(),
            (int)grid->grid_x, (int)grid->grid_y, (int)grid->grid_size,
			(int)p.x, (int)p.y, (int)s.x, (int)s.y, 
			grid->visible? Py_True: Py_False);

		grid->visible ? Py_INCREF(Py_True) : Py_INCREF(Py_False);
        //std::cout << PyUnicode_AsUTF8(PyObject_Repr(grid_args)) << std::endl;

        PyObject* gridobj = PyObject_CallObject((PyObject*) grid_type, grid_args);
        //std::cout << (long)gridobj << std::flush <<std::endl;

        //std::cout << PyUnicode_AsUTF8(PyObject_Repr(gridobj)) << std::endl;
        // Loop: Convert GridPoint objects to Python Objects
        PyObject* gridp_list = PyObject_GetAttrString(gridobj, "points");
        for(auto& p : grid->points) {
            PyObject* gridp_args = Py_BuildValue("((iii)OiOOO(iii)ii)",
                (int)p.color.r, (int)p.color.g, (int)p.color.b,
				p.walkable ? Py_True: Py_False,
        		p.tilesprite,
				p.transparent ? Py_True: Py_False,
				p.visible ? Py_True: Py_False,
				p.discovered ? Py_True: Py_False,
                (int)p.color_overlay.r, (int)p.color_overlay.g, (int)p.color_overlay.b,
                p.tile_overlay,
				p.uisprite);
			p.walkable ? Py_INCREF(Py_True) : Py_INCREF(Py_False);
			p.transparent ? Py_INCREF(Py_True) : Py_INCREF(Py_False);
            p.visible ? Py_INCREF(Py_True) : Py_INCREF(Py_False);
			p.discovered ? Py_INCREF(Py_True) : Py_INCREF(Py_False);
            PyObject* gridpobj = PyObject_CallObject((PyObject*) gridpoint_type, gridp_args);
            PyList_Append(gridp_list, gridpobj);
		}
		
		PyObject* ent_list = PyObject_GetAttrString(gridobj, "entities");
		for (auto e : grid->entities) {
			//def __init__(self, parent, tex_index, sprite_index, x, y, visible=True):
			PyObject* ent_args = Py_BuildValue("siiiiO",
				title.c_str(),
				e->cGrid->indexsprite.texture_index,
				e->cGrid->indexsprite.sprite_index,
				e->cGrid->x,
				e->cGrid->y,
				e->cGrid->visible ? Py_True: Py_False);
			//std::cout << PyUnicode_AsUTF8(PyObject_Repr(ent_args)) << std::endl;
			e->cGrid->visible ? Py_INCREF(Py_True) : Py_INCREF(Py_False);
			PyObject* entobj = PyObject_CallObject((PyObject*) entity_type, ent_args);
			PyList_Append(ent_list, entobj);
			//std::cout << PyUnicode_AsUTF8(PyObject_Repr(ent_list)) << std::endl;
		}
		
		PyList_SET_ITEM(gridlist, i, gridobj);
        i++; // count iterator steps
    }
    return gridlist;
}

PyObject* McRFPy_API::_modGrid(PyObject* self, PyObject* args) {
    PyObject* o;
    PyObject* bool_is_entityonly = Py_False;
    if (!PyArg_ParseTuple(args, "O|O", &o, &bool_is_entityonly)) return NULL;
    //std::cout << "EntOnly Flag: " << PyUnicode_AsUTF8(PyObject_Repr(bool_is_entityonly)) << std::endl;
    std::string title = PyUnicode_AsUTF8(PyObject_GetAttrString(o, "title"));
    int grid_x = PyLong_AsLong(PyObject_GetAttrString(o, "grid_x"));
    int grid_y = PyLong_AsLong(PyObject_GetAttrString(o, "grid_y"));
    int grid_size = PyLong_AsLong(PyObject_GetAttrString(o, "grid_size"));
    int x = PyLong_AsLong(PyObject_GetAttrString(o, "x"));
    int y = PyLong_AsLong(PyObject_GetAttrString(o, "y"));
    int w = PyLong_AsLong(PyObject_GetAttrString(o, "w"));
    int h = PyLong_AsLong(PyObject_GetAttrString(o, "h"));
    bool visible = PyObject_IsTrue(PyObject_GetAttrString(o, "visible"));

    auto grid = grids[title];
    if (grid == NULL) return NULL;
    grid->box.setPosition(sf::Vector2f(x, y));
    grid->box.setSize(sf::Vector2f(w, h));
    grid->visible = visible;

    //iterate over gridpoints
    if (!PyObject_IsTrue(bool_is_entityonly)) {
		PyObject* gpointlist = PyObject_GetAttrString(o, "points");
		//std::cout << PyUnicode_AsUTF8(PyObject_Repr(gpointlist)) << std::endl;
		for (int i = 0; i < grid->points.size(); i++) {
			PyObject* gpointobj = PyList_GetItem(gpointlist, i);
			PyObject* colortuple = PyObject_GetAttrString(gpointobj, "color");
			grid->points[i].color =
				sf::Color(
					PyLong_AsLong(PyTuple_GetItem(colortuple, 0)),
					PyLong_AsLong(PyTuple_GetItem(colortuple, 1)),
					PyLong_AsLong(PyTuple_GetItem(colortuple, 2))
					);
			grid->points[i].walkable = PyObject_IsTrue(PyObject_GetAttrString(gpointobj, "walkable"));
			grid->points[i].tilesprite = PyLong_AsLong(PyObject_GetAttrString(gpointobj, "tilesprite"));
			grid->points[i].transparent = PyObject_IsTrue(PyObject_GetAttrString(gpointobj, "transparent"));
			grid->points[i].visible = PyObject_IsTrue(PyObject_GetAttrString(gpointobj, "visible"));
			grid->points[i].discovered = PyObject_IsTrue(PyObject_GetAttrString(gpointobj, "discovered"));
			PyObject* overlaycolortuple = PyObject_GetAttrString(gpointobj, "color_overlay");
			grid->points[i].color_overlay =
				sf::Color(
					PyLong_AsLong(PyTuple_GetItem(overlaycolortuple, 0)),
					PyLong_AsLong(PyTuple_GetItem(overlaycolortuple, 1)),
					PyLong_AsLong(PyTuple_GetItem(overlaycolortuple, 2))
					);
			grid->points[i].tile_overlay = PyLong_AsLong(PyObject_GetAttrString(gpointobj, "tile_overlay"));
			grid->points[i].uisprite = PyLong_AsLong(PyObject_GetAttrString(gpointobj, "uisprite"));
		}
		
		// update grid pathfinding & visibility
		grid->refreshTCODmap();
		for (auto e : McRFPy_API::entities.getEntities("player")) {
			grid->refreshTCODsight(e->cGrid->x, e->cGrid->y);
		}
	}
    PyObject* entlist = PyObject_GetAttrString(o, "entities");
    //std::cout << PyUnicode_AsUTF8(PyObject_Repr(entlist)) << std::endl;
    for (int i = 0; i < grid->entities.size(); i++) {
		PyObject* entobj = PyList_GetItem(entlist, i);
		//std::cout << PyUnicode_AsUTF8(PyObject_Repr(entobj)) << std::endl;
		grid->entities[i]->cGrid->x = PyLong_AsLong(PyObject_GetAttrString(entobj, "x"));
		grid->entities[i]->cGrid->y = PyLong_AsLong(PyObject_GetAttrString(entobj, "y"));
		grid->entities[i]->cGrid->indexsprite.texture_index = PyLong_AsLong(PyObject_GetAttrString(entobj, "tex_index"));
		grid->entities[i]->cGrid->indexsprite.sprite_index = PyLong_AsLong(PyObject_GetAttrString(entobj, "sprite_index"));
	}

    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* McRFPy_API::_refreshFov(PyObject* self, PyObject* args) {
	for (auto e : McRFPy_API::entities.getEntities("player")) {
		e->cGrid->grid->refreshTCODsight(e->cGrid->x, e->cGrid->y);
	}
	Py_INCREF(Py_None);
    return Py_None;
}

PyObject* _test_createAnimation(PyObject *self, PyObject *args) {
    //LerpAnimation<T>::LerpAnimation(float _d, T _ev, T* _t, std::function<void()> _cb, std::function<void(T)> _w, bool _l)
    std::string menu_key = "demobox1";
    McRFPy_API::animations.push_back(
        new LerpAnimation<sf::Vector2f>(
         3.0, 
         sf::Vector2f(100, 100), 
         McRFPy_API::menus[menu_key]->box.getPosition(),
         [](){McRFPy_API::executePyString("print('animation callback')");},
         [=](sf::Vector2f v) {
			 //std::cout << "write lambda!" << std::endl; 
			 McRFPy_API::menus[menu_key]->box.setPosition(v); 
			 //std::cout << "Position set to" << McRFPy_API::menus[menu_key]->box.getPosition().x 
			 //<< ", " << McRFPy_API::menus[menu_key]->box.getPosition().y << std::endl;
			 }, 
         false)
    );

    Py_INCREF(Py_None);
    return Py_None;
}

#define CEQ(A, B) (std::string(A).compare(B) == 0)

PyObject* McRFPy_API::_createAnimation(PyObject *self, PyObject *args) {
	//std::cout << "Creating animation called..." << std::endl;
    float duration;
	const char* parent;
	const char* target_type;
	PyObject* target_id_obj;
	const char* field;
	PyObject* callback;
	PyObject* loop_obj;
	PyObject* values_obj;
	PyObject* evdata; // for decoding values_obj
	//std::cout << PyUnicode_AsUTF8(PyObject_Repr(args)) << std::endl;
    if (!PyArg_ParseTuple(args, "fssOsOOO", &duration, &parent, &target_type, &target_id_obj, &field, &callback, &loop_obj, &values_obj)) { return NULL; }
    bool loop = PyObject_IsTrue(loop_obj);
    int target_id = PyLong_AsLong(target_id_obj);
    Py_INCREF(callback);
    /*
    std::cout << "Animation fields received:" <<
		"\nduration: " << duration <<
		"\nparent: " << parent <<
		"\ntarget type: " << target_type <<
		"\ntarget id: " << PyUnicode_AsUTF8(PyObject_Repr(target_id_obj)) <<
		"\nfield: " << field <<
		"\ncallback: " << PyUnicode_AsUTF8(PyObject_Repr(callback)) <<
		"\nloop: " << loop <<
		"\nvalues: " << PyUnicode_AsUTF8(PyObject_Repr(values_obj)) << std::endl;
	*/
	/* Jank alert:
	 * The following block is meant to raise an exception when index is missing from object animations that require one,
	 * but accept the target_id_obj error (and accept None as an index) for menus/grids.
	 * Instead, I get a "latent" exception, not properly raised, when the index is None.
	 * That not-really-raised exception causes other scripts to silently fail to execute
	 * until I go into the REPL and run any code, and get a bizarre, botched traceback.
	 * So, Grid/Menu can just take an index of 0 in the scripts until this is dejankified
	 */
	if (!CEQ(target_type, "menu") && !CEQ(target_type, "grid") && target_id == -1) {
		PyErr_SetObject(PyExc_TypeError, target_id_obj);
		PyErr_SetString(PyExc_TypeError, "target_id (integer, index value) is required for targets other than 'menu' or 'grid'");
		return NULL;
	}
	// at this point, `values` needs to be decoded based on the `field` provided
	
//            3.0, # duration, seconds
//            "demobox1", # parent: a UIMenu or Grid key
//            "menu", # target type: 'menu', 'grid', 'caption', 'button', 'sprite', or 'entity'
//            None, # target id: integer index for menu or grid objs; None for grid/menu
//            "position", # field: 'position', 'size', 'bgcolor', 'textcolor', or 'sprite'
//            lambda: self.animation_done("demobox1"), #callback: callable once animation is complete
//            False, #loop: repeat indefinitely
//            [100, 100] # values: iterable of frames for 'sprite', lerp target for others

//LerpAnimation<T>::LerpAnimation(float _d, T _ev, T _sv, std::function<void()> _cb, std::function<void(T)> _w, bool _l)
	if (CEQ(target_type, "menu")) {
		auto obj = menus[std::string(parent)];
		if (CEQ(field, "position")) {
			if (PyList_Check(values_obj)) evdata = PyList_AsTuple(values_obj); else evdata = values_obj;
			auto end_value = sf::Vector2f(PyFloat_AsDouble(PyTuple_GetItem(evdata, 0)),
										  PyFloat_AsDouble(PyTuple_GetItem(evdata, 1)));
			McRFPy_API::animations.push_back(new LerpAnimation<sf::Vector2f>(
				duration, end_value,
				obj->box.getPosition(),
				[=](){PyObject_Call(callback, PyTuple_New(0), NULL);},
				[=](sf::Vector2f v){obj->box.setPosition(v);},
				loop)
			);	
		}
		else if (CEQ(field, "size")) {
			if (PyList_Check(values_obj)) evdata = PyList_AsTuple(values_obj); else evdata = values_obj;
			auto end_value = sf::Vector2f(PyFloat_AsDouble(PyTuple_GetItem(evdata, 0)),
										  PyFloat_AsDouble(PyTuple_GetItem(evdata, 1)));
			McRFPy_API::animations.push_back(new LerpAnimation<sf::Vector2f>(
				duration, end_value,
				obj->box.getSize(),
				[=](){PyObject_Call(callback, PyTuple_New(0), NULL);},
				[=](sf::Vector2f v){obj->box.setSize(v);},
				loop)
			);
		}
		// else if (CEQ(field, "bgcolor")) { )
	}
	else if (CEQ(target_type, "sprite")) {
		if (CEQ(field, "position")) {
			auto obj = menus[std::string(parent)]->sprites[target_id];
			PyObject* evdata;
			if (PyList_Check(values_obj)) evdata = PyList_AsTuple(values_obj); else evdata = values_obj;
			auto end_value = sf::Vector2f(PyFloat_AsDouble(PyTuple_GetItem(evdata, 0)),
										  PyFloat_AsDouble(PyTuple_GetItem(evdata, 1)));
			McRFPy_API::animations.push_back(new LerpAnimation<sf::Vector2f>(duration, end_value,
				sf::Vector2f(obj.x, obj.y),
				[=](){PyObject_Call(callback, PyTuple_New(0), NULL);},
				[&](sf::Vector2f v){obj.x = v.x; obj.y = v.y;},
				loop)
			);			
		}
		else if (CEQ(field, "sprite")) {
			auto obj = menus[std::string(parent)];
			PyObject* evdata;
			if (PyList_Check(values_obj)) evdata = PyList_AsTuple(values_obj); else evdata = values_obj;
			std::vector<int> frames;
			for (int i = 0; i < PyTuple_Size(evdata); i++) {
				frames.push_back(PyLong_AsLong(PyTuple_GetItem(evdata, i)));
			}
//DiscreteAnimation(float _d, std::vector<T> _v, std::function<void()> _cb, std::function<void(T)> _w, bool _l)
			McRFPy_API::animations.push_back(new DiscreteAnimation<int>(
				duration,
				frames,
				[=](){PyObject_Call(callback, PyTuple_New(0), NULL);},
				[=](int s){obj->sprites[target_id].sprite_index = s;},
				loop)
			);
			//std::cout << "Frame animation constructed, there are now " <<McRFPy_API::animations.size() << std::endl;
		}
	}
	else if (CEQ(target_type, "entity")) {
		if (CEQ(field, "position")) {
			auto obj = grids[std::string(parent)]->entities[target_id];
			PyObject* evdata;
			if (PyList_Check(values_obj)) evdata = PyList_AsTuple(values_obj); else evdata = values_obj;
			auto end_value = sf::Vector2f(PyFloat_AsDouble(PyTuple_GetItem(evdata, 0)),
										  PyFloat_AsDouble(PyTuple_GetItem(evdata, 1)));
			McRFPy_API::animations.push_back(new LerpAnimation<sf::Vector2f>(duration, end_value,
				sf::Vector2f(obj->cGrid->indexsprite.x, obj->cGrid->indexsprite.y),
				[=](){PyObject_Call(callback, PyTuple_New(0), NULL);},
				[=](sf::Vector2f v){obj->cGrid->indexsprite.x = v.x; obj->cGrid->indexsprite.y = v.y;},
				loop)
			);			
		}
		else if (CEQ(field, "sprite")) {
			auto obj = grids[std::string(parent)];
			PyObject* evdata;
			if (PyList_Check(values_obj)) evdata = PyList_AsTuple(values_obj); else evdata = values_obj;
			std::vector<int> frames;
			for (int i = 0; i < PyTuple_Size(evdata); i++) {
				frames.push_back(PyLong_AsLong(PyTuple_GetItem(evdata, i)));
			}
//DiscreteAnimation(float _d, std::vector<T> _v, std::function<void()> _cb, std::function<void(T)> _w, bool _l)
			McRFPy_API::animations.push_back(new DiscreteAnimation<int>(
				duration,
				frames,
				[=](){PyObject_Call(callback, PyTuple_New(0), NULL);},
				[=](int s){obj->entities[target_id]->cGrid->indexsprite.sprite_index = s;},
				loop)
			);
		}
	}

    Py_INCREF(Py_None);
    return Py_None;	
}

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

PyObject* McRFPy_API::_unlockPlayerInput(PyObject* self, PyObject* args) {
	McRFPy_API::input_mode = "playerturn";
    Py_INCREF(Py_None);
    return Py_None;	
}
PyObject* McRFPy_API::_lockPlayerInput(PyObject* self, PyObject* args) {
	McRFPy_API::input_mode = "computerturnwait";
    Py_INCREF(Py_None);
    return Py_None;		
}
PyObject* McRFPy_API::_requestGridTarget(PyObject* self, PyObject* args) {
	const char* requestmode;
	if (!PyArg_ParseTuple(args, "s", &requestmode)) return NULL;
	McRFPy_API::input_mode = requestmode;
    Py_INCREF(Py_None);
    return Py_None;	
}
PyObject* McRFPy_API::_activeGrid(PyObject* self, PyObject* args) {
	return Py_BuildValue("s", McRFPy_API::active_grid.c_str());
}
PyObject* McRFPy_API::_setActiveGrid(PyObject* self, PyObject* args) {
	const char* newactivegrid;
	if (!PyArg_ParseTuple(args, "s", &newactivegrid)) return NULL;
	McRFPy_API::active_grid = newactivegrid;
    Py_INCREF(Py_None);
    return Py_None;		
}
PyObject* McRFPy_API::_inputMode(PyObject* self, PyObject* args) {
	return Py_BuildValue("s", McRFPy_API::input_mode.c_str());
}
PyObject* McRFPy_API::_turnNumber(PyObject* self, PyObject* args) {
	return Py_BuildValue("i", McRFPy_API::turn_number);
}
PyObject* McRFPy_API::_createEntity(PyObject* self, PyObject* args) {
	const char * grid_cstr, *entity_tag;
    int ti, si, x, y;
    PyObject* behavior_obj;
    if (!PyArg_ParseTuple(args, "ssiiii|O", &grid_cstr, &entity_tag, &ti, &si, &x, &y, &behavior_obj)) return NULL;
    auto e = entities.addEntity(std::string(entity_tag));
    Grid* grid_ptr = grids[grid_cstr];
	grid_ptr->entities.push_back(e);
    e->cGrid = std::make_shared<CGrid>(grid_ptr, ti, si, x, y, true);
    e->cBehavior = std::make_shared<CBehavior>(behavior_obj);
    Py_INCREF(behavior_obj);
	Py_INCREF(Py_None);
    return Py_None;
}

/*
PyObject* McRFPy_API::_listEntities(PyObject* self, PyObject* args) {
	Py_INCREF(Py_None);
    return Py_None;	
}
*/

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
