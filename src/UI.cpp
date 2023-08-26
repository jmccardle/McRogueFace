#include "UI.h"
#include "Resources.h"
#include "GameEngine.h"

void UIDrawable::render()
{
    //std::cout << "Rendering base UIDrawable\n";
    render(sf::Vector2f());
}

void UIFrame::render(sf::Vector2f offset)
{
    //std::cout << "Rendering UIFrame w/ offset\n";
    box.move(offset);
    Resources::game->getWindow().draw(box);
    box.move(-offset);
    for (auto drawable : children) {
        drawable->render(offset + box.getPosition());
    }
}

void UICaption::render(sf::Vector2f offset)
{
    //std::cout << "Rendering Caption with offset\n";
    text.move(offset);
    Resources::game->getWindow().draw(text);
    text.move(-offset);
}

void UISprite::render(sf::Vector2f offset)
{
    sprite.move(offset);
    Resources::game->getWindow().draw(sprite);
    sprite.move(-offset);
}