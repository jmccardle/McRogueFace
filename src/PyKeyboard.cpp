#include "PyKeyboard.h"
#include "McRFPy_Doc.h"
#include "McRFPy_API.h"
#include "GameEngine.h"

// #497: modifier state is the one carried by the key event being handled (see
// GameEngine::noteKeyModifiers), not a poll of the hardware.
static const GameEngine::KeyModifiers* current_modifiers()
{
    if (!McRFPy_API::game) {
        PyErr_SetString(PyExc_RuntimeError, "keyboard: the game engine is not running");
        return nullptr;
    }
    return &McRFPy_API::game->keyModifiers();
}

PyObject* PyKeyboard::repr(PyObject* obj)
{
    const auto* m = current_modifiers();
    if (!m) return NULL;

    std::ostringstream ss;
    ss << "<Keyboard shift=" << (m->shift ? "True" : "False")
       << " ctrl=" << (m->ctrl ? "True" : "False")
       << " alt=" << (m->alt ? "True" : "False")
       << " system=" << (m->system ? "True" : "False") << ">";

    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

PyObject* PyKeyboard::get_shift(PyObject* self, void* closure)
{
    const auto* m = current_modifiers();
    return m ? PyBool_FromLong(m->shift) : NULL;
}

PyObject* PyKeyboard::get_ctrl(PyObject* self, void* closure)
{
    const auto* m = current_modifiers();
    return m ? PyBool_FromLong(m->ctrl) : NULL;
}

PyObject* PyKeyboard::get_alt(PyObject* self, void* closure)
{
    const auto* m = current_modifiers();
    return m ? PyBool_FromLong(m->alt) : NULL;
}

PyObject* PyKeyboard::get_system(PyObject* self, void* closure)
{
    const auto* m = current_modifiers();
    return m ? PyBool_FromLong(m->system) : NULL;
}

PyGetSetDef PyKeyboard::getsetters[] = {
    {"shift", (getter)PyKeyboard::get_shift, NULL,
     MCRF_PROPERTY(shift, "True if Shift was held for the key event being handled (read-only). Read from the event stream, so it is correct inside on_key, for synthesized events and in headless runs."), NULL},
    {"ctrl", (getter)PyKeyboard::get_ctrl, NULL,
     MCRF_PROPERTY(ctrl, "True if Control was held for the key event being handled (read-only). See shift."), NULL},
    {"alt", (getter)PyKeyboard::get_alt, NULL,
     MCRF_PROPERTY(alt, "True if Alt was held for the key event being handled (read-only). See shift."), NULL},
    {"system", (getter)PyKeyboard::get_system, NULL,
     MCRF_PROPERTY(system, "True if the System key (Win/Cmd) was held for the key event being handled (read-only). See shift."), NULL},
    {NULL}
};
