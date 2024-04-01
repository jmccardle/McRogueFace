#include "PyFont.h"


PyFont::PyFont(std::string filename)
: source(filename)
{
    font = sf::Font();
    font.loadFromFile(source);
}

PyObject* PyFont::pyObject()
{
    PyObject* obj = PyType_GenericAlloc(&mcrfpydef::PyFontType, 0);
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
