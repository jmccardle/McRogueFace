#pragma once

#include "Common.h"

#include "Components.h"

class Entity
{
    friend class EntityManager;

    bool m_active = true;
    size_t m_id = 0;
    std::string m_tag = "default";

    //constructor and destructor
    Entity(const size_t id, const std::string & t);

public:
    // component pointers
    //std::shared_ptr<CTransform> cTransform;
    //std::shared_ptr<CShape> cShape;
    //std::shared_ptr<CCollision> cCollision;
    //std::shared_ptr<CInput> cInput;
    //std::shared_ptr<CScore> cScore;
    //std::shared_ptr<CLifespan> cLifespan;
    std::shared_ptr<CGrid> cGrid;
    std::shared_ptr<CInventory> cInventory;
    std::shared_ptr<CBehavior> cBehavior;

    //private member access functions
    bool isActive() const;
    const std::string & tag() const;
    const size_t id() const;
    void destroy();
};
