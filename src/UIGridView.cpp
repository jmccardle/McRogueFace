// UIGridView.cpp - Rendering view for GridData (#252)
#include "UIGridView.h"
#include "PyGridData.h"
#include "UIGridPoint.h"
#include "UIEntity.h"
#include "GameEngine.h"
#include "McRFPy_API.h"
#include "Resources.h"
#include "Profiler.h"
#include "PyShader.h"
#include "PyTexture.h"
#include "PyUniformCollection.h"
#include "PyPositionHelper.h"
#include "PyVector.h"
#include "PythonObjectCache.h"
#include "PySceneObject.h"  // parent= kwarg: Scene is a valid parent type
#include "McRFPy_Doc.h"
#include "PyMouseButton.h"  // #355 - MouseButton enum for cell click args
#include "PyInputState.h"   // #355 - InputState enum for cell click args
#include <cmath>
#include <algorithm>

UIGridView::UIGridView()
{
    renderTexture.create(1, 1);
    renderTextureSize = {1, 1};
    output.setTextureRect(sf::IntRect(0, 0, 0, 0));
    output.setPosition(0, 0);
    output.setTexture(renderTexture.getTexture());
    box.setSize(sf::Vector2f(256, 256));
    box.setFillColor(sf::Color(0, 0, 0, 0));
    children = std::make_shared<std::vector<std::shared_ptr<UIDrawable>>>();  // #364
}

UIGridView::~UIGridView() {
    // #362: drop ourselves from the GridData's view registry. This is the only
    // place guaranteed to run exactly once per view: tp_dealloc's unregister is
    // gated on data.use_count() <= 1 (the #251 pattern), so a view that outlives
    // its Python wrapper -- the normal case, when the scene holds the last ref --
    // would otherwise leave an expired weak_ptr in `views` forever. markDirty()
    // walks that vector on every entity move.
    if (grid_data) {
        grid_data->unregisterView(this);
    }

    // #348: release the persistent internal-Grid wrapper. Guard with
    // Py_IsInitialized() because this destructor may run during interpreter
    // shutdown (mirrors Animation::~Animation).
    if (cached_grid_wrapper && Py_IsInitialized()) {
        PyGILState_STATE gstate = PyGILState_Ensure();
        Py_DECREF(cached_grid_wrapper);
        PyGILState_Release(gstate);
    }
    cached_grid_wrapper = nullptr;
}

PyObjectsEnum UIGridView::derived_type()
{
    return PyObjectsEnum::UIGRIDVIEW;
}

void UIGridView::ensureRenderTextureSize()
{
    sf::Vector2u resolution{1920, 1080};
    if (Resources::game) {
        resolution = Resources::game->getGameResolution();
    }
    unsigned int required_w = std::min(resolution.x, 4096u);
    unsigned int required_h = std::min(resolution.y, 4096u);

    if (renderTextureSize.x != required_w || renderTextureSize.y != required_h) {
        renderTexture.create(required_w, required_h);
        renderTextureSize = {required_w, required_h};
        output.setTexture(renderTexture.getTexture());
    }
}

sf::FloatRect UIGridView::get_bounds() const
{
    return sf::FloatRect(box.getPosition(), box.getSize());
}

void UIGridView::move(float dx, float dy)
{
    box.move(dx, dy);
    position += sf::Vector2f(dx, dy);
}

void UIGridView::resize(float w, float h)
{
    box.setSize(sf::Vector2f(w, h));

    // #364: aligned children re-anchor against the widget's new bounds. This ran in
    // PyGridData::resize before children moved to the view; it belongs here now.
    if (children) {
        for (auto& child : *children) {
            if (child->getAlignment() != AlignmentType::NONE) {
                child->applyAlignment();
            }
        }
    }
}

void UIGridView::onPositionChanged()
{
    // #355: UIDrawable::set_pos/set_float_member write `position` and call this;
    // without it the rendered box (and every hit test derived from it) stayed at
    // the construction-time origin.
    box.setPosition(position);
}

sf::Vector2f UIGridView::getEffectiveCellSize() const
{
    int cw = ptex ? ptex->sprite_width : DEFAULT_CELL_WIDTH;
    int ch = ptex ? ptex->sprite_height : DEFAULT_CELL_HEIGHT;
    return sf::Vector2f(cw * zoom, ch * zoom);
}

sf::Vector2f UIGridView::localToGridWorld(sf::Vector2f local) const
{
    // Exact inverse of render()'s rasterize-then-composite transform (including
    // the int truncation of left/top_spritepixels), so hit testing matches what
    // is drawn -- rotated camera included.
    //
    // render(): grid-world -> texture pixel
    //     T = (gw - spritepixels) * zoom          [texture is aabb_w x aabb_h]
    // then the texture is blitted rotated by camera_rotation about its center,
    // landing on the widget center:
    //     L - box_center = R(camera_rotation) * (T - tex_center)
    // Inverting: T = R(-camera_rotation) * (L - box_center) + tex_center,
    //            gw = T / zoom + spritepixels.
    const float grid_w_px = box.getSize().x;
    const float grid_h_px = box.getSize().y;

    const float rad = camera_rotation * (float)(M_PI / 180.0);
    const float cos_r = std::cos(rad);
    const float sin_r = std::sin(rad);
    // Same AABB the renderer rasterizes into (equals the box when unrotated).
    const float aabb_w = grid_w_px * std::abs(cos_r) + grid_h_px * std::abs(sin_r);
    const float aabb_h = grid_w_px * std::abs(sin_r) + grid_h_px * std::abs(cos_r);

    const float dx = local.x - grid_w_px / 2.0f;
    const float dy = local.y - grid_h_px / 2.0f;
    // R(-camera_rotation) applied to (dx, dy), then re-centered on the AABB.
    const float tx =  dx * cos_r + dy * sin_r + aabb_w / 2.0f;
    const float ty = -dx * sin_r + dy * cos_r + aabb_h / 2.0f;

    int left_spritepixels = center_x - (aabb_w / 2.0 / zoom);
    int top_spritepixels  = center_y - (aabb_h / 2.0 / zoom);
    return sf::Vector2f(tx / zoom + left_spritepixels,
                        ty / zoom + top_spritepixels);
}

std::optional<sf::Vector2i> UIGridView::cellAtLocal(sf::Vector2f local) const
{
    if (!grid_data) return std::nullopt;
    if (local.x < 0 || local.y < 0 ||
        local.x >= box.getSize().x || local.y >= box.getSize().y) {
        return std::nullopt;
    }
    int cw = ptex ? ptex->sprite_width  : DEFAULT_CELL_WIDTH;
    int ch = ptex ? ptex->sprite_height : DEFAULT_CELL_HEIGHT;
    sf::Vector2f gw = localToGridWorld(local);
    int cx = static_cast<int>(std::floor(gw.x / cw));
    int cy = static_cast<int>(std::floor(gw.y / ch));
    if (cx < 0 || cx >= grid_data->grid_w || cy < 0 || cy >= grid_data->grid_h)
        return std::nullopt;
    return sf::Vector2i(cx, cy);
}

void UIGridView::center_camera()
{
    if (!grid_data) return;
    int cw = ptex ? ptex->sprite_width : DEFAULT_CELL_WIDTH;
    int ch = ptex ? ptex->sprite_height : DEFAULT_CELL_HEIGHT;
    center_x = (grid_data->grid_w / 2.0f) * cw;
    center_y = (grid_data->grid_h / 2.0f) * ch;
}

void UIGridView::center_camera(float tile_x, float tile_y)
{
    int cw = ptex ? ptex->sprite_width : DEFAULT_CELL_WIDTH;
    int ch = ptex ? ptex->sprite_height : DEFAULT_CELL_HEIGHT;
    center_x = tile_x * cw;
    center_y = tile_y * ch;
}

// =========================================================================
// Render -- adapted from PyGridData::render()
// =========================================================================
void UIGridView::render(sf::Vector2f offset, sf::RenderTarget& target)
{
    if (!visible || !grid_data) return;

    ensureRenderTextureSize();

    // #351 - clean-state early-out: re-blit the cached RenderTexture when nothing
    // affecting the raster changed since last frame. Camera params are compared
    // directly (view-local); grid content changes bump content_generation. The
    // perspective overlay (single source of truth: this view's own
    // perspective_enabled, see #355 fix) and any grid children are conservative
    // always-render carve-outs until tracked precisely (#352).
    // last_perspective_enabled: the cached raster HAS an overlay baked into it, so
    // the frame that turns perspective off must re-rasterize even though every
    // other input is unchanged (otherwise the fog stays on screen forever).
    bool can_skip =
        has_rendered_once
        // #364 - a child mutation (move, recolor, add, remove) reaches us as
        // render_dirty via the parent chain, because grid children now parent to the
        // view. The children carve-out below cannot catch the removal of the LAST
        // child -- children is empty by then, so the carve-out lifts and the cached
        // raster, which still has that child baked into it, would be re-blitted.
        && !render_dirty
        && !perspective_enabled
        && !last_perspective_enabled
        && (!children || children->empty())
        && grid_data->content_generation == last_content_gen
        && center_x == last_center_x && center_y == last_center_y
        && zoom == last_zoom && camera_rotation == last_camera_rotation
        && box.getSize() == last_box_size
        && fill_color == last_fill_color
        && renderTextureSize == last_render_tex_size;
    if (can_skip) {
        if (rotation != 0.0f) {
            output.setOrigin(origin);
            output.setRotation(rotation);
            output.setPosition(box.getPosition() + offset + origin);
        } else {
            output.setOrigin(0, 0);
            output.setRotation(0);
            output.setPosition(box.getPosition() + offset);
        }
        if (shader && shader->shader) {
            sf::Vector2f resolution(box.getSize().x, box.getSize().y);
            PyShader::applyEngineUniforms(*shader->shader, resolution);
            if (uniforms) uniforms->applyTo(*shader->shader);
            target.draw(output, shader->shader.get());
        } else {
            target.draw(output);
        }
        return;
    }

    int cell_width = ptex ? ptex->sprite_width : DEFAULT_CELL_WIDTH;
    int cell_height = ptex ? ptex->sprite_height : DEFAULT_CELL_HEIGHT;

    bool has_camera_rotation = (camera_rotation != 0.0f);
    float grid_w_px = box.getSize().x;
    float grid_h_px = box.getSize().y;

    float rad = camera_rotation * (M_PI / 180.0f);
    float cos_r = std::cos(rad);
    float sin_r = std::sin(rad);
    float abs_cos = std::abs(cos_r);
    float abs_sin = std::abs(sin_r);
    float aabb_w = grid_w_px * abs_cos + grid_h_px * abs_sin;
    float aabb_h = grid_w_px * abs_sin + grid_h_px * abs_cos;

    sf::RenderTexture* activeTexture = &renderTexture;

    if (has_camera_rotation) {
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
    if (x_limit > grid_data->grid_w) x_limit = grid_data->grid_w;
    int y_limit = top_edge + height_sq + 2;
    if (y_limit > grid_data->grid_h) y_limit = grid_data->grid_h;

    // #341: re-instrument the grid render counters. These were declared and reset
    // every frame but never incremented anywhere -- the increments were lost in the
    // GridView/chunk refactor, so grid_cells_rendered/entities_rendered/
    // grid_render_time have read 0 ever since. Accumulating (not assigning) so that
    // two views over one map sum rather than clobber each other.
    auto& metrics = Resources::game->metrics;
    ScopedAccumTimer gridTimer(metrics.gridRenderTime);

    // Cells actually inside the viewport window, per layer drawn.
    const int x_start = std::max(0, static_cast<int>(left_edge));
    const int y_start = std::max(0, static_cast<int>(top_edge));
    const int visible_cells = std::max(0, x_limit - x_start) * std::max(0, y_limit - y_start);

    // Render layers below entities (z_index <= 0)
    grid_data->sortLayers();
    int layers_drawn = 0;
    for (auto& layer : grid_data->layers) {
        if (layer->z_index > 0) break;  // #257: z_index=0 is ground level (below entities)
        layer->render(*activeTexture, left_spritepixels, top_spritepixels,
                     left_edge, top_edge, x_limit, y_limit, zoom, cell_width, cell_height);
        ++layers_drawn;
    }

    // Render entities
    if (grid_data->entities) {
        ScopedAccumTimer entityTimer(metrics.entityRenderTime);
        metrics.totalEntities += static_cast<int>(grid_data->entities->size());
        for (auto& e : *grid_data->entities) {
            if (e->position.x < left_edge - 2 || e->position.x >= left_edge + width_sq + 2 ||
                e->position.y < top_edge - 2 || e->position.y >= top_edge + height_sq + 2) {
                continue;
            }
            auto& drawent = e->sprite;
            drawent.setScale(sf::Vector2f(zoom, zoom));
            auto pixel_pos = sf::Vector2f(
                (e->position.x*cell_width - left_spritepixels + e->sprite_offset.x) * zoom,
                (e->position.y*cell_height - top_spritepixels + e->sprite_offset.y) * zoom);
            drawent.render(pixel_pos, *activeTexture);
            ++metrics.entitiesRendered;
        }
    }

    // Render layers above entities (z_index > 0)
    for (auto& layer : grid_data->layers) {
        if (layer->z_index <= 0) continue;  // #257: skip ground-level and below
        layer->render(*activeTexture, left_spritepixels, top_spritepixels,
                     left_edge, top_edge, x_limit, y_limit, zoom, cell_width, cell_height);
        ++layers_drawn;
    }

    // One "cell rendered" per cell per layer drawn -- i.e. cell draw operations.
    metrics.gridCellsRendered += visible_cells * layers_drawn;

    // Children (grid-world pixel coordinates; owned by this view -- #364)
    if (children && !children->empty()) {
        if (children_need_sort) {
            std::sort(children->begin(), children->end(),
                [](const auto& a, const auto& b) { return a->z_index < b->z_index; });
            children_need_sort = false;
        }
        for (auto& child : *children) {
            if (!child->visible) continue;
            float child_grid_x = child->position.x / cell_width;
            float child_grid_y = child->position.y / cell_height;
            if (child_grid_x < left_edge - 2 || child_grid_x >= left_edge + width_sq + 2 ||
                child_grid_y < top_edge - 2 || child_grid_y >= top_edge + height_sq + 2)
                continue;
            auto pixel_pos = sf::Vector2f(
                (child->position.x - left_spritepixels) * zoom,
                (child->position.y - top_spritepixels) * zoom);
            child->render(pixel_pos, *activeTexture);
        }
    }

    // Perspective overlay (#355: state owned by the view -- see get/set_perspective)
    if (perspective_enabled) {
        // #341: accumulate -- with two perspective views on screen, assignment made
        // the second view's time silently replace the first's.
        ScopedAccumTimer fovTimer(Resources::game->metrics.fovOverlayTime);
        auto entity = perspective_entity.lock();
        sf::RectangleShape overlay;
        overlay.setSize(sf::Vector2f(cell_width * zoom, cell_height * zoom));

        if (entity && entity->perspective_map) {
            // #294: perspective_map values: 0=unknown, 1=discovered, 2=visible.
            const uint8_t* pm = entity->perspective_map->data();
            const int pm_w = entity->perspective_map->width();
            const int pm_h = entity->perspective_map->height();
            for (int x = std::max(0, (int)(left_edge - 1)); x < x_limit; x++) {
                for (int y = std::max(0, (int)(top_edge - 1)); y < y_limit; y++) {
                    if (x < 0 || x >= grid_data->grid_w || y < 0 || y >= grid_data->grid_h) continue;
                    if (x >= pm_w || y >= pm_h) continue;
                    auto pixel_pos = sf::Vector2f(
                        (x*cell_width - left_spritepixels) * zoom,
                        (y*cell_height - top_spritepixels) * zoom);
                    uint8_t state = pm[y * pm_w + x];
                    overlay.setPosition(pixel_pos);
                    if (state == 0) {
                        overlay.setFillColor(sf::Color(0, 0, 0, 255));
                        activeTexture->draw(overlay);
                    } else if (state == 1) {
                        overlay.setFillColor(sf::Color(32, 32, 40, 192));
                        activeTexture->draw(overlay);
                    }
                    // state == 2: visible -- no overlay
                }
            }
        } else {
            for (int x = std::max(0, (int)(left_edge - 1)); x < x_limit; x++) {
                for (int y = std::max(0, (int)(top_edge - 1)); y < y_limit; y++) {
                    if (x < 0 || x >= grid_data->grid_w || y < 0 || y >= grid_data->grid_h) continue;
                    auto pixel_pos = sf::Vector2f(
                        (x*cell_width - left_spritepixels) * zoom,
                        (y*cell_height - top_spritepixels) * zoom);
                    overlay.setPosition(pixel_pos);
                    overlay.setFillColor(sf::Color(0, 0, 0, 255));
                    activeTexture->draw(overlay);
                }
            }
        }
    }

    activeTexture->display();

    // Camera rotation compositing
    if (has_camera_rotation) {
        renderTexture.clear(fill_color);
        sf::Sprite rotatedSprite(rotationTexture->getTexture());
        float tex_center_x = aabb_w / 2.0f;
        float tex_center_y = aabb_h / 2.0f;
        rotatedSprite.setOrigin(tex_center_x, tex_center_y);
        rotatedSprite.setRotation(camera_rotation);
        rotatedSprite.setPosition(grid_w_px / 2.0f, grid_h_px / 2.0f);
        rotatedSprite.setTextureRect(sf::IntRect(0, 0, (int)aabb_w, (int)aabb_h));
        renderTexture.draw(rotatedSprite);
        renderTexture.display();
        output.setPosition(box.getPosition() + offset);
        output.setTextureRect(sf::IntRect(0, 0, grid_w_px, grid_h_px));
    }

    if (rotation != 0.0f) {
        output.setOrigin(origin);
        output.setRotation(rotation);
        output.setPosition(box.getPosition() + offset + origin);
    } else {
        output.setOrigin(0, 0);
        output.setRotation(0);
    }

    // #351 - record the inputs this raster was built from for next frame's early-out.
    has_rendered_once = true;
    // #364 - the raster is now current with every child mutation that pushed dirt up
    // the parent chain into us. Clearing here is what makes render_dirty a usable
    // early-out input (see can_skip): without it the flag latches true forever after
    // the first child edit and the early-out could never fire again.
    clearDirty();
    last_content_gen = grid_data->content_generation;
    last_center_x = center_x;
    last_center_y = center_y;
    last_zoom = zoom;
    last_camera_rotation = camera_rotation;
    last_box_size = box.getSize();
    last_fill_color = fill_color;
    last_render_tex_size = renderTextureSize;
    last_perspective_enabled = perspective_enabled;

    if (shader && shader->shader) {
        sf::Vector2f resolution(box.getSize().x, box.getSize().y);
        PyShader::applyEngineUniforms(*shader->shader, resolution);
        if (uniforms) uniforms->applyTo(*shader->shader);
        target.draw(output, shader->shader.get());
    } else {
        target.draw(output);
    }
}

UIDrawable* UIGridView::click_at(sf::Vector2f point)
{
    // point is in PARENT-LOCAL space (UIFrame::click_at passes point - position down).
    if (!box.getGlobalBounds().contains(point)) return nullptr;
    if (!grid_data) {
        // #365: a view with no cells cannot produce a cell event. Drop any cell
        // stashed by an earlier click, or dispatchCellClick would fire it for a
        // grid that no longer exists.
        last_clicked_cell = std::nullopt;
        return (click_callable || is_python_subclass) ? this : nullptr;
    }

    sf::Vector2f local = point - box.getPosition();
    sf::Vector2f gw    = localToGridWorld(local);

    int cw = ptex ? ptex->sprite_width  : DEFAULT_CELL_WIDTH;
    int ch = ptex ? ptex->sprite_height : DEFAULT_CELL_HEIGHT;
    float grid_x = gw.x / cw;
    float grid_y = gw.y / ch;

    // 1. Children first (drawn on top). Children of a grid live in GRID-WORLD PIXEL
    //    coordinates -- NOT view-local, NOT screen (#360, by design: moving the
    //    camera must not move a child's logical position). Do not "fix" this.
    if (children && !children->empty()) {
        if (children_need_sort) {
            std::sort(children->begin(), children->end(),
                [](const auto& a, const auto& b) { return a->z_index < b->z_index; });
            children_need_sort = false;
        }
        for (auto it = children->rbegin(); it != children->rend(); ++it) {
            auto& child = *it;
            if (!child->visible) continue;
            if (auto target = child->click_at(gw)) return target;
        }
    }

    // 2. Entities: 1x1 cell hit box matching the renderer, which draws the sprite at
    //    position.x * cell_width -- i.e. cell [pos, pos+1).
    //    NOTE: unreachable from Python today -- Entity exposes no on_click/sprite
    //    binding, so entity->sprite.click_callable can never be set, and this branch
    //    cannot fire. Implemented per #355; dead until an Entity.on_click binding
    //    exists (needs its own issue).
    if (grid_data->entities) {
        for (auto it = grid_data->entities->rbegin(); it != grid_data->entities->rend(); ++it) {
            auto& entity = *it;
            if (!entity || !entity->sprite.visible) continue;
            float dx = grid_x - entity->position.x;
            float dy = grid_y - entity->position.y;
            if (dx >= 0.0f && dx < 1.0f && dy >= 0.0f && dy < 1.0f) {
                if (entity->sprite.click_callable) return &entity->sprite;
            }
        }
    }

    // 3. The cell itself. Stash for dispatchCellClick (PyScene has only global coords).
    //    #365: only stash when we are actually returning ourselves as the click
    //    target. Returning nullptr means PyScene never calls dispatchCellClick, so
    //    nothing would consume the stash (dispatchCellClick clears it on read) and
    //    the cell would linger until some later dispatch fired it.
    if (click_callable || is_python_subclass || on_cell_click_callable) {
        last_clicked_cell = cellAtLocal(local);
        return this;
    }
    last_clicked_cell = std::nullopt;
    return nullptr;
}

// Property system
bool UIGridView::setProperty(const std::string& name, float value)
{
    if (name == "center_x") { center_x = value; return true; }
    if (name == "center_y") { center_y = value; return true; }
    if (name == "zoom") { zoom = value; return true; }
    if (name == "camera_rotation") { camera_rotation = value; return true; }
    if (setShaderProperty(name, value)) return true;
    return UIDrawable::setProperty(name, value);
}

bool UIGridView::setProperty(const std::string& name, const sf::Vector2f& value)
{
    if (name == "center") {
        center_x = value.x;
        center_y = value.y;
        return true;
    }
    return UIDrawable::setProperty(name, value);
}

bool UIGridView::getProperty(const std::string& name, float& value) const
{
    if (name == "center_x") { value = center_x; return true; }
    if (name == "center_y") { value = center_y; return true; }
    if (name == "zoom") { value = zoom; return true; }
    if (name == "camera_rotation") { value = camera_rotation; return true; }
    if (getShaderProperty(name, value)) return true;
    return UIDrawable::getProperty(name, value);
}

bool UIGridView::getProperty(const std::string& name, sf::Vector2f& value) const
{
    if (name == "center") {
        value = sf::Vector2f(center_x, center_y);
        return true;
    }
    return UIDrawable::getProperty(name, value);
}

bool UIGridView::hasProperty(const std::string& name) const
{
    if (name == "center_x" || name == "center_y" || name == "zoom" || name == "camera_rotation" || name == "center")
        return true;
    // #106: Shader uniform properties
    if (hasShaderProperty(name))
        return true;
    return UIDrawable::hasProperty(name);
}

// =========================================================================
// Python API
// =========================================================================

// #252: Grid/GridView API Unification
// Two construction modes:
//   Mode 1 (view): Grid(grid=existing_grid, pos=..., size=...)
//   Mode 2 (factory): Grid(grid_size=..., pos=..., texture=..., ...)
//
// Mode 2 creates a UIGrid internally and copies rendering state to GridView.
// Attribute access delegates to the underlying UIGrid for data operations.

int UIGridView::init(PyUIGridViewObject* self, PyObject* args, PyObject* kwds)
{
    // #361: ONE parse for both construction modes.
    //
    //   Grid(grid_size=(80,40), pos=..., size=...)   -- creates its own GridData
    //   Grid(grid=data, pos=..., size=...)           -- a camera onto existing data
    //
    // This used to be two functions, and the factory mode built a throwaway
    // Python _GridData object just to steal its GridData base subobject via an
    // aliasing shared_ptr, then copied a dozen fields of rendering state out of
    // the discarded wrapper. The view now constructs the GridData directly. As a
    // side effect the view-mode kwarg set is no longer a crippled subset: z_index,
    // visible, opacity, on_click and align work on a second view too, which they
    // silently did not before (they raised TypeError).
    PyObject* pos_obj = nullptr;
    PyObject* size_obj = nullptr;
    PyObject* grid_size_obj = nullptr;
    PyObject* texture_obj = nullptr;
    PyObject* grid_obj = nullptr;
    PyObject* fill_color_obj = nullptr;
    PyObject* click_handler = nullptr;
    PyObject* layers_obj = nullptr;
    PyObject* parent_obj = nullptr;
    PyObject* align_obj = nullptr;
    // #169 - NaN sentinel: distinguishes "user passed a center" from "default it".
    float center_x = std::numeric_limits<float>::quiet_NaN();
    float center_y = std::numeric_limits<float>::quiet_NaN();
    float zoom = 1.0f;
    int visible = 1;
    float opacity = 1.0f;
    int z_index = 0;
    const char* name = nullptr;
    float x = 0.0f, y = 0.0f, w = 0.0f, h = 0.0f;
    int grid_w = 2, grid_h = 2;
    float margin = 0.0f, horiz_margin = -1.0f, vert_margin = -1.0f;

    static const char* kwlist[] = {
        "pos", "size", "grid_size", "texture",   // positional
        "grid", "fill_color", "on_click", "center_x", "center_y", "zoom",
        "visible", "opacity", "z_index", "name", "x", "y", "w", "h",
        "grid_w", "grid_h", "layers", "parent",
        "align", "margin", "horiz_margin", "vert_margin",
        nullptr
    };

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OOOOOOOfffifizffffiiOOOfff",
                                     const_cast<char**>(kwlist),
                                     &pos_obj, &size_obj, &grid_size_obj, &texture_obj,
                                     &grid_obj, &fill_color_obj, &click_handler,
                                     &center_x, &center_y, &zoom,
                                     &visible, &opacity, &z_index, &name,
                                     &x, &y, &w, &h, &grid_w, &grid_h,
                                     &layers_obj, &parent_obj,
                                     &align_obj, &margin, &horiz_margin, &vert_margin)) {
        return -1;
    }

    const bool attaching = (grid_obj && grid_obj != Py_None);

    // --------------------------------------------------------------------
    // The map: attach to an existing one, or build a new one.
    // --------------------------------------------------------------------
    if (attaching) {
        // A camera onto someone else's map cannot also specify that map's shape.
        // Silently ignoring these would quietly hand back a view of a DIFFERENT
        // size than asked for.
        if (grid_size_obj || texture_obj || layers_obj) {
            PyErr_SetString(PyExc_TypeError,
                "grid= names an existing GridData; grid_size/texture/layers describe a "
                "new one. Pass one or the other, not both.");
            return -1;
        }

        if (PyObject_IsInstance(grid_obj, (PyObject*)&mcrfpydef::PyGridDataType)) {
            self->data->grid_data = ((PyGridDataObject*)grid_obj)->data;
        } else if (PyObject_IsInstance(grid_obj, (PyObject*)&mcrfpydef::PyUIGridViewType)) {
            // Another Grid/GridView: share the map it is looking at.
            self->data->grid_data = ((PyUIGridViewObject*)grid_obj)->data->grid_data;
        } else {
            PyErr_SetString(PyExc_TypeError, "grid must be a GridData or a Grid");
            return -1;
        }
        if (!self->data->grid_data) {
            PyErr_SetString(PyExc_ValueError, "grid has no data to view");
            return -1;
        }
        self->data->ptex = self->data->grid_data->getTexture();
    } else {
        std::shared_ptr<PyTexture> texture;
        if (PyGridData::parse_grid_shape(grid_size_obj, texture_obj,
                                         grid_w, grid_h, texture) < 0) {
            return -1;
        }
        self->data->grid_data = std::make_shared<GridData>(grid_w, grid_h, texture);
        if (PyGridData::apply_layers_arg(self->data->grid_data, layers_obj, texture) < 0) {
            return -1;
        }
        self->data->ptex = texture;
    }

    auto& grid_data = self->data->grid_data;

    // --------------------------------------------------------------------
    // The camera: this view's own rendering state.
    // --------------------------------------------------------------------
    if (pos_obj && pos_obj != Py_None) {
        PyVectorObject* vec = PyVector::from_arg(pos_obj);
        if (vec) {
            x = vec->data.x;
            y = vec->data.y;
            Py_DECREF(vec);
        } else {
            PyErr_Clear();
            sf::Vector2f p = PyObject_to_sfVector2f(pos_obj);
            if (PyErr_Occurred()) {
                PyErr_SetString(PyExc_TypeError, "pos must be a tuple (x, y) or Vector");
                return -1;
            }
            x = p.x;
            y = p.y;
        }
    }

    if (size_obj && size_obj != Py_None) {
        sf::Vector2f s = PyObject_to_sfVector2f(size_obj);
        if (PyErr_Occurred()) {
            PyErr_SetString(PyExc_TypeError, "size must be a tuple (w, h)");
            return -1;
        }
        w = s.x;
        h = s.y;
    } else if (w == 0.0f && h == 0.0f) {
        // Default: show the whole map at 1:1.
        w = grid_data->grid_w * static_cast<float>(grid_data->cell_width());
        h = grid_data->grid_h * static_cast<float>(grid_data->cell_height());
    }

    self->data->zoom = zoom;
    self->data->position = sf::Vector2f(x, y);
    self->data->box.setPosition(self->data->position);
    self->data->box.setSize(sf::Vector2f(w, h));
    self->data->visible = visible;
    self->data->opacity = opacity;
    self->data->z_index = z_index;
    if (name) self->data->UIDrawable::name = std::string(name);

    // #169 - default camera puts tile (0,0) at the widget's top-left.
    if (std::isnan(center_x)) center_x = w / (2.0f * zoom);
    if (std::isnan(center_y)) center_y = h / (2.0f * zoom);
    self->data->center_x = center_x;
    self->data->center_y = center_y;

    if (fill_color_obj && fill_color_obj != Py_None) {
        self->data->fill_color = PyColor::fromPy(fill_color_obj);
        if (PyErr_Occurred()) return -1;
    }

    if (click_handler && click_handler != Py_None) {
        if (!PyCallable_Check(click_handler)) {
            PyErr_SetString(PyExc_TypeError, "on_click must be callable");
            return -1;
        }
        self->data->click_register(click_handler);
    }

    UIDRAWABLE_PROCESS_ALIGNMENT(self->data, align_obj, margin, horiz_margin, vert_margin);

    self->data->ensureRenderTextureSize();

    // #359 - Register with the map so data-layer mutations invalidate THIS view's
    // cache and push dirt up ITS ancestor chain. Registration order matters: the
    // creating view is views.front().
    grid_data->registerView(self->data);

    self->weakreflist = NULL;

    if (self->data->serial_number == 0) {
        self->data->serial_number = PythonObjectCache::getInstance().assignSerial();
        PyObject* weakref = PyWeakref_NewRef((PyObject*)self, NULL);
        if (weakref) {
            PythonObjectCache::getInstance().registerObject(self->data->serial_number, weakref);
            Py_DECREF(weakref);
        }
    }
    self->data->is_python_subclass =
        (PyObject*)Py_TYPE(self) != (PyObject*)&mcrfpydef::PyUIGridViewType;

    if (parent_obj && parent_obj != Py_None) {
        UIDRAWABLE_ATTACH_TO_PARENT(parent_obj, self);
    }

    return 0;
}

PyObject* UIGridView::repr(PyUIGridViewObject* self)
{
    std::ostringstream ss;
    ss << "<GridView";
    if (self->data->grid_data) {
        ss << " (" << self->data->grid_data->grid_w << "x" << self->data->grid_data->grid_h << ")";
    } else {
        ss << " (no data)";
    }
    ss << " pos=(" << self->data->box.getPosition().x << ", " << self->data->box.getPosition().y << ")"
       << " size=(" << self->data->box.getSize().x << ", " << self->data->box.getSize().y << ")"
       << " zoom=" << self->data->zoom << ">";
    return PyUnicode_FromString(ss.str().c_str());
}

// =========================================================================
// #252: Attribute delegation to underlying Grid (UIGrid)
// =========================================================================

PyObject* UIGridView::get_grid_pyobj(PyUIGridViewObject* self)
{
    if (!self->data || !self->data->grid_data) {
        return nullptr;
    }
    return get_grid(self, nullptr);  // Returns new ref to internal UIGrid wrapper
}

PyObject* UIGridView::getattro(PyObject* self, PyObject* name)
{
    // First try normal attribute lookup on GridView (own getsetters + methods)
    PyObject* result = PyObject_GenericGetAttr(self, name);
    if (result) return result;

    // Only delegate on AttributeError, not other exceptions
    if (!PyErr_ExceptionMatches(PyExc_AttributeError)) return nullptr;

    PyUIGridViewObject* view = (PyUIGridViewObject*)self;
    if (!view->data || !view->data->grid_data) {
        // No grid data - can't delegate, return original AttributeError
        return nullptr;
    }

    // Clear error and try the internal Grid object
    PyErr_Clear();

    PyObject* grid = get_grid_pyobj(view);
    if (!grid) {
        PyErr_Format(PyExc_AttributeError,
            "'Grid' object has no attribute '%.200s'",
            PyUnicode_AsUTF8(name));
        return nullptr;
    }

    result = PyObject_GetAttr(grid, name);
    Py_DECREF(grid);
    return result;  // Returns result or propagates Grid's AttributeError
}

int UIGridView::setattro(PyObject* self, PyObject* name, PyObject* value)
{
    // First try normal attribute set on GridView (own getsetters)
    int result = PyObject_GenericSetAttr(self, name, value);
    if (result == 0) return 0;

    // Only delegate on AttributeError
    if (!PyErr_ExceptionMatches(PyExc_AttributeError)) return -1;

    PyUIGridViewObject* view = (PyUIGridViewObject*)self;
    if (!view->data || !view->data->grid_data) {
        return -1;  // No grid data, return original error
    }

    PyErr_Clear();

    PyObject* grid = get_grid_pyobj(view);
    if (!grid) {
        PyErr_Format(PyExc_AttributeError,
            "'Grid' object has no attribute '%.200s'",
            PyUnicode_AsUTF8(name));
        return -1;
    }

    result = PyObject_SetAttr(grid, name, value);
    Py_DECREF(grid);
    return result;
}

// Property getters/setters
PyObject* UIGridView::get_grid(PyUIGridViewObject* self, void* closure)
{
    if (!self->data->grid_data) Py_RETURN_NONE;

    // #348: fast path -- the view holds a persistent strong ref to the internal
    // Grid wrapper, so repeated access (grid.at(), grid.entities, layer writes,
    // per-cell procgen loops) reuses one object instead of allocating a fresh
    // wrapper + weakref every call (previously 0% cache-hit alloc churn).
    if (self->data->cached_grid_wrapper) {
        Py_INCREF(self->data->cached_grid_wrapper);
        return self->data->cached_grid_wrapper;
    }

    // #361: build (or find) the map's one Python wrapper, then adopt it as this
    // view's persistent cache so subsequent accesses hit the fast path above.
    // The aliasing shared_ptr this used to reconstruct -- to recover the "full
    // UIGrid" that every GridData was secretly a base subobject of -- is gone
    // along with UIGrid itself.
    PyObject* pyGrid = PyGridData::pyobject_for(self->data->grid_data);
    if (!pyGrid || pyGrid == Py_None) return pyGrid;

    // pyobject_for returns a strong ref; keep it as the view's cache and hand a
    // second ref to the caller.
    self->data->cached_grid_wrapper = pyGrid;
    Py_INCREF(pyGrid);
    return pyGrid;
}

int UIGridView::set_grid(PyUIGridViewObject* self, PyObject* value, void* closure)
{
    // #348: the persistent wrapper tracks the *current* grid_data; any reassign
    // (including to None) invalidates it so get_grid rebuilds for the new data.
    Py_CLEAR(self->data->cached_grid_wrapper);
    // #359 - Unregister self from whatever grid_data it was viewing before
    // reassignment. unregisterView matches by identity (self->data.get()), so
    // this is safe even when other views also share the old grid_data.
    if (self->data->grid_data) {
        self->data->grid_data->unregisterView(self->data.get());
    }
    if (value == Py_None) {
        self->data->grid_data = nullptr;
        return 0;
    }
    // A GridData: point this camera at that map. (#361: no aliasing cast -- the
    // wrapper holds the GridData itself, not a UIGrid it was a base subobject of.)
    if (PyObject_IsInstance(value, (PyObject*)&mcrfpydef::PyGridDataType)) {
        PyGridDataObject* pygrid = (PyGridDataObject*)value;
        self->data->grid_data = pygrid->data;
        self->data->ptex = pygrid->data->getTexture();
        self->data->grid_data->registerView(self->data);
        return 0;
    }
    // A Grid/GridView: share the map it is looking at.
    if (PyObject_IsInstance(value, (PyObject*)&mcrfpydef::PyUIGridViewType)) {
        PyUIGridViewObject* pyview = (PyUIGridViewObject*)value;
        if (pyview->data->grid_data) {
            self->data->grid_data = pyview->data->grid_data;
            self->data->ptex = pyview->data->ptex;
            // #359: register self alongside the original owner (and any other
            // secondary views) -- does not disturb primaryView() identity,
            // which stays views.front() (the original creator).
            self->data->grid_data->registerView(self->data);
            return 0;
        }
        self->data->grid_data = nullptr;
        return 0;
    }
    PyErr_SetString(PyExc_TypeError, "grid_data must be a GridData, a Grid, or None");
    return -1;
}

PyObject* UIGridView::get_center(PyUIGridViewObject* self, void* closure)
{
    return sfVector2f_to_PyObject(sf::Vector2f(self->data->center_x, self->data->center_y));
}

int UIGridView::set_center(PyUIGridViewObject* self, PyObject* value, void* closure)
{
    sf::Vector2f vec = PyObject_to_sfVector2f(value);
    if (PyErr_Occurred()) return -1;
    self->data->center_x = vec.x;
    self->data->center_y = vec.y;
    return 0;
}

PyObject* UIGridView::get_zoom(PyUIGridViewObject* self, void* closure)
{
    return PyFloat_FromDouble(self->data->zoom);
}

int UIGridView::set_zoom(PyUIGridViewObject* self, PyObject* value, void* closure)
{
    double val = PyFloat_AsDouble(value);
    if (val == -1.0 && PyErr_Occurred()) return -1;
    self->data->zoom = static_cast<float>(val);
    self->data->markDirty();
    return 0;
}

// #361 - `size` and `center_camera()` were NEVER on the view. They resolved, via
// getattro delegation, to the internal UIGrid's copies -- the ghost camera nobody
// renders -- so `grid.size = (w, h)` and `grid.center_camera(...)` were SILENT
// NO-OPS on the widget the user was actually looking at. Deleting the ghost is
// what surfaced them.
PyObject* UIGridView::get_size(PyUIGridViewObject* self, void* closure)
{
    return PyVector(self->data->box.getSize()).pyObject();
}

int UIGridView::set_size(PyUIGridViewObject* self, PyObject* value, void* closure)
{
    float w, h;
    PyVectorObject* vec = PyVector::from_arg(value);
    if (vec) {
        w = vec->data.x;
        h = vec->data.y;
        Py_DECREF(vec);
    } else {
        PyErr_Clear();
        if (!PyArg_ParseTuple(value, "ff", &w, &h)) {
            PyErr_SetString(PyExc_TypeError, "size must be a Vector or tuple (w, h)");
            return -1;
        }
    }
    self->data->resize(w, h);
    return 0;
}

PyObject* UIGridView::py_center_camera(PyUIGridViewObject* self, PyObject* args)
{
    PyObject* pos_arg = nullptr;
    if (!PyArg_ParseTuple(args, "|O", &pos_arg)) return nullptr;

    if (pos_arg == nullptr || pos_arg == Py_None) {
        self->data->center_camera();
        Py_RETURN_NONE;
    }

    float tile_x, tile_y;
    PyVectorObject* vec = PyVector::from_arg(pos_arg);
    if (vec) {
        tile_x = vec->data.x;
        tile_y = vec->data.y;
        Py_DECREF(vec);
    } else {
        PyErr_Clear();
        if (!PyTuple_Check(pos_arg) || PyTuple_Size(pos_arg) != 2) {
            PyErr_SetString(PyExc_TypeError,
                "center_camera() takes an optional (tile_x, tile_y) tuple or Vector");
            return nullptr;
        }
        PyObject* x_obj = PyTuple_GetItem(pos_arg, 0);
        PyObject* y_obj = PyTuple_GetItem(pos_arg, 1);
        if (!(PyFloat_Check(x_obj) || PyLong_Check(x_obj)) ||
            !(PyFloat_Check(y_obj) || PyLong_Check(y_obj))) {
            PyErr_SetString(PyExc_TypeError, "tile coordinates must be numeric");
            return nullptr;
        }
        tile_x = PyFloat_Check(x_obj) ? PyFloat_AsDouble(x_obj) : (float)PyLong_AsLong(x_obj);
        tile_y = PyFloat_Check(y_obj) ? PyFloat_AsDouble(y_obj) : (float)PyLong_AsLong(y_obj);
    }

    self->data->center_camera(tile_x, tile_y);
    Py_RETURN_NONE;
}

PyObject* UIGridView::get_fill_color(PyUIGridViewObject* self, void* closure)
{
    auto type = &mcrfpydef::PyColorType;
    auto obj = (PyColorObject*)type->tp_alloc(type, 0);
    if (obj) obj->data = self->data->fill_color;
    return (PyObject*)obj;
}

int UIGridView::set_fill_color(PyUIGridViewObject* self, PyObject* value, void* closure)
{
    self->data->fill_color = PyColor::fromPy(value);
    if (PyErr_Occurred()) return -1;
    return 0;
}

// =========================================================================
// Perspective (#355 fix): OWNED BY THE VIEW. The FOV overlay is drawn by
// UIGridView::render, so the state it gates on must live here -- previously
// `grid.perspective` fell through getattro to the internal _GridData and wrote
// PyGridData::perspective_enabled, which render() never read: the overlay was dead.
// Per-view ownership is also the correct semantics for shared GridData (#359):
// two views of one map can follow two different entities' FOV.
// =========================================================================
PyObject* UIGridView::get_perspective(PyUIGridViewObject* self, void* closure)
{
    auto locked = self->data->perspective_entity.lock();
    if (!locked) Py_RETURN_NONE;

    // Honor the cache so Entity subclass identity survives (#266).
    if (locked->serial_number != 0) {
        PyObject* cached = PythonObjectCache::getInstance().lookup(locked->serial_number);
        if (cached) return cached;  // new ref
    }

    auto type = &mcrfpydef::PyUIEntityType;
    auto o = (PyUIEntityObject*)type->tp_alloc(type, 0);
    if (!o) return PyErr_NoMemory();
    o->data = locked;
    o->weakreflist = NULL;
    return (PyObject*)o;
}

int UIGridView::set_perspective(PyUIGridViewObject* self, PyObject* value, void* closure)
{
    if (value == Py_None) {
        self->data->perspective_entity.reset();
        self->data->perspective_enabled = false;
        self->data->markDirty();
        return 0;
    }

    if (!PyObject_IsInstance(value, (PyObject*)&mcrfpydef::PyUIEntityType)) {
        PyErr_SetString(PyExc_TypeError, "perspective must be an Entity or None");
        return -1;
    }

    PyUIEntityObject* entity_obj = (PyUIEntityObject*)value;
    self->data->perspective_entity = entity_obj->data;
    self->data->perspective_enabled = true;
    self->data->markDirty();
    return 0;
}

PyObject* UIGridView::get_perspective_enabled(PyUIGridViewObject* self, void* closure)
{
    return PyBool_FromLong(self->data->perspective_enabled);
}

int UIGridView::set_perspective_enabled(PyUIGridViewObject* self, PyObject* value, void* closure)
{
    int enabled = PyObject_IsTrue(value);
    if (enabled == -1) return -1;
    self->data->perspective_enabled = enabled;
    self->data->markDirty();
    return 0;
}

PyObject* UIGridView::get_texture(PyUIGridViewObject* self, void* closure)
{
    // #318: return a Texture wrapper sharing the underlying shared_ptr<PyTexture>,
    // mirroring PyGridData::get_texture. None only when the view has no texture.
    auto& texture = self->data->ptex;
    if (!texture) Py_RETURN_NONE;

    auto type = &mcrfpydef::PyTextureType;
    auto obj = (PyTextureObject*)type->tp_alloc(type, 0);
    if (!obj) return NULL;
    obj->data = texture;
    return (PyObject*)obj;
}

// Float member getters/setters for GridView-specific float members (center_x, center_y, zoom, camera_rotation)
PyObject* UIGridView::get_float_member_gv(PyUIGridViewObject* self, void* closure)
{
    auto member_offset = (int)(intptr_t)closure;
    float value;
    switch (member_offset) {
        case 4: value = self->data->center_x; break;
        case 5: value = self->data->center_y; break;
        case 6: value = self->data->zoom; break;
        case 7: value = self->data->camera_rotation; break;
        default: PyErr_SetString(PyExc_RuntimeError, "Invalid member offset"); return NULL;
    }
    return PyFloat_FromDouble(value);
}

int UIGridView::set_float_member_gv(PyUIGridViewObject* self, PyObject* value, void* closure)
{
    float val;
    if (PyFloat_Check(value)) val = PyFloat_AsDouble(value);
    else if (PyLong_Check(value)) val = PyLong_AsLong(value);
    else { PyErr_SetString(PyExc_TypeError, "Value must be a number"); return -1; }

    auto member_offset = (int)(intptr_t)closure;
    switch (member_offset) {
        case 4: self->data->center_x = val; break;
        case 5: self->data->center_y = val; break;
        case 6: self->data->zoom = val; break;
        case 7: self->data->camera_rotation = val; break;
        default: PyErr_SetString(PyExc_RuntimeError, "Invalid member offset"); return -1;
    }
    self->data->markDirty();
    return 0;
}

// =========================================================================
// #355 - Cell input machinery (moved verbatim from UIGrid, retargeted to the view)
// =========================================================================

// Helper function to convert button string to MouseButton enum value
static int buttonStringToEnum(const std::string& button) {
    if (button == "left") return 0;       // MouseButton.LEFT
    if (button == "right") return 1;      // MouseButton.RIGHT
    if (button == "middle") return 2;     // MouseButton.MIDDLE
    if (button == "wheel_up") return 3;   // MouseButton.WHEEL_UP
    if (button == "wheel_down") return 4; // MouseButton.WHEEL_DOWN
    return 0; // Default to LEFT
}

// Helper function to convert action string to InputState enum value
static int actionStringToEnum(const std::string& action) {
    if (action == "start" || action == "pressed") return 0;   // InputState.PRESSED
    if (action == "end" || action == "released") return 1;    // InputState.RELEASED
    return 0; // Default to PRESSED
}

// Helper to create typed cell callback arguments: (Vector, MouseButton, InputState)
static PyObject* createCellCallbackArgs(sf::Vector2i cell, const std::string& button, const std::string& action) {
    PyObject* cell_pos = PyObject_CallFunction((PyObject*)&mcrfpydef::PyVectorType, "ff", (float)cell.x, (float)cell.y);
    if (!cell_pos) {
        PyErr_Print();
        return nullptr;
    }

    int button_val = buttonStringToEnum(button);
    PyObject* button_enum = PyObject_CallFunction(PyMouseButton::mouse_button_enum_class, "i", button_val);
    if (!button_enum) {
        Py_DECREF(cell_pos);
        PyErr_Print();
        return nullptr;
    }

    int action_val = actionStringToEnum(action);
    PyObject* action_enum = PyObject_CallFunction(PyInputState::input_state_enum_class, "i", action_val);
    if (!action_enum) {
        Py_DECREF(cell_pos);
        Py_DECREF(button_enum);
        PyErr_Print();
        return nullptr;
    }

    PyObject* args = Py_BuildValue("(OOO)", cell_pos, button_enum, action_enum);
    Py_DECREF(cell_pos);
    Py_DECREF(button_enum);
    Py_DECREF(action_enum);
    return args;
}

// #230 - Helper to create cell hover callback arguments: (Vector) only
static PyObject* createCellHoverArgs(sf::Vector2i cell) {
    PyObject* cell_pos = PyObject_CallFunction((PyObject*)&mcrfpydef::PyVectorType, "ii", cell.x, cell.y);
    if (!cell_pos) {
        PyErr_Print();
        return nullptr;
    }

    PyObject* args = Py_BuildValue("(O)", cell_pos);
    Py_DECREF(cell_pos);
    return args;
}

// #142 - Refresh cell callback cache for Python subclass method support
void UIGridView::refreshCellCallbackCache(PyObject* pyObj) {
    if (!pyObj || !is_python_subclass) {
        cell_callback_cache.valid = false;
        return;
    }

    // Get the class's callback generation counter
    PyObject* cls = (PyObject*)Py_TYPE(pyObj);
    uint32_t current_gen = 0;
    PyObject* gen_obj = PyObject_GetAttrString(cls, "_mcrf_callback_gen");
    if (gen_obj) {
        current_gen = static_cast<uint32_t>(PyLong_AsUnsignedLong(gen_obj));
        Py_DECREF(gen_obj);
    } else {
        PyErr_Clear();
    }

    if (cell_callback_cache.valid && cell_callback_cache.generation == current_gen) {
        return; // Cache is fresh
    }

    cell_callback_cache.has_on_cell_click = false;
    cell_callback_cache.has_on_cell_enter = false;
    cell_callback_cache.has_on_cell_exit = false;

    // Walk the class hierarchy down to (but not including) the base Grid type.
    // #355: sentinel is PyUIGridViewType -- mcrfpy.Grid IS UIGridView.
    PyTypeObject* type = Py_TYPE(pyObj);
    while (type && type != &mcrfpydef::PyUIGridViewType && type != &PyBaseObject_Type) {
        if (type->tp_dict) {
            if (!cell_callback_cache.has_on_cell_click) {
                PyObject* method = PyDict_GetItemString(type->tp_dict, "on_cell_click");
                if (method && PyCallable_Check(method)) {
                    cell_callback_cache.has_on_cell_click = true;
                }
            }
            if (!cell_callback_cache.has_on_cell_enter) {
                PyObject* method = PyDict_GetItemString(type->tp_dict, "on_cell_enter");
                if (method && PyCallable_Check(method)) {
                    cell_callback_cache.has_on_cell_enter = true;
                }
            }
            if (!cell_callback_cache.has_on_cell_exit) {
                PyObject* method = PyDict_GetItemString(type->tp_dict, "on_cell_exit");
                if (method && PyCallable_Check(method)) {
                    cell_callback_cache.has_on_cell_exit = true;
                }
            }
        }
        type = type->tp_base;
    }

    cell_callback_cache.generation = current_gen;
    cell_callback_cache.valid = true;
}

// Fire cell click callback with full signature (cell_pos, button, action)
bool UIGridView::fireCellClick(sf::Vector2i cell, const std::string& button, const std::string& action) {
    // Try property-assigned callback first
    if (on_cell_click_callable && !on_cell_click_callable->isNone()) {
        PyObject* args = createCellCallbackArgs(cell, button, action);
        if (args) {
            PyObject* result = PyObject_CallObject(on_cell_click_callable->borrow(), args);
            Py_DECREF(args);
            if (!result) {
                std::cerr << "Cell click callback raised an exception:" << std::endl;
                PyErr_Print();
                PyErr_Clear();
            } else {
                Py_DECREF(result);
            }
            return true;
        }
    }

    // Try Python subclass method
    if (is_python_subclass) {
        PyObject* pyObj = PythonObjectCache::getInstance().lookup(this->serial_number);
        if (pyObj) {
            refreshCellCallbackCache(pyObj);
            if (cell_callback_cache.has_on_cell_click) {
                PyObject* method = PyObject_GetAttrString(pyObj, "on_cell_click");
                if (method && PyCallable_Check(method)) {
                    PyObject* args = createCellCallbackArgs(cell, button, action);
                    if (args) {
                        PyObject* result = PyObject_CallObject(method, args);
                        Py_DECREF(args);
                        Py_DECREF(method);
                        Py_DECREF(pyObj);
                        if (!result) {
                            std::cerr << "Cell click method raised an exception:" << std::endl;
                            PyErr_Print();
                            PyErr_Clear();
                        } else {
                            Py_DECREF(result);
                        }
                        return true;
                    }
                }
                Py_XDECREF(method);
            }
            Py_DECREF(pyObj);
        }
    }
    return false;
}

// #230 - Fire cell enter callback with position-only signature (cell_pos)
bool UIGridView::fireCellEnter(sf::Vector2i cell) {
    if (on_cell_enter_callable && !on_cell_enter_callable->isNone()) {
        on_cell_enter_callable->call(cell);
        return true;
    }

    if (is_python_subclass) {
        PyObject* pyObj = PythonObjectCache::getInstance().lookup(this->serial_number);
        if (pyObj) {
            refreshCellCallbackCache(pyObj);
            if (cell_callback_cache.has_on_cell_enter) {
                PyObject* method = PyObject_GetAttrString(pyObj, "on_cell_enter");
                if (method && PyCallable_Check(method)) {
                    PyObject* args = createCellHoverArgs(cell);
                    if (args) {
                        PyObject* result = PyObject_CallObject(method, args);
                        Py_DECREF(args);
                        Py_DECREF(method);
                        Py_DECREF(pyObj);
                        if (!result) {
                            std::cerr << "Cell enter method raised an exception:" << std::endl;
                            PyErr_Print();
                            PyErr_Clear();
                        } else {
                            Py_DECREF(result);
                        }
                        return true;
                    }
                }
                Py_XDECREF(method);
            }
            Py_DECREF(pyObj);
        }
    }
    return false;
}

// #230 - Fire cell exit callback with position-only signature (cell_pos)
bool UIGridView::fireCellExit(sf::Vector2i cell) {
    if (on_cell_exit_callable && !on_cell_exit_callable->isNone()) {
        on_cell_exit_callable->call(cell);
        return true;
    }

    if (is_python_subclass) {
        PyObject* pyObj = PythonObjectCache::getInstance().lookup(this->serial_number);
        if (pyObj) {
            refreshCellCallbackCache(pyObj);
            if (cell_callback_cache.has_on_cell_exit) {
                PyObject* method = PyObject_GetAttrString(pyObj, "on_cell_exit");
                if (method && PyCallable_Check(method)) {
                    PyObject* args = createCellHoverArgs(cell);
                    if (args) {
                        PyObject* result = PyObject_CallObject(method, args);
                        Py_DECREF(args);
                        Py_DECREF(method);
                        Py_DECREF(pyObj);
                        if (!result) {
                            std::cerr << "Cell exit method raised an exception:" << std::endl;
                            PyErr_Print();
                            PyErr_Clear();
                        } else {
                            Py_DECREF(result);
                        }
                        return true;
                    }
                }
                Py_XDECREF(method);
            }
            Py_DECREF(pyObj);
        }
    }
    return false;
}

// #355 - UIDrawable input virtuals
bool UIGridView::dispatchCellClick(const std::string& button, const std::string& action)
{
    if (!last_clicked_cell.has_value()) return false;
    sf::Vector2i cell = last_clicked_cell.value();
    last_clicked_cell = std::nullopt;
    return fireCellClick(cell, button, action);
}

void UIGridView::updateHover(sf::Vector2f point, bool hit_allowed)
{
    // point is PARENT-local (same space as click_at); the view's own box position
    // takes it to widget-local, and cellAtLocal applies this view's camera.
    std::optional<sf::Vector2i> new_cell = std::nullopt;
    if (hit_allowed) new_cell = cellAtLocal(point - box.getPosition());
    if (new_cell != hovered_cell) {
        if (hovered_cell.has_value()) fireCellExit(hovered_cell.value());
        if (new_cell.has_value())     fireCellEnter(new_cell.value());
        hovered_cell = new_cell;
    }
}

// =========================================================================
// #355 - Cell callback properties (moved from UIGrid)
// =========================================================================
PyObject* UIGridView::get_on_cell_enter(PyUIGridViewObject* self, void* closure) {
    if (self->data->on_cell_enter_callable) {
        PyObject* cb = self->data->on_cell_enter_callable->borrow();
        Py_INCREF(cb);
        return cb;
    }
    Py_RETURN_NONE;
}

int UIGridView::set_on_cell_enter(PyUIGridViewObject* self, PyObject* value, void* closure) {
    if (value == Py_None) {
        self->data->on_cell_enter_callable.reset();
    } else {
        self->data->on_cell_enter_callable = std::make_unique<PyCellHoverCallable>(value);
    }
    return 0;
}

PyObject* UIGridView::get_on_cell_exit(PyUIGridViewObject* self, void* closure) {
    if (self->data->on_cell_exit_callable) {
        PyObject* cb = self->data->on_cell_exit_callable->borrow();
        Py_INCREF(cb);
        return cb;
    }
    Py_RETURN_NONE;
}

int UIGridView::set_on_cell_exit(PyUIGridViewObject* self, PyObject* value, void* closure) {
    if (value == Py_None) {
        self->data->on_cell_exit_callable.reset();
    } else {
        self->data->on_cell_exit_callable = std::make_unique<PyCellHoverCallable>(value);
    }
    return 0;
}

PyObject* UIGridView::get_on_cell_click(PyUIGridViewObject* self, void* closure) {
    if (self->data->on_cell_click_callable) {
        PyObject* cb = self->data->on_cell_click_callable->borrow();
        Py_INCREF(cb);
        return cb;
    }
    Py_RETURN_NONE;
}

int UIGridView::set_on_cell_click(PyUIGridViewObject* self, PyObject* value, void* closure) {
    if (value == Py_None) {
        self->data->on_cell_click_callable.reset();
    } else {
        self->data->on_cell_click_callable = std::make_unique<PyClickCallable>(value);
    }
    return 0;
}

// #364 - Overlay children. The collection's owner is the VIEW, so UICollection::append
// parents each child to a drawable that is actually in the scene graph: its dirty push
// then reaches this view and every caching ancestor above it.
PyObject* UIGridView::get_children(PyUIGridViewObject* self, void* closure)
{
    PyTypeObject* type = &mcrfpydef::PyUICollectionType;
    auto o = (PyUICollectionObject*)type->tp_alloc(type, 0);
    if (o) {
        o->data = self->data->children;
        o->owner = self->data;
    }
    return (PyObject*)o;
}

PyObject* UIGridView::get_hovered_cell(PyUIGridViewObject* self, void* closure) {
    if (self->data->hovered_cell.has_value()) {
        return Py_BuildValue("(ii)", self->data->hovered_cell->x, self->data->hovered_cell->y);
    }
    Py_RETURN_NONE;
}

// =========================================================================
// Subscript protocol: grid[x, y] -> GridPoint (delegates to GridData).
// Setitem raises TypeError (GridPoints are views, not assignable).
// =========================================================================
PyObject* UIGridView::subscript(PyUIGridViewObject* self, PyObject* key)
{
    if (!self->data || !self->data->grid_data) {
        PyErr_SetString(PyExc_RuntimeError, "Grid has no underlying data");
        return NULL;
    }
    if (!PyTuple_Check(key) || PyTuple_Size(key) != 2) {
        PyErr_SetString(PyExc_TypeError, "Grid indices must be a 2-tuple (x, y)");
        return NULL;
    }
    PyObject* x_obj = PyTuple_GetItem(key, 0);
    PyObject* y_obj = PyTuple_GetItem(key, 1);
    if (!PyLong_Check(x_obj) || !PyLong_Check(y_obj)) {
        PyErr_SetString(PyExc_TypeError, "Grid indices must be integers");
        return NULL;
    }
    int x = (int)PyLong_AsLong(x_obj);
    int y = (int)PyLong_AsLong(y_obj);

    auto& grid_data = self->data->grid_data;
    if (x < 0 || x >= grid_data->grid_w) {
        PyErr_Format(PyExc_IndexError, "x index %d is out of range [0, %d)",
            x, grid_data->grid_w);
        return NULL;
    }
    if (y < 0 || y >= grid_data->grid_h) {
        PyErr_Format(PyExc_IndexError, "y index %d is out of range [0, %d)",
            y, grid_data->grid_h);
        return NULL;
    }

    auto type = &mcrfpydef::PyUIGridPointType;
    auto obj = (PyUIGridPointObject*)type->tp_alloc(type, 0);
    if (!obj) return NULL;
    obj->grid = grid_data;  // #361: the GridPoint holds the map directly
    obj->x = x;
    obj->y = y;
    return (PyObject*)obj;
}

int UIGridView::subscript_assign(PyUIGridViewObject* self, PyObject* key, PyObject* value)
{
    (void)self; (void)key; (void)value;
    PyErr_SetString(PyExc_TypeError,
        "Grid points are not assignable; modify properties on the returned point");
    return -1;
}

PyMappingMethods UIGridView::mpmethods = {
    .mp_length = NULL,
    .mp_subscript = (binaryfunc)UIGridView::subscript,
    .mp_ass_subscript = (objobjargproc)UIGridView::subscript_assign,
};

// #252: PyObjectType typedef for UIDRAWABLE_* macros
typedef PyUIGridViewObject PyObjectType;

// Methods and getsetters arrays
PyMethodDef UIGridView_all_methods[] = {
    UIDRAWABLE_METHODS,
    {"center_camera", (PyCFunction)UIGridView::py_center_camera, METH_VARARGS,
     MCRF_METHOD(GridView, center_camera,
         MCRF_SIG("(pos: tuple = None)", "None"),
         MCRF_DESC("Point this view's camera at a tile, or at the middle of the map when "
                   "called with no argument.")
         MCRF_ARGS_START
         MCRF_ARG("pos", "(tile_x, tile_y) to center on. Offset by 0.5 to aim at a tile's "
                         "middle rather than its top-left corner.")
         MCRF_NOTE("The camera belongs to the VIEW, not the map: two views of one GridData "
                   "pan independently.")
     )},
    {NULL}
};

// GridView getsetters for view-specific AND UIDrawable base properties.
// Data properties (entities, grid_size, layers, etc.) are accessed via getattro delegation.
PyGetSetDef UIGridView::getsetters[] = {
    {"grid_data", (getter)UIGridView::get_grid, (setter)UIGridView::set_grid,
     MCRF_PROPERTY(grid_data, "The underlying grid data object (Grid | None). Used for multi-view scenarios where multiple GridViews share one Grid."), NULL},
    {"children", (getter)UIGridView::get_children, NULL,
     MCRF_PROPERTY(children,
         "UICollection of UIDrawable children such as speech bubbles, effects, and range "
         "indicators anchored to grid content (UICollection, read-only)."
         MCRF_NOTE(
             "Grid children are positioned in the grid's pixel-world coordinates -- the same "
             "origin as Entity positions -- NOT in the grid widget's screen-space pixels. They "
             "pan and zoom with the grid camera (center, zoom), so a child placed near an "
             "entity stays near that entity as the camera moves. This differs from "
             "Frame.children, which are frame-local: since a Frame cannot pan its content, "
             "Frame children are effectively already in screen coordinates. If you want UI "
             "that floats over the grid regardless of camera position (e.g. a HUD), do not use "
             "Grid.children -- add a sibling Frame with the same pos/size as the Grid instead."
         )
         MCRF_NOTE(
             "Children belong to the VIEW, not to the shared grid data: they are overlays drawn "
             "through this camera, so two views over one grid have independent children (a "
             "minimap does not inherit the main view's speech bubbles) while sharing every "
             "entity. Entities are the world contents; children are annotations over them."
         )
         MCRF_LINK("docs/grid-coordinate-spaces.md", "Grid Coordinate Spaces & Overlay Pattern")
     ), NULL},
    {"center", (getter)UIGridView::get_center, (setter)UIGridView::set_center,
     MCRF_PROPERTY(center, "Camera center point in pixel coordinates (Vector)."), NULL},
    {"size", (getter)UIGridView::get_size, (setter)UIGridView::set_size,
     MCRF_PROPERTY(size, "Size of the grid widget in pixels as (w, h) (Vector). This is the "
                         "viewport, not the map: the map's dimensions are grid_size."), NULL},
    {"zoom", (getter)UIGridView::get_zoom, (setter)UIGridView::set_zoom,
     MCRF_PROPERTY(zoom, "Zoom level for rendering (float). Values greater than 1.0 magnify; less than 1.0 shrink."), NULL},
    {"fill_color", (getter)UIGridView::get_fill_color, (setter)UIGridView::set_fill_color,
     MCRF_PROPERTY(fill_color, "Background fill color (Color). Drawn behind all tiles and entities."), NULL},
    // #318/#252: this type is exposed as BOTH mcrfpy.Grid and mcrfpy.GridView, so the
    // docstring is kept type-neutral (accurate for either name).
    {"texture", (getter)UIGridView::get_texture, NULL,
     MCRF_PROPERTY(texture, "Texture used for tile rendering (Texture | None, read-only)."), NULL},
    // UIDrawable base properties - applied to GridView (the rendered object)
    {"pos", (getter)UIDrawable::get_pos, (setter)UIDrawable::set_pos,
     MCRF_PROPERTY(pos, "Position of the grid as Vector (Vector)."), (void*)PyObjectsEnum::UIGRIDVIEW},
    {"x", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member,
     MCRF_PROPERTY(x, "Top-left corner X-coordinate (float)."), (void*)((intptr_t)PyObjectsEnum::UIGRIDVIEW << 8 | 0)},
    {"y", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member,
     MCRF_PROPERTY(y, "Top-left corner Y-coordinate (float)."), (void*)((intptr_t)PyObjectsEnum::UIGRIDVIEW << 8 | 1)},
    {"w", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member,
     MCRF_PROPERTY(w, "Visible widget width (float)."), (void*)((intptr_t)PyObjectsEnum::UIGRIDVIEW << 8 | 2)},
    {"h", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member,
     MCRF_PROPERTY(h, "Visible widget height (float)."), (void*)((intptr_t)PyObjectsEnum::UIGRIDVIEW << 8 | 3)},
    {"center_x", (getter)UIGridView::get_float_member_gv, (setter)UIGridView::set_float_member_gv,
     MCRF_PROPERTY(center_x, "Camera center X-coordinate in pixel space (float)."), (void*)4},
    {"center_y", (getter)UIGridView::get_float_member_gv, (setter)UIGridView::set_float_member_gv,
     MCRF_PROPERTY(center_y, "Camera center Y-coordinate in pixel space (float)."), (void*)5},
    {"camera_rotation", (getter)UIGridView::get_float_member_gv, (setter)UIGridView::set_float_member_gv,
     MCRF_PROPERTY(camera_rotation, "Rotation of grid contents around camera center in degrees (float)."), (void*)7},
    {"on_click", (getter)UIDrawable::get_click, (setter)UIDrawable::set_click,
     MCRF_PROPERTY(on_click, "Callable executed when object is clicked (Callable | None)."), (void*)PyObjectsEnum::UIGRIDVIEW},
    {"z_index", (getter)UIDrawable::get_int, (setter)UIDrawable::set_int,
     MCRF_PROPERTY(z_index, "Z-order for rendering (int). Lower values are rendered first."), (void*)PyObjectsEnum::UIGRIDVIEW},
    {"name", (getter)UIDrawable::get_name, (setter)UIDrawable::set_name,
     MCRF_PROPERTY(name, "Name for finding elements (str)."), (void*)PyObjectsEnum::UIGRIDVIEW},
    UIDRAWABLE_GETSETTERS,
    UIDRAWABLE_PARENT_GETSETTERS(PyObjectsEnum::UIGRIDVIEW),
    UIDRAWABLE_ALIGNMENT_GETSETTERS(PyObjectsEnum::UIGRIDVIEW),
    UIDRAWABLE_ROTATION_GETSETTERS(PyObjectsEnum::UIGRIDVIEW),
    UIDRAWABLE_SHADER_GETSETTERS(PyObjectsEnum::UIGRIDVIEW),
    // #355 - cell input properties (moved from _GridData to the view)
    {"on_cell_enter", (getter)UIGridView::get_on_cell_enter, (setter)UIGridView::set_on_cell_enter,
     MCRF_PROPERTY(on_cell_enter, "Callback when mouse enters a grid cell (Callable | None). Called with (cell_pos: Vector)."), NULL},
    {"on_cell_exit", (getter)UIGridView::get_on_cell_exit, (setter)UIGridView::set_on_cell_exit,
     MCRF_PROPERTY(on_cell_exit, "Callback when mouse exits a grid cell (Callable | None). Called with (cell_pos: Vector)."), NULL},
    {"on_cell_click", (getter)UIGridView::get_on_cell_click, (setter)UIGridView::set_on_cell_click,
     MCRF_PROPERTY(on_cell_click, "Callback when a grid cell is clicked (Callable | None). Called with (cell_pos: Vector, button: MouseButton, action: InputState)."), NULL},
    {"hovered_cell", (getter)UIGridView::get_hovered_cell, NULL,
     MCRF_PROPERTY(hovered_cell, "Currently hovered cell as (x, y) tuple, or None if not hovering (tuple | None, read-only)."), NULL},
    // #355 - perspective moved from _GridData to the view: render() draws the FOV
    // overlay, so the view must own the state it gates on. Per-view, so two views
    // of one grid can follow different entities.
    {"perspective", (getter)UIGridView::get_perspective, (setter)UIGridView::set_perspective,
     MCRF_PROPERTY(perspective,
         "Entity whose perspective_map drives fog-of-war rendering in this view (Entity | None). "
         "Setting an entity enables perspective mode; setting None disables it. "
         "Cells the entity has never seen are drawn black, discovered-but-not-visible cells dimmed."), NULL},
    {"perspective_enabled", (getter)UIGridView::get_perspective_enabled, (setter)UIGridView::set_perspective_enabled,
     MCRF_PROPERTY(perspective_enabled,
         "Whether this view renders the perspective/FOV overlay (bool). "
         "Set automatically when assigning perspective; set False to show the whole map without clearing the entity."), NULL},
    {NULL}
};
