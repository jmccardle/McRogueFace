// VoxelGrid.cpp - Dense 3D voxel array implementation
// Part of McRogueFace 3D Extension - Milestones 9-10

#include "VoxelGrid.h"
#include "VoxelMesher.h"
#include "MeshLayer.h"  // For MeshVertex

namespace mcrf {

// Static air material for out-of-bounds or ID=0 queries
static VoxelMaterial airMaterial{"air", sf::Color::Transparent, -1, true, 0.0f};

// =============================================================================
// Constructor
// =============================================================================

VoxelGrid::VoxelGrid(int w, int h, int d, float cellSize)
    : width_(w), height_(h), depth_(d), cellSize_(cellSize),
      offset_(0, 0, 0), rotation_(0.0f)
{
    if (w <= 0 || h <= 0 || d <= 0) {
        throw std::invalid_argument("VoxelGrid dimensions must be positive");
    }
    if (cellSize <= 0.0f) {
        throw std::invalid_argument("VoxelGrid cell size must be positive");
    }

    // Allocate dense array, initialized to air (0)
    size_t totalSize = static_cast<size_t>(w) * h * d;
    data_.resize(totalSize, 0);
}

// =============================================================================
// Per-voxel access
// =============================================================================

bool VoxelGrid::isValid(int x, int y, int z) const {
    return x >= 0 && x < width_ &&
           y >= 0 && y < height_ &&
           z >= 0 && z < depth_;
}

uint8_t VoxelGrid::get(int x, int y, int z) const {
    if (!isValid(x, y, z)) {
        return 0;  // Out of bounds returns air
    }
    return data_[index(x, y, z)];
}

void VoxelGrid::set(int x, int y, int z, uint8_t material) {
    if (!isValid(x, y, z)) {
        return;  // Out of bounds is no-op
    }
    data_[index(x, y, z)] = material;
    meshDirty_ = true;
}

// =============================================================================
// Material palette
// =============================================================================

uint8_t VoxelGrid::addMaterial(const VoxelMaterial& mat) {
    if (materials_.size() >= 255) {
        throw std::runtime_error("Material palette full (max 255 materials)");
    }
    materials_.push_back(mat);
    return static_cast<uint8_t>(materials_.size());  // 1-indexed
}

uint8_t VoxelGrid::addMaterial(const std::string& name, sf::Color color,
                               int spriteIndex, bool transparent, float pathCost) {
    return addMaterial(VoxelMaterial(name, color, spriteIndex, transparent, pathCost));
}

const VoxelMaterial& VoxelGrid::getMaterial(uint8_t id) const {
    if (id == 0 || id > materials_.size()) {
        return airMaterial;
    }
    return materials_[id - 1];  // 1-indexed, so ID 1 = materials_[0]
}

// =============================================================================
// Bulk operations
// =============================================================================

void VoxelGrid::fill(uint8_t material) {
    std::fill(data_.begin(), data_.end(), material);
    meshDirty_ = true;
}

// =============================================================================
// Transform
// =============================================================================

mat4 VoxelGrid::getModelMatrix() const {
    // Apply translation first, then rotation around Y axis
    mat4 translation = mat4::translate(offset_);
    mat4 rotation = mat4::rotateY(rotation_ * DEG_TO_RAD);
    return translation * rotation;
}

// =============================================================================
// Statistics
// =============================================================================

size_t VoxelGrid::countNonAir() const {
    size_t count = 0;
    for (uint8_t v : data_) {
        if (v != 0) {
            count++;
        }
    }
    return count;
}

size_t VoxelGrid::countMaterial(uint8_t material) const {
    size_t count = 0;
    for (uint8_t v : data_) {
        if (v == material) {
            count++;
        }
    }
    return count;
}

// =============================================================================
// fillBox (Milestone 10)
// =============================================================================

void VoxelGrid::fillBox(int x0, int y0, int z0, int x1, int y1, int z1, uint8_t material) {
    // Ensure proper ordering (min to max)
    if (x0 > x1) std::swap(x0, x1);
    if (y0 > y1) std::swap(y0, y1);
    if (z0 > z1) std::swap(z0, z1);

    // Clamp to valid range
    x0 = std::max(0, std::min(x0, width_ - 1));
    x1 = std::max(0, std::min(x1, width_ - 1));
    y0 = std::max(0, std::min(y0, height_ - 1));
    y1 = std::max(0, std::min(y1, height_ - 1));
    z0 = std::max(0, std::min(z0, depth_ - 1));
    z1 = std::max(0, std::min(z1, depth_ - 1));

    for (int z = z0; z <= z1; z++) {
        for (int y = y0; y <= y1; y++) {
            for (int x = x0; x <= x1; x++) {
                data_[index(x, y, z)] = material;
            }
        }
    }
    meshDirty_ = true;
}

// =============================================================================
// Mesh Caching (Milestone 10)
// =============================================================================

const std::vector<MeshVertex>& VoxelGrid::getVertices() const {
    if (meshDirty_) {
        rebuildMesh();
    }
    return cachedVertices_;
}

void VoxelGrid::rebuildMesh() const {
    cachedVertices_.clear();
    VoxelMesher::generateMesh(*this, cachedVertices_);
    meshDirty_ = false;
}

} // namespace mcrf
