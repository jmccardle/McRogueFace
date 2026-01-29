#include "PyCallable.h"
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

    // Convert button string to MouseButton enum (#222, #232)
    int button_val = 0;  // Default to LEFT
    if (button == "left") button_val = 0;
    else if (button == "right") button_val = 1;
    else if (button == "middle") button_val = 2;
    else if (button == "x1") button_val = 3;
    else if (button == "x2") button_val = 4;
    else if (button == "wheel_up") button_val = 10;   // SCROLL_UP
    else if (button == "wheel_down") button_val = 11; // SCROLL_DOWN

    PyObject* button_enum = nullptr;
    if (PyMouseButton::mouse_button_enum_class) {
        button_enum = PyObject_CallFunction(PyMouseButton::mouse_button_enum_class, "i", button_val);
    }
    if (!button_enum) {
        // Fallback to string if enum creation fails
        PyErr_Clear();
        button_enum = PyUnicode_FromString(button.c_str());
    }

    // Convert action string to InputState enum (#222)
    int action_val = (action == "start") ? 0 : 1;  // PRESSED=0, RELEASED=1

    PyObject* action_enum = nullptr;
    if (PyInputState::input_state_enum_class) {
        action_enum = PyObject_CallFunction(PyInputState::input_state_enum_class, "i", action_val);
    }
    if (!action_enum) {
        // Fallback to string if enum creation fails
        PyErr_Clear();
        action_enum = PyUnicode_FromString(action.c_str());
    }

    PyObject* args = Py_BuildValue("(OOO)", pos, button_enum, action_enum);
    Py_DECREF(pos);
    Py_DECREF(button_enum);
    Py_DECREF(action_enum);

    PyObject* retval = PyCallable::call(args, NULL);
    Py_DECREF(args);
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

    // Convert key string to Key enum
    sf::Keyboard::Key sfml_key = PyKey::from_legacy_string(key.c_str());
    PyObject* key_enum = PyObject_CallFunction(PyKey::key_enum_class, "i", static_cast<int>(sfml_key));
    if (!key_enum) {
        std::cerr << "Failed to create Key enum for key: " << key << std::endl;
        PyErr_Print();
        PyErr_Clear();
        return;
    }

    // Convert action string to InputState enum
    int action_val = (action == "start" || action == "pressed") ? 0 : 1;  // PRESSED = 0, RELEASED = 1
    PyObject* action_enum = PyObject_CallFunction(PyInputState::input_state_enum_class, "i", action_val);
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
    PyObject* vector_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    if (!vector_type) {
        std::cerr << "Failed to get Vector type for hover callback" << std::endl;
        PyErr_Print();
        PyErr_Clear();
        return;
    }
    PyObject* pos = PyObject_CallFunction(vector_type, "ff", mousepos.x, mousepos.y);
    Py_DECREF(vector_type);
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
        std::cerr << "Hover callback raised an exception:" << std::endl;
        PyErr_Print();
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
    PyObject* vector_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    if (!vector_type) {
        std::cerr << "Failed to get Vector type for cell hover callback" << std::endl;
        PyErr_Print();
        PyErr_Clear();
        return;
    }
    PyObject* pos = PyObject_CallFunction(vector_type, "ii", cellpos.x, cellpos.y);
    Py_DECREF(vector_type);
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
        std::cerr << "Cell hover callback raised an exception:" << std::endl;
        PyErr_Print();
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
