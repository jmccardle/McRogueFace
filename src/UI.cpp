#include "UI.h"
#include "Resources.h"
#include "GameEngine.h"

void UIDrawable::render()
{
    //std::cout << "Rendering base UIDrawable\n";
    render(sf::Vector2f());
}
UIFrame::UIFrame():
x(0), y(0), w(0), h(0), outline(0)
{
    children = std::make_shared<std::vector<std::shared_ptr<UIDrawable>>>();
    /*
    pyOutlineColor = NULL;
    pyFillColor = NULL;
    _outlineColor = NULL;
    _fillColor = NULL;
    */
}

UIFrame::UIFrame(float _x, float _y, float _w, float _h):
x(_x), y(_y), w(_w), h(_h), outline(0)
{
    children = std::make_shared<std::vector<std::shared_ptr<UIDrawable>>>();
    /*
    pyOutlineColor = NULL;
    pyFillColor = NULL;
    _outlineColor = NULL;
    _fillColor = NULL;
    */
}

UIFrame::~UIFrame()
{
    children.reset();
    /*
    if (pyOutlineColor) Py_DECREF(pyOutlineColor);
    else if (_outlineColor) delete _outlineColor;
    if (pyFillColor) Py_DECREF(pyFillColor);
    else if (_fillColor) delete _fillColor;
    */
}

/*
    sf::Color& fillColor(); // getter
    void fillColor(sf::Color c); // C++ setter
    void fillColor(PyObject* pyColor); // Python setter
    
    sf::Color& outlineColor(); // getter
    void outlineColor(sf::Color c); // C++ setter
    void outlineColor(PyObject* pyColor); // Python setter
*/


void UIFrame::render(sf::Vector2f offset)
{
    //std::cout << "Rendering UIFrame w/ offset " << offset.x << ", " << offset.y << "\n";
    //std::cout << "position = " << x << ", " << y << "\n";
    box.move(offset);
    Resources::game->getWindow().draw(box);
    box.move(-offset);
    //sf::RectangleShape box = sf::RectangleShape(sf::Vector2f(w,h));
    //sf::Vector2f pos = sf::Vector2f(x, y);
    //box.setPosition(offset + pos);
    //if (_fillColor) { box.setFillColor(fillColor()); }
    //if (_outlineColor) { box.setOutlineColor(outlineColor()); }
    //box.setOutlineThickness(outline);
    //Resources::game->getWindow().draw(box);
    for (auto drawable : *children) {
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
