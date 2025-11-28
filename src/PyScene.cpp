#include "PyScene.h"
#include "ActionCode.h"
#include "Resources.h"
#include "PyCallable.h"
#include "UIFrame.h"
#include "UIGrid.h"
#include "McRFPy_Automation.h"  // #111 - For simulated mouse position
#include <algorithm>
#include <functional>

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
    sf::Vector2f mousepos;

    // #111 - In headless mode, use simulated mouse position
    if (game->isHeadless()) {
        sf::Vector2i simPos = McRFPy_Automation::getSimulatedMousePosition();
        mousepos = sf::Vector2f(static_cast<float>(simPos.x), static_cast<float>(simPos.y));
    } else {
        auto unscaledmousepos = sf::Mouse::getPosition(game->getWindow());
        // Convert window coordinates to game coordinates using the viewport
        mousepos = game->windowToGameCoords(sf::Vector2f(unscaledmousepos));
    }
    
    // Only sort if z_index values have changed
    if (ui_elements_need_sort) {
        // Sort in ascending order (same as render)
        std::sort(ui_elements->begin(), ui_elements->end(),
            [](const auto& a, const auto& b) { return a->z_index < b->z_index; });
        ui_elements_need_sort = false;
    }
    
    // Check elements in reverse z-order (highest z_index first, top to bottom)
    // Use reverse iterators to go from end to beginning
    for (auto it = ui_elements->rbegin(); it != ui_elements->rend(); ++it) {
        const auto& element = *it;
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

// #140 - Mouse enter/exit tracking
void PyScene::do_mouse_hover(int x, int y)
{
    // In headless mode, use the coordinates directly (already in game space)
    sf::Vector2f mousepos;
    if (game->isHeadless()) {
        mousepos = sf::Vector2f(static_cast<float>(x), static_cast<float>(y));
    } else {
        // Convert window coordinates to game coordinates using the viewport
        mousepos = game->windowToGameCoords(sf::Vector2f(static_cast<float>(x), static_cast<float>(y)));
    }

    // Helper function to process hover for a single drawable and its children
    std::function<void(UIDrawable*)> processHover = [&](UIDrawable* drawable) {
        if (!drawable || !drawable->visible) return;

        bool is_inside = drawable->contains_point(mousepos.x, mousepos.y);
        bool was_hovered = drawable->hovered;

        if (is_inside && !was_hovered) {
            // Mouse entered
            drawable->hovered = true;
            if (drawable->on_enter_callable) {
                drawable->on_enter_callable->call(mousepos, "enter", "start");
            }
        } else if (!is_inside && was_hovered) {
            // Mouse exited
            drawable->hovered = false;
            if (drawable->on_exit_callable) {
                drawable->on_exit_callable->call(mousepos, "exit", "start");
            }
        }

        // #141 - Fire on_move if mouse is inside and has a move callback
        if (is_inside && drawable->on_move_callable) {
            drawable->on_move_callable->call(mousepos, "move", "start");
        }

        // Process children for Frame elements
        if (drawable->derived_type() == PyObjectsEnum::UIFRAME) {
            auto frame = static_cast<UIFrame*>(drawable);
            if (frame->children) {
                for (auto& child : *frame->children) {
                    processHover(child.get());
                }
            }
        }
        // Process children for Grid elements
        else if (drawable->derived_type() == PyObjectsEnum::UIGRID) {
            auto grid = static_cast<UIGrid*>(drawable);

            // #142 - Update cell hover tracking for grid
            grid->updateCellHover(mousepos);

            if (grid->children) {
                for (auto& child : *grid->children) {
                    processHover(child.get());
                }
            }
        }
    };

    // Process all top-level UI elements
    for (auto& element : *ui_elements) {
        processHover(element.get());
    }
}

void PyScene::render()
{
    // #118: Skip rendering if scene is not visible
    if (!visible) {
        return;
    }

    game->getRenderTarget().clear();

    // Only sort if z_index values have changed
    if (ui_elements_need_sort) {
        std::sort(ui_elements->begin(), ui_elements->end(),
            [](const std::shared_ptr<UIDrawable>& a, const std::shared_ptr<UIDrawable>& b) {
                return a->z_index < b->z_index;
            });
        ui_elements_need_sort = false;
    }

    // Render in sorted order with scene-level transformations
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

            // #118: Apply scene-level opacity to element
            float original_opacity = e->opacity;
            if (opacity < 1.0f) {
                e->opacity = original_opacity * opacity;
            }

            // #118: Render with scene position offset
            e->render(position, game->getRenderTarget());

            // #118: Restore original opacity
            if (opacity < 1.0f) {
                e->opacity = original_opacity;
            }
        }
    }

    // Display is handled by GameEngine
}
