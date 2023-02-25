#pragma once

#include "Common.h"

/*
class CTransform
{
public:
    Vec2 pos = { 0.0, 0.0 };
    Vec2 velocity = { 0.0, 0.0 };
    float angle = 0;

    CTransform(const Vec2 & p, const Vec2 & v, float a)
        : pos(p), velocity(v), angle(a) {}
};
*/

class CShape
{
public:
    sf::CircleShape circle;

    CShape(float radius, int points, const sf::Color & fill, const sf::Color & outline, float thickness)
        : circle(radius, points)
    {
        circle.setFillColor(fill);
        circle.setOutlineColor(outline);
        circle.setOutlineThickness(thickness);
        circle.setOrigin(radius, radius);
    }
};

class CCollision
{
public:
    float radius = 0;
    CCollision(float r)
        : radius(r) {}
};

class CScore
{
public:
    int score = 0;
    CScore(int s)
        : score(s) {}
};

class CLifespan
{
public:
    int remaining = 0;
    int total = 0;
    CLifespan(int t)
        : remaining(t), total(t) {}
};

class CInput
{
public:
    bool up = false;
    bool left = false;
    bool right = false;
    bool down = false;
    bool fire = false;

    CInput() {}
};

class CSteer
{
public:
    sf::Vector2f position;
    sf::Vector2f velocity;
    float v_max;
    float dv_max;
    float theta_max;
    float dtheta_max;
};
