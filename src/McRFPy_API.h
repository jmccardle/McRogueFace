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
    //static PyObject* _drawSprite(PyObject*, PyObject*);
    static void REPL_device(FILE * fp, const char *filename);
    static void REPL();

    // Jank mode engage: let the API hold data for Python to hack on
    //static std::map<std::string, UIMenu*> menus;
    //static EntityManager entities; // this is also kinda good, entities not on the current grid can still act (like monsters following you through doors??)
    //static std::map<std::string, Grid*> grids;
    //static std::list<Animation*> animations;
    static std::vector<sf::SoundBuffer> soundbuffers;
    static sf::Music music;
    static sf::Sound sfx;
    
    static std::shared_ptr<Entity> player;

    static std::map<std::string, PyObject*> callbacks;
    static PyObject* _registerPyAction(PyObject*, PyObject*);
    static PyObject* _registerInputAction(PyObject*, PyObject*);
    
    static PyObject* _createSoundBuffer(PyObject*, PyObject*);
    static PyObject* _loadMusic(PyObject*, PyObject*);
    static PyObject* _setMusicVolume(PyObject*, PyObject*);
    static PyObject* _setSoundVolume(PyObject*, PyObject*);
    static PyObject* _playSound(PyObject*, PyObject*);
    static PyObject* _getMusicVolume(PyObject*, PyObject*);
    static PyObject* _getSoundVolume(PyObject*, PyObject*);
    
    static PyObject* _sceneUI(PyObject*, PyObject*);

    // scene control
    static PyObject* _setScene(PyObject*, PyObject*);
    static PyObject* _currentScene(PyObject*, PyObject*);
    static PyObject* _createScene(PyObject*, PyObject*);
    static PyObject* _keypressScene(PyObject*, PyObject*); 
    // accept keyboard input from scene
    static sf::Vector2i cursor_position;
    static void player_input(int, int);
    static void computerTurn();
    static void playerTurn();
    
    static void doAction(std::string);

    static void executeScript(std::string);
    static void executePyString(std::string);
};
