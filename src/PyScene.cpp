#include "PyScene.h"
#include "ActionCode.h"
#include "Resources.h"
#include "PyCallable.h"
#include <algorithm>

PyScene::PyScene(GameEngine* g) : Scene(g)
{
    // mouse events
    registerAction(ActionCode::MOUSEBUTTON + sf::Mouse::Left, "left");
    registerAction(ActionCode::MOUSEBUTTON + sf::Mouse::Right, "right");
    registerAction(ActionCode::MOUSEWHEEL + ActionCode::WHEEL_DEL, "wheel_up");
    registerAction(ActionCode::MOUSEWHEEL + ActionCode::WHEEL_NEG + ActionCode::WHEEL_DEL, "wheel_down");

    // console (` / ~ key) - don't hard code.
    //registerAction(ActionCode::KEY + sf::Keyboard::Grave, "debug_menu");
}

void PyScene::update()
{
}

void PyScene::do_mouse_input(std::string button, std::string type)
{
    // In headless mode, mouse input is not available
    if (game->isHeadless()) {
        return;
    }
    
    auto unscaledmousepos = sf::Mouse::getPosition(game->getWindow());
    // Convert window coordinates to game coordinates using the viewport
    auto mousepos = game->windowToGameCoords(sf::Vector2f(unscaledmousepos));
    
    // Create a sorted copy by z-index (highest first)
    std::vector<std::shared_ptr<UIDrawable>> sorted_elements(*ui_elements);
    std::sort(sorted_elements.begin(), sorted_elements.end(),
        [](const auto& a, const auto& b) { return a->z_index > b->z_index; });
    
    // Check elements in z-order (top to bottom)
    for (const auto& element : sorted_elements) {
        if (!element->visible) continue;
        
        if (auto target = element->click_at(sf::Vector2f(mousepos))) {
            target->click_callable->call(mousepos, button, type);
            return; // Stop after first handler
        }
    }
}

void PyScene::doAction(std::string name, std::string type)
{
    if (name.compare("left") == 0 || name.compare("rclick") == 0 || name.compare("wheel_up") == 0 || name.compare("wheel_down") == 0) {
        do_mouse_input(name, type);
    }
    else if ACTIONONCE("debug_menu") {
        McRFPy_API::REPL();
    }
}

void PyScene::render()
{
    game->getRenderTarget().clear();
    
    // Only sort if z_index values have changed
    if (ui_elements_need_sort) {
        std::sort(ui_elements->begin(), ui_elements->end(), 
            [](const std::shared_ptr<UIDrawable>& a, const std::shared_ptr<UIDrawable>& b) {
                return a->z_index < b->z_index;
            });
        ui_elements_need_sort = false;
    }
    
    // Render in sorted order (no need to copy anymore)
    for (auto e: *ui_elements)
    {
        if (e) {
            // Track metrics
            game->metrics.uiElements++;
            if (e->visible) {
                game->metrics.visibleElements++;
                // Count this as a draw call (each visible element = 1+ draw calls)
                game->metrics.drawCalls++;
            }
            e->render();
        }
    }
    
    // Display is handled by GameEngine
}
