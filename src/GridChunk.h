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
 * #123 - Grid chunk for sub-grid data storage
 * #150 - Rendering removed; layers now handle all rendering
 *
 * Each chunk represents a CHUNK_SIZE x CHUNK_SIZE portion of the grid.
 * Chunks store GridPoint data for pathfinding and game logic.
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

    // Cell data for this chunk (pathfinding properties only)
    std::vector<UIGridPoint> cells;

    // Dirty flag (for layer sync if needed)
    bool dirty;

    // Parent grid reference
    UIGrid* parent_grid;

    // Constructor
    GridChunk(int chunk_x, int chunk_y, int width, int height,
              int world_x, int world_y, UIGrid* parent);

    // Access cell at local chunk coordinates
    UIGridPoint& at(int local_x, int local_y);
    const UIGridPoint& at(int local_x, int local_y) const;

    // Mark chunk as dirty
    void markDirty();

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

    // Resize grid (rebuilds chunks)
    void resize(int new_grid_x, int new_grid_y);

    // Get total number of chunks
    int totalChunks() const { return chunks_x * chunks_y; }

    // Get number of dirty chunks
    int dirtyChunks() const;
};
