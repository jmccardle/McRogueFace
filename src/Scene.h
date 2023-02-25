#pragma once

// macros for scene input
#define ACTION(X, Y) (name.compare(X) == 0 && type.compare(Y) == 0)
#define ACTIONONCE(X) ((name.compare(X) == 0 && type.compare("start") == 0 && !actionState[name]))

#include "Common.h"
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
    virtual void sRender() = 0;
    virtual void doAction(std::string, std::string) = 0;
    bool hasAction(std::string);
    bool hasAction(int);
    std::string action(int);

};
