#pragma once

#include "Common.h"
#include "Scene.h"
#include "GameEngine.h"
#include "Button.h"
#include "UIMenu.h"
#include "VectorShape.h"

class UITestScene: public Scene
{
    sf::Text text;
    EntityManager entities;
    //Button test_button;
    //UIMenu test_menu;
    //UIMenu test_menu2;
    std::vector<UIMenu> menus;
    VectorShape test_ship;
    float desired_angle = 0;
    sf::View viewport;
    float zoom = 1;
    sf::Vector2f resolution;
    int grid_spacing = 500;

public:
    UITestScene(GameEngine*);
    void update() override final;
    void doAction(std::string, std::string) override final;
    void doButton(std::string);
    void sRender() override final;
};
