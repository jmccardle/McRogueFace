#pragma once

#include "Common.h"
#include "Scene.h"
#include "GameEngine.h"

class MenuScene: public Scene
{
    sf::Text text;
    sf::Text text2;
    sf::Text text3;

public:
    MenuScene(GameEngine*);
    void update() override final;
    void doAction(std::string, std::string) override final;
    void sRender() override final;
};
