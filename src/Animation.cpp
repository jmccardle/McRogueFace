#include "Animation.h"
#include "UIDrawable.h"
#include "UIEntity.h"
#include "3d/Entity3D.h"
#include "PyAnimation.h"
#include "McRFPy_API.h"
#include "GameEngine.h"
#include "PythonObjectCache.h"
// #229 - Includes for animation callback target conversion
#include "UIFrame.h"
#include "UICaption.h"
#include "UISprite.h"
#include "UIGrid.h"
#include "UILine.h"
#include "UICircle.h"
#include "UIArc.h"
#include <cmath>
#include <algorithm>
#include <unordered_map>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

// Forward declaration of PyAnimation type
namespace mcrfpydef {
    extern PyTypeObject PyAnimationType;
}

// Animation implementation
Animation::Animation(const std::string& targetProperty,
                     const AnimationValue& targetValue,
                     float duration,
                     EasingFunction easingFunc,
                     bool delta,
                     bool loop,
                     PyObject* callback)
    : targetProperty(targetProperty)
    , targetValue(targetValue)
    , duration(duration)
    , easingFunc(easingFunc)
    , delta(delta)
    , loop(loop)
    , pythonCallback(callback)
{
    // Increase reference count for Python callback
    if (pythonCallback) {
        Py_INCREF(pythonCallback);
    }
}

Animation::~Animation() {
    // Decrease reference count for Python callback if we still own it
    // Guard with Py_IsInitialized() because destructor may run during interpreter shutdown
    PyObject* callback = pythonCallback;
    if (callback && Py_IsInitialized()) {
        pythonCallback = nullptr;

        PyGILState_STATE gstate = PyGILState_Ensure();
        Py_DECREF(callback);
        PyGILState_Release(gstate);
    }

    // Clean up cache entry (also guard - PythonObjectCache may use Python)
    if (serial_number != 0 && Py_IsInitialized()) {
        PythonObjectCache::getInstance().remove(serial_number);
    }
}

void Animation::start(std::shared_ptr<UIDrawable> target) {
    if (!target) return;

    targetWeak = target;
    elapsed = 0.0f;
    callbackTriggered = false; // Reset callback state

    // Capture start value from target
    std::visit([this, &target](const auto& targetVal) {
        using T = std::decay_t<decltype(targetVal)>;

        if constexpr (std::is_same_v<T, float>) {
            float value;
            if (target->getProperty(targetProperty, value)) {
                startValue = value;
            }
        }
        else if constexpr (std::is_same_v<T, int>) {
            // Most UI properties use float, so try float first, then int
            float fvalue;
            if (target->getProperty(targetProperty, fvalue)) {
                startValue = static_cast<int>(fvalue);
            } else {
                int ivalue;
                if (target->getProperty(targetProperty, ivalue)) {
                    startValue = ivalue;
                }
            }
        }
        else if constexpr (std::is_same_v<T, std::vector<int>>) {
            // For sprite animation, get current sprite index
            int value;
            if (target->getProperty(targetProperty, value)) {
                startValue = value;
            }
        }
        else if constexpr (std::is_same_v<T, sf::Color>) {
            sf::Color value;
            if (target->getProperty(targetProperty, value)) {
                startValue = value;
            }
        }
        else if constexpr (std::is_same_v<T, sf::Vector2f>) {
            sf::Vector2f value;
            if (target->getProperty(targetProperty, value)) {
                startValue = value;
            }
        }
        else if constexpr (std::is_same_v<T, std::string>) {
            std::string value;
            if (target->getProperty(targetProperty, value)) {
                startValue = value;
            }
        }
    }, targetValue);

    // For zero-duration animations, apply final value immediately
    if (duration <= 0.0f) {
        AnimationValue finalValue = interpolate(easingFunc(1.0f));
        applyValue(target.get(), finalValue);
        if (pythonCallback && !callbackTriggered) {
            triggerCallback();
        }
        callbackTriggered = true;
    }
}

void Animation::startEntity(std::shared_ptr<UIEntity> target) {
    if (!target) return;

    entityTargetWeak = target;
    elapsed = 0.0f;
    callbackTriggered = false; // Reset callback state

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
            // For entities, we might need to handle sprite_index differently
            if (targetProperty == "sprite_index" || targetProperty == "sprite_number") {
                startValue = target->sprite.getSpriteIndex();
            }
        }
        else if constexpr (std::is_same_v<T, std::vector<int>>) {
            // For sprite animation frame lists, get current sprite index
            if (targetProperty == "sprite_index" || targetProperty == "sprite_number") {
                startValue = target->sprite.getSpriteIndex();
            }
        }
        // Entities don't support other types yet
    }, targetValue);

    // For zero-duration animations, apply final value immediately
    if (duration <= 0.0f) {
        AnimationValue finalValue = interpolate(easingFunc(1.0f));
        applyValue(target.get(), finalValue);
        if (pythonCallback && !callbackTriggered) {
            triggerCallback();
        }
        callbackTriggered = true;
    }
}

void Animation::startEntity3D(std::shared_ptr<mcrf::Entity3D> target) {
    if (!target) return;

    entity3dTargetWeak = target;
    elapsed = 0.0f;
    callbackTriggered = false;

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
            // For sprite_index/visible: capture via float and convert
            float fvalue = 0.0f;
            if (target->getProperty(targetProperty, fvalue)) {
                startValue = static_cast<int>(fvalue);
            }
        }
        // Entity3D doesn't support other types
    }, targetValue);

    // For zero-duration animations, apply final value immediately
    if (duration <= 0.0f) {
        AnimationValue finalValue = interpolate(easingFunc(1.0f));
        applyValue(target.get(), finalValue);
        if (pythonCallback && !callbackTriggered) {
            triggerCallback();
        }
        callbackTriggered = true;
    }
}

bool Animation::hasValidTarget() const {
    return !targetWeak.expired() || !entityTargetWeak.expired() || !entity3dTargetWeak.expired();
}

void Animation::clearCallback() {
    // Safely clear the callback when PyAnimation is being destroyed
    PyObject* callback = pythonCallback;
    if (callback) {
        pythonCallback = nullptr;
        callbackTriggered = true; // Prevent future triggering
        
        PyGILState_STATE gstate = PyGILState_Ensure();
        Py_DECREF(callback);
        PyGILState_Release(gstate);
    }
}

void Animation::complete() {
    // Jump to end of animation
    elapsed = duration;

    // Apply final value through easing function
    // For standard easings, easingFunc(1.0) = 1.0 (no change)
    // For ping-pong easings, easingFunc(1.0) = 0.0 (returns to start value)
    float finalT = easingFunc(1.0f);
    if (auto target = targetWeak.lock()) {
        AnimationValue finalValue = interpolate(finalT);
        applyValue(target.get(), finalValue);
    }
    else if (auto entity = entityTargetWeak.lock()) {
        AnimationValue finalValue = interpolate(finalT);
        applyValue(entity.get(), finalValue);
    }
    else if (auto entity3d = entity3dTargetWeak.lock()) {
        AnimationValue finalValue = interpolate(finalT);
        applyValue(entity3d.get(), finalValue);
    }
}

void Animation::stop() {
    // Mark as stopped - no final value applied, no callback triggered
    stopped = true;
    // AnimationManager will remove this on next update() call
}

bool Animation::update(float deltaTime) {
    // Check if animation was stopped
    if (stopped) {
        return false;  // Signal removal from AnimationManager
    }

    // Try to lock weak_ptr to get shared_ptr
    std::shared_ptr<UIDrawable> target = targetWeak.lock();
    std::shared_ptr<UIEntity> entity = entityTargetWeak.lock();
    std::shared_ptr<mcrf::Entity3D> entity3d = entity3dTargetWeak.lock();

    // If all are null, target was destroyed
    if (!target && !entity && !entity3d) {
        return false;  // Remove this animation
    }

    // Handle already-complete animations (e.g., duration=0)
    // Apply final value once before returning
    if (isComplete()) {
        if (!callbackTriggered) {
            // Apply final value through easing function
            float finalT = easingFunc(1.0f);
            AnimationValue finalValue = interpolate(finalT);
            if (target) {
                applyValue(target.get(), finalValue);
            } else if (entity) {
                applyValue(entity.get(), finalValue);
            } else if (entity3d) {
                applyValue(entity3d.get(), finalValue);
            }
            // Trigger callback
            if (pythonCallback) {
                triggerCallback();
            }
            callbackTriggered = true;
        }
        return false;
    }

    elapsed += deltaTime;
    if (loop && duration > 0.0f) {
        while (elapsed >= duration) elapsed -= duration;
    } else {
        elapsed = std::min(elapsed, duration);
    }

    // Calculate easing value (0.0 to 1.0)
    float t = duration > 0 ? elapsed / duration : 1.0f;
    float easedT = easingFunc(t);

    // Get interpolated value
    AnimationValue currentValue = interpolate(easedT);

    // Apply to whichever target is valid
    if (target) {
        applyValue(target.get(), currentValue);
    } else if (entity) {
        applyValue(entity.get(), currentValue);
    } else if (entity3d) {
        applyValue(entity3d.get(), currentValue);
    }

    // Trigger callback when animation completes
    // Check pythonCallback again in case it was cleared during update
    if (isComplete() && !callbackTriggered && pythonCallback) {
        triggerCallback();
    }

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

void Animation::applyValue(UIDrawable* target, const AnimationValue& value) {
    if (!target) return;

    std::visit([this, target](const auto& val) {
        using T = std::decay_t<decltype(val)>;

        if constexpr (std::is_same_v<T, float>) {
            target->setProperty(targetProperty, val);
        }
        else if constexpr (std::is_same_v<T, int>) {
            // Most UI properties use float setProperty, so try float first
            if (!target->setProperty(targetProperty, static_cast<float>(val))) {
                // Fall back to int if float didn't work
                target->setProperty(targetProperty, val);
            }
        }
        else if constexpr (std::is_same_v<T, sf::Color>) {
            target->setProperty(targetProperty, val);
        }
        else if constexpr (std::is_same_v<T, sf::Vector2f>) {
            target->setProperty(targetProperty, val);
        }
        else if constexpr (std::is_same_v<T, std::string>) {
            target->setProperty(targetProperty, val);
        }
    }, value);
}

void Animation::applyValue(UIEntity* entity, const AnimationValue& value) {
    if (!entity) return;

    std::visit([this, entity](const auto& val) {
        using T = std::decay_t<decltype(val)>;

        if constexpr (std::is_same_v<T, float>) {
            entity->setProperty(targetProperty, val);
        }
        else if constexpr (std::is_same_v<T, int>) {
            entity->setProperty(targetProperty, val);
        }
        // Entities don't support other types yet
    }, value);
}

void Animation::applyValue(mcrf::Entity3D* entity, const AnimationValue& value) {
    if (!entity) return;

    std::visit([this, entity](const auto& val) {
        using T = std::decay_t<decltype(val)>;

        if constexpr (std::is_same_v<T, float>) {
            entity->setProperty(targetProperty, val);
        }
        else if constexpr (std::is_same_v<T, int>) {
            entity->setProperty(targetProperty, val);
        }
        // Entity3D doesn't support other types
    }, value);
}

// #229 - Helper to convert UIDrawable target to Python object
static PyObject* convertDrawableToPython(std::shared_ptr<UIDrawable> drawable) {
    if (!drawable) {
        Py_RETURN_NONE;
    }

    // Check cache first
    if (drawable->serial_number != 0) {
        PyObject* cached = PythonObjectCache::getInstance().lookup(drawable->serial_number);
        if (cached) {
            return cached;  // Already INCREF'd by lookup
        }
    }

    PyTypeObject* type = nullptr;
    PyObject* obj = nullptr;

    switch (drawable->derived_type()) {
        case PyObjectsEnum::UIFRAME:
        {
            type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Frame");
            if (!type) return nullptr;
            auto pyObj = (PyUIFrameObject*)type->tp_alloc(type, 0);
            if (pyObj) {
                pyObj->data = std::static_pointer_cast<UIFrame>(drawable);
                pyObj->weakreflist = NULL;
            }
            obj = (PyObject*)pyObj;
            break;
        }
        case PyObjectsEnum::UICAPTION:
        {
            type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Caption");
            if (!type) return nullptr;
            auto pyObj = (PyUICaptionObject*)type->tp_alloc(type, 0);
            if (pyObj) {
                pyObj->data = std::static_pointer_cast<UICaption>(drawable);
                pyObj->font = nullptr;
                pyObj->weakreflist = NULL;
            }
            obj = (PyObject*)pyObj;
            break;
        }
        case PyObjectsEnum::UISPRITE:
        {
            type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Sprite");
            if (!type) return nullptr;
            auto pyObj = (PyUISpriteObject*)type->tp_alloc(type, 0);
            if (pyObj) {
                pyObj->data = std::static_pointer_cast<UISprite>(drawable);
                pyObj->weakreflist = NULL;
            }
            obj = (PyObject*)pyObj;
            break;
        }
        case PyObjectsEnum::UIGRID:
        {
            type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Grid");
            if (!type) return nullptr;
            auto pyObj = (PyUIGridObject*)type->tp_alloc(type, 0);
            if (pyObj) {
                pyObj->data = std::static_pointer_cast<UIGrid>(drawable);
                pyObj->weakreflist = NULL;
            }
            obj = (PyObject*)pyObj;
            break;
        }
        case PyObjectsEnum::UILINE:
        {
            type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Line");
            if (!type) return nullptr;
            auto pyObj = (PyUILineObject*)type->tp_alloc(type, 0);
            if (pyObj) {
                pyObj->data = std::static_pointer_cast<UILine>(drawable);
                pyObj->weakreflist = NULL;
            }
            obj = (PyObject*)pyObj;
            break;
        }
        case PyObjectsEnum::UICIRCLE:
        {
            type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Circle");
            if (!type) return nullptr;
            auto pyObj = (PyUICircleObject*)type->tp_alloc(type, 0);
            if (pyObj) {
                pyObj->data = std::static_pointer_cast<UICircle>(drawable);
                pyObj->weakreflist = NULL;
            }
            obj = (PyObject*)pyObj;
            break;
        }
        case PyObjectsEnum::UIARC:
        {
            type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Arc");
            if (!type) return nullptr;
            auto pyObj = (PyUIArcObject*)type->tp_alloc(type, 0);
            if (pyObj) {
                pyObj->data = std::static_pointer_cast<UIArc>(drawable);
                pyObj->weakreflist = NULL;
            }
            obj = (PyObject*)pyObj;
            break;
        }
        default:
            Py_RETURN_NONE;
    }

    if (type) {
        Py_DECREF(type);
    }

    return obj ? obj : Py_None;
}

// #229 - Helper to convert UIEntity target to Python object
static PyObject* convertEntityToPython(std::shared_ptr<UIEntity> entity) {
    if (!entity) {
        Py_RETURN_NONE;
    }

    // Check cache first
    if (entity->serial_number != 0) {
        PyObject* cached = PythonObjectCache::getInstance().lookup(entity->serial_number);
        if (cached) {
            return cached;  // Already INCREF'd by lookup
        }
    }

    PyTypeObject* type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity");
    if (!type) {
        Py_RETURN_NONE;
    }

    auto pyObj = (PyUIEntityObject*)type->tp_alloc(type, 0);
    Py_DECREF(type);

    if (!pyObj) {
        Py_RETURN_NONE;
    }

    pyObj->data = entity;
    pyObj->weakreflist = NULL;

    return (PyObject*)pyObj;
}

// Helper to convert Entity3D target to Python object
static PyObject* convertEntity3DToPython(std::shared_ptr<mcrf::Entity3D> entity) {
    if (!entity) {
        Py_RETURN_NONE;
    }

    // Use the entity's cached Python self pointer if available
    if (entity->self) {
        Py_INCREF(entity->self);
        return entity->self;
    }

    // Create a new wrapper
    PyTypeObject* type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity3D");
    if (!type) {
        Py_RETURN_NONE;
    }

    auto pyObj = (PyEntity3DObject*)type->tp_alloc(type, 0);
    Py_DECREF(type);

    if (!pyObj) {
        Py_RETURN_NONE;
    }

    pyObj->data = entity;
    pyObj->weakreflist = NULL;

    return (PyObject*)pyObj;
}

// #229 - Helper to convert AnimationValue to Python object
static PyObject* animationValueToPython(const AnimationValue& value) {
    return std::visit([](const auto& val) -> PyObject* {
        using T = std::decay_t<decltype(val)>;

        if constexpr (std::is_same_v<T, float>) {
            return PyFloat_FromDouble(val);
        }
        else if constexpr (std::is_same_v<T, int>) {
            return PyLong_FromLong(val);
        }
        else if constexpr (std::is_same_v<T, std::vector<int>>) {
            // Sprite frame list - return current frame as int
            // (the interpolate function returns the current frame)
            if (!val.empty()) {
                return PyLong_FromLong(val.back());
            }
            return PyLong_FromLong(0);
        }
        else if constexpr (std::is_same_v<T, sf::Color>) {
            return Py_BuildValue("(iiii)", val.r, val.g, val.b, val.a);
        }
        else if constexpr (std::is_same_v<T, sf::Vector2f>) {
            return Py_BuildValue("(ff)", val.x, val.y);
        }
        else if constexpr (std::is_same_v<T, std::string>) {
            return PyUnicode_FromString(val.c_str());
        }

        Py_RETURN_NONE;
    }, value);
}

void Animation::triggerCallback() {
    if (!pythonCallback) return;

    // Ensure we only trigger once
    if (callbackTriggered) return;
    callbackTriggered = true;

    PyGILState_STATE gstate = PyGILState_Ensure();

    // #229 - Pass (target, property, final_value) instead of (None, None)
    // Convert target to Python object
    PyObject* targetObj = nullptr;
    if (auto drawable = targetWeak.lock()) {
        targetObj = convertDrawableToPython(drawable);
    } else if (auto entity = entityTargetWeak.lock()) {
        targetObj = convertEntityToPython(entity);
    } else if (auto entity3d = entity3dTargetWeak.lock()) {
        targetObj = convertEntity3DToPython(entity3d);
    }

    // If target conversion failed, use None
    if (!targetObj) {
        targetObj = Py_None;
        Py_INCREF(targetObj);
    }

    // Property name
    PyObject* propertyObj = PyUnicode_FromString(targetProperty.c_str());
    if (!propertyObj) {
        Py_DECREF(targetObj);
        PyGILState_Release(gstate);
        return;
    }

    // Final value (interpolated through easing function at t=1.0)
    // For ping-pong easings, this returns the start value (easingFunc(1.0) = 0.0)
    PyObject* valueObj = animationValueToPython(interpolate(easingFunc(1.0f)));
    if (!valueObj) {
        Py_DECREF(targetObj);
        Py_DECREF(propertyObj);
        PyGILState_Release(gstate);
        return;
    }

    PyObject* args = Py_BuildValue("(OOO)", targetObj, propertyObj, valueObj);
    Py_DECREF(targetObj);
    Py_DECREF(propertyObj);
    Py_DECREF(valueObj);

    if (!args) {
        PyGILState_Release(gstate);
        return;
    }

    PyObject* result = PyObject_CallObject(pythonCallback, args);
    Py_DECREF(args);

    if (!result) {
        std::cerr << "Animation callback raised an exception:" << std::endl;
        PyErr_Print();
        PyErr_Clear();

        // Check if we should exit on exception
        if (McRFPy_API::game && McRFPy_API::game->getConfig().exit_on_exception) {
            McRFPy_API::signalPythonException();
        }
    } else {
        Py_DECREF(result);
    }

    PyGILState_Release(gstate);
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

// Ping-pong easing functions (0 -> 1 -> 0)
// These are designed for looping animations where the value should
// smoothly return to the start position each cycle.

float pingPong(float t) {
    // Linear triangle wave: 0 -> 1 -> 0
    return 1.0f - std::fabs(2.0f * t - 1.0f);
}

float pingPongSmooth(float t) {
    // Sine bell curve: smooth acceleration and deceleration
    return std::sin(static_cast<float>(M_PI) * t);
}

float pingPongEaseIn(float t) {
    // Quadratic ease at rest positions (smooth departure/return, sharp peak)
    float pp = 1.0f - std::fabs(2.0f * t - 1.0f);
    return pp * pp;
}

float pingPongEaseOut(float t) {
    // Ease-out at peak (sharp departure, smooth turnaround)
    float pp = 1.0f - std::fabs(2.0f * t - 1.0f);
    return pp * (2.0f - pp);
}

float pingPongEaseInOut(float t) {
    // sin^2: smooth everywhere including at loop seam
    float s = std::sin(static_cast<float>(M_PI) * t);
    return s * s;
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
        {"easeInOutBounce", easeInOutBounce},
        {"pingPong", pingPong},
        {"pingPongSmooth", pingPongSmooth},
        {"pingPongEaseIn", pingPongEaseIn},
        {"pingPongEaseOut", pingPongEaseOut},
        {"pingPongEaseInOut", pingPongEaseInOut}
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

void* AnimationManager::getAnimationTarget(const std::shared_ptr<Animation>& anim) const {
    return anim ? anim->getTargetPtr() : nullptr;
}

bool AnimationManager::isPropertyAnimating(void* target, const std::string& property) const {
    if (!target) return false;
    PropertyKey key{target, property};
    auto it = propertyLocks.find(key);
    if (it == propertyLocks.end()) return false;
    // Check if the animation is still valid
    return !it->second.expired();
}

void AnimationManager::cleanupPropertyLocks() {
    // Remove expired locks
    for (auto it = propertyLocks.begin(); it != propertyLocks.end(); ) {
        if (it->second.expired()) {
            it = propertyLocks.erase(it);
        } else {
            ++it;
        }
    }
}

void AnimationManager::processQueue() {
    // Try to start queued animations whose properties are now free
    for (auto it = animationQueue.begin(); it != animationQueue.end(); ) {
        const auto& key = it->first;
        auto& anim = it->second;

        // Check if property is now free
        auto lockIt = propertyLocks.find(key);
        bool propertyFree = (lockIt == propertyLocks.end()) || lockIt->second.expired();

        if (propertyFree && anim && anim->hasValidTarget()) {
            // Property is free, start the animation
            propertyLocks[key] = anim;
            activeAnimations.push_back(anim);
            it = animationQueue.erase(it);
        } else if (!anim || !anim->hasValidTarget()) {
            // Animation target was destroyed, remove from queue
            it = animationQueue.erase(it);
        } else {
            ++it;
        }
    }
}

void AnimationManager::addAnimation(std::shared_ptr<Animation> animation,
                                    AnimationConflictMode conflict_mode) {
    if (!animation || !animation->hasValidTarget()) {
        return;
    }

    void* target = getAnimationTarget(animation);
    std::string property = animation->getTargetProperty();
    PropertyKey key{target, property};

    // Check for existing animation on this property (#120)
    auto existingIt = propertyLocks.find(key);
    bool hasExisting = (existingIt != propertyLocks.end()) && !existingIt->second.expired();

    if (hasExisting) {
        auto existingAnim = existingIt->second.lock();

        switch (conflict_mode) {
            case AnimationConflictMode::REPLACE:
                if (existingAnim) {
                    if (isUpdating) {
                        // During update, just stop the animation without completing
                        // to avoid recursive callback issues and iterator invalidation.
                        // The update loop will clean up stopped animations.
                        existingAnim->stop();
                    } else {
                        // Outside update loop, complete the animation (jump to final value)
                        // and remove it safely
                        existingAnim->complete();
                        activeAnimations.erase(
                            std::remove(activeAnimations.begin(), activeAnimations.end(), existingAnim),
                            activeAnimations.end()
                        );
                    }
                }
                // Fall through to add the new animation
                break;

            case AnimationConflictMode::QUEUE:
                // Add to queue - will start when existing completes
                if (isUpdating) {
                    // Also defer queue additions during update
                    pendingAnimations.push_back(animation);
                } else {
                    animationQueue.emplace_back(key, animation);
                }
                return;  // Don't add to active animations yet

            case AnimationConflictMode::RAISE_ERROR:
                // Raise Python exception
                PyGILState_STATE gstate = PyGILState_Ensure();
                PyErr_Format(PyExc_RuntimeError,
                    "Animation conflict: property '%s' is already being animated on this target. "
                    "Use conflict_mode='replace' to override or 'queue' to wait.",
                    property.c_str());
                PyGILState_Release(gstate);
                return;
        }
    }

    // Register property lock and add animation
    propertyLocks[key] = animation;

    if (isUpdating) {
        // Defer adding during update to avoid iterator invalidation
        pendingAnimations.push_back(animation);
    } else {
        activeAnimations.push_back(animation);
    }
}

void AnimationManager::update(float deltaTime) {
    // Set flag to defer new animations
    isUpdating = true;

    // Remove completed or invalid animations
    activeAnimations.erase(
        std::remove_if(activeAnimations.begin(), activeAnimations.end(),
            [deltaTime](std::shared_ptr<Animation>& anim) {
                return !anim || !anim->update(deltaTime);
            }),
        activeAnimations.end()
    );

    // Clear update flag
    isUpdating = false;

    // Clean up expired property locks (#120)
    cleanupPropertyLocks();

    // Process queued animations - start any that are now unblocked (#120)
    processQueue();

    // Add any animations that were created during update
    if (!pendingAnimations.empty()) {
        for (auto& anim : pendingAnimations) {
            if (anim && anim->hasValidTarget()) {
                void* target = getAnimationTarget(anim);
                std::string property = anim->getTargetProperty();
                PropertyKey key{target, property};

                // Check if this animation is already the property lock holder
                // (this happens when addAnimation was called during update)
                auto lockIt = propertyLocks.find(key);
                bool isLockHolder = (lockIt != propertyLocks.end()) &&
                                   (lockIt->second.lock() == anim);
                bool propertyFree = (lockIt == propertyLocks.end()) ||
                                   lockIt->second.expired();

                if (isLockHolder || propertyFree) {
                    // This animation owns the lock or property is free - add it
                    propertyLocks[key] = anim;
                    activeAnimations.push_back(anim);
                } else {
                    // Property still locked by another animation, re-queue
                    animationQueue.emplace_back(key, anim);
                }
            }
        }
        pendingAnimations.clear();
    }
}


void AnimationManager::clear(bool completeAnimations) {
    if (completeAnimations) {
        // Complete all animations before clearing
        for (auto& anim : activeAnimations) {
            if (anim) {
                anim->complete();
            }
        }
    }
    activeAnimations.clear();
    pendingAnimations.clear();
    animationQueue.clear();
    propertyLocks.clear();
}