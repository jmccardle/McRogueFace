// VoxelGrid.h - Dense 3D voxel array with material palette
// Part of McRogueFace 3D Extension - Milestones 9-11
#pragma once

#include "../Common.h"
#include "Math3D.h"
#include "MeshLayer.h"  // For MeshVertex (needed for std::vector<MeshVertex>)
#include <vector>
#include <string>
#include <stdexcept>
#include <cstdint>

namespace mcrf {

// =============================================================================
// VoxelMaterial - Properties for a voxel material type
// =============================================================================

struct VoxelMaterial {
    std::string name;
    sf::Color color;           // Fallback solid color
    int spriteIndex = -1;      // Texture atlas index (-1 = use color)
    bool transparent = false;  // For FOV projection and face culling
    float pathCost = 1.0f;     // Navigation cost multiplier (0 = impassable)

    VoxelMaterial() : name("unnamed"), color(sf::Color::White) {}
    VoxelMaterial(const std::string& n, sf::Color c, int sprite = -1,
                  bool transp = false, float cost = 1.0f)
        : name(n), color(c), spriteIndex(sprite), transparent(transp), pathCost(cost) {}
};

// =============================================================================
// VoxelRegion - Portable voxel data for copy/paste operations (Milestone 11)
// =============================================================================

struct VoxelRegion {
    int width, height, depth;
    std::vector<uint8_t> data;

    VoxelRegion() : width(0), height(0), depth(0) {}
    VoxelRegion(int w, int h, int d) : width(w), height(h), depth(d),
        data(static_cast<size_t>(w) * h * d, 0) {}

    bool isValid() const { return width > 0 && height > 0 && depth > 0; }
    size_t totalVoxels() const { return static_cast<size_t>(width) * height * depth; }
};

// =============================================================================
// VoxelGrid - Dense 3D array of material IDs
// =============================================================================

class VoxelGrid {
private:
    int width_, height_, depth_;
    float cellSize_;
    std::vector<uint8_t> data_;          // Material ID per cell (0 = air)
    std::vector<VoxelMaterial> materials_;

    // Transform
    vec3 offset_;
    float rotation_ = 0.0f;  // Y-axis only, degrees

    // Mesh caching (Milestones 10, 13)
    mutable bool meshDirty_ = true;
    mutable std::vector<MeshVertex> cachedVertices_;
    bool greedyMeshing_ = false;  // Use greedy meshing algorithm
    bool visible_ = true;          // Visibility toggle for rendering

    // Index calculation (row-major: X varies fastest, then Y, then Z)
    inline size_t index(int x, int y, int z) const {
        return static_cast<size_t>(z) * (width_ * height_) +
               static_cast<size_t>(y) * width_ +
               static_cast<size_t>(x);
    }

public:
    // Constructor
    VoxelGrid(int w, int h, int d, float cellSize = 1.0f);

    // Dimensions (read-only)
    int width() const { return width_; }
    int height() const { return height_; }
    int depth() const { return depth_; }
    float cellSize() const { return cellSize_; }
    size_t totalVoxels() const { return static_cast<size_t>(width_) * height_ * depth_; }

    // Per-voxel access
    uint8_t get(int x, int y, int z) const;
    void set(int x, int y, int z, uint8_t material);
    bool isValid(int x, int y, int z) const;

    // Material palette
    // Returns 1-indexed material ID (0 = air, always implicit)
    uint8_t addMaterial(const VoxelMaterial& mat);
    uint8_t addMaterial(const std::string& name, sf::Color color,
                        int spriteIndex = -1, bool transparent = false,
                        float pathCost = 1.0f);
    const VoxelMaterial& getMaterial(uint8_t id) const;
    size_t materialCount() const { return materials_.size(); }

    // Bulk operations - Basic
    void fill(uint8_t material);
    void clear() { fill(0); }
    void fillBox(int x0, int y0, int z0, int x1, int y1, int z1, uint8_t material);

    // Bulk operations - Milestone 11
    void fillBoxHollow(int x0, int y0, int z0, int x1, int y1, int z1,
                       uint8_t material, int thickness = 1);
    void fillSphere(int cx, int cy, int cz, int radius, uint8_t material);
    void fillCylinder(int cx, int cy, int cz, int radius, int height, uint8_t material);
    void fillNoise(int x0, int y0, int z0, int x1, int y1, int z1,
                   uint8_t material, float threshold = 0.5f,
                   float scale = 0.1f, unsigned int seed = 0);

    // Copy/paste operations - Milestone 11
    VoxelRegion copyRegion(int x0, int y0, int z0, int x1, int y1, int z1) const;
    void pasteRegion(const VoxelRegion& region, int x, int y, int z, bool skipAir = true);

    // Navigation projection - Milestone 12
    struct NavInfo {
        float height = 0.0f;
        bool walkable = false;
        bool transparent = true;
        float pathCost = 1.0f;
    };

    /// Project a single column to get navigation info
    /// @param x X coordinate in voxel grid
    /// @param z Z coordinate in voxel grid
    /// @param headroom Required air voxels above floor (default 2)
    /// @return Navigation info for this column
    NavInfo projectColumn(int x, int z, int headroom = 2) const;

    // Transform
    void setOffset(const vec3& offset) { offset_ = offset; }
    void setOffset(float x, float y, float z) { offset_ = vec3(x, y, z); }
    vec3 getOffset() const { return offset_; }
    void setRotation(float degrees) { rotation_ = degrees; }
    float getRotation() const { return rotation_; }
    mat4 getModelMatrix() const;

    // Statistics
    size_t countNonAir() const;
    size_t countMaterial(uint8_t material) const;

    // Mesh caching (Milestones 10, 13)
    /// Mark mesh as needing rebuild (called automatically by set/fill operations)
    void markDirty() { meshDirty_ = true; }

    /// Check if mesh needs rebuild
    bool isMeshDirty() const { return meshDirty_; }

    /// Get vertices for rendering (rebuilds mesh if dirty)
    const std::vector<MeshVertex>& getVertices() const;

    /// Force immediate mesh rebuild
    void rebuildMesh() const;

    /// Get vertex count after mesh generation
    size_t vertexCount() const { return cachedVertices_.size(); }

    /// Enable/disable greedy meshing (Milestone 13)
    /// Greedy meshing merges coplanar faces to reduce vertex count
    void setGreedyMeshing(bool enabled) { greedyMeshing_ = enabled; markDirty(); }
    bool isGreedyMeshingEnabled() const { return greedyMeshing_; }

    /// Show/hide this voxel grid in rendering
    void setVisible(bool v) { visible_ = v; }
    bool isVisible() const { return visible_; }

    // Memory info (for debugging)
    size_t memoryUsageBytes() const {
        return data_.size() + materials_.size() * sizeof(VoxelMaterial);
    }

    // Serialization (Milestone 14)
    /// Save voxel grid to binary file
    /// @param path File path to save to
    /// @return true on success
    bool save(const std::string& path) const;

    /// Load voxel grid from binary file
    /// @param path File path to load from
    /// @return true on success
    bool load(const std::string& path);

    /// Save to memory buffer
    /// @param buffer Output buffer (resized as needed)
    /// @return true on success
    bool saveToBuffer(std::vector<uint8_t>& buffer) const;

    /// Load from memory buffer
    /// @param data Buffer to load from
    /// @param size Buffer size
    /// @return true on success
    bool loadFromBuffer(const uint8_t* data, size_t size);
};

} // namespace mcrf
