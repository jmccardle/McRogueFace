#include "GameEngine.h"
//#include "MenuScene.h"
//#include "UITestScene.h"
#include "ActionCode.h"
#include "McRFPy_API.h"
//#include "PythonScene.h"
#include "PyScene.h"
#include "UITestScene.h"
#include "Resources.h"

GameEngine::GameEngine()
{
    Resources::font.loadFromFile("./assets/JetbrainsMono.ttf");
    Resources::game = this;
    window_title = "McRogueFace - 7DRL 2024 Engine Demo";
    window.create(sf::VideoMode(1024, 768), window_title, sf::Style::Titlebar | sf::Style::Close);
    visible = window.getDefaultView();
    window.setFramerateLimit(30);
    scene = "uitest";
    //std::cout << "Constructing MenuScene" << std::endl;
    //scenes["menu"] = new MenuScene(this);
    scenes["uitest"] = new UITestScene(this);

    //std::cout << "Constructed MenuScene" <<std::endl;
    //scenes["play"] = new UITestScene(this);
    //api = new McRFPy_API(this);
    
    McRFPy_API::game = this;
    McRFPy_API::api_init();
    McRFPy_API::executePyString("import mcrfpy");
    McRFPy_API::executeScript("scripts/game.py");
    //McRFPy_API::executePyString("from UIMenu import *");
    //McRFPy_API::executePyString("from Grid import *");

    //scenes["py"] = new PythonScene(this, "TestScene");

    IndexSprite::game = this;

    clock.restart();
    runtime.restart();
}

Scene* GameEngine::currentScene() { return scenes[scene]; }
void GameEngine::changeScene(std::string s)
{
    /*std::cout << "Current scene is now '" << s << "'\n";*/
    if (scenes.find(s) != scenes.end())
        scene = s;
    else
        std::cout << "Attempted to change to a scene that doesn't exist (`" << s << "`)" << std::endl;
}
void GameEngine::quit() { running = false; }
void GameEngine::setPause(bool p) { paused = p; }
sf::Font & GameEngine::getFont() { /*return font; */ return Resources::font; }
sf::RenderWindow & GameEngine::getWindow() { return window; }

void GameEngine::createScene(std::string s) { scenes[s] = new PyScene(this); }

void GameEngine::setWindowScale(float multiplier)
{
    window.setSize(sf::Vector2u(1024 * multiplier, 768 * multiplier)); // 7DRL 2024: window scaling
    //window.create(sf::VideoMode(1024 * multiplier, 768 * multiplier), window_title, sf::Style::Titlebar | sf::Style::Close);
}

void GameEngine::run()
{
    float fps = 0.0;
    clock.restart();
    while (running)
    {
        currentScene()->update();
        testTimers();
        sUserInput();
        if (!paused)
        {
        }
        currentScene()->sRender();
        currentFrame++;
        frameTime = clock.restart().asSeconds();
        fps = 1 / frameTime;
        window.setTitle(window_title + " " + std::to_string(fps) + " FPS");
    }
}

void GameEngine::manageTimer(std::string name, PyObject* target, int interval)
{
    //std::cout << "Manage timer called. " << name << " " << interval << std::endl;
    auto it = timers.find(name);
    if (it != timers.end()) // overwrite existing
    {
        if (target == NULL || target == Py_None) // delete
        {
            Py_DECREF(timers[name].target);
            timers.erase(it);
            return;
        }
    }
    if (target == NULL || target == Py_None)
    {
        std::cout << "Refusing to initialize timer to None. It's not an error, it's just pointless." << std::endl;
        return;
    }
    timers[name] = Timer(target, interval, runtime.getElapsedTime().asMilliseconds());
    Py_INCREF(target);
}

void GameEngine::testTimers()
{
    int now = runtime.getElapsedTime().asMilliseconds();
    for (auto& [name, timer]: timers)
    {
        timer.test(now);
    }
}

void GameEngine::sUserInput()
{
    sf::Event event;
    while (window.pollEvent(event))
    {
        std::string actionType;
        int actionCode = 0;

        if (event.type == sf::Event::Closed) { running = false; continue; }
        // TODO: add resize event to Scene to react; call it after constructor too, maybe
        else if (event.type == sf::Event::Resized) {
            continue; // 7DRL short circuit. Resizing manually disabled
            /*
            sf::FloatRect area(0.f, 0.f, event.size.width, event.size.height);
            //sf::FloatRect area(0.f, 0.f, 1024.f, 768.f); // 7DRL 2024: attempt to set scale appropriately
            //sf::FloatRect area(0.f, 0.f, event.size.width, event.size.width * 0.75);
            visible = sf::View(area);
            window.setView(visible);
            //window.setSize(sf::Vector2u(event.size.width, event.size.width * 0.75)); // 7DRL 2024: window scaling
            std::cout << "Visible area set to (0, 0, " << event.size.width << ", " << event.size.height <<")"<<std::endl;
            actionType = "resize";
            //window.setSize(sf::Vector2u(event.size.width, event.size.width * 0.75)); // 7DRL 2024: window scaling
            */
        }

        else if (event.type == sf::Event::KeyPressed || event.type == sf::Event::MouseButtonPressed || event.type == sf::Event::MouseWheelScrolled) actionType = "start";
        else if (event.type == sf::Event::KeyReleased || event.type == sf::Event::MouseButtonReleased) actionType = "end";

        if (event.type == sf::Event::MouseButtonPressed || event.type == sf::Event::MouseButtonReleased)
            actionCode = ActionCode::keycode(event.mouseButton.button);
        else if (event.type == sf::Event::KeyPressed || event.type == sf::Event::KeyReleased)
            actionCode = ActionCode::keycode(event.key.code);
        else if (event.type == sf::Event::MouseWheelScrolled)
        {
        //    //sf::Mouse::Wheel w = event.MouseWheelScrollEvent.wheel;
            if (event.mouseWheelScroll.wheel == sf::Mouse::VerticalWheel)
            {
                int delta = 1;
                if (event.mouseWheelScroll.delta < 0) delta = -1;
                actionCode = ActionCode::keycode(event.mouseWheelScroll.wheel, delta );
                /*
                std::cout << "[GameEngine] Generated MouseWheel code w(" << (int)event.mouseWheelScroll.wheel << ") d(" << event.mouseWheelScroll.delta << ") D(" << delta << ") = " << actionCode << std::endl;
                std::cout << " test decode: isMouseWheel=" << ActionCode::isMouseWheel(actionCode) << ", wheel=" << ActionCode::wheel(actionCode) << ", delta=" << ActionCode::delta(actionCode) << std::endl;
                std::cout << " math test: actionCode && WHEEL_NEG -> " << (actionCode && ActionCode::WHEEL_NEG) << "; actionCode && WHEEL_DEL -> " << (actionCode && ActionCode::WHEEL_DEL) << ";" << std::endl;
                */
            }
        //    float d = event.MouseWheelScrollEvent.delta;
        //    actionCode = ActionCode::keycode(0, d);
        }
        else
            continue;

        //std::cout << "Event produced action code " << actionCode << ": " << actionType << std::endl;

        if (currentScene()->hasAction(actionCode))
        {
            std::string name = currentScene()->action(actionCode);
            currentScene()->doAction(name, actionType);
        }
        else if (currentScene()->key_callable != NULL && currentScene()->key_callable != Py_None)
        {
            PyObject* args = Py_BuildValue("(ss)", ActionCode::key_str(event.key.code).c_str(), actionType.c_str());
            PyObject* retval = PyObject_Call(currentScene()->key_callable, args, NULL);
            if (!retval)
            {   
                std::cout << "key_callable has raised an exception. It's going to STDERR and being dropped:" << std::endl;
                PyErr_Print();
                PyErr_Clear();
            } else if (retval != Py_None)
            {   
                std::cout << "key_callable returned a non-None value. It's not an error, it's just not being saved or used." << std::endl;
            }
        }
        else
        {
            //std::cout << "[GameEngine] Action not registered for input: " << actionCode << ": " << actionType << std::endl;
        }
    }
}

std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>> GameEngine::scene_ui(std::string target)
{
    /* 
    // facts about maps
    // You just can't do this during scenes["new_menu"] being assigned.
    std::cout << "Current scene is: " << scene << ". Searching for: " << target << ".\n";
    std::cout << "scenes.size(): " << scenes.size() << std::endl;
    std::cout << "scenes.count(target): " << scenes.count(target) << std::endl;
    std::cout << "scenes.find(target): " << std::distance(scenes.begin(), scenes.find(target)) << std::endl;
    std::cout << "iterators: " << std::distance(scenes.begin(), scenes.begin()) << " " <<
        std::distance(scenes.begin(), scenes.end()) << std::endl;
    std::cout << "scenes.contains(target): " << scenes.contains(target) << std::endl;
    std::cout << "scenes[target]: " << (long)(scenes[target]) << std::endl;
    */
    if (scenes.count(target) == 0) return NULL;
    return scenes[target]->ui_elements;
}
