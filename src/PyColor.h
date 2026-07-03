#pragma once
#include "Common.h"
#include "Python.h"

class PyColor;
class UIDrawable; // forward declare for pointer

typedef struct {
    PyObject_HEAD
    sf::Color data;
} PyColorObject;

class PyColor
{
private:
public:
    sf::Color data;
    PyColor(sf::Color);
    void set(sf::Color);
    sf::Color get();
    PyObject* pyObject();
    static sf::Color fromPy(PyObject*);
    static sf::Color fromPy(PyColorObject*);
    static PyObject* repr(PyObject*);
    static Py_hash_t hash(PyObject*);
    static PyObject* richcompare(PyObject*, PyObject*, int);
    static int init(PyColorObject*, PyObject*, PyObject*);
    static PyObject* pynew(PyTypeObject* type, PyObject* args=NULL, PyObject* kwds=NULL);
    static PyObject* get_member(PyObject*, void*);
    static int set_member(PyObject*, PyObject*, void*);
    
    // Color helper methods
    static PyObject* from_hex(PyObject* cls, PyObject* args);
    static PyObject* to_hex(PyColorObject* self, PyObject* Py_UNUSED(ignored));
    static PyObject* lerp(PyColorObject* self, PyObject* args);
    
    static PyGetSetDef getsetters[];
    static PyMethodDef methods[];
    static PyColorObject* from_arg(PyObject*);
};

namespace mcrfpydef {
    inline PyTypeObject PyColorType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Color",
        .tp_basicsize = sizeof(PyColorObject),
        .tp_itemsize = 0,
        .tp_repr = PyColor::repr,
        .tp_hash = PyColor::hash,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR(
            "Color(r: int = 0, g: int = 0, b: int = 0, a: int = 255)\n"
            "\n"
            "RGBA color representation.\n"
            "\n"
            "Args:\n"
            "    r: Red component (0-255)\n"
            "    g: Green component (0-255)\n"
            "    b: Blue component (0-255)\n"
            "    a: Alpha component (0-255, default 255 = opaque)\n"
            "\n"
            "Note:\n"
            "    Color is a VALUE TYPE (frozen 1.0 contract): properties that return a\n"
            "    Color (e.g. frame.fill_color) return a fresh COPY, so mutating a component\n"
            "    of the returned object is a silent no-op on the original. The two supported\n"
            "    idioms are read-modify-writeback and whole-value assignment:\n"
            "\n"
            "        # This does NOT work:\n"
            "        frame.fill_color.r = 255  # Modifies a temporary copy\n"
            "\n"
            "        # Read-modify-writeback:\n"
            "        c = frame.fill_color\n"
            "        c.r = 255\n"
            "        frame.fill_color = c\n"
            "\n"
            "        # Whole-value assignment:\n"
            "        frame.fill_color = mcrfpy.Color(255, 0, 0)\n"
            "\n"
            "    See also: API stability policy (docs/api-stability.md)\n"
        ),
        .tp_richcompare = PyColor::richcompare,
        .tp_methods = PyColor::methods,
        .tp_getset = PyColor::getsetters,
        .tp_init = (initproc)PyColor::init,
        .tp_new = PyColor::pynew,
    };
}
