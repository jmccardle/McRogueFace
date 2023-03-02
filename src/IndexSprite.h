#pragma once
#include "Common.h"
class GameEngine; // forward declare

class IndexSprite {
public:
    int texture_index, sprite_index, x, y;
    float scale;
    static GameEngine* game;
    sf::Sprite drawable();
    IndexSprite(int, int, int, int, float);
};
