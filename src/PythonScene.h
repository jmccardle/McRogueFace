#pragma once

#include "Common.h"
#include "Scene.h"
#include "GameEngine.h"
#include "Grid.h"
//#include "Animation.h"
//#include <list>

class PythonScene: public Scene
{
    sf::Vector2i dragstart, mouseprev;
    bool dragging;
    Grid* drag_grid;
    void doLClick(sf::Vector2i);
    void doRClick(sf::Vector2i);
    void doZoom(sf::Vector2i, int);
    //std::list<Animation*> animations;
    void animate();
    std::map<std::string, bool> actionInjected;
    
public:
    PythonScene(GameEngine*, std::string);
    void update() override final;
    void doAction(std::string, std::string) override final;
    void sRender() override final;
    bool registerActionInjected(int, std::string) override;
    bool unregisterActionInjected(int, std::string) override;
};
