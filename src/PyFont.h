#pragma once
#include "Common.h"
#include "Python.h"

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
public:
    PyFont(std::string filename);
    ~PyFont();
    PyFont(const PyFont&) = delete;
    PyFont& operator=(const PyFont&) = delete;
    sf::Font font;
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
