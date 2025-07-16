#pragma once

#include <string>
#include <functional>
#include <memory>
#include <variant>
#include <vector>
#include <SFML/Graphics.hpp>
#include "Python.h"

// Forward declarations
class UIDrawable;
class UIEntity;

// Forward declare namespace
namespace EasingFunctions {
    float linear(float t);
}

// Easing function type
typedef std::function<float(float)> EasingFunction;

// Animation target value can be various types
typedef std::variant<
    float,                    // Single float value
    int,                      // Single integer value
    std::vector<int>,         // List of integers (for sprite animation)
    sf::Color,                // Color animation
    sf::Vector2f,             // Vector animation
    std::string               // String animation (for text)
> AnimationValue;

class Animation {
public:
    // Constructor
    Animation(const std::string& targetProperty, 
              const AnimationValue& targetValue,
              float duration,
              EasingFunction easingFunc = EasingFunctions::linear,
              bool delta = false,
              PyObject* callback = nullptr);
    
    // Destructor - cleanup Python callback reference
    ~Animation();
    
    // Apply this animation to a drawable
    void start(std::shared_ptr<UIDrawable> target);
    
    // Apply this animation to an entity (special case since Entity doesn't inherit from UIDrawable)
    void startEntity(std::shared_ptr<UIEntity> target);
    
    // Complete the animation immediately (jump to final value)
    void complete();
    
    // Update animation (called each frame)
    // Returns true if animation is still running, false if complete
    bool update(float deltaTime);
    
    // Get current interpolated value
    AnimationValue getCurrentValue() const;
    
    // Check if animation has valid target
    bool hasValidTarget() const;
    
    // Clear the callback (called when PyAnimation is deallocated)
    void clearCallback();
    
    // Animation properties
    std::string getTargetProperty() const { return targetProperty; }
    float getDuration() const { return duration; }
    float getElapsed() const { return elapsed; }
    bool isComplete() const { return elapsed >= duration; }
    bool isDelta() const { return delta; }
    
private:
    std::string targetProperty;    // Property name to animate (e.g., "x", "color.r", "sprite_number")
    AnimationValue startValue;     // Starting value (captured when animation starts)
    AnimationValue targetValue;    // Target value to animate to
    float duration;                // Animation duration in seconds
    float elapsed = 0.0f;          // Elapsed time
    EasingFunction easingFunc;     // Easing function to use
    bool delta;                    // If true, targetValue is relative to start
    
    // RAII: Use weak_ptr for safe target tracking
    std::weak_ptr<UIDrawable> targetWeak;
    std::weak_ptr<UIEntity> entityTargetWeak;
    
    // Callback support
    PyObject* pythonCallback = nullptr;  // Python callback function (we own a reference)
    bool callbackTriggered = false;      // Ensure callback only fires once
    PyObject* pyAnimationWrapper = nullptr; // Weak reference to PyAnimation if created from Python
    
    // Python object cache support
    uint64_t serial_number = 0;
    
    // Helper to interpolate between values
    AnimationValue interpolate(float t) const;
    
    // Helper to apply value to target
    void applyValue(UIDrawable* target, const AnimationValue& value);
    void applyValue(UIEntity* entity, const AnimationValue& value);
    
    // Trigger callback when animation completes
    void triggerCallback();
};

// Easing functions library
namespace EasingFunctions {
    // Basic easing functions
    float linear(float t);
    float easeIn(float t);
    float easeOut(float t);
    float easeInOut(float t);
    
    // Advanced easing functions
    float easeInQuad(float t);
    float easeOutQuad(float t);
    float easeInOutQuad(float t);
    
    float easeInCubic(float t);
    float easeOutCubic(float t);
    float easeInOutCubic(float t);
    
    float easeInQuart(float t);
    float easeOutQuart(float t);
    float easeInOutQuart(float t);
    
    float easeInSine(float t);
    float easeOutSine(float t);
    float easeInOutSine(float t);
    
    float easeInExpo(float t);
    float easeOutExpo(float t);
    float easeInOutExpo(float t);
    
    float easeInCirc(float t);
    float easeOutCirc(float t);
    float easeInOutCirc(float t);
    
    float easeInElastic(float t);
    float easeOutElastic(float t);
    float easeInOutElastic(float t);
    
    float easeInBack(float t);
    float easeOutBack(float t);
    float easeInOutBack(float t);
    
    float easeInBounce(float t);
    float easeOutBounce(float t);
    float easeInOutBounce(float t);
    
    // Get easing function by name
    EasingFunction getByName(const std::string& name);
}

// Animation manager to handle active animations
class AnimationManager {
public:
    static AnimationManager& getInstance();
    
    // Add an animation to be managed
    void addAnimation(std::shared_ptr<Animation> animation);
    
    // Update all animations
    void update(float deltaTime);
    
    // Clear all animations (optionally completing them first)
    void clear(bool completeAnimations = false);
    
private:
    AnimationManager() = default;
    std::vector<std::shared_ptr<Animation>> activeAnimations;
    std::vector<std::shared_ptr<Animation>> pendingAnimations; // Animations to add after update
    bool isUpdating = false; // Flag to track if we're in update loop
};