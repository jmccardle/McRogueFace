#pragma once

// macros for scene input
#define ACTION(X, Y) (name.compare(X) == 0 && type.compare(Y) == 0)
#define ACTIONONCE(X) ((name.compare(X) == 0 && type.compare("start") == 0 && !actionState[name]))
#define ACTIONAFTER(X) ((name.compare(X) == 0 && type.compare("end") == 0))

#include "Common.h"
#include <list>
#include "UI.h"
#include "PyCallable.h"
//#include "GameEngine.h"

class GameEngine; // forward declare

class Scene
{
protected:
    bool hasEnded = false;
    bool paused = false;
    std::map<int, std::string> actions;
    std::map<std::string, bool> actionState;
    GameEngine* game;

    void simulate(int);
    void registerAction(int, std::string);


public:
    //Scene();
    Scene(GameEngine*);
    virtual void update() = 0;
    virtual void render() = 0;
    virtual void doAction(std::string, std::string) = 0;
    bool hasAction(std::string);
    bool hasAction(int);
    std::string action(int);


    std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>> ui_elements;

    //PyObject* key_callable;
    std::unique_ptr<PyKeyCallable> key_callable;
    void key_register(PyObject*);
    void key_unregister();

    // #118: Scene-level UIDrawable-like properties for animations/transitions
    sf::Vector2f position{0.0f, 0.0f};  // Offset applied to all ui_elements
    bool visible = true;                 // Controls rendering of scene
    float opacity = 1.0f;                // Applied to all ui_elements (0.0-1.0)

    // Animation support for scene properties
    bool setProperty(const std::string& name, float value);
    bool setProperty(const std::string& name, const sf::Vector2f& value);
    float getProperty(const std::string& name) const;
};
