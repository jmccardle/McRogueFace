#include "GameEngine.h"
#include "MenuScene.h"
//#include "UITestScene.h"
#include "ActionCode.h"
#include "McRFPy_API.h"
#include "PythonScene.h"
#include "UITestScene.h"
#include "Resources.h"

GameEngine::GameEngine()
{
    Resources::font.loadFromFile("./assets/JetbrainsMono.ttf");
    Resources::game = this;
    window.create(sf::VideoMode(1024, 768), "McRogueFace - r/RoguelikeDev Tutorial Run");
    visible = window.getDefaultView();
    window.setFramerateLimit(30);
    scene = "uitest";
    //std::cout << "Constructing MenuScene" << std::endl;
    scenes["menu"] = new MenuScene(this);
    scenes["uitest"] = new UITestScene(this);
    //std::cout << "Constructed MenuScene" <<std::endl;
    //scenes["play"] = new UITestScene(this);
    //api = new McRFPy_API(this);
    
    McRFPy_API::game = this;
    McRFPy_API::api_init();
    McRFPy_API::executePyString("import mcrfpy");
    //McRFPy_API::executePyString("from UIMenu import *");
    //McRFPy_API::executePyString("from Grid import *");

    //scenes["py"] = new PythonScene(this, "TestScene");

    IndexSprite::game = this;

    clock.restart();
}

Scene* GameEngine::currentScene() { return scenes[scene]; }
void GameEngine::changeScene(std::string s) { std::cout << "Current scene is now '" << s << "'\n"; scene = s; }
void GameEngine::quit() { running = false; }
void GameEngine::setPause(bool p) { paused = p; }
sf::Font & GameEngine::getFont() { /*return font; */ return Resources::font; }
sf::RenderWindow & GameEngine::getWindow() { return window; }

void GameEngine::run()
{
    clock.restart();
    while (running)
    {
        currentScene()->update();
        sUserInput();
        if (!paused)
        {
        }
        currentScene()->sRender();
        currentFrame++;
        frameTime = clock.restart().asSeconds();
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
        else if (event.type == sf::Event::Resized) {
            sf::FloatRect area(0.f, 0.f, event.size.width, event.size.height);
            visible = sf::View(area);
            window.setView(visible);
            //std::cout << "Visible area set to (0, 0, " << event.size.width << ", " << event.size.height <<")"<<std::endl;
            actionType = "resize";
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
        else
        {
            //std::cout << "[GameEngine] Action not registered for input: " << actionCode << ": " << actionType << std::endl;
        }
    }
}
