#include "UICaption.h"
#include "GameEngine.h"

UIDrawable* UICaption::click_at(sf::Vector2f point)
{
    if (click_callable)
    {
        if (text.getGlobalBounds().contains(point)) return this;
    }
    return NULL;
}

void UICaption::render(sf::Vector2f offset)
{
    text.move(offset);
    Resources::game->getWindow().draw(text);
    text.move(-offset);
}

PyObjectsEnum UICaption::derived_type()
{
    return PyObjectsEnum::UICAPTION;
}
