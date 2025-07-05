#include "UISprite.h"
#include "GameEngine.h"
#include "PyVector.h"

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

/*
void UISprite::render(sf::Vector2f offset)
{
    sprite.move(offset);
    Resources::game->getWindow().draw(sprite);
    sprite.move(-offset);
}
*/

void UISprite::render(sf::Vector2f offset, sf::RenderTarget& target)
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

sf::Vector2f UISprite::getScale() const
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
    else if (member_ptr == 3)
        return PyFloat_FromDouble(self->data->getScale().x); // scale_x
    else if (member_ptr == 4)
        return PyFloat_FromDouble(self->data->getScale().y); // scale_y
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
    else if (member_ptr == 2) // scale (uniform)
        self->data->setScale(sf::Vector2f(val, val));
    else if (member_ptr == 3) // scale_x
        self->data->setScale(sf::Vector2f(val, self->data->getScale().y));
    else if (member_ptr == 4) // scale_y
        self->data->setScale(sf::Vector2f(self->data->getScale().x, val));
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
    
    // Validate sprite index is within texture bounds
    auto texture = self->data->getTexture();
    if (texture) {
        int sprite_count = texture->getSpriteCount();
        
        if (val < 0 || val >= sprite_count) {
            PyErr_Format(PyExc_ValueError, 
                "Sprite index %d out of range. Texture has %d sprites (0-%d)", 
                val, sprite_count, sprite_count - 1);
            return -1;
        }
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
    // Check if value is a Texture instance
    if (!PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Texture"))) {
        PyErr_SetString(PyExc_TypeError, "texture must be a mcrfpy.Texture instance");
        return -1;
    }
    
    // Get the texture from the Python object
    auto pytexture = (PyTextureObject*)value;
    if (!pytexture->data) {
        PyErr_SetString(PyExc_ValueError, "Invalid texture object");
        return -1;
    }
    
    // Update the sprite's texture
    self->data->setTexture(pytexture->data);
    
    return 0;
}

PyObject* UISprite::get_pos(PyUISpriteObject* self, void* closure)
{
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    auto obj = (PyVectorObject*)type->tp_alloc(type, 0);
    if (obj) {
        auto pos = self->data->getPosition();
        obj->data = sf::Vector2f(pos.x, pos.y);
    }
    return (PyObject*)obj;
}

int UISprite::set_pos(PyUISpriteObject* self, PyObject* value, void* closure)
{
    PyVectorObject* vec = PyVector::from_arg(value);
    if (!vec) {
        PyErr_SetString(PyExc_TypeError, "pos must be a Vector or convertible to Vector");
        return -1;
    }
    self->data->setPosition(vec->data);
    return 0;
}

PyGetSetDef UISprite::getsetters[] = {
    {"x", (getter)UISprite::get_float_member, (setter)UISprite::set_float_member, "X coordinate of top-left corner",   (void*)0},
    {"y", (getter)UISprite::get_float_member, (setter)UISprite::set_float_member, "Y coordinate of top-left corner",   (void*)1},
    {"scale", (getter)UISprite::get_float_member, (setter)UISprite::set_float_member, "Uniform size factor",                   (void*)2},
    {"scale_x", (getter)UISprite::get_float_member, (setter)UISprite::set_float_member, "Horizontal scale factor",         (void*)3},
    {"scale_y", (getter)UISprite::get_float_member, (setter)UISprite::set_float_member, "Vertical scale factor",           (void*)4},
    {"sprite_index", (getter)UISprite::get_int_member, (setter)UISprite::set_int_member, "Which sprite on the texture is shown", NULL},
    {"sprite_number", (getter)UISprite::get_int_member, (setter)UISprite::set_int_member, "Which sprite on the texture is shown (deprecated: use sprite_index)", NULL},
    {"texture", (getter)UISprite::get_texture, (setter)UISprite::set_texture,     "Texture object",                    NULL},
    {"click", (getter)UIDrawable::get_click, (setter)UIDrawable::set_click, "Object called with (x, y, button) when clicked", (void*)PyObjectsEnum::UISPRITE},
    {"z_index", (getter)UIDrawable::get_int, (setter)UIDrawable::set_int, "Z-order for rendering (lower values rendered first)", (void*)PyObjectsEnum::UISPRITE},
    {"pos", (getter)UISprite::get_pos, (setter)UISprite::set_pos, "Position as a Vector", NULL},
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
            "sprite_index=" << self->data->getSpriteIndex() << ")>";
    }
    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

int UISprite::init(PyUISpriteObject* self, PyObject* args, PyObject* kwds)
{
    //std::cout << "Init called\n";
    static const char* keywords[] = { "x", "y", "texture", "sprite_index", "scale", nullptr };
    float x = 0.0f, y = 0.0f, scale = 1.0f;
    int sprite_index = 0;
    PyObject* texture = NULL;

    // First try to parse as (x, y, texture, ...)
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|ffOif",
        const_cast<char**>(keywords), &x, &y, &texture, &sprite_index, &scale))
    {
        PyErr_Clear();  // Clear the error
        
        // Try to parse as ((x,y), texture, ...) or (Vector, texture, ...)
        PyObject* pos_obj = nullptr;
        const char* alt_keywords[] = { "pos", "texture", "sprite_index", "scale", nullptr };
        
        if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OOif", const_cast<char**>(alt_keywords), 
                                          &pos_obj, &texture, &sprite_index, &scale))
        {
            return -1;
        }
        
        // Convert position argument to x, y
        if (pos_obj) {
            PyVectorObject* vec = PyVector::from_arg(pos_obj);
            if (!vec) {
                PyErr_SetString(PyExc_TypeError, "First argument must be a tuple (x, y) or Vector when not providing x, y separately");
                return -1;
            }
            x = vec->data.x;
            y = vec->data.y;
        }
    }

    // Handle texture - allow None or use default
    std::shared_ptr<PyTexture> texture_ptr = nullptr;
    if (texture != NULL && texture != Py_None && !PyObject_IsInstance(texture, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Texture"))){
        PyErr_SetString(PyExc_TypeError, "texture must be a mcrfpy.Texture instance or None");
        return -1;
    } else if (texture != NULL && texture != Py_None) {
        auto pytexture = (PyTextureObject*)texture;
        texture_ptr = pytexture->data;
    } else {
        // Use default texture when None or not provided
        texture_ptr = McRFPy_API::default_texture;
    }
    
    if (!texture_ptr) {
        PyErr_SetString(PyExc_RuntimeError, "No texture provided and no default texture available");
        return -1;
    }
    
    self->data = std::make_shared<UISprite>(texture_ptr, sprite_index, sf::Vector2f(x, y), scale);
    self->data->setPosition(sf::Vector2f(x, y));

    return 0;
}

// Property system implementation for animations
bool UISprite::setProperty(const std::string& name, float value) {
    if (name == "x") {
        sprite.setPosition(sf::Vector2f(value, sprite.getPosition().y));
        return true;
    }
    else if (name == "y") {
        sprite.setPosition(sf::Vector2f(sprite.getPosition().x, value));
        return true;
    }
    else if (name == "scale") {
        sprite.setScale(sf::Vector2f(value, value));
        return true;
    }
    else if (name == "scale_x") {
        sprite.setScale(sf::Vector2f(value, sprite.getScale().y));
        return true;
    }
    else if (name == "scale_y") {
        sprite.setScale(sf::Vector2f(sprite.getScale().x, value));
        return true;
    }
    else if (name == "z_index") {
        z_index = static_cast<int>(value);
        return true;
    }
    return false;
}

bool UISprite::setProperty(const std::string& name, int value) {
    if (name == "sprite_index" || name == "sprite_number") {
        setSpriteIndex(value);
        return true;
    }
    else if (name == "z_index") {
        z_index = value;
        return true;
    }
    return false;
}

bool UISprite::getProperty(const std::string& name, float& value) const {
    if (name == "x") {
        value = sprite.getPosition().x;
        return true;
    }
    else if (name == "y") {
        value = sprite.getPosition().y;
        return true;
    }
    else if (name == "scale") {
        value = sprite.getScale().x;  // Assuming uniform scale
        return true;
    }
    else if (name == "scale_x") {
        value = sprite.getScale().x;
        return true;
    }
    else if (name == "scale_y") {
        value = sprite.getScale().y;
        return true;
    }
    else if (name == "z_index") {
        value = static_cast<float>(z_index);
        return true;
    }
    return false;
}

bool UISprite::getProperty(const std::string& name, int& value) const {
    if (name == "sprite_index" || name == "sprite_number") {
        value = sprite_index;
        return true;
    }
    else if (name == "z_index") {
        value = z_index;
        return true;
    }
    return false;
}
