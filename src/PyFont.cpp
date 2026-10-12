#include "PyFont.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"
#include "PyWrap.h"


PyFont::PyFont(std::string filename)
: source(filename)
{
    font = sf::Font();
    font.loadFromFile(source);
}

PyFont::~PyFont()
{
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
    // #430: a re-run __init__ swaps in a new PyFont; the old one must stop answering
    // with this (now different) wrapper.
    if (self->data && self->data->serial_number != 0) {
        mcrf::unregister_wrapper(self->data->serial_number);
    }
    self->data = std::make_shared<PyFont>(filename);
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
