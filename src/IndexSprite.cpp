#include "IndexSprite.h"
#include "GameEngine.h"

//int texture_index, sprite_index, x, y;

GameEngine* IndexSprite::game;

sf::Sprite IndexSprite::drawable()
{
    sf::Sprite s;
    auto& tex = IndexSprite::game->textures[texture_index];
    s.setTexture(tex.texture);
    s.setPosition(sf::Vector2f(x, y));
    s.setTextureRect(tex.spriteCoordinates(sprite_index));
    return s;
}
