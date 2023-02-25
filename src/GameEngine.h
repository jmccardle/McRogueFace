#pragma once

#include "Common.h"
#include "Entity.h"
#include "EntityManager.h"
#include "Scene.h"

class GameEngine
{
    sf::RenderWindow window;
    sf::Font font;
    std::string scene;
    std::map<std::string, Scene*> scenes;
    bool running = true;
    bool paused = false;
    int currentFrame = 0;
    sf::View visible;

public:
    GameEngine();
    Scene* currentScene();
    void changeScene(std::string);
    void quit();
    void setPause(bool);
    sf::Font & getFont();
    sf::RenderWindow & getWindow();
    void run();
    void sUserInput();
    int getFrame() { return currentFrame; }
    sf::View getView() { return visible; }
};
