#include "PyScene.h"
#include "ActionCode.h"
#include "Resources.h"

PyScene::PyScene(GameEngine* g) : Scene(g)
{
    // mouse events
    registerAction(ActionCode::MOUSEBUTTON + sf::Mouse::Left, "left");
    registerAction(ActionCode::MOUSEBUTTON + sf::Mouse::Right, "right");
    registerAction(ActionCode::MOUSEWHEEL + ActionCode::WHEEL_DEL, "wheel_up");
    registerAction(ActionCode::MOUSEWHEEL + ActionCode::WHEEL_NEG + ActionCode::WHEEL_DEL, "wheel_down");

    registerAction(ActionCode::KEY + sf::Keyboard::Escape, "debug_menu");
}

void PyScene::update()
{
}

void PyScene::do_mouse_input(std::string button, std::string type)
{
    auto mousepos = sf::Mouse::getPosition(game->getWindow());
    UIDrawable* target;
    for (auto d: *ui_elements)
    {
        target = d->click_at(sf::Vector2f(mousepos));
        if (target)
        {
            PyObject* args = Py_BuildValue("(iiss)", mousepos.x, mousepos.y, button.c_str(), type.c_str());
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
        }
    }
}

void PyScene::doAction(std::string name, std::string type)
{
    if (ACTIONPY) {
        McRFPy_API::doAction(name.substr(0, name.size() - 3));
    }
    else if (name.compare("left") == 0 || name.compare("rclick") == 0 || name.compare("wheel_up") == 0 || name.compare("wheel_down") == 0) {
        do_mouse_input(name, type);
    }
    else if ACTIONONCE("debug_menu") {
        McRFPy_API::REPL();
    }
}

void PyScene::sRender()
{
    game->getWindow().clear();
    
    auto vec = *ui_elements;
    for (auto e: vec)
    {
        if (e)
            e->render();
    }
    
    game->getWindow().display();
}
