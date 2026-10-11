// GridData.cpp - Pure data layer implementation (#252)
#include "GridData.h"
#include "UIEntity.h"
#include "PyTexture.h"
#include "UIGridView.h"        // #313/#359 - markDirty notifies registered views
#include "PyWrap.h"
#include "McRFPy_API.h"
#include <algorithm>

// #313/#361 - Render invalidation from the data layer (see GridData.h).
// Notifies every registered view; there is no longer a drawable half of `this`
// to notify.
void GridData::markDirty() {
    content_generation++;  // #351 - content changed; invalidate view early-out
    for (auto& weak_view : views) {
        if (auto view = weak_view.lock()) view->markDirty();
    }
}

void GridData::markCompositeDirty() {
    content_generation++;  // #351 - content changed; invalidate view early-out
    for (auto& weak_view : views) {
        if (auto view = weak_view.lock()) view->markCompositeDirty();
    }
}

// #359 - View registry (see GridData.h). Kept small (typically 1-2 entries:
// split-screen / minimap use cases), so linear scan is fine.
void GridData::registerView(const std::shared_ptr<UIGridView>& view) {
    if (!view) return;
    for (auto& weak_view : views) {
        if (weak_view.lock() == view) return;  // already registered
    }
    views.push_back(view);
}

void GridData::unregisterView(UIGridView* view) {
    views.erase(
        std::remove_if(views.begin(), views.end(),
            [view](const std::weak_ptr<UIGridView>& weak_view) {
                auto locked = weak_view.lock();
                return !locked || locked.get() == view;  // prune expired too
            }),
        views.end());
}

std::shared_ptr<UIGridView> GridData::primaryView() const {
    for (auto& weak_view : views) {
        if (auto view = weak_view.lock()) return view;
    }
    return nullptr;
}

GridData::GridData()
{
    entities = std::make_shared<std::vector<std::shared_ptr<UIEntity>>>();  // #329
    // #364: children live on UIGridView, not here -- see GridData.h.
}

// #361 - The real constructor. A texture fills the cell size (#453); without one
// it stays unset and reads 1x1 until a texture or a size is given.
GridData::GridData(int gx, int gy, std::shared_ptr<PyTexture> texture)
: ptex(texture)
{
    entities = std::make_shared<std::vector<std::shared_ptr<UIEntity>>>();  // #329
    if (ptex) cell_size = sf::Vector2i(ptex->sprite_width, ptex->sprite_height);
    initStorage(gx, gy, this);
}

// #453 - cell size (see GridData.h)
sf::Vector2i GridData::cellSize() const
{
    if (cell_size) return *cell_size;
    if (ptex) return sf::Vector2i(ptex->sprite_width, ptex->sprite_height);
    return sf::Vector2i(1, 1);
}

void GridData::setCellSize(std::optional<sf::Vector2i> size)
{
    sf::Vector2i old = cellSize();
    cell_size = size;
    if (cellSize() != old) cellSizeChanged(old);
}

void GridData::setTexture(std::shared_ptr<PyTexture> texture)
{
    sf::Vector2i old = cellSize();
    ptex = std::move(texture);
    if (ptex && !cell_size) cell_size = sf::Vector2i(ptex->sprite_width, ptex->sprite_height);
    // Layers that inherit notice the new texture when they draw (TileLayer::render);
    // this repaints the views so they do draw.
    if (cellSize() != old) cellSizeChanged(old);
    else markDirty();
}

void GridData::cellSizeChanged(sf::Vector2i old)
{
    sf::Vector2i now = cellSize();
    for (auto& weak_view : views) {
        if (auto view = weak_view.lock()) view->onCellSizeChanged(old, now);
    }
    for (auto& layer : layers) {
        if (layer) layer->markDirty();   // chunks are rasterized at the cell size
    }
    markDirty();
}

bool GridData::ensureTextureForDrawing()
{
    if (ptex) return true;
    auto texture = McRFPy_API::defaultTexture();
    if (!texture) return false;
    if (PyErr_WarnEx(McRFPy_API::texture_warning,
            "a grid with no texture is being drawn; using mcrfpy.default_texture. Give the "
            "GridData (or Grid) a texture=, or set its cell_size to keep the size it "
            "calculates with.", 1) < 0) {
        return false;
    }
    setTexture(texture);
    return true;
}

GridData::~GridData()
{
    // #361: GridData carries its own PythonObjectCache serial now that it is
    // not a UIDrawable (which used to do this in ~UIDrawable).
    if (serial_number != 0) mcrf::unregister_wrapper(serial_number);
    if (entities_serial != 0) mcrf::unregister_wrapper(entities_serial);

    // #437: entities that outlive their grid are detached, which also releases their
    // identity pins (#436). The vector still owns each entity during the loop, so a
    // released pin can't free an entity out from under us.
    if (entities) {
        for (auto& e : *entities) {
            if (e) e->setGrid(nullptr);
        }
    }

    // #270: Null out parent_grid in all layers so surviving shared_ptrs
    // (held by Python wrappers) don't dangle after grid destruction
    for (auto& layer : layers) {
        if (layer) layer->parent_grid = nullptr;
    }

    // #332: cell storage is now plain uint8 planes (no per-cell back-pointers
    // to null out; they free with the vectors).

    cleanupTCOD();
}

void GridData::cleanupTCOD()
{
    dijkstra_cache.clear();
    if (tcod_map) {
        delete tcod_map;
        tcod_map = nullptr;
    }
}

void GridData::initStorage(int gx, int gy, GridData* parent_ref)
{
    grid_w = gx;
    grid_h = gy;
    (void)parent_ref;  // #332 - planes need no per-cell back-pointer

    if (tcod_map) delete tcod_map;
    tcod_map = new TCODMap(gx, gy);

    // #332 - dense uint8 planes; default cells are not walkable / not
    // transparent (matches the former UIGridPoint() default).
    walkable_plane.assign((size_t)gx * (size_t)gy, 0);
    transparent_plane.assign((size_t)gx * (size_t)gy, 0);

    syncTCODMap();
}

// TCOD integration
void GridData::syncTCODMap()
{
    if (!tcod_map) return;
    for (int y = 0; y < grid_h; y++) {
        for (int x = 0; x < grid_w; x++) {
            tcod_map->setProperties(x, y, isTransparent(x, y), isWalkable(x, y));
        }
    }
    fov_dirty = true;
    transparency_generation++;
}

void GridData::syncTCODMapCell(int x, int y)
{
    if (!tcod_map || x < 0 || x >= grid_w || y < 0 || y >= grid_h) return;
    tcod_map->setProperties(x, y, isTransparent(x, y), isWalkable(x, y));
    fov_dirty = true;
    transparency_generation++;
}

void GridData::computeFOV(int x, int y, int radius, bool light_walls, TCOD_fov_algorithm_t algo)
{
    if (!tcod_map || x < 0 || x >= grid_w || y < 0 || y >= grid_h) return;

    if (!fov_dirty &&
        x == fov_last_x && y == fov_last_y &&
        radius == fov_last_radius &&
        light_walls == fov_last_light_walls &&
        algo == fov_last_algo) {
        return;
    }

    std::lock_guard<std::mutex> lock(fov_mutex);
    tcod_map->computeFov(x, y, radius, light_walls, algo);

    fov_dirty = false;
    fov_last_x = x;
    fov_last_y = y;
    fov_last_radius = radius;
    fov_last_light_walls = light_walls;
    fov_last_algo = algo;
}

bool GridData::isInFOV(int x, int y) const
{
    if (!tcod_map || x < 0 || x >= grid_w || y < 0 || y >= grid_h) return false;
    std::lock_guard<std::mutex> lock(fov_mutex);
    return tcod_map->isInFov(x, y);
}

// #402 - see the contract in GridData.h.
bool GridData::computeFOVInto(int x, int y, int radius, bool light_walls,
                              TCOD_fov_algorithm_t algo, std::vector<uint8_t>& out) const
{
    out.assign((size_t)grid_w * (size_t)grid_h, 0);
    if (!tcod_map || x < 0 || x >= grid_w || y < 0 || y >= grid_h) return false;

    // The scratch map is built from GridData's own transparency/walkability planes,
    // NOT copied from tcod_map. Two reasons, both deliberate:
    //   * the planes are the source of truth that syncTCODMap() itself writes from,
    //     so this cannot inherit a stale shared map, and
    //   * it reads nothing from tcod_map at all, so no lock over the shared map is
    //     needed and no ordering with another caller's compute exists to get wrong.
    TCODMap scratch(grid_w, grid_h);
    for (int cy = 0; cy < grid_h; cy++) {
        for (int cx = 0; cx < grid_w; cx++) {
            scratch.setProperties(cx, cy, isTransparent(cx, cy), isWalkable(cx, cy));
        }
    }

    scratch.computeFov(x, y, radius, light_walls, algo);

    for (int cy = 0; cy < grid_h; cy++) {
        for (int cx = 0; cx < grid_w; cx++) {
            out[(size_t)cy * grid_w + cx] = scratch.isInFov(cx, cy) ? 1 : 0;
        }
    }
    return true;
}

// Layer management
std::shared_ptr<ColorLayer> GridData::addColorLayer(int z_index, const std::string& name)
{
    auto layer = std::make_shared<ColorLayer>(z_index, grid_w, grid_h, this);
    layer->name = name;
    layers.push_back(layer);
    layers_need_sort = true;
    markDirty();  // #427 - layer set changed; reaches views and their parents
    return layer;
}

std::shared_ptr<TileLayer> GridData::addTileLayer(int z_index, std::shared_ptr<PyTexture> texture, const std::string& name)
{
    auto layer = std::make_shared<TileLayer>(z_index, grid_w, grid_h, this, texture);
    layer->name = name;
    layers.push_back(layer);
    layers_need_sort = true;
    markDirty();  // #427 - layer set changed; reaches views and their parents
    return layer;
}

void GridData::attachLayer(std::shared_ptr<GridLayer> layer)
{
    layer->parent_grid = this;
    layers.push_back(std::move(layer));
    layers_need_sort = true;
    markDirty();  // #427 - layer set changed; reaches views and their parents
}

void GridData::removeLayer(std::shared_ptr<GridLayer> layer)
{
    auto it = std::find(layers.begin(), layers.end(), layer);
    if (it != layers.end()) {
        layers.erase(it);
    }
    if (layer) {
        layer->parent_grid = nullptr;
    }
    markDirty();  // #427 - layer set changed; reaches views and their parents
}

void GridData::sortLayers()
{
    if (layers_need_sort) {
        std::sort(layers.begin(), layers.end(),
            [](const auto& a, const auto& b) { return a->z_index < b->z_index; });
        layers_need_sort = false;
    }
}

std::shared_ptr<GridLayer> GridData::getLayerByName(const std::string& name)
{
    if (name.empty()) return nullptr;
    for (auto& layer : layers) {
        if (layer->name == name) return layer;
    }
    return nullptr;
}

bool GridData::isProtectedLayerName(const std::string& name)
{
    static const std::vector<std::string> protected_names = {
        "walkable", "transparent"
    };
    for (const auto& pn : protected_names) {
        if (name == pn) return true;
    }
    return false;
}

// =========================================================================
// #441: GC ownership -- see mcrf::owns_exclusively (PyWrap.h)
// =========================================================================

long GridData::wrapperKeepers(const PyObject* wrapper) const
{
    long n = 0;
    for (const auto& weak_view : views) {
        auto view = weak_view.lock();
        if (view && view->grid_data.get() == this && view->cached_grid_wrapper == wrapper) ++n;
    }
    return n;
}

int GridData::traverseOwned(visitproc visit, void* arg)
{
    // The entity collection wrapper shares the vector and can outlive this map.
    if (!entities || entities.use_count() != 1) return 0;
    for (const auto& e : *entities) {
        if (!e) continue;
        if (e->identity_pin.pinned()) {
            if (e->getGrid().get() == this) MCRF_VISIT(e->identity_pin.visit(visit, arg));
        } else if (e.use_count() == 1) {
            MCRF_VISIT(e->traverseOwned(visit, arg));
        }
    }
    return 0;
}

void GridData::clearOwned()
{
    if (!entities || entities.use_count() != 1) return;
    // Decide first, act second: detaching releases a pin, which can free a wrapper.
    std::vector<std::shared_ptr<UIEntity>> detach, descend;
    for (const auto& e : *entities) {
        if (!e) continue;
        if (e->identity_pin.pinned()) {
            if (e->getGrid().get() == this) detach.push_back(e);
        } else if (e.use_count() == 1) {
            descend.push_back(e);
        }
    }
    for (auto& e : descend) e->clearOwned();
    // What ~GridData does to entities that outlive it (#437).
    for (auto& e : detach) e->setGrid(nullptr);
}
