#include "McRFPy_API.h"
#include "platform.h"
#include "GameEngine.h"
#include "Grid.h"

// static class members...?
std::map<std::string, UIMenu*> McRFPy_API::menus;
std::map<std::string, Grid*> McRFPy_API::grids;

static PyMethodDef mcrfpyMethods[] = {
    {"drawSprite", McRFPy_API::_drawSprite, METH_VARARGS,
        "Draw a sprite (index, x, y)"},

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

    {NULL, NULL, 0, NULL}
};

static PyModuleDef mcrfpyModule = {
    PyModuleDef_HEAD_INIT, "mcrfpy", NULL, -1, mcrfpyMethods,
    NULL, NULL, NULL, NULL
};

// Module initializer fn, passed to PyImport_AppendInittab
PyObject* PyInit_mcrfpy()
{
    return PyModule_Create(&mcrfpyModule);
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
        narrow_string(executable_path() + L"/Python311").c_str());

    status = PyConfig_SetBytesString(&config, &config.program_name,
                                     program_name);

    // under Windows, the search paths are correct; under Linux, they need manual insertion
#if __PLATFORM_SET_PYTHON_SEARCH_PATHS == 1
    config.module_search_paths_set = 1;
	
	// search paths for python libs/modules/scripts
    const wchar_t* str_arr[] = {
        L"/scripts",
        L"/Python311/lib.linux-x86_64-3.11",
	    L"/Python311",
        L"/Python311/Lib",
        L"/venv/lib/python3.11/site-packages"
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

// functionality
void McRFPy_API::drawSprite(int tex_index, int grid_x, int grid_y)
{
    setSpriteTexture(tex_index);
    sprite.setPosition(
            sf::Vector2f(grid_x * texture_size, 
                         grid_y * texture_size)
            );
    game->getWindow().draw(sprite);
}

// python connection
PyObject* McRFPy_API::_drawSprite(PyObject *self, PyObject *args)
{
    int ti, gx, gy;
    if (!PyArg_ParseTuple(args, "iii", &ti, &gx, &gy)) return NULL;
    drawSprite(ti, gx, gy);

    // return None correctly
    Py_INCREF(Py_None);
    return Py_None;
}

void McRFPy_API::api_init() {

    // build API exposure before python initialization
    PyImport_AppendInittab("mcrfpy", PyInit_mcrfpy);
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
            PyObject* spr_args = Py_BuildValue("(iiii)",
                s.texture_index, s.sprite_index, s.x, s.y);
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
    int ti, si, x, y;
    float s;
    if (!PyArg_ParseTuple(args, "siiiif", &menu_cstr, &ti, &si, &x, &y, &s)) return NULL;
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

void McRFPy_API::createSprite(std::string menukey, int ti, int si, int x, int y, float scale) {
    auto menu = menus[menukey];
    auto s = IndexSprite(ti, si, x, y, scale);
    menu->add_sprite(s);
}

int McRFPy_API::createTexture(std::string filename, int grid_size, int grid_width, int grid_height) {
    sf::Texture t;
    t.loadFromFile(filename.c_str());
    t.setSmooth(false);
    auto indextex = IndexTexture(t, grid_size, grid_width, grid_height);
    game->textures.push_back(indextex);

    return game->textures.size() - 1;
}
