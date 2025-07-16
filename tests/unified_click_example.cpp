// Example of how UIFrame would implement unified click handling
//
// Click Priority Example:
// - Dialog Frame (has click handler to drag window)
//   - Title Caption (no click handler)
//   - Button Frame (has click handler)
//     - Button Caption "OK" (no click handler)
//   - Close X Sprite (has click handler)
//
// Clicking on:
// - "OK" text -> Button Frame gets the click (deepest parent with handler)
// - Close X -> Close sprite gets the click 
// - Title bar -> Dialog Frame gets the click (no child has handler there)
// - Outside dialog -> nullptr (bounds check fails)

class UIFrame : public UIDrawable, protected RectangularContainer {
private:
    // Implementation of container interface
    sf::Vector2f toChildCoordinates(sf::Vector2f localPoint, int childIndex) const override {
        // Children use same coordinate system as frame's local coordinates
        return localPoint;
    }
    
    UIDrawable* getClickHandler() override {
        return click_callable ? this : nullptr;
    }
    
    std::vector<UIDrawable*> getClickableChildren() override {
        std::vector<UIDrawable*> result;
        for (auto& child : *children) {
            result.push_back(child.get());
        }
        return result;
    }
    
public:
    UIDrawable* click_at(sf::Vector2f point) override {
        // Update bounds from box
        bounds = sf::FloatRect(box.getPosition().x, box.getPosition().y, 
                              box.getSize().x, box.getSize().y);
        
        // Use unified handler
        return handleClick(point);
    }
};

// Example for UIGrid with entity coordinate transformation
class UIGrid : public UIDrawable, protected RectangularContainer {
private:
    sf::Vector2f toChildCoordinates(sf::Vector2f localPoint, int childIndex) const override {
        // For entities, we need to transform from pixel coordinates to grid coordinates
        // This is where the grid's special coordinate system is handled
        
        // Assuming entity positions are in grid cells, not pixels
        // We pass pixel coordinates relative to the grid's rendering area
        return localPoint; // Entities will handle their own sprite positioning
    }
    
    std::vector<UIDrawable*> getClickableChildren() override {
        std::vector<UIDrawable*> result;
        
        // Only check entities that are visible on screen
        float left_edge = center_x - (box.getSize().x / 2.0f) / (grid_size * zoom);
        float top_edge = center_y - (box.getSize().y / 2.0f) / (grid_size * zoom);
        float right_edge = left_edge + (box.getSize().x / (grid_size * zoom));
        float bottom_edge = top_edge + (box.getSize().y / (grid_size * zoom));
        
        for (auto& entity : entities) {
            // Check if entity is within visible bounds
            if (entity->position.x >= left_edge - 1 && entity->position.x < right_edge + 1 &&
                entity->position.y >= top_edge - 1 && entity->position.y < bottom_edge + 1) {
                result.push_back(&entity->sprite);
            }
        }
        return result;
    }
};

// For Scene, which has no coordinate transformation
class PyScene : protected UIContainerBase {
private:
    sf::Vector2f toLocalCoordinates(sf::Vector2f point) const override {
        // Scene uses window coordinates directly
        return point;
    }
    
    sf::Vector2f toChildCoordinates(sf::Vector2f localPoint, int childIndex) const override {
        // Top-level drawables use window coordinates
        return localPoint;
    }
    
    bool containsPoint(sf::Vector2f localPoint) const override {
        // Scene contains all points (full window)
        return true;
    }
    
    UIDrawable* getClickHandler() override {
        // Scene itself doesn't handle clicks
        return nullptr;
    }
};