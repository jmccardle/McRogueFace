#include "PyTexture.h"


PyTexture::PyTexture(std::string filename, int sprite_w, int sprite_h)
: source(filename), sprite_width(sprite_w), sprite_height(sprite_h)
{
    texture = sf::Texture();
    texture.loadFromFile(source);
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
    int tx = index % sheet_width, ty = index / sheet_width;
    auto ir = sf::IntRect(tx * sprite_width, ty * sprite_height, sprite_width, sprite_height);
    auto sprite = sf::Sprite(texture, ir);
    sprite.setPosition(pos);
    sprite.setScale(s);
    return sprite;
}

PyObject* PyTexture::pyObject()
{
    PyObject* obj = PyType_GenericAlloc(&mcrfpydef::PyTextureType, 0);
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
    self->data = std::make_shared<PyTexture>(filename, sprite_width, sprite_height);
    return 0;
}

PyObject* PyTexture::pynew(PyTypeObject* type, PyObject* args, PyObject* kwds)
{
    return (PyObject*)type->tp_alloc(type, 0);
}
