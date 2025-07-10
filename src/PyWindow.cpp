#include "PyWindow.h"
#include "GameEngine.h"
#include "McRFPy_API.h"
#include <SFML/Graphics.hpp>
#include <cstring>

// Singleton instance - static variable, not a class member
static PyWindowObject* window_instance = nullptr;

PyObject* PyWindow::get(PyObject* cls, PyObject* args)
{
    // Create singleton instance if it doesn't exist
    if (!window_instance) {
        // Use the class object passed as first argument
        PyTypeObject* type = (PyTypeObject*)cls;
        
        if (!type->tp_alloc) {
            PyErr_SetString(PyExc_RuntimeError, "Window type not properly initialized");
            return NULL;
        }
        
        window_instance = (PyWindowObject*)type->tp_alloc(type, 0);
        if (!window_instance) {
            return NULL;
        }
    }
    
    Py_INCREF(window_instance);
    return (PyObject*)window_instance;
}

PyObject* PyWindow::repr(PyWindowObject* self)
{
    GameEngine* game = McRFPy_API::game;
    if (!game) {
        return PyUnicode_FromString("<Window [no game engine]>");
    }
    
    if (game->isHeadless()) {
        return PyUnicode_FromString("<Window [headless mode]>");
    }
    
    auto& window = game->getWindow();
    auto size = window.getSize();
    
    return PyUnicode_FromFormat("<Window %dx%d>", size.x, size.y);
}

// Property getters and setters

PyObject* PyWindow::get_resolution(PyWindowObject* self, void* closure)
{
    GameEngine* game = McRFPy_API::game;
    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "No game engine initialized");
        return NULL;
    }
    
    if (game->isHeadless()) {
        // Return headless renderer size
        return Py_BuildValue("(ii)", 1024, 768);  // Default headless size
    }
    
    auto& window = game->getWindow();
    auto size = window.getSize();
    return Py_BuildValue("(ii)", size.x, size.y);
}

int PyWindow::set_resolution(PyWindowObject* self, PyObject* value, void* closure)
{
    GameEngine* game = McRFPy_API::game;
    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "No game engine initialized");
        return -1;
    }
    
    if (game->isHeadless()) {
        PyErr_SetString(PyExc_RuntimeError, "Cannot change resolution in headless mode");
        return -1;
    }
    
    int width, height;
    if (!PyArg_ParseTuple(value, "ii", &width, &height)) {
        PyErr_SetString(PyExc_TypeError, "Resolution must be a tuple of two integers (width, height)");
        return -1;
    }
    
    if (width <= 0 || height <= 0) {
        PyErr_SetString(PyExc_ValueError, "Resolution dimensions must be positive");
        return -1;
    }
    
    auto& window = game->getWindow();
    
    // Get current window settings
    auto style = sf::Style::Titlebar | sf::Style::Close;
    if (window.getSize() == sf::Vector2u(sf::VideoMode::getDesktopMode().width, 
                                         sf::VideoMode::getDesktopMode().height)) {
        style = sf::Style::Fullscreen;
    }
    
    // Recreate window with new size
    window.create(sf::VideoMode(width, height), game->getWindowTitle(), style);
    
    // Restore vsync and framerate settings
    // Note: We'll need to store these settings in GameEngine
    window.setFramerateLimit(60);  // Default for now
    
    return 0;
}

PyObject* PyWindow::get_fullscreen(PyWindowObject* self, void* closure)
{
    GameEngine* game = McRFPy_API::game;
    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "No game engine initialized");
        return NULL;
    }
    
    if (game->isHeadless()) {
        Py_RETURN_FALSE;
    }
    
    auto& window = game->getWindow();
    auto size = window.getSize();
    auto desktop = sf::VideoMode::getDesktopMode();
    
    // Check if window size matches desktop size (rough fullscreen check)
    bool fullscreen = (size.x == desktop.width && size.y == desktop.height);
    
    return PyBool_FromLong(fullscreen);
}

int PyWindow::set_fullscreen(PyWindowObject* self, PyObject* value, void* closure)
{
    GameEngine* game = McRFPy_API::game;
    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "No game engine initialized");
        return -1;
    }
    
    if (game->isHeadless()) {
        PyErr_SetString(PyExc_RuntimeError, "Cannot change fullscreen in headless mode");
        return -1;
    }
    
    if (!PyBool_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "Fullscreen must be a boolean");
        return -1;
    }
    
    bool fullscreen = PyObject_IsTrue(value);
    auto& window = game->getWindow();
    
    if (fullscreen) {
        // Switch to fullscreen
        auto desktop = sf::VideoMode::getDesktopMode();
        window.create(desktop, game->getWindowTitle(), sf::Style::Fullscreen);
    } else {
        // Switch to windowed mode
        window.create(sf::VideoMode(1024, 768), game->getWindowTitle(), 
                     sf::Style::Titlebar | sf::Style::Close);
    }
    
    // Restore settings
    window.setFramerateLimit(60);
    
    return 0;
}

PyObject* PyWindow::get_vsync(PyWindowObject* self, void* closure)
{
    GameEngine* game = McRFPy_API::game;
    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "No game engine initialized");
        return NULL;
    }
    
    return PyBool_FromLong(game->getVSync());
}

int PyWindow::set_vsync(PyWindowObject* self, PyObject* value, void* closure)
{
    GameEngine* game = McRFPy_API::game;
    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "No game engine initialized");
        return -1;
    }
    
    if (game->isHeadless()) {
        PyErr_SetString(PyExc_RuntimeError, "Cannot change vsync in headless mode");
        return -1;
    }
    
    if (!PyBool_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "vsync must be a boolean");
        return -1;
    }
    
    bool vsync = PyObject_IsTrue(value);
    game->setVSync(vsync);
    
    return 0;
}

PyObject* PyWindow::get_title(PyWindowObject* self, void* closure)
{
    GameEngine* game = McRFPy_API::game;
    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "No game engine initialized");
        return NULL;
    }
    
    return PyUnicode_FromString(game->getWindowTitle().c_str());
}

int PyWindow::set_title(PyWindowObject* self, PyObject* value, void* closure)
{
    GameEngine* game = McRFPy_API::game;
    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "No game engine initialized");
        return -1;
    }
    
    if (game->isHeadless()) {
        // Silently ignore in headless mode
        return 0;
    }
    
    const char* title = PyUnicode_AsUTF8(value);
    if (!title) {
        PyErr_SetString(PyExc_TypeError, "Title must be a string");
        return -1;
    }
    
    game->setWindowTitle(title);
    
    return 0;
}

PyObject* PyWindow::get_visible(PyWindowObject* self, void* closure)
{
    GameEngine* game = McRFPy_API::game;
    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "No game engine initialized");
        return NULL;
    }
    
    if (game->isHeadless()) {
        Py_RETURN_FALSE;
    }
    
    auto& window = game->getWindow();
    bool visible = window.isOpen();  // Best approximation
    
    return PyBool_FromLong(visible);
}

int PyWindow::set_visible(PyWindowObject* self, PyObject* value, void* closure)
{
    GameEngine* game = McRFPy_API::game;
    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "No game engine initialized");
        return -1;
    }
    
    if (game->isHeadless()) {
        // Silently ignore in headless mode
        return 0;
    }
    
    if (!PyBool_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "visible must be a boolean");
        return -1;
    }
    
    bool visible = PyObject_IsTrue(value);
    auto& window = game->getWindow();
    window.setVisible(visible);
    
    return 0;
}

PyObject* PyWindow::get_framerate_limit(PyWindowObject* self, void* closure)
{
    GameEngine* game = McRFPy_API::game;
    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "No game engine initialized");
        return NULL;
    }
    
    return PyLong_FromLong(game->getFramerateLimit());
}

int PyWindow::set_framerate_limit(PyWindowObject* self, PyObject* value, void* closure)
{
    GameEngine* game = McRFPy_API::game;
    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "No game engine initialized");
        return -1;
    }
    
    if (game->isHeadless()) {
        // Silently ignore in headless mode
        return 0;
    }
    
    long limit = PyLong_AsLong(value);
    if (PyErr_Occurred()) {
        PyErr_SetString(PyExc_TypeError, "framerate_limit must be an integer");
        return -1;
    }
    
    if (limit < 0) {
        PyErr_SetString(PyExc_ValueError, "framerate_limit must be non-negative (0 for unlimited)");
        return -1;
    }
    
    game->setFramerateLimit(limit);
    
    return 0;
}

// Methods

PyObject* PyWindow::center(PyWindowObject* self, PyObject* args)
{
    GameEngine* game = McRFPy_API::game;
    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "No game engine initialized");
        return NULL;
    }
    
    if (game->isHeadless()) {
        PyErr_SetString(PyExc_RuntimeError, "Cannot center window in headless mode");
        return NULL;
    }
    
    auto& window = game->getWindow();
    auto size = window.getSize();
    auto desktop = sf::VideoMode::getDesktopMode();
    
    int x = (desktop.width - size.x) / 2;
    int y = (desktop.height - size.y) / 2;
    
    window.setPosition(sf::Vector2i(x, y));
    
    Py_RETURN_NONE;
}

PyObject* PyWindow::screenshot(PyWindowObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"filename", NULL};
    const char* filename = nullptr;
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|s", const_cast<char**>(keywords), &filename)) {
        return NULL;
    }
    
    GameEngine* game = McRFPy_API::game;
    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "No game engine initialized");
        return NULL;
    }
    
    // Get the render target pointer
    sf::RenderTarget* target = game->getRenderTargetPtr();
    if (!target) {
        PyErr_SetString(PyExc_RuntimeError, "No render target available");
        return NULL;
    }
    
    sf::Image screenshot;
    
    // For RenderWindow
    if (auto* window = dynamic_cast<sf::RenderWindow*>(target)) {
        sf::Vector2u windowSize = window->getSize();
        sf::Texture texture;
        texture.create(windowSize.x, windowSize.y);
        texture.update(*window);
        screenshot = texture.copyToImage();
    }
    // For RenderTexture (headless mode)
    else if (auto* renderTexture = dynamic_cast<sf::RenderTexture*>(target)) {
        screenshot = renderTexture->getTexture().copyToImage();
    }
    else {
        PyErr_SetString(PyExc_RuntimeError, "Unknown render target type");
        return NULL;
    }
    
    // Save to file if filename provided
    if (filename) {
        if (!screenshot.saveToFile(filename)) {
            PyErr_SetString(PyExc_IOError, "Failed to save screenshot");
            return NULL;
        }
        Py_RETURN_NONE;
    }
    
    // Otherwise return as bytes
    auto pixels = screenshot.getPixelsPtr();
    auto size = screenshot.getSize();
    
    return PyBytes_FromStringAndSize((const char*)pixels, size.x * size.y * 4);
}

PyObject* PyWindow::get_game_resolution(PyWindowObject* self, void* closure)
{
    GameEngine* game = McRFPy_API::game;
    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "No game engine initialized");
        return NULL;
    }
    
    auto resolution = game->getGameResolution();
    return Py_BuildValue("(ii)", resolution.x, resolution.y);
}

int PyWindow::set_game_resolution(PyWindowObject* self, PyObject* value, void* closure)
{
    GameEngine* game = McRFPy_API::game;
    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "No game engine initialized");
        return -1;
    }
    
    int width, height;
    if (!PyArg_ParseTuple(value, "ii", &width, &height)) {
        PyErr_SetString(PyExc_TypeError, "game_resolution must be a tuple of two integers (width, height)");
        return -1;
    }
    
    if (width <= 0 || height <= 0) {
        PyErr_SetString(PyExc_ValueError, "Game resolution dimensions must be positive");
        return -1;
    }
    
    game->setGameResolution(width, height);
    return 0;
}

PyObject* PyWindow::get_scaling_mode(PyWindowObject* self, void* closure)
{
    GameEngine* game = McRFPy_API::game;
    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "No game engine initialized");
        return NULL;
    }
    
    return PyUnicode_FromString(game->getViewportModeString().c_str());
}

int PyWindow::set_scaling_mode(PyWindowObject* self, PyObject* value, void* closure)
{
    GameEngine* game = McRFPy_API::game;
    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "No game engine initialized");
        return -1;
    }
    
    const char* mode_str = PyUnicode_AsUTF8(value);
    if (!mode_str) {
        PyErr_SetString(PyExc_TypeError, "scaling_mode must be a string");
        return -1;
    }
    
    GameEngine::ViewportMode mode;
    if (strcmp(mode_str, "center") == 0) {
        mode = GameEngine::ViewportMode::Center;
    } else if (strcmp(mode_str, "stretch") == 0) {
        mode = GameEngine::ViewportMode::Stretch;
    } else if (strcmp(mode_str, "fit") == 0) {
        mode = GameEngine::ViewportMode::Fit;
    } else {
        PyErr_SetString(PyExc_ValueError, "scaling_mode must be 'center', 'stretch', or 'fit'");
        return -1;
    }
    
    game->setViewportMode(mode);
    return 0;
}

// Property definitions
PyGetSetDef PyWindow::getsetters[] = {
    {"resolution", (getter)get_resolution, (setter)set_resolution, 
     "Window resolution as (width, height) tuple", NULL},
    {"fullscreen", (getter)get_fullscreen, (setter)set_fullscreen,
     "Window fullscreen state", NULL},
    {"vsync", (getter)get_vsync, (setter)set_vsync,
     "Vertical sync enabled state", NULL},
    {"title", (getter)get_title, (setter)set_title,
     "Window title string", NULL},
    {"visible", (getter)get_visible, (setter)set_visible,
     "Window visibility state", NULL},
    {"framerate_limit", (getter)get_framerate_limit, (setter)set_framerate_limit,
     "Frame rate limit (0 for unlimited)", NULL},
    {"game_resolution", (getter)get_game_resolution, (setter)set_game_resolution,
     "Fixed game resolution as (width, height) tuple", NULL},
    {"scaling_mode", (getter)get_scaling_mode, (setter)set_scaling_mode,
     "Viewport scaling mode: 'center', 'stretch', or 'fit'", NULL},
    {NULL}
};

// Method definitions
PyMethodDef PyWindow::methods[] = {
    {"get", (PyCFunction)PyWindow::get, METH_VARARGS | METH_CLASS,
     "Get the Window singleton instance"},
    {"center", (PyCFunction)PyWindow::center, METH_NOARGS,
     "Center the window on the screen"},
    {"screenshot", (PyCFunction)PyWindow::screenshot, METH_VARARGS | METH_KEYWORDS,
     "Take a screenshot. Pass filename to save to file, or get raw bytes if no filename."},
    {NULL}
};