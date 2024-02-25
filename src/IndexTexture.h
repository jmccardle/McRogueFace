#pragma once
#include "Common.h"
class GameEngine; // forward declare

class IndexTexture {
public:
    sf::Texture texture;
    int grid_size, grid_width, grid_height;
    static GameEngine* game;
    sf::IntRect spriteCoordinates(int);
    IndexTexture(sf::Texture, int, int, int);
};
