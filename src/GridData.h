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

// Forward declarations
class DijkstraMap;
class UIEntity;
class UIDrawable;
class UIGridView;
class PyTexture;

// GridData is a MAP, not a widget (#361). It has no position, no size, no
// camera, and no render(). Only UIGridView -- which holds a camera and points
// at a GridData -- is a UIDrawable. `mcrfpy.Grid` is a GridView that creates
// its own GridData; N views may share one GridData (split-screen, minimap).
class GridData {
public:
    GridData();
    GridData(int gx, int gy, std::shared_ptr<PyTexture> texture);
    virtual ~GridData();

    // =========================================================================
    // Grid dimensions and cell storage
    // =========================================================================
    int grid_w = 0, grid_h = 0;

    // #361 - The tile atlas. This is DATA, not rendering state: it is what
    // defines the cell size in pixels, which every tile<->pixel conversion in
    // the engine (entity positions, layer geometry, a view's camera math)
    // depends on. Views copy it to draw with; they do not own it. Write-once
    // at construction, so cell_width_px/cell_height_px never go stale.
    std::shared_ptr<PyTexture> ptex;
    std::shared_ptr<PyTexture> getTexture() const { return ptex; }

    static constexpr int DEFAULT_CELL_WIDTH = 16;
    static constexpr int DEFAULT_CELL_HEIGHT = 16;

    // #361 - PythonObjectCache identity. GridData used to inherit this from
    // UIDrawable; now that it is not a drawable it carries its own, so that
    // `entity.grid`, `view.grid_data` and the GridPoint/layer back-references
    // all resolve to ONE Python wrapper instead of a fresh one per access.
    uint64_t serial_number = 0;

    // #313 - Cell pixel dimensions, mirrored from ptex at construction. Lets
    // the data layer do tile<->pixel math without reaching into a view.
    int cell_width_px = 16;
    int cell_height_px = 16;
    int cell_width() const { return cell_width_px; }
    int cell_height() const { return cell_height_px; }

    // #332 - Logic cell storage as two dense row-major uint8 planes (SoA).
    // Replaces the 24-byte-per-cell array-of-UIGridPoint (walkable/transparent
    // were only 2 bytes of payload; grid_x/grid_y/parent_grid were derivable or
    // back-reference bookkeeping). 12x smaller, cache-friendly, and contiguous
    // at ANY size -- chunking is dropped for logic data (render caches still
    // chunk independently in GridLayers). Indexed y*grid_w + x. The Python
    // GridPoint wrapper holds (grid, x, y) and reads/writes via these accessors.
    std::vector<uint8_t> walkable_plane;
    std::vector<uint8_t> transparent_plane;

    bool isWalkable(int x, int y) const { return walkable_plane[(size_t)y * grid_w + x] != 0; }
    bool isTransparent(int x, int y) const { return transparent_plane[(size_t)y * grid_w + x] != 0; }
    void setWalkable(int x, int y, bool v) { walkable_plane[(size_t)y * grid_w + x] = v ? 1 : 0; }
    void setTransparent(int x, int y, bool v) { transparent_plane[(size_t)y * grid_w + x] = v ? 1 : 0; }

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

    // #355 - Cell input (callbacks, hovered/last-clicked cell, subclass-dispatch
    // cache) moved to UIGridView: input is a property of the VIEW (camera), not of
    // the data. Two views over one GridData must track hover independently, and
    // the subclassable Python type (mcrfpy.Grid) IS UIGridView.

    // #364 - UIDrawable children (speech bubbles, markers, range indicators) moved
    // to UIGridView. They are OVERLAYS painted over the map through one camera, not
    // world contents: nothing collides with them, they occupy no cell, and the turn
    // manager cannot see them. Entities are the world contents, and those stay here,
    // shared by every view.
    //
    // Ownership follows from that. A UIDrawable has exactly one `parent`, but a
    // GridData may have N views -- so a child owned by the data could only ever name
    // one of them as parent, arbitrarily, and would dangle if that view died while
    // the others kept rendering it. Owned by the view, a child's parent is a real
    // scene-graph drawable, so its dirty push reaches the view and every caching
    // ancestor above it, and its grid-world position resolves through exactly one
    // camera.

    // =========================================================================
    // #252/#359 - GridView back-references. Multiple GridViews can share one
    // GridData (split-screen, minimap, multiple cameras); a single weak_ptr
    // cannot represent that, so this is a vector. A fresh GridData is only
    // ever produced by UIGridView::init_with_data (the Grid() factory path --
    // UIGridView::init_explicit_view / set_grid can only ATTACH to an
    // EXISTING GridData, never create one), so views.front() is always the
    // view that created this data: that ordering guarantee is what lets
    // primaryView() give UIEntity::get_grid a deterministic (not arbitrary)
    // answer for API identity, even once secondary views are registered.
    // =========================================================================
    std::vector<std::weak_ptr<UIGridView>> views;

    // Append view (idempotent -- a view already present is not duplicated).
    void registerView(const std::shared_ptr<UIGridView>& view);
    // Remove view by identity (prunes expired entries too). Safe to call even
    // if view was never registered.
    void unregisterView(UIGridView* view);
    // The view that created this GridData (views.front()), or the first
    // still-alive view if the creator has since been destroyed while
    // secondary views live on. nullptr if no view is alive.
    std::shared_ptr<UIGridView> primaryView() const;

    // #351 - Monotonic counter bumped whenever grid content drawn into a view's
    // RenderTexture changes (entities added/removed/moved, sprite changes, layer
    // edits, layer add/remove). UIGridView compares it against the generation it
    // last rendered to skip re-rasterizing an unchanged grid. Camera parameters
    // live on the view and are compared there directly, not counted here.
    uint64_t content_generation = 0;

    // #313/#359 - Render invalidation from the data layer. Entities hold
    // shared_ptr<GridData> but still need to invalidate rendering when their
    // visual state changes, so the data notifies every registered view (see
    // `views` above) -- and each view then pushes up its OWN ancestor chain,
    // since a Frame(cache_subtree=True) wrapping ANY of the N views needs its
    // cache invalidated, not just the creator's.
    //
    // #361: these used to ALSO downcast `this` to UIGrid and set the dirty
    // flags on its UIDrawable half, feeding a second, stale render path (a
    // bare _GridData appended to a scene drew the map through a frozen camera).
    // That path is gone: GridData is not a drawable, so there is nothing to
    // notify but the views.
    //
    // Note the #351 render early-out does NOT depend on this push -- it polls
    // content_generation directly in UIGridView::render(). This is only for
    // bottom-up propagation through a view's parent chain, which a top-down
    // render traversal cannot poll for.
    void markDirty();
    void markCompositeDirty();

protected:
    // Initialize grid storage (flat or chunked) and TCOD map
    void initStorage(int gx, int gy, GridData* parent_ref);
    void cleanupTCOD();
};
