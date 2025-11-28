#include "UIGrid.h"
#include "GameEngine.h"
#include "McRFPy_API.h"
#include "PythonObjectCache.h"
#include "UIEntity.h"
#include "Profiler.h"
#include <algorithm>
#include <cmath>  // #142 - for std::floor
// UIDrawable methods now in UIBase.h

UIGrid::UIGrid() 
: grid_x(0), grid_y(0), zoom(1.0f), center_x(0.0f), center_y(0.0f), ptex(nullptr),
  fill_color(8, 8, 8, 255), tcod_map(nullptr), tcod_dijkstra(nullptr), tcod_path(nullptr),
  perspective_enabled(false)  // Default to omniscient view
{
    // Initialize entities list
    entities = std::make_shared<std::list<std::shared_ptr<UIEntity>>>();

    // Initialize children collection (for UIDrawables like speech bubbles, effects)
    children = std::make_shared<std::vector<std::shared_ptr<UIDrawable>>>();

    // Initialize box with safe defaults
    box.setSize(sf::Vector2f(0, 0));
    position = sf::Vector2f(0, 0);  // Set base class position
    box.setPosition(position);      // Sync box position
    box.setFillColor(sf::Color(0, 0, 0, 0));
    
    // Initialize render texture (small default size)
    renderTexture.create(1, 1);
    
    // Initialize output sprite
    output.setTextureRect(sf::IntRect(0, 0, 0, 0));
    output.setPosition(0, 0);
    output.setTexture(renderTexture.getTexture());
    
    // Points vector starts empty (grid_x * grid_y = 0)
    // TCOD map will be created when grid is resized
}

UIGrid::UIGrid(int gx, int gy, std::shared_ptr<PyTexture> _ptex, sf::Vector2f _xy, sf::Vector2f _wh)
: grid_x(gx), grid_y(gy),
  zoom(1.0f), 
  ptex(_ptex), points(gx * gy),
  fill_color(8, 8, 8, 255), tcod_map(nullptr), tcod_dijkstra(nullptr), tcod_path(nullptr),
  perspective_enabled(false)  // Default to omniscient view
{
    // Use texture dimensions if available, otherwise use defaults
    int cell_width = _ptex ? _ptex->sprite_width : DEFAULT_CELL_WIDTH;
    int cell_height = _ptex ? _ptex->sprite_height : DEFAULT_CELL_HEIGHT;
    
    center_x = (gx/2) * cell_width;
    center_y = (gy/2) * cell_height;
    entities = std::make_shared<std::list<std::shared_ptr<UIEntity>>>();

    // Initialize children collection (for UIDrawables like speech bubbles, effects)
    children = std::make_shared<std::vector<std::shared_ptr<UIDrawable>>>();

    box.setSize(_wh);
    position = _xy;               // Set base class position
    box.setPosition(position);    // Sync box position 

    box.setFillColor(sf::Color(0,0,0,0));
    // create renderTexture with maximum theoretical size; sprite can resize to show whatever amount needs to be rendered
    renderTexture.create(1920, 1080); // TODO - renderTexture should be window size; above 1080p this will cause rendering errors
    
    // Only initialize sprite if texture is available
    if (ptex) {
        sprite = ptex->sprite(0);
    }

    output.setTextureRect(
         sf::IntRect(0, 0,
         box.getSize().x, box.getSize().y));
     output.setPosition(box.getPosition());
     // textures are upside-down inside renderTexture
     output.setTexture(renderTexture.getTexture());

    // Create TCOD map
    tcod_map = new TCODMap(gx, gy);
    
    // Create TCOD dijkstra pathfinder
    tcod_dijkstra = new TCODDijkstra(tcod_map);
    
    // Create TCOD A* pathfinder
    tcod_path = new TCODPath(tcod_map);
    
    // Initialize grid points with parent reference
    for (int y = 0; y < gy; y++) {
        for (int x = 0; x < gx; x++) {
            int idx = y * gx + x;
            points[idx].grid_x = x;
            points[idx].grid_y = y;
            points[idx].parent_grid = this;
        }
    }
    
    // Initial sync of TCOD map
    syncTCODMap();
}

void UIGrid::update() {}


void UIGrid::render(sf::Vector2f offset, sf::RenderTarget& target)
{
    // Profile total grid rendering time
    ScopedTimer gridTimer(Resources::game->metrics.gridRenderTime);

    // Check visibility
    if (!visible) return;

    // TODO: Apply opacity to output sprite

    output.setPosition(box.getPosition() + offset); // output sprite can move; update position when drawing
    // output size can change; update size when drawing
    output.setTextureRect(
         sf::IntRect(0, 0,
         box.getSize().x, box.getSize().y));
    renderTexture.clear(fill_color);
    
    // Get cell dimensions - use texture if available, otherwise defaults
    int cell_width = ptex ? ptex->sprite_width : DEFAULT_CELL_WIDTH;
    int cell_height = ptex ? ptex->sprite_height : DEFAULT_CELL_HEIGHT;
    
    // sprites that are visible according to zoom, center_x, center_y, and box width
    float center_x_sq = center_x / cell_width;
    float center_y_sq = center_y / cell_height;

    float width_sq = box.getSize().x / (cell_width * zoom);
    float height_sq = box.getSize().y / (cell_height * zoom);
    float left_edge = center_x_sq - (width_sq / 2.0);
    float top_edge = center_y_sq - (height_sq / 2.0);

    int left_spritepixels = center_x - (box.getSize().x / 2.0 / zoom);
    int top_spritepixels = center_y - (box.getSize().y / 2.0 / zoom);

    //sprite.setScale(sf::Vector2f(zoom, zoom));
    sf::RectangleShape r; // for colors and overlays
    r.setSize(sf::Vector2f(cell_width * zoom, cell_height * zoom));
    r.setOutlineThickness(0);

    int x_limit = left_edge + width_sq + 2;
    if (x_limit > grid_x) x_limit = grid_x;

    int y_limit = top_edge + height_sq + 2;
    if (y_limit > grid_y) y_limit = grid_y;

    // base layer - bottom color, tile sprite ("ground")
    int cellsRendered = 0;
    for (int x = (left_edge - 1 >= 0 ? left_edge - 1 : 0);
        x < x_limit; //x < view_width;
        x+=1)
    {
        //for (float y = (top_edge >= 0 ? top_edge : 0);
        for (int y = (top_edge - 1 >= 0 ? top_edge - 1 : 0);
            y < y_limit; //y < view_height;
            y+=1)
        {
            auto pixel_pos = sf::Vector2f(
                    (x*cell_width - left_spritepixels) * zoom,
                    (y*cell_height - top_spritepixels) * zoom );

            auto gridpoint = at(std::floor(x), std::floor(y));

            //sprite.setPosition(pixel_pos);

            r.setPosition(pixel_pos);
            r.setFillColor(gridpoint.color);
            renderTexture.draw(r);

            // tilesprite - only draw if texture is available
            // if discovered but not visible, set opacity to 90%
            // if not discovered... just don't draw it?
            if (ptex && gridpoint.tilesprite != -1) {
                sprite = ptex->sprite(gridpoint.tilesprite, pixel_pos, sf::Vector2f(zoom, zoom)); //setSprite(gridpoint.tilesprite);;
                renderTexture.draw(sprite);
            }

            cellsRendered++;
        }
    }

    // Record how many cells were rendered
    Resources::game->metrics.gridCellsRendered += cellsRendered;

    // middle layer - entities
    // disabling entity rendering until I can render their UISprite inside the rendertexture (not directly to window)
    {
        ScopedTimer entityTimer(Resources::game->metrics.entityRenderTime);
        int entitiesRendered = 0;
        int totalEntities = entities->size();

        for (auto e : *entities) {
            // Skip out-of-bounds entities for performance
            // Check if entity is within visible bounds (with 1 cell margin for partially visible entities)
            if (e->position.x < left_edge - 1 || e->position.x >= left_edge + width_sq + 1 ||
                e->position.y < top_edge - 1 || e->position.y >= top_edge + height_sq + 1) {
                continue; // Skip this entity as it's not visible
            }

            //auto drawent = e->cGrid->indexsprite.drawable();
            auto& drawent = e->sprite;
            //drawent.setScale(zoom, zoom);
            drawent.setScale(sf::Vector2f(zoom, zoom));
            auto pixel_pos = sf::Vector2f(
                (e->position.x*cell_width - left_spritepixels) * zoom,
                (e->position.y*cell_height - top_spritepixels) * zoom );
            //drawent.setPosition(pixel_pos);
            //renderTexture.draw(drawent);
            drawent.render(pixel_pos, renderTexture);

            entitiesRendered++;
        }

        // Record entity rendering stats
        Resources::game->metrics.entitiesRendered += entitiesRendered;
        Resources::game->metrics.totalEntities += totalEntities;
    }

    // Children layer - UIDrawables in grid-world pixel coordinates
    // Positioned between entities and FOV overlay for proper z-ordering
    if (children && !children->empty()) {
        // Sort by z_index if needed
        if (children_need_sort) {
            std::sort(children->begin(), children->end(),
                [](const auto& a, const auto& b) { return a->z_index < b->z_index; });
            children_need_sort = false;
        }

        for (auto& child : *children) {
            if (!child->visible) continue;

            // Cull children outside visible region (convert pixel pos to cell coords)
            float child_grid_x = child->position.x / cell_width;
            float child_grid_y = child->position.y / cell_height;

            if (child_grid_x < left_edge - 2 || child_grid_x >= left_edge + width_sq + 2 ||
                child_grid_y < top_edge - 2 || child_grid_y >= top_edge + height_sq + 2) {
                continue; // Not visible, skip rendering
            }

            // Transform grid-world pixel position to RenderTexture pixel position
            auto pixel_pos = sf::Vector2f(
                (child->position.x - left_spritepixels) * zoom,
                (child->position.y - top_spritepixels) * zoom
            );

            child->render(pixel_pos, renderTexture);
        }
    }

    // top layer - opacity for discovered / visible status based on perspective
    // Only render visibility overlay if perspective is enabled
    if (perspective_enabled) {
        ScopedTimer fovTimer(Resources::game->metrics.fovOverlayTime);
        auto entity = perspective_entity.lock();
        
        // Create rectangle for overlays
        sf::RectangleShape overlay;
        overlay.setSize(sf::Vector2f(cell_width * zoom, cell_height * zoom));
        
        if (entity) {
            // Valid entity - use its gridstate for visibility
            for (int x = (left_edge - 1 >= 0 ? left_edge - 1 : 0);
                x < x_limit;
                x+=1)
            {
                for (int y = (top_edge - 1 >= 0 ? top_edge - 1 : 0);
                    y < y_limit;
                    y+=1)
                {
                    // Skip out-of-bounds cells
                    if (x < 0 || x >= grid_x || y < 0 || y >= grid_y) continue;
                    
                    auto pixel_pos = sf::Vector2f(
                            (x*cell_width - left_spritepixels) * zoom,
                            (y*cell_height - top_spritepixels) * zoom );

                    // Get visibility state from entity's perspective
                    int idx = y * grid_x + x;
                    if (idx >= 0 && idx < static_cast<int>(entity->gridstate.size())) {
                        const auto& state = entity->gridstate[idx];
                        
                        overlay.setPosition(pixel_pos);
                        
                        // Three overlay colors as specified:
                        if (!state.discovered) {
                            // Never seen - black
                            overlay.setFillColor(sf::Color(0, 0, 0, 255));
                            renderTexture.draw(overlay);
                        } else if (!state.visible) {
                            // Discovered but not currently visible - dark gray
                            overlay.setFillColor(sf::Color(32, 32, 40, 192));
                            renderTexture.draw(overlay);
                        }
                        // If visible and discovered, no overlay (fully visible)
                    }
                }
            }
        } else {
            // Invalid/destroyed entity with perspective_enabled = true
            // Show all cells as undiscovered (black)
            for (int x = (left_edge - 1 >= 0 ? left_edge - 1 : 0);
                x < x_limit;
                x+=1)
            {
                for (int y = (top_edge - 1 >= 0 ? top_edge - 1 : 0);
                    y < y_limit;
                    y+=1)
                {
                    // Skip out-of-bounds cells
                    if (x < 0 || x >= grid_x || y < 0 || y >= grid_y) continue;
                    
                    auto pixel_pos = sf::Vector2f(
                            (x*cell_width - left_spritepixels) * zoom,
                            (y*cell_height - top_spritepixels) * zoom );
                    
                    overlay.setPosition(pixel_pos);
                    overlay.setFillColor(sf::Color(0, 0, 0, 255));
                    renderTexture.draw(overlay);
                }
            }
        }
    }
    // else: omniscient view (no overlays)

    // grid lines for testing & validation
    /*
    sf::Vertex line[] =
    {
        sf::Vertex(sf::Vector2f(0, 0), sf::Color::Red),
        sf::Vertex(box.getSize(), sf::Color::Red),

    };

    renderTexture.draw(line, 2, sf::Lines);
    sf::Vertex lineb[] =
    {
        sf::Vertex(sf::Vector2f(0, box.getSize().y), sf::Color::Blue),
        sf::Vertex(sf::Vector2f(box.getSize().x, 0), sf::Color::Blue),

    };

    renderTexture.draw(lineb, 2, sf::Lines);
    */

    // render to window
    renderTexture.display();
    //Resources::game->getWindow().draw(output);
    target.draw(output);

}

UIGridPoint& UIGrid::at(int x, int y)
{
    return points[y * grid_x + x];
}

UIGrid::~UIGrid()
{
    if (tcod_path) {
        delete tcod_path;
        tcod_path = nullptr;
    }
    if (tcod_dijkstra) {
        delete tcod_dijkstra;
        tcod_dijkstra = nullptr;
    }
    if (tcod_map) {
        delete tcod_map;
        tcod_map = nullptr;
    }
}

PyObjectsEnum UIGrid::derived_type()
{
    return PyObjectsEnum::UIGRID;
}

// TCOD integration methods
void UIGrid::syncTCODMap()
{
    if (!tcod_map) return;
    
    for (int y = 0; y < grid_y; y++) {
        for (int x = 0; x < grid_x; x++) {
            const UIGridPoint& point = at(x, y);
            tcod_map->setProperties(x, y, point.transparent, point.walkable);
        }
    }
}

void UIGrid::syncTCODMapCell(int x, int y)
{
    if (!tcod_map || x < 0 || x >= grid_x || y < 0 || y >= grid_y) return;
    
    const UIGridPoint& point = at(x, y);
    tcod_map->setProperties(x, y, point.transparent, point.walkable);
}

void UIGrid::computeFOV(int x, int y, int radius, bool light_walls, TCOD_fov_algorithm_t algo)
{
    if (!tcod_map || x < 0 || x >= grid_x || y < 0 || y >= grid_y) return;
    
    std::lock_guard<std::mutex> lock(fov_mutex);
    tcod_map->computeFov(x, y, radius, light_walls, algo);
}

bool UIGrid::isInFOV(int x, int y) const
{
    if (!tcod_map || x < 0 || x >= grid_x || y < 0 || y >= grid_y) return false;
    
    std::lock_guard<std::mutex> lock(fov_mutex);
    return tcod_map->isInFov(x, y);
}

std::vector<std::pair<int, int>> UIGrid::findPath(int x1, int y1, int x2, int y2, float diagonalCost)
{
    std::vector<std::pair<int, int>> path;
    
    if (!tcod_map || x1 < 0 || x1 >= grid_x || y1 < 0 || y1 >= grid_y ||
        x2 < 0 || x2 >= grid_x || y2 < 0 || y2 >= grid_y) {
        return path;
    }
    
    TCODPath tcod_path(tcod_map, diagonalCost);
    if (tcod_path.compute(x1, y1, x2, y2)) {
        for (int i = 0; i < tcod_path.size(); i++) {
            int x, y;
            tcod_path.get(i, &x, &y);
            path.push_back(std::make_pair(x, y));
        }
    }
    
    return path;
}

void UIGrid::computeDijkstra(int rootX, int rootY, float diagonalCost)
{
    if (!tcod_map || !tcod_dijkstra || rootX < 0 || rootX >= grid_x || rootY < 0 || rootY >= grid_y) return;
    
    // Compute the Dijkstra map from the root position
    tcod_dijkstra->compute(rootX, rootY);
}

float UIGrid::getDijkstraDistance(int x, int y) const
{
    if (!tcod_dijkstra || x < 0 || x >= grid_x || y < 0 || y >= grid_y) {
        return -1.0f;  // Invalid position
    }
    
    return tcod_dijkstra->getDistance(x, y);
}

std::vector<std::pair<int, int>> UIGrid::getDijkstraPath(int x, int y) const
{
    std::vector<std::pair<int, int>> path;
    
    if (!tcod_dijkstra || x < 0 || x >= grid_x || y < 0 || y >= grid_y) {
        return path;  // Empty path for invalid position
    }
    
    // Set the destination
    if (tcod_dijkstra->setPath(x, y)) {
        // Walk the path and collect points
        int px, py;
        while (tcod_dijkstra->walk(&px, &py)) {
            path.push_back(std::make_pair(px, py));
        }
    }
    
    return path;
}

// A* pathfinding implementation
std::vector<std::pair<int, int>> UIGrid::computeAStarPath(int x1, int y1, int x2, int y2, float diagonalCost)
{
    std::vector<std::pair<int, int>> path;
    
    // Validate inputs
    if (!tcod_map || !tcod_path || 
        x1 < 0 || x1 >= grid_x || y1 < 0 || y1 >= grid_y ||
        x2 < 0 || x2 >= grid_x || y2 < 0 || y2 >= grid_y) {
        return path; // Return empty path
    }
    
    // Set diagonal cost (TCODPath doesn't take it as parameter to compute)
    // Instead, diagonal cost is set during TCODPath construction
    // For now, we'll use the default diagonal cost from the constructor
    
    // Compute the path
    bool success = tcod_path->compute(x1, y1, x2, y2);
    
    if (success) {
        // Get the computed path
        int pathSize = tcod_path->size();
        path.reserve(pathSize);
        
        // TCOD path includes the starting position, so we start from index 0
        for (int i = 0; i < pathSize; i++) {
            int px, py;
            tcod_path->get(i, &px, &py);
            path.push_back(std::make_pair(px, py));
        }
    }
    
    return path;
}

// Phase 1 implementations
sf::FloatRect UIGrid::get_bounds() const
{
    auto size = box.getSize();
    return sf::FloatRect(position.x, position.y, size.x, size.y);
}

void UIGrid::move(float dx, float dy)
{
    position.x += dx;
    position.y += dy;
    box.setPosition(position);  // Keep box in sync
    output.setPosition(position);  // Keep output sprite in sync too
}

void UIGrid::resize(float w, float h)
{
    box.setSize(sf::Vector2f(w, h));
    // Recreate render texture with new size
    if (w > 0 && h > 0) {
        renderTexture.create(static_cast<unsigned int>(w), static_cast<unsigned int>(h));
        output.setTexture(renderTexture.getTexture());
    }
}

void UIGrid::onPositionChanged()
{
    // Sync box and output sprite positions with base class position
    box.setPosition(position);
    output.setPosition(position);
}

std::shared_ptr<PyTexture> UIGrid::getTexture()
{
    return ptex;
}

UIDrawable* UIGrid::click_at(sf::Vector2f point)
{
    // Check grid bounds first
    if (!box.getGlobalBounds().contains(point)) {
        return nullptr;
    }
    
    // Transform to local coordinates
    sf::Vector2f localPoint = point - box.getPosition();
    
    // Get cell dimensions
    int cell_width = ptex ? ptex->sprite_width : DEFAULT_CELL_WIDTH;
    int cell_height = ptex ? ptex->sprite_height : DEFAULT_CELL_HEIGHT;
    
    // Calculate visible area parameters (from render function)
    float center_x_sq = center_x / cell_width;
    float center_y_sq = center_y / cell_height;
    float width_sq = box.getSize().x / (cell_width * zoom);
    float height_sq = box.getSize().y / (cell_height * zoom);
    
    int left_spritepixels = center_x - (box.getSize().x / 2.0 / zoom);
    int top_spritepixels = center_y - (box.getSize().y / 2.0 / zoom);
    
    // Convert click position to grid-world pixel coordinates
    float grid_world_x = localPoint.x / zoom + left_spritepixels;
    float grid_world_y = localPoint.y / zoom + top_spritepixels;

    // Convert to grid cell coordinates
    float grid_x = grid_world_x / cell_width;
    float grid_y = grid_world_y / cell_height;

    // Check children first (they render on top, so they get priority)
    // Children are positioned in grid-world pixel coordinates
    if (children && !children->empty()) {
        // Check in reverse z-order (highest z_index first, rendered last = on top)
        for (auto it = children->rbegin(); it != children->rend(); ++it) {
            auto& child = *it;
            if (!child->visible) continue;

            // Transform click to child's local coordinate space
            // Children's position is in grid-world pixels
            sf::Vector2f childLocalPoint = sf::Vector2f(grid_world_x, grid_world_y);

            if (auto target = child->click_at(childLocalPoint)) {
                return target;
            }
        }
    }

    // Check entities in reverse order (assuming they should be checked top to bottom)
    // Note: entities list is not sorted by z-index currently, but we iterate in reverse
    // to match the render order assumption
    if (entities) {
        for (auto it = entities->rbegin(); it != entities->rend(); ++it) {
            auto& entity = *it;
            if (!entity || !entity->sprite.visible) continue;
            
            // Check if click is within entity's grid cell
            // Entities occupy a 1x1 grid cell centered on their position
            float dx = grid_x - entity->position.x;
            float dy = grid_y - entity->position.y;
            
            if (dx >= -0.5f && dx < 0.5f && dy >= -0.5f && dy < 0.5f) {
                // Click is within the entity's cell
                // Check if entity sprite has a click handler
                // For now, we return the entity's sprite as the click target
                // Note: UIEntity doesn't derive from UIDrawable, so we check its sprite
                if (entity->sprite.click_callable) {
                    return &entity->sprite;
                }
            }
        }
    }
    
    // No entity handled it, check if grid itself has handler
    if (click_callable) {
        // #142 - Fire on_cell_click if we have the callback and clicked on a valid cell
        if (on_cell_click_callable) {
            int cell_x = static_cast<int>(std::floor(grid_x));
            int cell_y = static_cast<int>(std::floor(grid_y));

            // Only fire if within valid grid bounds
            if (cell_x >= 0 && cell_x < this->grid_x && cell_y >= 0 && cell_y < this->grid_y) {
                PyObject* args = Py_BuildValue("(ii)", cell_x, cell_y);
                PyObject* result = PyObject_CallObject(on_cell_click_callable->borrow(), args);
                Py_DECREF(args);
                if (!result) {
                    std::cerr << "Cell click callback raised an exception:" << std::endl;
                    PyErr_Print();
                    PyErr_Clear();
                } else {
                    Py_DECREF(result);
                }
            }
        }
        return this;
    }

    // #142 - Even without click_callable, fire on_cell_click if present
    // Note: We fire the callback but DON'T return this, because PyScene::do_mouse_input
    // would try to call click_callable which doesn't exist
    if (on_cell_click_callable) {
        int cell_x = static_cast<int>(std::floor(grid_x));
        int cell_y = static_cast<int>(std::floor(grid_y));

        // Only fire if within valid grid bounds
        if (cell_x >= 0 && cell_x < this->grid_x && cell_y >= 0 && cell_y < this->grid_y) {
            PyObject* args = Py_BuildValue("(ii)", cell_x, cell_y);
            PyObject* result = PyObject_CallObject(on_cell_click_callable->borrow(), args);
            Py_DECREF(args);
            if (!result) {
                std::cerr << "Cell click callback raised an exception:" << std::endl;
                PyErr_Print();
                PyErr_Clear();
            } else {
                Py_DECREF(result);
            }
            // Don't return this - no click_callable to call
        }
    }

    return nullptr;
}


int UIGrid::init(PyUIGridObject* self, PyObject* args, PyObject* kwds) {
    // Define all parameters with defaults
    PyObject* pos_obj = nullptr;
    PyObject* size_obj = nullptr;
    PyObject* grid_size_obj = nullptr;
    PyObject* textureObj = nullptr;
    PyObject* fill_color = nullptr;
    PyObject* click_handler = nullptr;
    float center_x = 0.0f, center_y = 0.0f;
    float zoom = 1.0f;
    // perspective is now handled via properties, not init args
    int visible = 1;
    float opacity = 1.0f;
    int z_index = 0;
    const char* name = nullptr;
    float x = 0.0f, y = 0.0f, w = 0.0f, h = 0.0f;
    int grid_x = 2, grid_y = 2;  // Default to 2x2 grid
    
    // Keywords list matches the new spec: positional args first, then all keyword args
    static const char* kwlist[] = {
        "pos", "size", "grid_size", "texture",  // Positional args (as per spec)
        // Keyword-only args
        "fill_color", "click", "center_x", "center_y", "zoom",
        "visible", "opacity", "z_index", "name", "x", "y", "w", "h", "grid_x", "grid_y",
        nullptr
    };
    
    // Parse arguments with | for optional positional args
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OOOOOOfffifizffffii", const_cast<char**>(kwlist),
                                     &pos_obj, &size_obj, &grid_size_obj, &textureObj,  // Positional
                                     &fill_color, &click_handler, &center_x, &center_y, &zoom,
                                     &visible, &opacity, &z_index, &name, &x, &y, &w, &h, &grid_x, &grid_y)) {
        return -1;
    }
    
    // Handle position argument (can be tuple, Vector, or use x/y keywords)
    if (pos_obj) {
        PyVectorObject* vec = PyVector::from_arg(pos_obj);
        if (vec) {
            x = vec->data.x;
            y = vec->data.y;
            Py_DECREF(vec);
        } else {
            PyErr_Clear();
            if (PyTuple_Check(pos_obj) && PyTuple_Size(pos_obj) == 2) {
                PyObject* x_val = PyTuple_GetItem(pos_obj, 0);
                PyObject* y_val = PyTuple_GetItem(pos_obj, 1);
                if ((PyFloat_Check(x_val) || PyLong_Check(x_val)) &&
                    (PyFloat_Check(y_val) || PyLong_Check(y_val))) {
                    x = PyFloat_Check(x_val) ? PyFloat_AsDouble(x_val) : PyLong_AsLong(x_val);
                    y = PyFloat_Check(y_val) ? PyFloat_AsDouble(y_val) : PyLong_AsLong(y_val);
                } else {
                    PyErr_SetString(PyExc_TypeError, "pos tuple must contain numbers");
                    return -1;
                }
            } else {
                PyErr_SetString(PyExc_TypeError, "pos must be a tuple (x, y) or Vector");
                return -1;
            }
        }
    }
    
    // Handle size argument (can be tuple or use w/h keywords)
    if (size_obj) {
        if (PyTuple_Check(size_obj) && PyTuple_Size(size_obj) == 2) {
            PyObject* w_val = PyTuple_GetItem(size_obj, 0);
            PyObject* h_val = PyTuple_GetItem(size_obj, 1);
            if ((PyFloat_Check(w_val) || PyLong_Check(w_val)) &&
                (PyFloat_Check(h_val) || PyLong_Check(h_val))) {
                w = PyFloat_Check(w_val) ? PyFloat_AsDouble(w_val) : PyLong_AsLong(w_val);
                h = PyFloat_Check(h_val) ? PyFloat_AsDouble(h_val) : PyLong_AsLong(h_val);
            } else {
                PyErr_SetString(PyExc_TypeError, "size tuple must contain numbers");
                return -1;
            }
        } else {
            PyErr_SetString(PyExc_TypeError, "size must be a tuple (w, h)");
            return -1;
        }
    }
    
    // Handle grid_size argument (can be tuple or use grid_x/grid_y keywords)
    if (grid_size_obj) {
        if (PyTuple_Check(grid_size_obj) && PyTuple_Size(grid_size_obj) == 2) {
            PyObject* gx_val = PyTuple_GetItem(grid_size_obj, 0);
            PyObject* gy_val = PyTuple_GetItem(grid_size_obj, 1);
            if (PyLong_Check(gx_val) && PyLong_Check(gy_val)) {
                grid_x = PyLong_AsLong(gx_val);
                grid_y = PyLong_AsLong(gy_val);
            } else {
                PyErr_SetString(PyExc_TypeError, "grid_size tuple must contain integers");
                return -1;
            }
        } else {
            PyErr_SetString(PyExc_TypeError, "grid_size must be a tuple (grid_x, grid_y)");
            return -1;
        }
    }
    
    // Validate grid dimensions
    if (grid_x <= 0 || grid_y <= 0) {
        PyErr_SetString(PyExc_ValueError, "Grid dimensions must be positive integers");
        return -1;
    }

    // Handle texture argument
    std::shared_ptr<PyTexture> texture_ptr = nullptr;
    if (textureObj && textureObj != Py_None) {
        if (!PyObject_IsInstance(textureObj, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Texture"))) {
            PyErr_SetString(PyExc_TypeError, "texture must be a mcrfpy.Texture instance or None");
            return -1;
        }
        PyTextureObject* pyTexture = reinterpret_cast<PyTextureObject*>(textureObj);
        texture_ptr = pyTexture->data;
    } else {
        // Use default texture when None is provided or texture not specified
        texture_ptr = McRFPy_API::default_texture;
    }
    
    // If size wasn't specified, calculate based on grid dimensions and texture
    if (!size_obj && texture_ptr) {
        w = grid_x * texture_ptr->sprite_width;
        h = grid_y * texture_ptr->sprite_height;
    } else if (!size_obj) {
        w = grid_x * 16.0f;  // Default tile size
        h = grid_y * 16.0f;
    }
    
    // Create the grid
    self->data = std::make_shared<UIGrid>(grid_x, grid_y, texture_ptr, 
                                          sf::Vector2f(x, y), sf::Vector2f(w, h));
    
    // Set additional properties
    self->data->center_x = center_x;
    self->data->center_y = center_y;
    self->data->zoom = zoom;
    // perspective is now handled by perspective_entity and perspective_enabled
    // self->data->perspective = perspective;
    self->data->visible = visible;
    self->data->opacity = opacity;
    self->data->z_index = z_index;
    if (name) {
        self->data->name = std::string(name);
    }
    
    // Handle fill_color
    if (fill_color && fill_color != Py_None) {
        PyColorObject* color_obj = PyColor::from_arg(fill_color);
        if (!color_obj) {
            PyErr_SetString(PyExc_TypeError, "fill_color must be a Color or color tuple");
            return -1;
        }
        self->data->box.setFillColor(color_obj->data);
        Py_DECREF(color_obj);
    }
    
    // Handle click handler
    if (click_handler && click_handler != Py_None) {
        if (!PyCallable_Check(click_handler)) {
            PyErr_SetString(PyExc_TypeError, "click must be callable");
            return -1;
        }
        self->data->click_register(click_handler);
    }
    
    // Initialize weak reference list
    self->weakreflist = NULL;
    
    // Register in Python object cache
    if (self->data->serial_number == 0) {
        self->data->serial_number = PythonObjectCache::getInstance().assignSerial();
        PyObject* weakref = PyWeakref_NewRef((PyObject*)self, NULL);
        if (weakref) {
            PythonObjectCache::getInstance().registerObject(self->data->serial_number, weakref);
            Py_DECREF(weakref);  // Cache owns the reference now
        }
    }
    
    return 0; // Success
}

PyObject* UIGrid::get_grid_size(PyUIGridObject* self, void* closure) {
    return Py_BuildValue("(ii)", self->data->grid_x, self->data->grid_y);
}

PyObject* UIGrid::get_grid_x(PyUIGridObject* self, void* closure) {
    return PyLong_FromLong(self->data->grid_x);
}

PyObject* UIGrid::get_grid_y(PyUIGridObject* self, void* closure) {
    return PyLong_FromLong(self->data->grid_y);
}

PyObject* UIGrid::get_position(PyUIGridObject* self, void* closure) {
    return Py_BuildValue("(ff)", self->data->position.x, self->data->position.y);
}

int UIGrid::set_position(PyUIGridObject* self, PyObject* value, void* closure) {
    float x, y;
    if (!PyArg_ParseTuple(value, "ff", &x, &y)) {
        PyErr_SetString(PyExc_ValueError, "Position must be a tuple of two floats");
        return -1;
    }
    self->data->position = sf::Vector2f(x, y);  // Update base class position
    self->data->box.setPosition(self->data->position);  // Sync box position
    self->data->output.setPosition(self->data->position);  // Sync output sprite position
    return 0;
}

PyObject* UIGrid::get_size(PyUIGridObject* self, void* closure) {
    auto& box = self->data->box;
    return Py_BuildValue("(ff)", box.getSize().x, box.getSize().y);
}

int UIGrid::set_size(PyUIGridObject* self, PyObject* value, void* closure) {
    float w, h;
    if (!PyArg_ParseTuple(value, "ff", &w, &h)) {
        PyErr_SetString(PyExc_ValueError, "Size must be a tuple of two floats");
        return -1;
    }
    self->data->box.setSize(sf::Vector2f(w, h));
    
    // Recreate renderTexture with new size to avoid rendering issues
    // Add some padding to handle zoom and ensure we don't cut off content
    unsigned int tex_width = static_cast<unsigned int>(w * 1.5f);
    unsigned int tex_height = static_cast<unsigned int>(h * 1.5f);
    
    // Clamp to reasonable maximum to avoid GPU memory issues
    tex_width = std::min(tex_width, 4096u);
    tex_height = std::min(tex_height, 4096u);
    
    self->data->renderTexture.create(tex_width, tex_height);
    
    return 0;
}

PyObject* UIGrid::get_center(PyUIGridObject* self, void* closure) {
    return Py_BuildValue("(ff)", self->data->center_x, self->data->center_y);
}

int UIGrid::set_center(PyUIGridObject* self, PyObject* value, void* closure) {
    float x, y;
    if (!PyArg_ParseTuple(value, "ff", &x, &y)) {
        PyErr_SetString(PyExc_ValueError, "Size must be a tuple of two floats");
        return -1;
    }
    self->data->center_x = x;
    self->data->center_y = y;
    return 0;
}

PyObject* UIGrid::get_float_member(PyUIGridObject* self, void* closure)
{
    auto member_ptr = reinterpret_cast<long>(closure);
    if (member_ptr == 0) // x
        return PyFloat_FromDouble(self->data->box.getPosition().x);
    else if (member_ptr == 1) // y
        return PyFloat_FromDouble(self->data->box.getPosition().y);
    else if (member_ptr == 2) // w
        return PyFloat_FromDouble(self->data->box.getSize().x);
    else if (member_ptr == 3) // h
        return PyFloat_FromDouble(self->data->box.getSize().y);
    else if (member_ptr == 4) // center_x
        return PyFloat_FromDouble(self->data->center_x);
    else if (member_ptr == 5) // center_y
        return PyFloat_FromDouble(self->data->center_y);
    else if (member_ptr == 6) // zoom
        return PyFloat_FromDouble(self->data->zoom);
    else
    {
        PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
        return nullptr;
    }
}

int UIGrid::set_float_member(PyUIGridObject* self, PyObject* value, void* closure)
{
    float val;
    auto member_ptr = reinterpret_cast<long>(closure);
    if (PyFloat_Check(value))
    {
        val = PyFloat_AsDouble(value);
    }
    else if (PyLong_Check(value))
    {
        val = PyLong_AsLong(value);
    }
    else
    {
        PyErr_SetString(PyExc_TypeError, "Value must be a number (int or float)");
        return -1;
    }
    if (member_ptr == 0) // x
        self->data->box.setPosition(val, self->data->box.getPosition().y);
    else if (member_ptr == 1) // y
        self->data->box.setPosition(self->data->box.getPosition().x, val);
    else if (member_ptr == 2) // w
    {
        self->data->box.setSize(sf::Vector2f(val, self->data->box.getSize().y));
        // Recreate renderTexture when width changes
        unsigned int tex_width = static_cast<unsigned int>(val * 1.5f);
        unsigned int tex_height = static_cast<unsigned int>(self->data->box.getSize().y * 1.5f);
        tex_width = std::min(tex_width, 4096u);
        tex_height = std::min(tex_height, 4096u);
        self->data->renderTexture.create(tex_width, tex_height);
    }
    else if (member_ptr == 3) // h
    {
        self->data->box.setSize(sf::Vector2f(self->data->box.getSize().x, val));
        // Recreate renderTexture when height changes
        unsigned int tex_width = static_cast<unsigned int>(self->data->box.getSize().x * 1.5f);
        unsigned int tex_height = static_cast<unsigned int>(val * 1.5f);
        tex_width = std::min(tex_width, 4096u);
        tex_height = std::min(tex_height, 4096u);
        self->data->renderTexture.create(tex_width, tex_height);
    }
    else if (member_ptr == 4) // center_x
        self->data->center_x = val;
    else if (member_ptr == 5) // center_y
        self->data->center_y = val;
    else if (member_ptr == 6) // zoom
        self->data->zoom = val;
    return 0;
}
// TODO (7DRL Day 2, item 5.) return Texture object
/*
PyObject* UIGrid::get_texture(PyUIGridObject* self, void* closure) {
    Py_INCREF(self->texture);
    return self->texture;
}
*/

PyObject* UIGrid::get_texture(PyUIGridObject* self, void* closure) {
        //return self->data->getTexture()->pyObject();
        // PyObject_GetAttrString(McRFPy_API::mcrf_module, "GridPointState")
        //PyTextureObject* obj = (PyTextureObject*)((&PyTextureType)->tp_alloc(&PyTextureType, 0));
        
        // Return None if no texture
        auto texture = self->data->getTexture();
        if (!texture) {
            Py_RETURN_NONE;
        }
        
        auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Texture");
        auto obj = (PyTextureObject*)type->tp_alloc(type, 0);
        obj->data = texture;
        return (PyObject*)obj;
}

PyObject* UIGrid::py_at(PyUIGridObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"x", "y", nullptr};
    int x = 0, y = 0;
    
    // First try to parse as two integers
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "ii", const_cast<char**>(keywords), &x, &y)) {
        PyErr_Clear();
        
        // Try to parse as a single tuple argument
        PyObject* pos_tuple = nullptr;
        if (PyArg_ParseTuple(args, "O", &pos_tuple)) {
            if (PyTuple_Check(pos_tuple) && PyTuple_Size(pos_tuple) == 2) {
                PyObject* x_obj = PyTuple_GetItem(pos_tuple, 0);
                PyObject* y_obj = PyTuple_GetItem(pos_tuple, 1);
                if (PyLong_Check(x_obj) && PyLong_Check(y_obj)) {
                    x = PyLong_AsLong(x_obj);
                    y = PyLong_AsLong(y_obj);
                } else {
                    PyErr_SetString(PyExc_TypeError, "Grid indices must be integers");
                    return NULL;
                }
            } else {
                PyErr_SetString(PyExc_TypeError, "at() takes two integers or a tuple of two integers");
                return NULL;
            }
        } else {
            PyErr_SetString(PyExc_TypeError, "at() takes two integers or a tuple of two integers");
            return NULL;
        }
    }
    
    // Range validation
    if (x < 0 || x >= self->data->grid_x) {
        PyErr_Format(PyExc_IndexError, "x index %d is out of range [0, %d)", x, self->data->grid_x);
        return NULL;
    }
    if (y < 0 || y >= self->data->grid_y) {
        PyErr_Format(PyExc_IndexError, "y index %d is out of range [0, %d)", y, self->data->grid_y);
        return NULL;
    }

    //PyUIGridPointObject* obj = (PyUIGridPointObject*)((&PyUIGridPointType)->tp_alloc(&PyUIGridPointType, 0));
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "GridPoint");
    auto obj = (PyUIGridPointObject*)type->tp_alloc(type, 0);
    //auto target = std::static_pointer_cast<UIEntity>(target);
    obj->data = &(self->data->points[x + self->data->grid_x * y]);
    obj->grid = self->data;
    return (PyObject*)obj;
}

PyObject* UIGrid::get_fill_color(PyUIGridObject* self, void* closure)
{
    auto& color = self->data->fill_color;
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Color");
    PyObject* args = Py_BuildValue("(iiii)", color.r, color.g, color.b, color.a);
    PyObject* obj = PyObject_CallObject((PyObject*)type, args);
    Py_DECREF(args);
    Py_DECREF(type);
    return obj;
}

int UIGrid::set_fill_color(PyUIGridObject* self, PyObject* value, void* closure)
{
    if (!PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Color"))) {
        PyErr_SetString(PyExc_TypeError, "fill_color must be a Color object");
        return -1;
    }
    
    PyColorObject* color = (PyColorObject*)value;
    self->data->fill_color = color->data;
    return 0;
}

PyObject* UIGrid::get_perspective(PyUIGridObject* self, void* closure)
{
    auto locked = self->data->perspective_entity.lock();
    if (locked) {
        // Check cache first to preserve derived class
        if (locked->serial_number != 0) {
            PyObject* cached = PythonObjectCache::getInstance().lookup(locked->serial_number);
            if (cached) {
                return cached;  // Already INCREF'd by lookup
            }
        }
        
        // Legacy: If the entity has a stored Python object reference
        if (locked->self != nullptr) {
            Py_INCREF(locked->self);
            return locked->self;
        }
        
        // Otherwise, create a new base Entity object
        auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity");
        auto o = (PyUIEntityObject*)type->tp_alloc(type, 0);
        if (o) {
            o->data = locked;
            o->weakreflist = NULL;
            Py_DECREF(type);
            return (PyObject*)o;
        }
        Py_XDECREF(type);
    }
    Py_RETURN_NONE;
}

int UIGrid::set_perspective(PyUIGridObject* self, PyObject* value, void* closure)
{
    if (value == Py_None) {
        // Clear perspective but keep perspective_enabled unchanged
        self->data->perspective_entity.reset();
        return 0;
    }
    
    // Extract UIEntity from PyObject
    // Get the Entity type from the module
    auto entity_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity");
    if (!entity_type) {
        PyErr_SetString(PyExc_RuntimeError, "Could not get Entity type from mcrfpy module");
        return -1;
    }
    
    if (!PyObject_IsInstance(value, entity_type)) {
        Py_DECREF(entity_type);
        PyErr_SetString(PyExc_TypeError, "perspective must be a UIEntity or None");
        return -1;
    }
    Py_DECREF(entity_type);
    
    PyUIEntityObject* entity_obj = (PyUIEntityObject*)value;
    self->data->perspective_entity = entity_obj->data;
    self->data->perspective_enabled = true;  // Enable perspective when entity assigned
    return 0;
}

PyObject* UIGrid::get_perspective_enabled(PyUIGridObject* self, void* closure)
{
    return PyBool_FromLong(self->data->perspective_enabled);
}

int UIGrid::set_perspective_enabled(PyUIGridObject* self, PyObject* value, void* closure)
{
    int enabled = PyObject_IsTrue(value);
    if (enabled == -1) {
        return -1;  // Error occurred
    }
    self->data->perspective_enabled = enabled;
    return 0;
}

// Python API implementations for TCOD functionality
PyObject* UIGrid::py_compute_fov(PyUIGridObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"x", "y", "radius", "light_walls", "algorithm", NULL};
    int x, y, radius = 0;
    int light_walls = 1;
    int algorithm = FOV_BASIC;
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "ii|ipi", const_cast<char**>(kwlist), 
                                     &x, &y, &radius, &light_walls, &algorithm)) {
        return NULL;
    }
    
    // Compute FOV
    self->data->computeFOV(x, y, radius, light_walls, (TCOD_fov_algorithm_t)algorithm);
    
    // Build list of visible cells as tuples (x, y, visible, discovered)
    PyObject* result_list = PyList_New(0);
    if (!result_list) return NULL;
    
    // Iterate through grid and collect visible cells
    for (int gy = 0; gy < self->data->grid_y; gy++) {
        for (int gx = 0; gx < self->data->grid_x; gx++) {
            if (self->data->isInFOV(gx, gy)) {
                // Create tuple (x, y, visible, discovered)
                PyObject* cell_tuple = PyTuple_New(4);
                if (!cell_tuple) {
                    Py_DECREF(result_list);
                    return NULL;
                }
                
                PyTuple_SET_ITEM(cell_tuple, 0, PyLong_FromLong(gx));
                PyTuple_SET_ITEM(cell_tuple, 1, PyLong_FromLong(gy));
                PyTuple_SET_ITEM(cell_tuple, 2, Py_True);  // visible
                PyTuple_SET_ITEM(cell_tuple, 3, Py_True);  // discovered
                Py_INCREF(Py_True);  // Need to increment ref count for True
                Py_INCREF(Py_True);
                
                // Append to list
                if (PyList_Append(result_list, cell_tuple) < 0) {
                    Py_DECREF(cell_tuple);
                    Py_DECREF(result_list);
                    return NULL;
                }
                Py_DECREF(cell_tuple);  // List now owns the reference
            }
        }
    }
    
    return result_list;
}

PyObject* UIGrid::py_is_in_fov(PyUIGridObject* self, PyObject* args)
{
    int x, y;
    if (!PyArg_ParseTuple(args, "ii", &x, &y)) {
        return NULL;
    }
    
    bool in_fov = self->data->isInFOV(x, y);
    return PyBool_FromLong(in_fov);
}

PyObject* UIGrid::py_find_path(PyUIGridObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"x1", "y1", "x2", "y2", "diagonal_cost", NULL};
    int x1, y1, x2, y2;
    float diagonal_cost = 1.41f;
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "iiii|f", const_cast<char**>(kwlist), 
                                     &x1, &y1, &x2, &y2, &diagonal_cost)) {
        return NULL;
    }
    
    std::vector<std::pair<int, int>> path = self->data->findPath(x1, y1, x2, y2, diagonal_cost);
    
    PyObject* path_list = PyList_New(path.size());
    if (!path_list) return NULL;
    
    for (size_t i = 0; i < path.size(); i++) {
        PyObject* coord = Py_BuildValue("(ii)", path[i].first, path[i].second);
        if (!coord) {
            Py_DECREF(path_list);
            return NULL;
        }
        PyList_SET_ITEM(path_list, i, coord);
    }
    
    return path_list;
}

PyObject* UIGrid::py_compute_dijkstra(PyUIGridObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"root_x", "root_y", "diagonal_cost", NULL};
    int root_x, root_y;
    float diagonal_cost = 1.41f;
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "ii|f", const_cast<char**>(kwlist), 
                                     &root_x, &root_y, &diagonal_cost)) {
        return NULL;
    }
    
    self->data->computeDijkstra(root_x, root_y, diagonal_cost);
    Py_RETURN_NONE;
}

PyObject* UIGrid::py_get_dijkstra_distance(PyUIGridObject* self, PyObject* args)
{
    int x, y;
    if (!PyArg_ParseTuple(args, "ii", &x, &y)) {
        return NULL;
    }
    
    float distance = self->data->getDijkstraDistance(x, y);
    if (distance < 0) {
        Py_RETURN_NONE;  // Invalid position
    }
    
    return PyFloat_FromDouble(distance);
}

PyObject* UIGrid::py_get_dijkstra_path(PyUIGridObject* self, PyObject* args)
{
    int x, y;
    if (!PyArg_ParseTuple(args, "ii", &x, &y)) {
        return NULL;
    }
    
    std::vector<std::pair<int, int>> path = self->data->getDijkstraPath(x, y);
    
    PyObject* path_list = PyList_New(path.size());
    for (size_t i = 0; i < path.size(); i++) {
        PyObject* pos = Py_BuildValue("(ii)", path[i].first, path[i].second);
        PyList_SetItem(path_list, i, pos);  // Steals reference
    }
    
    return path_list;
}

PyObject* UIGrid::py_compute_astar_path(PyUIGridObject* self, PyObject* args, PyObject* kwds)
{
    int x1, y1, x2, y2;
    float diagonal_cost = 1.41f;
    
    static const char* kwlist[] = {"x1", "y1", "x2", "y2", "diagonal_cost", NULL};
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "iiii|f", const_cast<char**>(kwlist), 
                                     &x1, &y1, &x2, &y2, &diagonal_cost)) {
        return NULL;
    }
    
    // Compute A* path
    std::vector<std::pair<int, int>> path = self->data->computeAStarPath(x1, y1, x2, y2, diagonal_cost);
    
    // Convert to Python list
    PyObject* path_list = PyList_New(path.size());
    for (size_t i = 0; i < path.size(); i++) {
        PyObject* pos = Py_BuildValue("(ii)", path[i].first, path[i].second);
        PyList_SetItem(path_list, i, pos);  // Steals reference
    }
    
    return path_list;
}

PyMethodDef UIGrid::methods[] = {
    {"at", (PyCFunction)UIGrid::py_at, METH_VARARGS | METH_KEYWORDS},
    {"compute_fov", (PyCFunction)UIGrid::py_compute_fov, METH_VARARGS | METH_KEYWORDS, 
     "compute_fov(x: int, y: int, radius: int = 0, light_walls: bool = True, algorithm: int = FOV_BASIC) -> List[Tuple[int, int, bool, bool]]\n\n"
     "Compute field of view from a position and return visible cells.\n\n"
     "Args:\n"
     "    x: X coordinate of the viewer\n"
     "    y: Y coordinate of the viewer\n"
     "    radius: Maximum view distance (0 = unlimited)\n"
     "    light_walls: Whether walls are lit when visible\n"
     "    algorithm: FOV algorithm to use (FOV_BASIC, FOV_DIAMOND, FOV_SHADOW, FOV_PERMISSIVE_0-8)\n\n"
     "Returns:\n"
     "    List of tuples (x, y, visible, discovered) for all visible cells:\n"
     "    - x, y: Grid coordinates\n"
     "    - visible: True (all returned cells are visible)\n"
     "    - discovered: True (FOV implies discovery)\n\n"
     "Also updates the internal FOV state for use with is_in_fov()."},
    {"is_in_fov", (PyCFunction)UIGrid::py_is_in_fov, METH_VARARGS, 
     "is_in_fov(x: int, y: int) -> bool\n\n"
     "Check if a cell is in the field of view.\n\n"
     "Args:\n"
     "    x: X coordinate to check\n"
     "    y: Y coordinate to check\n\n"
     "Returns:\n"
     "    True if the cell is visible, False otherwise\n\n"
     "Must call compute_fov() first to calculate visibility."},
    {"find_path", (PyCFunction)UIGrid::py_find_path, METH_VARARGS | METH_KEYWORDS, 
     "find_path(x1: int, y1: int, x2: int, y2: int, diagonal_cost: float = 1.41) -> List[Tuple[int, int]]\n\n"
     "Find A* path between two points.\n\n"
     "Args:\n"
     "    x1: Starting X coordinate\n"
     "    y1: Starting Y coordinate\n"
     "    x2: Target X coordinate\n"
     "    y2: Target Y coordinate\n"
     "    diagonal_cost: Cost of diagonal movement (default: 1.41)\n\n"
     "Returns:\n"
     "    List of (x, y) tuples representing the path, empty list if no path exists\n\n"
     "Uses A* algorithm with walkability from grid cells."},
    {"compute_dijkstra", (PyCFunction)UIGrid::py_compute_dijkstra, METH_VARARGS | METH_KEYWORDS, 
     "compute_dijkstra(root_x: int, root_y: int, diagonal_cost: float = 1.41) -> None\n\n"
     "Compute Dijkstra map from root position.\n\n"
     "Args:\n"
     "    root_x: X coordinate of the root/target\n"
     "    root_y: Y coordinate of the root/target\n"
     "    diagonal_cost: Cost of diagonal movement (default: 1.41)\n\n"
     "Precomputes distances from all reachable cells to the root.\n"
     "Use get_dijkstra_distance() and get_dijkstra_path() to query results.\n"
     "Useful for multiple entities pathfinding to the same target."},
    {"get_dijkstra_distance", (PyCFunction)UIGrid::py_get_dijkstra_distance, METH_VARARGS,
     "get_dijkstra_distance(x: int, y: int) -> Optional[float]\n\n"
     "Get distance from Dijkstra root to position.\n\n"
     "Args:\n"
     "    x: X coordinate to query\n"
     "    y: Y coordinate to query\n\n"
     "Returns:\n"
     "    Distance as float, or None if position is unreachable or invalid\n\n"
     "Must call compute_dijkstra() first."},
    {"get_dijkstra_path", (PyCFunction)UIGrid::py_get_dijkstra_path, METH_VARARGS,
     "get_dijkstra_path(x: int, y: int) -> List[Tuple[int, int]]\n\n"
     "Get path from position to Dijkstra root.\n\n"
     "Args:\n"
     "    x: Starting X coordinate\n"
     "    y: Starting Y coordinate\n\n"
     "Returns:\n"
     "    List of (x, y) tuples representing path to root, empty if unreachable\n\n"
     "Must call compute_dijkstra() first. Path includes start but not root position."},
    {"compute_astar_path", (PyCFunction)UIGrid::py_compute_astar_path, METH_VARARGS | METH_KEYWORDS,
     "compute_astar_path(x1: int, y1: int, x2: int, y2: int, diagonal_cost: float = 1.41) -> List[Tuple[int, int]]\n\n"
     "Compute A* path between two points.\n\n"
     "Args:\n"
     "    x1: Starting X coordinate\n"
     "    y1: Starting Y coordinate\n"
     "    x2: Target X coordinate\n"
     "    y2: Target Y coordinate\n"
     "    diagonal_cost: Cost of diagonal movement (default: 1.41)\n\n"
     "Returns:\n"
     "    List of (x, y) tuples representing the path, empty list if no path exists\n\n"
     "Alternative A* implementation. Prefer find_path() for consistency."},
    {NULL, NULL, 0, NULL}
};

// Define the PyObjectType alias for the macros
typedef PyUIGridObject PyObjectType;

// Combined methods array
PyMethodDef UIGrid_all_methods[] = {
    UIDRAWABLE_METHODS,
    {"at", (PyCFunction)UIGrid::py_at, METH_VARARGS | METH_KEYWORDS},
    {"compute_fov", (PyCFunction)UIGrid::py_compute_fov, METH_VARARGS | METH_KEYWORDS, 
     "compute_fov(x: int, y: int, radius: int = 0, light_walls: bool = True, algorithm: int = FOV_BASIC) -> List[Tuple[int, int, bool, bool]]\n\n"
     "Compute field of view from a position and return visible cells.\n\n"
     "Args:\n"
     "    x: X coordinate of the viewer\n"
     "    y: Y coordinate of the viewer\n"
     "    radius: Maximum view distance (0 = unlimited)\n"
     "    light_walls: Whether walls are lit when visible\n"
     "    algorithm: FOV algorithm to use (FOV_BASIC, FOV_DIAMOND, FOV_SHADOW, FOV_PERMISSIVE_0-8)\n\n"
     "Returns:\n"
     "    List of tuples (x, y, visible, discovered) for all visible cells:\n"
     "    - x, y: Grid coordinates\n"
     "    - visible: True (all returned cells are visible)\n"
     "    - discovered: True (FOV implies discovery)\n\n"
     "Also updates the internal FOV state for use with is_in_fov()."},
    {"is_in_fov", (PyCFunction)UIGrid::py_is_in_fov, METH_VARARGS, 
     "is_in_fov(x: int, y: int) -> bool\n\n"
     "Check if a cell is in the field of view.\n\n"
     "Args:\n"
     "    x: X coordinate to check\n"
     "    y: Y coordinate to check\n\n"
     "Returns:\n"
     "    True if the cell is visible, False otherwise\n\n"
     "Must call compute_fov() first to calculate visibility."},
    {"find_path", (PyCFunction)UIGrid::py_find_path, METH_VARARGS | METH_KEYWORDS, 
     "find_path(x1: int, y1: int, x2: int, y2: int, diagonal_cost: float = 1.41) -> List[Tuple[int, int]]\n\n"
     "Find A* path between two points.\n\n"
     "Args:\n"
     "    x1: Starting X coordinate\n"
     "    y1: Starting Y coordinate\n"
     "    x2: Target X coordinate\n"
     "    y2: Target Y coordinate\n"
     "    diagonal_cost: Cost of diagonal movement (default: 1.41)\n\n"
     "Returns:\n"
     "    List of (x, y) tuples representing the path, empty list if no path exists\n\n"
     "Uses A* algorithm with walkability from grid cells."},
    {"compute_dijkstra", (PyCFunction)UIGrid::py_compute_dijkstra, METH_VARARGS | METH_KEYWORDS, 
     "compute_dijkstra(root_x: int, root_y: int, diagonal_cost: float = 1.41) -> None\n\n"
     "Compute Dijkstra map from root position.\n\n"
     "Args:\n"
     "    root_x: X coordinate of the root/target\n"
     "    root_y: Y coordinate of the root/target\n"
     "    diagonal_cost: Cost of diagonal movement (default: 1.41)\n\n"
     "Precomputes distances from all reachable cells to the root.\n"
     "Use get_dijkstra_distance() and get_dijkstra_path() to query results.\n"
     "Useful for multiple entities pathfinding to the same target."},
    {"get_dijkstra_distance", (PyCFunction)UIGrid::py_get_dijkstra_distance, METH_VARARGS,
     "get_dijkstra_distance(x: int, y: int) -> Optional[float]\n\n"
     "Get distance from Dijkstra root to position.\n\n"
     "Args:\n"
     "    x: X coordinate to query\n"
     "    y: Y coordinate to query\n\n"
     "Returns:\n"
     "    Distance as float, or None if position is unreachable or invalid\n\n"
     "Must call compute_dijkstra() first."},
    {"get_dijkstra_path", (PyCFunction)UIGrid::py_get_dijkstra_path, METH_VARARGS,
     "get_dijkstra_path(x: int, y: int) -> List[Tuple[int, int]]\n\n"
     "Get path from position to Dijkstra root.\n\n"
     "Args:\n"
     "    x: Starting X coordinate\n"
     "    y: Starting Y coordinate\n\n"
     "Returns:\n"
     "    List of (x, y) tuples representing path to root, empty if unreachable\n\n"
     "Must call compute_dijkstra() first. Path includes start but not root position."},
    {"compute_astar_path", (PyCFunction)UIGrid::py_compute_astar_path, METH_VARARGS | METH_KEYWORDS,
     "compute_astar_path(x1: int, y1: int, x2: int, y2: int, diagonal_cost: float = 1.41) -> List[Tuple[int, int]]\n\n"
     "Compute A* path between two points.\n\n"
     "Args:\n"
     "    x1: Starting X coordinate\n"
     "    y1: Starting Y coordinate\n"
     "    x2: Target X coordinate\n"
     "    y2: Target Y coordinate\n"
     "    diagonal_cost: Cost of diagonal movement (default: 1.41)\n\n"
     "Returns:\n"
     "    List of (x, y) tuples representing the path, empty list if no path exists\n\n"
     "Alternative A* implementation. Prefer find_path() for consistency."},
    {NULL}  // Sentinel
};

PyGetSetDef UIGrid::getsetters[] = {

    // TODO - refactor into get_vector_member with field identifier values `(void*)n`
    {"grid_size", (getter)UIGrid::get_grid_size, NULL, "Grid dimensions (grid_x, grid_y)", NULL},
    {"grid_x", (getter)UIGrid::get_grid_x, NULL, "Grid x dimension", NULL},
    {"grid_y", (getter)UIGrid::get_grid_y, NULL, "Grid y dimension", NULL},
    {"position", (getter)UIGrid::get_position, (setter)UIGrid::set_position, "Position of the grid (x, y)", NULL},
    {"pos", (getter)UIDrawable::get_pos, (setter)UIDrawable::set_pos, "Position of the grid as Vector", (void*)PyObjectsEnum::UIGRID},
    {"size", (getter)UIGrid::get_size, (setter)UIGrid::set_size, "Size of the grid (width, height)", NULL},
    {"center", (getter)UIGrid::get_center, (setter)UIGrid::set_center, "Grid coordinate at the center of the Grid's view (pan)", NULL},

    {"entities", (getter)UIGrid::get_entities, NULL, "EntityCollection of entities on this grid", NULL},
    {"children", (getter)UIGrid::get_children, NULL, "UICollection of UIDrawable children (speech bubbles, effects, overlays)", NULL},

    {"x", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member, "top-left corner X-coordinate", (void*)((intptr_t)PyObjectsEnum::UIGRID << 8 | 0)},
    {"y", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member, "top-left corner Y-coordinate", (void*)((intptr_t)PyObjectsEnum::UIGRID << 8 | 1)},
    {"w", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member, "visible widget width", (void*)((intptr_t)PyObjectsEnum::UIGRID << 8 | 2)},
    {"h", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member, "visible widget height", (void*)((intptr_t)PyObjectsEnum::UIGRID << 8 | 3)},
    {"center_x", (getter)UIGrid::get_float_member, (setter)UIGrid::set_float_member, "center of the view X-coordinate", (void*)4},
    {"center_y", (getter)UIGrid::get_float_member, (setter)UIGrid::set_float_member, "center of the view Y-coordinate", (void*)5},
    {"zoom", (getter)UIGrid::get_float_member, (setter)UIGrid::set_float_member, "zoom factor for displaying the Grid", (void*)6},

    {"on_click", (getter)UIDrawable::get_click, (setter)UIDrawable::set_click,
     MCRF_PROPERTY(on_click,
         "Callable executed when object is clicked. "
         "Function receives (x, y) coordinates of click."
     ), (void*)PyObjectsEnum::UIGRID},

    {"texture", (getter)UIGrid::get_texture, NULL, "Texture of the grid", NULL}, //TODO 7DRL-day2-item5
    {"fill_color", (getter)UIGrid::get_fill_color, (setter)UIGrid::set_fill_color, "Background fill color of the grid", NULL},
    {"perspective", (getter)UIGrid::get_perspective, (setter)UIGrid::set_perspective, 
     "Entity whose perspective to use for FOV rendering (None for omniscient view). "
     "Setting an entity automatically enables perspective mode.", NULL},
    {"perspective_enabled", (getter)UIGrid::get_perspective_enabled, (setter)UIGrid::set_perspective_enabled,
     "Whether to use perspective-based FOV rendering. When True with no valid entity, "
     "all cells appear undiscovered.", NULL},
    {"z_index", (getter)UIDrawable::get_int, (setter)UIDrawable::set_int,
     MCRF_PROPERTY(z_index,
         "Z-order for rendering (lower values rendered first). "
         "Automatically triggers scene resort when changed."
     ), (void*)PyObjectsEnum::UIGRID},
    {"name", (getter)UIDrawable::get_name, (setter)UIDrawable::set_name, "Name for finding elements", (void*)PyObjectsEnum::UIGRID},
    UIDRAWABLE_GETSETTERS,
    UIDRAWABLE_PARENT_GETSETTERS(PyObjectsEnum::UIGRID),
    // #142 - Grid cell mouse events
    {"on_cell_enter", (getter)UIGrid::get_on_cell_enter, (setter)UIGrid::set_on_cell_enter,
     "Callback when mouse enters a grid cell. Called with (cell_x, cell_y).", NULL},
    {"on_cell_exit", (getter)UIGrid::get_on_cell_exit, (setter)UIGrid::set_on_cell_exit,
     "Callback when mouse exits a grid cell. Called with (cell_x, cell_y).", NULL},
    {"on_cell_click", (getter)UIGrid::get_on_cell_click, (setter)UIGrid::set_on_cell_click,
     "Callback when a grid cell is clicked. Called with (cell_x, cell_y).", NULL},
    {"hovered_cell", (getter)UIGrid::get_hovered_cell, NULL,
     "Currently hovered cell as (x, y) tuple, or None if not hovering.", NULL},
    {NULL}  /* Sentinel */
};

PyObject* UIGrid::get_entities(PyUIGridObject* self, void* closure)
{
    // Returns EntityCollection for entity management
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "EntityCollection");
    auto o = (PyUIEntityCollectionObject*)type->tp_alloc(type, 0);
    if (o) {
        o->data = self->data->entities;
        o->grid = self->data;
    }
    return (PyObject*)o;
}

PyObject* UIGrid::get_children(PyUIGridObject* self, void* closure)
{
    // Returns UICollection for UIDrawable children (speech bubbles, effects, overlays)
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "UICollection");
    auto o = (PyUICollectionObject*)type->tp_alloc(type, 0);
    Py_DECREF(type);
    if (o) {
        o->data = self->data->children;
        o->owner = self->data;  // #122: Set owner for parent tracking
    }
    return (PyObject*)o;
}

PyObject* UIGrid::repr(PyUIGridObject* self)
{
    std::ostringstream ss;
    if (!self->data) ss << "<Grid (invalid internal object)>";
    else {
        auto grid = self->data;
        auto box = grid->box;
        ss << "<Grid (x=" << box.getPosition().x << ", y=" << box.getPosition().y << ", w=" << box.getSize().x << ", h=" << box.getSize().y << ", " <<
            "center=(" << grid->center_x << ", " << grid->center_y << "), zoom=" << grid->zoom <<
            ")>";
    }
    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

/* // TODO standard pointer would need deleted, but I opted for a shared pointer. tp_dealloc currently not even defined in the PyTypeObject
void PyUIGrid_dealloc(PyUIGridObject* self) {
    delete self->data; // Clean up the allocated UIGrid object
    Py_TYPE(self)->tp_free((PyObject*)self);
}
*/

// #142 - Grid cell mouse event getters/setters
PyObject* UIGrid::get_on_cell_enter(PyUIGridObject* self, void* closure) {
    if (self->data->on_cell_enter_callable) {
        PyObject* cb = self->data->on_cell_enter_callable->borrow();
        Py_INCREF(cb);  // Return new reference, not borrowed
        return cb;
    }
    Py_RETURN_NONE;
}

int UIGrid::set_on_cell_enter(PyUIGridObject* self, PyObject* value, void* closure) {
    if (value == Py_None) {
        self->data->on_cell_enter_callable.reset();
    } else {
        self->data->on_cell_enter_callable = std::make_unique<PyClickCallable>(value);
    }
    return 0;
}

PyObject* UIGrid::get_on_cell_exit(PyUIGridObject* self, void* closure) {
    if (self->data->on_cell_exit_callable) {
        PyObject* cb = self->data->on_cell_exit_callable->borrow();
        Py_INCREF(cb);  // Return new reference, not borrowed
        return cb;
    }
    Py_RETURN_NONE;
}

int UIGrid::set_on_cell_exit(PyUIGridObject* self, PyObject* value, void* closure) {
    if (value == Py_None) {
        self->data->on_cell_exit_callable.reset();
    } else {
        self->data->on_cell_exit_callable = std::make_unique<PyClickCallable>(value);
    }
    return 0;
}

PyObject* UIGrid::get_on_cell_click(PyUIGridObject* self, void* closure) {
    if (self->data->on_cell_click_callable) {
        PyObject* cb = self->data->on_cell_click_callable->borrow();
        Py_INCREF(cb);  // Return new reference, not borrowed
        return cb;
    }
    Py_RETURN_NONE;
}

int UIGrid::set_on_cell_click(PyUIGridObject* self, PyObject* value, void* closure) {
    if (value == Py_None) {
        self->data->on_cell_click_callable.reset();
    } else {
        self->data->on_cell_click_callable = std::make_unique<PyClickCallable>(value);
    }
    return 0;
}

PyObject* UIGrid::get_hovered_cell(PyUIGridObject* self, void* closure) {
    if (self->data->hovered_cell.has_value()) {
        return Py_BuildValue("(ii)", self->data->hovered_cell->x, self->data->hovered_cell->y);
    }
    Py_RETURN_NONE;
}

// #142 - Convert screen coordinates to cell coordinates
std::optional<sf::Vector2i> UIGrid::screenToCell(sf::Vector2f screen_pos) const {
    // Get grid's global position
    sf::Vector2f global_pos = get_global_position();
    sf::Vector2f local_pos = screen_pos - global_pos;

    // Check if within grid bounds
    sf::FloatRect bounds = box.getGlobalBounds();
    if (local_pos.x < 0 || local_pos.y < 0 ||
        local_pos.x >= bounds.width || local_pos.y >= bounds.height) {
        return std::nullopt;
    }

    // Get cell size from texture or default
    float cell_width = ptex ? ptex->sprite_width : DEFAULT_CELL_WIDTH;
    float cell_height = ptex ? ptex->sprite_height : DEFAULT_CELL_HEIGHT;

    // Apply zoom
    cell_width *= zoom;
    cell_height *= zoom;

    // Calculate grid space position (account for center/pan)
    float half_width = bounds.width / 2.0f;
    float half_height = bounds.height / 2.0f;
    float grid_space_x = (local_pos.x - half_width) / zoom + center_x;
    float grid_space_y = (local_pos.y - half_height) / zoom + center_y;

    // Convert to cell coordinates
    int cell_x = static_cast<int>(std::floor(grid_space_x / (ptex ? ptex->sprite_width : DEFAULT_CELL_WIDTH)));
    int cell_y = static_cast<int>(std::floor(grid_space_y / (ptex ? ptex->sprite_height : DEFAULT_CELL_HEIGHT)));

    // Check if within valid cell range
    if (cell_x < 0 || cell_x >= grid_x || cell_y < 0 || cell_y >= grid_y) {
        return std::nullopt;
    }

    return sf::Vector2i(cell_x, cell_y);
}

// #142 - Update cell hover state and fire callbacks
void UIGrid::updateCellHover(sf::Vector2f mousepos) {
    auto new_cell = screenToCell(mousepos);

    // Check if cell changed
    if (new_cell != hovered_cell) {
        // Fire exit callback for old cell
        if (hovered_cell.has_value() && on_cell_exit_callable) {
            PyObject* args = Py_BuildValue("(ii)", hovered_cell->x, hovered_cell->y);
            PyObject* result = PyObject_CallObject(on_cell_exit_callable->borrow(), args);
            Py_DECREF(args);
            if (!result) {
                std::cerr << "Cell exit callback raised an exception:" << std::endl;
                PyErr_Print();
                PyErr_Clear();
            } else {
                Py_DECREF(result);
            }
        }

        // Fire enter callback for new cell
        if (new_cell.has_value() && on_cell_enter_callable) {
            PyObject* args = Py_BuildValue("(ii)", new_cell->x, new_cell->y);
            PyObject* result = PyObject_CallObject(on_cell_enter_callable->borrow(), args);
            Py_DECREF(args);
            if (!result) {
                std::cerr << "Cell enter callback raised an exception:" << std::endl;
                PyErr_Print();
                PyErr_Clear();
            } else {
                Py_DECREF(result);
            }
        }

        hovered_cell = new_cell;
    }
}

int UIEntityCollectionIter::init(PyUIEntityCollectionIterObject* self, PyObject* args, PyObject* kwds)
{
    PyErr_SetString(PyExc_TypeError, "UICollection cannot be instantiated: a C++ data source is required.");
    return -1;
}

PyObject* UIEntityCollectionIter::next(PyUIEntityCollectionIterObject* self)
{
    if (self->data->size() != self->start_size)
    {
        PyErr_SetString(PyExc_RuntimeError, "collection changed size during iteration");
        return NULL;
    }

    if (self->index > self->start_size - 1)
    {
        PyErr_SetNone(PyExc_StopIteration);
        return NULL;
    }
    self->index++;
    auto vec = self->data.get();
    if (!vec)
    {
        PyErr_SetString(PyExc_RuntimeError, "the collection store returned a null pointer");
        return NULL;
    }
    // Advance list iterator since Entities are stored in a list, not a vector
    auto l_begin = (*vec).begin();
    std::advance(l_begin, self->index-1);
    auto target = *l_begin;
    
    // Return the stored Python object if it exists (preserves derived types)
    if (target->self != nullptr) {
        Py_INCREF(target->self);
        return target->self;
    }
    
    // Otherwise create and return a new Python Entity object
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity");
    auto o = (PyUIEntityObject*)type->tp_alloc(type, 0);
    auto p = std::static_pointer_cast<UIEntity>(target);
    o->data = p;
    return (PyObject*)o;
}

PyObject* UIEntityCollectionIter::repr(PyUIEntityCollectionIterObject* self)
{
    std::ostringstream ss;
    if (!self->data) ss << "<UICollectionIter (invalid internal object)>";
    else {
        ss << "<UICollectionIter (" << self->data->size() << " child objects, @ index " << self->index  << ")>";
    }
    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

Py_ssize_t UIEntityCollection::len(PyUIEntityCollectionObject* self) {
    return self->data->size();
}

PyObject* UIEntityCollection::getitem(PyUIEntityCollectionObject* self, Py_ssize_t index) {
    // build a Python version of item at self->data[index]
    //  Copy pasted::
    auto vec = self->data.get();
    if (!vec)
    {
        PyErr_SetString(PyExc_RuntimeError, "the collection store returned a null pointer");
        return NULL;
    }
    while (index < 0) index += self->data->size();
    if (index > self->data->size() - 1)
    {
        PyErr_SetString(PyExc_IndexError, "EntityCollection index out of range");
        return NULL;
    }
    auto l_begin = (*vec).begin();
    std::advance(l_begin, index);
    auto target = *l_begin; //auto target = (*vec)[index];
    
    // Check cache first to preserve derived class
    if (target->serial_number != 0) {
        PyObject* cached = PythonObjectCache::getInstance().lookup(target->serial_number);
        if (cached) {
            return cached;  // Already INCREF'd by lookup
        }
    }
    
    // Legacy: If the entity has a stored Python object reference, return that to preserve derived class
    if (target->self != nullptr) {
        Py_INCREF(target->self);
        return target->self;
    }
    
    // Otherwise, create a new base Entity object
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity");
    auto o = (PyUIEntityObject*)type->tp_alloc(type, 0);
    auto p = std::static_pointer_cast<UIEntity>(target);
    o->data = p;
    return (PyObject*)o;
}

int UIEntityCollection::setitem(PyUIEntityCollectionObject* self, Py_ssize_t index, PyObject* value) {
    auto list = self->data.get();
    if (!list) {
        PyErr_SetString(PyExc_RuntimeError, "the collection store returned a null pointer");
        return -1;
    }
    
    // Handle negative indexing
    while (index < 0) index += list->size();
    
    // Bounds check
    if (index >= list->size()) {
        PyErr_SetString(PyExc_IndexError, "EntityCollection assignment index out of range");
        return -1;
    }
    
    // Get iterator to the target position
    auto it = list->begin();
    std::advance(it, index);
    
    // Handle deletion
    if (value == NULL) {
        // Clear grid reference from the entity being removed
        (*it)->grid = nullptr;
        list->erase(it);
        return 0;
    }
    
    // Type checking - must be an Entity
    if (!PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity"))) {
        PyErr_SetString(PyExc_TypeError, "EntityCollection can only contain Entity objects");
        return -1;
    }
    
    // Get the C++ object from the Python object
    PyUIEntityObject* entity = (PyUIEntityObject*)value;
    if (!entity->data) {
        PyErr_SetString(PyExc_RuntimeError, "Invalid Entity object");
        return -1;
    }
    
    // Clear grid reference from the old entity
    (*it)->grid = nullptr;
    
    // Replace the element and set grid reference
    *it = entity->data;
    entity->data->grid = self->grid;
    
    return 0;
}

int UIEntityCollection::contains(PyUIEntityCollectionObject* self, PyObject* value) {
    auto list = self->data.get();
    if (!list) {
        PyErr_SetString(PyExc_RuntimeError, "the collection store returned a null pointer");
        return -1;
    }
    
    // Type checking - must be an Entity
    if (!PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity"))) {
        // Not an Entity, so it can't be in the collection
        return 0;
    }
    
    // Get the C++ object from the Python object
    PyUIEntityObject* entity = (PyUIEntityObject*)value;
    if (!entity->data) {
        return 0;
    }
    
    // Search for the object by comparing C++ pointers
    for (const auto& ent : *list) {
        if (ent.get() == entity->data.get()) {
            return 1;  // Found
        }
    }
    
    return 0;  // Not found
}

PyObject* UIEntityCollection::concat(PyUIEntityCollectionObject* self, PyObject* other) {
    // Create a new Python list containing elements from both collections
    if (!PySequence_Check(other)) {
        PyErr_SetString(PyExc_TypeError, "can only concatenate sequence to EntityCollection");
        return NULL;
    }
    
    Py_ssize_t self_len = self->data->size();
    Py_ssize_t other_len = PySequence_Length(other);
    if (other_len == -1) {
        return NULL;  // Error already set
    }
    
    PyObject* result_list = PyList_New(self_len + other_len);
    if (!result_list) {
        return NULL;
    }
    
    // Add all elements from self
    Py_ssize_t idx = 0;
    for (const auto& entity : *self->data) {
        auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity");
        auto obj = (PyUIEntityObject*)type->tp_alloc(type, 0);
        if (obj) {
            obj->data = entity;
            PyList_SET_ITEM(result_list, idx, (PyObject*)obj);  // Steals reference
        } else {
            Py_DECREF(result_list);
            Py_DECREF(type);
            return NULL;
        }
        Py_DECREF(type);
        idx++;
    }
    
    // Add all elements from other
    for (Py_ssize_t i = 0; i < other_len; i++) {
        PyObject* item = PySequence_GetItem(other, i);
        if (!item) {
            Py_DECREF(result_list);
            return NULL;
        }
        PyList_SET_ITEM(result_list, self_len + i, item);  // Steals reference
    }
    
    return result_list;
}

PyObject* UIEntityCollection::inplace_concat(PyUIEntityCollectionObject* self, PyObject* other) {
    if (!PySequence_Check(other)) {
        PyErr_SetString(PyExc_TypeError, "can only concatenate sequence to EntityCollection");
        return NULL;
    }
    
    // First, validate ALL items in the sequence before modifying anything
    Py_ssize_t other_len = PySequence_Length(other);
    if (other_len == -1) {
        return NULL;  // Error already set
    }
    
    // Validate all items first
    for (Py_ssize_t i = 0; i < other_len; i++) {
        PyObject* item = PySequence_GetItem(other, i);
        if (!item) {
            return NULL;
        }
        
        // Type check
        if (!PyObject_IsInstance(item, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity"))) {
            Py_DECREF(item);
            PyErr_Format(PyExc_TypeError, 
                "EntityCollection can only contain Entity objects; "
                "got %s at index %zd", Py_TYPE(item)->tp_name, i);
            return NULL;
        }
        Py_DECREF(item);
    }
    
    // All items validated, now we can safely add them
    for (Py_ssize_t i = 0; i < other_len; i++) {
        PyObject* item = PySequence_GetItem(other, i);
        if (!item) {
            return NULL;  // Shouldn't happen, but be safe
        }
        
        // Use the existing append method which handles grid references
        PyObject* result = append(self, item);
        Py_DECREF(item);
        
        if (!result) {
            return NULL;  // append() failed
        }
        Py_DECREF(result);  // append returns Py_None
    }
    
    Py_INCREF(self);
    return (PyObject*)self;
}


PySequenceMethods UIEntityCollection::sqmethods = {
    .sq_length = (lenfunc)UIEntityCollection::len,
    .sq_concat = (binaryfunc)UIEntityCollection::concat,
    .sq_repeat = NULL,
    .sq_item = (ssizeargfunc)UIEntityCollection::getitem,
    .was_sq_slice = NULL,
    .sq_ass_item = (ssizeobjargproc)UIEntityCollection::setitem,
    .was_sq_ass_slice = NULL,
    .sq_contains = (objobjproc)UIEntityCollection::contains,
    .sq_inplace_concat = (binaryfunc)UIEntityCollection::inplace_concat,
    .sq_inplace_repeat = NULL
};

PyObject* UIEntityCollection::append(PyUIEntityCollectionObject* self, PyObject* o)
{
    // Type check - must be Entity
    if (!PyObject_IsInstance(o, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity")))
    {
        PyErr_SetString(PyExc_TypeError, "Only Entity objects can be added to EntityCollection");
        return NULL;
    }
    PyUIEntityObject* entity = (PyUIEntityObject*)o;

    // Remove from old grid first (if different from target grid)
    // This implements the documented "single grid only" behavior
    if (entity->data->grid && entity->data->grid != self->grid) {
        auto& old_entities = entity->data->grid->entities;
        auto it = std::find_if(old_entities->begin(), old_entities->end(),
            [entity](const std::shared_ptr<UIEntity>& e) {
                return e.get() == entity->data.get();
            });
        if (it != old_entities->end()) {
            old_entities->erase(it);
        }
    }

    // Add to this grid (if not already in it)
    if (entity->data->grid != self->grid) {
        self->data->push_back(entity->data);
        entity->data->grid = self->grid;
    }

    // Initialize gridstate if not already done
    if (entity->data->gridstate.size() == 0 && self->grid) {
        entity->data->gridstate.resize(self->grid->grid_x * self->grid->grid_y);
        // Initialize all cells as not visible/discovered
        for (auto& state : entity->data->gridstate) {
            state.visible = false;
            state.discovered = false;
        }
    }

    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* UIEntityCollection::remove(PyUIEntityCollectionObject* self, PyObject* o)
{
    // Type checking - must be an Entity
    if (!PyObject_IsInstance(o, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity")))
    {
        PyErr_SetString(PyExc_TypeError, "EntityCollection.remove requires an Entity object");
        return NULL;
    }
    
    // Get the C++ object from the Python object
    PyUIEntityObject* entity = (PyUIEntityObject*)o;
    if (!entity->data) {
        PyErr_SetString(PyExc_RuntimeError, "Invalid Entity object");
        return NULL;
    }
    
    // Get the underlying list
    auto list = self->data.get();
    if (!list) {
        PyErr_SetString(PyExc_RuntimeError, "The collection store returned a null pointer");
        return NULL;
    }
    
    // Search for the entity by comparing C++ pointers
    auto it = list->begin();
    while (it != list->end()) {
        if (it->get() == entity->data.get()) {
            // Found it - clear grid reference before removing
            (*it)->grid = nullptr;
            
            // Remove from the list
            self->data->erase(it);
            
            Py_INCREF(Py_None);
            return Py_None;
        }
        ++it;
    }
    
    // Entity not found - raise ValueError
    PyErr_SetString(PyExc_ValueError, "Entity not in EntityCollection");
    return NULL;
}

PyObject* UIEntityCollection::extend(PyUIEntityCollectionObject* self, PyObject* o)
{
    // Accept any iterable of Entity objects
    PyObject* iterator = PyObject_GetIter(o);
    if (iterator == NULL) {
        PyErr_SetString(PyExc_TypeError, "UIEntityCollection.extend requires an iterable");
        return NULL;
    }
    
    PyObject* item;
    while ((item = PyIter_Next(iterator)) != NULL) {
        // Check if item is an Entity
        if (!PyObject_IsInstance(item, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity"))) {
            Py_DECREF(item);
            Py_DECREF(iterator);
            PyErr_SetString(PyExc_TypeError, "All items in iterable must be Entity objects");
            return NULL;
        }
        
        // Add the entity to the collection
        PyUIEntityObject* entity = (PyUIEntityObject*)item;
        self->data->push_back(entity->data);
        entity->data->grid = self->grid;
        
        Py_DECREF(item);
    }
    
    Py_DECREF(iterator);
    
    // Check if iteration ended due to an error
    if (PyErr_Occurred()) {
        return NULL;
    }
    
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* UIEntityCollection::pop(PyUIEntityCollectionObject* self, PyObject* args)
{
    Py_ssize_t index = -1;  // Default to last element

    if (!PyArg_ParseTuple(args, "|n", &index)) {
        return NULL;
    }

    auto list = self->data.get();
    if (!list) {
        PyErr_SetString(PyExc_RuntimeError, "Collection data is null");
        return NULL;
    }

    if (list->empty()) {
        PyErr_SetString(PyExc_IndexError, "pop from empty EntityCollection");
        return NULL;
    }

    // Handle negative indexing
    Py_ssize_t size = static_cast<Py_ssize_t>(list->size());
    if (index < 0) {
        index += size;
    }

    if (index < 0 || index >= size) {
        PyErr_SetString(PyExc_IndexError, "pop index out of range");
        return NULL;
    }

    // Navigate to the element (std::list requires iteration)
    auto it = list->begin();
    std::advance(it, index);

    // Get the entity before removing
    std::shared_ptr<UIEntity> entity = *it;

    // Clear grid reference and remove from list
    entity->grid = nullptr;
    list->erase(it);

    // Create Python object for the entity
    PyTypeObject* entityType = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity");
    if (!entityType) {
        PyErr_SetString(PyExc_RuntimeError, "Could not find Entity type");
        return NULL;
    }

    PyUIEntityObject* py_entity = (PyUIEntityObject*)entityType->tp_alloc(entityType, 0);
    Py_DECREF(entityType);

    if (!py_entity) {
        return NULL;
    }

    py_entity->data = entity;
    py_entity->weakreflist = NULL;

    return (PyObject*)py_entity;
}

PyObject* UIEntityCollection::insert(PyUIEntityCollectionObject* self, PyObject* args)
{
    Py_ssize_t index;
    PyObject* o;

    if (!PyArg_ParseTuple(args, "nO", &index, &o)) {
        return NULL;
    }

    auto list = self->data.get();
    if (!list) {
        PyErr_SetString(PyExc_RuntimeError, "Collection data is null");
        return NULL;
    }

    // Type checking - must be an Entity
    if (!PyObject_IsInstance(o, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity"))) {
        PyErr_SetString(PyExc_TypeError, "EntityCollection.insert requires an Entity object");
        return NULL;
    }

    PyUIEntityObject* entity = (PyUIEntityObject*)o;
    if (!entity->data) {
        PyErr_SetString(PyExc_RuntimeError, "Invalid Entity object");
        return NULL;
    }

    // Handle negative indexing and clamping (Python list.insert behavior)
    Py_ssize_t size = static_cast<Py_ssize_t>(list->size());
    if (index < 0) {
        index += size;
        if (index < 0) {
            index = 0;
        }
    } else if (index > size) {
        index = size;
    }

    // Navigate to insert position
    auto it = list->begin();
    std::advance(it, index);

    // Insert and set grid reference
    list->insert(it, entity->data);
    entity->data->grid = self->grid;

    // Initialize gridstate if needed
    if (entity->data->gridstate.size() == 0 && self->grid) {
        entity->data->gridstate.resize(self->grid->grid_x * self->grid->grid_y);
        for (auto& state : entity->data->gridstate) {
            state.visible = false;
            state.discovered = false;
        }
    }

    Py_RETURN_NONE;
}

PyObject* UIEntityCollection::index_method(PyUIEntityCollectionObject* self, PyObject* value) {
    auto list = self->data.get();
    if (!list) {
        PyErr_SetString(PyExc_RuntimeError, "the collection store returned a null pointer");
        return NULL;
    }

    // Type checking - must be an Entity
    if (!PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity"))) {
        PyErr_SetString(PyExc_TypeError, "EntityCollection.index requires an Entity object");
        return NULL;
    }
    
    // Get the C++ object from the Python object
    PyUIEntityObject* entity = (PyUIEntityObject*)value;
    if (!entity->data) {
        PyErr_SetString(PyExc_RuntimeError, "Invalid Entity object");
        return NULL;
    }
    
    // Search for the object
    Py_ssize_t idx = 0;
    for (const auto& ent : *list) {
        if (ent.get() == entity->data.get()) {
            return PyLong_FromSsize_t(idx);
        }
        idx++;
    }
    
    PyErr_SetString(PyExc_ValueError, "Entity not in EntityCollection");
    return NULL;
}

PyObject* UIEntityCollection::count(PyUIEntityCollectionObject* self, PyObject* value) {
    auto list = self->data.get();
    if (!list) {
        PyErr_SetString(PyExc_RuntimeError, "the collection store returned a null pointer");
        return NULL;
    }
    
    // Type checking - must be an Entity
    if (!PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity"))) {
        // Not an Entity, so count is 0
        return PyLong_FromLong(0);
    }
    
    // Get the C++ object from the Python object
    PyUIEntityObject* entity = (PyUIEntityObject*)value;
    if (!entity->data) {
        return PyLong_FromLong(0);
    }
    
    // Count occurrences
    Py_ssize_t count = 0;
    for (const auto& ent : *list) {
        if (ent.get() == entity->data.get()) {
            count++;
        }
    }
    
    return PyLong_FromSsize_t(count);
}

PyObject* UIEntityCollection::subscript(PyUIEntityCollectionObject* self, PyObject* key) {
    if (PyLong_Check(key)) {
        // Single index - delegate to sq_item
        Py_ssize_t index = PyLong_AsSsize_t(key);
        if (index == -1 && PyErr_Occurred()) {
            return NULL;
        }
        return getitem(self, index);
    } else if (PySlice_Check(key)) {
        // Handle slice
        Py_ssize_t start, stop, step, slicelength;
        
        if (PySlice_GetIndicesEx(key, self->data->size(), &start, &stop, &step, &slicelength) < 0) {
            return NULL;
        }
        
        PyObject* result_list = PyList_New(slicelength);
        if (!result_list) {
            return NULL;
        }
        
        // Iterate through the list with slice parameters
        auto it = self->data->begin();
        for (Py_ssize_t i = 0, cur = start; i < slicelength; i++, cur += step) {
            auto cur_it = it;
            std::advance(cur_it, cur);
            
            auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity");
            auto obj = (PyUIEntityObject*)type->tp_alloc(type, 0);
            if (obj) {
                obj->data = *cur_it;
                PyList_SET_ITEM(result_list, i, (PyObject*)obj);  // Steals reference
            } else {
                Py_DECREF(result_list);
                Py_DECREF(type);
                return NULL;
            }
            Py_DECREF(type);
        }
        
        return result_list;
    } else {
        PyErr_Format(PyExc_TypeError, "EntityCollection indices must be integers or slices, not %.200s",
                     Py_TYPE(key)->tp_name);
        return NULL;
    }
}

int UIEntityCollection::ass_subscript(PyUIEntityCollectionObject* self, PyObject* key, PyObject* value) {
    if (PyLong_Check(key)) {
        // Single index - delegate to sq_ass_item
        Py_ssize_t index = PyLong_AsSsize_t(key);
        if (index == -1 && PyErr_Occurred()) {
            return -1;
        }
        return setitem(self, index, value);
    } else if (PySlice_Check(key)) {
        // Handle slice assignment/deletion
        Py_ssize_t start, stop, step, slicelength;
        
        if (PySlice_GetIndicesEx(key, self->data->size(), &start, &stop, &step, &slicelength) < 0) {
            return -1;
        }
        
        if (value == NULL) {
            // Deletion
            if (step != 1) {
                // For non-contiguous slices, delete from highest to lowest to maintain indices
                std::vector<Py_ssize_t> indices;
                for (Py_ssize_t i = 0, cur = start; i < slicelength; i++, cur += step) {
                    indices.push_back(cur);
                }
                // Sort in descending order
                std::sort(indices.begin(), indices.end(), std::greater<Py_ssize_t>());
                
                // Delete each index
                for (Py_ssize_t idx : indices) {
                    auto it = self->data->begin();
                    std::advance(it, idx);
                    (*it)->grid = nullptr;  // Clear grid reference
                    self->data->erase(it);
                }
            } else {
                // Contiguous slice - delete range
                auto it_start = self->data->begin();
                auto it_stop = self->data->begin();
                std::advance(it_start, start);
                std::advance(it_stop, stop);
                
                // Clear grid references
                for (auto it = it_start; it != it_stop; ++it) {
                    (*it)->grid = nullptr;
                }
                
                self->data->erase(it_start, it_stop);
            }
            return 0;
        } else {
            // Assignment
            if (!PySequence_Check(value)) {
                PyErr_SetString(PyExc_TypeError, "can only assign sequence to slice");
                return -1;
            }
            
            Py_ssize_t value_len = PySequence_Length(value);
            if (value_len == -1) {
                return -1;
            }
            
            // Validate all items first
            std::vector<std::shared_ptr<UIEntity>> new_items;
            for (Py_ssize_t i = 0; i < value_len; i++) {
                PyObject* item = PySequence_GetItem(value, i);
                if (!item) {
                    return -1;
                }
                
                // Type check
                if (!PyObject_IsInstance(item, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity"))) {
                    Py_DECREF(item);
                    PyErr_Format(PyExc_TypeError, 
                        "EntityCollection can only contain Entity objects; "
                        "got %s at index %zd", Py_TYPE(item)->tp_name, i);
                    return -1;
                }
                
                PyUIEntityObject* entity = (PyUIEntityObject*)item;
                Py_DECREF(item);
                new_items.push_back(entity->data);
            }
            
            // Now perform the assignment
            if (step == 1) {
                // Contiguous slice
                if (slicelength != value_len) {
                    // Need to resize - remove old items and insert new ones
                    auto it_start = self->data->begin();
                    auto it_stop = self->data->begin();
                    std::advance(it_start, start);
                    std::advance(it_stop, stop);
                    
                    // Clear grid references from old items
                    for (auto it = it_start; it != it_stop; ++it) {
                        (*it)->grid = nullptr;
                    }
                    
                    // Erase old range
                    it_start = self->data->erase(it_start, it_stop);
                    
                    // Insert new items
                    for (const auto& entity : new_items) {
                        entity->grid = self->grid;
                        it_start = self->data->insert(it_start, entity);
                        ++it_start;
                    }
                } else {
                    // Same size, just replace
                    auto it = self->data->begin();
                    std::advance(it, start);
                    for (const auto& entity : new_items) {
                        (*it)->grid = nullptr;  // Clear old grid ref
                        *it = entity;
                        entity->grid = self->grid;  // Set new grid ref
                        ++it;
                    }
                }
            } else {
                // Extended slice
                if (slicelength != value_len) {
                    PyErr_Format(PyExc_ValueError,
                        "attempt to assign sequence of size %zd to extended slice of size %zd",
                        value_len, slicelength);
                    return -1;
                }
                
                auto list_it = self->data->begin();
                for (Py_ssize_t i = 0, cur = start; i < slicelength; i++, cur += step) {
                    auto cur_it = list_it;
                    std::advance(cur_it, cur);
                    (*cur_it)->grid = nullptr;  // Clear old grid ref
                    *cur_it = new_items[i];
                    new_items[i]->grid = self->grid;  // Set new grid ref
                }
            }
            
            return 0;
        }
    } else {
        PyErr_Format(PyExc_TypeError, "EntityCollection indices must be integers or slices, not %.200s",
                     Py_TYPE(key)->tp_name);
        return -1;
    }
}

PyMappingMethods UIEntityCollection::mpmethods = {
    .mp_length = (lenfunc)UIEntityCollection::len,
    .mp_subscript = (binaryfunc)UIEntityCollection::subscript,
    .mp_ass_subscript = (objobjargproc)UIEntityCollection::ass_subscript
};

// Helper function for entity name matching with wildcards
static bool matchEntityName(const std::string& name, const std::string& pattern) {
    if (pattern.find('*') != std::string::npos) {
        if (pattern == "*") {
            return true;
        } else if (pattern.front() == '*' && pattern.back() == '*' && pattern.length() > 2) {
            std::string substring = pattern.substr(1, pattern.length() - 2);
            return name.find(substring) != std::string::npos;
        } else if (pattern.front() == '*') {
            std::string suffix = pattern.substr(1);
            return name.length() >= suffix.length() &&
                   name.compare(name.length() - suffix.length(), suffix.length(), suffix) == 0;
        } else if (pattern.back() == '*') {
            std::string prefix = pattern.substr(0, pattern.length() - 1);
            return name.compare(0, prefix.length(), prefix) == 0;
        }
        return name == pattern;
    }
    return name == pattern;
}

PyObject* UIEntityCollection::find(PyUIEntityCollectionObject* self, PyObject* args, PyObject* kwds) {
    const char* name = nullptr;

    static const char* kwlist[] = {"name", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "s", const_cast<char**>(kwlist), &name)) {
        return NULL;
    }

    auto list = self->data.get();
    if (!list) {
        PyErr_SetString(PyExc_RuntimeError, "Collection data is null");
        return NULL;
    }

    std::string pattern(name);
    bool has_wildcard = (pattern.find('*') != std::string::npos);

    // Get the Entity type for creating Python objects
    PyTypeObject* entityType = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity");
    if (!entityType) {
        PyErr_SetString(PyExc_RuntimeError, "Could not find Entity type");
        return NULL;
    }

    if (has_wildcard) {
        // Return list of all matches
        PyObject* results = PyList_New(0);
        if (!results) {
            Py_DECREF(entityType);
            return NULL;
        }

        for (auto& entity : *list) {
            // Entity name is stored in sprite.name
            if (matchEntityName(entity->sprite.name, pattern)) {
                PyUIEntityObject* py_entity = (PyUIEntityObject*)entityType->tp_alloc(entityType, 0);
                if (!py_entity) {
                    Py_DECREF(results);
                    Py_DECREF(entityType);
                    return NULL;
                }
                py_entity->data = entity;
                py_entity->weakreflist = NULL;

                if (PyList_Append(results, (PyObject*)py_entity) < 0) {
                    Py_DECREF(py_entity);
                    Py_DECREF(results);
                    Py_DECREF(entityType);
                    return NULL;
                }
                Py_DECREF(py_entity);  // PyList_Append increfs
            }
        }

        Py_DECREF(entityType);
        return results;
    } else {
        // Return first exact match or None
        for (auto& entity : *list) {
            if (entity->sprite.name == pattern) {
                PyUIEntityObject* py_entity = (PyUIEntityObject*)entityType->tp_alloc(entityType, 0);
                if (!py_entity) {
                    Py_DECREF(entityType);
                    return NULL;
                }
                py_entity->data = entity;
                py_entity->weakreflist = NULL;
                Py_DECREF(entityType);
                return (PyObject*)py_entity;
            }
        }

        Py_DECREF(entityType);
        Py_RETURN_NONE;
    }
}

PyMethodDef UIEntityCollection::methods[] = {
    {"append", (PyCFunction)UIEntityCollection::append, METH_O,
     "append(entity)\n\n"
     "Add an entity to the end of the collection."},
    {"extend", (PyCFunction)UIEntityCollection::extend, METH_O,
     "extend(iterable)\n\n"
     "Add all entities from an iterable to the collection."},
    {"insert", (PyCFunction)UIEntityCollection::insert, METH_VARARGS,
     "insert(index, entity)\n\n"
     "Insert entity at index. Like list.insert(), indices past the end append."},
    {"remove", (PyCFunction)UIEntityCollection::remove, METH_O,
     "remove(entity)\n\n"
     "Remove first occurrence of entity. Raises ValueError if not found."},
    {"pop", (PyCFunction)UIEntityCollection::pop, METH_VARARGS,
     "pop([index]) -> entity\n\n"
     "Remove and return entity at index (default: last entity)."},
    {"index", (PyCFunction)UIEntityCollection::index_method, METH_O,
     "index(entity) -> int\n\n"
     "Return index of first occurrence of entity. Raises ValueError if not found."},
    {"count", (PyCFunction)UIEntityCollection::count, METH_O,
     "count(entity) -> int\n\n"
     "Count occurrences of entity in the collection."},
    {"find", (PyCFunction)UIEntityCollection::find, METH_VARARGS | METH_KEYWORDS,
     "find(name) -> entity or list\n\n"
     "Find entities by name.\n\n"
     "Args:\n"
     "    name (str): Name to search for. Supports wildcards:\n"
     "        - 'exact' for exact match (returns single entity or None)\n"
     "        - 'prefix*' for starts-with match (returns list)\n"
     "        - '*suffix' for ends-with match (returns list)\n"
     "        - '*substring*' for contains match (returns list)\n\n"
     "Returns:\n"
     "    Single entity if exact match, list if wildcard, None if not found."},
    {NULL, NULL, 0, NULL}
};

PyObject* UIEntityCollection::repr(PyUIEntityCollectionObject* self)
{
    std::ostringstream ss;
    if (!self->data) ss << "<UICollection (invalid internal object)>";
    else {
        ss << "<UICollection (" << self->data->size() << " child objects)>";
    }
    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

int UIEntityCollection::init(PyUIEntityCollectionObject* self, PyObject* args, PyObject* kwds)
{
    PyErr_SetString(PyExc_TypeError, "EntityCollection cannot be instantiated: a C++ data source is required.");
    return -1;
}

PyObject* UIEntityCollection::iter(PyUIEntityCollectionObject* self)
{
    // Get the iterator type from the module to ensure we have the registered version
    PyTypeObject* iterType = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "UIEntityCollectionIter");
    if (!iterType) {
        PyErr_SetString(PyExc_RuntimeError, "Could not find UIEntityCollectionIter type in module");
        return NULL;
    }
    
    // Allocate new iterator instance
    PyUIEntityCollectionIterObject* iterObj = (PyUIEntityCollectionIterObject*)iterType->tp_alloc(iterType, 0);
    
    if (iterObj == NULL) {
        Py_DECREF(iterType);
        return NULL;  // Failed to allocate memory for the iterator object
    }

    iterObj->data = self->data;
    iterObj->index = 0;
    iterObj->start_size = self->data->size();

    Py_DECREF(iterType);
    return (PyObject*)iterObj;
}

// Property system implementation for animations
bool UIGrid::setProperty(const std::string& name, float value) {
    if (name == "x") {
        position.x = value;
        box.setPosition(position);
        output.setPosition(position);
        return true;
    }
    else if (name == "y") {
        position.y = value;
        box.setPosition(position);
        output.setPosition(position);
        return true;
    }
    else if (name == "w" || name == "width") {
        box.setSize(sf::Vector2f(value, box.getSize().y));
        output.setTextureRect(sf::IntRect(0, 0, box.getSize().x, box.getSize().y));
        return true;
    }
    else if (name == "h" || name == "height") {
        box.setSize(sf::Vector2f(box.getSize().x, value));
        output.setTextureRect(sf::IntRect(0, 0, box.getSize().x, box.getSize().y));
        return true;
    }
    else if (name == "center_x") {
        center_x = value;
        return true;
    }
    else if (name == "center_y") {
        center_y = value;
        return true;
    }
    else if (name == "zoom") {
        zoom = value;
        return true;
    }
    else if (name == "z_index") {
        z_index = static_cast<int>(value);
        return true;
    }
    else if (name == "fill_color.r") {
        fill_color.r = static_cast<uint8_t>(std::max(0.0f, std::min(255.0f, value)));
        return true;
    }
    else if (name == "fill_color.g") {
        fill_color.g = static_cast<uint8_t>(std::max(0.0f, std::min(255.0f, value)));
        return true;
    }
    else if (name == "fill_color.b") {
        fill_color.b = static_cast<uint8_t>(std::max(0.0f, std::min(255.0f, value)));
        return true;
    }
    else if (name == "fill_color.a") {
        fill_color.a = static_cast<uint8_t>(std::max(0.0f, std::min(255.0f, value)));
        return true;
    }
    return false;
}

bool UIGrid::setProperty(const std::string& name, const sf::Vector2f& value) {
    if (name == "position") {
        position = value;
        box.setPosition(position);
        output.setPosition(position);
        return true;
    }
    else if (name == "size") {
        box.setSize(value);
        output.setTextureRect(sf::IntRect(0, 0, box.getSize().x, box.getSize().y));
        return true;
    }
    else if (name == "center") {
        center_x = value.x;
        center_y = value.y;
        return true;
    }
    return false;
}

bool UIGrid::getProperty(const std::string& name, float& value) const {
    if (name == "x") {
        value = position.x;
        return true;
    }
    else if (name == "y") {
        value = position.y;
        return true;
    }
    else if (name == "w" || name == "width") {
        value = box.getSize().x;
        return true;
    }
    else if (name == "h" || name == "height") {
        value = box.getSize().y;
        return true;
    }
    else if (name == "center_x") {
        value = center_x;
        return true;
    }
    else if (name == "center_y") {
        value = center_y;
        return true;
    }
    else if (name == "zoom") {
        value = zoom;
        return true;
    }
    else if (name == "z_index") {
        value = static_cast<float>(z_index);
        return true;
    }
    else if (name == "fill_color.r") {
        value = static_cast<float>(fill_color.r);
        return true;
    }
    else if (name == "fill_color.g") {
        value = static_cast<float>(fill_color.g);
        return true;
    }
    else if (name == "fill_color.b") {
        value = static_cast<float>(fill_color.b);
        return true;
    }
    else if (name == "fill_color.a") {
        value = static_cast<float>(fill_color.a);
        return true;
    }
    return false;
}

bool UIGrid::getProperty(const std::string& name, sf::Vector2f& value) const {
    if (name == "position") {
        value = position;
        return true;
    }
    else if (name == "size") {
        value = box.getSize();
        return true;
    }
    else if (name == "center") {
        value = sf::Vector2f(center_x, center_y);
        return true;
    }
    return false;
}
