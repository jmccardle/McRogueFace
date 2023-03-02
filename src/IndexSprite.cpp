#include "IndexSprite.h"
#include "GameEngine.h"

//int texture_index, sprite_index, x, y;

GameEngine* IndexSprite::game;

sf::Sprite IndexSprite::drawable()
{
    sf::Sprite s;
    auto& tex = IndexSprite::game->textures[texture_index];
    s.setTexture(tex.texture);
    s.setScale(sf::Vector2f(scale, scale));
    s.setPosition(sf::Vector2f(x, y));
    s.setTextureRect(tex.spriteCoordinates(sprite_index));
    return s;
}

IndexSprite::IndexSprite(int _ti, int _si, int _x, int _y, float _s):
    texture_index(_ti), sprite_index(_si), x(_x), y(_y), scale(_s) {}
