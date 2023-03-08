#pragma once

#include "Common.h"

class Button
{

protected:

public:
    // TODO / JankMode: setter & getter for these three fields
    // were protected, but directly changing them should be...fine?
    sf::RectangleShape rect;
    sf::Text caption;
    std::string action;

    Button() {};
    Button(int x, int y, int w, int h,
        sf::Color _background, sf::Color _textcolor,
        const char * _caption, sf::Font & font,
        const char * _action);
    void setPosition(sf::Vector2f v) { rect.setPosition(v); caption.setPosition(v); }
    void setSize(sf::Vector2f & v) { rect.setSize(v); }
    void setBackground(sf::Color c) { rect.setFillColor(c); }
    void setCaption(std::string & s) { caption.setString(s); }
    void setTextColor(sf::Color c) { caption.setFillColor(c); }
    void render(sf::RenderWindow & window);
    auto contains(sf::Vector2i p) { return rect.getGlobalBounds().contains(p.x, p.y); }
    auto contains(sf::Vector2f rel, sf::Vector2i p) { 
		return rect.getGlobalBounds().contains(p.x - rel.x, p.y - rel.y);
	}
    auto getAction() { return action; }

private:
};
