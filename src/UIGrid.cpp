#include "UIGrid.h"
#include "UIGridView.h"  // #252: GridView shim
#include "UIGridPathfinding.h"  // New pathfinding API
#include "GameEngine.h"
#include "McRFPy_API.h"
#include "PythonObjectCache.h"
#include "PyAlignment.h"
#include "UIEntity.h"
#include "Profiler.h"
#include "PyFOV.h"
#include "PyPositionHelper.h"  // For standardized position argument parsing
#include "PyVector.h"  // #179, #181 - For Vector return types
// PyHeightMap.h moved to UIGridPyMethods.cpp
#include "PyShader.h"  // #106: Shader support
#include "PyUniformCollection.h"  // #106: Uniform collection support
#include "PyMouseButton.h"  // For MouseButton enum
#include "PyInputState.h"   // For InputState enum
#include <algorithm>
#include <cmath>    // #142 - for std::floor, std::isnan
#include <cstring>  // #150 - for strcmp
#include <limits>   // #169 - for std::numeric_limits
// UIDrawable methods now in UIBase.h
// UIEntityCollection code moved to UIEntityCollection.cpp

UIGrid::UIGrid()
: GridData(),  // Initialize data layer (entities, children, FOV defaults)
  zoom(1.0f), center_x(0.0f), center_y(0.0f), ptex(nullptr),
  fill_color(8, 8, 8, 255)
{
    // Initialize box with safe defaults
    box.setSize(sf::Vector2f(0, 0));
    position = sf::Vector2f(0, 0);  // Set base class position
    box.setPosition(position);      // Sync box position
    box.setFillColor(sf::Color(0, 0, 0, 0));

    // #228 - Initialize render texture to game resolution (small default until game init)
    renderTexture.create(1, 1);
    renderTextureSize = {1, 1};

    // Initialize output sprite
    output.setTextureRect(sf::IntRect(0, 0, 0, 0));
    output.setPosition(0, 0);
    output.setTexture(renderTexture.getTexture());

    // Points vector starts empty (grid_w * grid_h = 0)
    // TCOD map will be created when grid is resized
}

UIGrid::UIGrid(int gx, int gy, std::shared_ptr<PyTexture> _ptex, sf::Vector2f _xy, sf::Vector2f _wh)
: GridData(),  // Initialize data layer
  zoom(1.0f),
  ptex(_ptex),
  fill_color(8, 8, 8, 255)
{
    // Use texture dimensions if available, otherwise use defaults
    int cell_width = _ptex ? _ptex->sprite_width : DEFAULT_CELL_WIDTH;
    int cell_height = _ptex ? _ptex->sprite_height : DEFAULT_CELL_HEIGHT;

    // #313: mirror into the GridData base so the data layer (and entities
    // holding shared_ptr<GridData>) can do tile<->pixel math. ptex is
    // write-once (ctor only), so this never goes stale.
    cell_width_px = cell_width;
    cell_height_px = cell_height;

    center_x = (gx/2) * cell_width;
    center_y = (gy/2) * cell_height;

    box.setSize(_wh);
    position = _xy;               // Set base class position
    box.setPosition(position);    // Sync box position

    box.setFillColor(sf::Color(0,0,0,0));
    // #228 - create renderTexture sized to game resolution (dynamically resized as needed)
    ensureRenderTextureSize();

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

    // Initialize grid storage, TCOD map, and sync (#252: delegated to GridData)
    initStorage(gx, gy, static_cast<GridData*>(this));
}

void UIGrid::update() {}


void UIGrid::render(sf::Vector2f offset, sf::RenderTarget& target)
{
    // Profile total grid rendering time
    ScopedTimer gridTimer(Resources::game->metrics.gridRenderTime);

    // Check visibility
    if (!visible) return;

    // #228 - Ensure renderTexture matches current game resolution
    ensureRenderTextureSize();

    if (!render_dirty && !composite_dirty) {
        if (shader && shader->shader) {
            sf::Vector2f resolution(box.getSize().x, box.getSize().y);
            PyShader::applyEngineUniforms(*shader->shader, resolution);

            // Apply user uniforms
            if (uniforms) {
                uniforms->applyTo(*shader->shader);
            }

            target.draw(output, shader->shader.get());
        }
        else
        {
            output.setPosition(box.getPosition() + offset);
            target.draw(output);
            return;
        }
    }

    // TODO: Apply opacity to output sprite

    // Get cell dimensions - use texture if available, otherwise defaults
    int cell_width = ptex ? ptex->sprite_width : DEFAULT_CELL_WIDTH;
    int cell_height = ptex ? ptex->sprite_height : DEFAULT_CELL_HEIGHT;

    // Determine if we need camera rotation handling
    bool has_camera_rotation = (camera_rotation != 0.0f);
    float grid_w_px = box.getSize().x;
    float grid_h_px = box.getSize().y;

    // Calculate AABB for rotated view (if camera rotation is active)
    float rad = camera_rotation * (M_PI / 180.0f);
    float cos_r = std::cos(rad);
    float sin_r = std::sin(rad);
    float abs_cos = std::abs(cos_r);
    float abs_sin = std::abs(sin_r);

    // AABB dimensions of the rotated viewport
    float aabb_w = grid_w_px * abs_cos + grid_h_px * abs_sin;
    float aabb_h = grid_w_px * abs_sin + grid_h_px * abs_cos;

    // Choose which texture to render to
    sf::RenderTexture* activeTexture = &renderTexture;

    if (has_camera_rotation) {
        // Ensure rotation texture is large enough
        unsigned int needed_size = static_cast<unsigned int>(std::max(aabb_w, aabb_h) + 1);
        if (!rotationTexture) rotationTexture = std::make_unique<sf::RenderTexture>();  // #338
        if (rotationTextureSize < needed_size) {
            rotationTexture->create(needed_size, needed_size);
            rotationTextureSize = needed_size;
        }
        activeTexture = rotationTexture.get();
        activeTexture->clear(fill_color);
    } else {
        output.setPosition(box.getPosition() + offset);
        output.setTextureRect(sf::IntRect(0, 0, grid_w_px, grid_h_px));
        renderTexture.clear(fill_color);
    }

    // Calculate visible tile range
    // For camera rotation, use AABB dimensions; otherwise use grid dimensions
    float render_w = has_camera_rotation ? aabb_w : grid_w_px;
    float render_h = has_camera_rotation ? aabb_h : grid_h_px;

    float center_x_sq = center_x / cell_width;
    float center_y_sq = center_y / cell_height;

    float width_sq = render_w / (cell_width * zoom);
    float height_sq = render_h / (cell_height * zoom);
    float left_edge = center_x_sq - (width_sq / 2.0);
    float top_edge = center_y_sq - (height_sq / 2.0);

    int left_spritepixels = center_x - (render_w / 2.0 / zoom);
    int top_spritepixels = center_y - (render_h / 2.0 / zoom);

    int x_limit = left_edge + width_sq + 2;
    if (x_limit > grid_w) x_limit = grid_w;

    int y_limit = top_edge + height_sq + 2;
    if (y_limit > grid_h) y_limit = grid_h;

    // #150 - Layers are now the sole source of grid rendering (base layer removed)
    // Render layers with z_index <= 0 (below entities)
    sortLayers();
    for (auto& layer : layers) {
        if (layer->z_index > 0) break;  // Stop at layers that go above entities (#257)
        layer->render(*activeTexture, left_spritepixels, top_spritepixels,
                     left_edge, top_edge, x_limit, y_limit, zoom, cell_width, cell_height);
    }

    // middle layer - entities
    // disabling entity rendering until I can render their UISprite inside the rendertexture (not directly to window)
    {
        ScopedTimer entityTimer(Resources::game->metrics.entityRenderTime);
        int entitiesRendered = 0;
        int totalEntities = entities->size();

        for (auto e : *entities) {
            // #236: Account for multi-tile entity size in frustum culling
            int margin = 2;
            if (e->position.x + e->tile_width < left_edge - margin ||
                e->position.x >= left_edge + width_sq + margin ||
                e->position.y + e->tile_height < top_edge - margin ||
                e->position.y >= top_edge + height_sq + margin) {
                continue; // Skip this entity as it's not visible
            }

            auto pixel_pos = sf::Vector2f(
                (e->position.x*cell_width - left_spritepixels + e->sprite_offset.x) * zoom,
                (e->position.y*cell_height - top_spritepixels + e->sprite_offset.y) * zoom );

            // #237: Composite sprite grid - render per-tile sprites
            if (!e->sprite_grid.empty() && e->sprite.getTexture()) {
                auto tex = e->sprite.getTexture();
                for (int dy = 0; dy < e->tile_height; dy++) {
                    for (int dx = 0; dx < e->tile_width; dx++) {
                        int idx = e->sprite_grid[dy * e->tile_width + dx];
                        if (idx < 0) continue;
                        auto tile_pos = sf::Vector2f(
                            pixel_pos.x + dx * cell_width * zoom,
                            pixel_pos.y + dy * cell_height * zoom);
                        auto spr = tex->sprite(idx, tile_pos, sf::Vector2f(zoom, zoom));
                        activeTexture->draw(spr);
                    }
                }
            } else {
                // Single sprite path
                auto& drawent = e->sprite;
                drawent.setScale(sf::Vector2f(zoom, zoom));
                drawent.render(pixel_pos, *activeTexture);
            }

            entitiesRendered++;
        }

        // Record entity rendering stats
        Resources::game->metrics.entitiesRendered += entitiesRendered;
        Resources::game->metrics.totalEntities += totalEntities;
    }

    // #147 - Render dynamic layers with z_index > 0 (above entities)
    for (auto& layer : layers) {
        if (layer->z_index <= 0) continue;  // Skip layers at or below entities (#257)
        layer->render(*activeTexture, left_spritepixels, top_spritepixels,
                     left_edge, top_edge, x_limit, y_limit, zoom, cell_width, cell_height);
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

            child->render(pixel_pos, *activeTexture);
        }
    }

    // #355: the perspective/FOV overlay is drawn by UIGridView::render, which owns
    // the perspective state. UIGrid (the internal _GridData) no longer duplicates it.

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

    // Finalize the active texture
    activeTexture->display();

    // If camera rotation was used, rotate and blit to the grid's renderTexture
    if (has_camera_rotation) {
        // Clear the final renderTexture with fill color
        renderTexture.clear(fill_color);

        // Create sprite from the larger rotated texture
        sf::Sprite rotatedSprite(rotationTexture->getTexture());

        // Set origin to center of the rendered content
        float tex_center_x = aabb_w / 2.0f;
        float tex_center_y = aabb_h / 2.0f;
        rotatedSprite.setOrigin(tex_center_x, tex_center_y);

        // Apply rotation
        rotatedSprite.setRotation(camera_rotation);

        // Position so the rotated center lands at the viewport center
        rotatedSprite.setPosition(grid_w_px / 2.0f, grid_h_px / 2.0f);

        // Set texture rect to only use the AABB portion (texture may be larger)
        rotatedSprite.setTextureRect(sf::IntRect(0, 0, static_cast<int>(aabb_w), static_cast<int>(aabb_h)));

        // Draw to the grid's renderTexture (which clips to grid bounds)
        renderTexture.draw(rotatedSprite);
        renderTexture.display();

        // Set up output sprite
        output.setPosition(box.getPosition() + offset);
        output.setTextureRect(sf::IntRect(0, 0, grid_w_px, grid_h_px));
    }

    // Apply viewport rotation (UIDrawable::rotation) to the entire grid widget
    if (rotation != 0.0f) {
        output.setOrigin(origin);
        output.setRotation(rotation);
        // Adjust position to account for origin offset
        output.setPosition(box.getPosition() + offset + origin);
    } else {
        output.setOrigin(0, 0);
        output.setRotation(0);
        // Position already set above
    }

    // #106: Apply shader if set
    if (shader && shader->shader) {
        sf::Vector2f resolution(box.getSize().x, box.getSize().y);
        PyShader::applyEngineUniforms(*shader->shader, resolution);

        // Apply user uniforms
        if (uniforms) {
            uniforms->applyTo(*shader->shader);
        }

        target.draw(output, shader->shader.get());
    } else {
        target.draw(output);
    }
}

// at(), syncTCODMap(), computeFOV(), isInFOV(), layer management methods
// are now in GridData.cpp (#252)

UIGrid::~UIGrid()
{
    // GridData destructor handles TCOD map and Dijkstra cleanup
}

void UIGrid::ensureRenderTextureSize()
{
    // Get game resolution (or use sensible defaults during early init)
    sf::Vector2u resolution{1920, 1080};
    if (Resources::game) {
        resolution = Resources::game->getGameResolution();
    }

    // Clamp to reasonable maximum (SFML texture size limits)
    unsigned int required_w = std::min(resolution.x, 4096u);
    unsigned int required_h = std::min(resolution.y, 4096u);

    // Only recreate if size changed
    if (renderTextureSize.x != required_w || renderTextureSize.y != required_h) {
        renderTexture.create(required_w, required_h);
        renderTextureSize = {required_w, required_h};
        output.setTexture(renderTexture.getTexture());
    }
}

PyObjectsEnum UIGrid::derived_type()
{
    return PyObjectsEnum::UIGRID;
}

// Pathfinding methods moved to UIGridPathfinding.cpp
// - Grid.find_path() returns AStarPath objects
// - Grid.get_dijkstra_map() returns DijkstraMap objects (cached)

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

    // Notify aligned children to recalculate their positions
    if (children) {
        for (auto& child : *children) {
            if (child->getAlignment() != AlignmentType::NONE) {
                child->applyAlignment();
            }
        }
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

UIDrawable* UIGrid::click_at(sf::Vector2f)
{
    // #355: a bare _GridData is never an input target -- the scene graph holds
    // UIGridView, which owns the camera and all cell/child/entity hit testing.
    // #361 removes UIDrawable from GridData entirely, which deletes this override.
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
    PyObject* layers_obj = nullptr;  // #150 - layers dict
    // #169 - Use NaN as sentinel to detect if user provided center values
    float center_x = std::numeric_limits<float>::quiet_NaN();
    float center_y = std::numeric_limits<float>::quiet_NaN();
    float zoom = 1.0f;
    // perspective is now handled via properties, not init args
    int visible = 1;
    float opacity = 1.0f;
    int z_index = 0;
    const char* name = nullptr;
    float x = 0.0f, y = 0.0f, w = 0.0f, h = 0.0f;
    int grid_w = 2, grid_h = 2;  // Default to 2x2 grid
    PyObject* align_obj = nullptr;  // Alignment enum or None
    float margin = 0.0f;
    float horiz_margin = -1.0f;
    float vert_margin = -1.0f;

    // Keywords list matches the new spec: positional args first, then all keyword args
    static const char* kwlist[] = {
        "pos", "size", "grid_size", "texture",  // Positional args (as per spec)
        // Keyword-only args
        "fill_color", "on_click", "center_x", "center_y", "zoom",
        "visible", "opacity", "z_index", "name", "x", "y", "w", "h", "grid_w", "grid_h",
        "layers",  // #150 - layers dict parameter
        "align", "margin", "horiz_margin", "vert_margin",
        nullptr
    };

    // Parse arguments with | for optional positional args
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OOOOOOfffifizffffiiOOfff", const_cast<char**>(kwlist),
                                     &pos_obj, &size_obj, &grid_size_obj, &textureObj,  // Positional
                                     &fill_color, &click_handler, &center_x, &center_y, &zoom,
                                     &visible, &opacity, &z_index, &name, &x, &y, &w, &h, &grid_w, &grid_h,
                                     &layers_obj,
                                     &align_obj, &margin, &horiz_margin, &vert_margin)) {
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
    
    // Handle grid_size argument (can be tuple or use grid_w/grid_h keywords)
    if (grid_size_obj) {
        if (PyTuple_Check(grid_size_obj) && PyTuple_Size(grid_size_obj) == 2) {
            PyObject* gx_val = PyTuple_GetItem(grid_size_obj, 0);
            PyObject* gy_val = PyTuple_GetItem(grid_size_obj, 1);
            if (PyLong_Check(gx_val) && PyLong_Check(gy_val)) {
                grid_w = PyLong_AsLong(gx_val);
                grid_h = PyLong_AsLong(gy_val);
            } else {
                PyErr_SetString(PyExc_TypeError, "grid_size tuple must contain integers");
                return -1;
            }
        } else {
            PyErr_SetString(PyExc_TypeError, "grid_size must be a tuple (grid_w, grid_h)");
            return -1;
        }
    }
    
    // Validate grid dimensions
    if (grid_w <= 0 || grid_h <= 0) {
        PyErr_SetString(PyExc_ValueError, "Grid dimensions must be positive integers");
        return -1;
    }

    // #212 - Validate against GRID_MAX
    if (grid_w > GRID_MAX || grid_h > GRID_MAX) {
        PyErr_Format(PyExc_ValueError,
            "Grid dimensions cannot exceed %d (got %dx%d)",
            GRID_MAX, grid_w, grid_h);
        return -1;
    }

    // Handle texture argument
    std::shared_ptr<PyTexture> texture_ptr = nullptr;
    if (textureObj && textureObj != Py_None) {
        if (!PyObject_IsInstance(textureObj, (PyObject*)&mcrfpydef::PyTextureType)) {
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
        w = grid_w * texture_ptr->sprite_width;
        h = grid_h * texture_ptr->sprite_height;
    } else if (!size_obj) {
        w = grid_w * 16.0f;  // Default tile size
        h = grid_h * 16.0f;
    }

    // Create the grid
    self->data = std::make_shared<UIGrid>(grid_w, grid_h, texture_ptr, 
                                          sf::Vector2f(x, y), sf::Vector2f(w, h));
    
    // Set additional properties
    self->data->zoom = zoom;  // Set zoom first, needed for default center calculation

    // #169 - Calculate default center if not provided by user
    // Default: tile (0,0) at top-left of widget
    if (std::isnan(center_x)) {
        // Center = half widget size (in pixels), so tile 0,0 appears at top-left
        center_x = w / (2.0f * zoom);
    }
    if (std::isnan(center_y)) {
        center_y = h / (2.0f * zoom);
    }
    self->data->center_x = center_x;
    self->data->center_y = center_y;
    // #355: perspective lives on UIGridView (the object that renders the overlay).
    self->data->visible = visible;
    self->data->opacity = opacity;
    self->data->z_index = z_index;
    if (name) {
        self->data->name = std::string(name);
    }

    // Process alignment arguments
    UIDRAWABLE_PROCESS_ALIGNMENT(self->data, align_obj, margin, horiz_margin, vert_margin);

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

    // #150 - Handle layers parameter
    // Default: single TileLayer named "tilesprite" when layers not provided
    // Empty list/None: no rendering layers (entity storage + pathfinding only)
    // List of layer objects: add each layer with lazy allocation
    if (layers_obj == nullptr) {
        // Default layer: single TileLayer named "tilesprite" (z_index -1 = below entities)
        self->data->addTileLayer(-1, texture_ptr, "tilesprite");
    } else if (layers_obj != Py_None) {
        // Accept any iterable of layer objects
        PyObject* iterator = PyObject_GetIter(layers_obj);
        if (!iterator) {
            PyErr_SetString(PyExc_TypeError, "layers must be an iterable of ColorLayer or TileLayer objects");
            return -1;
        }

        auto* color_layer_type = (PyObject*)&mcrfpydef::PyColorLayerType;
        auto* tile_layer_type = (PyObject*)&mcrfpydef::PyTileLayerType;

        PyObject* item;
        while ((item = PyIter_Next(iterator)) != NULL) {
            std::shared_ptr<GridLayer> layer;

            if (PyObject_IsInstance(item, color_layer_type)) {
                PyColorLayerObject* py_layer = (PyColorLayerObject*)item;
                if (!py_layer->data) {
                    Py_DECREF(item);
                    Py_DECREF(iterator);
                    PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
                    return -1;
                }

                // Check if already attached to another grid
                if (py_layer->grid) {
                    Py_DECREF(item);
                    Py_DECREF(iterator);
                    PyErr_SetString(PyExc_ValueError, "Layer is already attached to another Grid");
                    return -1;
                }

                layer = py_layer->data;

                // Check for protected names
                if (!layer->name.empty() && UIGrid::isProtectedLayerName(layer->name)) {
                    Py_DECREF(item);
                    Py_DECREF(iterator);
                    PyErr_Format(PyExc_ValueError, "Layer name '%s' is reserved", layer->name.c_str());
                    return -1;
                }

                // Handle name collision
                if (!layer->name.empty()) {
                    auto existing = self->data->getLayerByName(layer->name);
                    if (existing) {
                        existing->parent_grid = nullptr;
                        self->data->removeLayer(existing);
                    }
                }

                // Lazy allocation: resize if layer is (0,0)
                if (layer->grid_x == 0 && layer->grid_y == 0) {
                    layer->resize(self->data->grid_w, self->data->grid_h);
                } else if (layer->grid_x != self->data->grid_w || layer->grid_y != self->data->grid_h) {
                    Py_DECREF(item);
                    Py_DECREF(iterator);
                    PyErr_Format(PyExc_ValueError,
                        "Layer size (%d, %d) does not match Grid size (%d, %d)",
                        layer->grid_x, layer->grid_y, self->data->grid_w, self->data->grid_h);
                    return -1;
                }

                // Link to grid
                layer->parent_grid = self->data.get();
                self->data->layers.push_back(layer);
                py_layer->grid = self->data;

            } else if (PyObject_IsInstance(item, tile_layer_type)) {
                PyTileLayerObject* py_layer = (PyTileLayerObject*)item;
                if (!py_layer->data) {
                    Py_DECREF(item);
                    Py_DECREF(iterator);
                    PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
                    return -1;
                }

                // Check if already attached to another grid
                if (py_layer->grid) {
                    Py_DECREF(item);
                    Py_DECREF(iterator);
                    PyErr_SetString(PyExc_ValueError, "Layer is already attached to another Grid");
                    return -1;
                }

                layer = py_layer->data;

                // Check for protected names
                if (!layer->name.empty() && UIGrid::isProtectedLayerName(layer->name)) {
                    Py_DECREF(item);
                    Py_DECREF(iterator);
                    PyErr_Format(PyExc_ValueError, "Layer name '%s' is reserved", layer->name.c_str());
                    return -1;
                }

                // Handle name collision
                if (!layer->name.empty()) {
                    auto existing = self->data->getLayerByName(layer->name);
                    if (existing) {
                        existing->parent_grid = nullptr;
                        self->data->removeLayer(existing);
                    }
                }

                // Lazy allocation: resize if layer is (0,0)
                if (layer->grid_x == 0 && layer->grid_y == 0) {
                    layer->resize(self->data->grid_w, self->data->grid_h);
                } else if (layer->grid_x != self->data->grid_w || layer->grid_y != self->data->grid_h) {
                    Py_DECREF(item);
                    Py_DECREF(iterator);
                    PyErr_Format(PyExc_ValueError,
                        "Layer size (%d, %d) does not match Grid size (%d, %d)",
                        layer->grid_x, layer->grid_y, self->data->grid_w, self->data->grid_h);
                    return -1;
                }

                // Link to grid
                layer->parent_grid = self->data.get();
                self->data->layers.push_back(layer);
                py_layer->grid = self->data;

                // Inherit grid texture if TileLayer has none (#254)
                auto tile_layer_ptr = std::static_pointer_cast<TileLayer>(layer);
                if (!tile_layer_ptr->texture) {
                    tile_layer_ptr->texture = self->data->getTexture();
                }

            } else {
                Py_DECREF(item);
                Py_DECREF(iterator);
                PyErr_SetString(PyExc_TypeError, "layers must contain only ColorLayer or TileLayer objects");
                return -1;
            }

            Py_DECREF(item);
        }

        Py_DECREF(iterator);

        if (PyErr_Occurred()) {
            return -1;
        }

        self->data->layers_need_sort = true;
    }
    // else: layers_obj is Py_None - explicit empty, no layers created

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

    // #184: Check if this is a Python subclass (for callback method support)
    self->data->is_python_subclass = (PyObject*)Py_TYPE(self) != (PyObject*)&mcrfpydef::PyUIGridType;

    // #359: previously constructed an extra "shim" GridView here (self->view)
    // that copied rendering state and allocated its own RenderTexture, but was
    // NEVER used -- UIGridView::init_with_data (the only caller of UIGrid::init,
    // see UIGridView.cpp) discards this PyUIGridObject wrapper immediately after
    // stealing its GridData via an aliasing shared_ptr, and builds the REAL,
    // user-visible view directly on itself. The shim was dead weight (a wasted
    // RenderTexture allocation on every Grid() construction) backing a field
    // (PyUIGridObject::view / `_GridData.view`) nothing ever read. Removed along
    // with the field itself.

    return 0; // Success
}

// Python property getters/setters moved to UIGridPyProperties.cpp
// Python method implementations moved to UIGridPyMethods.cpp

// #221 - Get effective cell size (texture size * zoom)
sf::Vector2f UIGrid::getEffectiveCellSize() const {
    float cell_w = ptex ? static_cast<float>(ptex->sprite_width) : static_cast<float>(DEFAULT_CELL_WIDTH);
    float cell_h = ptex ? static_cast<float>(ptex->sprite_height) : static_cast<float>(DEFAULT_CELL_HEIGHT);
    return sf::Vector2f(cell_w * zoom, cell_h * zoom);
}

// UIEntityCollection code has been moved to UIEntityCollection.cpp

// Property system implementation for animations
bool UIGrid::setProperty(const std::string& name, float value) {
    if (name == "x") {
        position.x = value;
        box.setPosition(position);
        output.setPosition(position);
        markCompositeDirty();  // #144 - Position change, texture still valid
        return true;
    }
    else if (name == "y") {
        position.y = value;
        box.setPosition(position);
        output.setPosition(position);
        markCompositeDirty();  // #144 - Position change, texture still valid
        return true;
    }
    else if (name == "w" || name == "width") {
        box.setSize(sf::Vector2f(value, box.getSize().y));
        output.setTextureRect(sf::IntRect(0, 0, box.getSize().x, box.getSize().y));
        markDirty();  // #144 - Size change
        return true;
    }
    else if (name == "h" || name == "height") {
        box.setSize(sf::Vector2f(box.getSize().x, value));
        output.setTextureRect(sf::IntRect(0, 0, box.getSize().x, box.getSize().y));
        markDirty();  // #144 - Size change
        return true;
    }
    else if (name == "center_x") {
        center_x = value;
        markDirty();  // #144 - View change affects content
        return true;
    }
    else if (name == "center_y") {
        center_y = value;
        markDirty();  // #144 - View change affects content
        return true;
    }
    else if (name == "zoom") {
        zoom = value;
        markDirty();  // #144 - View change affects content
        return true;
    }
    else if (name == "camera_rotation") {
        camera_rotation = value;
        markDirty();  // View rotation affects content
        return true;
    }
    else if (name == "rotation") {
        rotation = value;
        markCompositeDirty();  // Viewport rotation doesn't affect internal content
        return true;
    }
    else if (name == "origin_x") {
        origin.x = value;
        markCompositeDirty();
        return true;
    }
    else if (name == "origin_y") {
        origin.y = value;
        markCompositeDirty();
        return true;
    }
    else if (name == "z_index") {
        z_index = static_cast<int>(value);
        markDirty();  // #144 - Z-order change affects parent
        return true;
    }
    else if (name == "fill_color.r") {
        fill_color.r = static_cast<uint8_t>(std::max(0.0f, std::min(255.0f, value)));
        markDirty();  // #144 - Content change
        return true;
    }
    else if (name == "fill_color.g") {
        fill_color.g = static_cast<uint8_t>(std::max(0.0f, std::min(255.0f, value)));
        markDirty();  // #144 - Content change
        return true;
    }
    else if (name == "fill_color.b") {
        fill_color.b = static_cast<uint8_t>(std::max(0.0f, std::min(255.0f, value)));
        markDirty();  // #144 - Content change
        return true;
    }
    else if (name == "fill_color.a") {
        fill_color.a = static_cast<uint8_t>(std::max(0.0f, std::min(255.0f, value)));
        markDirty();  // #144 - Content change
        return true;
    }
    // #106: Shader uniform properties
    if (setShaderProperty(name, value)) {
        return true;
    }
    return false;
}

bool UIGrid::setProperty(const std::string& name, const sf::Vector2f& value) {
    if (name == "size") {
        box.setSize(value);
        output.setTextureRect(sf::IntRect(0, 0, box.getSize().x, box.getSize().y));
        markDirty();  // #144 - Size change
        return true;
    }
    else if (name == "center") {
        center_x = value.x;
        center_y = value.y;
        markDirty();  // #144 - View change affects content
        return true;
    }
    else if (name == "origin") {
        origin = value;
        markCompositeDirty();
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
    else if (name == "camera_rotation") {
        value = camera_rotation;
        return true;
    }
    else if (name == "rotation") {
        value = rotation;
        return true;
    }
    else if (name == "origin_x") {
        value = origin.x;
        return true;
    }
    else if (name == "origin_y") {
        value = origin.y;
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
    // #106: Shader uniform properties
    if (getShaderProperty(name, value)) {
        return true;
    }
    return false;
}

bool UIGrid::getProperty(const std::string& name, sf::Vector2f& value) const {
    if (name == "size") {
        value = box.getSize();
        return true;
    }
    else if (name == "center") {
        value = sf::Vector2f(center_x, center_y);
        return true;
    }
    else if (name == "origin") {
        value = origin;
        return true;
    }
    return false;
}

bool UIGrid::hasProperty(const std::string& name) const {
    // Float properties
    if (name == "x" || name == "y" ||
        name == "w" || name == "h" || name == "width" || name == "height" ||
        name == "center_x" || name == "center_y" || name == "zoom" ||
        name == "camera_rotation" || name == "rotation" ||
        name == "origin_x" || name == "origin_y" || name == "z_index" ||
        name == "fill_color.r" || name == "fill_color.g" ||
        name == "fill_color.b" || name == "fill_color.a") {
        return true;
    }
    // Vector2f properties
    if (name == "size" || name == "center" || name == "origin") {
        return true;
    }
    // #106: Shader uniform properties
    if (hasShaderProperty(name)) {
        return true;
    }
    return false;
}
