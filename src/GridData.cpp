// GridData.cpp - Pure data layer implementation (#252)
#include "GridData.h"
#include "UIEntity.h"
#include "PyTexture.h"
#include "UIGrid.h"      // #313 - markDirty forwards to the UIGrid subobject
#include "UIGridView.h"  // #313 - and notifies owning_view
#include <algorithm>

// #313 - Render invalidation from the data layer (see GridData.h).
// GridData is never independently heap-allocated (always a UIGrid base
// subobject), so the downcast is valid; remove once #252 allows pure GridData.
void GridData::markDirty() {
    content_generation++;  // #351 - content changed; invalidate view early-out
    static_cast<UIGrid*>(this)->UIDrawable::markDirty();
    if (auto view = owning_view.lock()) {
        view->markDirty();
    }
}

void GridData::markCompositeDirty() {
    content_generation++;  // #351 - content changed; invalidate view early-out
    static_cast<UIGrid*>(this)->UIDrawable::markCompositeDirty();
    if (auto view = owning_view.lock()) {
        view->markCompositeDirty();
    }
}

GridData::GridData()
{
    entities = std::make_shared<std::vector<std::shared_ptr<UIEntity>>>();  // #329
    children = std::make_shared<std::vector<std::shared_ptr<UIDrawable>>>();
}

GridData::~GridData()
{
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
    dijkstra_maps.clear();
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

// Layer management
std::shared_ptr<ColorLayer> GridData::addColorLayer(int z_index, const std::string& name)
{
    auto layer = std::make_shared<ColorLayer>(z_index, grid_w, grid_h, this);
    layer->name = name;
    layers.push_back(layer);
    layers_need_sort = true;
    content_generation++;  // #351 - layer set changed
    return layer;
}

std::shared_ptr<TileLayer> GridData::addTileLayer(int z_index, std::shared_ptr<PyTexture> texture, const std::string& name)
{
    auto layer = std::make_shared<TileLayer>(z_index, grid_w, grid_h, this, texture);
    layer->name = name;
    layers.push_back(layer);
    layers_need_sort = true;
    content_generation++;  // #351 - layer set changed
    return layer;
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
    content_generation++;  // #351 - layer set changed
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
