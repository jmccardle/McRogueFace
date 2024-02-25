#include "EntityManager.h"

EntityManager::EntityManager()
    :m_totalEntities(0) {}

void EntityManager::update()
{
    //TODO: add entities from m_entitiesToAdd to all vector / tag map
    removeDeadEntities(m_entities);

    // C++17 way of iterating!
    for (auto& [tag, entityVec] : m_entityMap)
    {
        removeDeadEntities(entityVec);
    }

    for (auto& e : m_entitiesToAdd)
    {
        m_entities.push_back(e);
        m_entityMap[e->tag()].push_back(e);
    }
    //if (m_entitiesToAdd.size())
    //    m_entitiesToAdd.erase(m_entitiesToAdd.begin(), m_entitiesToAdd.end());
    m_entitiesToAdd = EntityVec();
    
}

void EntityManager::removeDeadEntities(EntityVec & vec)
{
    EntityVec survivors; // New vector
    for (auto& e : m_entities){
        if (e->isActive()) survivors.push_back(e); // populate new vector
        else if (e->cGrid) { // erase vector from grid
			for( auto it = e->cGrid->grid->entities.begin(); it != e->cGrid->grid->entities.end(); it++){
				if( *it == e ){
					e->cGrid->grid->entities.erase( it );
					break;
				}
			}
		}
    }
    //std::cout << "All entities: " << m_entities.size() << " Survivors: " << survivors.size() << std::endl;
    m_entities = survivors; // point to new vector
    for (auto& [tag, entityVec] : m_entityMap)
    {
        EntityVec tag_survivors; // New vector
        for (auto& e : m_entityMap[tag])
        {
            if (e->isActive()) tag_survivors.push_back(e); // populate new vector
        }
        m_entityMap[tag] = tag_survivors; // point to new vector
    //std::cout << tag << " entities: " << m_entityMap[tag].size() << " Survivors: " << tag_survivors.size() << std::endl;
    }
}

std::shared_ptr<Entity> EntityManager::addEntity(const std::string & tag)
{
    // create the entity shared pointer
    auto entity = std::shared_ptr<Entity>(new Entity(m_totalEntities++, tag));
    m_entitiesToAdd.push_back(entity);
    return entity;
}

const EntityVec & EntityManager::getEntities()
{
    return m_entities;
}

const EntityVec & EntityManager::getEntities(const std::string & tag)
{
    return m_entityMap[tag];
}

