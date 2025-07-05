#include "PyScene.h"
#include "ActionCode.h"
#include "Resources.h"
#include "PyCallable.h"
#include <algorithm>

PyScene::PyScene(GameEngine* g) : Scene(g)
{
    // mouse events
    registerAction(ActionCode::MOUSEBUTTON + sf::Mouse::Left, "left");
    registerAction(ActionCode::MOUSEBUTTON + sf::Mouse::Right, "right");
    registerAction(ActionCode::MOUSEWHEEL + ActionCode::WHEEL_DEL, "wheel_up");
    registerAction(ActionCode::MOUSEWHEEL + ActionCode::WHEEL_NEG + ActionCode::WHEEL_DEL, "wheel_down");

    // console (` / ~ key) - don't hard code.
    //registerAction(ActionCode::KEY + sf::Keyboard::Grave, "debug_menu");
}

void PyScene::update()
{
}

void PyScene::do_mouse_input(std::string button, std::string type)
{
    // In headless mode, mouse input is not available
    if (game->isHeadless()) {
        return;
    }
    
    auto unscaledmousepos = sf::Mouse::getPosition(game->getWindow());
    auto mousepos = game->getWindow().mapPixelToCoords(unscaledmousepos);
    UIDrawable* target;
    for (auto d: *ui_elements)
    {
        target = d->click_at(sf::Vector2f(mousepos));
        if (target)
        {
            /*
            PyObject* args = Py_BuildValue("(iiss)", (int)mousepos.x, (int)mousepos.y, button.c_str(), type.c_str());
            PyObject* retval = PyObject_Call(target->click_callable, args, NULL);
            if (!retval)
            {   
                std::cout << "click_callable has raised an exception. It's going to STDERR and being dropped:" << std::endl;
                PyErr_Print();
                PyErr_Clear();
            } else if (retval != Py_None)
            {   
                std::cout << "click_callable returned a non-None value. It's not an error, it's just not being saved or used." << std::endl;
            }
            */
            target->click_callable->call(mousepos, button, type);
        }
    }
}

void PyScene::doAction(std::string name, std::string type)
{
    if (name.compare("left") == 0 || name.compare("rclick") == 0 || name.compare("wheel_up") == 0 || name.compare("wheel_down") == 0) {
        do_mouse_input(name, type);
    }
    else if ACTIONONCE("debug_menu") {
        McRFPy_API::REPL();
    }
}

void PyScene::render()
{
    game->getRenderTarget().clear();
    
    // Only sort if z_index values have changed
    if (ui_elements_need_sort) {
        std::sort(ui_elements->begin(), ui_elements->end(), 
            [](const std::shared_ptr<UIDrawable>& a, const std::shared_ptr<UIDrawable>& b) {
                return a->z_index < b->z_index;
            });
        ui_elements_need_sort = false;
    }
    
    // Render in sorted order (no need to copy anymore)
    for (auto e: *ui_elements)
    {
        if (e)
            e->render();
    }
    
    // Display is handled by GameEngine
}
