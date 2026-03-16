// GridData.cpp - Pure data layer implementation (#252)
#include "GridData.h"
#include "UIEntity.h"
#include "PyTexture.h"
#include <algorithm>

GridData::GridData()
{
    entities = std::make_shared<std::list<std::shared_ptr<UIEntity>>>();
    children = std::make_shared<std::vector<std::shared_ptr<UIDrawable>>>();
}

GridData::~GridData()
{
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
    use_chunks = (gx > CHUNK_THRESHOLD || gy > CHUNK_THRESHOLD);

    if (tcod_map) delete tcod_map;
    tcod_map = new TCODMap(gx, gy);

    if (use_chunks) {
        chunk_manager = std::make_unique<ChunkManager>(gx, gy, parent_ref);
        for (int cy = 0; cy < chunk_manager->chunks_y; ++cy) {
            for (int cx = 0; cx < chunk_manager->chunks_x; ++cx) {
                GridChunk* chunk = chunk_manager->getChunk(cx, cy);
                if (!chunk) continue;
                for (int ly = 0; ly < chunk->height; ++ly) {
                    for (int lx = 0; lx < chunk->width; ++lx) {
                        auto& cell = chunk->at(lx, ly);
                        cell.grid_x = chunk->world_x + lx;
                        cell.grid_y = chunk->world_y + ly;
                        cell.parent_grid = parent_ref;
                    }
                }
            }
        }
    } else {
        points.resize(gx * gy);
        for (int y = 0; y < gy; y++) {
            for (int x = 0; x < gx; x++) {
                int idx = y * gx + x;
                points[idx].grid_x = x;
                points[idx].grid_y = y;
                points[idx].parent_grid = parent_ref;
            }
        }
    }

    syncTCODMap();
}

// Cell access
UIGridPoint& GridData::at(int x, int y)
{
    if (use_chunks && chunk_manager) {
        return chunk_manager->at(x, y);
    }
    return points[y * grid_w + x];
}

// TCOD integration
void GridData::syncTCODMap()
{
    if (!tcod_map) return;
    for (int y = 0; y < grid_h; y++) {
        for (int x = 0; x < grid_w; x++) {
            const UIGridPoint& point = at(x, y);
            tcod_map->setProperties(x, y, point.transparent, point.walkable);
        }
    }
    fov_dirty = true;
}

void GridData::syncTCODMapCell(int x, int y)
{
    if (!tcod_map || x < 0 || x >= grid_w || y < 0 || y >= grid_h) return;
    const UIGridPoint& point = at(x, y);
    tcod_map->setProperties(x, y, point.transparent, point.walkable);
    fov_dirty = true;
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
    return layer;
}

std::shared_ptr<TileLayer> GridData::addTileLayer(int z_index, std::shared_ptr<PyTexture> texture, const std::string& name)
{
    auto layer = std::make_shared<TileLayer>(z_index, grid_w, grid_h, this, texture);
    layer->name = name;
    layers.push_back(layer);
    layers_need_sort = true;
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
