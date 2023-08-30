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
    pyOutlineColor = NULL;
    pyFillColor = NULL;
    _outlineColor = NULL;
    _fillColor = NULL;
}

UIFrame::UIFrame(float _x, float _y, float _w, float _h):
x(_x), y(_y), w(_w), h(_h), outline(0)
{
    pyOutlineColor = NULL;
    pyFillColor = NULL;
    _outlineColor = NULL;
    _fillColor = NULL;
}

UIFrame::~UIFrame()
{
    if (pyOutlineColor) { Py_DECREF(pyOutlineColor); }
    else { if (_outlineColor) { delete _outlineColor; } }
    if (pyFillColor) { Py_DECREF(pyFillColor); }
    else { if (_fillColor) { delete _fillColor; } }
}

/*
    sf::Color& fillColor(); // getter
    void fillColor(sf::Color c); // C++ setter
    void fillColor(PyObject* pyColor); // Python setter
    
    sf::Color& outlineColor(); // getter
    void outlineColor(sf::Color c); // C++ setter
    void outlineColor(PyObject* pyColor); // Python setter
*/

sf::Color UIFrame::fillColor()
{
    if (_fillColor == NULL) return sf::Color();
    return *_fillColor;
}

void UIFrame::fillColor(sf::Color c)
{
    if (pyFillColor) { Py_DECREF(pyFillColor); }
    else { delete _fillColor; }
    _fillColor = new sf::Color(c.r, c.g, c.b, c.a);
    pyFillColor = NULL;
}

void UIFrame::fillColor(PyColorObject* pyColor)
{
    if (pyFillColor) { Py_DECREF(pyFillColor); }
    else { delete _fillColor; }
    Py_INCREF(pyColor);
    pyFillColor = pyColor;
    _fillColor = &(pyFillColor->color);
}

sf::Color UIFrame::outlineColor()
{
    if (_outlineColor == NULL) return sf::Color();
    return *_outlineColor;
}

void UIFrame::outlineColor(sf::Color c)
{
    if (pyOutlineColor) { Py_DECREF(pyOutlineColor); }
    else { delete _outlineColor; }
    _outlineColor = new sf::Color(c.r, c.g, c.b, c.a);
    pyOutlineColor = NULL;
}

void UIFrame::outlineColor(PyColorObject* pyColor)
{
    if (pyOutlineColor) { Py_DECREF(pyOutlineColor); }
    else { delete _outlineColor; }
    Py_INCREF(pyColor);
    pyOutlineColor = pyColor;
    _outlineColor = &(pyOutlineColor->color);
}

void UIFrame::render(sf::Vector2f offset)
{
    //std::cout << "Rendering UIFrame w/ offset " << offset.x << ", " << offset.y << "\n";
    //std::cout << "position = " << x << ", " << y << "\n";
    //box.move(offset);
    //Resources::game->getWindow().draw(box);
    //box.move(-offset);
    sf::RectangleShape box = sf::RectangleShape(sf::Vector2f(w,h));
    sf::Vector2f pos = sf::Vector2f(x, y);
    box.setPosition(offset + pos);
    if (_fillColor) { box.setFillColor(fillColor()); }
    if (_outlineColor) { box.setOutlineColor(outlineColor()); }
    box.setOutlineThickness(outline);
    Resources::game->getWindow().draw(box);
    for (auto drawable : children) {
        drawable->render(offset + pos);
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