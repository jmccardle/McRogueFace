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
#include <list>

// implementation required to link templates
#include "Animation.h"

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
    static std::map<std::string, UIMenu*> menus;
    static EntityManager entities; // this is also kinda good, entities not on the current grid can still act (like monsters following you through doors??)
    static std::map<std::string, Grid*> grids;
    static std::list<Animation*> animations;
    static std::vector<sf::SoundBuffer> soundbuffers;
    static sf::Music music;
    static sf::Sound sfx;
    
    static std::shared_ptr<Entity> player;

    static std::map<std::string, PyObject*> callbacks;

    // Jank Python Method Exposures
    static PyObject* _createMenu(PyObject*, PyObject*); // creates a new menu object in McRFPy_API::menus
    static PyObject* _listMenus(PyObject*, PyObject*);
    static PyObject* _modMenu(PyObject*, PyObject*);

    static PyObject* _createCaption(PyObject*, PyObject*); // calls menu.add_caption
    static PyObject* _createButton(PyObject*, PyObject*);
    static PyObject* _createTexture(PyObject*, PyObject*);
    static PyObject* _listTextures(PyObject*, PyObject*);
    static PyObject* _createSprite(PyObject*, PyObject*);

    // use _listMenus, probably will not implement
    //static PyObject* _listCaptions(PyObject*, PyObject*);
    //static PyObject* _listButtons(PyObject*, PyObject*);

    static PyObject* _createEntity(PyObject*, PyObject*);
    //static PyObject* _listEntities(PyObject*, PyObject*);

    static PyObject* _createGrid(PyObject*, PyObject*);
    static PyObject* _listGrids(PyObject*, PyObject*);
    static PyObject* _modGrid(PyObject*, PyObject*);

    static PyObject* _createAnimation(PyObject*, PyObject*);
    
    static PyObject* _registerPyAction(PyObject*, PyObject*);
    static PyObject* _registerInputAction(PyObject*, PyObject*);
    
    static PyObject* _createSoundBuffer(PyObject*, PyObject*);
    static PyObject* _loadMusic(PyObject*, PyObject*);
    static PyObject* _setMusicVolume(PyObject*, PyObject*);
    static PyObject* _setSoundVolume(PyObject*, PyObject*);
    static PyObject* _playSound(PyObject*, PyObject*);
    static PyObject* _getMusicVolume(PyObject*, PyObject*);
    static PyObject* _getSoundVolume(PyObject*, PyObject*);
    
    // allow all player actions (items, menus, movement, combat)
    static PyObject* _unlockPlayerInput(PyObject*, PyObject*);
    // disallow player actions (animating enemy actions)
    static PyObject* _lockPlayerInput(PyObject*, PyObject*);
    // prompt C++/Grid Objects to callback with a target Entity or grid space
    static PyObject* _requestGridTarget(PyObject*, PyObject*);
    // string for labeling the map
    static std::string active_grid;
    static PyObject* _activeGrid(PyObject*, PyObject*);
    static PyObject* _setActiveGrid(PyObject*, PyObject*);
    // string for prompting input
    static std::string input_mode;
    static PyObject* _inputMode(PyObject*, PyObject*);
    // turn cycle
    static int turn_number;
    static PyObject* _turnNumber(PyObject*, PyObject*);
    static PyObject* _refreshFov(PyObject*, PyObject*);
    static bool do_camfollow;
    static void camFollow();
    static PyObject* _camFollow(PyObject*, PyObject*);

    static PyObject* _sceneUI(PyObject*, PyObject*);
    
    // accept keyboard input from scene
    static sf::Vector2i cursor_position;
    static void player_input(int, int);
    static void computerTurn();
    static void playerTurn();

    // Jank Functionality
    static UIMenu* createMenu(int posx, int posy, int sizex, int sizey);
    static void createCaption(std::string menukey, std::string text, int fontsize, sf::Color textcolor);
    static void createButton(std::string menukey, int x, int y, int w, int h, sf::Color bgcolor, sf::Color textcolor, std::string caption, std::string action);
    static void createSprite(std::string menukey, int ti, int si, float x, float y, float scale);
    static int createTexture(std::string filename, int grid_size, int grid_width, int grid_height);
    //static void playSound(const char * filename);
    //static void playMusic(const char * filename);
    
    static void doAction(std::string);

    //    McRFPy_API(GameEngine*);

    // API functionality - use from C++ directly

    //void spawnEntity(int tex_index, int grid_x, int grid_y, PyObject* script);

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
