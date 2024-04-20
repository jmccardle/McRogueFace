#pragma once

#include "Common.h"
#include "Scene.h"
#include "GameEngine.h"
//#include <list>
//#include "UI.h"

class UITestScene: public Scene
{
    sf::Text text;
    //UIFrame e1, e1a, e1aa;
    //UICaption e2;
    //std::vector<UIDrawable*> ui_elements;
    sf::Texture t;

public:
    UITestScene(GameEngine*);
    void update() override final;
    void doAction(std::string, std::string) override final;
    void render() override final;
};
