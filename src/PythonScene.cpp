#include "PythonScene.h"
#include "ActionCode.h"
#include "McRFPy_API.h"
//#include "Animation.h"

PythonScene::PythonScene(GameEngine* g, std::string pymodule)
: Scene(g) {
    // mouse events
    registerAction(ActionCode::MOUSEBUTTON + sf::Mouse::Left, "click");
    registerAction(ActionCode::MOUSEBUTTON + sf::Mouse::Right, "rclick");
    registerAction(ActionCode::MOUSEWHEEL + ActionCode::WHEEL_DEL, "wheel_up");
    registerAction(ActionCode::MOUSEWHEEL + ActionCode::WHEEL_NEG + ActionCode::WHEEL_DEL, "wheel_down");

    // keyboard events
    /*
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
    */
    // window resize
    registerAction(0, "event");

    dragging = false;
    drag_grid = NULL;
    
    // import pymodule and call start()
    McRFPy_API::executePyString("import " + pymodule);
    McRFPy_API::executePyString(pymodule + ".start()");
    
}

void PythonScene::animate() {
    //std::cout << "Number of animations: " << McRFPy_API::animations.size() << std::endl;
    auto frametime = game->getFrameTime();
    auto it = McRFPy_API::animations.begin();
    while (it != McRFPy_API::animations.end()) {
        //std::cout << "Iterating" << std::endl;
        (*it)->step(frametime);
        //std::cout << "Step complete" << std::endl;
        if ((*it)->isDone()) {
            //std::cout << "Cleaning up Animation" << std::endl;
            auto prev = it;
            it++;
            McRFPy_API::animations.erase(prev);
        } else it++;
    }
    /* // workin on it
    for (auto p : animations) {
        if (p.first == "int") {
            ((Animation<int>)p.second).step(frametime);
        } else if (p.first == "string") {
            ((Animation<std::string>)p.second).step(frametime);
        } else if (p.first == "float") {
            ((Animation<float>)p.second).step(frametime);
        } else if (p.first == "vector2f") {
            ((Animation<sf::Vector2f>)p.second).step(frametime);
        } else if (p.first == "vector2i") {
            ((Animation<sf::Vector2i>)p.second).step(frametime);
        } else if (p.first == "color") {
            ((Animation<int>)p.second).step(frametime); // TODO
        } else {
            std::cout << "Animation has label " << p.first << "; no type found" << std::endl;
        }
    }
    auto it = animations.begin();
    while (it != animations.end()) {
        bool done = false;
        if (p.first == "int") {
            ((Animation<int>)p.second).step(frametime);
        } else if (p.first == "string") {
            if ((Animation<std::string>)p.second).isDone()
                delete (Animation<std::string>)p.second
        } else if (p.first == "float") {
            ((Animation<float>)p.second).step(frametime);
        } else if (p.first == "vector2f") {
            ((Animation<sf::Vector2f>)p.second).step(frametime);
        } else if (p.first == "vector2i") {
            ((Animation<sf::Vector2i>)p.second).step(frametime);
        } else if (p.first == "color") {
            ((Animation<int>)p.second).step(frametime); // TODO
        if ((*it).second.isDone()) {
            animations.erase(it++);
        } else { it++; }
    }
        */
}

void PythonScene::update() {
	
	// turn cycle: If player's input made the state "computerturnwait", finish
	// 		all animations and then let the NPCs act
	if (McRFPy_API::animations.size() == 0 && McRFPy_API::input_mode.compare("computerturnwait") == 0) {
		McRFPy_API::input_mode = "computerturn";
	}
	else if (McRFPy_API::animations.size() == 0 && McRFPy_API::input_mode.compare("computerturnrunning") == 0) {
		McRFPy_API::input_mode = "playerturnstart";
	}
    McRFPy_API::entities.update();

    // check if left click is still down & mouse has moved
    // continue the drag motion
    if (dragging && drag_grid) {
        //std::cout << "Compute dragging" << std::endl;
        auto mousepos = sf::Mouse::getPosition(game->getWindow());
        auto dx = mouseprev.x - mousepos.x,
             dy = mouseprev.y - mousepos.y;
        if (dx != 0 || dy != 0) { McRFPy_API::do_camfollow = false; }
        drag_grid->center_x += (dx / drag_grid->zoom);
        drag_grid->center_y += (dy / drag_grid->zoom);
        mouseprev = mousepos;
    }

    animate();
    McRFPy_API::camFollow();
    if (McRFPy_API::input_mode.compare(std::string("computerturn")) == 0) McRFPy_API::computerTurn();
    if (McRFPy_API::input_mode.compare(std::string("playerturnstart")) == 0) McRFPy_API::playerTurn();
}

void PythonScene::doLClick(sf::Vector2i mousepos) {
    // UI buttons get first chance
    for (auto pair : McRFPy_API::menus) {
        if (!pair.second->visible) continue;
        for (auto b : pair.second->buttons) {
			//std::cout << "Box: " << pair.second->box.getPosition().x << ", " 
			//<< pair.second->box.getPosition().y << "; Button:" << b.rect.getPosition().x <<
			//", "  << b.rect.getPosition().y << "; Mouse: " << mousepos.x << ", " <<
			//mousepos.y << std::endl;
			
			// JANK: provide the button a relative coordinate.
            if (b.contains(pair.second->box.getPosition(), mousepos)) {
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
    //std::cout << "name: " << name << ", type: " << type << std::endl;
    if (ACTIONPY) {
        McRFPy_API::doAction(name.substr(0, name.size() - 3));
    }
    else if (ACTIONONCE("click")) {
        // left click start
        //std::cout << "LClick started at (" << mousepos.x << ", " << mousepos.y << ")" << std::endl;
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
        //std::cout << "LClick ended at (" << mousepos.x << ", " << mousepos.y << ")" << std::endl;
        // if click ended without starting a drag event, try lclick?
        if (dragstart == mousepos) {
            // mouse did not move, do click
            //std::cout << "(did not move)" << std::endl;
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
    else if (ACTIONONCE("up"))        { McRFPy_API::player_input(+0, -1); }
    else if (ACTIONONCE("upright"))   { McRFPy_API::player_input(+1, -1); }
    else if (ACTIONONCE("right"))     { McRFPy_API::player_input(+1, +0); }
    else if (ACTIONONCE("downright")) { McRFPy_API::player_input(+1, +1); }
    else if (ACTIONONCE("down"))      { McRFPy_API::player_input(+0, +1); }
    else if (ACTIONONCE("downleft"))  { McRFPy_API::player_input(-1, +1); }
    else if (ACTIONONCE("left"))      { McRFPy_API::player_input(-1, +0); }
    else if (ACTIONONCE("upleft"))    { McRFPy_API::player_input(-1, -1); }
    else if (ACTIONONCE("wait"))      { McRFPy_API::player_input(+0, +0); }
}

bool PythonScene::registerActionInjected(int code, std::string name) {
    std::cout << "Registering injected action (PythonScene): " << code << " (" << ActionCode::KEY + code << ")\n";
    registerAction(ActionCode::KEY + code, name);
    //return false;
    return true;
}

bool PythonScene::unregisterActionInjected(int code, std::string name) {
    return false;
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
