#pragma once
#include "UIDrawable.h"
#include <vector>
#include <memory>

// Base class for UI containers that provides common click handling logic
class UIContainerBase {
protected:
    // Transform a point from parent coordinates to this container's local coordinates
    virtual sf::Vector2f toLocalCoordinates(sf::Vector2f point) const = 0;
    
    // Transform a point from this container's local coordinates to child coordinates
    virtual sf::Vector2f toChildCoordinates(sf::Vector2f localPoint, int childIndex) const = 0;
    
    // Get the bounds of this container in parent coordinates
    virtual sf::FloatRect getBounds() const = 0;
    
    // Check if a local point is within this container's bounds
    virtual bool containsPoint(sf::Vector2f localPoint) const = 0;
    
    // Get click handler if this container has one
    virtual UIDrawable* getClickHandler() = 0;
    
    // Get children to check for clicks (can be empty)
    virtual std::vector<UIDrawable*> getClickableChildren() = 0;
    
public:
    // Standard click handling algorithm for all containers
    // Returns the deepest UIDrawable that has a click handler and contains the point
    UIDrawable* handleClick(sf::Vector2f point) {
        // Transform to local coordinates
        sf::Vector2f localPoint = toLocalCoordinates(point);
        
        // Check if point is within our bounds
        if (!containsPoint(localPoint)) {
            return nullptr;
        }
        
        // Check children in reverse z-order (top-most first)
        // This ensures that elements rendered on top get first chance at clicks
        auto children = getClickableChildren();
        
        // TODO: Sort by z-index if not already sorted
        // std::sort(children.begin(), children.end(), 
        //     [](UIDrawable* a, UIDrawable* b) { return a->z_index > b->z_index; });
        
        for (int i = children.size() - 1; i >= 0; --i) {
            if (!children[i]->visible) continue;
            
            sf::Vector2f childPoint = toChildCoordinates(localPoint, i);
            if (auto target = children[i]->click_at(childPoint)) {
                // Child (or its descendant) handled the click
                return target;
            }
            // If child didn't handle it, continue checking other children
            // This allows click-through for elements without handlers
        }
        
        // No child consumed the click
        // Now check if WE have a click handler
        return getClickHandler();
    }
};

// Helper for containers with simple box bounds
class RectangularContainer : public UIContainerBase {
protected:
    sf::FloatRect bounds;
    
    sf::Vector2f toLocalCoordinates(sf::Vector2f point) const override {
        return point - sf::Vector2f(bounds.left, bounds.top);
    }
    
    bool containsPoint(sf::Vector2f localPoint) const override {
        return localPoint.x >= 0 && localPoint.y >= 0 && 
               localPoint.x < bounds.width && localPoint.y < bounds.height;
    }
    
    sf::FloatRect getBounds() const override {
        return bounds;
    }
};