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
    //inline static sf::Sprite sprite;
    //inline static sf::Texture texture;
    //static void setSpriteTexture(int);
    inline static GameEngine* game;
    static void api_init();
    static void api_init(const McRogueFaceConfig& config);
    static PyStatus init_python_with_config(const McRogueFaceConfig& config);
    static void api_shutdown();
    // Python API functionality - use mcrfpy.* in scripts
    //static PyObject* _drawSprite(PyObject*, PyObject*);
    static void REPL_device(FILE * fp, const char *filename);
    static void REPL();

    static std::vector<sf::SoundBuffer>* soundbuffers;
    static sf::Music* music;
    static sf::Sound* sfx;
    
    
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

    // timer control
    static PyObject* _setTimer(PyObject*, PyObject*);
    static PyObject* _delTimer(PyObject*, PyObject*);

    static PyObject* _exit(PyObject*, PyObject*);
    static PyObject* _setScale(PyObject*, PyObject*);

    // accept keyboard input from scene
    static sf::Vector2i cursor_position;
    

    static void executeScript(std::string);
    static void executePyString(std::string);
    
    // Helper to mark scenes as needing z_index resort
    static void markSceneNeedsSort();
    
    // Name-based finding methods
    static PyObject* _find(PyObject*, PyObject*);
    static PyObject* _findAll(PyObject*, PyObject*);
    
    // Profiling/metrics
    static PyObject* _getMetrics(PyObject*, PyObject*);

    // Benchmark logging (#104)
    static PyObject* _startBenchmark(PyObject*, PyObject*);
    static PyObject* _endBenchmark(PyObject*, PyObject*);
    static PyObject* _logBenchmark(PyObject*, PyObject*);

    // Developer console
    static PyObject* _setDevConsole(PyObject*, PyObject*);

    // Scene lifecycle management for Python Scene objects
    static void triggerSceneChange(const std::string& from_scene, const std::string& to_scene);
    static void updatePythonScenes(float dt);
    static void triggerResize(int width, int height);

    // Exception handling - signal game loop to exit on unhandled Python exceptions
    static std::atomic<bool> exception_occurred;
    static std::atomic<int> exit_code;
    static void signalPythonException();  // Called by exception handlers
    static bool shouldExit();             // Checked by game loop
};
