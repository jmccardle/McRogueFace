#include "SceneTransition.h"

void SceneTransition::start(TransitionType t, const std::string& from, const std::string& to, float dur) {
    type = t;
    fromScene = from;
    toScene = to;
    duration = dur;
    elapsed = 0.0f;

    // Initialize render textures if needed
    if (!oldSceneTexture) {
        oldSceneTexture = std::make_unique<sf::RenderTexture>();
        oldSceneTexture->create(width, height);
    }
    if (!newSceneTexture) {
        newSceneTexture = std::make_unique<sf::RenderTexture>();
        newSceneTexture->create(width, height);
    }
}

void SceneTransition::update(float dt) {
    if (type == TransitionType::None) return;
    elapsed += dt;
}

void SceneTransition::render(sf::RenderTarget& target) {
    if (type == TransitionType::None) return;

    float progress = getProgress();
    float easedProgress = easeInOut(progress);

    float w = static_cast<float>(width);
    float h = static_cast<float>(height);

    // Update sprites with current textures
    oldSprite.setTexture(oldSceneTexture->getTexture());
    newSprite.setTexture(newSceneTexture->getTexture());

    switch (type) {
        case TransitionType::Fade:
            // Fade out old scene, fade in new scene
            oldSprite.setColor(sf::Color(255, 255, 255, 255 * (1.0f - easedProgress)));
            newSprite.setColor(sf::Color(255, 255, 255, 255 * easedProgress));
            target.draw(oldSprite);
            target.draw(newSprite);
            break;

        case TransitionType::SlideLeft:
            // Old scene slides out to left, new scene slides in from right
            oldSprite.setPosition(-w * easedProgress, 0);
            newSprite.setPosition(w * (1.0f - easedProgress), 0);
            target.draw(oldSprite);
            target.draw(newSprite);
            break;

        case TransitionType::SlideRight:
            // Old scene slides out to right, new scene slides in from left
            oldSprite.setPosition(w * easedProgress, 0);
            newSprite.setPosition(-w * (1.0f - easedProgress), 0);
            target.draw(oldSprite);
            target.draw(newSprite);
            break;

        case TransitionType::SlideUp:
            // Old scene slides up, new scene slides in from bottom
            oldSprite.setPosition(0, -h * easedProgress);
            newSprite.setPosition(0, h * (1.0f - easedProgress));
            target.draw(oldSprite);
            target.draw(newSprite);
            break;

        case TransitionType::SlideDown:
            // Old scene slides down, new scene slides in from top
            oldSprite.setPosition(0, h * easedProgress);
            newSprite.setPosition(0, -h * (1.0f - easedProgress));
            target.draw(oldSprite);
            target.draw(newSprite);
            break;

        default:
            break;
    }
}

float SceneTransition::easeInOut(float t) {
    // Smooth ease-in-out curve
    return t < 0.5f ? 2 * t * t : -1 + (4 - 2 * t) * t;
}
