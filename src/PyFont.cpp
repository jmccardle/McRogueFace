#include "PyFont.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"
#include "PyWrap.h"

#if !defined(MCRF_HEADLESS)
#include <ft2build.h>
#include FT_FREETYPE_H
#endif

#if !defined(MCRF_HEADLESS) && !defined(MCRF_SDL2)
// #478: SFML 2.6's sf::Font keeps its FT_Face private and has no ascent getter, so the
// SFML build opens the same file with the same FreeType (the one SFML links) for metrics.
static FT_Library metrics_library()
{
    static FT_Library library = nullptr;
    if (!library && FT_Init_FreeType(&library) != 0) library = nullptr;
    return library;
}
#endif

PyFont::PyFont(std::string filename)
: source(filename)
{
    font = sf::Font();
    load_ok = font.loadFromFile(source);
#if !defined(MCRF_HEADLESS) && !defined(MCRF_SDL2)
    if (load_ok) {
        FT_Library library = metrics_library();
        FT_Face face = nullptr;
        if (!library || FT_New_Face(library, source.c_str(), 0, &face) != 0) {
            load_ok = false;  // SFML read it but FreeType can't: no metrics, so no layout
        } else {
            metrics_face = face;
        }
    }
#endif
}

bool PyFont::metrics(unsigned int characterSize, Metrics& out)
{
    auto it = metrics_cache.find(characterSize);
    if (it != metrics_cache.end()) { out = it->second; return true; }
#if defined(MCRF_HEADLESS)
    return false;  // no font rasterizer, no metrics
#else
  #if defined(MCRF_SDL2)
    FT_Face face = static_cast<FT_Face>(font.getFTFace());
  #else
    FT_Face face = static_cast<FT_Face>(metrics_face);
  #endif
    if (!face) return false;
    if (characterSize == 0) {
        out = Metrics{};  // nothing is drawn at size 0
    } else {
        if (FT_Set_Pixel_Sizes(face, 0, characterSize) != 0) return false;
        // 26.6 fixed point. `height` is what both backends advance per line: SFML's
        // Font::getLineSpacing() and the SDL2 FontAtlas line height read the same field.
        out.ascent = face->size->metrics.ascender / 64.0f;
        out.descent = -face->size->metrics.descender / 64.0f;
        out.line_height = face->size->metrics.height / 64.0f;
    }
    metrics_cache[characterSize] = out;
    return true;
#endif
}

bool PyFont::ascent(unsigned int characterSize, float& out)
{
    Metrics m;
    if (!metrics(characterSize, m)) return false;
    out = m.ascent;
    return true;
}

bool PyFont::metricsOrRaise(unsigned int characterSize, Metrics& out)
{
    if (metrics(characterSize, out)) return true;
#if defined(MCRF_HEADLESS)
    PyErr_SetString(PyExc_RuntimeError,
        "font metrics are not available in an MCRF_HEADLESS build (no font rasterizer)");
#else
    PyErr_Format(PyExc_ValueError, "font '%s' has no metrics at size %u",
                 source.c_str(), characterSize);
#endif
    return false;
}

PyObject* PyFont::py_metrics(PyFontObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = { "size", nullptr };
    int size;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "i", const_cast<char**>(keywords), &size))
        return NULL;
    if (size < 1 || size > 2048) {
        PyErr_Format(PyExc_ValueError, "size must be between 1 and 2048 pixels, got %d", size);
        return NULL;
    }
    Metrics m;
    if (!self->data->metricsOrRaise(static_cast<unsigned int>(size), m)) return NULL;
    return Py_BuildValue("(fff)", m.ascent, m.descent, m.line_height);
}

PyMethodDef PyFont::methods[] = {
    {"metrics", (PyCFunction)PyFont::py_metrics, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(Font, metrics,
         MCRF_SIG("(size: int)", "tuple[float, float, float]"),
         MCRF_DESC("Vertical metrics of this font at a pixel size, as a Caption of that "
                   "font_size lays it out: (ascent, descent, line_height)."),
         MCRF_ARGS_START
         MCRF_ARG("size", "Pixel size (a Caption's font_size), 1 to 2048")
         MCRF_RETURNS("(ascent, descent, line_height) in px: ascent above the baseline, "
                      "descent below it (positive), and the baseline-to-baseline distance "
                      "between lines of multi-line text")
         MCRF_RAISES("ValueError", "size is out of range, or the font has no metrics at it")
         MCRF_RAISES("RuntimeError", "in an MCRF_HEADLESS build, which has no font rasterizer")
     )},
    {NULL}
};

PyFont::~PyFont()
{
#if !defined(MCRF_HEADLESS) && !defined(MCRF_SDL2)
    if (metrics_face) FT_Done_Face(static_cast<FT_Face>(metrics_face));
#endif
    // #430: drop the wrapper-cache entry (a no-op once Python is gone).
    if (serial_number != 0) mcrf::unregister_wrapper(serial_number);
}

PyObject* PyFont::pyobject_for(const std::shared_ptr<PyFont>& font)
{
    if (!font) Py_RETURN_NONE;
    return mcrf::cached_wrapper<PyFontObject>(font->serial_number, &mcrfpydef::PyFontType,
        [&](PyFontObject* o) {
            new (&o->data) std::shared_ptr<PyFont>(font);
            o->weakreflist = NULL;
        });
}

PyObject* PyFont::pyObject()
{
    auto self = weak_from_this().lock();
    if (!self) {
        PyErr_SetString(PyExc_RuntimeError, "PyFont was not created with std::make_shared");
        return NULL;
    }
    return pyobject_for(self);
}

void PyFont::dealloc(PyFontObject* self)
{
    if (self->weakreflist != NULL) PyObject_ClearWeakRefs((PyObject*)self);
    // Releasing the last owner runs ~PyFont, which unregisters the serial.
    self->data.~shared_ptr<PyFont>();
    Py_TYPE(self)->tp_free((PyObject*)self);
}

PyObject* PyFont::repr(PyObject* obj)
{
    PyFontObject* self = (PyFontObject*)obj;
    std::ostringstream ss;
    if (!self->data)
    {
        ss << "<Font [invalid internal object]>";
        std::string repr_str = ss.str();
        return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
    }
    auto& pfont = *(self->data);
    ss << "<Font (family=" << pfont.font.getInfo().family << ") source=`" << pfont.source << "`>";
    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

Py_hash_t PyFont::hash(PyObject* obj)
{
    auto self = (PyFontObject*)obj;
    return reinterpret_cast<Py_hash_t>(self->data.get());
}

int PyFont::init(PyFontObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = { "filename", nullptr };
    char* filename;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "s", const_cast<char**>(keywords), &filename))
        return -1;
    auto font = std::make_shared<PyFont>(filename);
    // #478: a font that did not load has no metrics to lay text out with (SFML printed why).
    if (!font->loaded()) {
        PyErr_Format(PyExc_IOError, "Failed to load font from file: %s", filename);
        return -1;
    }
    // #430: a re-run __init__ swaps in a new PyFont; the old one must stop answering
    // with this (now different) wrapper.
    if (self->data && self->data->serial_number != 0) {
        mcrf::unregister_wrapper(self->data->serial_number);
    }
    self->data = font;
    // #430: a Font the user built is THE wrapper for its PyFont.
    if (mcrf::register_wrapper(self->data->serial_number, (PyObject*)self) < 0) return -1;
    return 0;
}

PyObject* PyFont::pynew(PyTypeObject* type, PyObject* args, PyObject* kwds)
{
    return (PyObject*)type->tp_alloc(type, 0);
}

PyObject* PyFont::get_family(PyFontObject* self, void* closure)
{
    return PyUnicode_FromString(self->data->font.getInfo().family.c_str());
}

PyObject* PyFont::get_source(PyFontObject* self, void* closure)
{
    return PyUnicode_FromString(self->data->source.c_str());
}

PyGetSetDef PyFont::getsetters[] = {
    {"family", (getter)PyFont::get_family, NULL,
     MCRF_PROPERTY(family, "Font family name (str, read-only). Retrieved from font metadata."), NULL},
    {"source", (getter)PyFont::get_source, NULL,
     MCRF_PROPERTY(source, "Source filename path (str, read-only). The path used to load this font."), NULL},
    {NULL}  // Sentinel
};
