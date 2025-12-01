#include "GridLayers.h"
#include "UIGrid.h"
#include "PyColor.h"
#include "PyTexture.h"
#include "PyFOV.h"
#include <sstream>

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

void GridLayer::getChunkCoords(int cell_x, int cell_y, int& chunk_x, int& chunk_y) const {
    chunk_x = cell_x / CHUNK_SIZE;
    chunk_y = cell_y / CHUNK_SIZE;
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
      colors(grid_x * grid_y, sf::Color::Transparent)
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
    {"at", (PyCFunction)PyGridLayerAPI::ColorLayer_at, METH_VARARGS,
     "at(x, y) -> Color\n\nGet the color at cell position (x, y)."},
    {"set", (PyCFunction)PyGridLayerAPI::ColorLayer_set, METH_VARARGS,
     "set(x, y, color)\n\nSet the color at cell position (x, y)."},
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

PyObject* PyGridLayerAPI::ColorLayer_at(PyColorLayerObject* self, PyObject* args) {
    int x, y;
    if (!PyArg_ParseTuple(args, "ii", &x, &y)) {
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
    int x, y;
    PyObject* color_obj;
    if (!PyArg_ParseTuple(args, "iiO", &x, &y, &color_obj)) {
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
    {"at", (PyCFunction)PyGridLayerAPI::TileLayer_at, METH_VARARGS,
     "at(x, y) -> int\n\nGet the tile index at cell position (x, y). Returns -1 if no tile."},
    {"set", (PyCFunction)PyGridLayerAPI::TileLayer_set, METH_VARARGS,
     "set(x, y, index)\n\nSet the tile index at cell position (x, y). Use -1 for no tile."},
    {"fill", (PyCFunction)PyGridLayerAPI::TileLayer_fill, METH_VARARGS,
     "fill(index)\n\nFill the entire layer with the specified tile index."},
    {"fill_rect", (PyCFunction)PyGridLayerAPI::TileLayer_fill_rect, METH_VARARGS | METH_KEYWORDS,
     "fill_rect(pos, size, index)\n\n"
     "Fill a rectangular region with a tile index.\n\n"
     "Args:\n"
     "    pos (tuple): Top-left corner as (x, y)\n"
     "    size (tuple): Dimensions as (width, height)\n"
     "    index (int): Tile index to fill with (-1 for no tile)"},
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

PyObject* PyGridLayerAPI::TileLayer_at(PyTileLayerObject* self, PyObject* args) {
    int x, y;
    if (!PyArg_ParseTuple(args, "ii", &x, &y)) {
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
    int x, y, index;
    if (!PyArg_ParseTuple(args, "iii", &x, &y, &index)) {
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
