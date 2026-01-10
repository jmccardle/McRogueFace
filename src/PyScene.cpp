#include "PyScene.h"
#include "ActionCode.h"
#include "Resources.h"
#include "PyCallable.h"
#include "UIFrame.h"
#include "UIGrid.h"
#include "McRFPy_Automation.h"  // #111 - For simulated mouse position
#include "PythonObjectCache.h"  // #184 - For subclass callback support
#include <algorithm>
#include <functional>

// ============================================================================
// #184: Helper functions for calling Python subclass methods
// ============================================================================

// Try to call a Python method on a UIDrawable subclass
// Returns true if a method was found and called, false otherwise
static bool tryCallPythonMethod(UIDrawable* drawable, const char* method_name,
                                 sf::Vector2f mousepos, const char* button, const char* action) {
    if (!drawable->is_python_subclass) return false;

    PyObject* pyObj = PythonObjectCache::getInstance().lookup(drawable->serial_number);
    if (!pyObj) return false;

    // Check and refresh cache if needed
    PyObject* type = (PyObject*)Py_TYPE(pyObj);
    if (!drawable->isCallbackCacheValid(type)) {
        drawable->refreshCallbackCache(pyObj);
    }

    // Check if this method exists in the cache
    bool has_method = false;
    if (strcmp(method_name, "on_click") == 0) {
        has_method = drawable->callback_cache.has_on_click;
    } else if (strcmp(method_name, "on_enter") == 0) {
        has_method = drawable->callback_cache.has_on_enter;
    } else if (strcmp(method_name, "on_exit") == 0) {
        has_method = drawable->callback_cache.has_on_exit;
    } else if (strcmp(method_name, "on_move") == 0) {
        has_method = drawable->callback_cache.has_on_move;
    }

    if (!has_method) {
        Py_DECREF(pyObj);
        return false;
    }

    // Get and call the method
    PyObject* method = PyObject_GetAttrString(pyObj, method_name);
    bool called = false;

    if (method && PyCallable_Check(method) && method != Py_None) {
        // Call with (x, y, button, action) signature
        PyObject* result = PyObject_CallFunction(method, "ffss",
            mousepos.x, mousepos.y, button, action);
        if (result) {
            Py_DECREF(result);
            called = true;
        } else {
            PyErr_Print();
        }
    }

    PyErr_Clear();
    Py_XDECREF(method);
    Py_DECREF(pyObj);

    return called;
}

// Check if a UIDrawable can potentially handle an event
// (has either a callable property OR is a Python subclass that might have a method)
static bool canHandleEvent(UIDrawable* drawable, const char* event_type) {
    // Check for property-assigned callable first
    if (strcmp(event_type, "click") == 0) {
        if (drawable->click_callable && !drawable->click_callable->isNone()) return true;
    } else if (strcmp(event_type, "enter") == 0) {
        if (drawable->on_enter_callable && !drawable->on_enter_callable->isNone()) return true;
    } else if (strcmp(event_type, "exit") == 0) {
        if (drawable->on_exit_callable && !drawable->on_exit_callable->isNone()) return true;
    } else if (strcmp(event_type, "move") == 0) {
        if (drawable->on_move_callable && !drawable->on_move_callable->isNone()) return true;
    }

    // If it's a Python subclass, it might have a method
    return drawable->is_python_subclass;
}

// ============================================================================

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
            // #184: Try property-assigned callable first (fast path)
            if (target->click_callable && !target->click_callable->isNone()) {
                target->click_callable->call(mousepos, button, type);
                return; // Stop after first handler
            }

            // #184: Try Python subclass method
            if (tryCallPythonMethod(target, "on_click", mousepos, button.c_str(), type.c_str())) {
                return; // Stop after first handler
            }

            // Element claimed the click but had no handler - still stop propagation
            // (This maintains consistent behavior for subclasses that don't define on_click)
            if (target->is_python_subclass) {
                return;
            }
        }
    }
}

void PyScene::doAction(std::string name, std::string type)
{
    if (name.compare("left") == 0 || name.compare("right") == 0 || name.compare("wheel_up") == 0 || name.compare("wheel_down") == 0) {
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
            // #184: Try property-assigned callable first, then Python subclass method
            if (drawable->on_enter_callable && !drawable->on_enter_callable->isNone()) {
                drawable->on_enter_callable->call(mousepos, "enter", "start");
            } else if (drawable->is_python_subclass) {
                tryCallPythonMethod(drawable, "on_enter", mousepos, "enter", "start");
            }
        } else if (!is_inside && was_hovered) {
            // Mouse exited
            drawable->hovered = false;
            // #184: Try property-assigned callable first, then Python subclass method
            if (drawable->on_exit_callable && !drawable->on_exit_callable->isNone()) {
                drawable->on_exit_callable->call(mousepos, "exit", "start");
            } else if (drawable->is_python_subclass) {
                tryCallPythonMethod(drawable, "on_exit", mousepos, "exit", "start");
            }
        }

        // #141 - Fire on_move if mouse is inside and has a move/on_move callback
        // #184: Try property-assigned callable first, then Python subclass method
        // Check is_python_subclass before function call to avoid overhead on hot path
        if (is_inside) {
            if (drawable->on_move_callable && !drawable->on_move_callable->isNone()) {
                drawable->on_move_callable->call(mousepos, "move", "start");
            } else if (drawable->is_python_subclass) {
                tryCallPythonMethod(drawable, "on_move", mousepos, "move", "start");
            }
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
