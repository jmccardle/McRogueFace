#pragma once

#include <string>
#include <memory>

class GameEngine;
class UIDrawable;
class UIEntity;
class UIFrame;
class UIGrid;

/**
 * @brief ImGui-based scene tree explorer for debugging
 *
 * Displays hierarchical view of all scenes and their UI elements.
 * Allows switching between scenes and collapsing/expanding the tree.
 * Activated by F4 key. Mutually exclusive with the console (grave key).
 */
class ImGuiSceneExplorer {
public:
    ImGuiSceneExplorer() = default;

    // Core functionality
    void render(GameEngine& engine);
    void toggle();
    bool isVisible() const { return visible; }
    void setVisible(bool v) { visible = v; }

    // Configuration - uses same enabled flag as console
    static bool isEnabled();

private:
    bool visible = false;

    // Tree rendering helpers
    void renderSceneNode(GameEngine& engine, const std::string& sceneName, bool isActive);
    void renderDrawableNode(std::shared_ptr<UIDrawable> drawable, int depth = 0);
    void renderEntityNode(std::shared_ptr<UIEntity> entity);

    // Get display name for a drawable (name or type + address)
    std::string getDisplayName(UIDrawable* drawable);
    std::string getEntityDisplayName(UIEntity* entity);

    // Get type name string
    const char* getTypeName(UIDrawable* drawable);
};
