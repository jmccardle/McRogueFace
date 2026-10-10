#pragma once
#include "Common.h"
#include "Python.h"

class PyTexture;

// #430: the struct is tp_alloc'd (zero-filled, not constructed). `data` is
// placement-new'd by whoever fills it and destroyed in PyTexture::dealloc.
typedef struct {
    PyObject_HEAD
    std::shared_ptr<PyTexture> data;
    PyObject* weakreflist;  // the wrapper cache holds weak references (#430)
} PyTextureObject;

class PyTexture : public std::enable_shared_from_this<PyTexture>
{
private:
    sf::Texture texture;
    std::string source;
    int sheet_width, sheet_height;

    // Private default constructor for factory methods
    PyTexture() : source("<uninitialized>"), sprite_width(0), sprite_height(0), sheet_width(0), sheet_height(0),
                  display_width(-1), display_height(-1), display_offset_x(0), display_offset_y(0) {}

public:
    // #430: PythonObjectCache key for this texture's one Python wrapper (0 = none yet).
    // Unregistered in ~PyTexture.
    uint64_t serial_number = 0;

    int sprite_width, sprite_height; // just use them read only, OK?
    // #235: Display bounds for non-uniform sprite content within cells
    int display_width, display_height;     // -1 = same as sprite_width/height
    int display_offset_x, display_offset_y; // offset within cell to content area
    PyTexture(std::string filename, int sprite_w, int sprite_h);
    ~PyTexture();
    PyTexture(const PyTexture&) = delete;
    PyTexture& operator=(const PyTexture&) = delete;

    // #144: Factory method to create texture from rendered content (snapshot)
    static std::shared_ptr<PyTexture> from_rendered(sf::RenderTexture& render_tex);

    // Factory method to create texture from an sf::Image (for LDtk flip-baked atlases)
    static std::shared_ptr<PyTexture> from_image(
        const sf::Image& img, int sprite_w, int sprite_h,
        const std::string& name = "<generated>");
    sf::Sprite sprite(int index, sf::Vector2f pos = sf::Vector2f(0, 0), sf::Vector2f s = sf::Vector2f(1.0, 1.0));
    int getSpriteCount() const { return sheet_width * sheet_height; }

    // Get the underlying sf::Texture for 3D rendering
    const sf::Texture* getSFMLTexture() const { return &texture; }

    // #430: the one cache-aware conversion. Returns the live wrapper for `tex` if one
    // exists (so `x.texture is x.texture`, and a Texture the user built comes back as
    // itself), else allocates and registers a new one. nullptr -> None.
    static PyObject* pyobject_for(const std::shared_ptr<PyTexture>& tex);
    // Same as pyobject_for(shared_from_this()); RuntimeError if not make_shared-owned.
    PyObject* pyObject();
    static PyObject* repr(PyObject*);
    static void dealloc(PyTextureObject* self);
    static Py_hash_t hash(PyObject*);
    static int init(PyTextureObject*, PyObject*, PyObject*);
    static PyObject* pynew(PyTypeObject* type, PyObject* args=NULL, PyObject* kwds=NULL);
    
    // Effective display dimensions (resolves -1 defaults)
    int getDisplayWidth() const { return display_width >= 0 ? display_width : sprite_width; }
    int getDisplayHeight() const { return display_height >= 0 ? display_height : sprite_height; }

    // Getters for properties
    static PyObject* get_sprite_width(PyTextureObject* self, void* closure);
    static PyObject* get_sprite_height(PyTextureObject* self, void* closure);
    static PyObject* get_sheet_width(PyTextureObject* self, void* closure);
    static PyObject* get_sheet_height(PyTextureObject* self, void* closure);
    static PyObject* get_sprite_count(PyTextureObject* self, void* closure);
    static PyObject* get_source(PyTextureObject* self, void* closure);
    static PyObject* get_display_width(PyTextureObject* self, void* closure);
    static PyObject* get_display_height(PyTextureObject* self, void* closure);
    static PyObject* get_display_offset_x(PyTextureObject* self, void* closure);
    static PyObject* get_display_offset_y(PyTextureObject* self, void* closure);
    
    static PyGetSetDef getsetters[];

    // Methods (classmethods and instance methods)
    static PyObject* from_bytes(PyObject* cls, PyObject* args, PyObject* kwds);
    static PyObject* composite(PyObject* cls, PyObject* args, PyObject* kwds);
    static PyObject* hsl_shift(PyTextureObject* self, PyObject* args, PyObject* kwds);
    static PyMethodDef methods[];
};

namespace mcrfpydef {
    inline PyTypeObject PyTextureType = {
        .ob_base = PyVarObject_HEAD_INIT(NULL, 0)
        .tp_name = "mcrfpy.Texture",
        .tp_basicsize = sizeof(PyTextureObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)PyTexture::dealloc,
        .tp_repr = PyTexture::repr,
        .tp_hash = PyTexture::hash,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR(
            "Texture(filename: str, sprite_width: int = 0, sprite_height: int = 0, "
            "display_size: tuple = None, display_origin: tuple = None)\n\n"
            "A texture atlas for sprites and tiles.\n\n"
            "Args:\n"
            "    filename: Path to an image file (PNG, BMP, etc.).\n"
            "    sprite_width: Width of each sprite cell in pixels (0 = full image).\n"
            "    sprite_height: Height of each sprite cell in pixels (0 = full image).\n"
            "    display_size: Optional (w, h) actual content size within each cell.\n"
            "    display_origin: Optional (x, y) content offset within each cell.\n\n"
            "Properties:\n"
            "    sprite_width, sprite_height (int, read-only): Cell dimensions.\n"
            "    sheet_width, sheet_height (int, read-only): Grid dimensions in cells.\n"
            "    sprite_count (int, read-only): Total number of sprite cells.\n"
            "    source (str, read-only): File path used to load this texture.\n"
            "    display_width, display_height (int, read-only): Content size within cells.\n"
            "    display_offset_x, display_offset_y (int, read-only): Content offset within cells.\n"
        ),
        .tp_weaklistoffset = offsetof(PyTextureObject, weakreflist),
        .tp_getset = PyTexture::getsetters,
        //.tp_base = &PyBaseObject_Type,
        .tp_init = (initproc)PyTexture::init,
        .tp_new = PyType_GenericNew, //PyTexture::pynew,
    };
}
