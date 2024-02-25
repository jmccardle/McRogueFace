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

UISprite::UISprite() {}

UISprite::UISprite(IndexTexture* _itex, int _sprite_index, float x = 0.0, float y = 0.0, float s = 1.0)
: itex(_itex), sprite_index(_sprite_index)
{
    sprite.setTexture(_itex->texture);
    sprite.setTextureRect(_itex->spriteCoordinates(_sprite_index));
    sprite.setPosition(sf::Vector2f(x, y));
    sprite.setScale(sf::Vector2f(s, s));
}

UISprite::UISprite(IndexTexture* _itex, int _sprite_index, sf::Vector2f pos, float s = 1.0)
: itex(_itex), sprite_index(_sprite_index)
{
    sprite.setTexture(_itex->texture);
    sprite.setTextureRect(_itex->spriteCoordinates(_sprite_index));
    sprite.setPosition(pos);
    sprite.setScale(sf::Vector2f(s, s));
}

//void UISprite::update()
//{
    //auto& tex = Resources::game->textures[texture_index];
    //sprite.setTexture(tex.texture);
    //sprite.setScale(sf::Vector2f(scale, scale));
    //sprite.setPosition(sf::Vector2f(x, y));
    //std::cout << "Drawable position: " << x << ", " << y << " -> " << s.getPosition().x << ", " << s.getPosition().y << std::endl;
    //sprite.setTextureRect(tex.spriteCoordinates(sprite_index));
//}

void UISprite::render(sf::Vector2f offset)
{
    sprite.move(offset);
    Resources::game->getWindow().draw(sprite);
    sprite.move(-offset);
}

void UISprite::setPosition(float x, float y)
{
    setPosition(sf::Vector2f(x, y));
}

void UISprite::setPosition(sf::Vector2f pos)
{
    sprite.setPosition(pos);
}

void UISprite::setScale(float s)
{
    sprite.setScale(sf::Vector2f(s, s));
}

PyObjectsEnum UICaption::derived_type()
{
    return PyObjectsEnum::UICAPTION;
}

PyObjectsEnum UISprite::derived_type()
{
    return PyObjectsEnum::UISPRITE;
}

PyObject* DEFUNCT_py_instance(std::shared_ptr<UIDrawable> source)
{
    // takes a UI drawable, calls its derived_type virtual function, and builds a Python object based on the return value.
    using namespace mcrfpydef;

    PyObject* newobj = NULL; 
    std::cout << "py_instance called\n";
    switch (source->derived_type())
    {
        case PyObjectsEnum::UIFRAME:
        {
            std::cout << "UIFRAME case\n" << std::flush;
            PyTypeObject* UIFrameType = &PyUIFrameType;
            //std::cout << "tp_alloc\n" << std::flush;
            //PyObject* _o = UIFrameType->tp_alloc(UIFrameType, 0);
            //std::cout << "reinterpret_cast\n" << std::flush;
            //auto o = reinterpret_cast<PyUICollectionObject*>(_o);
            //PyUIFrameObject* o = (PyUIFrameObject*)PyObject_New(PyUIFrameObject, UIFrameType);
            
            PyUIFrameObject* o = (PyUIFrameObject*)(UIFrameType->tp_alloc(UIFrameType, 0));
            //PyUIFrameObject* o = PyObject_New(PyUIFrameObject, UIFrameType);

            /*
            // backtracking the problem: instantiate a PyColor of (255, 0, 0) for testing
            PyTypeObject* colorType = &PyColorType;
            PyObject* pyColor = colorType->tp_alloc(colorType, 0);
            if (pyColor == NULL)
            {
                std::cout << "failure to allocate mcrfpy.Color / PyColorType" << std::endl;
                return NULL;
            }
            PyColorObject* pyColorObj = reinterpret_cast<PyColorObject*>(pyColor);
            pyColorObj->data = std::make_shared<sf::Color>();
            pyColorObj->data-> r = 255;
            return (PyObject*)pyColorObj;
            */

            
            std::cout << "pointer check: " << o << "\n" << std::flush;
            if (o)
            {
                std::cout << "Casting data...\n" << std::flush;
                auto p = std::static_pointer_cast<UIFrame>(source);
                std::cout << "casted. Assigning...\n" << std::flush;
                //o->data = std::make_shared<UIFrame>();

                o->data = p;
                //std::cout << "assigned.\n" << std::flush;
                auto usource = o->data; //(UIFrame*)source.get();
                std::cout << "Loaded data into object. " << usource->box.getPosition().x << " " << usource->box.getPosition().y << " " <<
                    usource->box.getSize().x << " " << usource->box.getSize().y << std::endl;
            }
            else
            {
                std::cout << "Allocation failed.\n" << std::flush;
            }
            newobj = (PyObject*)o;
            break;
            
        }
        case PyObjectsEnum::UICAPTION:
        {
            std::cout << "UICAPTION case\n";
            PyErr_SetString(PyExc_NotImplementedError, "UICaption class not implemented in Python yet.");
            /* not yet implemented
            PyUICaptionObject* o = (PyUICaptionObject*)PyUICaptionType.tp_alloc(&PyUICaptionType, 0);
            if (o)
                o->data = std::static_pointer_cast<UICaption>(source);
            */
            break;
        }
        case PyObjectsEnum::UISPRITE:
        {
            std::cout << "UISPRITE case\n";
            PyErr_SetString(PyExc_NotImplementedError, "UISprite class not implemented in Python yet.");
            /*
            PyUISpriteObject* o = (PyUISpriteObject*)PyUISpriteType.tp_alloc(&PyUISpriteType, 0);
            if (o)
                o->data = std::static_pointer_cast<UISprite>(source);
            */
            break;
        }
        default:
            return NULL;
            break;
    }

    return newobj;
}
