#pragma once
#include "Common.h"
class GameEngine; // forward declare

class IndexSprite {
public:
    int texture_index, sprite_index;
    float x, y;
    float scale;
    static GameEngine* game;
    sf::Sprite drawable();
    IndexSprite(int, int, float, float, float);
};
