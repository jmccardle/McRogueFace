#include "GridChunk.h"
#include "UIGrid.h"
#include "PyTexture.h"
#include <algorithm>
#include <cmath>

// =============================================================================
// GridChunk implementation
// =============================================================================

GridChunk::GridChunk(int chunk_x, int chunk_y, int width, int height,
                     int world_x, int world_y, UIGrid* parent)
    : chunk_x(chunk_x), chunk_y(chunk_y),
      width(width), height(height),
      world_x(world_x), world_y(world_y),
      cells(width * height),
      dirty(true), texture_initialized(false),
      parent_grid(parent)
{}

UIGridPoint& GridChunk::at(int local_x, int local_y) {
    return cells[local_y * width + local_x];
}

const UIGridPoint& GridChunk::at(int local_x, int local_y) const {
    return cells[local_y * width + local_x];
}

void GridChunk::markDirty() {
    dirty = true;
}

void GridChunk::ensureTexture(int cell_width, int cell_height) {
    unsigned int required_width = width * cell_width;
    unsigned int required_height = height * cell_height;

    if (texture_initialized &&
        cached_texture.getSize().x == required_width &&
        cached_texture.getSize().y == required_height) {
        return;
    }

    if (!cached_texture.create(required_width, required_height)) {
        texture_initialized = false;
        return;
    }

    texture_initialized = true;
    dirty = true;  // Force re-render after resize
    cached_sprite.setTexture(cached_texture.getTexture());
}

void GridChunk::renderToTexture(int cell_width, int cell_height,
                                std::shared_ptr<PyTexture> texture) {
    ensureTexture(cell_width, cell_height);
    if (!texture_initialized) return;

    cached_texture.clear(sf::Color::Transparent);

    sf::RectangleShape rect;
    rect.setSize(sf::Vector2f(cell_width, cell_height));
    rect.setOutlineThickness(0);

    // Render all cells in this chunk
    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            const auto& cell = at(x, y);
            sf::Vector2f pixel_pos(x * cell_width, y * cell_height);

            // Draw background color
            rect.setPosition(pixel_pos);
            rect.setFillColor(cell.color);
            cached_texture.draw(rect);

            // Draw tile sprite if available
            if (texture && cell.tilesprite != -1) {
                sf::Sprite sprite = texture->sprite(cell.tilesprite, pixel_pos,
                                                    sf::Vector2f(1.0f, 1.0f));
                cached_texture.draw(sprite);
            }
        }
    }

    cached_texture.display();
    dirty = false;
}

sf::FloatRect GridChunk::getWorldBounds(int cell_width, int cell_height) const {
    return sf::FloatRect(
        sf::Vector2f(world_x * cell_width, world_y * cell_height),
        sf::Vector2f(width * cell_width, height * cell_height)
    );
}

bool GridChunk::isVisible(float left_edge, float top_edge,
                          float right_edge, float bottom_edge) const {
    // Check if chunk's cell range overlaps with viewport's cell range
    float chunk_right = world_x + width;
    float chunk_bottom = world_y + height;

    return !(world_x >= right_edge || chunk_right <= left_edge ||
             world_y >= bottom_edge || chunk_bottom <= top_edge);
}

// =============================================================================
// ChunkManager implementation
// =============================================================================

ChunkManager::ChunkManager(int grid_x, int grid_y, UIGrid* parent)
    : grid_x(grid_x), grid_y(grid_y), parent_grid(parent)
{
    // Calculate number of chunks needed
    chunks_x = (grid_x + GridChunk::CHUNK_SIZE - 1) / GridChunk::CHUNK_SIZE;
    chunks_y = (grid_y + GridChunk::CHUNK_SIZE - 1) / GridChunk::CHUNK_SIZE;

    chunks.reserve(chunks_x * chunks_y);

    // Create chunks
    for (int cy = 0; cy < chunks_y; ++cy) {
        for (int cx = 0; cx < chunks_x; ++cx) {
            // Calculate world position
            int world_x = cx * GridChunk::CHUNK_SIZE;
            int world_y = cy * GridChunk::CHUNK_SIZE;

            // Calculate actual size (may be smaller at edges)
            int chunk_width = std::min(GridChunk::CHUNK_SIZE, grid_x - world_x);
            int chunk_height = std::min(GridChunk::CHUNK_SIZE, grid_y - world_y);

            chunks.push_back(std::make_unique<GridChunk>(
                cx, cy, chunk_width, chunk_height, world_x, world_y, parent
            ));
        }
    }
}

GridChunk* ChunkManager::getChunkForCell(int x, int y) {
    if (x < 0 || x >= grid_x || y < 0 || y >= grid_y) {
        return nullptr;
    }

    int chunk_x = x / GridChunk::CHUNK_SIZE;
    int chunk_y = y / GridChunk::CHUNK_SIZE;
    return getChunk(chunk_x, chunk_y);
}

const GridChunk* ChunkManager::getChunkForCell(int x, int y) const {
    if (x < 0 || x >= grid_x || y < 0 || y >= grid_y) {
        return nullptr;
    }

    int chunk_x = x / GridChunk::CHUNK_SIZE;
    int chunk_y = y / GridChunk::CHUNK_SIZE;
    return getChunk(chunk_x, chunk_y);
}

GridChunk* ChunkManager::getChunk(int chunk_x, int chunk_y) {
    if (chunk_x < 0 || chunk_x >= chunks_x || chunk_y < 0 || chunk_y >= chunks_y) {
        return nullptr;
    }
    return chunks[chunk_y * chunks_x + chunk_x].get();
}

const GridChunk* ChunkManager::getChunk(int chunk_x, int chunk_y) const {
    if (chunk_x < 0 || chunk_x >= chunks_x || chunk_y < 0 || chunk_y >= chunks_y) {
        return nullptr;
    }
    return chunks[chunk_y * chunks_x + chunk_x].get();
}

UIGridPoint& ChunkManager::at(int x, int y) {
    GridChunk* chunk = getChunkForCell(x, y);
    if (!chunk) {
        // Return a static dummy point for out-of-bounds access
        // This matches the original behavior of UIGrid::at()
        static UIGridPoint dummy;
        return dummy;
    }

    // Convert to local coordinates within chunk
    int local_x = x % GridChunk::CHUNK_SIZE;
    int local_y = y % GridChunk::CHUNK_SIZE;

    // Mark chunk dirty when accessed for modification
    chunk->markDirty();

    return chunk->at(local_x, local_y);
}

const UIGridPoint& ChunkManager::at(int x, int y) const {
    const GridChunk* chunk = getChunkForCell(x, y);
    if (!chunk) {
        static UIGridPoint dummy;
        return dummy;
    }

    int local_x = x % GridChunk::CHUNK_SIZE;
    int local_y = y % GridChunk::CHUNK_SIZE;

    return chunk->at(local_x, local_y);
}

void ChunkManager::markAllDirty() {
    for (auto& chunk : chunks) {
        chunk->markDirty();
    }
}

std::vector<GridChunk*> ChunkManager::getVisibleChunks(float left_edge, float top_edge,
                                                        float right_edge, float bottom_edge) {
    std::vector<GridChunk*> visible;
    visible.reserve(chunks.size()); // Pre-allocate for worst case

    for (auto& chunk : chunks) {
        if (chunk->isVisible(left_edge, top_edge, right_edge, bottom_edge)) {
            visible.push_back(chunk.get());
        }
    }

    return visible;
}

void ChunkManager::resize(int new_grid_x, int new_grid_y) {
    // For now, simple rebuild - could be optimized to preserve data
    grid_x = new_grid_x;
    grid_y = new_grid_y;

    chunks_x = (grid_x + GridChunk::CHUNK_SIZE - 1) / GridChunk::CHUNK_SIZE;
    chunks_y = (grid_y + GridChunk::CHUNK_SIZE - 1) / GridChunk::CHUNK_SIZE;

    chunks.clear();
    chunks.reserve(chunks_x * chunks_y);

    for (int cy = 0; cy < chunks_y; ++cy) {
        for (int cx = 0; cx < chunks_x; ++cx) {
            int world_x = cx * GridChunk::CHUNK_SIZE;
            int world_y = cy * GridChunk::CHUNK_SIZE;
            int chunk_width = std::min(GridChunk::CHUNK_SIZE, grid_x - world_x);
            int chunk_height = std::min(GridChunk::CHUNK_SIZE, grid_y - world_y);

            chunks.push_back(std::make_unique<GridChunk>(
                cx, cy, chunk_width, chunk_height, world_x, world_y, parent_grid
            ));
        }
    }
}

int ChunkManager::dirtyChunks() const {
    int count = 0;
    for (const auto& chunk : chunks) {
        if (chunk->dirty) ++count;
    }
    return count;
}
