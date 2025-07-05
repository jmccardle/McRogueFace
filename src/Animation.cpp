#include "Animation.h"
#include "UIDrawable.h"
#include "UIEntity.h"
#include <cmath>
#include <algorithm>
#include <unordered_map>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

// Animation implementation
Animation::Animation(const std::string& targetProperty, 
                     const AnimationValue& targetValue,
                     float duration,
                     EasingFunction easingFunc,
                     bool delta)
    : targetProperty(targetProperty)
    , targetValue(targetValue)
    , duration(duration)
    , easingFunc(easingFunc)
    , delta(delta)
{
}

void Animation::start(UIDrawable* target) {
    currentTarget = target;
    elapsed = 0.0f;
    
    // Capture startValue from target based on targetProperty
    if (!currentTarget) return;
    
    // Try to get the current value based on the expected type
    std::visit([this](const auto& targetVal) {
        using T = std::decay_t<decltype(targetVal)>;
        
        if constexpr (std::is_same_v<T, float>) {
            float value;
            if (currentTarget->getProperty(targetProperty, value)) {
                startValue = value;
            }
        }
        else if constexpr (std::is_same_v<T, int>) {
            int value;
            if (currentTarget->getProperty(targetProperty, value)) {
                startValue = value;
            }
        }
        else if constexpr (std::is_same_v<T, std::vector<int>>) {
            // For sprite animation, get current sprite index
            int value;
            if (currentTarget->getProperty(targetProperty, value)) {
                startValue = value;
            }
        }
        else if constexpr (std::is_same_v<T, sf::Color>) {
            sf::Color value;
            if (currentTarget->getProperty(targetProperty, value)) {
                startValue = value;
            }
        }
        else if constexpr (std::is_same_v<T, sf::Vector2f>) {
            sf::Vector2f value;
            if (currentTarget->getProperty(targetProperty, value)) {
                startValue = value;
            }
        }
        else if constexpr (std::is_same_v<T, std::string>) {
            std::string value;
            if (currentTarget->getProperty(targetProperty, value)) {
                startValue = value;
            }
        }
    }, targetValue);
}

void Animation::startEntity(UIEntity* target) {
    currentEntityTarget = target;
    currentTarget = nullptr;  // Clear drawable target
    elapsed = 0.0f;
    
    // Capture the starting value from the entity
    std::visit([this, target](const auto& val) {
        using T = std::decay_t<decltype(val)>;
        
        if constexpr (std::is_same_v<T, float>) {
            float value = 0.0f;
            if (target->getProperty(targetProperty, value)) {
                startValue = value;
            }
        }
        else if constexpr (std::is_same_v<T, int>) {
            // For entities, we might need to handle sprite_number differently
            if (targetProperty == "sprite_number") {
                startValue = target->sprite.getSpriteIndex();
            }
        }
        // Entities don't support other types yet
    }, targetValue);
}

bool Animation::update(float deltaTime) {
    if ((!currentTarget && !currentEntityTarget) || isComplete()) {
        return false;
    }
    
    elapsed += deltaTime;
    elapsed = std::min(elapsed, duration);
    
    // Calculate easing value (0.0 to 1.0)
    float t = duration > 0 ? elapsed / duration : 1.0f;
    float easedT = easingFunc(t);
    
    // Get interpolated value
    AnimationValue currentValue = interpolate(easedT);
    
    // Apply currentValue to target (either drawable or entity)
    std::visit([this](const auto& value) {
        using T = std::decay_t<decltype(value)>;
        
        if (currentTarget) {
            // Handle UIDrawable targets
            if constexpr (std::is_same_v<T, float>) {
                currentTarget->setProperty(targetProperty, value);
            }
            else if constexpr (std::is_same_v<T, int>) {
                currentTarget->setProperty(targetProperty, value);
            }
            else if constexpr (std::is_same_v<T, sf::Color>) {
                currentTarget->setProperty(targetProperty, value);
            }
            else if constexpr (std::is_same_v<T, sf::Vector2f>) {
                currentTarget->setProperty(targetProperty, value);
            }
            else if constexpr (std::is_same_v<T, std::string>) {
                currentTarget->setProperty(targetProperty, value);
            }
        }
        else if (currentEntityTarget) {
            // Handle UIEntity targets
            if constexpr (std::is_same_v<T, float>) {
                currentEntityTarget->setProperty(targetProperty, value);
            }
            else if constexpr (std::is_same_v<T, int>) {
                currentEntityTarget->setProperty(targetProperty, value);
            }
            // Entities don't support other types yet
        }
    }, currentValue);
    
    return !isComplete();
}

AnimationValue Animation::getCurrentValue() const {
    float t = duration > 0 ? elapsed / duration : 1.0f;
    float easedT = easingFunc(t);
    return interpolate(easedT);
}

AnimationValue Animation::interpolate(float t) const {
    // Visit the variant to perform type-specific interpolation
    return std::visit([this, t](const auto& target) -> AnimationValue {
        using T = std::decay_t<decltype(target)>;
        
        if constexpr (std::is_same_v<T, float>) {
            // Interpolate float
            const float* start = std::get_if<float>(&startValue);
            if (!start) return target;  // Type mismatch
            
            if (delta) {
                return *start + target * t;
            } else {
                return *start + (target - *start) * t;
            }
        }
        else if constexpr (std::is_same_v<T, int>) {
            // Interpolate integer
            const int* start = std::get_if<int>(&startValue);
            if (!start) return target;
            
            float result;
            if (delta) {
                result = *start + target * t;
            } else {
                result = *start + (target - *start) * t;
            }
            return static_cast<int>(std::round(result));
        }
        else if constexpr (std::is_same_v<T, std::vector<int>>) {
            // For sprite animation, interpolate through the list
            if (target.empty()) return target;
            
            // Map t to an index in the vector
            size_t index = static_cast<size_t>(t * (target.size() - 1));
            index = std::min(index, target.size() - 1);
            return static_cast<int>(target[index]);
        }
        else if constexpr (std::is_same_v<T, sf::Color>) {
            // Interpolate color
            const sf::Color* start = std::get_if<sf::Color>(&startValue);
            if (!start) return target;
            
            sf::Color result;
            if (delta) {
                result.r = std::clamp(start->r + target.r * t, 0.0f, 255.0f);
                result.g = std::clamp(start->g + target.g * t, 0.0f, 255.0f);
                result.b = std::clamp(start->b + target.b * t, 0.0f, 255.0f);
                result.a = std::clamp(start->a + target.a * t, 0.0f, 255.0f);
            } else {
                result.r = start->r + (target.r - start->r) * t;
                result.g = start->g + (target.g - start->g) * t;
                result.b = start->b + (target.b - start->b) * t;
                result.a = start->a + (target.a - start->a) * t;
            }
            return result;
        }
        else if constexpr (std::is_same_v<T, sf::Vector2f>) {
            // Interpolate vector
            const sf::Vector2f* start = std::get_if<sf::Vector2f>(&startValue);
            if (!start) return target;
            
            if (delta) {
                return sf::Vector2f(start->x + target.x * t, 
                                    start->y + target.y * t);
            } else {
                return sf::Vector2f(start->x + (target.x - start->x) * t,
                                    start->y + (target.y - start->y) * t);
            }
        }
        else if constexpr (std::is_same_v<T, std::string>) {
            // For text, show characters based on t
            const std::string* start = std::get_if<std::string>(&startValue);
            if (!start) return target;
            
            // If delta mode, append characters from target
            if (delta) {
                size_t chars = static_cast<size_t>(target.length() * t);
                return *start + target.substr(0, chars);
            } else {
                // Transition from start text to target text
                if (t < 0.5f) {
                    // First half: remove characters from start
                    size_t chars = static_cast<size_t>(start->length() * (1.0f - t * 2.0f));
                    return start->substr(0, chars);
                } else {
                    // Second half: add characters to target
                    size_t chars = static_cast<size_t>(target.length() * ((t - 0.5f) * 2.0f));
                    return target.substr(0, chars);
                }
            }
        }
        
        return target;  // Fallback
    }, targetValue);
}

// Easing functions implementation
namespace EasingFunctions {

float linear(float t) {
    return t;
}

float easeIn(float t) {
    return t * t;
}

float easeOut(float t) {
    return t * (2.0f - t);
}

float easeInOut(float t) {
    return t < 0.5f ? 2.0f * t * t : -1.0f + (4.0f - 2.0f * t) * t;
}

// Quadratic
float easeInQuad(float t) {
    return t * t;
}

float easeOutQuad(float t) {
    return t * (2.0f - t);
}

float easeInOutQuad(float t) {
    return t < 0.5f ? 2.0f * t * t : -1.0f + (4.0f - 2.0f * t) * t;
}

// Cubic
float easeInCubic(float t) {
    return t * t * t;
}

float easeOutCubic(float t) {
    float t1 = t - 1.0f;
    return t1 * t1 * t1 + 1.0f;
}

float easeInOutCubic(float t) {
    return t < 0.5f ? 4.0f * t * t * t : (t - 1.0f) * (2.0f * t - 2.0f) * (2.0f * t - 2.0f) + 1.0f;
}

// Quartic
float easeInQuart(float t) {
    return t * t * t * t;
}

float easeOutQuart(float t) {
    float t1 = t - 1.0f;
    return 1.0f - t1 * t1 * t1 * t1;
}

float easeInOutQuart(float t) {
    return t < 0.5f ? 8.0f * t * t * t * t : 1.0f - 8.0f * (t - 1.0f) * (t - 1.0f) * (t - 1.0f) * (t - 1.0f);
}

// Sine
float easeInSine(float t) {
    return 1.0f - std::cos(t * M_PI / 2.0f);
}

float easeOutSine(float t) {
    return std::sin(t * M_PI / 2.0f);
}

float easeInOutSine(float t) {
    return 0.5f * (1.0f - std::cos(M_PI * t));
}

// Exponential
float easeInExpo(float t) {
    return t == 0.0f ? 0.0f : std::pow(2.0f, 10.0f * (t - 1.0f));
}

float easeOutExpo(float t) {
    return t == 1.0f ? 1.0f : 1.0f - std::pow(2.0f, -10.0f * t);
}

float easeInOutExpo(float t) {
    if (t == 0.0f) return 0.0f;
    if (t == 1.0f) return 1.0f;
    if (t < 0.5f) {
        return 0.5f * std::pow(2.0f, 20.0f * t - 10.0f);
    } else {
        return 1.0f - 0.5f * std::pow(2.0f, -20.0f * t + 10.0f);
    }
}

// Circular
float easeInCirc(float t) {
    return 1.0f - std::sqrt(1.0f - t * t);
}

float easeOutCirc(float t) {
    float t1 = t - 1.0f;
    return std::sqrt(1.0f - t1 * t1);
}

float easeInOutCirc(float t) {
    if (t < 0.5f) {
        return 0.5f * (1.0f - std::sqrt(1.0f - 4.0f * t * t));
    } else {
        return 0.5f * (std::sqrt(1.0f - (2.0f * t - 2.0f) * (2.0f * t - 2.0f)) + 1.0f);
    }
}

// Elastic
float easeInElastic(float t) {
    if (t == 0.0f) return 0.0f;
    if (t == 1.0f) return 1.0f;
    float p = 0.3f;
    float a = 1.0f;
    float s = p / 4.0f;
    float t1 = t - 1.0f;
    return -(a * std::pow(2.0f, 10.0f * t1) * std::sin((t1 - s) * (2.0f * M_PI) / p));
}

float easeOutElastic(float t) {
    if (t == 0.0f) return 0.0f;
    if (t == 1.0f) return 1.0f;
    float p = 0.3f;
    float a = 1.0f;
    float s = p / 4.0f;
    return a * std::pow(2.0f, -10.0f * t) * std::sin((t - s) * (2.0f * M_PI) / p) + 1.0f;
}

float easeInOutElastic(float t) {
    if (t == 0.0f) return 0.0f;
    if (t == 1.0f) return 1.0f;
    float p = 0.45f;
    float a = 1.0f;
    float s = p / 4.0f;
    
    if (t < 0.5f) {
        float t1 = 2.0f * t - 1.0f;
        return -0.5f * (a * std::pow(2.0f, 10.0f * t1) * std::sin((t1 - s) * (2.0f * M_PI) / p));
    } else {
        float t1 = 2.0f * t - 1.0f;
        return a * std::pow(2.0f, -10.0f * t1) * std::sin((t1 - s) * (2.0f * M_PI) / p) * 0.5f + 1.0f;
    }
}

// Back (overshooting)
float easeInBack(float t) {
    const float s = 1.70158f;
    return t * t * ((s + 1.0f) * t - s);
}

float easeOutBack(float t) {
    const float s = 1.70158f;
    float t1 = t - 1.0f;
    return t1 * t1 * ((s + 1.0f) * t1 + s) + 1.0f;
}

float easeInOutBack(float t) {
    const float s = 1.70158f * 1.525f;
    if (t < 0.5f) {
        return 0.5f * (4.0f * t * t * ((s + 1.0f) * 2.0f * t - s));
    } else {
        float t1 = 2.0f * t - 2.0f;
        return 0.5f * (t1 * t1 * ((s + 1.0f) * t1 + s) + 2.0f);
    }
}

// Bounce
float easeOutBounce(float t) {
    if (t < 1.0f / 2.75f) {
        return 7.5625f * t * t;
    } else if (t < 2.0f / 2.75f) {
        float t1 = t - 1.5f / 2.75f;
        return 7.5625f * t1 * t1 + 0.75f;
    } else if (t < 2.5f / 2.75f) {
        float t1 = t - 2.25f / 2.75f;
        return 7.5625f * t1 * t1 + 0.9375f;
    } else {
        float t1 = t - 2.625f / 2.75f;
        return 7.5625f * t1 * t1 + 0.984375f;
    }
}

float easeInBounce(float t) {
    return 1.0f - easeOutBounce(1.0f - t);
}

float easeInOutBounce(float t) {
    if (t < 0.5f) {
        return 0.5f * easeInBounce(2.0f * t);
    } else {
        return 0.5f * easeOutBounce(2.0f * t - 1.0f) + 0.5f;
    }
}

// Get easing function by name
EasingFunction getByName(const std::string& name) {
    static std::unordered_map<std::string, EasingFunction> easingMap = {
        {"linear", linear},
        {"easeIn", easeIn},
        {"easeOut", easeOut},
        {"easeInOut", easeInOut},
        {"easeInQuad", easeInQuad},
        {"easeOutQuad", easeOutQuad},
        {"easeInOutQuad", easeInOutQuad},
        {"easeInCubic", easeInCubic},
        {"easeOutCubic", easeOutCubic},
        {"easeInOutCubic", easeInOutCubic},
        {"easeInQuart", easeInQuart},
        {"easeOutQuart", easeOutQuart},
        {"easeInOutQuart", easeInOutQuart},
        {"easeInSine", easeInSine},
        {"easeOutSine", easeOutSine},
        {"easeInOutSine", easeInOutSine},
        {"easeInExpo", easeInExpo},
        {"easeOutExpo", easeOutExpo},
        {"easeInOutExpo", easeInOutExpo},
        {"easeInCirc", easeInCirc},
        {"easeOutCirc", easeOutCirc},
        {"easeInOutCirc", easeInOutCirc},
        {"easeInElastic", easeInElastic},
        {"easeOutElastic", easeOutElastic},
        {"easeInOutElastic", easeInOutElastic},
        {"easeInBack", easeInBack},
        {"easeOutBack", easeOutBack},
        {"easeInOutBack", easeInOutBack},
        {"easeInBounce", easeInBounce},
        {"easeOutBounce", easeOutBounce},
        {"easeInOutBounce", easeInOutBounce}
    };
    
    auto it = easingMap.find(name);
    if (it != easingMap.end()) {
        return it->second;
    }
    return linear;  // Default to linear
}

} // namespace EasingFunctions

// AnimationManager implementation
AnimationManager& AnimationManager::getInstance() {
    static AnimationManager instance;
    return instance;
}

void AnimationManager::addAnimation(std::shared_ptr<Animation> animation) {
    activeAnimations.push_back(animation);
}

void AnimationManager::update(float deltaTime) {
    for (auto& anim : activeAnimations) {
        anim->update(deltaTime);
    }
    cleanup();
}

void AnimationManager::cleanup() {
    activeAnimations.erase(
        std::remove_if(activeAnimations.begin(), activeAnimations.end(),
            [](const std::shared_ptr<Animation>& anim) {
                return anim->isComplete();
            }),
        activeAnimations.end()
    );
}

void AnimationManager::clear() {
    activeAnimations.clear();
}