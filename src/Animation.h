#pragma once
#include "Common.h"

class Animation
{
protected:
    static constexpr float EPSILON = 0.05;
    float duration, elapsed;
    void* target;
    std::function<void()> callback;
    bool loop;
public:
    //Animation(float, T, T*, std::function<void()>, bool); // lerp
    //Animation(float, std::vector<T>, T*, std::function<void()>, bool); // discrete 
    Animation(float, void*, std::function<void()>, bool);
    virtual void step(float) = 0;
    virtual void cancel() = 0;
    bool isDone();
};

template<typename T>
class LerpAnimation: public Animation
{
    T startvalue, endvalue;
    void lerp();
public:
    ~LerpAnimation() { cancel(); }
    LerpAnimation(float, T, T*, std::function<void()>, bool);
    void step(float) override final;
    void cancel() override final;
};

template<typename T>
class DiscreteAnimation: public Animation
{
    std::vector<T> values;
    float nonelapsed, timestep;
    int index;
public:
    DiscreteAnimation(float, std::vector<T>, T*, std::function<void()>, bool);
    ~DiscreteAnimation() { cancel(); }
    void step(float) override final;
    void cancel() override final;
};
