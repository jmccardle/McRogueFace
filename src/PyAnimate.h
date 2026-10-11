#pragma once
// #423, #426: the one front end for every animate() method.
//
// Rule: every name animate() accepts is a readable attribute of the object, animated in
// that attribute's units and type. The property's type is read from the object itself
// (which getProperty() overload answers for the name), and the target is converted the
// way assigning that attribute converts it: a Vector property takes a Vector, tuple or
// list, a Color property takes a Color, tuple, list or int, and so on.

#include "Common.h"
#include "Python.h"
#include "Animation.h"
#include <memory>
#include <string>

namespace mcrf {

enum class AnimKind { None, Float, Int, Vector, Color, String };

// The type of an animatable property, or None when the object doesn't animate `name`.
// Target needs hasProperty() and the five getProperty() overloads.
template <class Target>
AnimKind animation_kind(const Target& t, const std::string& name)
{
    if (!t.hasProperty(name)) return AnimKind::None;
    // Shader uniforms are floats that exist once first set.
    if (name.compare(0, 7, "shader.") == 0) return AnimKind::Float;
    float f; int i; sf::Vector2f v; sf::Color c; std::string s;
    if (t.getProperty(name, f)) return AnimKind::Float;
    if (t.getProperty(name, i)) return AnimKind::Int;
    if (t.getProperty(name, v)) return AnimKind::Vector;
    if (t.getProperty(name, c)) return AnimKind::Color;
    if (t.getProperty(name, s)) return AnimKind::String;
    return AnimKind::None;
}

struct AnimateArgs {
    const char* property = nullptr;
    PyObject* target = nullptr;   // borrowed
    float duration = 0.0f;
    EasingFunction easing;
    bool delta = false;
    bool loop = false;
    PyObject* callback = nullptr; // borrowed; nullptr for None
    AnimationConflictMode conflict = AnimationConflictMode::REPLACE;
};

// Parses animate(property, target, duration, easing=None, delta=False, loop=False,
// callback=None, conflict_mode='replace'). Sets a Python error and returns false on failure.
bool parse_animate_args(PyObject* args, PyObject* kwds, AnimateArgs& out);

// Converts `value` to a target for a property of type `kind`. Raises TypeError naming
// the property and the type it takes.
bool animation_target(PyObject* value, AnimKind kind, const char* property, AnimationValue& out);

// ValueError: `property` is not an animatable property of `type_name`, with a pointer to
// the replacement for names that animate() used to accept.
void raise_not_animatable(const char* type_name, const char* property);

// Adds a started animation to the manager and returns its Python wrapper.
PyObject* launch_animation(const std::shared_ptr<Animation>& animation, AnimationConflictMode conflict);

// The shared body of every animate(): parse, type the target from the property, build the
// Animation, `start(animation, target)` it and launch it.
template <class Target, class Start>
PyObject* animate(const std::shared_ptr<Target>& target, const char* type_name,
                  PyObject* args, PyObject* kwds, Start start)
{
    AnimateArgs a;
    if (!parse_animate_args(args, kwds, a)) return nullptr;
    const AnimKind kind = animation_kind(*target, a.property);
    if (kind == AnimKind::None) {
        raise_not_animatable(type_name, a.property);
        return nullptr;
    }
    AnimationValue value;
    if (!animation_target(a.target, kind, a.property, value)) return nullptr;
    auto animation = std::make_shared<Animation>(a.property, value, a.duration, a.easing,
                                                 a.delta, a.loop, a.callback);
    start(*animation, target);
    return launch_animation(animation, a.conflict);
}

} // namespace mcrf
