#pragma once
// GridData.h - Pure data layer for grid state (#252)
//
// GridData holds all non-rendering grid state: cells, entities, TCOD map,
// spatial hash, layers, FOV, pathfinding caches. UIGrid inherits from this
// and adds rendering. GridView can also reference GridData for multi-view.

#include "Common.h"
#include "Python.h"
#include <list>
#include <libtcod.h>
#include <mutex>
#include <optional>
#include <map>
#include <memory>
#include <tuple>
#include <vector>

#include "PyCallable.h"
#include "UIGridPoint.h"
#include "SpatialHash.h"
#include "GridLayers.h"
#include "GridChunk.h"

// Forward declarations
class DijkstraMap;
class UIEntity;
class UIDrawable;
class UIGridView;
class PyTexture;

class GridData {
public:
    GridData();
    virtual ~GridData();

    // =========================================================================
    // Grid dimensions and cell storage
    // =========================================================================
    int grid_w = 0, grid_h = 0;

    // #313 - Cell pixel dimensions, mirrored from the owning UIGrid's texture
    // at construction (UIGrid::ptex is write-once, ctor only). Lets the data
    // layer do tile<->pixel math without reaching into rendering state.
    int cell_width_px = 16;
    int cell_height_px = 16;
    int cell_width() const { return cell_width_px; }
    int cell_height() const { return cell_height_px; }

    // #123 - Chunk-based storage for large grid support
    std::unique_ptr<ChunkManager> chunk_manager;
    // Legacy flat storage (kept for small grids or compatibility)
    std::vector<UIGridPoint> points;
    // Use chunks for grids larger than this threshold
    static constexpr int CHUNK_THRESHOLD = 64;
    bool use_chunks = false;

    // Cell access (handles both flat and chunked storage)
    UIGridPoint& at(int x, int y);

    // =========================================================================
    // Entity management
    // =========================================================================
    // #329 - std::vector (was std::list) so grid.entities[i] is O(1). Entity
    // addresses stay stable via shared_ptr; only node-iterator assumptions
    // changed (audited: none remain -- all call sites use begin/end/erase/
    // push_back/find_if, and grid.step() snapshots into a local vector).
    std::shared_ptr<std::vector<std::shared_ptr<UIEntity>>> entities;
    SpatialHash spatial_hash;  // O(1) entity queries (#115)

    // =========================================================================
    // TCOD integration (FOV and pathfinding base)
    // =========================================================================
    TCODMap* tcod_map = nullptr;
    mutable std::mutex fov_mutex;

    void syncTCODMap();
    void syncTCODMapCell(int x, int y);
    void computeFOV(int x, int y, int radius, bool light_walls = true,
                    TCOD_fov_algorithm_t algo = FOV_BASIC);
    bool isInFOV(int x, int y) const;
    TCODMap* getTCODMap() const { return tcod_map; }

    // #114 - FOV algorithm and radius defaults
    TCOD_fov_algorithm_t fov_algorithm = FOV_BASIC;
    int fov_radius = 10;

    // #292 - FOV deduplication
    bool fov_dirty = true;
    int fov_last_x = -1, fov_last_y = -1;
    int fov_last_radius = -1;
    bool fov_last_light_walls = true;
    TCOD_fov_algorithm_t fov_last_algo = FOV_BASIC;

    // #303 - Transparency generation counter for per-entity FOV caching
    // Bumped whenever any cell's transparent/walkable property changes
    uint32_t transparency_generation = 0;

    // =========================================================================
    // Pathfinding caches
    // =========================================================================
    // Cache key: (root_x, root_y, collide_label) where collide_label="" means no collision filtering
    std::map<std::tuple<int,int,std::string>, std::shared_ptr<DijkstraMap>> dijkstra_maps;

    // =========================================================================
    // Layer system (#147, #150)
    // =========================================================================
    std::vector<std::shared_ptr<GridLayer>> layers;
    bool layers_need_sort = true;

    std::shared_ptr<ColorLayer> addColorLayer(int z_index, const std::string& name = "");
    std::shared_ptr<TileLayer> addTileLayer(int z_index, std::shared_ptr<PyTexture> texture = nullptr,
                                             const std::string& name = "");
    void removeLayer(std::shared_ptr<GridLayer> layer);
    void sortLayers();
    std::shared_ptr<GridLayer> getLayerByName(const std::string& name);
    static bool isProtectedLayerName(const std::string& name);

    // =========================================================================
    // Cell callbacks (#142, #230)
    // =========================================================================
    std::unique_ptr<PyCellHoverCallable> on_cell_enter_callable;
    std::unique_ptr<PyCellHoverCallable> on_cell_exit_callable;
    std::unique_ptr<PyClickCallable> on_cell_click_callable;
    std::optional<sf::Vector2i> hovered_cell;
    std::optional<sf::Vector2i> last_clicked_cell;

    struct CellCallbackCache {
        uint32_t generation = 0;
        bool valid = false;
        bool has_on_cell_click = false;
        bool has_on_cell_enter = false;
        bool has_on_cell_exit = false;
    };
    CellCallbackCache cell_callback_cache;

    // fireCellClick/Enter/Exit and refreshCellCallbackCache are on UIGrid
    // because they need access to UIDrawable::serial_number/is_python_subclass

    // =========================================================================
    // UIDrawable children (speech bubbles, effects, overlays)
    // =========================================================================
    std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>> children;
    bool children_need_sort = true;

    // =========================================================================
    // #252 - Owning GridView back-reference (for Entity.grid → GridView lookup)
    // =========================================================================
    std::weak_ptr<UIGridView> owning_view;

    // #351 - Monotonic counter bumped whenever grid content drawn into a view's
    // RenderTexture changes (entities added/removed/moved, sprite changes, layer
    // edits, layer add/remove). UIGridView compares it against the generation it
    // last rendered to skip re-rasterizing an unchanged grid. Camera parameters
    // live on the view and are compared there directly, not counted here.
    uint64_t content_generation = 0;

    // #313 - Render invalidation from the data layer. Entities hold
    // shared_ptr<GridData> but still need to invalidate rendering when their
    // visual state changes. These set the dirty flags on the UIGrid subobject
    // (GridData is never independently heap-allocated -- always a UIGrid base)
    // AND notify owning_view, covering both render paths (a bare _GridData
    // rendered directly, and the normal GridView). Within UIGrid itself the
    // UIDrawable versions win via using-declarations (see UIGrid.h).
    // Multi-view broadcast (secondary views) is deferred to #252.
    void markDirty();
    void markCompositeDirty();

protected:
    // Initialize grid storage (flat or chunked) and TCOD map
    void initStorage(int gx, int gy, GridData* parent_ref);
    void cleanupTCOD();
};
