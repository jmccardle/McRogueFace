#include "PyCallable.h"
#include "McRFPy_API.h"
#include "GameEngine.h"
#include "PyVector.h"

PyCallable::PyCallable(PyObject* _target)
{
    target = Py_XNewRef(_target);
}

PyCallable::PyCallable(const PyCallable& other)
{
    target = Py_XNewRef(other.target);
}

PyCallable& PyCallable::operator=(const PyCallable& other)
{
    if (this != &other) {
        PyObject* old_target = target;
        target = Py_XNewRef(other.target);
        Py_XDECREF(old_target);
    }
    return *this;
}

PyCallable::~PyCallable()
{
    if (target)
        Py_DECREF(target);
}

PyObject* PyCallable::call(PyObject* args, PyObject* kwargs)
{
    return PyObject_Call(target, args, kwargs);
}

bool PyCallable::isNone() const
{
    return (target == Py_None || target == NULL);
}


PyClickCallable::PyClickCallable(PyObject* _target)
: PyCallable(_target)
{}

PyClickCallable::PyClickCallable()
: PyCallable(Py_None)
{}

void PyClickCallable::call(sf::Vector2f mousepos, std::string button, std::string action)
{
    // Create a Vector object for the position - must fetch the finalized type from the module
    PyObject* vector_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    if (!vector_type) {
        std::cerr << "Failed to get Vector type for click callback" << std::endl;
        PyErr_Print();
        PyErr_Clear();
        return;
    }
    PyObject* pos = PyObject_CallFunction(vector_type, "ff", mousepos.x, mousepos.y);
    Py_DECREF(vector_type);
    if (!pos) {
        std::cerr << "Failed to create Vector object for click callback" << std::endl;
        PyErr_Print();
        PyErr_Clear();
        return;
    }
    PyObject* args = Py_BuildValue("(Oss)", pos, button.c_str(), action.c_str());
    Py_DECREF(pos);  // Py_BuildValue increments the refcount
    PyObject* retval = PyCallable::call(args, NULL);
    if (!retval)
    {
        std::cerr << "Click callback raised an exception:" << std::endl;
        PyErr_Print();
        PyErr_Clear();

        // Check if we should exit on exception
        if (McRFPy_API::game && McRFPy_API::game->getConfig().exit_on_exception) {
            McRFPy_API::signalPythonException();
        }
    } else if (retval != Py_None)
    {
        std::cout << "ClickCallable returned a non-None value. It's not an error, it's just not being saved or used." << std::endl;
        std::cout << PyUnicode_AsUTF8(PyObject_Repr(retval)) << std::endl;
    }
}

PyObject* PyClickCallable::borrow()
{
    return target;
}

PyKeyCallable::PyKeyCallable(PyObject* _target)
: PyCallable(_target)
{}

PyKeyCallable::PyKeyCallable()
: PyCallable(Py_None)
{}

void PyKeyCallable::call(std::string key, std::string action)
{
    if (target == Py_None || target == NULL) return;
    PyObject* args = Py_BuildValue("(ss)", key.c_str(), action.c_str());
    PyObject* retval = PyCallable::call(args, NULL);
    if (!retval)
    {
        std::cerr << "Key callback raised an exception:" << std::endl;
        PyErr_Print();
        PyErr_Clear();

        // Check if we should exit on exception
        if (McRFPy_API::game && McRFPy_API::game->getConfig().exit_on_exception) {
            McRFPy_API::signalPythonException();
        }
    } else if (retval != Py_None)
    {
        std::cout << "KeyCallable returned a non-None value. It's not an error, it's just not being saved or used." << std::endl;
    }
}
