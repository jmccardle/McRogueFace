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
    void render() override final;

    void do_mouse_input(std::string, std::string);
    
    // Dirty flag for z_index sorting optimization
    bool ui_elements_need_sort = true;
};
