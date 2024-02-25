#pragma once

#include "Common.h"
#include "Button.h"
#include "IndexSprite.h"

class UIMenu
{
public:
    //UIMenu() {};
    sf::Font & font;
    UIMenu(sf::Font & _font);
    UIMenu();
    std::vector<sf::Text> captions;
    std::vector<Button> buttons;
    std::vector<IndexSprite> sprites;
    
    /* idea: */ //std::vector<UIDrawable> children; // on the UIBox class?
    
    sf::RectangleShape box;
    bool visible = false;
    int next_text = 10;
    int next_button = 10;

    void render(sf::RenderWindow & window);
    void refresh();
    void add_caption(const char* text, int size, sf::Color color);
    void add_button(Button b);
    void add_sprite(IndexSprite s);


protected:

private:



};
