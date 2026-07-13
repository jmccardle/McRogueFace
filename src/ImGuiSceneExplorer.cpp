// ImGuiSceneExplorer.cpp - Debug scene hierarchy explorer using ImGui
// This file is excluded from headless and SDL2 builds (ImGui-SFML only)

#if !defined(MCRF_HEADLESS) && !defined(MCRF_SDL2)

#include "ImGuiSceneExplorer.h"
#include "imgui.h"
#include "GameEngine.h"
#include "Scene.h"
#include "UIDrawable.h"
#include "UIFrame.h"
#include "UICaption.h"
#include "UISprite.h"
#include "UIGridView.h"
#include "GridData.h"
#include "UIEntity.h"
#include "ImGuiConsole.h"
#include "PythonObjectCache.h"
#include <sstream>
#include <iomanip>
#include <vector>

bool ImGuiSceneExplorer::isEnabled() {
    // Use the same enabled flag as the console
    return ImGuiConsole::isEnabled();
}

void ImGuiSceneExplorer::toggle() {
    if (isEnabled()) {
        visible = !visible;
    }
}

void ImGuiSceneExplorer::render(GameEngine& engine) {
    if (!visible || !isEnabled()) return;

    ImGuiIO& io = ImGui::GetIO();

    // Position on the right side of the screen
    ImGui::SetNextWindowSize(ImVec2(350, io.DisplaySize.y * 0.6f), ImGuiCond_FirstUseEver);
    ImGui::SetNextWindowPos(ImVec2(io.DisplaySize.x - 360, 10), ImGuiCond_FirstUseEver);

    ImGuiWindowFlags flags = ImGuiWindowFlags_NoCollapse;

    if (!ImGui::Begin("Scene Explorer", &visible, flags)) {
        ImGui::End();
        return;
    }

    // Scene tree header
    ImGui::Text("Scenes (%zu):", engine.getSceneNames().size());
    ImGui::Separator();

    // Scrollable tree region
    ImGui::BeginChild("SceneTree", ImVec2(0, 0), false, ImGuiWindowFlags_HorizontalScrollbar);

    // Get all scene names and render each
    std::string currentSceneName = engine.scene;
    std::vector<std::string> sceneNames = engine.getSceneNames();

    for (const auto& sceneName : sceneNames) {
        bool isActive = (sceneName == currentSceneName);
        renderSceneNode(engine, sceneName, isActive);
    }

    ImGui::EndChild();

    ImGui::End();
}

void ImGuiSceneExplorer::renderSceneNode(GameEngine& engine, const std::string& sceneName, bool isActive) {
    ImGuiTreeNodeFlags sceneFlags = ImGuiTreeNodeFlags_OpenOnArrow
                                   | ImGuiTreeNodeFlags_OpenOnDoubleClick
                                   | ImGuiTreeNodeFlags_DefaultOpen;

    if (isActive) {
        sceneFlags |= ImGuiTreeNodeFlags_Selected;
    }

    // Build label with active indicator
    std::string label = sceneName;
    if (isActive) {
        label += " [active]";
    }

    // Scene icon/indicator
    bool sceneOpen = ImGui::TreeNodeEx(("##scene_" + sceneName).c_str(), sceneFlags, "%s %s",
                                        isActive ? ">" : " ", label.c_str());

    // Click to activate scene (if not already active)
    if (ImGui::IsItemClicked() && !isActive) {
        engine.changeScene(sceneName);
    }

    if (sceneOpen) {
        // Get scene's UI elements
        auto ui_elements = engine.scene_ui(sceneName);
        if (ui_elements && !ui_elements->empty()) {
            for (auto& drawable : *ui_elements) {
                if (drawable) {
                    renderDrawableNode(drawable, 0);
                }
            }
        } else {
            ImGui::TextDisabled("  (empty)");
        }
        ImGui::TreePop();
    }
}

void ImGuiSceneExplorer::renderDrawableNode(std::shared_ptr<UIDrawable> drawable, int depth) {
    if (!drawable) return;

    ImGuiTreeNodeFlags flags = ImGuiTreeNodeFlags_OpenOnArrow
                              | ImGuiTreeNodeFlags_OpenOnDoubleClick
                              | ImGuiTreeNodeFlags_SpanAvailWidth;

    // Check if this node has children
    bool hasChildren = false;
    UIFrame* frame = nullptr;
    // #358: dispatch on the asGridData() virtual (#355), not derived_type() --
    // nothing in a scene graph is ever a bare UIGRID since #252 (Grid nodes are
    // UIGridView instances), so a UIGRID enum arm here is always dead code.
    GridData* gridData = drawable->asGridData();
    // #364: overlay children hang off the VIEW; entities off the shared data.
    UIGridView* gridView = nullptr;

    switch (drawable->derived_type()) {
        case PyObjectsEnum::UIFRAME:
            frame = static_cast<UIFrame*>(drawable.get());
            hasChildren = frame->children && !frame->children->empty();
            break;
        case PyObjectsEnum::UIGRIDVIEW:
            gridView = static_cast<UIGridView*>(drawable.get());
            break;
        default:
            break;
    }

    if (gridData) {
        hasChildren = (gridData->entities && !gridData->entities->empty()) ||
                     (gridView && gridView->children && !gridView->children->empty());
    }

    if (!hasChildren) {
        flags |= ImGuiTreeNodeFlags_Leaf | ImGuiTreeNodeFlags_NoTreePushOnOpen;
    }

    // Visibility indicator
    const char* visIcon = drawable->visible ? "[v]" : "[h]";

    // Build display string
    std::string displayName = getDisplayName(drawable.get());
    std::string nodeLabel = std::string(visIcon) + " " + getTypeName(drawable.get()) + ": " + displayName;

    // Use pointer as unique ID
    bool nodeOpen = ImGui::TreeNodeEx((void*)(intptr_t)drawable.get(), flags, "%s", nodeLabel.c_str());

    // Double-click to toggle visibility
    if (ImGui::IsItemHovered() && ImGui::IsMouseDoubleClicked(0)) {
        drawable->visible = !drawable->visible;
    }

    // Handle leaf nodes (NoTreePushOnOpen means TreePop not needed)
    if (!hasChildren) {
        return;
    }

    if (nodeOpen) {
        // Render children based on type
        if (frame && frame->children) {
            for (auto& child : *frame->children) {
                if (child) {
                    renderDrawableNode(child, depth + 1);
                }
            }
        }

        if (gridData) {
            // Render entities
            if (gridData->entities && !gridData->entities->empty()) {
                ImGuiTreeNodeFlags entityGroupFlags = ImGuiTreeNodeFlags_OpenOnArrow;
                bool entitiesOpen = ImGui::TreeNodeEx("Entities", entityGroupFlags, "Entities (%zu)",
                                                       gridData->entities->size());
                if (entitiesOpen) {
                    for (auto& entity : *gridData->entities) {
                        if (entity) {
                            renderEntityNode(entity);
                        }
                    }
                    ImGui::TreePop();
                }
            }

            // Render the view's drawable children (overlays) -- #364: owned by the
            // view, not the shared data, so a second view lists its own.
            if (gridView && gridView->children && !gridView->children->empty()) {
                ImGuiTreeNodeFlags overlayGroupFlags = ImGuiTreeNodeFlags_OpenOnArrow;
                bool overlaysOpen = ImGui::TreeNodeEx("Overlays", overlayGroupFlags, "Overlays (%zu)",
                                                       gridView->children->size());
                if (overlaysOpen) {
                    for (auto& child : *gridView->children) {
                        if (child) {
                            renderDrawableNode(child, depth + 1);
                        }
                    }
                    ImGui::TreePop();
                }
            }
        }

        ImGui::TreePop();
    }
}

void ImGuiSceneExplorer::renderEntityNode(std::shared_ptr<UIEntity> entity) {
    if (!entity) return;

    ImGuiTreeNodeFlags flags = ImGuiTreeNodeFlags_Leaf
                              | ImGuiTreeNodeFlags_NoTreePushOnOpen
                              | ImGuiTreeNodeFlags_SpanAvailWidth;

    std::string displayName = getEntityDisplayName(entity.get());
    std::string nodeLabel = "Entity: " + displayName;

    ImGui::TreeNodeEx((void*)(intptr_t)entity.get(), flags, "%s", nodeLabel.c_str());
}

std::string ImGuiSceneExplorer::getDisplayName(UIDrawable* drawable) {
    if (!drawable) return "(null)";

    // Try to get Python object repr from cache
    if (drawable->serial_number != 0) {
        PyObject* pyObj = PythonObjectCache::getInstance().lookup(drawable->serial_number);
        if (pyObj) {
            PyObject* repr = PyObject_Repr(pyObj);
            if (repr) {
                const char* repr_str = PyUnicode_AsUTF8(repr);
                if (repr_str) {
                    std::string result(repr_str);
                    Py_DECREF(repr);
                    Py_DECREF(pyObj);
                    return result;
                }
                Py_DECREF(repr);
            }
            Py_DECREF(pyObj);
        }
    }

    // Use name if available
    if (!drawable->name.empty()) {
        return "\"" + drawable->name + "\"";
    }

    // Fall back to address
    std::ostringstream oss;
    oss << "@" << std::hex << std::setw(8) << std::setfill('0') << (uintptr_t)drawable;
    return oss.str();
}

std::string ImGuiSceneExplorer::getEntityDisplayName(UIEntity* entity) {
    if (!entity) return "(null)";

    // Try to get Python object repr from cache
    if (entity->serial_number != 0) {
        PyObject* pyObj = PythonObjectCache::getInstance().lookup(entity->serial_number);
        if (pyObj) {
            PyObject* repr = PyObject_Repr(pyObj);
            if (repr) {
                const char* repr_str = PyUnicode_AsUTF8(repr);
                if (repr_str) {
                    std::string result(repr_str);
                    Py_DECREF(repr);
                    Py_DECREF(pyObj);
                    return result;
                }
                Py_DECREF(repr);
            }
            Py_DECREF(pyObj);
        }
    }

    // Fall back to position
    std::ostringstream oss;
    oss << "(" << entity->position.x << ", " << entity->position.y << ")";
    return oss.str();
}

const char* ImGuiSceneExplorer::getTypeName(UIDrawable* drawable) {
    if (!drawable) return "null";

    switch (drawable->derived_type()) {
        case PyObjectsEnum::UIFRAME:      return "Frame";
        case PyObjectsEnum::UICAPTION:    return "Caption";
        case PyObjectsEnum::UISPRITE:     return "Sprite";
        case PyObjectsEnum::UIGRID:       return "Grid";
        case PyObjectsEnum::UIGRIDVIEW:   return "GridView";
        case PyObjectsEnum::UILINE:       return "Line";
        case PyObjectsEnum::UICIRCLE:     return "Circle";
        case PyObjectsEnum::UIARC:        return "Arc";
        case PyObjectsEnum::UIVIEWPORT3D: return "Viewport3D";
        default:                          return "Unknown";
    }
}

#endif // MCRF_HEADLESS
