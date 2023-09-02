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

PyObjectsEnum UIFrame::derived_type()
{
    return PyObjectsEnum::UIFRAME;
}

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

PyObjectsEnum UICaption::derived_type()
{
    return PyObjectsEnum::UICAPTION;
}

PyObjectsEnum UISprite::derived_type()
{
    return PyObjectsEnum::UISPRITE;
}

PyObject* py_instance(std::shared_ptr<UIDrawable> source)
{
    // takes a UI drawable, calls its derived_type virtual function, and builds a Python object based on the return value.
    using namespace mcrfpydef;
    PyObject* newobj; 
    switch (source->derived_type())
    {
        case PyObjectsEnum::UIFRAME:
            {
                PyUIFrameObject* o = (PyUIFrameObject*)PyUIFrameType.tp_alloc(&PyUIFrameType, 0);
                if (o)
                    o->data = std::static_pointer_cast<UIFrame>(source);
                newobj = (PyObject*)o;
                break;
            }
        /* not yet implemented
        case PyObjectsEnum::UICAPTION:
            PyUICaptionObject* o = (PyUICaptionObject*)PyUICaptionType.tp_alloc(&PyUICaptionType, 0);
            if (o)
                o->data = std::static_pointer_cast<UICaption>(source);
            break;
        case PyObjectsEnum::UISPRITE:
            PyUISpriteObject* o = (PyUISpriteObject*)PyUISpriteType.tp_alloc(&PyUISpriteType, 0);
            if (o)
                o->data = std::static_pointer_cast<UISprite>(source);
            break;
        */
        default:
            return NULL;
            break;
    }

    return newobj;
}
