#include "PyTexture.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"

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

// #144: Factory method to create texture from rendered content (snapshot)
std::shared_ptr<PyTexture> PyTexture::from_rendered(sf::RenderTexture& render_tex)
{
    // Use a custom shared_ptr construction to access private default constructor
    struct MakeSharedEnabler : public PyTexture {
        MakeSharedEnabler() : PyTexture() {}
    };
    auto ptex = std::make_shared<MakeSharedEnabler>();

    // Copy the rendered texture data
    ptex->texture = render_tex.getTexture();
    ptex->texture.setSmooth(false);  // Maintain pixel art aesthetic

    // Set source to indicate this is a snapshot
    ptex->source = "<snapshot>";

    // Treat entire texture as single sprite
    auto size = ptex->texture.getSize();
    ptex->sprite_width = size.x;
    ptex->sprite_height = size.y;
    ptex->sheet_width = 1;
    ptex->sheet_height = 1;

    return ptex;
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
    if (!type) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to get Texture type from module");
        return NULL;
    }
    PyObject* obj = PyTexture::pynew(type, Py_None, Py_None);
    Py_DECREF(type);  // GetAttrString returns new reference

    if (!obj) {
        return NULL;
    }

    try {
        // Use placement new to properly construct the shared_ptr
        // tp_alloc zeroes memory but doesn't call C++ constructors
        new (&((PyTextureObject*)obj)->data) std::shared_ptr<PyTexture>(shared_from_this());
    }
    catch (std::bad_weak_ptr& e)
    {
        std::cout << "Bad weak ptr: shared_from_this() failed in PyTexture::pyObject(); did you create a PyTexture outside of std::make_shared? enjoy your segfault, soon!" << std::endl;
        Py_DECREF(obj);
        PyErr_SetString(PyExc_RuntimeError, "PyTexture was not created with std::make_shared");
        return NULL;
    }
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
    {"sprite_width", (getter)PyTexture::get_sprite_width, NULL,
     MCRF_PROPERTY(sprite_width, "Width of each sprite in pixels (int, read-only). Specified during texture initialization."), NULL},
    {"sprite_height", (getter)PyTexture::get_sprite_height, NULL,
     MCRF_PROPERTY(sprite_height, "Height of each sprite in pixels (int, read-only). Specified during texture initialization."), NULL},
    {"sheet_width", (getter)PyTexture::get_sheet_width, NULL,
     MCRF_PROPERTY(sheet_width, "Number of sprite columns in the texture sheet (int, read-only). Calculated as texture_width / sprite_width."), NULL},
    {"sheet_height", (getter)PyTexture::get_sheet_height, NULL,
     MCRF_PROPERTY(sheet_height, "Number of sprite rows in the texture sheet (int, read-only). Calculated as texture_height / sprite_height."), NULL},
    {"sprite_count", (getter)PyTexture::get_sprite_count, NULL,
     MCRF_PROPERTY(sprite_count, "Total number of sprites in the texture sheet (int, read-only). Equals sheet_width * sheet_height."), NULL},
    {"source", (getter)PyTexture::get_source, NULL,
     MCRF_PROPERTY(source, "Source filename path (str, read-only). The path used to load this texture."), NULL},
    {NULL}  // Sentinel
};
