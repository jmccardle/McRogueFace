#include "PyTexture.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"
#include "PyTypeCache.h"
#include <cmath>
#include <algorithm>

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

// Factory method to create texture from an sf::Image (for LDtk flip-baked atlases)
std::shared_ptr<PyTexture> PyTexture::from_image(
    const sf::Image& img, int sprite_w, int sprite_h,
    const std::string& name)
{
    struct MakeSharedEnabler : public PyTexture {
        MakeSharedEnabler() : PyTexture() {}
    };
    auto ptex = std::make_shared<MakeSharedEnabler>();

    ptex->texture.loadFromImage(img);
    ptex->texture.setSmooth(false);

    ptex->source = name;
    ptex->sprite_width = sprite_w;
    ptex->sprite_height = sprite_h;

    auto size = ptex->texture.getSize();
    ptex->sheet_width = (sprite_w > 0) ? (size.x / sprite_w) : 0;
    ptex->sheet_height = (sprite_h > 0) ? (size.y / sprite_h) : 0;

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
    PyTypeObject* type = PyTypeCache::Texture();
    if (!type) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to get Texture type from cache");
        return NULL;
    }
    PyObject* obj = PyTexture::pynew(type, Py_None, Py_None);
    // PyTypeCache returns borrowed reference — no DECREF needed

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

// ============================================================================
// Texture.from_bytes(data, width, height, sprite_w, sprite_h, name) classmethod
// ============================================================================
PyObject* PyTexture::from_bytes(PyObject* cls, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"data", "width", "height", "sprite_width", "sprite_height", "name", nullptr};
    Py_buffer buf;
    int width, height, sprite_w, sprite_h;
    const char* name = "<generated>";

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "y*iiii|s",
            const_cast<char**>(keywords),
            &buf, &width, &height, &sprite_w, &sprite_h, &name))
        return NULL;

    Py_ssize_t expected = (Py_ssize_t)width * height * 4;
    if (buf.len != expected) {
        PyBuffer_Release(&buf);
        PyErr_Format(PyExc_ValueError,
            "Expected %zd bytes (width=%d * height=%d * 4), got %zd",
            expected, width, height, buf.len);
        return NULL;
    }

    sf::Image img;
    img.create(width, height, (const sf::Uint8*)buf.buf);
    PyBuffer_Release(&buf);

    auto ptex = PyTexture::from_image(img, sprite_w, sprite_h, name);
    return ptex->pyObject();
}

// ============================================================================
// Texture.composite(layers, sprite_w, sprite_h, name) classmethod
// ============================================================================
PyObject* PyTexture::composite(PyObject* cls, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"layers", "sprite_width", "sprite_height", "name", nullptr};
    PyObject* layers_list;
    int sprite_w, sprite_h;
    const char* name = "<composite>";

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "Oii|s",
            const_cast<char**>(keywords),
            &layers_list, &sprite_w, &sprite_h, &name))
        return NULL;

    if (!PyList_Check(layers_list)) {
        PyErr_SetString(PyExc_TypeError, "layers must be a list of Texture objects");
        return NULL;
    }

    Py_ssize_t count = PyList_Size(layers_list);
    if (count == 0) {
        PyErr_SetString(PyExc_ValueError, "layers list must not be empty");
        return NULL;
    }

    // Validate all elements are Texture objects and collect images
    std::vector<sf::Image> images;
    unsigned int tex_w = 0, tex_h = 0;

    // Use PyTypeCache for reliable, leak-free isinstance check
    PyTypeObject* texture_type = PyTypeCache::Texture();
    if (!texture_type) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to get Texture type from cache");
        return NULL;
    }

    for (Py_ssize_t i = 0; i < count; i++) {
        PyObject* item = PyList_GetItem(layers_list, i);
        if (!PyObject_IsInstance(item, (PyObject*)texture_type)) {
            PyErr_Format(PyExc_TypeError,
                "layers[%zd] is not a Texture object", i);
            return NULL;
        }
        auto& ptex = ((PyTextureObject*)item)->data;
        if (!ptex) {
            PyErr_Format(PyExc_ValueError,
                "layers[%zd] has invalid internal data", i);
            return NULL;
        }

        sf::Image img = ptex->texture.copyToImage();
        auto size = img.getSize();

        if (i == 0) {
            tex_w = size.x;
            tex_h = size.y;
        } else if (size.x != tex_w || size.y != tex_h) {
            PyErr_Format(PyExc_ValueError,
                "All layers must have same dimensions. "
                "Layer 0 is %ux%u, layer %zd is %ux%u",
                tex_w, tex_h, i, size.x, size.y);
            return NULL;
        }
        images.push_back(std::move(img));
    }
    // PyTypeCache returns borrowed reference — no DECREF needed

    // Alpha-composite all layers bottom-to-top
    sf::Image result;
    result.create(tex_w, tex_h, sf::Color::Transparent);

    for (unsigned int y = 0; y < tex_h; y++) {
        for (unsigned int x = 0; x < tex_w; x++) {
            // Start with first layer
            sf::Color dst = images[0].getPixel(x, y);

            // Composite each subsequent layer on top
            for (size_t i = 1; i < images.size(); i++) {
                sf::Color src = images[i].getPixel(x, y);
                if (src.a == 0) continue;
                if (src.a == 255 || dst.a == 0) {
                    dst = src;
                    continue;
                }

                // Standard alpha compositing (Porter-Duff "over")
                float sa = src.a / 255.0f;
                float da = dst.a / 255.0f;
                float out_a = sa + da * (1.0f - sa);

                if (out_a > 0.0f) {
                    dst.r = (sf::Uint8)((src.r * sa + dst.r * da * (1.0f - sa)) / out_a);
                    dst.g = (sf::Uint8)((src.g * sa + dst.g * da * (1.0f - sa)) / out_a);
                    dst.b = (sf::Uint8)((src.b * sa + dst.b * da * (1.0f - sa)) / out_a);
                    dst.a = (sf::Uint8)(out_a * 255.0f);
                }
            }
            result.setPixel(x, y, dst);
        }
    }

    auto ptex = PyTexture::from_image(result, sprite_w, sprite_h, name);
    return ptex->pyObject();
}

// ============================================================================
// HSL conversion helpers (internal)
// ============================================================================
namespace {

struct HSL {
    float h, s, l;
};

HSL rgb_to_hsl(sf::Uint8 r, sf::Uint8 g, sf::Uint8 b)
{
    float rf = r / 255.0f, gf = g / 255.0f, bf = b / 255.0f;
    float mx = std::max({rf, gf, bf});
    float mn = std::min({rf, gf, bf});
    float l = (mx + mn) / 2.0f;

    if (mx == mn) return {0.0f, 0.0f, l};

    float d = mx - mn;
    float s = (l > 0.5f) ? d / (2.0f - mx - mn) : d / (mx + mn);
    float h;
    if (mx == rf) {
        h = (gf - bf) / d + (gf < bf ? 6.0f : 0.0f);
    } else if (mx == gf) {
        h = (bf - rf) / d + 2.0f;
    } else {
        h = (rf - gf) / d + 4.0f;
    }
    h *= 60.0f;
    return {h, s, l};
}

static float hue_to_rgb(float p, float q, float t)
{
    if (t < 0.0f) t += 1.0f;
    if (t > 1.0f) t -= 1.0f;
    if (t < 1.0f/6.0f) return p + (q - p) * 6.0f * t;
    if (t < 1.0f/2.0f) return q;
    if (t < 2.0f/3.0f) return p + (q - p) * (2.0f/3.0f - t) * 6.0f;
    return p;
}

sf::Color hsl_to_rgb(float h, float s, float l, sf::Uint8 a)
{
    if (s <= 0.0f) {
        sf::Uint8 v = (sf::Uint8)(l * 255.0f);
        return sf::Color(v, v, v, a);
    }

    float hn = h / 360.0f;
    float q = (l < 0.5f) ? l * (1.0f + s) : l + s - l * s;
    float p = 2.0f * l - q;

    float r = hue_to_rgb(p, q, hn + 1.0f/3.0f);
    float g = hue_to_rgb(p, q, hn);
    float b = hue_to_rgb(p, q, hn - 1.0f/3.0f);

    return sf::Color(
        (sf::Uint8)(r * 255.0f),
        (sf::Uint8)(g * 255.0f),
        (sf::Uint8)(b * 255.0f),
        a);
}

} // anonymous namespace

// ============================================================================
// texture.hsl_shift(hue_shift, sat_shift, lit_shift) instance method
// ============================================================================
PyObject* PyTexture::hsl_shift(PyTextureObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"hue_shift", "sat_shift", "lit_shift", nullptr};
    float hue_shift, sat_shift = 0.0f, lit_shift = 0.0f;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "f|ff",
            const_cast<char**>(keywords),
            &hue_shift, &sat_shift, &lit_shift))
        return NULL;

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Texture has invalid internal data");
        return NULL;
    }

    sf::Image img = self->data->texture.copyToImage();
    auto size = img.getSize();

    for (unsigned int y = 0; y < size.y; y++) {
        for (unsigned int x = 0; x < size.x; x++) {
            sf::Color px = img.getPixel(x, y);
            if (px.a == 0) continue; // skip transparent

            HSL hsl = rgb_to_hsl(px.r, px.g, px.b);

            // Apply shifts
            hsl.h = std::fmod(hsl.h + hue_shift, 360.0f);
            if (hsl.h < 0.0f) hsl.h += 360.0f;

            hsl.s = std::clamp(hsl.s + sat_shift, 0.0f, 1.0f);
            hsl.l = std::clamp(hsl.l + lit_shift, 0.0f, 1.0f);

            img.setPixel(x, y, hsl_to_rgb(hsl.h, hsl.s, hsl.l, px.a));
        }
    }

    auto ptex = PyTexture::from_image(img,
        self->data->sprite_width, self->data->sprite_height,
        self->data->source + "+hsl");
    return ptex->pyObject();
}

// ============================================================================
// Methods table
// ============================================================================
PyMethodDef PyTexture::methods[] = {
    {"from_bytes", (PyCFunction)PyTexture::from_bytes, METH_VARARGS | METH_KEYWORDS | METH_CLASS,
     MCRF_METHOD(Texture, from_bytes,
         MCRF_SIG("(data: bytes, width: int, height: int, sprite_width: int, sprite_height: int, name: str = '<generated>')", "Texture"),
         MCRF_DESC("Create a Texture from raw RGBA pixel data."),
         MCRF_ARGS_START
         MCRF_ARG("data", "Raw RGBA bytes (length must equal width * height * 4)")
         MCRF_ARG("width", "Image width in pixels")
         MCRF_ARG("height", "Image height in pixels")
         MCRF_ARG("sprite_width", "Width of each sprite cell")
         MCRF_ARG("sprite_height", "Height of each sprite cell")
         MCRF_ARG("name", "Optional name for the texture (default: '<generated>')")
         MCRF_RETURNS("Texture: New texture containing the pixel data")
         MCRF_RAISES("ValueError", "If data length does not match width * height * 4")
         MCRF_NOTE("This is a class method. Useful for procedurally generated textures.")
     )},
    {"composite", (PyCFunction)PyTexture::composite, METH_VARARGS | METH_KEYWORDS | METH_CLASS,
     MCRF_METHOD(Texture, composite,
         MCRF_SIG("(layers: list[Texture], sprite_width: int, sprite_height: int, name: str = '<composite>')", "Texture"),
         MCRF_DESC("Alpha-composite multiple texture layers into a single texture."),
         MCRF_ARGS_START
         MCRF_ARG("layers", "List of Texture objects, composited bottom-to-top")
         MCRF_ARG("sprite_width", "Width of each sprite cell in the result")
         MCRF_ARG("sprite_height", "Height of each sprite cell in the result")
         MCRF_ARG("name", "Optional name for the composite texture")
         MCRF_RETURNS("Texture: New texture with all layers composited")
         MCRF_RAISES("ValueError", "If layers have different dimensions or list is empty")
         MCRF_NOTE("This is a class method. Uses Porter-Duff 'over' alpha compositing.")
     )},
    {"hsl_shift", (PyCFunction)PyTexture::hsl_shift, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(Texture, hsl_shift,
         MCRF_SIG("(hue_shift: float, sat_shift: float = 0.0, lit_shift: float = 0.0)", "Texture"),
         MCRF_DESC("Create a new texture with HSL color adjustments applied."),
         MCRF_ARGS_START
         MCRF_ARG("hue_shift", "Hue rotation in degrees [0.0, 360.0)")
         MCRF_ARG("sat_shift", "Saturation adjustment [-1.0, 1.0] (default 0.0)")
         MCRF_ARG("lit_shift", "Lightness adjustment [-1.0, 1.0] (default 0.0)")
         MCRF_RETURNS("Texture: New texture with color-shifted pixels")
         MCRF_NOTE("Preserves alpha channel. Skips fully transparent pixels.")
     )},
    {NULL}  // Sentinel
};
