#include "PyCallable.h"
#include "PyWrap.h"
#include "McRFPy_API.h"
#include "GameEngine.h"
#include "PyVector.h"
#include "PyMouseButton.h"
#include "PyInputState.h"
#include "PyKey.h"

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
    // #468: an owner destroyed after Py_Finalize (none should hold a callback by then)
    // must not touch the freed interpreter.
    if (target && mcrf::python_alive())
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
    // Create a Vector object for the position
    PyObject* pos = PyObject_CallFunction((PyObject*)&mcrfpydef::PyVectorType, "ff", mousepos.x, mousepos.y);
    if (!pos) {
        std::cerr << "Failed to create Vector object for click callback" << std::endl;
        PyErr_Print();
        PyErr_Clear();
        return;
    }

    // (#222, #232, #428) The shared conversions. An unknown name is an engine bug: it
    // is reported, not delivered as a LEFT click or a bare string.
    PyObject* button_enum = PyMouseButton::from_action_name(button);
    PyObject* action_enum = button_enum ? PyInputState::from_action_type(action) : nullptr;
    if (!action_enum) {
        Py_DECREF(pos);
        Py_XDECREF(button_enum);
        std::cerr << "Click callback not called:" << std::endl;
        PyErr_Print();
        return;
    }

    PyObject* args = Py_BuildValue("(OOO)", pos, button_enum, action_enum);
    Py_DECREF(pos);
    Py_DECREF(button_enum);
    Py_DECREF(action_enum);

    PyObject* retval = PyCallable::call(args, NULL);
    Py_DECREF(args);
    if (!retval)
    {
        mcrf::print_callback_error("Click");
        PyErr_Clear();

        // Check if we should exit on exception
        if (McRFPy_API::game && McRFPy_API::game->getConfig().exit_on_exception) {
            McRFPy_API::signalPythonException();
        }
    } else if (retval != Py_None)
    {
        std::cout << "ClickCallable returned a non-None value. It's not an error, it's just not being saved or used." << std::endl;
        if (mcrf::PyRef repr{PyObject_Repr(retval)}) {
            std::cout << PyUnicode_AsUTF8(repr.get()) << std::endl;
        }
        Py_DECREF(retval);
    } else {
        Py_DECREF(retval);
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

    // Convert key string to Key enum (#344: cached member, not EnumMeta.__call__)
    sf::Keyboard::Key sfml_key = PyKey::from_legacy_string(key.c_str());
    PyObject* key_enum = PyKey::get_enum_member(static_cast<int>(sfml_key));
    if (!key_enum) {
        std::cerr << "Failed to create Key enum for key: " << key << std::endl;
        PyErr_Print();
        PyErr_Clear();
        return;
    }

    // Convert action string to InputState enum (#344: cached member, #428: shared)
    PyObject* action_enum = PyInputState::from_action_type(action);
    if (!action_enum) {
        Py_DECREF(key_enum);
        std::cerr << "Failed to create InputState enum for action: " << action << std::endl;
        PyErr_Print();
        PyErr_Clear();
        return;
    }

    PyObject* args = Py_BuildValue("(OO)", key_enum, action_enum);
    Py_DECREF(key_enum);
    Py_DECREF(action_enum);

    PyObject* retval = PyCallable::call(args, NULL);
    if (!retval)
    {
        mcrf::print_callback_error("Key");
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

// #495 - PyTextCallable: scene.on_text(text: str)
PyTextCallable::PyTextCallable(PyObject* _target)
: PyCallable(_target)
{}

PyTextCallable::PyTextCallable()
: PyCallable(Py_None)
{}

void PyTextCallable::call(const std::string& utf8)
{
    if (target == Py_None || target == NULL) return;

    mcrf::PyRef text(PyUnicode_DecodeUTF8(utf8.data(), utf8.size(), "strict"));
    if (!text) {
        mcrf::print_callback_error("Text");
        PyErr_Clear();
        return;
    }
    mcrf::PyRef args(PyTuple_Pack(1, text.get()));
    PyObject* retval = args ? PyCallable::call(args.get(), NULL) : NULL;
    if (!retval)
    {
        mcrf::print_callback_error("Text");
        PyErr_Clear();
        if (McRFPy_API::game && McRFPy_API::game->getConfig().exit_on_exception) {
            McRFPy_API::signalPythonException();
        }
        return;
    }
    Py_DECREF(retval);
}

// #230 - PyHoverCallable implementation (position-only for on_enter/on_exit/on_move)
PyHoverCallable::PyHoverCallable(PyObject* _target)
: PyCallable(_target)
{}

PyHoverCallable::PyHoverCallable()
: PyCallable(Py_None)
{}

void PyHoverCallable::call(sf::Vector2f mousepos)
{
    if (target == Py_None || target == NULL) return;

    // Create a Vector object for the position
    PyObject* pos = PyObject_CallFunction((PyObject*)&mcrfpydef::PyVectorType, "ff", mousepos.x, mousepos.y);
    if (!pos) {
        std::cerr << "Failed to create Vector object for hover callback" << std::endl;
        PyErr_Print();
        PyErr_Clear();
        return;
    }

    // #230 - Hover callbacks take only (pos), not (pos, button, action)
    PyObject* args = Py_BuildValue("(O)", pos);
    Py_DECREF(pos);

    PyObject* retval = PyCallable::call(args, NULL);
    Py_DECREF(args);
    if (!retval)
    {
        mcrf::print_callback_error("Hover");
        PyErr_Clear();

        // Check if we should exit on exception
        if (McRFPy_API::game && McRFPy_API::game->getConfig().exit_on_exception) {
            McRFPy_API::signalPythonException();
        }
    } else if (retval != Py_None)
    {
        std::cout << "HoverCallable returned a non-None value. It's not an error, it's just not being saved or used." << std::endl;
        Py_DECREF(retval);
    } else {
        Py_DECREF(retval);
    }
}

PyObject* PyHoverCallable::borrow()
{
    return target;
}

// #230 - PyCellHoverCallable implementation (cell position-only for on_cell_enter/on_cell_exit)
PyCellHoverCallable::PyCellHoverCallable(PyObject* _target)
: PyCallable(_target)
{}

PyCellHoverCallable::PyCellHoverCallable()
: PyCallable(Py_None)
{}

void PyCellHoverCallable::call(sf::Vector2i cellpos)
{
    if (target == Py_None || target == NULL) return;

    // Create a Vector object for the cell position
    PyObject* pos = PyObject_CallFunction((PyObject*)&mcrfpydef::PyVectorType, "ii", cellpos.x, cellpos.y);
    if (!pos) {
        std::cerr << "Failed to create Vector object for cell hover callback" << std::endl;
        PyErr_Print();
        PyErr_Clear();
        return;
    }

    // #230 - Cell hover callbacks take only (cell_pos), not (cell_pos, button, action)
    PyObject* args = Py_BuildValue("(O)", pos);
    Py_DECREF(pos);

    PyObject* retval = PyCallable::call(args, NULL);
    Py_DECREF(args);
    if (!retval)
    {
        mcrf::print_callback_error("Cell hover");
        PyErr_Clear();

        // Check if we should exit on exception
        if (McRFPy_API::game && McRFPy_API::game->getConfig().exit_on_exception) {
            McRFPy_API::signalPythonException();
        }
    } else if (retval != Py_None)
    {
        std::cout << "CellHoverCallable returned a non-None value. It's not an error, it's just not being saved or used." << std::endl;
        Py_DECREF(retval);
    } else {
        Py_DECREF(retval);
    }
}

PyObject* PyCellHoverCallable::borrow()
{
    return target;
}
