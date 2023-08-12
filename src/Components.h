#pragma once

#include "Common.h"
#include "IndexSprite.h"
#include "Grid.h"
//#include "Item.h"
#include "Python.h"
#include <list>

class CGrid
{
public:
	bool visible;
	int x, y;
	IndexSprite indexsprite;
	Grid* grid;
	CGrid(Grid* _g, int _ti, int _si, int _x, int _y, bool _v)
	: visible(_v), x(_x), y(_y), grid(_g), indexsprite(_ti, _si, _x, _y, 1.0) {}
};

class CInventory
{
public:
	//std::list<std::shared_ptr<Item>>;
	int x;
};

class CBehavior
{
public:
	PyObject* object;
	CBehavior(PyObject* p): object(p) {}
};

/*
class CCombatant
{
public:
	int hp;
	int maxhp; 
}

class CCaster
{
public:
	int mp;
	int maxmp;
}

class CLevel
{
	int constitution; // +HP, resist effects
	int strength; // +damage, block/parry
	int dexterity; // +speed, dodge
	int intelligence; // +MP, spell resist
	int wisdom; // +damage, deflect
	int luck; // crit, loot
}
*/


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

/*
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
*/
