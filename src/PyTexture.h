#pragma once
#include "Common.h"
#include "Python.h"

class PyTexture;

typedef struct {
    PyObject_HEAD
        std::shared_ptr<PyTexture> data;
} PyTextureObject;

class PyTexture : public std::enable_shared_from_this<PyTexture>
{
private:
    sf::Texture texture;
    std::string source;
    int sheet_width, sheet_height;
public:
    int sprite_width, sprite_height; // just use them read only, OK?
    PyTexture(std::string filename, int sprite_w, int sprite_h);
    sf::Sprite sprite(int index, sf::Vector2f pos = sf::Vector2f(0, 0), sf::Vector2f s = sf::Vector2f(1.0, 1.0));

    PyObject* pyObject();
    static PyObject* repr(PyObject*);
    static Py_hash_t hash(PyObject*);
    static int init(PyTextureObject*, PyObject*, PyObject*);
    static PyObject* pynew(PyTypeObject* type, PyObject* args=NULL, PyObject* kwds=NULL);
};

namespace mcrfpydef {
    static PyTypeObject PyTextureType = {
        .tp_name = "mcrfpy.Texture",
        .tp_basicsize = sizeof(PyTextureObject),
        .tp_itemsize = 0,
        .tp_repr = PyTexture::repr,
        .tp_hash = PyTexture::hash,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("SFML Texture Object"),
        //.tp_base = &PyBaseObject_Type,
        .tp_init = (initproc)PyTexture::init,
        .tp_new = PyType_GenericNew, //PyTexture::pynew,
    };
}
