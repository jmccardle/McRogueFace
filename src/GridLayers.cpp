#include "GridLayers.h"
#include "UIGrid.h"
#include "UIEntity.h"
#include "PyColor.h"
#include "PyTexture.h"
#include "PyFOV.h"
#include "PyPositionHelper.h"
#include "PyHeightMap.h"
#include <sstream>

// =============================================================================
// HeightMap helper functions for layer operations
// =============================================================================

// Helper to parse a range tuple (min, max) and validate
static bool ParseRange(PyObject* range_obj, float* out_min, float* out_max, const char* arg_name) {
    if (!PyTuple_Check(range_obj) && !PyList_Check(range_obj)) {
        PyErr_Format(PyExc_TypeError, "%s must be a (min, max) tuple or list", arg_name);
        return false;
    }

    PyObject* seq = PySequence_Fast(range_obj, "range must be sequence");
    if (!seq) return false;

    if (PySequence_Fast_GET_SIZE(seq) != 2) {
        Py_DECREF(seq);
        PyErr_Format(PyExc_ValueError, "%s must have exactly 2 elements (min, max)", arg_name);
        return false;
    }

    *out_min = (float)PyFloat_AsDouble(PySequence_Fast_GET_ITEM(seq, 0));
    *out_max = (float)PyFloat_AsDouble(PySequence_Fast_GET_ITEM(seq, 1));
    Py_DECREF(seq);

    if (PyErr_Occurred()) return false;

    if (*out_min > *out_max) {
        // Build error message manually since PyErr_Format has limited float support
        char buf[256];
        snprintf(buf, sizeof(buf), "%s: min (%.3f) must be <= max (%.3f)",
                 arg_name, *out_min, *out_max);
        PyErr_SetString(PyExc_ValueError, buf);
        return false;
    }

    return true;
}

// Helper to validate HeightMap matches layer dimensions
static bool ValidateHeightMapSize(PyHeightMapObject* hmap, int grid_x, int grid_y) {
    int hmap_width = hmap->heightmap->w;
    int hmap_height = hmap->heightmap->h;

    if (hmap_width != grid_x || hmap_height != grid_y) {
        PyErr_Format(PyExc_ValueError,
                     "HeightMap size (%d, %d) does not match layer size (%d, %d)",
                     hmap_width, hmap_height, grid_x, grid_y);
        return false;
    }
    return true;
}

// Helper to check if an object is a HeightMap (runtime lookup to avoid static type issues)
static bool IsHeightMapObject(PyObject* obj, PyHeightMapObject** out_hmap) {
    auto* mcrfpy_module = PyImport_ImportModule("mcrfpy");
    if (!mcrfpy_module) return false;

    auto* heightmap_type = PyObject_GetAttrString(mcrfpy_module, "HeightMap");
    Py_DECREF(mcrfpy_module);
    if (!heightmap_type) return false;

    bool result = PyObject_IsInstance(obj, heightmap_type);
    Py_DECREF(heightmap_type);

    if (result && out_hmap) {
        *out_hmap = (PyHeightMapObject*)obj;
    }
    return result;
}

// Helper to parse a color from Python object
static bool ParseColorArg(PyObject* obj, sf::Color& out_color, const char* arg_name) {
    if (!obj || obj == Py_None) {
        PyErr_Format(PyExc_TypeError, "%s cannot be None", arg_name);
        return false;
    }

    auto* mcrfpy_module = PyImport_ImportModule("mcrfpy");
    if (!mcrfpy_module) return false;

    auto* color_type = PyObject_GetAttrString(mcrfpy_module, "Color");
    Py_DECREF(mcrfpy_module);
    if (!color_type) return false;

    if (PyObject_IsInstance(obj, color_type)) {
        out_color = ((PyColorObject*)obj)->data;
        Py_DECREF(color_type);
        return true;
    }
    Py_DECREF(color_type);

    if (PyTuple_Check(obj) || PyList_Check(obj)) {
        PyObject* seq = PySequence_Fast(obj, "color must be sequence");
        if (!seq) return false;

        Py_ssize_t len = PySequence_Fast_GET_SIZE(seq);
        if (len < 3 || len > 4) {
            Py_DECREF(seq);
            PyErr_Format(PyExc_ValueError, "%s must be (r, g, b) or (r, g, b, a)", arg_name);
            return false;
        }

        int r = (int)PyLong_AsLong(PySequence_Fast_GET_ITEM(seq, 0));
        int g = (int)PyLong_AsLong(PySequence_Fast_GET_ITEM(seq, 1));
        int b = (int)PyLong_AsLong(PySequence_Fast_GET_ITEM(seq, 2));
        int a = (len == 4) ? (int)PyLong_AsLong(PySequence_Fast_GET_ITEM(seq, 3)) : 255;
        Py_DECREF(seq);

        if (PyErr_Occurred()) return false;

        out_color = sf::Color(r, g, b, a);
        return true;
    }

    PyErr_Format(PyExc_TypeError, "%s must be a Color or (r, g, b[, a]) tuple", arg_name);
    return false;
}

// Interpolate between two colors
static sf::Color LerpColor(const sf::Color& a, const sf::Color& b, float t) {
    t = std::max(0.0f, std::min(1.0f, t));  // Clamp t to [0, 1]
    return sf::Color(
        static_cast<sf::Uint8>(a.r + (b.r - a.r) * t),
        static_cast<sf::Uint8>(a.g + (b.g - a.g) * t),
        static_cast<sf::Uint8>(a.b + (b.b - a.b) * t),
        static_cast<sf::Uint8>(a.a + (b.a - a.a) * t)
    );
}

// =============================================================================
// GridLayer base class
// =============================================================================

GridLayer::GridLayer(GridLayerType type, int z_index, int grid_x, int grid_y, UIGrid* parent)
    : type(type), z_index(z_index), grid_x(grid_x), grid_y(grid_y),
      parent_grid(parent), visible(true),
      chunks_x(0), chunks_y(0),
      cached_cell_width(0), cached_cell_height(0)
{
    initChunks();
}

void GridLayer::initChunks() {
    // Calculate chunk dimensions
    chunks_x = (grid_x + CHUNK_SIZE - 1) / CHUNK_SIZE;
    chunks_y = (grid_y + CHUNK_SIZE - 1) / CHUNK_SIZE;
    int total_chunks = chunks_x * chunks_y;

    // Initialize per-chunk tracking
    chunk_dirty.assign(total_chunks, true);  // All chunks start dirty
    chunk_texture_initialized.assign(total_chunks, false);
    chunk_textures.clear();
    chunk_textures.reserve(total_chunks);
    for (int i = 0; i < total_chunks; ++i) {
        chunk_textures.push_back(std::make_unique<sf::RenderTexture>());
    }
}

void GridLayer::markDirty() {
    // Mark ALL chunks as dirty
    std::fill(chunk_dirty.begin(), chunk_dirty.end(), true);
}

void GridLayer::markDirty(int cell_x, int cell_y) {
    // Mark only the specific chunk containing this cell
    if (cell_x < 0 || cell_x >= grid_x || cell_y < 0 || cell_y >= grid_y) return;

    int chunk_idx = getChunkIndex(cell_x, cell_y);
    if (chunk_idx >= 0 && chunk_idx < static_cast<int>(chunk_dirty.size())) {
        chunk_dirty[chunk_idx] = true;
    }
}

int GridLayer::getChunkIndex(int cell_x, int cell_y) const {
    int cx = cell_x / CHUNK_SIZE;
    int cy = cell_y / CHUNK_SIZE;
    return cy * chunks_x + cx;
}

void GridLayer::getChunkBounds(int chunk_x, int chunk_y, int& start_x, int& start_y, int& end_x, int& end_y) const {
    start_x = chunk_x * CHUNK_SIZE;
    start_y = chunk_y * CHUNK_SIZE;
    end_x = std::min(start_x + CHUNK_SIZE, grid_x);
    end_y = std::min(start_y + CHUNK_SIZE, grid_y);
}

void GridLayer::ensureChunkTexture(int chunk_idx, int cell_width, int cell_height) {
    if (chunk_idx < 0 || chunk_idx >= static_cast<int>(chunk_textures.size())) return;
    if (!chunk_textures[chunk_idx]) return;

    // Calculate chunk dimensions in cells
    int cx = chunk_idx % chunks_x;
    int cy = chunk_idx / chunks_x;
    int start_x, start_y, end_x, end_y;
    getChunkBounds(cx, cy, start_x, start_y, end_x, end_y);

    int chunk_width_cells = end_x - start_x;
    int chunk_height_cells = end_y - start_y;

    unsigned int required_width = chunk_width_cells * cell_width;
    unsigned int required_height = chunk_height_cells * cell_height;

    // Check if texture needs (re)creation
    if (chunk_texture_initialized[chunk_idx] &&
        chunk_textures[chunk_idx]->getSize().x == required_width &&
        chunk_textures[chunk_idx]->getSize().y == required_height &&
        cached_cell_width == cell_width &&
        cached_cell_height == cell_height) {
        return;  // Already properly sized
    }

    // Create the texture for this chunk
    if (!chunk_textures[chunk_idx]->create(required_width, required_height)) {
        chunk_texture_initialized[chunk_idx] = false;
        return;
    }

    chunk_texture_initialized[chunk_idx] = true;
    chunk_dirty[chunk_idx] = true;  // Force re-render after resize
    cached_cell_width = cell_width;
    cached_cell_height = cell_height;
}

// =============================================================================
// ColorLayer implementation
// =============================================================================

ColorLayer::ColorLayer(int z_index, int grid_x, int grid_y, UIGrid* parent)
    : GridLayer(GridLayerType::Color, z_index, grid_x, grid_y, parent),
      colors(grid_x * grid_y, sf::Color::Transparent),
      perspective_visible(255, 255, 200, 64),
      perspective_discovered(100, 100, 100, 128),
      perspective_unknown(0, 0, 0, 255),
      has_perspective(false)
{}

sf::Color& ColorLayer::at(int x, int y) {
    return colors[y * grid_x + x];
}

const sf::Color& ColorLayer::at(int x, int y) const {
    return colors[y * grid_x + x];
}

void ColorLayer::fill(const sf::Color& color) {
    std::fill(colors.begin(), colors.end(), color);
    markDirty();  // Mark ALL chunks for re-render
}

void ColorLayer::fillRect(int x, int y, int width, int height, const sf::Color& color) {
    // Clamp to valid bounds
    int x1 = std::max(0, x);
    int y1 = std::max(0, y);
    int x2 = std::min(grid_x, x + width);
    int y2 = std::min(grid_y, y + height);

    // Fill the rectangle
    for (int fy = y1; fy < y2; ++fy) {
        for (int fx = x1; fx < x2; ++fx) {
            colors[fy * grid_x + fx] = color;
        }
    }

    // Mark affected chunks dirty
    int chunk_x1 = x1 / CHUNK_SIZE;
    int chunk_y1 = y1 / CHUNK_SIZE;
    int chunk_x2 = (x2 - 1) / CHUNK_SIZE;
    int chunk_y2 = (y2 - 1) / CHUNK_SIZE;

    for (int cy = chunk_y1; cy <= chunk_y2; ++cy) {
        for (int cx = chunk_x1; cx <= chunk_x2; ++cx) {
            int idx = cy * chunks_x + cx;
            if (idx >= 0 && idx < static_cast<int>(chunk_dirty.size())) {
                chunk_dirty[idx] = true;
            }
        }
    }
}

void ColorLayer::drawFOV(int source_x, int source_y, int radius,
                         TCOD_fov_algorithm_t algorithm,
                         const sf::Color& visible_color,
                         const sf::Color& discovered_color,
                         const sf::Color& unknown_color) {
    // Need parent grid for TCOD map access
    if (!parent_grid) {
        return;  // Cannot compute FOV without parent grid
    }

    // Import UIGrid here to avoid circular dependency in header
    // parent_grid is already a UIGrid*, we can use its tcod_map directly
    // But we need to forward declare access to it...

    // Compute FOV on the parent grid
    parent_grid->computeFOV(source_x, source_y, radius, true, algorithm);

    // Paint cells based on visibility
    for (int cy = 0; cy < grid_y; ++cy) {
        for (int cx = 0; cx < grid_x; ++cx) {
            // Check if in FOV (visible right now)
            if (parent_grid->isInFOV(cx, cy)) {
                colors[cy * grid_x + cx] = visible_color;
            }
            // Check if previously discovered (current color != unknown)
            else if (colors[cy * grid_x + cx] != unknown_color) {
                colors[cy * grid_x + cx] = discovered_color;
            }
            // Otherwise leave as unknown (or set to unknown if first time)
            else {
                colors[cy * grid_x + cx] = unknown_color;
            }
        }
    }

    // Mark entire layer dirty
    markDirty();
}

void ColorLayer::applyPerspective(std::shared_ptr<UIEntity> entity,
                                   const sf::Color& visible,
                                   const sf::Color& discovered,
                                   const sf::Color& unknown) {
    perspective_entity = entity;
    perspective_visible = visible;
    perspective_discovered = discovered;
    perspective_unknown = unknown;
    has_perspective = true;

    // Initial draw based on entity's current position
    updatePerspective();
}

void ColorLayer::updatePerspective() {
    if (!has_perspective) return;

    auto entity = perspective_entity.lock();
    if (!entity) {
        // Entity was deleted, clear perspective
        has_perspective = false;
        return;
    }

    if (!parent_grid) return;

    // Get entity position and grid's FOV settings
    int source_x = static_cast<int>(entity->position.x);
    int source_y = static_cast<int>(entity->position.y);
    int radius = parent_grid->fov_radius;
    TCOD_fov_algorithm_t algorithm = parent_grid->fov_algorithm;

    // Use drawFOV with our stored colors
    drawFOV(source_x, source_y, radius, algorithm,
            perspective_visible, perspective_discovered, perspective_unknown);
}

void ColorLayer::clearPerspective() {
    perspective_entity.reset();
    has_perspective = false;
}

void ColorLayer::resize(int new_grid_x, int new_grid_y) {
    std::vector<sf::Color> new_colors(new_grid_x * new_grid_y, sf::Color::Transparent);

    // Copy existing data
    int copy_x = std::min(grid_x, new_grid_x);
    int copy_y = std::min(grid_y, new_grid_y);
    for (int y = 0; y < copy_y; ++y) {
        for (int x = 0; x < copy_x; ++x) {
            new_colors[y * new_grid_x + x] = colors[y * grid_x + x];
        }
    }

    colors = std::move(new_colors);
    grid_x = new_grid_x;
    grid_y = new_grid_y;

    // Reinitialize chunks for new dimensions
    initChunks();
}

// Render a single chunk to its cached texture
void ColorLayer::renderChunkToTexture(int chunk_x, int chunk_y, int cell_width, int cell_height) {
    int chunk_idx = chunk_y * chunks_x + chunk_x;
    if (chunk_idx < 0 || chunk_idx >= static_cast<int>(chunk_textures.size())) return;
    if (!chunk_textures[chunk_idx]) return;

    ensureChunkTexture(chunk_idx, cell_width, cell_height);
    if (!chunk_texture_initialized[chunk_idx]) return;

    // Get chunk bounds
    int start_x, start_y, end_x, end_y;
    getChunkBounds(chunk_x, chunk_y, start_x, start_y, end_x, end_y);

    chunk_textures[chunk_idx]->clear(sf::Color::Transparent);

    sf::RectangleShape rect;
    rect.setSize(sf::Vector2f(cell_width, cell_height));
    rect.setOutlineThickness(0);

    // Render only cells within this chunk (local coordinates in texture)
    for (int x = start_x; x < end_x; ++x) {
        for (int y = start_y; y < end_y; ++y) {
            const sf::Color& color = at(x, y);
            if (color.a == 0) continue;  // Skip fully transparent

            // Position relative to chunk origin
            rect.setPosition(sf::Vector2f((x - start_x) * cell_width, (y - start_y) * cell_height));
            rect.setFillColor(color);
            chunk_textures[chunk_idx]->draw(rect);
        }
    }

    chunk_textures[chunk_idx]->display();
    chunk_dirty[chunk_idx] = false;
}

// Legacy: render all chunks (used by fill, resize, etc.)
void ColorLayer::renderToTexture(int cell_width, int cell_height) {
    for (int cy = 0; cy < chunks_y; ++cy) {
        for (int cx = 0; cx < chunks_x; ++cx) {
            renderChunkToTexture(cx, cy, cell_width, cell_height);
        }
    }
}

void ColorLayer::render(sf::RenderTarget& target,
                       float left_spritepixels, float top_spritepixels,
                       int left_edge, int top_edge, int x_limit, int y_limit,
                       float zoom, int cell_width, int cell_height) {
    if (!visible) return;

    // Calculate visible chunk range
    int chunk_left = std::max(0, left_edge / CHUNK_SIZE);
    int chunk_top = std::max(0, top_edge / CHUNK_SIZE);
    int chunk_right = std::min(chunks_x - 1, (x_limit + CHUNK_SIZE - 1) / CHUNK_SIZE);
    int chunk_bottom = std::min(chunks_y - 1, (y_limit + CHUNK_SIZE - 1) / CHUNK_SIZE);

    // Iterate only over visible chunks
    for (int cy = chunk_top; cy <= chunk_bottom; ++cy) {
        for (int cx = chunk_left; cx <= chunk_right; ++cx) {
            int chunk_idx = cy * chunks_x + cx;

            // Re-render chunk only if dirty AND visible
            if (chunk_dirty[chunk_idx] || !chunk_texture_initialized[chunk_idx]) {
                renderChunkToTexture(cx, cy, cell_width, cell_height);
            }

            if (!chunk_texture_initialized[chunk_idx]) {
                // Fallback: direct rendering for this chunk
                int start_x, start_y, end_x, end_y;
                getChunkBounds(cx, cy, start_x, start_y, end_x, end_y);

                sf::RectangleShape rect;
                rect.setSize(sf::Vector2f(cell_width * zoom, cell_height * zoom));
                rect.setOutlineThickness(0);

                for (int x = start_x; x < end_x; ++x) {
                    for (int y = start_y; y < end_y; ++y) {
                        const sf::Color& color = at(x, y);
                        if (color.a == 0) continue;

                        auto pixel_pos = sf::Vector2f(
                            (x * cell_width - left_spritepixels) * zoom,
                            (y * cell_height - top_spritepixels) * zoom
                        );
                        rect.setPosition(pixel_pos);
                        rect.setFillColor(color);
                        target.draw(rect);
                    }
                }
                continue;
            }

            // Blit this chunk's texture to target
            int start_x, start_y, end_x, end_y;
            getChunkBounds(cx, cy, start_x, start_y, end_x, end_y);

            // Chunk position in world pixel coordinates
            float chunk_world_x = start_x * cell_width;
            float chunk_world_y = start_y * cell_height;

            // Position in target (accounting for viewport offset and zoom)
            float dest_x = (chunk_world_x - left_spritepixels) * zoom;
            float dest_y = (chunk_world_y - top_spritepixels) * zoom;

            sf::Sprite chunk_sprite(chunk_textures[chunk_idx]->getTexture());
            chunk_sprite.setPosition(sf::Vector2f(dest_x, dest_y));
            chunk_sprite.setScale(sf::Vector2f(zoom, zoom));

            target.draw(chunk_sprite);
        }
    }
}

// =============================================================================
// TileLayer implementation
// =============================================================================

TileLayer::TileLayer(int z_index, int grid_x, int grid_y, UIGrid* parent,
                     std::shared_ptr<PyTexture> texture)
    : GridLayer(GridLayerType::Tile, z_index, grid_x, grid_y, parent),
      tiles(grid_x * grid_y, -1),  // -1 = no tile
      texture(texture)
{}

int& TileLayer::at(int x, int y) {
    return tiles[y * grid_x + x];
}

int TileLayer::at(int x, int y) const {
    return tiles[y * grid_x + x];
}

void TileLayer::fill(int tile_index) {
    std::fill(tiles.begin(), tiles.end(), tile_index);
    markDirty();  // Mark ALL chunks for re-render
}

void TileLayer::fillRect(int x, int y, int width, int height, int tile_index) {
    // Clamp to valid bounds
    int x1 = std::max(0, x);
    int y1 = std::max(0, y);
    int x2 = std::min(grid_x, x + width);
    int y2 = std::min(grid_y, y + height);

    // Fill the rectangle
    for (int fy = y1; fy < y2; ++fy) {
        for (int fx = x1; fx < x2; ++fx) {
            tiles[fy * grid_x + fx] = tile_index;
        }
    }

    // Mark affected chunks dirty
    int chunk_x1 = x1 / CHUNK_SIZE;
    int chunk_y1 = y1 / CHUNK_SIZE;
    int chunk_x2 = (x2 - 1) / CHUNK_SIZE;
    int chunk_y2 = (y2 - 1) / CHUNK_SIZE;

    for (int cy = chunk_y1; cy <= chunk_y2; ++cy) {
        for (int cx = chunk_x1; cx <= chunk_x2; ++cx) {
            int idx = cy * chunks_x + cx;
            if (idx >= 0 && idx < static_cast<int>(chunk_dirty.size())) {
                chunk_dirty[idx] = true;
            }
        }
    }
}

void TileLayer::resize(int new_grid_x, int new_grid_y) {
    std::vector<int> new_tiles(new_grid_x * new_grid_y, -1);

    // Copy existing data
    int copy_x = std::min(grid_x, new_grid_x);
    int copy_y = std::min(grid_y, new_grid_y);
    for (int y = 0; y < copy_y; ++y) {
        for (int x = 0; x < copy_x; ++x) {
            new_tiles[y * new_grid_x + x] = tiles[y * grid_x + x];
        }
    }

    tiles = std::move(new_tiles);
    grid_x = new_grid_x;
    grid_y = new_grid_y;

    // Reinitialize chunks for new dimensions
    initChunks();
}

// Render a single chunk to its cached texture
void TileLayer::renderChunkToTexture(int chunk_x, int chunk_y, int cell_width, int cell_height) {
    if (!texture) return;

    int chunk_idx = chunk_y * chunks_x + chunk_x;
    if (chunk_idx < 0 || chunk_idx >= static_cast<int>(chunk_textures.size())) return;
    if (!chunk_textures[chunk_idx]) return;

    ensureChunkTexture(chunk_idx, cell_width, cell_height);
    if (!chunk_texture_initialized[chunk_idx]) return;

    // Get chunk bounds
    int start_x, start_y, end_x, end_y;
    getChunkBounds(chunk_x, chunk_y, start_x, start_y, end_x, end_y);

    chunk_textures[chunk_idx]->clear(sf::Color::Transparent);

    // Render only tiles within this chunk (local coordinates in texture)
    for (int x = start_x; x < end_x; ++x) {
        for (int y = start_y; y < end_y; ++y) {
            int tile_index = at(x, y);
            if (tile_index < 0) continue;  // No tile

            // Position relative to chunk origin
            auto pixel_pos = sf::Vector2f((x - start_x) * cell_width, (y - start_y) * cell_height);
            sf::Sprite sprite = texture->sprite(tile_index, pixel_pos, sf::Vector2f(1.0f, 1.0f));
            chunk_textures[chunk_idx]->draw(sprite);
        }
    }

    chunk_textures[chunk_idx]->display();
    chunk_dirty[chunk_idx] = false;
}

// Legacy: render all chunks (used by fill, resize, etc.)
void TileLayer::renderToTexture(int cell_width, int cell_height) {
    for (int cy = 0; cy < chunks_y; ++cy) {
        for (int cx = 0; cx < chunks_x; ++cx) {
            renderChunkToTexture(cx, cy, cell_width, cell_height);
        }
    }
}

void TileLayer::render(sf::RenderTarget& target,
                      float left_spritepixels, float top_spritepixels,
                      int left_edge, int top_edge, int x_limit, int y_limit,
                      float zoom, int cell_width, int cell_height) {
    if (!visible || !texture) return;

    // Calculate visible chunk range
    int chunk_left = std::max(0, left_edge / CHUNK_SIZE);
    int chunk_top = std::max(0, top_edge / CHUNK_SIZE);
    int chunk_right = std::min(chunks_x - 1, (x_limit + CHUNK_SIZE - 1) / CHUNK_SIZE);
    int chunk_bottom = std::min(chunks_y - 1, (y_limit + CHUNK_SIZE - 1) / CHUNK_SIZE);

    // Iterate only over visible chunks
    for (int cy = chunk_top; cy <= chunk_bottom; ++cy) {
        for (int cx = chunk_left; cx <= chunk_right; ++cx) {
            int chunk_idx = cy * chunks_x + cx;

            // Re-render chunk only if dirty AND visible
            if (chunk_dirty[chunk_idx] || !chunk_texture_initialized[chunk_idx]) {
                renderChunkToTexture(cx, cy, cell_width, cell_height);
            }

            if (!chunk_texture_initialized[chunk_idx]) {
                // Fallback: direct rendering for this chunk
                int start_x, start_y, end_x, end_y;
                getChunkBounds(cx, cy, start_x, start_y, end_x, end_y);

                for (int x = start_x; x < end_x; ++x) {
                    for (int y = start_y; y < end_y; ++y) {
                        int tile_index = at(x, y);
                        if (tile_index < 0) continue;

                        auto pixel_pos = sf::Vector2f(
                            (x * cell_width - left_spritepixels) * zoom,
                            (y * cell_height - top_spritepixels) * zoom
                        );
                        sf::Sprite sprite = texture->sprite(tile_index, pixel_pos, sf::Vector2f(zoom, zoom));
                        target.draw(sprite);
                    }
                }
                continue;
            }

            // Blit this chunk's texture to target
            int start_x, start_y, end_x, end_y;
            getChunkBounds(cx, cy, start_x, start_y, end_x, end_y);

            // Chunk position in world pixel coordinates
            float chunk_world_x = start_x * cell_width;
            float chunk_world_y = start_y * cell_height;

            // Position in target (accounting for viewport offset and zoom)
            float dest_x = (chunk_world_x - left_spritepixels) * zoom;
            float dest_y = (chunk_world_y - top_spritepixels) * zoom;

            sf::Sprite chunk_sprite(chunk_textures[chunk_idx]->getTexture());
            chunk_sprite.setPosition(sf::Vector2f(dest_x, dest_y));
            chunk_sprite.setScale(sf::Vector2f(zoom, zoom));

            target.draw(chunk_sprite);
        }
    }
}

// =============================================================================
// Python API - ColorLayer
// =============================================================================

PyMethodDef PyGridLayerAPI::ColorLayer_methods[] = {
    {"at", (PyCFunction)PyGridLayerAPI::ColorLayer_at, METH_VARARGS | METH_KEYWORDS,
     "at(pos) -> Color\nat(x, y) -> Color\n\n"
     "Get the color at cell position.\n\n"
     "Args:\n"
     "    pos: Position as (x, y) tuple, list, or Vector\n"
     "    x, y: Position as separate integer arguments"},
    {"set", (PyCFunction)PyGridLayerAPI::ColorLayer_set, METH_VARARGS,
     "set(pos, color)\n\n"
     "Set the color at cell position.\n\n"
     "Args:\n"
     "    pos: Position as (x, y) tuple, list, or Vector\n"
     "    color: Color object or (r, g, b[, a]) tuple"},
    {"fill", (PyCFunction)PyGridLayerAPI::ColorLayer_fill, METH_VARARGS,
     "fill(color)\n\nFill the entire layer with the specified color."},
    {"fill_rect", (PyCFunction)PyGridLayerAPI::ColorLayer_fill_rect, METH_VARARGS | METH_KEYWORDS,
     "fill_rect(pos, size, color)\n\n"
     "Fill a rectangular region with a color.\n\n"
     "Args:\n"
     "    pos (tuple): Top-left corner as (x, y)\n"
     "    size (tuple): Dimensions as (width, height)\n"
     "    color: Color object or (r, g, b[, a]) tuple"},
    {"draw_fov", (PyCFunction)PyGridLayerAPI::ColorLayer_draw_fov, METH_VARARGS | METH_KEYWORDS,
     "draw_fov(source, radius=None, fov=None, visible=None, discovered=None, unknown=None)\n\n"
     "Paint cells based on field-of-view visibility from source position.\n\n"
     "Args:\n"
     "    source (tuple): FOV origin as (x, y)\n"
     "    radius (int): FOV radius. Default: grid's fov_radius\n"
     "    fov (FOV): FOV algorithm. Default: grid's fov setting\n"
     "    visible (Color): Color for currently visible cells\n"
     "    discovered (Color): Color for previously seen cells\n"
     "    unknown (Color): Color for never-seen cells\n\n"
     "Note: Layer must be attached to a grid for FOV calculation."},
    {"apply_perspective", (PyCFunction)PyGridLayerAPI::ColorLayer_apply_perspective, METH_VARARGS | METH_KEYWORDS,
     "apply_perspective(entity, visible=None, discovered=None, unknown=None)\n\n"
     "Bind this layer to an entity for automatic FOV updates.\n\n"
     "Args:\n"
     "    entity (Entity): The entity whose perspective to track\n"
     "    visible (Color): Color for currently visible cells\n"
     "    discovered (Color): Color for previously seen cells\n"
     "    unknown (Color): Color for never-seen cells\n\n"
     "After binding, call update_perspective() when the entity moves."},
    {"update_perspective", (PyCFunction)PyGridLayerAPI::ColorLayer_update_perspective, METH_NOARGS,
     "update_perspective()\n\n"
     "Redraw FOV based on the bound entity's current position.\n\n"
     "Call this after the entity moves to update the visibility layer."},
    {"clear_perspective", (PyCFunction)PyGridLayerAPI::ColorLayer_clear_perspective, METH_NOARGS,
     "clear_perspective()\n\n"
     "Remove the perspective binding from this layer."},
    {"apply_threshold", (PyCFunction)PyGridLayerAPI::ColorLayer_apply_hmap_threshold, METH_VARARGS | METH_KEYWORDS,
     "apply_threshold(source, range, color) -> ColorLayer\n\n"
     "Set fixed color for cells where HeightMap value is within range.\n\n"
     "Args:\n"
     "    source (HeightMap): Source heightmap (must match layer dimensions)\n"
     "    range (tuple): Value range as (min, max) inclusive\n"
     "    color: Color or (r, g, b[, a]) tuple to set for cells in range\n\n"
     "Returns:\n"
     "    self for method chaining\n\n"
     "Example:\n"
     "    layer.apply_threshold(terrain, (0.0, 0.3), (0, 0, 180))  # Blue for water"},
    {"apply_gradient", (PyCFunction)PyGridLayerAPI::ColorLayer_apply_gradient, METH_VARARGS | METH_KEYWORDS,
     "apply_gradient(source, range, color_low, color_high) -> ColorLayer\n\n"
     "Interpolate between colors based on HeightMap value within range.\n\n"
     "Args:\n"
     "    source (HeightMap): Source heightmap (must match layer dimensions)\n"
     "    range (tuple): Value range as (min, max) inclusive\n"
     "    color_low: Color at range minimum\n"
     "    color_high: Color at range maximum\n\n"
     "Returns:\n"
     "    self for method chaining\n\n"
     "Note:\n"
     "    Uses the original HeightMap value for interpolation, not binary.\n"
     "    This allows smooth color transitions within a value range.\n\n"
     "Example:\n"
     "    layer.apply_gradient(terrain, (0.3, 0.7),\n"
     "                         (50, 120, 50),    # Dark green at 0.3\n"
     "                         (100, 200, 100))  # Light green at 0.7"},
    {"apply_ranges", (PyCFunction)PyGridLayerAPI::ColorLayer_apply_ranges, METH_VARARGS,
     "apply_ranges(source, ranges) -> ColorLayer\n\n"
     "Apply multiple color assignments in a single pass.\n\n"
     "Args:\n"
     "    source (HeightMap): Source heightmap (must match layer dimensions)\n"
     "    ranges (list): List of range specifications. Each entry is:\n"
     "        ((min, max), (r, g, b[, a])) - for fixed color\n"
     "        ((min, max), ((r1, g1, b1[, a1]), (r2, g2, b2[, a2]))) - for gradient\n\n"
     "Returns:\n"
     "    self for method chaining\n\n"
     "Note:\n"
     "    Later ranges override earlier ones if overlapping.\n"
     "    Cells not matching any range are left unchanged.\n\n"
     "Example:\n"
     "    layer.apply_ranges(terrain, [\n"
     "        ((0.0, 0.3), (0, 0, 180)),                       # Fixed blue\n"
     "        ((0.3, 0.7), ((50, 120, 50), (100, 200, 100))), # Gradient\n"
     "        ((0.7, 1.0), ((100, 100, 100), (255, 255, 255))), # Gradient\n"
     "    ])"},
    {NULL}
};

PyGetSetDef PyGridLayerAPI::ColorLayer_getsetters[] = {
    {"z_index", (getter)PyGridLayerAPI::ColorLayer_get_z_index,
                (setter)PyGridLayerAPI::ColorLayer_set_z_index,
     "Layer z-order. Negative values render below entities.", NULL},
    {"visible", (getter)PyGridLayerAPI::ColorLayer_get_visible,
                (setter)PyGridLayerAPI::ColorLayer_set_visible,
     "Whether the layer is rendered.", NULL},
    {"grid_size", (getter)PyGridLayerAPI::ColorLayer_get_grid_size, NULL,
     "Layer dimensions as (width, height) tuple.", NULL},
    {NULL}
};

int PyGridLayerAPI::ColorLayer_init(PyColorLayerObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"z_index", "grid_size", NULL};
    int z_index = -1;
    PyObject* grid_size_obj = nullptr;
    int grid_x = 0, grid_y = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|iO", const_cast<char**>(kwlist),
                                     &z_index, &grid_size_obj)) {
        return -1;
    }

    // Parse grid_size if provided
    if (grid_size_obj && grid_size_obj != Py_None) {
        if (!PyTuple_Check(grid_size_obj) || PyTuple_Size(grid_size_obj) != 2) {
            PyErr_SetString(PyExc_TypeError, "grid_size must be a (width, height) tuple");
            return -1;
        }
        grid_x = PyLong_AsLong(PyTuple_GetItem(grid_size_obj, 0));
        grid_y = PyLong_AsLong(PyTuple_GetItem(grid_size_obj, 1));
        if (PyErr_Occurred()) return -1;
    }

    // Create the layer (will be attached to grid via add_layer)
    self->data = std::make_shared<ColorLayer>(z_index, grid_x, grid_y, nullptr);
    self->grid.reset();

    return 0;
}

PyObject* PyGridLayerAPI::ColorLayer_at(PyColorLayerObject* self, PyObject* args, PyObject* kwds) {
    int x, y;
    if (!PyPosition_ParseInt(args, kwds, &x, &y)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }

    if (x < 0 || x >= self->data->grid_x || y < 0 || y >= self->data->grid_y) {
        PyErr_SetString(PyExc_IndexError, "Cell coordinates out of bounds");
        return NULL;
    }

    const sf::Color& color = self->data->at(x, y);

    // Return as mcrfpy.Color
    auto* color_type = (PyTypeObject*)PyObject_GetAttrString(
        PyImport_ImportModule("mcrfpy"), "Color");
    if (!color_type) return NULL;

    PyColorObject* color_obj = (PyColorObject*)color_type->tp_alloc(color_type, 0);
    Py_DECREF(color_type);
    if (!color_obj) return NULL;

    color_obj->data = color;
    return (PyObject*)color_obj;
}

PyObject* PyGridLayerAPI::ColorLayer_set(PyColorLayerObject* self, PyObject* args) {
    PyObject* pos_obj;
    PyObject* color_obj;
    if (!PyArg_ParseTuple(args, "OO", &pos_obj, &color_obj)) {
        return NULL;
    }

    int x, y;
    if (!PyPosition_FromObjectInt(pos_obj, &x, &y)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }

    if (x < 0 || x >= self->data->grid_x || y < 0 || y >= self->data->grid_y) {
        PyErr_SetString(PyExc_IndexError, "Cell coordinates out of bounds");
        return NULL;
    }

    // Parse color
    sf::Color color;
    auto* mcrfpy_module = PyImport_ImportModule("mcrfpy");
    if (!mcrfpy_module) return NULL;

    auto* color_type = PyObject_GetAttrString(mcrfpy_module, "Color");
    Py_DECREF(mcrfpy_module);
    if (!color_type) return NULL;

    if (PyObject_IsInstance(color_obj, color_type)) {
        color = ((PyColorObject*)color_obj)->data;
    } else if (PyTuple_Check(color_obj)) {
        int r, g, b, a = 255;
        if (!PyArg_ParseTuple(color_obj, "iii|i", &r, &g, &b, &a)) {
            Py_DECREF(color_type);
            return NULL;
        }
        color = sf::Color(r, g, b, a);
    } else {
        Py_DECREF(color_type);
        PyErr_SetString(PyExc_TypeError, "color must be a Color object or (r, g, b[, a]) tuple");
        return NULL;
    }
    Py_DECREF(color_type);

    self->data->at(x, y) = color;
    self->data->markDirty(x, y);  // Mark only the affected chunk
    Py_RETURN_NONE;
}

PyObject* PyGridLayerAPI::ColorLayer_fill(PyColorLayerObject* self, PyObject* args) {
    PyObject* color_obj;
    if (!PyArg_ParseTuple(args, "O", &color_obj)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }

    // Parse color
    sf::Color color;
    auto* mcrfpy_module = PyImport_ImportModule("mcrfpy");
    if (!mcrfpy_module) return NULL;

    auto* color_type = PyObject_GetAttrString(mcrfpy_module, "Color");
    Py_DECREF(mcrfpy_module);
    if (!color_type) return NULL;

    if (PyObject_IsInstance(color_obj, color_type)) {
        color = ((PyColorObject*)color_obj)->data;
    } else if (PyTuple_Check(color_obj)) {
        int r, g, b, a = 255;
        if (!PyArg_ParseTuple(color_obj, "iii|i", &r, &g, &b, &a)) {
            Py_DECREF(color_type);
            return NULL;
        }
        color = sf::Color(r, g, b, a);
    } else {
        Py_DECREF(color_type);
        PyErr_SetString(PyExc_TypeError, "color must be a Color object or (r, g, b[, a]) tuple");
        return NULL;
    }
    Py_DECREF(color_type);

    self->data->fill(color);
    Py_RETURN_NONE;
}

PyObject* PyGridLayerAPI::ColorLayer_fill_rect(PyColorLayerObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"pos", "size", "color", NULL};
    PyObject* pos_obj;
    PyObject* size_obj;
    PyObject* color_obj;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OOO", const_cast<char**>(kwlist),
                                     &pos_obj, &size_obj, &color_obj)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }

    // Parse pos
    int x, y;
    if (PyTuple_Check(pos_obj) && PyTuple_Size(pos_obj) == 2) {
        x = PyLong_AsLong(PyTuple_GetItem(pos_obj, 0));
        y = PyLong_AsLong(PyTuple_GetItem(pos_obj, 1));
        if (PyErr_Occurred()) return NULL;
    } else {
        PyErr_SetString(PyExc_TypeError, "pos must be a (x, y) tuple");
        return NULL;
    }

    // Parse size
    int width, height;
    if (PyTuple_Check(size_obj) && PyTuple_Size(size_obj) == 2) {
        width = PyLong_AsLong(PyTuple_GetItem(size_obj, 0));
        height = PyLong_AsLong(PyTuple_GetItem(size_obj, 1));
        if (PyErr_Occurred()) return NULL;
    } else {
        PyErr_SetString(PyExc_TypeError, "size must be a (width, height) tuple");
        return NULL;
    }

    // Parse color
    sf::Color color;
    auto* mcrfpy_module = PyImport_ImportModule("mcrfpy");
    if (!mcrfpy_module) return NULL;

    auto* color_type = PyObject_GetAttrString(mcrfpy_module, "Color");
    Py_DECREF(mcrfpy_module);
    if (!color_type) return NULL;

    if (PyObject_IsInstance(color_obj, color_type)) {
        color = ((PyColorObject*)color_obj)->data;
    } else if (PyTuple_Check(color_obj)) {
        int r, g, b, a = 255;
        if (!PyArg_ParseTuple(color_obj, "iii|i", &r, &g, &b, &a)) {
            Py_DECREF(color_type);
            return NULL;
        }
        color = sf::Color(r, g, b, a);
    } else {
        Py_DECREF(color_type);
        PyErr_SetString(PyExc_TypeError, "color must be a Color object or (r, g, b[, a]) tuple");
        return NULL;
    }
    Py_DECREF(color_type);

    self->data->fillRect(x, y, width, height, color);
    Py_RETURN_NONE;
}

PyObject* PyGridLayerAPI::ColorLayer_draw_fov(PyColorLayerObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"source", "radius", "fov", "visible", "discovered", "unknown", NULL};
    PyObject* source_obj;
    int radius = -1;  // -1 means use grid's default
    PyObject* fov_obj = Py_None;
    PyObject* visible_obj = nullptr;
    PyObject* discovered_obj = nullptr;
    PyObject* unknown_obj = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|iOOOO", const_cast<char**>(kwlist),
                                     &source_obj, &radius, &fov_obj, &visible_obj, &discovered_obj, &unknown_obj)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }

    if (!self->grid) {
        PyErr_SetString(PyExc_RuntimeError, "Layer is not attached to a grid");
        return NULL;
    }

    // Parse source position
    int source_x, source_y;
    if (PyTuple_Check(source_obj) && PyTuple_Size(source_obj) == 2) {
        source_x = PyLong_AsLong(PyTuple_GetItem(source_obj, 0));
        source_y = PyLong_AsLong(PyTuple_GetItem(source_obj, 1));
        if (PyErr_Occurred()) return NULL;
    } else {
        PyErr_SetString(PyExc_TypeError, "source must be a (x, y) tuple");
        return NULL;
    }

    // Get radius from grid if not specified
    if (radius < 0) {
        radius = self->grid->fov_radius;
    }

    // Get FOV algorithm
    TCOD_fov_algorithm_t algorithm;
    bool was_none = false;
    if (!PyFOV::from_arg(fov_obj, &algorithm, &was_none)) {
        return NULL;
    }
    if (was_none) {
        algorithm = self->grid->fov_algorithm;
    }

    // Helper lambda to parse color
    auto parse_color = [](PyObject* obj, sf::Color& out, const sf::Color& default_val, const char* name) -> bool {
        if (!obj || obj == Py_None) {
            out = default_val;
            return true;
        }

        auto* mcrfpy_module = PyImport_ImportModule("mcrfpy");
        if (!mcrfpy_module) return false;

        auto* color_type = PyObject_GetAttrString(mcrfpy_module, "Color");
        Py_DECREF(mcrfpy_module);
        if (!color_type) return false;

        if (PyObject_IsInstance(obj, color_type)) {
            out = ((PyColorObject*)obj)->data;
            Py_DECREF(color_type);
            return true;
        } else if (PyTuple_Check(obj)) {
            int r, g, b, a = 255;
            if (!PyArg_ParseTuple(obj, "iii|i", &r, &g, &b, &a)) {
                Py_DECREF(color_type);
                return false;
            }
            out = sf::Color(r, g, b, a);
            Py_DECREF(color_type);
            return true;
        }

        Py_DECREF(color_type);
        PyErr_Format(PyExc_TypeError, "%s must be a Color object or (r, g, b[, a]) tuple", name);
        return false;
    };

    // Default colors for FOV visualization
    sf::Color visible_color(255, 255, 200, 64);   // Light yellow tint
    sf::Color discovered_color(128, 128, 128, 128); // Gray
    sf::Color unknown_color(0, 0, 0, 255);          // Black

    if (!parse_color(visible_obj, visible_color, visible_color, "visible")) return NULL;
    if (!parse_color(discovered_obj, discovered_color, discovered_color, "discovered")) return NULL;
    if (!parse_color(unknown_obj, unknown_color, unknown_color, "unknown")) return NULL;

    self->data->drawFOV(source_x, source_y, radius, algorithm, visible_color, discovered_color, unknown_color);
    Py_RETURN_NONE;
}

PyObject* PyGridLayerAPI::ColorLayer_apply_perspective(PyColorLayerObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"entity", "visible", "discovered", "unknown", NULL};
    PyObject* entity_obj;
    PyObject* visible_obj = nullptr;
    PyObject* discovered_obj = nullptr;
    PyObject* unknown_obj = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OOO", const_cast<char**>(kwlist),
                                     &entity_obj, &visible_obj, &discovered_obj, &unknown_obj)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }

    if (!self->grid) {
        PyErr_SetString(PyExc_RuntimeError, "Layer is not attached to a grid");
        return NULL;
    }

    // Get the Entity type
    auto* mcrfpy_module = PyImport_ImportModule("mcrfpy");
    if (!mcrfpy_module) return NULL;

    auto* entity_type = PyObject_GetAttrString(mcrfpy_module, "Entity");
    Py_DECREF(mcrfpy_module);
    if (!entity_type) return NULL;

    if (!PyObject_IsInstance(entity_obj, entity_type)) {
        Py_DECREF(entity_type);
        PyErr_SetString(PyExc_TypeError, "entity must be an Entity object");
        return NULL;
    }
    Py_DECREF(entity_type);

    // Get the shared_ptr to the entity
    PyUIEntityObject* py_entity = (PyUIEntityObject*)entity_obj;
    if (!py_entity->data) {
        PyErr_SetString(PyExc_RuntimeError, "Entity has no data");
        return NULL;
    }

    // Helper lambda to parse color
    auto parse_color = [](PyObject* obj, sf::Color& out, const sf::Color& default_val, const char* name) -> bool {
        if (!obj || obj == Py_None) {
            out = default_val;
            return true;
        }

        auto* mcrfpy_module = PyImport_ImportModule("mcrfpy");
        if (!mcrfpy_module) return false;

        auto* color_type = PyObject_GetAttrString(mcrfpy_module, "Color");
        Py_DECREF(mcrfpy_module);
        if (!color_type) return false;

        if (PyObject_IsInstance(obj, color_type)) {
            out = ((PyColorObject*)obj)->data;
            Py_DECREF(color_type);
            return true;
        } else if (PyTuple_Check(obj)) {
            int r, g, b, a = 255;
            if (!PyArg_ParseTuple(obj, "iii|i", &r, &g, &b, &a)) {
                Py_DECREF(color_type);
                return false;
            }
            out = sf::Color(r, g, b, a);
            Py_DECREF(color_type);
            return true;
        }

        Py_DECREF(color_type);
        PyErr_Format(PyExc_TypeError, "%s must be a Color object or (r, g, b[, a]) tuple", name);
        return false;
    };

    // Parse colors with defaults
    sf::Color visible_color(255, 255, 200, 64);
    sf::Color discovered_color(100, 100, 100, 128);
    sf::Color unknown_color(0, 0, 0, 255);

    if (!parse_color(visible_obj, visible_color, visible_color, "visible")) return NULL;
    if (!parse_color(discovered_obj, discovered_color, discovered_color, "discovered")) return NULL;
    if (!parse_color(unknown_obj, unknown_color, unknown_color, "unknown")) return NULL;

    self->data->applyPerspective(py_entity->data, visible_color, discovered_color, unknown_color);
    Py_RETURN_NONE;
}

PyObject* PyGridLayerAPI::ColorLayer_update_perspective(PyColorLayerObject* self, PyObject* args) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }

    if (!self->data->has_perspective) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no perspective binding. Call apply_perspective() first.");
        return NULL;
    }

    self->data->updatePerspective();
    Py_RETURN_NONE;
}

PyObject* PyGridLayerAPI::ColorLayer_clear_perspective(PyColorLayerObject* self, PyObject* args) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }

    self->data->clearPerspective();
    Py_RETURN_NONE;
}

PyObject* PyGridLayerAPI::ColorLayer_apply_hmap_threshold(PyColorLayerObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"source", "range", "color", NULL};
    PyObject* source_obj;
    PyObject* range_obj;
    PyObject* color_obj;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OOO", const_cast<char**>(kwlist),
                                     &source_obj, &range_obj, &color_obj)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }

    // Validate source is a HeightMap
    PyHeightMapObject* hmap;
    if (!IsHeightMapObject(source_obj, &hmap)) {
        PyErr_SetString(PyExc_TypeError, "source must be a HeightMap");
        return NULL;
    }

    if (!ValidateHeightMapSize(hmap, self->data->grid_x, self->data->grid_y)) {
        return NULL;
    }

    // Parse range
    float range_min, range_max;
    if (!ParseRange(range_obj, &range_min, &range_max, "range")) {
        return NULL;
    }

    // Parse color
    sf::Color color;
    if (!ParseColorArg(color_obj, color, "color")) {
        return NULL;
    }

    // Apply threshold
    int width = self->data->grid_x;
    int height = self->data->grid_y;

    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            float value = TCOD_heightmap_get_value(hmap->heightmap, x, y);
            if (value >= range_min && value <= range_max) {
                self->data->at(x, y) = color;
            }
        }
    }

    self->data->markDirty();

    // Return self for chaining
    Py_INCREF(self);
    return (PyObject*)self;
}

PyObject* PyGridLayerAPI::ColorLayer_apply_gradient(PyColorLayerObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"source", "range", "color_low", "color_high", NULL};
    PyObject* source_obj;
    PyObject* range_obj;
    PyObject* color_low_obj;
    PyObject* color_high_obj;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OOOO", const_cast<char**>(kwlist),
                                     &source_obj, &range_obj, &color_low_obj, &color_high_obj)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }

    // Validate source is a HeightMap
    PyHeightMapObject* hmap;
    if (!IsHeightMapObject(source_obj, &hmap)) {
        PyErr_SetString(PyExc_TypeError, "source must be a HeightMap");
        return NULL;
    }

    if (!ValidateHeightMapSize(hmap, self->data->grid_x, self->data->grid_y)) {
        return NULL;
    }

    // Parse range
    float range_min, range_max;
    if (!ParseRange(range_obj, &range_min, &range_max, "range")) {
        return NULL;
    }

    // Parse colors
    sf::Color color_low, color_high;
    if (!ParseColorArg(color_low_obj, color_low, "color_low")) {
        return NULL;
    }
    if (!ParseColorArg(color_high_obj, color_high, "color_high")) {
        return NULL;
    }

    // Apply gradient
    int width = self->data->grid_x;
    int height = self->data->grid_y;
    float range_span = range_max - range_min;

    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            float value = TCOD_heightmap_get_value(hmap->heightmap, x, y);
            if (value >= range_min && value <= range_max) {
                // Normalize value within range for interpolation
                float t = (range_span > 0.0f) ? (value - range_min) / range_span : 0.0f;
                self->data->at(x, y) = LerpColor(color_low, color_high, t);
            }
        }
    }

    self->data->markDirty();

    // Return self for chaining
    Py_INCREF(self);
    return (PyObject*)self;
}

PyObject* PyGridLayerAPI::ColorLayer_apply_ranges(PyColorLayerObject* self, PyObject* args) {
    PyObject* source_obj;
    PyObject* ranges_obj;

    if (!PyArg_ParseTuple(args, "OO", &source_obj, &ranges_obj)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }

    // Validate source is a HeightMap
    PyHeightMapObject* hmap;
    if (!IsHeightMapObject(source_obj, &hmap)) {
        PyErr_SetString(PyExc_TypeError, "source must be a HeightMap");
        return NULL;
    }

    if (!ValidateHeightMapSize(hmap, self->data->grid_x, self->data->grid_y)) {
        return NULL;
    }

    // Validate ranges is a list
    if (!PyList_Check(ranges_obj)) {
        PyErr_SetString(PyExc_TypeError, "ranges must be a list");
        return NULL;
    }

    // Pre-parse all ranges for validation
    // Each range can be:
    //   ((min, max), (r, g, b[, a])) - fixed color
    //   ((min, max), ((r1, g1, b1[, a1]), (r2, g2, b2[, a2]))) - gradient
    struct ColorRange {
        float min_val, max_val;
        sf::Color color_low;
        sf::Color color_high;
        bool is_gradient;
    };
    std::vector<ColorRange> ranges;

    Py_ssize_t n_ranges = PyList_Size(ranges_obj);
    for (Py_ssize_t i = 0; i < n_ranges; ++i) {
        PyObject* item = PyList_GetItem(ranges_obj, i);

        if (!PyTuple_Check(item) || PyTuple_Size(item) != 2) {
            PyErr_Format(PyExc_TypeError,
                         "ranges[%zd] must be a ((min, max), color) tuple", i);
            return NULL;
        }

        PyObject* range_tuple = PyTuple_GetItem(item, 0);
        PyObject* color_spec = PyTuple_GetItem(item, 1);

        float min_val, max_val;
        char range_name[32];
        snprintf(range_name, sizeof(range_name), "ranges[%zd] range", i);
        if (!ParseRange(range_tuple, &min_val, &max_val, range_name)) {
            return NULL;
        }

        ColorRange cr;
        cr.min_val = min_val;
        cr.max_val = max_val;

        // Determine if this is a gradient (tuple of 2 tuples) or fixed color
        // Check if color_spec is a tuple of 2 elements where each element is also a sequence
        bool is_gradient = false;
        if (PyTuple_Check(color_spec) && PyTuple_Size(color_spec) == 2) {
            PyObject* first = PyTuple_GetItem(color_spec, 0);
            PyObject* second = PyTuple_GetItem(color_spec, 1);
            // If both elements are tuples/lists (not ints), it's a gradient
            if ((PyTuple_Check(first) || PyList_Check(first)) &&
                (PyTuple_Check(second) || PyList_Check(second))) {
                is_gradient = true;
            }
        }

        cr.is_gradient = is_gradient;

        if (is_gradient) {
            // Parse as gradient: ((r1,g1,b1), (r2,g2,b2))
            PyObject* color_low_obj = PyTuple_GetItem(color_spec, 0);
            PyObject* color_high_obj = PyTuple_GetItem(color_spec, 1);

            char color_name[48];
            snprintf(color_name, sizeof(color_name), "ranges[%zd] color_low", i);
            if (!ParseColorArg(color_low_obj, cr.color_low, color_name)) {
                return NULL;
            }
            snprintf(color_name, sizeof(color_name), "ranges[%zd] color_high", i);
            if (!ParseColorArg(color_high_obj, cr.color_high, color_name)) {
                return NULL;
            }
        } else {
            // Parse as fixed color
            char color_name[48];
            snprintf(color_name, sizeof(color_name), "ranges[%zd] color", i);
            if (!ParseColorArg(color_spec, cr.color_low, color_name)) {
                return NULL;
            }
            cr.color_high = cr.color_low;  // Not used, but set for consistency
        }

        ranges.push_back(cr);
    }

    // Apply all ranges in order (later ranges override)
    int width = self->data->grid_x;
    int height = self->data->grid_y;

    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            float value = TCOD_heightmap_get_value(hmap->heightmap, x, y);

            // Check ranges in order, last match wins
            for (const auto& cr : ranges) {
                if (value >= cr.min_val && value <= cr.max_val) {
                    if (cr.is_gradient) {
                        float range_span = cr.max_val - cr.min_val;
                        float t = (range_span > 0.0f) ? (value - cr.min_val) / range_span : 0.0f;
                        self->data->at(x, y) = LerpColor(cr.color_low, cr.color_high, t);
                    } else {
                        self->data->at(x, y) = cr.color_low;
                    }
                }
            }
        }
    }

    self->data->markDirty();

    // Return self for chaining
    Py_INCREF(self);
    return (PyObject*)self;
}

PyObject* PyGridLayerAPI::ColorLayer_get_z_index(PyColorLayerObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }
    return PyLong_FromLong(self->data->z_index);
}

int PyGridLayerAPI::ColorLayer_set_z_index(PyColorLayerObject* self, PyObject* value, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return -1;
    }
    long z = PyLong_AsLong(value);
    if (PyErr_Occurred()) return -1;
    self->data->z_index = z;
    // TODO: Trigger re-sort in parent grid
    return 0;
}

PyObject* PyGridLayerAPI::ColorLayer_get_visible(PyColorLayerObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }
    return PyBool_FromLong(self->data->visible);
}

int PyGridLayerAPI::ColorLayer_set_visible(PyColorLayerObject* self, PyObject* value, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return -1;
    }
    int v = PyObject_IsTrue(value);
    if (v < 0) return -1;
    self->data->visible = v;
    return 0;
}

PyObject* PyGridLayerAPI::ColorLayer_get_grid_size(PyColorLayerObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }
    return Py_BuildValue("(ii)", self->data->grid_x, self->data->grid_y);
}

PyObject* PyGridLayerAPI::ColorLayer_repr(PyColorLayerObject* self) {
    std::ostringstream ss;
    if (!self->data) {
        ss << "<ColorLayer (invalid)>";
    } else {
        ss << "<ColorLayer z_index=" << self->data->z_index
           << " size=(" << self->data->grid_x << "x" << self->data->grid_y << ")"
           << " visible=" << (self->data->visible ? "True" : "False") << ">";
    }
    return PyUnicode_FromString(ss.str().c_str());
}

// =============================================================================
// Python API - TileLayer
// =============================================================================

PyMethodDef PyGridLayerAPI::TileLayer_methods[] = {
    {"at", (PyCFunction)PyGridLayerAPI::TileLayer_at, METH_VARARGS | METH_KEYWORDS,
     "at(pos) -> int\nat(x, y) -> int\n\n"
     "Get the tile index at cell position. Returns -1 if no tile.\n\n"
     "Args:\n"
     "    pos: Position as (x, y) tuple, list, or Vector\n"
     "    x, y: Position as separate integer arguments"},
    {"set", (PyCFunction)PyGridLayerAPI::TileLayer_set, METH_VARARGS,
     "set(pos, index)\n\n"
     "Set the tile index at cell position. Use -1 for no tile.\n\n"
     "Args:\n"
     "    pos: Position as (x, y) tuple, list, or Vector\n"
     "    index: Tile index (-1 for no tile)"},
    {"fill", (PyCFunction)PyGridLayerAPI::TileLayer_fill, METH_VARARGS,
     "fill(index)\n\nFill the entire layer with the specified tile index."},
    {"fill_rect", (PyCFunction)PyGridLayerAPI::TileLayer_fill_rect, METH_VARARGS | METH_KEYWORDS,
     "fill_rect(pos, size, index)\n\n"
     "Fill a rectangular region with a tile index.\n\n"
     "Args:\n"
     "    pos (tuple): Top-left corner as (x, y)\n"
     "    size (tuple): Dimensions as (width, height)\n"
     "    index (int): Tile index to fill with (-1 for no tile)"},
    {"apply_threshold", (PyCFunction)PyGridLayerAPI::TileLayer_apply_threshold, METH_VARARGS | METH_KEYWORDS,
     "apply_threshold(source, range, tile) -> TileLayer\n\n"
     "Set tile index for cells where HeightMap value is within range.\n\n"
     "Args:\n"
     "    source (HeightMap): Source heightmap (must match layer dimensions)\n"
     "    range (tuple): Value range as (min, max) inclusive\n"
     "    tile (int): Tile index to set for cells in range\n\n"
     "Returns:\n"
     "    self for method chaining\n\n"
     "Example:\n"
     "    layer.apply_threshold(terrain, (0.0, 0.3), WATER_TILE)"},
    {"apply_ranges", (PyCFunction)PyGridLayerAPI::TileLayer_apply_ranges, METH_VARARGS,
     "apply_ranges(source, ranges) -> TileLayer\n\n"
     "Apply multiple tile assignments in a single pass.\n\n"
     "Args:\n"
     "    source (HeightMap): Source heightmap (must match layer dimensions)\n"
     "    ranges (list): List of ((min, max), tile_index) tuples\n\n"
     "Returns:\n"
     "    self for method chaining\n\n"
     "Note:\n"
     "    Later ranges override earlier ones if overlapping.\n"
     "    Cells not matching any range are left unchanged.\n\n"
     "Example:\n"
     "    layer.apply_ranges(terrain, [\n"
     "        ((0.0, 0.2), DEEP_WATER),\n"
     "        ((0.2, 0.3), SHALLOW_WATER),\n"
     "        ((0.3, 0.7), GRASS),\n"
     "    ])"},
    {NULL}
};

PyGetSetDef PyGridLayerAPI::TileLayer_getsetters[] = {
    {"z_index", (getter)PyGridLayerAPI::TileLayer_get_z_index,
                (setter)PyGridLayerAPI::TileLayer_set_z_index,
     "Layer z-order. Negative values render below entities.", NULL},
    {"visible", (getter)PyGridLayerAPI::TileLayer_get_visible,
                (setter)PyGridLayerAPI::TileLayer_set_visible,
     "Whether the layer is rendered.", NULL},
    {"texture", (getter)PyGridLayerAPI::TileLayer_get_texture,
                (setter)PyGridLayerAPI::TileLayer_set_texture,
     "Texture atlas for tile sprites.", NULL},
    {"grid_size", (getter)PyGridLayerAPI::TileLayer_get_grid_size, NULL,
     "Layer dimensions as (width, height) tuple.", NULL},
    {NULL}
};

int PyGridLayerAPI::TileLayer_init(PyTileLayerObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"z_index", "texture", "grid_size", NULL};
    int z_index = -1;
    PyObject* texture_obj = nullptr;
    PyObject* grid_size_obj = nullptr;
    int grid_x = 0, grid_y = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|iOO", const_cast<char**>(kwlist),
                                     &z_index, &texture_obj, &grid_size_obj)) {
        return -1;
    }

    // Parse texture
    std::shared_ptr<PyTexture> texture;
    if (texture_obj && texture_obj != Py_None) {
        // Check if it's a PyTexture
        auto* mcrfpy_module = PyImport_ImportModule("mcrfpy");
        if (!mcrfpy_module) return -1;

        auto* texture_type = PyObject_GetAttrString(mcrfpy_module, "Texture");
        Py_DECREF(mcrfpy_module);
        if (!texture_type) return -1;

        if (PyObject_IsInstance(texture_obj, texture_type)) {
            texture = ((PyTextureObject*)texture_obj)->data;
        } else {
            Py_DECREF(texture_type);
            PyErr_SetString(PyExc_TypeError, "texture must be a Texture object");
            return -1;
        }
        Py_DECREF(texture_type);
    }

    // Parse grid_size if provided
    if (grid_size_obj && grid_size_obj != Py_None) {
        if (!PyTuple_Check(grid_size_obj) || PyTuple_Size(grid_size_obj) != 2) {
            PyErr_SetString(PyExc_TypeError, "grid_size must be a (width, height) tuple");
            return -1;
        }
        grid_x = PyLong_AsLong(PyTuple_GetItem(grid_size_obj, 0));
        grid_y = PyLong_AsLong(PyTuple_GetItem(grid_size_obj, 1));
        if (PyErr_Occurred()) return -1;
    }

    // Create the layer
    self->data = std::make_shared<TileLayer>(z_index, grid_x, grid_y, nullptr, texture);
    self->grid.reset();

    return 0;
}

PyObject* PyGridLayerAPI::TileLayer_at(PyTileLayerObject* self, PyObject* args, PyObject* kwds) {
    int x, y;
    if (!PyPosition_ParseInt(args, kwds, &x, &y)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }

    if (x < 0 || x >= self->data->grid_x || y < 0 || y >= self->data->grid_y) {
        PyErr_SetString(PyExc_IndexError, "Cell coordinates out of bounds");
        return NULL;
    }

    return PyLong_FromLong(self->data->at(x, y));
}

PyObject* PyGridLayerAPI::TileLayer_set(PyTileLayerObject* self, PyObject* args) {
    PyObject* pos_obj;
    int index;
    if (!PyArg_ParseTuple(args, "Oi", &pos_obj, &index)) {
        return NULL;
    }

    int x, y;
    if (!PyPosition_FromObjectInt(pos_obj, &x, &y)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }

    if (x < 0 || x >= self->data->grid_x || y < 0 || y >= self->data->grid_y) {
        PyErr_SetString(PyExc_IndexError, "Cell coordinates out of bounds");
        return NULL;
    }

    self->data->at(x, y) = index;
    self->data->markDirty(x, y);  // Mark only the affected chunk
    Py_RETURN_NONE;
}

PyObject* PyGridLayerAPI::TileLayer_fill(PyTileLayerObject* self, PyObject* args) {
    int index;
    if (!PyArg_ParseTuple(args, "i", &index)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }

    self->data->fill(index);
    Py_RETURN_NONE;
}

PyObject* PyGridLayerAPI::TileLayer_fill_rect(PyTileLayerObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"pos", "size", "index", NULL};
    PyObject* pos_obj;
    PyObject* size_obj;
    int tile_index;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OOi", const_cast<char**>(kwlist),
                                     &pos_obj, &size_obj, &tile_index)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }

    // Parse pos
    int x, y;
    if (PyTuple_Check(pos_obj) && PyTuple_Size(pos_obj) == 2) {
        x = PyLong_AsLong(PyTuple_GetItem(pos_obj, 0));
        y = PyLong_AsLong(PyTuple_GetItem(pos_obj, 1));
        if (PyErr_Occurred()) return NULL;
    } else {
        PyErr_SetString(PyExc_TypeError, "pos must be a (x, y) tuple");
        return NULL;
    }

    // Parse size
    int width, height;
    if (PyTuple_Check(size_obj) && PyTuple_Size(size_obj) == 2) {
        width = PyLong_AsLong(PyTuple_GetItem(size_obj, 0));
        height = PyLong_AsLong(PyTuple_GetItem(size_obj, 1));
        if (PyErr_Occurred()) return NULL;
    } else {
        PyErr_SetString(PyExc_TypeError, "size must be a (width, height) tuple");
        return NULL;
    }

    self->data->fillRect(x, y, width, height, tile_index);
    Py_RETURN_NONE;
}

PyObject* PyGridLayerAPI::TileLayer_apply_threshold(PyTileLayerObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"source", "range", "tile", NULL};
    PyObject* source_obj;
    PyObject* range_obj;
    int tile_index;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OOi", const_cast<char**>(kwlist),
                                     &source_obj, &range_obj, &tile_index)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }

    // Validate source is a HeightMap
    PyHeightMapObject* hmap;
    if (!IsHeightMapObject(source_obj, &hmap)) {
        PyErr_SetString(PyExc_TypeError, "source must be a HeightMap");
        return NULL;
    }

    if (!ValidateHeightMapSize(hmap, self->data->grid_x, self->data->grid_y)) {
        return NULL;
    }

    // Parse range
    float range_min, range_max;
    if (!ParseRange(range_obj, &range_min, &range_max, "range")) {
        return NULL;
    }

    // Apply threshold
    int width = self->data->grid_x;
    int height = self->data->grid_y;

    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            float value = TCOD_heightmap_get_value(hmap->heightmap, x, y);
            if (value >= range_min && value <= range_max) {
                self->data->at(x, y) = tile_index;
            }
        }
    }

    self->data->markDirty();

    // Return self for chaining
    Py_INCREF(self);
    return (PyObject*)self;
}

PyObject* PyGridLayerAPI::TileLayer_apply_ranges(PyTileLayerObject* self, PyObject* args) {
    PyObject* source_obj;
    PyObject* ranges_obj;

    if (!PyArg_ParseTuple(args, "OO", &source_obj, &ranges_obj)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }

    // Validate source is a HeightMap
    PyHeightMapObject* hmap;
    if (!IsHeightMapObject(source_obj, &hmap)) {
        PyErr_SetString(PyExc_TypeError, "source must be a HeightMap");
        return NULL;
    }

    if (!ValidateHeightMapSize(hmap, self->data->grid_x, self->data->grid_y)) {
        return NULL;
    }

    // Validate ranges is a list
    if (!PyList_Check(ranges_obj)) {
        PyErr_SetString(PyExc_TypeError, "ranges must be a list");
        return NULL;
    }

    // Pre-parse all ranges for validation
    struct TileRange {
        float min_val, max_val;
        int tile_index;
    };
    std::vector<TileRange> ranges;

    Py_ssize_t n_ranges = PyList_Size(ranges_obj);
    for (Py_ssize_t i = 0; i < n_ranges; ++i) {
        PyObject* item = PyList_GetItem(ranges_obj, i);

        if (!PyTuple_Check(item) || PyTuple_Size(item) != 2) {
            PyErr_Format(PyExc_TypeError,
                         "ranges[%zd] must be a ((min, max), tile) tuple", i);
            return NULL;
        }

        PyObject* range_tuple = PyTuple_GetItem(item, 0);
        PyObject* tile_obj = PyTuple_GetItem(item, 1);

        float min_val, max_val;
        char range_name[32];
        snprintf(range_name, sizeof(range_name), "ranges[%zd] range", i);
        if (!ParseRange(range_tuple, &min_val, &max_val, range_name)) {
            return NULL;
        }

        int tile_index = (int)PyLong_AsLong(tile_obj);
        if (PyErr_Occurred()) {
            PyErr_Format(PyExc_TypeError, "ranges[%zd] tile must be an integer", i);
            return NULL;
        }

        ranges.push_back({min_val, max_val, tile_index});
    }

    // Apply all ranges in order (later ranges override)
    int width = self->data->grid_x;
    int height = self->data->grid_y;

    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            float value = TCOD_heightmap_get_value(hmap->heightmap, x, y);

            // Check ranges in order, last match wins
            for (const auto& range : ranges) {
                if (value >= range.min_val && value <= range.max_val) {
                    self->data->at(x, y) = range.tile_index;
                }
            }
        }
    }

    self->data->markDirty();

    // Return self for chaining
    Py_INCREF(self);
    return (PyObject*)self;
}

PyObject* PyGridLayerAPI::TileLayer_get_z_index(PyTileLayerObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }
    return PyLong_FromLong(self->data->z_index);
}

int PyGridLayerAPI::TileLayer_set_z_index(PyTileLayerObject* self, PyObject* value, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return -1;
    }
    long z = PyLong_AsLong(value);
    if (PyErr_Occurred()) return -1;
    self->data->z_index = z;
    // TODO: Trigger re-sort in parent grid
    return 0;
}

PyObject* PyGridLayerAPI::TileLayer_get_visible(PyTileLayerObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }
    return PyBool_FromLong(self->data->visible);
}

int PyGridLayerAPI::TileLayer_set_visible(PyTileLayerObject* self, PyObject* value, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return -1;
    }
    int v = PyObject_IsTrue(value);
    if (v < 0) return -1;
    self->data->visible = v;
    return 0;
}

PyObject* PyGridLayerAPI::TileLayer_get_texture(PyTileLayerObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }

    if (!self->data->texture) {
        Py_RETURN_NONE;
    }

    auto* texture_type = (PyTypeObject*)PyObject_GetAttrString(
        PyImport_ImportModule("mcrfpy"), "Texture");
    if (!texture_type) return NULL;

    PyTextureObject* tex_obj = (PyTextureObject*)texture_type->tp_alloc(texture_type, 0);
    Py_DECREF(texture_type);
    if (!tex_obj) return NULL;

    tex_obj->data = self->data->texture;
    return (PyObject*)tex_obj;
}

int PyGridLayerAPI::TileLayer_set_texture(PyTileLayerObject* self, PyObject* value, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return -1;
    }

    if (value == Py_None) {
        self->data->texture.reset();
        self->data->markDirty();  // Mark ALL chunks for re-render (texture change affects all)
        return 0;
    }

    auto* mcrfpy_module = PyImport_ImportModule("mcrfpy");
    if (!mcrfpy_module) return -1;

    auto* texture_type = PyObject_GetAttrString(mcrfpy_module, "Texture");
    Py_DECREF(mcrfpy_module);
    if (!texture_type) return -1;

    if (!PyObject_IsInstance(value, texture_type)) {
        Py_DECREF(texture_type);
        PyErr_SetString(PyExc_TypeError, "texture must be a Texture object or None");
        return -1;
    }
    Py_DECREF(texture_type);

    self->data->texture = ((PyTextureObject*)value)->data;
    self->data->markDirty();  // Mark ALL chunks for re-render (texture change affects all)
    return 0;
}

PyObject* PyGridLayerAPI::TileLayer_get_grid_size(PyTileLayerObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }
    return Py_BuildValue("(ii)", self->data->grid_x, self->data->grid_y);
}

PyObject* PyGridLayerAPI::TileLayer_repr(PyTileLayerObject* self) {
    std::ostringstream ss;
    if (!self->data) {
        ss << "<TileLayer (invalid)>";
    } else {
        ss << "<TileLayer z_index=" << self->data->z_index
           << " size=(" << self->data->grid_x << "x" << self->data->grid_y << ")"
           << " visible=" << (self->data->visible ? "True" : "False")
           << " texture=" << (self->data->texture ? "set" : "None") << ">";
    }
    return PyUnicode_FromString(ss.str().c_str());
}
