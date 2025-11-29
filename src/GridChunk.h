#pragma once
#include "Common.h"
#include <SFML/Graphics.hpp>
#include <vector>
#include <memory>
#include "UIGridPoint.h"

// Forward declarations
class UIGrid;
class PyTexture;

/**
 * #123 - Grid chunk for sub-grid rendering system
 *
 * Each chunk represents a CHUNK_SIZE x CHUNK_SIZE portion of the grid.
 * Chunks have their own RenderTexture and dirty flag for efficient
 * incremental rendering - only dirty chunks are re-rendered.
 */
class GridChunk {
public:
    // Compile-time configurable chunk size (power of 2 recommended)
    static constexpr int CHUNK_SIZE = 64;

    // Position of this chunk in chunk coordinates
    int chunk_x, chunk_y;

    // Actual dimensions (may be less than CHUNK_SIZE at grid edges)
    int width, height;

    // World position (in cell coordinates)
    int world_x, world_y;

    // Cell data for this chunk
    std::vector<UIGridPoint> cells;

    // Cached rendering
    sf::RenderTexture cached_texture;
    sf::Sprite cached_sprite;
    bool dirty;
    bool texture_initialized;

    // Parent grid reference (for texture access)
    UIGrid* parent_grid;

    // Constructor
    GridChunk(int chunk_x, int chunk_y, int width, int height,
              int world_x, int world_y, UIGrid* parent);

    // Access cell at local chunk coordinates
    UIGridPoint& at(int local_x, int local_y);
    const UIGridPoint& at(int local_x, int local_y) const;

    // Mark chunk as needing re-render
    void markDirty();

    // Ensure texture is properly sized
    void ensureTexture(int cell_width, int cell_height);

    // Render chunk content to cached texture
    void renderToTexture(int cell_width, int cell_height,
                         std::shared_ptr<PyTexture> texture);

    // Get pixel bounds of this chunk in world coordinates
    sf::FloatRect getWorldBounds(int cell_width, int cell_height) const;

    // Check if chunk overlaps with viewport
    bool isVisible(float left_edge, float top_edge,
                   float right_edge, float bottom_edge) const;
};

/**
 * Manages a 2D array of chunks for a grid
 */
class ChunkManager {
public:
    // Dimensions in chunks
    int chunks_x, chunks_y;

    // Grid dimensions in cells
    int grid_x, grid_y;

    // All chunks (row-major order)
    std::vector<std::unique_ptr<GridChunk>> chunks;

    // Parent grid
    UIGrid* parent_grid;

    // Constructor - creates chunks for given grid dimensions
    ChunkManager(int grid_x, int grid_y, UIGrid* parent);

    // Get chunk containing cell (x, y)
    GridChunk* getChunkForCell(int x, int y);
    const GridChunk* getChunkForCell(int x, int y) const;

    // Get chunk at chunk coordinates
    GridChunk* getChunk(int chunk_x, int chunk_y);
    const GridChunk* getChunk(int chunk_x, int chunk_y) const;

    // Access cell at grid coordinates (routes through chunk)
    UIGridPoint& at(int x, int y);
    const UIGridPoint& at(int x, int y) const;

    // Mark all chunks dirty (for full rebuild)
    void markAllDirty();

    // Get chunks that overlap with viewport
    std::vector<GridChunk*> getVisibleChunks(float left_edge, float top_edge,
                                              float right_edge, float bottom_edge);

    // Resize grid (rebuilds chunks)
    void resize(int new_grid_x, int new_grid_y);

    // Get total number of chunks
    int totalChunks() const { return chunks_x * chunks_y; }

    // Get number of dirty chunks
    int dirtyChunks() const;
};
