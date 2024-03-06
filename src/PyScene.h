#pragma once

#include "Common.h"
#include "Scene.h"
#include "GameEngine.h"

class PyScene: public Scene
{

public:
    PyScene(GameEngine*);
    void update() override final;
    void doAction(std::string, std::string) override final;
    void sRender() override final;
};
