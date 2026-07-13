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
    void do_mouse_hover(int x, int y);  // #140 - Mouse enter/exit tracking
    void do_mouse_leave();              // #363 - cursor left the window

    // Dirty flag for z_index sorting optimization
    bool ui_elements_need_sort = true;

private:
    // #363 - Shared hover walk. in_window=false makes it an exit-only sweep (no
    // drawable may become hovered), which is what a window-leave means.
    void dispatch_hover(sf::Vector2f mousepos, bool in_window);

    // #363 - Last cursor position seen by do_mouse_hover, reported to the exit
    // callbacks fired by do_mouse_leave (MouseLeft carries no coordinates).
    sf::Vector2f last_mouse_pos{0.f, 0.f};
};
