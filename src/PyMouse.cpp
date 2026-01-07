#include "PyMouse.h"
#include "McRFPy_API.h"
#include "McRFPy_Automation.h"
#include "GameEngine.h"
#include "McRFPy_Doc.h"
#include "PyVector.h"

int PyMouse::init(PyMouseObject* self, PyObject* args, PyObject* kwds)
{
    // Initialize tracked state to SFML defaults
    self->cursor_visible = true;
    self->cursor_grabbed = false;
    return 0;
}

// Helper to get current mouse position, handling headless mode
static sf::Vector2i getMousePosition()
{
    GameEngine* engine = McRFPy_API::game;

    if (!engine || !engine->getRenderTargetPtr()) {
        return McRFPy_Automation::getSimulatedMousePosition();
    }

    if (engine->isHeadless()) {
        // In headless mode, return simulated position from automation
        return McRFPy_Automation::getSimulatedMousePosition();
    }

    // In windowed mode, get actual mouse position relative to window
    if (auto* window = dynamic_cast<sf::RenderWindow*>(engine->getRenderTargetPtr())) {
        return sf::Mouse::getPosition(*window);
    }

    // Fallback to simulated position
    return McRFPy_Automation::getSimulatedMousePosition();
}

PyObject* PyMouse::repr(PyObject* obj)
{
    sf::Vector2i pos = getMousePosition();
    bool left = sf::Mouse::isButtonPressed(sf::Mouse::Left);
    bool right = sf::Mouse::isButtonPressed(sf::Mouse::Right);
    bool middle = sf::Mouse::isButtonPressed(sf::Mouse::Middle);

    PyMouseObject* self = (PyMouseObject*)obj;

    std::ostringstream ss;
    ss << "<Mouse pos=(" << pos.x << ", " << pos.y << ")"
       << " left=" << (left ? "True" : "False")
       << " right=" << (right ? "True" : "False")
       << " middle=" << (middle ? "True" : "False")
       << " visible=" << (self->cursor_visible ? "True" : "False")
       << " grabbed=" << (self->cursor_grabbed ? "True" : "False") << ">";

    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

PyObject* PyMouse::get_x(PyObject* self, void* closure)
{
    sf::Vector2i pos = getMousePosition();
    return PyLong_FromLong(pos.x);
}

PyObject* PyMouse::get_y(PyObject* self, void* closure)
{
    sf::Vector2i pos = getMousePosition();
    return PyLong_FromLong(pos.y);
}

PyObject* PyMouse::get_pos(PyObject* self, void* closure)
{
    sf::Vector2i pos = getMousePosition();

    // Return a Vector object
    auto vector_type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    if (!vector_type) {
        PyErr_SetString(PyExc_RuntimeError, "Vector type not found in mcrfpy module");
        return NULL;
    }
    PyObject* result = PyObject_CallFunction((PyObject*)vector_type, "ff", (float)pos.x, (float)pos.y);
    Py_DECREF(vector_type);
    return result;
}

PyObject* PyMouse::get_left(PyObject* self, void* closure)
{
    bool pressed = sf::Mouse::isButtonPressed(sf::Mouse::Left);
    return PyBool_FromLong(pressed);
}

PyObject* PyMouse::get_right(PyObject* self, void* closure)
{
    bool pressed = sf::Mouse::isButtonPressed(sf::Mouse::Right);
    return PyBool_FromLong(pressed);
}

PyObject* PyMouse::get_middle(PyObject* self, void* closure)
{
    bool pressed = sf::Mouse::isButtonPressed(sf::Mouse::Middle);
    return PyBool_FromLong(pressed);
}

PyObject* PyMouse::get_visible(PyObject* self, void* closure)
{
    PyMouseObject* mouse = (PyMouseObject*)self;
    return PyBool_FromLong(mouse->cursor_visible);
}

int PyMouse::set_visible(PyObject* self, PyObject* value, void* closure)
{
    if (!PyBool_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "visible must be a boolean");
        return -1;
    }

    PyMouseObject* mouse = (PyMouseObject*)self;
    bool visible = PyObject_IsTrue(value);
    mouse->cursor_visible = visible;

    // Apply to window if available
    GameEngine* engine = McRFPy_API::game;
    if (engine && !engine->isHeadless()) {
        if (auto* window = dynamic_cast<sf::RenderWindow*>(engine->getRenderTargetPtr())) {
            window->setMouseCursorVisible(visible);
        }
    }

    return 0;
}

PyObject* PyMouse::get_grabbed(PyObject* self, void* closure)
{
    PyMouseObject* mouse = (PyMouseObject*)self;
    return PyBool_FromLong(mouse->cursor_grabbed);
}

int PyMouse::set_grabbed(PyObject* self, PyObject* value, void* closure)
{
    if (!PyBool_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "grabbed must be a boolean");
        return -1;
    }

    PyMouseObject* mouse = (PyMouseObject*)self;
    bool grabbed = PyObject_IsTrue(value);
    mouse->cursor_grabbed = grabbed;

    // Apply to window if available
    GameEngine* engine = McRFPy_API::game;
    if (engine && !engine->isHeadless()) {
        if (auto* window = dynamic_cast<sf::RenderWindow*>(engine->getRenderTargetPtr())) {
            window->setMouseCursorGrabbed(grabbed);
        }
    }

    return 0;
}

PyGetSetDef PyMouse::getsetters[] = {
    // Position (read-only)
    {"x", (getter)PyMouse::get_x, NULL,
     MCRF_PROPERTY(x, "Current mouse X position in window coordinates (read-only)."), NULL},
    {"y", (getter)PyMouse::get_y, NULL,
     MCRF_PROPERTY(y, "Current mouse Y position in window coordinates (read-only)."), NULL},
    {"pos", (getter)PyMouse::get_pos, NULL,
     MCRF_PROPERTY(pos, "Current mouse position as Vector (read-only)."), NULL},

    // Button state (read-only)
    {"left", (getter)PyMouse::get_left, NULL,
     MCRF_PROPERTY(left, "True if left mouse button is currently pressed (read-only)."), NULL},
    {"right", (getter)PyMouse::get_right, NULL,
     MCRF_PROPERTY(right, "True if right mouse button is currently pressed (read-only)."), NULL},
    {"middle", (getter)PyMouse::get_middle, NULL,
     MCRF_PROPERTY(middle, "True if middle mouse button is currently pressed (read-only)."), NULL},

    // Cursor control (read-write)
    {"visible", (getter)PyMouse::get_visible, (setter)PyMouse::set_visible,
     MCRF_PROPERTY(visible, "Whether the mouse cursor is visible (default: True)."), NULL},
    {"grabbed", (getter)PyMouse::get_grabbed, (setter)PyMouse::set_grabbed,
     MCRF_PROPERTY(grabbed, "Whether the mouse cursor is confined to the window (default: False)."), NULL},

    {NULL}
};
