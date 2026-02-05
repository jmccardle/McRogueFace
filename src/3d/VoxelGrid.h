// VoxelGrid.h - Dense 3D voxel array with material palette
// Part of McRogueFace 3D Extension - Milestones 9-10
#pragma once

#include "../Common.h"
#include "Math3D.h"
#include "MeshLayer.h"  // For MeshVertex (needed for std::vector<MeshVertex>)
#include <vector>
#include <string>
#include <stdexcept>

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

    // Mesh caching (Milestone 10)
    mutable bool meshDirty_ = true;
    mutable std::vector<MeshVertex> cachedVertices_;

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

    // Bulk operations
    void fill(uint8_t material);
    void clear() { fill(0); }
    void fillBox(int x0, int y0, int z0, int x1, int y1, int z1, uint8_t material);

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

    // Mesh caching (Milestone 10)
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

    // Memory info (for debugging)
    size_t memoryUsageBytes() const {
        return data_.size() + materials_.size() * sizeof(VoxelMaterial);
    }
};

} // namespace mcrf
