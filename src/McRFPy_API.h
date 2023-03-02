#pragma once
#include "Common.h"
#include "Entity.h"
//#include "EntityManager.h"
//#include "Scene.h"
//#include "GameEngine.h" // can't - need forward declaration
//#include "ActionCode.h"
#include "Python.h"
#include "UIMenu.h"
#include "Grid.h"
#include "IndexSprite.h"
#include "EntityManager.h"

class GameEngine; // forward declared (circular members)

class McRFPy_API
{
private:
    static const int texture_size = 16, // w & h (pixels) of one sprite in the tex
        texture_width = 12, texture_height = 11, // w & h sprite/frame count
        texture_sprite_count = 11 * 12; // t_width * t_height, minus blanks?

    // TODO: this is wrong, load resources @ GameEngineSprite sprite;
    // sf::Texture texture;

    //std::vector<PyMethodDef> mcrfpyMethodsVector;
    //static PyObject* PyInit_mcrfpy();

    McRFPy_API();

public:
    inline static sf::Sprite sprite;
    inline static sf::Texture texture;
    static void setSpriteTexture(int);
    inline static GameEngine* game;
    static void api_init();
    static void api_shutdown();
    // Python API functionality - use mcrfpy.* in scripts
    static PyObject* _drawSprite(PyObject*, PyObject*);
    static void REPL_device(FILE * fp, const char *filename);
    static void REPL();

    // Jank mode engage: let the API hold data for Python to hack on
    static std::vector<UIMenu> menus;
    EntityManager entities; // this is also kinda good, entities not on the current grid can still act (like monsters following you through doors??)
    static std::vector<Grid> grids;

    // Jank Python Method Exposures
    static PyObject* _createMenu(PyObject*, PyObject*); // creates a new menu object in McRFPy_API::menus
    static PyObject* _listMenus(PyObject*, PyObject*);
    //static PyObject* _createCaption(PyObject*, PyObject*); // calls menu.add_caption
    //static PyObject* _listCaptions(PyObject*, PyObject*);
    //static PyObject* _createButton(PyObject*, PyObject*);
    //static PyObject* _listButtons(PyObject*, PyObject*);
    //static PyObject* _createEntity(PyObject*, PyObject*);
    //static PyObject* _listEntities(PyObject*, PyObject*);
    //static PyObject* _createGrid(PyObject*, PyObject*);
    //static PyObject* _listGrids(PyObject*, PyObject*);
    //static PyObject* _createSprite(PyObject*, PyObject*);

    // Jank Functionality
    static UIMenu createMenu(int posx, int posy, int sizex, int sizey);
    //static Button createButton(UIMenu & menu, int x, int y, int w, int h);
    //static sf::Sprite createSprite(int tex_index, int x, int y);
    //static void playSound(const char * filename);
    //static void playMusic(const char * filename);


    //    McRFPy_API(GameEngine*);

    // API functionality - use from C++ directly

    //void spawnEntity(int tex_index, int grid_x, int grid_y, PyObject* script);

    // test function, do not use in production
    static void drawSprite(int tex_index, int grid_x, int grid_y);

    static void executeScript(std::string);
    static void executePyString(std::string);
};

/*
static PyMethodDef mcrfpyMethods[] = {
    {"drawSprite", McRFPy_API::_drawSprite, METH_VARARGS,
        "Draw a sprite (index, x, y)"},
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
*/
