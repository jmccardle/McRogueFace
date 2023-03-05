#include "PythonScene.h"
#include "ActionCode.h"
#include "McRFPy_API.h"

PythonScene::PythonScene(GameEngine* g, std::string pymodule)
: Scene(g) {
    // mouse events
    registerAction(ActionCode::MOUSEBUTTON + sf::Mouse::Left, "click");
    registerAction(ActionCode::MOUSEBUTTON + sf::Mouse::Left, "rclick");
    registerAction(ActionCode::MOUSEWHEEL + ActionCode::WHEEL_DEL, "wheel_up");
    registerAction(ActionCode::MOUSEWHEEL + ActionCode::WHEEL_NEG + ActionCode::WHEEL_DEL, "wheel_down");

    // keyboard events
    registerAction(ActionCode::KEY + sf::Keyboard::Q, "upleft");
    registerAction(ActionCode::KEY + sf::Keyboard::W, "up");
    registerAction(ActionCode::KEY + sf::Keyboard::E, "upright");
    registerAction(ActionCode::KEY + sf::Keyboard::A, "left");
    registerAction(ActionCode::KEY + sf::Keyboard::S, "down");
    registerAction(ActionCode::KEY + sf::Keyboard::D, "right");
    registerAction(ActionCode::KEY + sf::Keyboard::Z, "downleft");
    registerAction(ActionCode::KEY + sf::Keyboard::X, "wait");
    registerAction(ActionCode::KEY + sf::Keyboard::C, "downright");

    registerAction(ActionCode::KEY + sf::Keyboard::Numpad7, "upleft");
    registerAction(ActionCode::KEY + sf::Keyboard::Numpad8, "up");
    registerAction(ActionCode::KEY + sf::Keyboard::Numpad9, "upright");
    registerAction(ActionCode::KEY + sf::Keyboard::Numpad4, "left");
    registerAction(ActionCode::KEY + sf::Keyboard::Numpad5, "wait");
    registerAction(ActionCode::KEY + sf::Keyboard::Numpad6, "right");
    registerAction(ActionCode::KEY + sf::Keyboard::Numpad1, "downleft");
    registerAction(ActionCode::KEY + sf::Keyboard::Numpad2, "down");
    registerAction(ActionCode::KEY + sf::Keyboard::Numpad3, "downright");

    // window resize
    registerAction(0, "event");

    dragging = false;
    
    // import pymodule and call start()
    McRFPy_API::executePyString("import " + pymodule);
    McRFPy_API::executePyString(pymodule + ".start()");
}

void PythonScene::update() {
    McRFPy_API::entities.update();

    // check if left click is still down & mouse has moved
    // continue the drag motion
    if (dragging && drag_grid) {
        auto mousepos = sf::Mouse::getPosition(game->getWindow());
        auto dx = mousepos.x - mouseprev.x,
             dy = mousepos.y - mouseprev.y;
        drag_grid->center_x += (dx / drag_grid->zoom);
        drag_grid->center_y += (dy / drag_grid->zoom);
    }

}

void PythonScene::doLClick(sf::Vector2i mousepos) {
    // UI buttons get first chance
    for (auto pair : McRFPy_API::menus) {
        if (!pair.second->visible) continue;
        for (auto b : pair.second->buttons) {
            if (b.contains(mousepos)) {
                McRFPy_API::doAction(b.getAction());
                return;
            }
        }
    }
    // left clicking a grid to select a square
    for (auto pair : McRFPy_API::grids) {
        if (!pair.second->visible) continue;
        if (pair.second->contains(mousepos)) {
            // grid was clicked
            return;
        }
    }
}

void PythonScene::doRClick(sf::Vector2i mousepos) {
    // just grids for right click
    for (auto pair : McRFPy_API::grids) {
        if (!pair.second->visible) continue;
        if (pair.second->contains(mousepos)) {
            // grid was clicked
            return;
        }
    }
}

void PythonScene::doZoom(sf::Vector2i mousepos, int value) {
    // just grids for right click
    for (auto pair : McRFPy_API::grids) {
        if (!pair.second->visible) continue;
        if (pair.second->contains(mousepos)) {
            // grid was zoomed
            float new_zoom = pair.second->zoom + (value * 0.25);
            if (new_zoom >= 0.5 && new_zoom <= 5.0) {
                pair.second->zoom = new_zoom;
            }
        }
    }
}

void PythonScene::doAction(std::string name, std::string type) {
    auto mousepos = sf::Mouse::getPosition(game->getWindow());
    if (ACTIONONCE("click")) {
        // left click start
        dragstart = mousepos;
        mouseprev = mousepos;
        dragging = true;
        // determine the grid that contains the cursor
        for (auto pair : McRFPy_API::grids) {
            if (!pair.second->visible) continue;
            if (pair.second->contains(mousepos)) {
                // grid was clicked
                drag_grid = pair.second;
            }
        }
    }
    else if (ACTIONAFTER("click")) {
        // left click end
        // if click ended without starting a drag event, try lclick?
        if (dragstart == mousepos) {
            // mouse did not move, do click
            doLClick(mousepos);
        }
        dragging = false;
        drag_grid = NULL;
    }
    else if (ACTIONONCE("rclick")) {
        // not going to test for right click drag - just rclick
        doRClick(mousepos);
    }
    else if (ACTIONONCE("wheel_up")) {
        // try zoom in
        doZoom(mousepos, 1);
    }
    else if (ACTIONONCE("wheel_down")) {
        // try zoom out
        doZoom(mousepos, -1);
    }
}

void PythonScene::sRender() {
    game->getWindow().clear();

    for (auto pair: McRFPy_API::grids) {
        if (!pair.second->visible) continue;
        pair.second->render(game->getWindow());
    }

    for (auto pair: McRFPy_API::menus) {
        if (!pair.second->visible) continue;
        pair.second->render(game->getWindow());
    }

    game->getWindow().display();
}
