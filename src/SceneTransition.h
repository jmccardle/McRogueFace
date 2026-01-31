#pragma once
#include "Common.h"
#include <string>
#include <memory>

enum class TransitionType {
    None,
    Fade,
    SlideLeft,
    SlideRight,
    SlideUp,
    SlideDown
};

class SceneTransition {
public:
    TransitionType type = TransitionType::None;
    float duration = 0.0f;
    float elapsed = 0.0f;
    std::string fromScene;
    std::string toScene;
    
    // Render textures for transition
    std::unique_ptr<sf::RenderTexture> oldSceneTexture;
    std::unique_ptr<sf::RenderTexture> newSceneTexture;
    
    // Sprites for rendering textures
    sf::Sprite oldSprite;
    sf::Sprite newSprite;
    
    SceneTransition() = default;
    
    void start(TransitionType t, const std::string& from, const std::string& to, float dur);
    void update(float dt);
    void render(sf::RenderTarget& target);
    bool isComplete() const { return elapsed >= duration; }
    float getProgress() const { return duration > 0 ? std::min(elapsed / duration, 1.0f) : 1.0f; }
    
    // Easing function for smooth transitions
    static float easeInOut(float t);
};