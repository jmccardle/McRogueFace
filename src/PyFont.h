#pragma once
#include "Common.h"
#include "Python.h"

class PyFont;

typedef struct {
    PyObject_HEAD
    std::shared_ptr<PyFont> data;
} PyFontObject;

class PyFont : public std::enable_shared_from_this<PyFont>
{
private:
    std::string source;
public:
    PyFont(std::string filename);
    sf::Font font;
    PyObject* pyObject();
    static PyObject* repr(PyObject*);
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
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Font",
        .tp_basicsize = sizeof(PyFontObject),
        .tp_itemsize = 0,
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
        .tp_getset = PyFont::getsetters,
        //.tp_base = &PyBaseObject_Type,
        .tp_init = (initproc)PyFont::init,
        .tp_new = PyType_GenericNew, //PyFont::pynew,
    };
}
