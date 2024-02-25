#include "Button.h"

void Button::render(sf::RenderWindow & window)
{
    window.draw(rect);
    window.draw(caption);
}

Button::Button(int x, int y, int w, int h,
        sf::Color _background, sf::Color _textcolor,
        const char * _caption, sf::Font & font,
        const char * _action)
{
    rect.setPosition(sf::Vector2f(x, y));
    rect.setSize(sf::Vector2f(w, h));
    rect.setFillColor(_background);

    caption.setFillColor(_textcolor);
    caption.setPosition(sf::Vector2f(x, y));
    caption.setString(_caption);
    caption.setFont(font);

    action = _action;
}
