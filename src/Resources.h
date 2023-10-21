#pragma once
#include "Common.h"
#include <list>
#include "UI.h"

class GameEngine; // forward declared

class Resources
{
public:
    static sf::Font font;
    static GameEngine* game;
};
