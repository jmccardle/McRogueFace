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
      dirty(true),
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

// #150 - Removed ensureTexture/renderToTexture - base layer rendering removed
// GridChunk now only provides data storage for GridPoints

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
