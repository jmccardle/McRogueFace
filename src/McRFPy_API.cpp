#include "McRFPy_API.h"
#include "platform.h"
#include "GameEngine.h"
#include "Grid.h"

// static class members...?
std::vector<UIMenu> McRFPy_API::menus;
std::vector<Grid> McRFPy_API::grids;

static PyMethodDef mcrfpyMethods[] = {
    {"drawSprite", McRFPy_API::_drawSprite, METH_VARARGS,
        "Draw a sprite (index, x, y)"},

    {"createMenu", McRFPy_API::_createMenu, METH_VARARGS,
        "Create a new uimenu (x, y, w, h)"},

    {"listMenus", McRFPy_API::_listMenus, METH_VARARGS,
        "return a list of existing menus"},

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

    int posx, posy, sizex, sizey;
    if (!PyArg_ParseTuple(args, "iiii", &posx, &posy, &sizex, &sizey)) return NULL;
    menus.push_back(createMenu(posx, posy, sizex, sizey));
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
    for (int i = 0; i < menus.size(); i++) {
        auto p = menus[i].box.getPosition();
        auto s = menus[i].box.getSize();
        PyObject* menu_args = Py_BuildValue("(iiii)", p.x, p.y, s.x, s.y);
        // * need uimenu_type (imported already to __main__)
        PyObject* menuobj = PyObject_CallObject((PyObject*) uimenu_type, menu_args);

        // Loop: Convert Button objects to Python Objects
        PyObject* button_list = PyObject_GetAttrString(menuobj, "buttons");
        for(auto& b : menus[i].buttons) {
            auto bp = b.rect.getPosition();
            auto bs = b.rect.getSize();
            auto bg = b.rect.getFillColor();
            auto bf = b.caption.getFillColor();
            PyObject* btn_args = Py_BuildValue("(iiii(iii)(iii)ss)",
                bp.x, bp.y, bs.x, bs.y,
                bg.r, bg.g, bg.b,
                bf.r, bf.g, bf.b,
                b.caption.getString().toAnsiString().c_str(),
                b.action.c_str());
            // * need btn_type
            PyObject* buttonobj = PyObject_CallObject((PyObject*) btn_type, btn_args);
            PyList_Append(button_list, buttonobj);
        }

        // Loop: Convert Caption objects to Python Objects
        PyObject* caption_list = PyObject_GetAttrString(menuobj, "captions");
        for (auto& c : menus[i].captions) {
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
        for (auto& s : menus[i].sprites) {
            PyObject* spr_args = Py_BuildValue("iiii",
                s.texture_index, s.sprite_index, s.x, s.y);
        }

        PyList_SET_ITEM(menulist, i, menuobj);
    }
    return menulist;
}

UIMenu McRFPy_API::createMenu(int posx, int posy, int sizex, int sizey) {
    auto m = UIMenu(game->getFont());
    m.box.setPosition(sf::Vector2f(posx, posy));
    m.box.setSize(sf::Vector2f(sizex, sizey));
    return m;
}
