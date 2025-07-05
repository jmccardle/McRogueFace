#include "McRFPy_Automation.h"
#include "McRFPy_API.h"
#include "GameEngine.h"
#include <fstream>
#include <iostream>
#include <sstream>
#include <unordered_map>

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
        {"capslock", sf::Keyboard::LControl},  // Note: SFML doesn't have CapsLock
        {"numlock", sf::Keyboard::LControl},   // Note: SFML doesn't have NumLock
        {"scrolllock", sf::Keyboard::LControl}, // Note: SFML doesn't have ScrollLock
    };
    
    auto it = keyMap.find(keyName);
    if (it != keyMap.end()) {
        return it->second;
    }
    return sf::Keyboard::Unknown;
}

// Inject mouse event into the game engine
void McRFPy_Automation::injectMouseEvent(sf::Event::EventType type, int x, int y, sf::Mouse::Button button) {
    auto engine = getGameEngine();
    if (!engine) return;
    
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
            event.mouseWheelScroll.delta = static_cast<float>(x); // x is used for scroll amount
            event.mouseWheelScroll.x = x;
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
        event.key.code = key;
        event.key.alt = sf::Keyboard::isKeyPressed(sf::Keyboard::LAlt) || 
                        sf::Keyboard::isKeyPressed(sf::Keyboard::RAlt);
        event.key.control = sf::Keyboard::isKeyPressed(sf::Keyboard::LControl) || 
                           sf::Keyboard::isKeyPressed(sf::Keyboard::RControl);
        event.key.shift = sf::Keyboard::isKeyPressed(sf::Keyboard::LShift) || 
                         sf::Keyboard::isKeyPressed(sf::Keyboard::RShift);
        event.key.system = sf::Keyboard::isKeyPressed(sf::Keyboard::LSystem) || 
                          sf::Keyboard::isKeyPressed(sf::Keyboard::RSystem);
    }
    
    engine->processEvent(event);
}

// Inject text event for typing
void McRFPy_Automation::injectTextEvent(sf::Uint32 unicode) {
    auto engine = getGameEngine();
    if (!engine) return;
    
    sf::Event event;
    event.type = sf::Event::TextEntered;
    event.text.unicode = unicode;
    
    engine->processEvent(event);
}

// Screenshot implementation
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
    
    // Get the render target
    sf::RenderTarget* target = engine->getRenderTargetPtr();
    if (!target) {
        PyErr_SetString(PyExc_RuntimeError, "No render target available");
        return NULL;
    }
    
    // For RenderWindow, we can get a screenshot directly
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
    // For RenderTexture (headless mode)
    else if (auto* renderTexture = dynamic_cast<sf::RenderTexture*>(target)) {
        if (renderTexture->getTexture().copyToImage().saveToFile(filename)) {
            Py_RETURN_TRUE;
        } else {
            Py_RETURN_FALSE;
        }
    }
    
    PyErr_SetString(PyExc_RuntimeError, "Unknown render target type");
    return NULL;
}

// Get current mouse position
PyObject* McRFPy_Automation::_position(PyObject* self, PyObject* args) {
    auto engine = getGameEngine();
    if (!engine || !engine->getRenderTargetPtr()) {
        return Py_BuildValue("(ii)", 0, 0);
    }
    
    // In headless mode, we'd need to track the simulated mouse position
    // For now, return the actual mouse position relative to window if available
    if (auto* window = dynamic_cast<sf::RenderWindow*>(engine->getRenderTargetPtr())) {
        sf::Vector2i pos = sf::Mouse::getPosition(*window);
        return Py_BuildValue("(ii)", pos.x, pos.y);
    }
    
    // In headless mode, return simulated position (TODO: track this)
    return Py_BuildValue("(ii)", 0, 0);
}

// Get screen size
PyObject* McRFPy_Automation::_size(PyObject* self, PyObject* args) {
    auto engine = getGameEngine();
    if (!engine || !engine->getRenderTargetPtr()) {
        return Py_BuildValue("(ii)", 1024, 768);  // Default size
    }
    
    sf::Vector2u size = engine->getRenderTarget().getSize();
    return Py_BuildValue("(ii)", size.x, size.y);
}

// Check if coordinates are on screen
PyObject* McRFPy_Automation::_onScreen(PyObject* self, PyObject* args) {
    int x, y;
    if (!PyArg_ParseTuple(args, "ii", &x, &y)) {
        return NULL;
    }
    
    auto engine = getGameEngine();
    if (!engine || !engine->getRenderTargetPtr()) {
        Py_RETURN_FALSE;
    }
    
    sf::Vector2u size = engine->getRenderTarget().getSize();
    if (x >= 0 && x < (int)size.x && y >= 0 && y < (int)size.y) {
        Py_RETURN_TRUE;
    } else {
        Py_RETURN_FALSE;
    }
}

// Move mouse to position
PyObject* McRFPy_Automation::_moveTo(PyObject* self, PyObject* args, PyObject* kwargs) {
    static const char* kwlist[] = {"x", "y", "duration", NULL};
    int x, y;
    float duration = 0.0f;
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "ii|f", const_cast<char**>(kwlist), 
                                     &x, &y, &duration)) {
        return NULL;
    }
    
    // TODO: Implement smooth movement with duration
    injectMouseEvent(sf::Event::MouseMoved, x, y);
    
    if (duration > 0) {
        sleep_ms(static_cast<int>(duration * 1000));
    }
    
    Py_RETURN_NONE;
}

// Move mouse relative
PyObject* McRFPy_Automation::_moveRel(PyObject* self, PyObject* args, PyObject* kwargs) {
    static const char* kwlist[] = {"xOffset", "yOffset", "duration", NULL};
    int xOffset, yOffset;
    float duration = 0.0f;
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "ii|f", const_cast<char**>(kwlist), 
                                     &xOffset, &yOffset, &duration)) {
        return NULL;
    }
    
    // Get current position
    PyObject* pos = _position(self, NULL);
    if (!pos) return NULL;
    
    int currentX, currentY;
    if (!PyArg_ParseTuple(pos, "ii", &currentX, &currentY)) {
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

// Click implementation
PyObject* McRFPy_Automation::_click(PyObject* self, PyObject* args, PyObject* kwargs) {
    static const char* kwlist[] = {"x", "y", "clicks", "interval", "button", NULL};
    int x = -1, y = -1;
    int clicks = 1;
    float interval = 0.0f;
    const char* button = "left";
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|iiifs", const_cast<char**>(kwlist), 
                                     &x, &y, &clicks, &interval, &button)) {
        return NULL;
    }
    
    // If no position specified, use current position
    if (x == -1 || y == -1) {
        PyObject* pos = _position(self, NULL);
        if (!pos) return NULL;
        
        if (!PyArg_ParseTuple(pos, "ii", &x, &y)) {
            Py_DECREF(pos);
            return NULL;
        }
        Py_DECREF(pos);
    }
    
    // Determine button
    sf::Mouse::Button sfButton = sf::Mouse::Left;
    if (strcmp(button, "right") == 0) {
        sfButton = sf::Mouse::Right;
    } else if (strcmp(button, "middle") == 0) {
        sfButton = sf::Mouse::Middle;
    }
    
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

// Right click
PyObject* McRFPy_Automation::_rightClick(PyObject* self, PyObject* args, PyObject* kwargs) {
    static const char* kwlist[] = {"x", "y", NULL};
    int x = -1, y = -1;
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|ii", const_cast<char**>(kwlist), &x, &y)) {
        return NULL;
    }
    
    // Build new args with button="right"
    PyObject* newKwargs = PyDict_New();
    PyDict_SetItemString(newKwargs, "button", PyUnicode_FromString("right"));
    if (x != -1) PyDict_SetItemString(newKwargs, "x", PyLong_FromLong(x));
    if (y != -1) PyDict_SetItemString(newKwargs, "y", PyLong_FromLong(y));
    
    PyObject* result = _click(self, PyTuple_New(0), newKwargs);
    Py_DECREF(newKwargs);
    return result;
}

// Double click
PyObject* McRFPy_Automation::_doubleClick(PyObject* self, PyObject* args, PyObject* kwargs) {
    static const char* kwlist[] = {"x", "y", NULL};
    int x = -1, y = -1;
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|ii", const_cast<char**>(kwlist), &x, &y)) {
        return NULL;
    }
    
    PyObject* newKwargs = PyDict_New();
    PyDict_SetItemString(newKwargs, "clicks", PyLong_FromLong(2));
    PyDict_SetItemString(newKwargs, "interval", PyFloat_FromDouble(0.1));
    if (x != -1) PyDict_SetItemString(newKwargs, "x", PyLong_FromLong(x));
    if (y != -1) PyDict_SetItemString(newKwargs, "y", PyLong_FromLong(y));
    
    PyObject* result = _click(self, PyTuple_New(0), newKwargs);
    Py_DECREF(newKwargs);
    return result;
}

// Type text
PyObject* McRFPy_Automation::_typewrite(PyObject* self, PyObject* args, PyObject* kwargs) {
    static const char* kwlist[] = {"message", "interval", NULL};
    const char* message;
    float interval = 0.0f;
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "s|f", const_cast<char**>(kwlist), 
                                     &message, &interval)) {
        return NULL;
    }
    
    // Type each character
    for (size_t i = 0; message[i] != '\0'; i++) {
        if (i > 0 && interval > 0) {
            sleep_ms(static_cast<int>(interval * 1000));
        }
        
        char c = message[i];
        
        // Handle special characters
        if (c == '\n') {
            injectKeyEvent(sf::Event::KeyPressed, sf::Keyboard::Enter);
            injectKeyEvent(sf::Event::KeyReleased, sf::Keyboard::Enter);
        } else if (c == '\t') {
            injectKeyEvent(sf::Event::KeyPressed, sf::Keyboard::Tab);
            injectKeyEvent(sf::Event::KeyReleased, sf::Keyboard::Tab);
        } else {
            // For regular characters, send text event
            injectTextEvent(static_cast<sf::Uint32>(c));
        }
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

// Scroll wheel
PyObject* McRFPy_Automation::_scroll(PyObject* self, PyObject* args, PyObject* kwargs) {
    static const char* kwlist[] = {"clicks", "x", "y", NULL};
    int clicks;
    int x = -1, y = -1;
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "i|ii", const_cast<char**>(kwlist), 
                                     &clicks, &x, &y)) {
        return NULL;
    }
    
    // If no position specified, use current position
    if (x == -1 || y == -1) {
        PyObject* pos = _position(self, NULL);
        if (!pos) return NULL;
        
        if (!PyArg_ParseTuple(pos, "ii", &x, &y)) {
            Py_DECREF(pos);
            return NULL;
        }
        Py_DECREF(pos);
    }
    
    // Inject scroll event
    injectMouseEvent(sf::Event::MouseWheelScrolled, clicks, y);
    
    Py_RETURN_NONE;
}

// Other click types using the main click function
PyObject* McRFPy_Automation::_middleClick(PyObject* self, PyObject* args, PyObject* kwargs) {
    static const char* kwlist[] = {"x", "y", NULL};
    int x = -1, y = -1;
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|ii", const_cast<char**>(kwlist), &x, &y)) {
        return NULL;
    }
    
    PyObject* newKwargs = PyDict_New();
    PyDict_SetItemString(newKwargs, "button", PyUnicode_FromString("middle"));
    if (x != -1) PyDict_SetItemString(newKwargs, "x", PyLong_FromLong(x));
    if (y != -1) PyDict_SetItemString(newKwargs, "y", PyLong_FromLong(y));
    
    PyObject* result = _click(self, PyTuple_New(0), newKwargs);
    Py_DECREF(newKwargs);
    return result;
}

PyObject* McRFPy_Automation::_tripleClick(PyObject* self, PyObject* args, PyObject* kwargs) {
    static const char* kwlist[] = {"x", "y", NULL};
    int x = -1, y = -1;
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|ii", const_cast<char**>(kwlist), &x, &y)) {
        return NULL;
    }
    
    PyObject* newKwargs = PyDict_New();
    PyDict_SetItemString(newKwargs, "clicks", PyLong_FromLong(3));
    PyDict_SetItemString(newKwargs, "interval", PyFloat_FromDouble(0.1));
    if (x != -1) PyDict_SetItemString(newKwargs, "x", PyLong_FromLong(x));
    if (y != -1) PyDict_SetItemString(newKwargs, "y", PyLong_FromLong(y));
    
    PyObject* result = _click(self, PyTuple_New(0), newKwargs);
    Py_DECREF(newKwargs);
    return result;
}

// Mouse button press/release
PyObject* McRFPy_Automation::_mouseDown(PyObject* self, PyObject* args, PyObject* kwargs) {
    static const char* kwlist[] = {"x", "y", "button", NULL};
    int x = -1, y = -1;
    const char* button = "left";
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|iis", const_cast<char**>(kwlist), 
                                     &x, &y, &button)) {
        return NULL;
    }
    
    // If no position specified, use current position
    if (x == -1 || y == -1) {
        PyObject* pos = _position(self, NULL);
        if (!pos) return NULL;
        
        if (!PyArg_ParseTuple(pos, "ii", &x, &y)) {
            Py_DECREF(pos);
            return NULL;
        }
        Py_DECREF(pos);
    }
    
    sf::Mouse::Button sfButton = sf::Mouse::Left;
    if (strcmp(button, "right") == 0) {
        sfButton = sf::Mouse::Right;
    } else if (strcmp(button, "middle") == 0) {
        sfButton = sf::Mouse::Middle;
    }
    
    injectMouseEvent(sf::Event::MouseButtonPressed, x, y, sfButton);
    Py_RETURN_NONE;
}

PyObject* McRFPy_Automation::_mouseUp(PyObject* self, PyObject* args, PyObject* kwargs) {
    static const char* kwlist[] = {"x", "y", "button", NULL};
    int x = -1, y = -1;
    const char* button = "left";
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|iis", const_cast<char**>(kwlist), 
                                     &x, &y, &button)) {
        return NULL;
    }
    
    // If no position specified, use current position
    if (x == -1 || y == -1) {
        PyObject* pos = _position(self, NULL);
        if (!pos) return NULL;
        
        if (!PyArg_ParseTuple(pos, "ii", &x, &y)) {
            Py_DECREF(pos);
            return NULL;
        }
        Py_DECREF(pos);
    }
    
    sf::Mouse::Button sfButton = sf::Mouse::Left;
    if (strcmp(button, "right") == 0) {
        sfButton = sf::Mouse::Right;
    } else if (strcmp(button, "middle") == 0) {
        sfButton = sf::Mouse::Middle;
    }
    
    injectMouseEvent(sf::Event::MouseButtonReleased, x, y, sfButton);
    Py_RETURN_NONE;
}

// Drag operations
PyObject* McRFPy_Automation::_dragTo(PyObject* self, PyObject* args, PyObject* kwargs) {
    static const char* kwlist[] = {"x", "y", "duration", "button", NULL};
    int x, y;
    float duration = 0.0f;
    const char* button = "left";
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "ii|fs", const_cast<char**>(kwlist), 
                                     &x, &y, &duration, &button)) {
        return NULL;
    }
    
    // Get current position
    PyObject* pos = _position(self, NULL);
    if (!pos) return NULL;
    
    int startX, startY;
    if (!PyArg_ParseTuple(pos, "ii", &startX, &startY)) {
        Py_DECREF(pos);
        return NULL;
    }
    Py_DECREF(pos);
    
    // Mouse down at current position
    PyObject* downArgs = Py_BuildValue("(ii)", startX, startY);
    PyObject* downKwargs = PyDict_New();
    PyDict_SetItemString(downKwargs, "button", PyUnicode_FromString(button));
    
    PyObject* downResult = _mouseDown(self, downArgs, downKwargs);
    Py_DECREF(downArgs);
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
    PyObject* upArgs = Py_BuildValue("(ii)", x, y);
    PyObject* upKwargs = PyDict_New();
    PyDict_SetItemString(upKwargs, "button", PyUnicode_FromString(button));
    
    PyObject* upResult = _mouseUp(self, upArgs, upKwargs);
    Py_DECREF(upArgs);
    Py_DECREF(upKwargs);
    if (!upResult) return NULL;
    Py_DECREF(upResult);
    
    Py_RETURN_NONE;
}

PyObject* McRFPy_Automation::_dragRel(PyObject* self, PyObject* args, PyObject* kwargs) {
    static const char* kwlist[] = {"xOffset", "yOffset", "duration", "button", NULL};
    int xOffset, yOffset;
    float duration = 0.0f;
    const char* button = "left";
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "ii|fs", const_cast<char**>(kwlist), 
                                     &xOffset, &yOffset, &duration, &button)) {
        return NULL;
    }
    
    // Get current position
    PyObject* pos = _position(self, NULL);
    if (!pos) return NULL;
    
    int currentX, currentY;
    if (!PyArg_ParseTuple(pos, "ii", &currentX, &currentY)) {
        Py_DECREF(pos);
        return NULL;
    }
    Py_DECREF(pos);
    
    // Call dragTo with absolute position
    PyObject* dragArgs = Py_BuildValue("(ii)", currentX + xOffset, currentY + yOffset);
    PyObject* dragKwargs = PyDict_New();
    PyDict_SetItemString(dragKwargs, "duration", PyFloat_FromDouble(duration));
    PyDict_SetItemString(dragKwargs, "button", PyUnicode_FromString(button));
    
    PyObject* result = _dragTo(self, dragArgs, dragKwargs);
    Py_DECREF(dragArgs);
    Py_DECREF(dragKwargs);
    
    return result;
}

// Method definitions for the automation module
static PyMethodDef automationMethods[] = {
    {"screenshot", McRFPy_Automation::_screenshot, METH_VARARGS, 
     "screenshot(filename) - Save a screenshot to the specified file"},
    
    {"position", McRFPy_Automation::_position, METH_NOARGS, 
     "position() - Get current mouse position as (x, y) tuple"},
    {"size", McRFPy_Automation::_size, METH_NOARGS, 
     "size() - Get screen size as (width, height) tuple"},
    {"onScreen", McRFPy_Automation::_onScreen, METH_VARARGS, 
     "onScreen(x, y) - Check if coordinates are within screen bounds"},
    
    {"moveTo", (PyCFunction)McRFPy_Automation::_moveTo, METH_VARARGS | METH_KEYWORDS, 
     "moveTo(x, y, duration=0.0) - Move mouse to absolute position"},
    {"moveRel", (PyCFunction)McRFPy_Automation::_moveRel, METH_VARARGS | METH_KEYWORDS, 
     "moveRel(xOffset, yOffset, duration=0.0) - Move mouse relative to current position"},
    {"dragTo", (PyCFunction)McRFPy_Automation::_dragTo, METH_VARARGS | METH_KEYWORDS, 
     "dragTo(x, y, duration=0.0, button='left') - Drag mouse to position"},
    {"dragRel", (PyCFunction)McRFPy_Automation::_dragRel, METH_VARARGS | METH_KEYWORDS, 
     "dragRel(xOffset, yOffset, duration=0.0, button='left') - Drag mouse relative to current position"},
    
    {"click", (PyCFunction)McRFPy_Automation::_click, METH_VARARGS | METH_KEYWORDS, 
     "click(x=None, y=None, clicks=1, interval=0.0, button='left') - Click at position"},
    {"rightClick", (PyCFunction)McRFPy_Automation::_rightClick, METH_VARARGS | METH_KEYWORDS, 
     "rightClick(x=None, y=None) - Right click at position"},
    {"middleClick", (PyCFunction)McRFPy_Automation::_middleClick, METH_VARARGS | METH_KEYWORDS, 
     "middleClick(x=None, y=None) - Middle click at position"},
    {"doubleClick", (PyCFunction)McRFPy_Automation::_doubleClick, METH_VARARGS | METH_KEYWORDS, 
     "doubleClick(x=None, y=None) - Double click at position"},
    {"tripleClick", (PyCFunction)McRFPy_Automation::_tripleClick, METH_VARARGS | METH_KEYWORDS, 
     "tripleClick(x=None, y=None) - Triple click at position"},
    {"scroll", (PyCFunction)McRFPy_Automation::_scroll, METH_VARARGS | METH_KEYWORDS, 
     "scroll(clicks, x=None, y=None) - Scroll wheel at position"},
    {"mouseDown", (PyCFunction)McRFPy_Automation::_mouseDown, METH_VARARGS | METH_KEYWORDS, 
     "mouseDown(x=None, y=None, button='left') - Press mouse button"},
    {"mouseUp", (PyCFunction)McRFPy_Automation::_mouseUp, METH_VARARGS | METH_KEYWORDS, 
     "mouseUp(x=None, y=None, button='left') - Release mouse button"},
    
    {"typewrite", (PyCFunction)McRFPy_Automation::_typewrite, METH_VARARGS | METH_KEYWORDS, 
     "typewrite(message, interval=0.0) - Type text with optional interval between keystrokes"},
    {"hotkey", McRFPy_Automation::_hotkey, METH_VARARGS, 
     "hotkey(*keys) - Press a hotkey combination (e.g., hotkey('ctrl', 'c'))"},
    {"keyDown", McRFPy_Automation::_keyDown, METH_VARARGS, 
     "keyDown(key) - Press and hold a key"},
    {"keyUp", McRFPy_Automation::_keyUp, METH_VARARGS, 
     "keyUp(key) - Release a key"},
    
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