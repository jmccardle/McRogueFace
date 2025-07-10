#include "PyTexture.h"
#include "McRFPy_API.h"

PyTexture::PyTexture(std::string filename, int sprite_w, int sprite_h)
: source(filename), sprite_width(sprite_w), sprite_height(sprite_h), sheet_width(0), sheet_height(0)
{
    texture = sf::Texture();
    if (!texture.loadFromFile(source)) {
        // Failed to load texture - leave sheet dimensions as 0
        // This will be checked in init()
        return;
    }
    texture.setSmooth(false);  // Disable smoothing for pixel art
    auto size = texture.getSize();
    sheet_width = (size.x / sprite_width);
    sheet_height = (size.y / sprite_height);
    if (size.x % sprite_width != 0 || size.y % sprite_height != 0)
    {
        std::cout << "Warning: Texture `" << source << "` is not an even number of sprite widths or heights across." << std::endl 
            << "Sprite size given was " << sprite_w << "x" << sprite_h << "px but the file has a resolution of " << sheet_width << "x" << sheet_height << "px." << std::endl;
    }
}

sf::Sprite PyTexture::sprite(int index, sf::Vector2f pos,  sf::Vector2f s)
{
    // Protect against division by zero if texture failed to load
    if (sheet_width == 0 || sheet_height == 0) {
        // Return an empty sprite
        return sf::Sprite();
    }
    
    int tx = index % sheet_width, ty = index / sheet_width;
    auto ir = sf::IntRect(tx * sprite_width, ty * sprite_height, sprite_width, sprite_height);
    auto sprite = sf::Sprite(texture, ir);
    sprite.setPosition(pos);
    sprite.setScale(s);
    return sprite;
}

PyObject* PyTexture::pyObject()
{
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Texture");
    PyObject* obj = PyTexture::pynew(type, Py_None, Py_None);

    try {
        ((PyTextureObject*)obj)->data = shared_from_this();
    }
    catch (std::bad_weak_ptr& e)
    {
        std::cout << "Bad weak ptr: shared_from_this() failed in PyTexture::pyObject(); did you create a PyTexture outside of std::make_shared? enjoy your segfault, soon!" << std::endl;
    }
    // TODO - shared_from_this will raise an exception if the object does not have a shared pointer. Constructor should be made private; write a factory function
    return obj;
}

PyObject* PyTexture::repr(PyObject* obj)
{
    PyTextureObject* self = (PyTextureObject*)obj;
    std::ostringstream ss;
    if (!self->data)
    {
        ss << "<Texture [invalid internal object]>";
        std::string repr_str = ss.str();
        return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
    }
    auto& ptex = *(self->data);
    ss << "<Texture " << ptex.sheet_height << " rows, " << ptex.sheet_width << " columns; " << ptex.sprite_width << "x" << ptex.sprite_height << "px sprites. source='" << ptex.source << "'>";
    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

Py_hash_t PyTexture::hash(PyObject* obj)
{
    auto self = (PyTextureObject*)obj;
    return reinterpret_cast<Py_hash_t>(self->data.get());
}

int PyTexture::init(PyTextureObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = { "filename", "sprite_width", "sprite_height", nullptr };
    char* filename;
    int sprite_width, sprite_height;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "sii", const_cast<char**>(keywords), &filename, &sprite_width, &sprite_height))
        return -1;
    
    // Create the texture object
    self->data = std::make_shared<PyTexture>(filename, sprite_width, sprite_height);
    
    // Check if the texture failed to load (sheet dimensions will be 0)
    if (self->data->sheet_width == 0 || self->data->sheet_height == 0) {
        PyErr_Format(PyExc_IOError, "Failed to load texture from file: %s", filename);
        return -1;
    }
    
    return 0;
}

PyObject* PyTexture::pynew(PyTypeObject* type, PyObject* args, PyObject* kwds)
{
    return (PyObject*)type->tp_alloc(type, 0);
}

PyObject* PyTexture::get_sprite_width(PyTextureObject* self, void* closure)
{
    return PyLong_FromLong(self->data->sprite_width);
}

PyObject* PyTexture::get_sprite_height(PyTextureObject* self, void* closure)
{
    return PyLong_FromLong(self->data->sprite_height);
}

PyObject* PyTexture::get_sheet_width(PyTextureObject* self, void* closure)
{
    return PyLong_FromLong(self->data->sheet_width);
}

PyObject* PyTexture::get_sheet_height(PyTextureObject* self, void* closure)
{
    return PyLong_FromLong(self->data->sheet_height);
}

PyObject* PyTexture::get_sprite_count(PyTextureObject* self, void* closure)
{
    return PyLong_FromLong(self->data->getSpriteCount());
}

PyObject* PyTexture::get_source(PyTextureObject* self, void* closure)
{
    return PyUnicode_FromString(self->data->source.c_str());
}

PyGetSetDef PyTexture::getsetters[] = {
    {"sprite_width", (getter)PyTexture::get_sprite_width, NULL, "Width of each sprite in pixels", NULL},
    {"sprite_height", (getter)PyTexture::get_sprite_height, NULL, "Height of each sprite in pixels", NULL},
    {"sheet_width", (getter)PyTexture::get_sheet_width, NULL, "Number of sprite columns in the texture", NULL},
    {"sheet_height", (getter)PyTexture::get_sheet_height, NULL, "Number of sprite rows in the texture", NULL},
    {"sprite_count", (getter)PyTexture::get_sprite_count, NULL, "Total number of sprites in the texture", NULL},
    {"source", (getter)PyTexture::get_source, NULL, "Source filename of the texture", NULL},
    {NULL}  // Sentinel
};
