#include "Animation.h"

Animation::Animation(float _d, std::function<void()> _cb, bool _l)
:duration(_d), callback(_cb), loop(_l), elapsed(0.0f) {}

// linear interpolation constructor
template<typename T>
LerpAnimation<T>::LerpAnimation(float _d, T _ev, T _sv, std::function<void()> _cb, std::function<void(T)> _w, bool _l)
:Animation(_d, _cb, _l), //duration(_d), target(_t), callback(_cb), loop(_l),elapsed(0.0f),
startvalue(_sv), endvalue(_ev), write(_w) {}

// discrete values constructor
template<typename T>
DiscreteAnimation<T>::DiscreteAnimation(float _d, std::vector<T> _v, std::function<void()> _cb, std::function<void(T)> _w, bool _l)
:Animation(_d, _cb, _l), //duration(_d), target(_t), callback(_cb), loop(_l), elapsed(0.0f),
index(0), nonelapsed(0.0f), values(_v), write(_w) {
    timestep = _d / _v.size();
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
    //*(std::string*)target = ;
    write(endvalue.substr(0, endvalue.length() * (elapsed / duration)));
}

template<>
void LerpAnimation<int>::lerp() {
    int delta = endvalue - startvalue;
    //*(int*)target = ;
    write(startvalue + (elapsed / duration * delta));
}

template<>
void LerpAnimation<float>::lerp() {
    int delta = endvalue - startvalue;
    //*(float*)target = ;
    write(startvalue + (elapsed / duration * delta));
}

template<>
void LerpAnimation<sf::Vector2f>::lerp() {
    //std::cout << "sf::Vector2f implementation of lerp." << std::endl;
    int delta_x = endvalue.x - startvalue.x;
    int delta_y = endvalue.y - startvalue.y;
    //std::cout << "Start: " << startvalue.x << ", " << startvalue.y << "; End: " << endvalue.x << ", " << endvalue.y << std::endl;
    //std::cout << "Delta: " << delta_x << ", " << delta_y << std::endl;
    //((sf::Vector2f*)target)->x = startvalue.x + (elapsed / duration * delta_x);
    //((sf::Vector2f*)target)->y = startvalue.y + (elapsed / duration * delta_y);
    write(sf::Vector2f(startvalue.x + (elapsed / duration * delta_x), 
                       startvalue.y + (elapsed / duration * delta_y)));
}

template<>
void LerpAnimation<sf::Vector2i>::lerp() {
    int delta_x = endvalue.x - startvalue.y;
    int delta_y = endvalue.y - startvalue.y;
    //((sf::Vector2i*)target)->x = startvalue.x + (elapsed / duration * delta_x);
    //((sf::Vector2i*)target)->y = startvalue.y + (elapsed / duration * delta_y);
    write(sf::Vector2i(startvalue.x + (elapsed / duration * delta_x), 
                       startvalue.y + (elapsed / duration * delta_y)));
}

template<typename T>
void LerpAnimation<T>::step(float delta) {
	if (complete) return;
    elapsed += delta;
    //std::cout << "LerpAnimation step function. Elapsed: " << elapsed <<std::endl;
    lerp();
    if (isDone()) { callback(); complete = true; cancel(); }; //use the exact value, not my math
}

template<typename T>
void DiscreteAnimation<T>::step(float delta)
{
	if (complete) return;
    nonelapsed += delta;
    //std::cout << "Nonelapsed: " << nonelapsed << " elapsed (pre-add): " << elapsed << " timestep: " << timestep << " duration: " << duration << " index: " << index << std::endl;
    if (nonelapsed < timestep) return;
    //std::cout << "values size: " << values.size() << " isDone(): " << isDone() << std::endl;
    if (elapsed > duration && !complete) {callback(); complete = true; return; }
    elapsed += nonelapsed; // or should it be += timestep?
    if (index == values.size() - 1) return;
    nonelapsed = 0; // or should it -= timestep?
    index++;
    //*(T*)target = values[index];
    write(values[index]);
}

template<typename T>
void LerpAnimation<T>::cancel() {
    //*(T*)target = endvalue;
    write(endvalue);
}

template<typename T>
void DiscreteAnimation<T>::cancel() {
    //*(T*)target = values[values.size() - 1];
    write(values[values.size() - 1]);
}

bool Animation::isDone() {
    return elapsed + Animation::EPSILON >= duration;
}

namespace animation_template_implementations {
    // instantiate to compile concrete templates
    //LerpAnimation<sf::Vector2f> implement_vector2f;

    auto implement_v2f_const = LerpAnimation<sf::Vector2<float>>(4.0, sf::Vector2<float>(), sf::Vector2f(1,1), [](){}, [](sf::Vector2f v){}, false);
    auto implement_disc_i = DiscreteAnimation<int>(3.0, std::vector<int>{0},[](){},[](int){},false);
    //LerpAnimation<sf::Vector2i> implement_vector2i;
    //LerpAnimation<int> implment_int;
    //LerpAnimation<std::string> implment_string;
    //LerpAnimation<float> implement_float;
    //DiscreteAnimation<int> implement_int_discrete;
}
