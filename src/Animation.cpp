#include "Animation.h"

Animation::Animation(float _d, void* _t, std::function<void()> _cb, bool _l)
:duration(_d), target(_t), callback(_cb), loop(_l), elapsed(0.0f) {}

// linear interpolation constructor
template<typename T>
LerpAnimation<T>::LerpAnimation(float _d, T _ev, T* _t, std::function<void()> _cb, bool _l)
:Animation(_d, _t, _cb, _l), //duration(_d), target(_t), callback(_cb), loop(_l),elapsed(0.0f),
startvalue(*_t), endvalue(_ev) {}

// discrete values constructor
template<typename T>
DiscreteAnimation<T>::DiscreteAnimation(float _d, std::vector<T> _v, T* _t, std::function<void()> _cb, bool _l)
:Animation(_d, _t, _cb, _l), //duration(_d), target(_t), callback(_cb), loop(_l), elapsed(0.0f),
index(0), nonelapsed(0.0f), values(_v) {
    timestep = _v.size() / _d;
}

/* // don't call virtual functions (like cancel()) from base class destructor
 * // child classes destructors' are called first anyway
Animation::~Animation() {
    // deconstructor sets target to desired end state (no partial values)
    cancel();
}
*/

template<>
void LerpAnimation<std::string>::lerp() {
    *(std::string*)target = endvalue.substr(0, endvalue.length() * (elapsed / duration));
}

template<>
void LerpAnimation<int>::lerp() {
    int delta = endvalue - startvalue;
    *(int*)target = startvalue + (elapsed / duration * delta);
}

template<>
void LerpAnimation<float>::lerp() {
    int delta = endvalue - startvalue;
    *(float*)target = startvalue + (elapsed / duration * delta);
}

template<>
void LerpAnimation<sf::Vector2f>::lerp() {
    int delta_x = endvalue.x - startvalue.x;
    int delta_y = endvalue.y - startvalue.y;
    ((sf::Vector2f*)target)->x = startvalue.x + (elapsed / duration * delta_x);
    ((sf::Vector2f*)target)->y = startvalue.y + (elapsed / duration * delta_y);
}

template<>
void LerpAnimation<sf::Vector2i>::lerp() {
    int delta_x = endvalue.x - startvalue.y;
    int delta_y = endvalue.y - startvalue.y;
    ((sf::Vector2i*)target)->x = startvalue.x + (elapsed / duration * delta_x);
    ((sf::Vector2i*)target)->y = startvalue.y + (elapsed / duration * delta_y);
}

template<typename T>
void LerpAnimation<T>::step(float delta) {
    elapsed += delta;
    lerp();
    if (isDone()) cancel(); //use the exact value, not my math
}

template<typename T>
void DiscreteAnimation<T>::step(float delta)
{
    nonelapsed += delta;
    if (nonelapsed < timestep) return;
    if (index == values.size() - 1) return;
    elapsed += nonelapsed; // or should it be += timestep?
    nonelapsed = 0; // or should it -= timestep?
    index++;
    *target = values[index];
    if (isDone()) cancel(); //use the exact value, not my math
}

template<typename T>
void LerpAnimation<T>::cancel() {
    *target = endvalue;
}

template<typename T>
void DiscreteAnimation<T>::cancel() {
    *target = values[values.size() - 1];
}

bool Animation::isDone() {
    return elapsed + Animation::EPSILON >= duration;
}
