#pragma once
#include "Common.h"
#include "Python.h"
#include <SFML/Graphics.hpp>
#include <SFML/Window.hpp>
#include <string>
#include <chrono>
#include <thread>

class GameEngine;

class McRFPy_Automation {
public:
    // Initialize the automation submodule
    static PyObject* init_automation_module();
    
    // Screenshot functionality
    static PyObject* _screenshot(PyObject* self, PyObject* args);
    
    // Mouse position and screen info
    static PyObject* _position(PyObject* self, PyObject* args);
    static PyObject* _size(PyObject* self, PyObject* args);
    static PyObject* _onScreen(PyObject* self, PyObject* args);
    
    // Mouse movement
    static PyObject* _moveTo(PyObject* self, PyObject* args, PyObject* kwargs);
    static PyObject* _moveRel(PyObject* self, PyObject* args, PyObject* kwargs);
    static PyObject* _dragTo(PyObject* self, PyObject* args, PyObject* kwargs);
    static PyObject* _dragRel(PyObject* self, PyObject* args, PyObject* kwargs);
    
    // Mouse clicks
    static PyObject* _click(PyObject* self, PyObject* args, PyObject* kwargs);
    static PyObject* _rightClick(PyObject* self, PyObject* args, PyObject* kwargs);
    static PyObject* _middleClick(PyObject* self, PyObject* args, PyObject* kwargs);
    static PyObject* _doubleClick(PyObject* self, PyObject* args, PyObject* kwargs);
    static PyObject* _tripleClick(PyObject* self, PyObject* args, PyObject* kwargs);
    static PyObject* _scroll(PyObject* self, PyObject* args, PyObject* kwargs);
    static PyObject* _mouseDown(PyObject* self, PyObject* args, PyObject* kwargs);
    static PyObject* _mouseUp(PyObject* self, PyObject* args, PyObject* kwargs);
    
    // Keyboard
    static PyObject* _typewrite(PyObject* self, PyObject* args, PyObject* kwargs);
    static PyObject* _hotkey(PyObject* self, PyObject* args);
    static PyObject* _keyDown(PyObject* self, PyObject* args);
    static PyObject* _keyUp(PyObject* self, PyObject* args);
    
    // Helper functions
    static void injectMouseEvent(sf::Event::EventType type, int x, int y, sf::Mouse::Button button = sf::Mouse::Left);
    static void injectKeyEvent(sf::Event::EventType type, sf::Keyboard::Key key);
    static void injectTextEvent(sf::Uint32 unicode);
    static sf::Keyboard::Key stringToKey(const std::string& keyName);
    static void sleep_ms(int milliseconds);
    
private:
    static GameEngine* getGameEngine();
};