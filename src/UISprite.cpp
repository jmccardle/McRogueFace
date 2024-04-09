#include "UISprite.h"

UIDrawable* UISprite::click_at(sf::Vector2f point)
{
    if (click_callable)
    {
        if(sprite.getGlobalBounds().contains(point)) return this;
    }
    return NULL;
}

UISprite::UISprite() {}

UISprite::UISprite(std::shared_ptr<PyTexture> _ptex, int _sprite_index, sf::Vector2f _pos, float _scale)
: ptex(_ptex), sprite_index(_sprite_index)
{
    sprite = ptex->sprite(sprite_index, _pos, sf::Vector2f(_scale, _scale));
}

void UISprite::render(sf::Vector2f offset)
{
    sprite.move(offset);
    Resources::game->getWindow().draw(sprite);
    sprite.move(-offset);
}

void UISprite::render(sf::Vector2f offset, sf::RenderTexture& target)
{
    sprite.move(offset);
    target.draw(sprite);
    sprite.move(-offset);
}

void UISprite::setPosition(sf::Vector2f pos)
{
    sprite.setPosition(pos);
}

void UISprite::setScale(sf::Vector2f s)
{
    sprite.setScale(s);
}

void UISprite::setTexture(std::shared_ptr<PyTexture> _ptex, int _sprite_index)
{
    ptex = _ptex;
    if (_sprite_index != -1) // if you are changing textures, there's a good chance you need a new index too
        sprite_index = _sprite_index;
    sprite = ptex->sprite(sprite_index, sprite.getPosition(), sprite.getScale());
}

void UISprite::setSpriteIndex(int _sprite_index)
{
    sprite_index = _sprite_index;
    sprite = ptex->sprite(sprite_index, sprite.getPosition(), sprite.getScale());
}

sf::Vector2f UISprite::getScale()
{
    return sprite.getScale();
}

sf::Vector2f UISprite::getPosition()
{
    return sprite.getPosition();
}

std::shared_ptr<PyTexture> UISprite::getTexture()
{
    return ptex;
}

int UISprite::getSpriteIndex()
{
    return sprite_index;
}

PyObjectsEnum UISprite::derived_type()
{
    return PyObjectsEnum::UISPRITE;
}
