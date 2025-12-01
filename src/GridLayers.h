#pragma once
#include "Common.h"
#include "Python.h"
#include "structmember.h"
#include <SFML/Graphics.hpp>
#include <libtcod.h>
#include <memory>
#include <vector>
#include <string>

// Forward declarations
class UIGrid;
class PyTexture;
class UIEntity;

// Include PyTexture.h for PyTextureObject (typedef, not struct)
#include "PyTexture.h"

// Layer type enumeration
enum class GridLayerType {
    Color,
    Tile
};

// Abstract base class for grid layers
class GridLayer {
public:
    // Chunk size for per-chunk dirty tracking (matches GridChunk::CHUNK_SIZE)
    static constexpr int CHUNK_SIZE = 64;

    GridLayerType type;
    std::string name;      // #150 - Layer name for GridPoint property access
    int z_index;           // Negative = below entities, >= 0 = above entities
    int grid_x, grid_y;    // Dimensions
    UIGrid* parent_grid;   // Parent grid reference
    bool visible;          // Visibility flag

    // Chunk dimensions
    int chunks_x, chunks_y;

    // Per-chunk dirty flags and RenderTextures
    std::vector<bool> chunk_dirty;                              // One flag per chunk
    std::vector<std::unique_ptr<sf::RenderTexture>> chunk_textures;  // One texture per chunk
    std::vector<bool> chunk_texture_initialized;                // Track which textures are created
    int cached_cell_width, cached_cell_height;                  // Cell size used for cached textures

    GridLayer(GridLayerType type, int z_index, int grid_x, int grid_y, UIGrid* parent);
    virtual ~GridLayer() = default;

    // Mark entire layer as needing re-render
    void markDirty();

    // Mark specific cell's chunk as dirty
    void markDirty(int cell_x, int cell_y);

    // Get chunk index for a cell
    int getChunkIndex(int cell_x, int cell_y) const;

    // Get chunk coordinates for a cell
    void getChunkCoords(int cell_x, int cell_y, int& chunk_x, int& chunk_y) const;

    // Get cell bounds for a chunk
    void getChunkBounds(int chunk_x, int chunk_y, int& start_x, int& start_y, int& end_x, int& end_y) const;

    // Ensure a specific chunk's texture is properly sized
    void ensureChunkTexture(int chunk_idx, int cell_width, int cell_height);

    // Initialize chunk tracking arrays
    void initChunks();

    // Render a specific chunk to its cached texture (called when chunk is dirty)
    virtual void renderChunkToTexture(int chunk_x, int chunk_y, int cell_width, int cell_height) = 0;

    // Render the layer content to the cached texture (legacy - marks all dirty)
    virtual void renderToTexture(int cell_width, int cell_height) = 0;

    // Render the layer to a RenderTarget with the given transformation parameters
    // Uses cached chunk textures, only re-renders visible dirty chunks
    virtual void render(sf::RenderTarget& target,
                       float left_spritepixels, float top_spritepixels,
                       int left_edge, int top_edge, int x_limit, int y_limit,
                       float zoom, int cell_width, int cell_height) = 0;

    // Resize the layer (reallocates storage and reinitializes chunks)
    virtual void resize(int new_grid_x, int new_grid_y) = 0;
};

// Color layer - stores RGBA color per cell
class ColorLayer : public GridLayer {
public:
    std::vector<sf::Color> colors;

    // Perspective binding (#113) - binds layer to entity for automatic FOV updates
    std::weak_ptr<UIEntity> perspective_entity;
    sf::Color perspective_visible;
    sf::Color perspective_discovered;
    sf::Color perspective_unknown;
    bool has_perspective;

    ColorLayer(int z_index, int grid_x, int grid_y, UIGrid* parent);

    // Access color at position
    sf::Color& at(int x, int y);
    const sf::Color& at(int x, int y) const;

    // Fill entire layer with a color
    void fill(const sf::Color& color);

    // Fill a rectangular region with a color (#113)
    void fillRect(int x, int y, int width, int height, const sf::Color& color);

    // Draw FOV-based visibility (#113)
    // Paints cells based on current FOV state from parent grid
    void drawFOV(int source_x, int source_y, int radius,
                 TCOD_fov_algorithm_t algorithm,
                 const sf::Color& visible,
                 const sf::Color& discovered,
                 const sf::Color& unknown);

    // Perspective binding (#113) - bind layer to entity for automatic updates
    void applyPerspective(std::shared_ptr<UIEntity> entity,
                          const sf::Color& visible,
                          const sf::Color& discovered,
                          const sf::Color& unknown);

    // Update perspective - redraws based on bound entity's current position
    void updatePerspective();

    // Clear perspective binding
    void clearPerspective();

    // Render a specific chunk to its texture (called when chunk is dirty AND visible)
    void renderChunkToTexture(int chunk_x, int chunk_y, int cell_width, int cell_height) override;

    // #148 - Render all content to cached texture (legacy - calls renderChunkToTexture for all)
    void renderToTexture(int cell_width, int cell_height) override;

    void render(sf::RenderTarget& target,
               float left_spritepixels, float top_spritepixels,
               int left_edge, int top_edge, int x_limit, int y_limit,
               float zoom, int cell_width, int cell_height) override;

    void resize(int new_grid_x, int new_grid_y) override;
};

// Tile layer - stores sprite index per cell with texture reference
class TileLayer : public GridLayer {
public:
    std::vector<int> tiles;  // Sprite indices (-1 = no tile)
    std::shared_ptr<PyTexture> texture;

    TileLayer(int z_index, int grid_x, int grid_y, UIGrid* parent,
              std::shared_ptr<PyTexture> texture = nullptr);

    // Access tile index at position
    int& at(int x, int y);
    int at(int x, int y) const;

    // Fill entire layer with a tile index
    void fill(int tile_index);

    // Fill a rectangular region with a tile index (#113)
    void fillRect(int x, int y, int width, int height, int tile_index);

    // Render a specific chunk to its texture (called when chunk is dirty AND visible)
    void renderChunkToTexture(int chunk_x, int chunk_y, int cell_width, int cell_height) override;

    // #148 - Render all content to cached texture (legacy - calls renderChunkToTexture for all)
    void renderToTexture(int cell_width, int cell_height) override;

    void render(sf::RenderTarget& target,
               float left_spritepixels, float top_spritepixels,
               int left_edge, int top_edge, int x_limit, int y_limit,
               float zoom, int cell_width, int cell_height) override;

    void resize(int new_grid_x, int new_grid_y) override;
};

// Python wrapper types
typedef struct {
    PyObject_HEAD
    std::shared_ptr<GridLayer> data;
    std::shared_ptr<UIGrid> grid;  // Parent grid reference
} PyGridLayerObject;

typedef struct {
    PyObject_HEAD
    std::shared_ptr<ColorLayer> data;
    std::shared_ptr<UIGrid> grid;
} PyColorLayerObject;

typedef struct {
    PyObject_HEAD
    std::shared_ptr<TileLayer> data;
    std::shared_ptr<UIGrid> grid;
} PyTileLayerObject;

// Python API classes
class PyGridLayerAPI {
public:
    // ColorLayer methods
    static int ColorLayer_init(PyColorLayerObject* self, PyObject* args, PyObject* kwds);
    static PyObject* ColorLayer_at(PyColorLayerObject* self, PyObject* args);
    static PyObject* ColorLayer_set(PyColorLayerObject* self, PyObject* args);
    static PyObject* ColorLayer_fill(PyColorLayerObject* self, PyObject* args);
    static PyObject* ColorLayer_fill_rect(PyColorLayerObject* self, PyObject* args, PyObject* kwds);
    static PyObject* ColorLayer_draw_fov(PyColorLayerObject* self, PyObject* args, PyObject* kwds);
    static PyObject* ColorLayer_apply_perspective(PyColorLayerObject* self, PyObject* args, PyObject* kwds);
    static PyObject* ColorLayer_update_perspective(PyColorLayerObject* self, PyObject* args);
    static PyObject* ColorLayer_clear_perspective(PyColorLayerObject* self, PyObject* args);
    static PyObject* ColorLayer_get_z_index(PyColorLayerObject* self, void* closure);
    static int ColorLayer_set_z_index(PyColorLayerObject* self, PyObject* value, void* closure);
    static PyObject* ColorLayer_get_visible(PyColorLayerObject* self, void* closure);
    static int ColorLayer_set_visible(PyColorLayerObject* self, PyObject* value, void* closure);
    static PyObject* ColorLayer_get_grid_size(PyColorLayerObject* self, void* closure);
    static PyObject* ColorLayer_repr(PyColorLayerObject* self);

    // TileLayer methods
    static int TileLayer_init(PyTileLayerObject* self, PyObject* args, PyObject* kwds);
    static PyObject* TileLayer_at(PyTileLayerObject* self, PyObject* args);
    static PyObject* TileLayer_set(PyTileLayerObject* self, PyObject* args);
    static PyObject* TileLayer_fill(PyTileLayerObject* self, PyObject* args);
    static PyObject* TileLayer_fill_rect(PyTileLayerObject* self, PyObject* args, PyObject* kwds);
    static PyObject* TileLayer_get_z_index(PyTileLayerObject* self, void* closure);
    static int TileLayer_set_z_index(PyTileLayerObject* self, PyObject* value, void* closure);
    static PyObject* TileLayer_get_visible(PyTileLayerObject* self, void* closure);
    static int TileLayer_set_visible(PyTileLayerObject* self, PyObject* value, void* closure);
    static PyObject* TileLayer_get_texture(PyTileLayerObject* self, void* closure);
    static int TileLayer_set_texture(PyTileLayerObject* self, PyObject* value, void* closure);
    static PyObject* TileLayer_get_grid_size(PyTileLayerObject* self, void* closure);
    static PyObject* TileLayer_repr(PyTileLayerObject* self);

    // Method and getset arrays
    static PyMethodDef ColorLayer_methods[];
    static PyGetSetDef ColorLayer_getsetters[];
    static PyMethodDef TileLayer_methods[];
    static PyGetSetDef TileLayer_getsetters[];
};

namespace mcrfpydef {
    // ColorLayer type
    static PyTypeObject PyColorLayerType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.ColorLayer",
        .tp_basicsize = sizeof(PyColorLayerObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)[](PyObject* self) {
            PyColorLayerObject* obj = (PyColorLayerObject*)self;
            obj->data.reset();
            obj->grid.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)PyGridLayerAPI::ColorLayer_repr,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("ColorLayer(z_index=-1, grid_size=None)\n\n"
                           "A grid layer that stores RGBA colors per cell.\n\n"
                           "Args:\n"
                           "    z_index (int): Render order. Negative = below entities. Default: -1\n"
                           "    grid_size (tuple): Dimensions as (width, height). Default: parent grid size\n\n"
                           "Attributes:\n"
                           "    z_index (int): Layer z-order relative to entities\n"
                           "    visible (bool): Whether layer is rendered\n"
                           "    grid_size (tuple): Layer dimensions (read-only)\n\n"
                           "Methods:\n"
                           "    at(x, y): Get color at cell position\n"
                           "    set(x, y, color): Set color at cell position\n"
                           "    fill(color): Fill entire layer with color"),
        .tp_methods = PyGridLayerAPI::ColorLayer_methods,
        .tp_getset = PyGridLayerAPI::ColorLayer_getsetters,
        .tp_init = (initproc)PyGridLayerAPI::ColorLayer_init,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject* {
            PyColorLayerObject* self = (PyColorLayerObject*)type->tp_alloc(type, 0);
            return (PyObject*)self;
        }
    };

    // TileLayer type
    static PyTypeObject PyTileLayerType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.TileLayer",
        .tp_basicsize = sizeof(PyTileLayerObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)[](PyObject* self) {
            PyTileLayerObject* obj = (PyTileLayerObject*)self;
            obj->data.reset();
            obj->grid.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)PyGridLayerAPI::TileLayer_repr,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("TileLayer(z_index=-1, texture=None, grid_size=None)\n\n"
                           "A grid layer that stores sprite indices per cell.\n\n"
                           "Args:\n"
                           "    z_index (int): Render order. Negative = below entities. Default: -1\n"
                           "    texture (Texture): Sprite atlas for tile rendering. Default: None\n"
                           "    grid_size (tuple): Dimensions as (width, height). Default: parent grid size\n\n"
                           "Attributes:\n"
                           "    z_index (int): Layer z-order relative to entities\n"
                           "    visible (bool): Whether layer is rendered\n"
                           "    texture (Texture): Tile sprite atlas\n"
                           "    grid_size (tuple): Layer dimensions (read-only)\n\n"
                           "Methods:\n"
                           "    at(x, y): Get tile index at cell position\n"
                           "    set(x, y, index): Set tile index at cell position\n"
                           "    fill(index): Fill entire layer with tile index"),
        .tp_methods = PyGridLayerAPI::TileLayer_methods,
        .tp_getset = PyGridLayerAPI::TileLayer_getsetters,
        .tp_init = (initproc)PyGridLayerAPI::TileLayer_init,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject* {
            PyTileLayerObject* self = (PyTileLayerObject*)type->tp_alloc(type, 0);
            return (PyObject*)self;
        }
    };
}
