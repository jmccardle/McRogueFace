#include "UISprite.h"
#include "GameEngine.h"

UIDrawable* UISprite::click_at(sf::Vector2f point)
{
    if (click_callable)
    {
        if(sprite.getGlobalBounds().contains(point)) return this;
    }
    return NULL;
}

UISprite::UISprite() {}

UISprite::UISprite(std::shared_ptr<PyTexture> _ptex, int _sprite_index, sf::Vector2f _pos, float _scale)
: ptex(_ptex), sprite_index(_sprite_index)
{
    sprite = ptex->sprite(sprite_index, _pos, sf::Vector2f(_scale, _scale));
}

void UISprite::render(sf::Vector2f offset)
{
    sprite.move(offset);
    Resources::game->getWindow().draw(sprite);
    sprite.move(-offset);
}

void UISprite::render(sf::Vector2f offset, sf::RenderTexture& target)
{
    sprite.move(offset);
    target.draw(sprite);
    sprite.move(-offset);
}

void UISprite::setPosition(sf::Vector2f pos)
{
    sprite.setPosition(pos);
}

void UISprite::setScale(sf::Vector2f s)
{
    sprite.setScale(s);
}

void UISprite::setTexture(std::shared_ptr<PyTexture> _ptex, int _sprite_index)
{
    ptex = _ptex;
    if (_sprite_index != -1) // if you are changing textures, there's a good chance you need a new index too
        sprite_index = _sprite_index;
    sprite = ptex->sprite(sprite_index, sprite.getPosition(), sprite.getScale());
}

void UISprite::setSpriteIndex(int _sprite_index)
{
    sprite_index = _sprite_index;
    sprite = ptex->sprite(sprite_index, sprite.getPosition(), sprite.getScale());
}

sf::Vector2f UISprite::getScale()
{
    return sprite.getScale();
}

sf::Vector2f UISprite::getPosition()
{
    return sprite.getPosition();
}

std::shared_ptr<PyTexture> UISprite::getTexture()
{
    return ptex;
}

int UISprite::getSpriteIndex()
{
    return sprite_index;
}

PyObjectsEnum UISprite::derived_type()
{
    return PyObjectsEnum::UISPRITE;
}

PyObject* UISprite::get_float_member(PyUISpriteObject* self, void* closure)
{
    auto member_ptr = reinterpret_cast<long>(closure);
    if (member_ptr == 0)
        return PyFloat_FromDouble(self->data->getPosition().x);
    else if (member_ptr == 1)
        return PyFloat_FromDouble(self->data->getPosition().y);
    else if (member_ptr == 2)
        return PyFloat_FromDouble(self->data->getScale().x); // scale X and Y are identical, presently
    else
    {
        PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
        return nullptr;
    }
}

int UISprite::set_float_member(PyUISpriteObject* self, PyObject* value, void* closure)
{
    float val;
    auto member_ptr = reinterpret_cast<long>(closure);
    if (PyFloat_Check(value))
    {
        val = PyFloat_AsDouble(value);
    }
    else if (PyLong_Check(value))
    {
        val = PyLong_AsLong(value);
    }
    else
    {
        PyErr_SetString(PyExc_TypeError, "Value must be a floating point number.");
        return -1;
    }
    if (member_ptr == 0) //x
        self->data->setPosition(sf::Vector2f(val, self->data->getPosition().y));
    else if (member_ptr == 1) //y
        self->data->setPosition(sf::Vector2f(self->data->getPosition().x, val));
    else if (member_ptr == 2) // scale
        self->data->setScale(sf::Vector2f(val, val));
    return 0;
}

PyObject* UISprite::get_int_member(PyUISpriteObject* self, void* closure)
{
    auto member_ptr = reinterpret_cast<long>(closure);
    if (true) {}
    else
    {
        PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
        return nullptr;
    }
    
    return PyLong_FromDouble(self->data->getSpriteIndex());
}

int UISprite::set_int_member(PyUISpriteObject* self, PyObject* value, void* closure)
{
    int val;
    auto member_ptr = reinterpret_cast<long>(closure);
    if (PyLong_Check(value))
    {
        val = PyLong_AsLong(value);
    }
    else
    {
        PyErr_SetString(PyExc_TypeError, "Value must be an integer.");
        return -1;
    }
    self->data->setSpriteIndex(val);
    return 0;
}

PyObject* UISprite::get_texture(PyUISpriteObject* self, void* closure)
{
    return self->data->getTexture()->pyObject();
}

int UISprite::set_texture(PyUISpriteObject* self, PyObject* value, void* closure)
{
    return -1;
}

PyGetSetDef UISprite::getsetters[] = {
    {"x", (getter)UISprite::get_float_member, (setter)UISprite::set_float_member, "X coordinate of top-left corner",   (void*)0},
    {"y", (getter)UISprite::get_float_member, (setter)UISprite::set_float_member, "Y coordinate of top-left corner",   (void*)1},
    {"scale", (getter)UISprite::get_float_member, (setter)UISprite::set_float_member, "Size factor",                   (void*)2},
    {"sprite_number", (getter)UISprite::get_int_member, (setter)UISprite::set_int_member, "Which sprite on the texture is shown", NULL},
    {"texture", (getter)UISprite::get_texture, (setter)UISprite::set_texture,     "Texture object",                    NULL},
    {"click", (getter)UIDrawable::get_click, (setter)UIDrawable::set_click, "Object called with (x, y, button) when clicked", (void*)PyObjectsEnum::UISPRITE},
    {NULL}
};

PyObject* UISprite::repr(PyUISpriteObject* self)
{
    std::ostringstream ss;
    if (!self->data) ss << "<Sprite (invalid internal object)>";
    else {
        //auto sprite = self->data->sprite;
        ss << "<Sprite (x=" << self->data->getPosition().x << ", y=" << self->data->getPosition().y << ", " <<
            "scale=" << self->data->getScale().x << ", " <<
            "sprite_number=" << self->data->getSpriteIndex() << ")>";
    }
    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

int UISprite::init(PyUISpriteObject* self, PyObject* args, PyObject* kwds)
{
    //std::cout << "Init called\n";
    static const char* keywords[] = { "x", "y", "texture", "sprite_index", "scale", nullptr };
    float x = 0.0f, y = 0.0f, scale = 1.0f;
    int sprite_index;
    PyObject* texture;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|ffOif",
        const_cast<char**>(keywords), &x, &y, &texture, &sprite_index, &scale))
    {
        return -1;
    }

    // check types for texture
    //if (texture != NULL && !PyObject_IsInstance(texture, (PyObject*)&PyTextureType)){
    if (texture != NULL && !PyObject_IsInstance(texture, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Texture"))){
        PyErr_SetString(PyExc_TypeError, "texture must be a mcrfpy.Texture instance");
        return -1;
    }
    auto pytexture = (PyTextureObject*)texture;
    self->data = std::make_shared<UISprite>(pytexture->data, sprite_index, sf::Vector2f(x, y), scale);
    self->data->setPosition(sf::Vector2f(x, y));

    return 0;
}
