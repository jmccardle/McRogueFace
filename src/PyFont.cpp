#include "PyFont.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"


PyFont::PyFont(std::string filename)
: source(filename)
{
    font = sf::Font();
    font.loadFromFile(source);
}

PyObject* PyFont::pyObject()
{
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Font");
    //PyObject* obj = PyType_GenericAlloc(&mcrfpydef::PyFontType, 0);
    PyObject* obj = PyFont::pynew(type, Py_None, Py_None);
    try {
        ((PyFontObject*)obj)->data = shared_from_this();
    }
    catch (std::bad_weak_ptr& e)
    {
        std::cout << "Bad weak ptr: shared_from_this() failed in PyFont::pyObject(); did you create a PyFont outside of std::make_shared? enjoy your segfault, soon!" << std::endl;
    }
    // TODO - shared_from_this will raise an exception if the object does not have a shared pointer. Constructor should be made private; write a factory function
    return obj;
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
    self->data = std::make_shared<PyFont>(filename);
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
