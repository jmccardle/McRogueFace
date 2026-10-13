#pragma once
#include "Common.h"
#include "Python.h"
#include <map>

class PyFont;

// #430: the struct is tp_alloc'd (zero-filled, not constructed). `data` is
// placement-new'd by whoever fills it and destroyed in PyFont::dealloc.
typedef struct {
    PyObject_HEAD
    std::shared_ptr<PyFont> data;
    PyObject* weakreflist;  // the wrapper cache holds weak references (#430)
} PyFontObject;

class PyFont : public std::enable_shared_from_this<PyFont>
{
private:
    std::string source;
    bool load_ok = false;
    // #478, SFML desktop only: SFML 2.6 does not expose a font's ascent, so a second
    // FreeType face on the same file answers it (FT_Face, typeless as in sf::Font).
    void* metrics_face = nullptr;
    std::map<unsigned int, float> ascent_cache;
public:
    PyFont(std::string filename);
    ~PyFont();
    PyFont(const PyFont&) = delete;
    PyFont& operator=(const PyFont&) = delete;
    sf::Font font;
    // #478: the font's ascent in px at `characterSize` (FreeType's
    // face->size->metrics.ascender after FT_Set_Pixel_Sizes(face, 0, characterSize), the
    // call SFML and the SDL2 backend both make). False when the font has no face.
    bool ascent(unsigned int characterSize, float& out);
    // #478: whether the file loaded (SFML's face, and on desktop our own metrics face).
    bool loaded() const { return load_ok; }
    // #430: PythonObjectCache key for this font's one Python wrapper (0 = none yet).
    uint64_t serial_number = 0;
    // #430: the one cache-aware conversion (see PyTexture::pyobject_for). nullptr -> None.
    static PyObject* pyobject_for(const std::shared_ptr<PyFont>& font);
    // Same as pyobject_for(shared_from_this()); RuntimeError if not make_shared-owned.
    PyObject* pyObject();
    static PyObject* repr(PyObject*);
    static void dealloc(PyFontObject* self);
    static Py_hash_t hash(PyObject*);
    static int init(PyFontObject*, PyObject*, PyObject*);
    static PyObject* pynew(PyTypeObject* type, PyObject* args=NULL, PyObject* kwds=NULL);
    
    // Getters for properties
    static PyObject* get_family(PyFontObject* self, void* closure);
    static PyObject* get_source(PyFontObject* self, void* closure);
    
    static PyGetSetDef getsetters[];
};

namespace mcrfpydef {
    inline PyTypeObject PyFontType = {
        .ob_base = PyVarObject_HEAD_INIT(NULL, 0)
        .tp_name = "mcrfpy.Font",
        .tp_basicsize = sizeof(PyFontObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)PyFont::dealloc,
        .tp_repr = PyFont::repr,
        //.tp_hash = PyFont::hash,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR(
            "Font(filename: str)\n\n"
            "A font resource for rendering text in Caption elements.\n\n"
            "Args:\n"
            "    filename: Path to a TrueType (.ttf) or OpenType (.otf) font file.\n\n"
            "Properties:\n"
            "    family (str, read-only): Font family name from metadata.\n"
            "    source (str, read-only): File path used to load this font.\n"
        ),
        .tp_weaklistoffset = offsetof(PyFontObject, weakreflist),
        .tp_getset = PyFont::getsetters,
        //.tp_base = &PyBaseObject_Type,
        .tp_init = (initproc)PyFont::init,
        .tp_new = PyType_GenericNew, //PyFont::pynew,
    };
}
