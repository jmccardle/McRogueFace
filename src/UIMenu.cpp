#include "UIMenu.h"
#include "Common.h"
#include "Resources.h"

UIMenu::UIMenu(sf::Font & _font)
: font(_font)
{
    //font = _font;
    box.setSize(sf::Vector2f(300, 400));
    box.setPosition(sf::Vector2f(300, 250));
    box.setFillColor(sf::Color(0,0,255));
}

UIMenu::UIMenu()
: font(Resources::font)
{
    box.setSize(sf::Vector2f(300, 400));
    box.setPosition(sf::Vector2f(300, 250));
    box.setFillColor(sf::Color(0,0,255));   
}

void UIMenu::render(sf::RenderWindow & window)
{
    window.draw(box);
    for (auto& s: sprites) {
        auto _s = s.drawable();
        //std::cout << "Sprite has values " << s.x << ", " << s.y << std::endl;
        //std::cout << "Drawable generated @ " << _s.getPosition().x << ", " << _s.getPosition().y << std::endl;
        _s.move(box.getPosition());
        //std::cout << "Moved by  " << box.getPosition().x << ", " << box.getPosition().y << std::endl;
        //std::cout << "Render UIMenu Sprite @ " << _s.getPosition().x << ", " << _s.getPosition().y << std::endl;
        window.draw(_s);
    }
    for (auto& c : captions) {
        //auto s = std::string(c.getString());
        //std::cout << s << std::flush << std::endl;
        c.move(box.getPosition());
        window.draw(c);
        c.move(-box.getPosition());
    }
    for (auto& b : buttons) { 
		//b.render(window); 
		b.setPosition(box.getPosition() + b.rect.getPosition());
		//b.caption.setPosition(box.getPosition() + b.caption.getPosition());
		b.render(window);
		b.setPosition(b.rect.getPosition() - box.getPosition());
		//b.caption.setPosition(b.caption.getPosition() - box.getPosition());
	}
}

void UIMenu::refresh()
{

}

void UIMenu::add_caption(const char* text, int tsize, sf::Color color)
{
    auto c = sf::Text();
    //auto bpos = box.getPosition();

    c.setFillColor(color);
    c.setPosition(10, next_text);
    next_text += 50;
    c.setCharacterSize(tsize);
    c.setString(text);
    c.setFont(font);
    captions.push_back(c);

}

void UIMenu::add_button(Button b)
{
    b.setPosition(sf::Vector2f(box.getSize().x / 2.0f, next_button));
    next_button += 50;
    buttons.push_back(b);
}

void UIMenu::add_sprite(IndexSprite s)
{
	//std::cout << "Adding sprite to UIMenu x,y " << s.x << ", " << s.y << std::endl;
    sprites.push_back(s);
}

