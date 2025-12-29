#include "PyKeyboard.h"
#include "McRFPy_Doc.h"

PyObject* PyKeyboard::repr(PyObject* obj)
{
    // Show current state in repr for debugging
    bool shift = sf::Keyboard::isKeyPressed(sf::Keyboard::LShift) ||
                 sf::Keyboard::isKeyPressed(sf::Keyboard::RShift);
    bool ctrl = sf::Keyboard::isKeyPressed(sf::Keyboard::LControl) ||
                sf::Keyboard::isKeyPressed(sf::Keyboard::RControl);
    bool alt = sf::Keyboard::isKeyPressed(sf::Keyboard::LAlt) ||
               sf::Keyboard::isKeyPressed(sf::Keyboard::RAlt);
    bool system = sf::Keyboard::isKeyPressed(sf::Keyboard::LSystem) ||
                  sf::Keyboard::isKeyPressed(sf::Keyboard::RSystem);

    std::ostringstream ss;
    ss << "<Keyboard shift=" << (shift ? "True" : "False")
       << " ctrl=" << (ctrl ? "True" : "False")
       << " alt=" << (alt ? "True" : "False")
       << " system=" << (system ? "True" : "False") << ">";

    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

PyObject* PyKeyboard::get_shift(PyObject* self, void* closure)
{
    bool pressed = sf::Keyboard::isKeyPressed(sf::Keyboard::LShift) ||
                   sf::Keyboard::isKeyPressed(sf::Keyboard::RShift);
    return PyBool_FromLong(pressed);
}

PyObject* PyKeyboard::get_ctrl(PyObject* self, void* closure)
{
    bool pressed = sf::Keyboard::isKeyPressed(sf::Keyboard::LControl) ||
                   sf::Keyboard::isKeyPressed(sf::Keyboard::RControl);
    return PyBool_FromLong(pressed);
}

PyObject* PyKeyboard::get_alt(PyObject* self, void* closure)
{
    bool pressed = sf::Keyboard::isKeyPressed(sf::Keyboard::LAlt) ||
                   sf::Keyboard::isKeyPressed(sf::Keyboard::RAlt);
    return PyBool_FromLong(pressed);
}

PyObject* PyKeyboard::get_system(PyObject* self, void* closure)
{
    bool pressed = sf::Keyboard::isKeyPressed(sf::Keyboard::LSystem) ||
                   sf::Keyboard::isKeyPressed(sf::Keyboard::RSystem);
    return PyBool_FromLong(pressed);
}

PyGetSetDef PyKeyboard::getsetters[] = {
    {"shift", (getter)PyKeyboard::get_shift, NULL,
     MCRF_PROPERTY(shift, "True if either Shift key is currently pressed (read-only)."), NULL},
    {"ctrl", (getter)PyKeyboard::get_ctrl, NULL,
     MCRF_PROPERTY(ctrl, "True if either Control key is currently pressed (read-only)."), NULL},
    {"alt", (getter)PyKeyboard::get_alt, NULL,
     MCRF_PROPERTY(alt, "True if either Alt key is currently pressed (read-only)."), NULL},
    {"system", (getter)PyKeyboard::get_system, NULL,
     MCRF_PROPERTY(system, "True if either System key (Win/Cmd) is currently pressed (read-only)."), NULL},
    {NULL}
};
