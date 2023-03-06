#pragma once
#include "Common.h"

template<typename T>
class Animation
{
    static constexpr float EPSILON = 0.05;
    T startvalue, endvalue;
    int index;
    float duration, elapsed, nonelapsed, timestep;
    T* target;
    std::vector<T> values;
    std::function<void()> callback;
    bool loop;
public:
    Animation(float, T, T*, std::function<void()>, bool); // lerp
    Animation(float, std::vector<T>, T*, std::function<void()>, bool); // discrete 
    ~Animation();
    void lerp();
    void step(float);
    void cancel();
    bool isDone();
};
