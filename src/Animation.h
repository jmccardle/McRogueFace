#pragma once
#include "Common.h"
#include <functional>

class Animation
{
protected:
    static constexpr float EPSILON = 0.05;
    float duration, elapsed;
    std::function<void()> callback;
    bool loop;
	bool complete=false;
public:
    //Animation(float, T, T*, std::function<void()>, bool); // lerp
    //Animation(float, std::vector<T>, T*, std::function<void()>, bool); // discrete 
    Animation(float, std::function<void()>, bool);
    //Animation() {};
    virtual void step(float) = 0;
    virtual void cancel() = 0;
    bool isDone();
};

template<typename T>
class LerpAnimation: public Animation
{
    T startvalue, endvalue;
    std::function<void(T)> write;
    void lerp();
public:
    ~LerpAnimation() { cancel(); }
    LerpAnimation(float, T, T, std::function<void()>, std::function<void(T)>, bool);
    //LerpAnimation() {};
    void step(float) override final;
    void cancel() override final;
};

template<typename T>
class DiscreteAnimation: public Animation
{
    std::vector<T> values;
    std::function<void(T)> write;
    float nonelapsed, timestep;
    int index;
public:
    DiscreteAnimation(float, std::vector<T>, std::function<void()>, std::function<void(T)>, bool);
    DiscreteAnimation() {};
    ~DiscreteAnimation() { cancel(); }
    void step(float) override final;
    void cancel() override final;
};
