#include "McRFPy_Automation.h"
#include "Display.h"
#include "PyMouseButton.h"
#include "PyWrap.h"
#include "McRFPy_API.h"
#include "GameEngine.h"
#include "PyPositionHelper.h"
#include "PyVector.h"
#include "McRFPy_Doc.h"
#include <fstream>
#include <iostream>
#include <sstream>
#include <unordered_map>

// #111 - Static member for simulated mouse position in headless mode
sf::Vector2i McRFPy_Automation::simulated_mouse_pos(0, 0);

// #111 - Get simulated mouse position for headless mode
sf::Vector2i McRFPy_Automation::getSimulatedMousePosition() {
    return simulated_mouse_pos;
}

// Helper function to get game engine
GameEngine* McRFPy_Automation::getGameEngine() {
    return McRFPy_API::game;
}

// Sleep helper
void McRFPy_Automation::sleep_ms(int milliseconds) {
    std::this_thread::sleep_for(std::chrono::milliseconds(milliseconds));
}

// Convert string to SFML key code
sf::Keyboard::Key McRFPy_Automation::stringToKey(const std::string& keyName) {
    static const std::unordered_map<std::string, sf::Keyboard::Key> keyMap = {
        // Letters
        {"a", sf::Keyboard::A}, {"b", sf::Keyboard::B}, {"c", sf::Keyboard::C},
        {"d", sf::Keyboard::D}, {"e", sf::Keyboard::E}, {"f", sf::Keyboard::F},
        {"g", sf::Keyboard::G}, {"h", sf::Keyboard::H}, {"i", sf::Keyboard::I},
        {"j", sf::Keyboard::J}, {"k", sf::Keyboard::K}, {"l", sf::Keyboard::L},
        {"m", sf::Keyboard::M}, {"n", sf::Keyboard::N}, {"o", sf::Keyboard::O},
        {"p", sf::Keyboard::P}, {"q", sf::Keyboard::Q}, {"r", sf::Keyboard::R},
        {"s", sf::Keyboard::S}, {"t", sf::Keyboard::T}, {"u", sf::Keyboard::U},
        {"v", sf::Keyboard::V}, {"w", sf::Keyboard::W}, {"x", sf::Keyboard::X},
        {"y", sf::Keyboard::Y}, {"z", sf::Keyboard::Z},

        // Numbers
        {"0", sf::Keyboard::Num0}, {"1", sf::Keyboard::Num1}, {"2", sf::Keyboard::Num2},
        {"3", sf::Keyboard::Num3}, {"4", sf::Keyboard::Num4}, {"5", sf::Keyboard::Num5},
        {"6", sf::Keyboard::Num6}, {"7", sf::Keyboard::Num7}, {"8", sf::Keyboard::Num8},
        {"9", sf::Keyboard::Num9},

        // Function keys
        {"f1", sf::Keyboard::F1}, {"f2", sf::Keyboard::F2}, {"f3", sf::Keyboard::F3},
        {"f4", sf::Keyboard::F4}, {"f5", sf::Keyboard::F5}, {"f6", sf::Keyboard::F6},
        {"f7", sf::Keyboard::F7}, {"f8", sf::Keyboard::F8}, {"f9", sf::Keyboard::F9},
        {"f10", sf::Keyboard::F10}, {"f11", sf::Keyboard::F11}, {"f12", sf::Keyboard::F12},
        {"f13", sf::Keyboard::F13}, {"f14", sf::Keyboard::F14}, {"f15", sf::Keyboard::F15},

        // Special keys
        {"escape", sf::Keyboard::Escape}, {"esc", sf::Keyboard::Escape},
        {"enter", sf::Keyboard::Enter}, {"return", sf::Keyboard::Enter},
        {"space", sf::Keyboard::Space}, {" ", sf::Keyboard::Space},
        {"tab", sf::Keyboard::Tab}, {"\t", sf::Keyboard::Tab},
        {"backspace", sf::Keyboard::BackSpace},
        {"delete", sf::Keyboard::Delete}, {"del", sf::Keyboard::Delete},
        {"insert", sf::Keyboard::Insert},
        {"home", sf::Keyboard::Home},
        {"end", sf::Keyboard::End},
        {"pageup", sf::Keyboard::PageUp}, {"pgup", sf::Keyboard::PageUp},
        {"pagedown", sf::Keyboard::PageDown}, {"pgdn", sf::Keyboard::PageDown},

        // Arrow keys
        {"left", sf::Keyboard::Left},
        {"right", sf::Keyboard::Right},
        {"up", sf::Keyboard::Up},
        {"down", sf::Keyboard::Down},

        // Modifiers
        {"ctrl", sf::Keyboard::LControl}, {"ctrlleft", sf::Keyboard::LControl},
        {"ctrlright", sf::Keyboard::RControl},
        {"alt", sf::Keyboard::LAlt}, {"altleft", sf::Keyboard::LAlt},
        {"altright", sf::Keyboard::RAlt},
        {"shift", sf::Keyboard::LShift}, {"shiftleft", sf::Keyboard::LShift},
        {"shiftright", sf::Keyboard::RShift},
        {"win", sf::Keyboard::LSystem}, {"winleft", sf::Keyboard::LSystem},
        {"winright", sf::Keyboard::RSystem}, {"command", sf::Keyboard::LSystem},

        // Punctuation
        {",", sf::Keyboard::Comma}, {".", sf::Keyboard::Period},
        {"/", sf::Keyboard::Slash}, {"\\", sf::Keyboard::BackSlash},
        {";", sf::Keyboard::SemiColon}, {"'", sf::Keyboard::Quote},
        {"[", sf::Keyboard::LBracket}, {"]", sf::Keyboard::RBracket},
        {"-", sf::Keyboard::Dash}, {"=", sf::Keyboard::Equal},
        {"`", sf::Keyboard::Grave}, {"grave", sf::Keyboard::Grave},

        // Numpad
        {"num0", sf::Keyboard::Numpad0}, {"num1", sf::Keyboard::Numpad1},
        {"num2", sf::Keyboard::Numpad2}, {"num3", sf::Keyboard::Numpad3},
        {"num4", sf::Keyboard::Numpad4}, {"num5", sf::Keyboard::Numpad5},
        {"num6", sf::Keyboard::Numpad6}, {"num7", sf::Keyboard::Numpad7},
        {"num8", sf::Keyboard::Numpad8}, {"num9", sf::Keyboard::Numpad9},
        {"add", sf::Keyboard::Add}, {"subtract", sf::Keyboard::Subtract},
        {"multiply", sf::Keyboard::Multiply}, {"divide", sf::Keyboard::Divide},

        // Other
        {"pause", sf::Keyboard::Pause},
        // No capslock/numlock/scrolllock: sf::Keyboard has no such keys (#504). An unknown
        // name returns Unknown and the callers raise ValueError, instead of faking a Ctrl.
    };

    auto it = keyMap.find(keyName);
    if (it != keyMap.end()) {
        return it->second;
    }
    return sf::Keyboard::Unknown;
}

// #367 - Inject a window-level event. These carry no coordinates and no button, which
// is why they get their own entry point rather than riding injectMouseEvent.
void McRFPy_Automation::injectWindowEvent(sf::Event::EventType type) {
    auto engine = getGameEngine();
    if (!engine) return;

    sf::Event event;
    event.type = type;
    engine->processEvent(event);
}

// Inject mouse event into the game engine
void McRFPy_Automation::injectMouseEvent(sf::Event::EventType type, int x, int y, sf::Mouse::Button button, float scrollDelta) {
    auto engine = getGameEngine();
    if (!engine) return;

    // #111 - Track simulated mouse position for headless mode
    if (type == sf::Event::MouseMoved ||
        type == sf::Event::MouseButtonPressed ||
        type == sf::Event::MouseButtonReleased) {
        simulated_mouse_pos = sf::Vector2i(x, y);
    }

    sf::Event event;
    event.type = type;

    switch (type) {
        case sf::Event::MouseMoved:
            event.mouseMove.x = x;
            event.mouseMove.y = y;
            break;
        case sf::Event::MouseButtonPressed:
        case sf::Event::MouseButtonReleased:
            event.mouseButton.button = button;
            event.mouseButton.x = x;
            event.mouseButton.y = y;
            break;
        case sf::Event::MouseWheelScrolled:
            event.mouseWheelScroll.wheel = sf::Mouse::VerticalWheel;
            event.mouseWheelScroll.delta = scrollDelta; // #317: scroll amount is its own arg
            event.mouseWheelScroll.x = x;               // position now honored on both axes
            event.mouseWheelScroll.y = y;
            break;
        default:
            break;
    }

    engine->processEvent(event);
}

// Inject keyboard event into the game engine
void McRFPy_Automation::injectKeyEvent(sf::Event::EventType type, sf::Keyboard::Key key) {
    auto engine = getGameEngine();
    if (!engine) return;

    sf::Event event;
    event.type = type;

    if (type == sf::Event::KeyPressed || type == sf::Event::KeyReleased) {
        // #497: a synthesized event never touches the hardware, so its modifiers are the
        // injected modifier keys that are held, in the order they were injected. As with
        // a real keyboard, the modifier's own press already counts and its release does not.
        static bool held[sf::Keyboard::KeyCount] = {};
        if (key >= 0 && key < sf::Keyboard::KeyCount)
            held[key] = (type == sf::Event::KeyPressed);
        event.key.code = key;
        event.key.shift = held[sf::Keyboard::LShift] || held[sf::Keyboard::RShift];
        event.key.control = held[sf::Keyboard::LControl] || held[sf::Keyboard::RControl];
        event.key.alt = held[sf::Keyboard::LAlt] || held[sf::Keyboard::RAlt];
        event.key.system = held[sf::Keyboard::LSystem] || held[sf::Keyboard::RSystem];
    }

    engine->noteKeyModifiers(event);
    if (engine->filterDevInput(event)) return;  // #496: same front door as a window event
    engine->processEvent(event);
}

// #495 - Inject a typed code point (sf::Event::TextEntered -> scene.on_text).
void McRFPy_Automation::injectTextEvent(uint32_t codepoint) {
    auto engine = getGameEngine();
    if (!engine) return;

    sf::Event event;
    event.type = sf::Event::TextEntered;
    event.text.unicode = codepoint;
    if (engine->filterDevInput(event)) return;  // #496: the console owns the keyboard while open
    engine->processEvent(event);
}

// #495 - Text is what on_text receives: a Unicode scalar that is not a control character
// (Enter, Tab, Backspace, Escape, DEL and C1 are keys, delivered to on_key only).
bool McRFPy_Automation::isTypeable(Py_UCS4 ch) {
    if (ch < 0x20 || (ch >= 0x7F && ch <= 0x9F)) return false;
    if (ch >= 0xD800 && ch <= 0xDFFF) return false;
    return ch <= 0x10FFFF;
}

// #433 - typewrite() simulates key presses, so each character maps to the key that
// types it on a US layout, with Shift for uppercase and shifted symbols. As a keyboard
// does, a character that types text also delivers it (#495) between press and release.
bool McRFPy_Automation::charToKeyStroke(Py_UCS4 ch, sf::Keyboard::Key* key, bool* shift) {
    *shift = false;
    if (ch >= 'a' && ch <= 'z') { *key = static_cast<sf::Keyboard::Key>(sf::Keyboard::A + (ch - 'a')); return true; }
    if (ch >= 'A' && ch <= 'Z') { *key = static_cast<sf::Keyboard::Key>(sf::Keyboard::A + (ch - 'A')); *shift = true; return true; }
    if (ch >= '0' && ch <= '9') { *key = static_cast<sf::Keyboard::Key>(sf::Keyboard::Num0 + (ch - '0')); return true; }

    struct Stroke { Py_UCS4 ch; sf::Keyboard::Key key; bool shift; };
    static const Stroke strokes[] = {
        {' ', sf::Keyboard::Space, false}, {'\n', sf::Keyboard::Enter, false},
        {'\t', sf::Keyboard::Tab, false},
        {',', sf::Keyboard::Comma, false}, {'<', sf::Keyboard::Comma, true},
        {'.', sf::Keyboard::Period, false}, {'>', sf::Keyboard::Period, true},
        {'/', sf::Keyboard::Slash, false}, {'?', sf::Keyboard::Slash, true},
        {';', sf::Keyboard::Semicolon, false}, {':', sf::Keyboard::Semicolon, true},
        {'\'', sf::Keyboard::Apostrophe, false}, {'"', sf::Keyboard::Apostrophe, true},
        {'[', sf::Keyboard::LBracket, false}, {'{', sf::Keyboard::LBracket, true},
        {']', sf::Keyboard::RBracket, false}, {'}', sf::Keyboard::RBracket, true},
        {'\\', sf::Keyboard::Backslash, false}, {'|', sf::Keyboard::Backslash, true},
        {'-', sf::Keyboard::Hyphen, false}, {'_', sf::Keyboard::Hyphen, true},
        {'=', sf::Keyboard::Equal, false}, {'+', sf::Keyboard::Equal, true},
        {'`', sf::Keyboard::Grave, false}, {'~', sf::Keyboard::Grave, true},
        {')', sf::Keyboard::Num0, true}, {'!', sf::Keyboard::Num1, true},
        {'@', sf::Keyboard::Num2, true}, {'#', sf::Keyboard::Num3, true},
        {'$', sf::Keyboard::Num4, true}, {'%', sf::Keyboard::Num5, true},
        {'^', sf::Keyboard::Num6, true}, {'&', sf::Keyboard::Num7, true},
        {'*', sf::Keyboard::Num8, true}, {'(', sf::Keyboard::Num9, true},
    };
    for (const auto& s : strokes) {
        if (s.ch == ch) { *key = s.key; *shift = s.shift; return true; }
    }
    return false;
}

// Screenshot implementation
// #153 - In headless mode, this is now SYNCHRONOUS: renders scene then captures
PyObject* McRFPy_Automation::_screenshot(PyObject* self, PyObject* args) {
    const char* filename;
    if (!PyArg_ParseTuple(args, "s", &filename)) {
        return NULL;
    }

    auto engine = getGameEngine();
    if (!engine) {
        PyErr_SetString(PyExc_RuntimeError, "Game engine not initialized");
        return NULL;
    }

    // Get the render target (#451: a headless one is created here, which needs a display)
    if (!mcrf::require_display_py("automation.screenshot()")) return NULL;
    sf::RenderTarget* target = &engine->getRenderTarget();

    // For RenderWindow (windowed mode), capture the current buffer
    if (auto* window = dynamic_cast<sf::RenderWindow*>(target)) {
        sf::Vector2u windowSize = window->getSize();
        sf::Texture texture;
        texture.create(windowSize.x, windowSize.y);
        texture.update(*window);

        if (texture.copyToImage().saveToFile(filename)) {
            Py_RETURN_TRUE;
        } else {
            Py_RETURN_FALSE;
        }
    }
    // For RenderTexture (headless mode) - SYNCHRONOUS render then capture
    else if (auto* renderTexture = dynamic_cast<sf::RenderTexture*>(target)) {
        // #153 - Force a synchronous render before capturing
        // This ensures we capture the CURRENT state, not the previous frame
        engine->renderScene();

        if (renderTexture->getTexture().copyToImage().saveToFile(filename)) {
            Py_RETURN_TRUE;
        } else {
            Py_RETURN_FALSE;
        }
    }

    PyErr_SetString(PyExc_RuntimeError, "Unknown render target type");
    return NULL;
}

// Get current mouse position - returns Vector object
PyObject* McRFPy_Automation::_position(PyObject* self, PyObject* args) {
    int x, y;

    auto engine = getGameEngine();
    if (!engine || !engine->getRenderTargetPtr()) {
        x = simulated_mouse_pos.x;
        y = simulated_mouse_pos.y;
    }
    else if (engine->isHeadless()) {
        // In headless mode, return the simulated mouse position (#111)
        x = simulated_mouse_pos.x;
        y = simulated_mouse_pos.y;
    }
    else if (auto* window = dynamic_cast<sf::RenderWindow*>(engine->getRenderTargetPtr())) {
        // In windowed mode, return the actual mouse position relative to window
        sf::Vector2i pos = sf::Mouse::getPosition(*window);
        x = pos.x;
        y = pos.y;
    }
    else {
        // Fallback to simulated position
        x = simulated_mouse_pos.x;
        y = simulated_mouse_pos.y;
    }

    // Return a Vector object
    PyObject* result = PyObject_CallFunction((PyObject*)&mcrfpydef::PyVectorType, "ff", (float)x, (float)y);
    return result;
}

// Get screen size - returns Vector object
PyObject* McRFPy_Automation::_size(PyObject* self, PyObject* args) {
    auto engine = getGameEngine();
    if (!engine) {
        return PyObject_CallFunction((PyObject*)&mcrfpydef::PyVectorType, "ff", 1024.0f, 768.0f);  // Default size
    }

    sf::Vector2u size = engine->renderSize();
    return PyObject_CallFunction((PyObject*)&mcrfpydef::PyVectorType, "ff", (float)size.x, (float)size.y);
}

// Check if coordinates are on screen - accepts onScreen(x, y) or onScreen(pos)
PyObject* McRFPy_Automation::_onScreen(PyObject* self, PyObject* args, PyObject* kwargs) {
    int x, y;
    if (!PyPosition_ParseInt(args, kwargs, &x, &y)) {
        return NULL;
    }

    auto engine = getGameEngine();
    if (!engine) {
        Py_RETURN_FALSE;
    }

    sf::Vector2u size = engine->renderSize();
    if (x >= 0 && x < (int)size.x && y >= 0 && y < (int)size.y) {
        Py_RETURN_TRUE;
    } else {
        Py_RETURN_FALSE;
    }
}

// Move mouse to position - accepts moveTo(pos, duration)
PyObject* McRFPy_Automation::_moveTo(PyObject* self, PyObject* args, PyObject* kwargs) {
    static const char* kwlist[] = {"pos", "duration", NULL};
    PyObject* pos_obj;
    float duration = 0.0f;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|f", const_cast<char**>(kwlist),
                                     &pos_obj, &duration)) {
        return NULL;
    }

    int x, y;
    if (!PyPosition_FromObjectInt(pos_obj, &x, &y)) {
        return NULL;
    }

    // TODO: Implement smooth movement with duration
    injectMouseEvent(sf::Event::MouseMoved, x, y);

    if (duration > 0) {
        sleep_ms(static_cast<int>(duration * 1000));
    }

    Py_RETURN_NONE;
}

// #363 - Simulate the cursor leaving the window. sf::Event::MouseLeft carries no
// coordinates, so this takes none; the engine reports the last known position to the
// exit callbacks it fires. The simulated position is deliberately NOT moved -- the
// cursor is outside the window, not at some new point inside it.
PyObject* McRFPy_Automation::_mouseLeave(PyObject* self, PyObject* args) {
    injectMouseEvent(sf::Event::MouseLeft, simulated_mouse_pos.x, simulated_mouse_pos.y);
    Py_RETURN_NONE;
}

// #367 - Simulate the window losing focus (alt-tab). Like a window-leave, this clears
// all hover state: an unfocused window receives no MouseMoved, so any drawable still
// marked hovered would stay lit indefinitely. The simulated cursor position is left
// alone -- focus and pointer location are independent, and the pointer has not moved.
PyObject* McRFPy_Automation::_loseFocus(PyObject* self, PyObject* args) {
    injectWindowEvent(sf::Event::LostFocus);
    Py_RETURN_NONE;
}

// Move mouse relative - accepts moveRel(offset, duration)
PyObject* McRFPy_Automation::_moveRel(PyObject* self, PyObject* args, PyObject* kwargs) {
    static const char* kwlist[] = {"offset", "duration", NULL};
    PyObject* offset_obj;
    float duration = 0.0f;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|f", const_cast<char**>(kwlist),
                                     &offset_obj, &duration)) {
        return NULL;
    }

    int xOffset, yOffset;
    if (!PyPosition_FromObjectInt(offset_obj, &xOffset, &yOffset)) {
        return NULL;
    }

    // Get current position from Vector
    PyObject* pos = _position(self, NULL);
    if (!pos) return NULL;

    // Extract position from Vector object
    int currentX, currentY;
    if (!PyPosition_FromObjectInt(pos, &currentX, &currentY)) {
        Py_DECREF(pos);
        return NULL;
    }
    Py_DECREF(pos);

    // Move to new position
    injectMouseEvent(sf::Event::MouseMoved, currentX + xOffset, currentY + yOffset);

    if (duration > 0) {
        sleep_ms(static_cast<int>(duration * 1000));
    }

    Py_RETURN_NONE;
}

// Click implementation - accepts click(pos, clicks, interval, button) or click() for current position
PyObject* McRFPy_Automation::_click(PyObject* self, PyObject* args, PyObject* kwargs) {
    static const char* kwlist[] = {"pos", "clicks", "interval", "button", NULL};
    PyObject* pos_obj = Py_None;
    int clicks = 1;
    float interval = 0.0f;
    const char* button = "left";

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|Oifs", const_cast<char**>(kwlist),
                                     &pos_obj, &clicks, &interval, &button)) {
        return NULL;
    }

    int x, y;

    // If no position specified or None, use current position
    if (pos_obj == Py_None) {
        PyObject* pos = _position(self, NULL);
        if (!pos) return NULL;

        if (!PyPosition_FromObjectInt(pos, &x, &y)) {
            Py_DECREF(pos);
            return NULL;
        }
        Py_DECREF(pos);
    } else {
        if (!PyPosition_FromObjectInt(pos_obj, &x, &y)) {
            return NULL;
        }
    }

    // #428: shared table; an unknown name raises instead of clicking LEFT
    sf::Mouse::Button sfButton;
    if (!PyMouseButton::button_from_action_name(button, &sfButton)) return NULL;

    // Move to position first
    injectMouseEvent(sf::Event::MouseMoved, x, y);

    // Perform clicks
    for (int i = 0; i < clicks; i++) {
        if (i > 0 && interval > 0) {
            sleep_ms(static_cast<int>(interval * 1000));
        }

        injectMouseEvent(sf::Event::MouseButtonPressed, x, y, sfButton);
        sleep_ms(10);  // Small delay between press and release
        injectMouseEvent(sf::Event::MouseButtonReleased, x, y, sfButton);
    }

    Py_RETURN_NONE;
}

// Right click - accepts rightClick(pos) or rightClick() for current position
PyObject* McRFPy_Automation::_rightClick(PyObject* self, PyObject* args, PyObject* kwargs) {
    static const char* kwlist[] = {"pos", NULL};
    PyObject* pos_obj = Py_None;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|O", const_cast<char**>(kwlist), &pos_obj)) {
        return NULL;
    }

    // Build new args with button="right"
    PyObject* newKwargs = PyDict_New();
    if (mcrf::dict_steal(newKwargs, "button", PyUnicode_FromString("right")) < 0) { Py_DECREF(newKwargs); return NULL; }
    if (pos_obj != Py_None) {
        PyDict_SetItemString(newKwargs, "pos", pos_obj);
    }

    PyObject* result = _click(self, mcrf::PyRef(PyTuple_New(0)).get(), newKwargs);
    Py_DECREF(newKwargs);
    return result;
}

// Double click - accepts doubleClick(pos) or doubleClick() for current position
PyObject* McRFPy_Automation::_doubleClick(PyObject* self, PyObject* args, PyObject* kwargs) {
    static const char* kwlist[] = {"pos", NULL};
    PyObject* pos_obj = Py_None;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|O", const_cast<char**>(kwlist), &pos_obj)) {
        return NULL;
    }

    PyObject* newKwargs = PyDict_New();
    if (mcrf::dict_steal(newKwargs, "clicks", PyLong_FromLong(2)) < 0) { Py_DECREF(newKwargs); return NULL; }
    if (mcrf::dict_steal(newKwargs, "interval", PyFloat_FromDouble(0.1)) < 0) { Py_DECREF(newKwargs); return NULL; }
    if (pos_obj != Py_None) {
        PyDict_SetItemString(newKwargs, "pos", pos_obj);
    }

    PyObject* result = _click(self, mcrf::PyRef(PyTuple_New(0)).get(), newKwargs);
    Py_DECREF(newKwargs);
    return result;
}

// Type text
PyObject* McRFPy_Automation::_typewrite(PyObject* self, PyObject* args, PyObject* kwargs) {
    static const char* kwlist[] = {"message", "interval", NULL};
    PyObject* message;
    float interval = 0.0f;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "U|f", const_cast<char**>(kwlist),
                                     &message, &interval)) {
        return NULL;
    }

    // #433: resolve every character before sending anything, so a string with an
    // untypeable character fails whole instead of half-typed.
    struct KeyStroke { sf::Keyboard::Key key; bool shift; Py_UCS4 ch; };
    std::vector<KeyStroke> strokes;
    Py_ssize_t len = PyUnicode_GET_LENGTH(message);
    strokes.reserve(len);
    for (Py_ssize_t i = 0; i < len; i++) {
        Py_UCS4 ch = PyUnicode_READ_CHAR(message, i);
        KeyStroke s;
        s.ch = ch;
        if (!charToKeyStroke(ch, &s.key, &s.shift)) {
            PyObject* one = PyUnicode_FromOrdinal(ch);
            if (one) {
                PyErr_Format(PyExc_ValueError,
                             "typewrite(): no key types %R (index %zd); use keyDown()/hotkey() "
                             "for keys that are not characters", one, i);
                Py_DECREF(one);
            }
            return NULL;
        }
        strokes.push_back(s);
    }

    for (size_t i = 0; i < strokes.size(); i++) {
        if (i > 0 && interval > 0) {
            sleep_ms(static_cast<int>(interval * 1000));
        }
        const KeyStroke& s = strokes[i];
        if (s.shift) injectKeyEvent(sf::Event::KeyPressed, sf::Keyboard::LShift);
        injectKeyEvent(sf::Event::KeyPressed, s.key);
        if (isTypeable(s.ch)) injectTextEvent(s.ch);
        injectKeyEvent(sf::Event::KeyReleased, s.key);
        if (s.shift) injectKeyEvent(sf::Event::KeyReleased, sf::Keyboard::LShift);
    }

    Py_RETURN_NONE;
}

// #495 - Type text without keys: layout-, dead-key- and IME-produced characters that no
// US key stroke can express. Delivered to on_text only, one call per code point.
PyObject* McRFPy_Automation::_typeText(PyObject* self, PyObject* args) {
    PyObject* message;
    if (!PyArg_ParseTuple(args, "U", &message)) {
        return NULL;
    }

    // Validate the whole string before sending any of it.
    Py_ssize_t len = PyUnicode_GET_LENGTH(message);
    for (Py_ssize_t i = 0; i < len; i++) {
        Py_UCS4 ch = PyUnicode_READ_CHAR(message, i);
        if (!isTypeable(ch)) {
            PyErr_Format(PyExc_ValueError,
                         "typeText(): U+%04X (index %zd) is not text; control characters are "
                         "keys, use keyDown()/keyUp()", (unsigned)ch, i);
            return NULL;
        }
    }
    for (Py_ssize_t i = 0; i < len; i++) {
        injectTextEvent(PyUnicode_READ_CHAR(message, i));
    }
    Py_RETURN_NONE;
}

// Press and hold key
PyObject* McRFPy_Automation::_keyDown(PyObject* self, PyObject* args) {
    const char* keyName;
    if (!PyArg_ParseTuple(args, "s", &keyName)) {
        return NULL;
    }

    sf::Keyboard::Key key = stringToKey(keyName);
    if (key == sf::Keyboard::Unknown) {
        PyErr_Format(PyExc_ValueError, "Unknown key: %s", keyName);
        return NULL;
    }

    injectKeyEvent(sf::Event::KeyPressed, key);
    Py_RETURN_NONE;
}

// Release key
PyObject* McRFPy_Automation::_keyUp(PyObject* self, PyObject* args) {
    const char* keyName;
    if (!PyArg_ParseTuple(args, "s", &keyName)) {
        return NULL;
    }

    sf::Keyboard::Key key = stringToKey(keyName);
    if (key == sf::Keyboard::Unknown) {
        PyErr_Format(PyExc_ValueError, "Unknown key: %s", keyName);
        return NULL;
    }

    injectKeyEvent(sf::Event::KeyReleased, key);
    Py_RETURN_NONE;
}

// Hotkey combination
PyObject* McRFPy_Automation::_hotkey(PyObject* self, PyObject* args) {
    // Get all keys as separate arguments
    Py_ssize_t numKeys = PyTuple_Size(args);
    if (numKeys == 0) {
        PyErr_SetString(PyExc_ValueError, "hotkey() requires at least one key");
        return NULL;
    }

    // Press all keys
    for (Py_ssize_t i = 0; i < numKeys; i++) {
        PyObject* keyObj = PyTuple_GetItem(args, i);
        const char* keyName = PyUnicode_AsUTF8(keyObj);
        if (!keyName) {
            return NULL;
        }

        sf::Keyboard::Key key = stringToKey(keyName);
        if (key == sf::Keyboard::Unknown) {
            PyErr_Format(PyExc_ValueError, "Unknown key: %s", keyName);
            return NULL;
        }

        injectKeyEvent(sf::Event::KeyPressed, key);
        sleep_ms(10);  // Small delay between key presses
    }

    // Release all keys in reverse order
    for (Py_ssize_t i = numKeys - 1; i >= 0; i--) {
        PyObject* keyObj = PyTuple_GetItem(args, i);
        const char* keyName = PyUnicode_AsUTF8(keyObj);

        sf::Keyboard::Key key = stringToKey(keyName);
        injectKeyEvent(sf::Event::KeyReleased, key);
        sleep_ms(10);
    }

    Py_RETURN_NONE;
}

// Scroll wheel - accepts scroll(clicks, pos) or scroll(clicks) for current position
PyObject* McRFPy_Automation::_scroll(PyObject* self, PyObject* args, PyObject* kwargs) {
    static const char* kwlist[] = {"clicks", "pos", NULL};
    int clicks;
    PyObject* pos_obj = Py_None;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "i|O", const_cast<char**>(kwlist),
                                     &clicks, &pos_obj)) {
        return NULL;
    }

    int x, y;

    // If no position specified or None, use current position
    if (pos_obj == Py_None) {
        PyObject* pos = _position(self, NULL);
        if (!pos) return NULL;

        if (!PyPosition_FromObjectInt(pos, &x, &y)) {
            Py_DECREF(pos);
            return NULL;
        }
        Py_DECREF(pos);
    } else {
        if (!PyPosition_FromObjectInt(pos_obj, &x, &y)) {
            return NULL;
        }
    }

    // #432: dispatch hit-tests at the simulated mouse position, so move there first,
    // exactly as click(pos) does. Without this the scroll landed under the cursor.
    injectMouseEvent(sf::Event::MouseMoved, x, y);

    // Inject scroll event (#317: forward the resolved x/y position; clicks is
    // the scroll delta, passed via its own argument).
    injectMouseEvent(sf::Event::MouseWheelScrolled, x, y, sf::Mouse::Left, static_cast<float>(clicks));

    Py_RETURN_NONE;
}

// Other click types using the main click function - accepts middleClick(pos) or middleClick()
PyObject* McRFPy_Automation::_middleClick(PyObject* self, PyObject* args, PyObject* kwargs) {
    static const char* kwlist[] = {"pos", NULL};
    PyObject* pos_obj = Py_None;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|O", const_cast<char**>(kwlist), &pos_obj)) {
        return NULL;
    }

    PyObject* newKwargs = PyDict_New();
    if (mcrf::dict_steal(newKwargs, "button", PyUnicode_FromString("middle")) < 0) { Py_DECREF(newKwargs); return NULL; }
    if (pos_obj != Py_None) {
        PyDict_SetItemString(newKwargs, "pos", pos_obj);
    }

    PyObject* result = _click(self, mcrf::PyRef(PyTuple_New(0)).get(), newKwargs);
    Py_DECREF(newKwargs);
    return result;
}

// Triple click - accepts tripleClick(pos) or tripleClick()
PyObject* McRFPy_Automation::_tripleClick(PyObject* self, PyObject* args, PyObject* kwargs) {
    static const char* kwlist[] = {"pos", NULL};
    PyObject* pos_obj = Py_None;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|O", const_cast<char**>(kwlist), &pos_obj)) {
        return NULL;
    }

    PyObject* newKwargs = PyDict_New();
    if (mcrf::dict_steal(newKwargs, "clicks", PyLong_FromLong(3)) < 0) { Py_DECREF(newKwargs); return NULL; }
    if (mcrf::dict_steal(newKwargs, "interval", PyFloat_FromDouble(0.1)) < 0) { Py_DECREF(newKwargs); return NULL; }
    if (pos_obj != Py_None) {
        PyDict_SetItemString(newKwargs, "pos", pos_obj);
    }

    PyObject* result = _click(self, mcrf::PyRef(PyTuple_New(0)).get(), newKwargs);
    Py_DECREF(newKwargs);
    return result;
}

// Mouse button press/release - accepts mouseDown(pos, button) or mouseDown() for current position
PyObject* McRFPy_Automation::_mouseDown(PyObject* self, PyObject* args, PyObject* kwargs) {
    static const char* kwlist[] = {"pos", "button", NULL};
    PyObject* pos_obj = Py_None;
    const char* button = "left";

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|Os", const_cast<char**>(kwlist),
                                     &pos_obj, &button)) {
        return NULL;
    }

    int x, y;

    // If no position specified or None, use current position
    if (pos_obj == Py_None) {
        PyObject* pos = _position(self, NULL);
        if (!pos) return NULL;

        if (!PyPosition_FromObjectInt(pos, &x, &y)) {
            Py_DECREF(pos);
            return NULL;
        }
        Py_DECREF(pos);
    } else {
        if (!PyPosition_FromObjectInt(pos_obj, &x, &y)) {
            return NULL;
        }
    }

    // #428: shared table; an unknown name raises instead of clicking LEFT
    sf::Mouse::Button sfButton;
    if (!PyMouseButton::button_from_action_name(button, &sfButton)) return NULL;

    injectMouseEvent(sf::Event::MouseButtonPressed, x, y, sfButton);
    Py_RETURN_NONE;
}

// Mouse up - accepts mouseUp(pos, button) or mouseUp() for current position
PyObject* McRFPy_Automation::_mouseUp(PyObject* self, PyObject* args, PyObject* kwargs) {
    static const char* kwlist[] = {"pos", "button", NULL};
    PyObject* pos_obj = Py_None;
    const char* button = "left";

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|Os", const_cast<char**>(kwlist),
                                     &pos_obj, &button)) {
        return NULL;
    }

    int x, y;

    // If no position specified or None, use current position
    if (pos_obj == Py_None) {
        PyObject* pos = _position(self, NULL);
        if (!pos) return NULL;

        if (!PyPosition_FromObjectInt(pos, &x, &y)) {
            Py_DECREF(pos);
            return NULL;
        }
        Py_DECREF(pos);
    } else {
        if (!PyPosition_FromObjectInt(pos_obj, &x, &y)) {
            return NULL;
        }
    }

    // #428: shared table; an unknown name raises instead of clicking LEFT
    sf::Mouse::Button sfButton;
    if (!PyMouseButton::button_from_action_name(button, &sfButton)) return NULL;

    injectMouseEvent(sf::Event::MouseButtonReleased, x, y, sfButton);
    Py_RETURN_NONE;
}

// Drag operations - accepts dragTo(pos, duration, button)
PyObject* McRFPy_Automation::_dragTo(PyObject* self, PyObject* args, PyObject* kwargs) {
    static const char* kwlist[] = {"pos", "duration", "button", NULL};
    PyObject* pos_obj;
    float duration = 0.0f;
    const char* button = "left";

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|fs", const_cast<char**>(kwlist),
                                     &pos_obj, &duration, &button)) {
        return NULL;
    }

    int x, y;
    if (!PyPosition_FromObjectInt(pos_obj, &x, &y)) {
        return NULL;
    }

    // Get current position
    PyObject* pos = _position(self, NULL);
    if (!pos) return NULL;

    int startX, startY;
    if (!PyPosition_FromObjectInt(pos, &startX, &startY)) {
        Py_DECREF(pos);
        return NULL;
    }
    Py_DECREF(pos);

    // Mouse down at current position - create position tuple for the call
    PyObject* startPosObj = Py_BuildValue("(ii)", startX, startY);
    PyObject* downKwargs = PyDict_New();
    if (mcrf::dict_steal(downKwargs, "pos", startPosObj) < 0) { Py_XDECREF(downKwargs); return NULL; }
    if (mcrf::dict_steal(downKwargs, "button", PyUnicode_FromString(button)) < 0) { Py_DECREF(downKwargs); return NULL; }

    PyObject* downResult = _mouseDown(self, mcrf::PyRef(PyTuple_New(0)).get(), downKwargs);
    Py_DECREF(downKwargs);
    if (!downResult) return NULL;
    Py_DECREF(downResult);

    // Move to target position
    if (duration > 0) {
        // Smooth movement
        int steps = static_cast<int>(duration * 60);  // 60 FPS
        for (int i = 1; i <= steps; i++) {
            int currentX = startX + (x - startX) * i / steps;
            int currentY = startY + (y - startY) * i / steps;
            injectMouseEvent(sf::Event::MouseMoved, currentX, currentY);
            sleep_ms(1000 / 60);  // 60 FPS
        }
    } else {
        injectMouseEvent(sf::Event::MouseMoved, x, y);
    }

    // Mouse up at target position
    PyObject* endPosObj = Py_BuildValue("(ii)", x, y);
    PyObject* upKwargs = PyDict_New();
    if (mcrf::dict_steal(upKwargs, "pos", endPosObj) < 0) { Py_XDECREF(upKwargs); return NULL; }
    if (mcrf::dict_steal(upKwargs, "button", PyUnicode_FromString(button)) < 0) { Py_DECREF(upKwargs); return NULL; }

    PyObject* upResult = _mouseUp(self, mcrf::PyRef(PyTuple_New(0)).get(), upKwargs);
    Py_DECREF(upKwargs);
    if (!upResult) return NULL;
    Py_DECREF(upResult);

    Py_RETURN_NONE;
}

// Drag relative - accepts dragRel(offset, duration, button)
PyObject* McRFPy_Automation::_dragRel(PyObject* self, PyObject* args, PyObject* kwargs) {
    static const char* kwlist[] = {"offset", "duration", "button", NULL};
    PyObject* offset_obj;
    float duration = 0.0f;
    const char* button = "left";

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|fs", const_cast<char**>(kwlist),
                                     &offset_obj, &duration, &button)) {
        return NULL;
    }

    int xOffset, yOffset;
    if (!PyPosition_FromObjectInt(offset_obj, &xOffset, &yOffset)) {
        return NULL;
    }

    // Get current position
    PyObject* pos = _position(self, NULL);
    if (!pos) return NULL;

    int currentX, currentY;
    if (!PyPosition_FromObjectInt(pos, &currentX, &currentY)) {
        Py_DECREF(pos);
        return NULL;
    }
    Py_DECREF(pos);

    // Call dragTo with absolute position
    PyObject* targetPos = Py_BuildValue("(ii)", currentX + xOffset, currentY + yOffset);
    PyObject* dragKwargs = PyDict_New();
    if (mcrf::dict_steal(dragKwargs, "pos", targetPos) < 0) { Py_XDECREF(dragKwargs); return NULL; }
    if (mcrf::dict_steal(dragKwargs, "duration", PyFloat_FromDouble(duration)) < 0) { Py_DECREF(dragKwargs); return NULL; }
    if (mcrf::dict_steal(dragKwargs, "button", PyUnicode_FromString(button)) < 0) { Py_DECREF(dragKwargs); return NULL; }

    PyObject* result = _dragTo(self, mcrf::PyRef(PyTuple_New(0)).get(), dragKwargs);
    Py_DECREF(dragKwargs);

    return result;
}

// Method definitions for the automation module
static PyMethodDef automationMethods[] = {
    {"screenshot", McRFPy_Automation::_screenshot, METH_VARARGS,
     MCRF_METHOD(automation, screenshot,
         MCRF_SIG("(filename: str)", "bool"),
         MCRF_DESC("Save a screenshot of the current render target to the specified file."),
         MCRF_ARGS_START
         MCRF_ARG("filename", "Path to the output image file (PNG, JPG, etc.)")
         MCRF_RETURNS("True if the file was saved successfully, False otherwise")
         MCRF_RAISES("RuntimeError", "If the game engine or render target is not initialized")
     )},

    {"position", McRFPy_Automation::_position, METH_NOARGS,
     MCRF_METHOD(automation, position,
         MCRF_SIG("()", "Vector"),
         MCRF_DESC("Get the current mouse position as a Vector."),
         MCRF_RETURNS("Vector: current mouse position in screen coordinates")
     )},
    {"size", McRFPy_Automation::_size, METH_NOARGS,
     MCRF_METHOD(automation, size,
         MCRF_SIG("()", "Vector"),
         MCRF_DESC("Get the current screen (render target) size as a Vector."),
         MCRF_RETURNS("Vector: screen width and height in pixels")
     )},
    {"onScreen", (PyCFunction)McRFPy_Automation::_onScreen, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(automation, onScreen,
         MCRF_SIG("(x: int, y: int) or (pos: tuple | list | Vector)", "bool"),
         MCRF_DESC("Check if a position is within the screen bounds."),
         MCRF_ARGS_START
         MCRF_ARG("x", "X coordinate (int), when passing two separate int arguments")
         MCRF_ARG("y", "Y coordinate (int), when passing two separate int arguments")
         MCRF_ARG("pos", "Position as (x, y) tuple, [x, y] list, or Vector")
         MCRF_RETURNS("True if the position is on screen, False otherwise")
     )},

    {"moveTo", (PyCFunction)McRFPy_Automation::_moveTo, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(automation, moveTo,
         MCRF_SIG("(pos: tuple | list | Vector, duration: float = 0.0)", "None"),
         MCRF_DESC("Move the mouse cursor to the specified position."),
         MCRF_ARGS_START
         MCRF_ARG("pos", "Target position as (x, y) tuple, [x, y] list, or Vector")
         MCRF_ARG("duration", "Time in seconds to take for the movement (default 0.0)")
     )},
    {"moveRel", (PyCFunction)McRFPy_Automation::_moveRel, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(automation, moveRel,
         MCRF_SIG("(offset: tuple | list | Vector, duration: float = 0.0)", "None"),
         MCRF_DESC("Move the mouse cursor relative to its current position."),
         MCRF_ARGS_START
         MCRF_ARG("offset", "Offset as (x, y) tuple, [x, y] list, or Vector")
         MCRF_ARG("duration", "Time in seconds to take for the movement (default 0.0)")
     )},
    {"dragTo", (PyCFunction)McRFPy_Automation::_dragTo, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(automation, dragTo,
         MCRF_SIG("(pos: tuple | list | Vector, duration: float = 0.0, button: str = 'left')", "None"),
         MCRF_DESC("Drag the mouse from the current position to the specified position."),
         MCRF_ARGS_START
         MCRF_ARG("pos", "Target position as (x, y) tuple, [x, y] list, or Vector")
         MCRF_ARG("duration", "Time in seconds for the drag (default 0.0)")
         MCRF_ARG("button", "Mouse button to use: 'left', 'right', 'middle', 'x1' or 'x2' (default 'left')")
     )},
    {"dragRel", (PyCFunction)McRFPy_Automation::_dragRel, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(automation, dragRel,
         MCRF_SIG("(offset: tuple | list | Vector, duration: float = 0.0, button: str = 'left')", "None"),
         MCRF_DESC("Drag the mouse relative to its current position."),
         MCRF_ARGS_START
         MCRF_ARG("offset", "Offset as (x, y) tuple, [x, y] list, or Vector")
         MCRF_ARG("duration", "Time in seconds for the drag (default 0.0)")
         MCRF_ARG("button", "Mouse button to use: 'left', 'right', 'middle', 'x1' or 'x2' (default 'left')")
     )},

    {"click", (PyCFunction)McRFPy_Automation::_click, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(automation, click,
         MCRF_SIG("(pos: tuple | list | Vector | None = None, clicks: int = 1, interval: float = 0.0, button: str = 'left')", "None"),
         MCRF_DESC("Click the mouse at the specified position."),
         MCRF_ARGS_START
         MCRF_ARG("pos", "Position as (x, y) tuple, [x, y] list, Vector, or None for current position")
         MCRF_ARG("clicks", "Number of clicks to perform (default 1)")
         MCRF_ARG("interval", "Seconds between clicks when clicks > 1 (default 0.0)")
         MCRF_ARG("button", "Mouse button: 'left', 'right', 'middle', 'x1' or 'x2' (default 'left')")
     )},
    {"rightClick", (PyCFunction)McRFPy_Automation::_rightClick, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(automation, rightClick,
         MCRF_SIG("(pos: tuple | list | Vector | None = None)", "None"),
         MCRF_DESC("Right-click the mouse at the specified position."),
         MCRF_ARGS_START
         MCRF_ARG("pos", "Position as (x, y) tuple, [x, y] list, Vector, or None for current position")
     )},
    {"middleClick", (PyCFunction)McRFPy_Automation::_middleClick, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(automation, middleClick,
         MCRF_SIG("(pos: tuple | list | Vector | None = None)", "None"),
         MCRF_DESC("Middle-click the mouse at the specified position."),
         MCRF_ARGS_START
         MCRF_ARG("pos", "Position as (x, y) tuple, [x, y] list, Vector, or None for current position")
     )},
    {"doubleClick", (PyCFunction)McRFPy_Automation::_doubleClick, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(automation, doubleClick,
         MCRF_SIG("(pos: tuple | list | Vector | None = None)", "None"),
         MCRF_DESC("Double-click the mouse at the specified position."),
         MCRF_ARGS_START
         MCRF_ARG("pos", "Position as (x, y) tuple, [x, y] list, Vector, or None for current position")
     )},
    {"tripleClick", (PyCFunction)McRFPy_Automation::_tripleClick, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(automation, tripleClick,
         MCRF_SIG("(pos: tuple | list | Vector | None = None)", "None"),
         MCRF_DESC("Triple-click the mouse at the specified position."),
         MCRF_ARGS_START
         MCRF_ARG("pos", "Position as (x, y) tuple, [x, y] list, Vector, or None for current position")
     )},
    {"scroll", (PyCFunction)McRFPy_Automation::_scroll, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(automation, scroll,
         MCRF_SIG("(clicks: int, pos: tuple | list | Vector | None = None)", "None"),
         MCRF_DESC("Scroll the mouse wheel at the specified position."),
         MCRF_ARGS_START
         MCRF_ARG("clicks", "Number of scroll steps (positive = up, negative = down)")
         MCRF_ARG("pos", "Position as (x, y) tuple, [x, y] list, Vector, or None for current position")
         MCRF_NOTE("Like click(pos), a pos moves the simulated mouse there first (firing hover "
                   "enter/exit), then scrolls; the widget under pos receives the scroll.")
     )},
    {"mouseDown", (PyCFunction)McRFPy_Automation::_mouseDown, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(automation, mouseDown,
         MCRF_SIG("(pos: tuple | list | Vector | None = None, button: str = 'left')", "None"),
         MCRF_DESC("Press and hold a mouse button at the specified position."),
         MCRF_ARGS_START
         MCRF_ARG("pos", "Position as (x, y) tuple, [x, y] list, Vector, or None for current position")
         MCRF_ARG("button", "Mouse button: 'left', 'right', 'middle', 'x1' or 'x2' (default 'left')")
     )},
    {"mouseUp", (PyCFunction)McRFPy_Automation::_mouseUp, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(automation, mouseUp,
         MCRF_SIG("(pos: tuple | list | Vector | None = None, button: str = 'left')", "None"),
         MCRF_DESC("Release a mouse button at the specified position."),
         MCRF_ARGS_START
         MCRF_ARG("pos", "Position as (x, y) tuple, [x, y] list, Vector, or None for current position")
         MCRF_ARG("button", "Mouse button: 'left', 'right', 'middle', 'x1' or 'x2' (default 'left')")
     )},
    {"mouseLeave", (PyCFunction)McRFPy_Automation::_mouseLeave, METH_NOARGS,
     MCRF_METHOD(automation, mouseLeave,
         MCRF_SIG("()", "None"),
         MCRF_DESC("Simulate the cursor leaving the window, clearing all hover state. "
                   "Every hovered drawable fires its on_exit, every hovered grid fires "
                   "on_cell_exit, and Grid.hovered_cell becomes None."),
         MCRF_NOTE("Takes no position: the cursor is outside the window, so there is none. "
                   "Exit callbacks receive the last position passed to moveTo/click.")
     )},
    {"loseFocus", (PyCFunction)McRFPy_Automation::_loseFocus, METH_NOARGS,
     MCRF_METHOD(automation, loseFocus,
         MCRF_SIG("()", "None"),
         MCRF_DESC("Simulate the window losing focus (alt-tab), clearing all hover state. "
                   "Every hovered drawable fires its on_exit, every hovered grid fires "
                   "on_cell_exit, and Grid.hovered_cell becomes None."),
         MCRF_NOTE("An unfocused window is delivered no mouse motion, so the engine cannot "
                   "know where the pointer is; hovering nothing is the only truthful state. "
                   "Hover is restored by the next mouse movement after focus returns.")
     )},

    {"typewrite", (PyCFunction)McRFPy_Automation::_typewrite, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(automation, typewrite,
         MCRF_SIG("(message: str, interval: float = 0.0)", "None"),
         MCRF_DESC("Type text as key presses: each character is a press and release of the key "
                   "that types it on a US layout, delivered to on_key. Uppercase letters and "
                   "shifted symbols hold LEFT_SHIFT around the key; '\\n' is ENTER, '\\t' is TAB."),
         MCRF_ARGS_START
         MCRF_ARG("message", "Text to type: letters, digits, space, US-keyboard punctuation, '\\n', '\\t'")
         MCRF_ARG("interval", "Seconds to wait between characters (default 0.0)")
         MCRF_RAISES("ValueError", "If a character has no key (e.g. 'é', '\\r'); checked before any key is sent")
         MCRF_NOTE("typewrite('a') is on_key(Key.A, PRESSED), on_text('a'), on_key(Key.A, RELEASED), "
                   "as a US keyboard delivers it. '\\n' and '\\t' are keys and send no text. "
                   "For characters no US key types, use typeText().")
     )},
    {"typeText", McRFPy_Automation::_typeText, METH_VARARGS,
     MCRF_METHOD(automation, typeText,
         MCRF_SIG("(text: str)", "None"),
         MCRF_DESC("Type text with no key presses: deliver each code point of text to the scene's "
                   "on_text handler, as a keyboard layout, dead key or IME would."),
         MCRF_ARGS_START
         MCRF_ARG("text", "Characters to type, delivered one code point per on_text call")
         MCRF_RAISES("ValueError", "If a character is a control character or not a Unicode scalar "
                     "(Enter, Tab, Backspace, Escape are keys); checked before anything is sent")
         MCRF_NOTE("on_key receives nothing. Use typewrite() to also exercise the US key presses.")
     )},
    {"hotkey", McRFPy_Automation::_hotkey, METH_VARARGS,
     MCRF_METHOD(automation, hotkey,
         MCRF_SIG("(*keys: str)", "None"),
         MCRF_DESC("Press a hotkey combination by pressing all keys in order then releasing in reverse."),
         MCRF_ARGS_START
         MCRF_ARG("*keys", "Key names to press, e.g. 'ctrl', 'c'")
         MCRF_RAISES("ValueError", "If any key name is not recognized")
     )},
    {"keyDown", McRFPy_Automation::_keyDown, METH_VARARGS,
     MCRF_METHOD(automation, keyDown,
         MCRF_SIG("(key: str)", "None"),
         MCRF_DESC("Press and hold a keyboard key."),
         MCRF_ARGS_START
         MCRF_ARG("key", "Key name string, e.g. 'a', 'enter', 'ctrl', 'f1'")
         MCRF_RAISES("ValueError", "If the key name is not recognized")
     )},
    {"keyUp", McRFPy_Automation::_keyUp, METH_VARARGS,
     MCRF_METHOD(automation, keyUp,
         MCRF_SIG("(key: str)", "None"),
         MCRF_DESC("Release a keyboard key."),
         MCRF_ARGS_START
         MCRF_ARG("key", "Key name string, e.g. 'a', 'enter', 'ctrl', 'f1'")
         MCRF_RAISES("ValueError", "If the key name is not recognized")
     )},

    {NULL, NULL, 0, NULL}
};

// Module definition for mcrfpy.automation
static PyModuleDef automationModule = {
    PyModuleDef_HEAD_INIT,
    "mcrfpy.automation",
    "Automation API for McRogueFace - PyAutoGUI-compatible interface",
    -1,
    automationMethods
};

// Initialize automation submodule
PyObject* McRFPy_Automation::init_automation_module() {
    PyObject* module = PyModule_Create(&automationModule);
    if (module == NULL) {
        return NULL;
    }

    return module;
}
