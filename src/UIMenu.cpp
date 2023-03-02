#include "UIMenu.h"
#include "Common.h"

UIMenu::UIMenu(sf::Font & _font)
: font(_font)
{
    //font = _font;
    box.setSize(sf::Vector2f(300, 400));
    box.setPosition(sf::Vector2f(300, 250));
    box.setFillColor(sf::Color(0,0,255));
}

void UIMenu::render(sf::RenderWindow & window)
{
    window.draw(box);
    for (auto& c : captions) {
        //auto s = std::string(c.getString());
        //std::cout << s << std::flush << std::endl;
        window.draw(c);
    }
    for (auto& b : buttons) { b.render(window); }
    for (auto& s: sprites) {
        auto _s = s.drawable();
        // TODO: s.move or whatever to make it's 0,0 relative to menu box
        window.draw(_s); }
}

void UIMenu::refresh()
{

}

void UIMenu::add_caption(const char* text, int tsize, sf::Color color)
{
    auto c = sf::Text();
    auto bpos = box.getPosition();

    c.setFillColor(color);
    c.setPosition(bpos.x + 10, bpos.y + next_text);
    next_text += 50;
    c.setCharacterSize(tsize);
    c.setString(text);
    c.setFont(font);
    captions.push_back(c);

}

void UIMenu::add_button(Button b)
{
    b.setPosition(box.getPosition() + sf::Vector2f(box.getSize().x / 2.0f, next_button));
    next_button += 50;
    buttons.push_back(b);
}

void UIMenu::add_sprite(IndexSprite s)
{
    sprites.push_back(s);
}

