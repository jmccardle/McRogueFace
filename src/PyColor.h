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
    // #450: THE conversion for every Python value written to a Color: attribute setters,
    // constructor kwargs, item assignment, method arguments and animate() targets.
    // Accepts a Color (or subclass) or anything Color(value) accepts -- an (r, g, b[, a])
    // tuple of ints in 0-255, or a colour string (name, "source:name", "#hex"; #458) --
    // and raises exactly what Color(value) raises otherwise.
    // Never clamps, wraps, or substitutes a default. Optional arguments decide what None
    // means before calling this; to_color itself rejects None as Color(None) does.
    static bool to_color(PyObject* value, sf::Color& out);
    static PyObject* repr(PyObject*);
    static Py_hash_t hash(PyObject*);
    static PyObject* richcompare(PyObject*, PyObject*, int);
    static int init(PyColorObject*, PyObject*, PyObject*);
    static PyObject* pynew(PyTypeObject* type, PyObject* args=NULL, PyObject* kwds=NULL);
    static PyObject* get_member(PyObject*, void*);
    static int set_member(PyObject*, PyObject*, void*);
    
    // Color helper methods
    static PyObject* from_hex(PyObject* cls, PyObject* args);
    static PyObject* names(PyObject* cls, PyObject* args, PyObject* kwds);
    static PyObject* to_hex(PyColorObject* self, PyObject* Py_UNUSED(ignored));
    static PyObject* lerp(PyColorObject* self, PyObject* args);
    
    static PyGetSetDef getsetters[];
    static PyMethodDef methods[];
};

namespace mcrfpydef {
    inline PyTypeObject PyColorType = {
        .ob_base = PyVarObject_HEAD_INIT(NULL, 0)
        .tp_name = "mcrfpy.Color",
        .tp_basicsize = sizeof(PyColorObject),
        .tp_itemsize = 0,
        .tp_repr = PyColor::repr,
        .tp_hash = PyColor::hash,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR(
            "Color(r: int, g: int, b: int, a: int = 255)\n"
            "Color(rgba: tuple[int, int, int] | tuple[int, int, int, int])\n"
            "Color(color: str, a: int = 255)\n"
            "\n"
            "RGBA color representation.\n"
            "\n"
            "Args:\n"
            "    r: Red component (0-255)\n"
            "    g: Green component (0-255)\n"
            "    b: Blue component (0-255)\n"
            "    a: Alpha component (0-255, default 255 = opaque)\n"
            "    color: A color name ('red', 'Dark Green'), a source-qualified name\n"
            "        ('xkcd:dust', 'crayola:Red'), or hex ('#f00', '#f008', '#ff0000',\n"
            "        '#ff000080'). Names ignore case and everything but letters and digits.\n"
            "        An unprefixed name takes the first source that has it: css, then\n"
            "        xkcd, then crayola, then jenny. Color.names() lists them. Unknown\n"
            "        names raise ValueError naming close matches.\n"
            "\n"
            "    Every Color property accepts the same values: frame.fill_color = 'red'.\n"
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
