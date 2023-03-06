#include "Animation.h"

// linear interpolation constructor
template<typename T>
Animation<T>::Animation(float _d, T _ev, T* _t, std::function<void()> _cb, bool _l)
:duration(_d), endvalue(_ev), target(_t), callback(_cb), loop(_l),
index(-1), startvalue(*_t), elapsed(0.0f) {}

// discrete values constructor
template<typename T>
Animation<T>::Animation(float _d, std::vector<T> _v, T* _t, std::function<void()> _cb, bool _l)
:duration(_d), target(_t), callback(_cb), values(_v), loop(_l),
index(0), startvalue(*_t), elapsed(0.0f), nonelapsed(0.0f) {
    timestep = _v.size() / _d;
}

template<typename T>
Animation<T>::~Animation() {
    // deconstructor sets target to desired end state (no partial values)
    cancel();
}

template<>
void Animation<std::string>::lerp() {
    *target = endvalue.substr(0, endvalue.length() * (elapsed / duration));
}

template<>
void Animation<int>::lerp() {
    int delta = endvalue - startvalue;
    *target = startvalue + (elapsed / duration * delta);
}

template<>
void Animation<float>::lerp() {
    int delta = endvalue - startvalue;
    *target = startvalue + (elapsed / duration * delta);
}

template<>
void Animation<sf::Vector2f>::lerp() {
    int delta_x = endvalue.x - startvalue.x;
    int delta_y = endvalue.y - startvalue.y;
    target->x = startvalue.x + (elapsed / duration * delta_x);
    target->y = startvalue.y + (elapsed / duration * delta_y);
}

template<>
void Animation<sf::Vector2i>::lerp() {
    int delta_x = endvalue.x - startvalue.y;
    int delta_y = endvalue.y - startvalue.y;
    target->x = startvalue.x + (elapsed / duration * delta_x);
    target->y = startvalue.y + (elapsed / duration * delta_y);
}

template<typename T>
void Animation<T>::step(float delta)
{
    if (index == -1) {
        // lerp function
        elapsed += delta;
        lerp();
    }
    else {
        nonelapsed += delta;
        if (nonelapsed < timestep) return;
        if (index == values.size() - 1) return;
        elapsed += nonelapsed; // or should it be += timestep?
        nonelapsed = 0; // or should it -= timestep?
        index++;
        *target = values[index];
    }
}

template<typename T>
void Animation<T>::cancel() {
    if (index == -1)
        *target = endvalue;
    else
        *target = values[values.size() - 1];
}
