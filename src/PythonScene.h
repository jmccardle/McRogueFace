#pragma once

#include "Common.h"
#include "Scene.h"
#include "GameEngine.h"
#include "Grid.h"

class PythonScene: public Scene
{
    sf::Vector2i dragstart, mouseprev;
    bool dragging;
    Grid* drag_grid;
    void doLClick(sf::Vector2i);
    void doRClick(sf::Vector2i);
    void doZoom(sf::Vector2i, int);
public:
    PythonScene(GameEngine*, std::string);
    void update() override final;
    void doAction(std::string, std::string) override final;
    void sRender() override final;
};
