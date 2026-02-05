// VoxelGrid.cpp - Dense 3D voxel array implementation
// Part of McRogueFace 3D Extension - Milestones 9-11

#include "VoxelGrid.h"
#include "VoxelMesher.h"
#include "MeshLayer.h"  // For MeshVertex
#include <cmath>
#include <algorithm>
#include <cstring>   // For memcpy, memcmp
#include <fstream>   // For file I/O

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
// Bulk Operations - Milestone 11
// =============================================================================

void VoxelGrid::fillBoxHollow(int x0, int y0, int z0, int x1, int y1, int z1,
                               uint8_t material, int thickness) {
    // Ensure proper ordering (min to max)
    if (x0 > x1) std::swap(x0, x1);
    if (y0 > y1) std::swap(y0, y1);
    if (z0 > z1) std::swap(z0, z1);

    // Fill entire box with material
    fillBox(x0, y0, z0, x1, y1, z1, material);

    // Carve out interior (inset by thickness on all sides)
    int ix0 = x0 + thickness;
    int iy0 = y0 + thickness;
    int iz0 = z0 + thickness;
    int ix1 = x1 - thickness;
    int iy1 = y1 - thickness;
    int iz1 = z1 - thickness;

    // Only carve if there's interior space
    if (ix0 <= ix1 && iy0 <= iy1 && iz0 <= iz1) {
        fillBox(ix0, iy0, iz0, ix1, iy1, iz1, 0);  // Air
    }
    // meshDirty_ already set by fillBox calls
}

void VoxelGrid::fillSphere(int cx, int cy, int cz, int radius, uint8_t material) {
    int r2 = radius * radius;

    for (int z = cz - radius; z <= cz + radius; z++) {
        for (int y = cy - radius; y <= cy + radius; y++) {
            for (int x = cx - radius; x <= cx + radius; x++) {
                int dx = x - cx;
                int dy = y - cy;
                int dz = z - cz;
                if (dx * dx + dy * dy + dz * dz <= r2) {
                    if (isValid(x, y, z)) {
                        data_[index(x, y, z)] = material;
                    }
                }
            }
        }
    }
    meshDirty_ = true;
}

void VoxelGrid::fillCylinder(int cx, int cy, int cz, int radius, int height, uint8_t material) {
    int r2 = radius * radius;

    for (int y = cy; y < cy + height; y++) {
        for (int z = cz - radius; z <= cz + radius; z++) {
            for (int x = cx - radius; x <= cx + radius; x++) {
                int dx = x - cx;
                int dz = z - cz;
                if (dx * dx + dz * dz <= r2) {
                    if (isValid(x, y, z)) {
                        data_[index(x, y, z)] = material;
                    }
                }
            }
        }
    }
    meshDirty_ = true;
}

// Simple 3D noise implementation (hash-based, similar to value noise)
namespace {
    // Simple hash function for noise
    inline unsigned int hash3D(int x, int y, int z, unsigned int seed) {
        unsigned int h = seed;
        h ^= static_cast<unsigned int>(x) * 374761393u;
        h ^= static_cast<unsigned int>(y) * 668265263u;
        h ^= static_cast<unsigned int>(z) * 2147483647u;
        h = (h ^ (h >> 13)) * 1274126177u;
        return h;
    }

    // Convert hash to 0-1 float
    inline float hashToFloat(unsigned int h) {
        return static_cast<float>(h & 0xFFFFFF) / static_cast<float>(0xFFFFFF);
    }

    // Linear interpolation
    inline float lerp(float a, float b, float t) {
        return a + t * (b - a);
    }

    // Smoothstep for smoother interpolation
    inline float smoothstep(float t) {
        return t * t * (3.0f - 2.0f * t);
    }

    // 3D value noise
    float noise3D(float x, float y, float z, unsigned int seed) {
        int xi = static_cast<int>(std::floor(x));
        int yi = static_cast<int>(std::floor(y));
        int zi = static_cast<int>(std::floor(z));

        float xf = x - xi;
        float yf = y - yi;
        float zf = z - zi;

        // Smoothstep the fractions
        float u = smoothstep(xf);
        float v = smoothstep(yf);
        float w = smoothstep(zf);

        // Hash corners of the unit cube
        float c000 = hashToFloat(hash3D(xi, yi, zi, seed));
        float c100 = hashToFloat(hash3D(xi + 1, yi, zi, seed));
        float c010 = hashToFloat(hash3D(xi, yi + 1, zi, seed));
        float c110 = hashToFloat(hash3D(xi + 1, yi + 1, zi, seed));
        float c001 = hashToFloat(hash3D(xi, yi, zi + 1, seed));
        float c101 = hashToFloat(hash3D(xi + 1, yi, zi + 1, seed));
        float c011 = hashToFloat(hash3D(xi, yi + 1, zi + 1, seed));
        float c111 = hashToFloat(hash3D(xi + 1, yi + 1, zi + 1, seed));

        // Trilinear interpolation
        float x00 = lerp(c000, c100, u);
        float x10 = lerp(c010, c110, u);
        float x01 = lerp(c001, c101, u);
        float x11 = lerp(c011, c111, u);

        float y0 = lerp(x00, x10, v);
        float y1 = lerp(x01, x11, v);

        return lerp(y0, y1, w);
    }
}

void VoxelGrid::fillNoise(int x0, int y0, int z0, int x1, int y1, int z1,
                           uint8_t material, float threshold, float scale, unsigned int seed) {
    // Ensure proper ordering
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
                float n = noise3D(x * scale, y * scale, z * scale, seed);
                if (n > threshold) {
                    data_[index(x, y, z)] = material;
                }
            }
        }
    }
    meshDirty_ = true;
}

// =============================================================================
// Copy/Paste Operations - Milestone 11
// =============================================================================

VoxelRegion VoxelGrid::copyRegion(int x0, int y0, int z0, int x1, int y1, int z1) const {
    // Ensure proper ordering
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

    int rw = x1 - x0 + 1;
    int rh = y1 - y0 + 1;
    int rd = z1 - z0 + 1;

    VoxelRegion region(rw, rh, rd);

    for (int rz = 0; rz < rd; rz++) {
        for (int ry = 0; ry < rh; ry++) {
            for (int rx = 0; rx < rw; rx++) {
                int sx = x0 + rx;
                int sy = y0 + ry;
                int sz = z0 + rz;
                size_t ri = static_cast<size_t>(rz) * (rw * rh) +
                            static_cast<size_t>(ry) * rw + rx;
                region.data[ri] = get(sx, sy, sz);
            }
        }
    }

    return region;
}

void VoxelGrid::pasteRegion(const VoxelRegion& region, int x, int y, int z, bool skipAir) {
    if (!region.isValid()) return;

    for (int rz = 0; rz < region.depth; rz++) {
        for (int ry = 0; ry < region.height; ry++) {
            for (int rx = 0; rx < region.width; rx++) {
                size_t ri = static_cast<size_t>(rz) * (region.width * region.height) +
                            static_cast<size_t>(ry) * region.width + rx;
                uint8_t mat = region.data[ri];

                if (skipAir && mat == 0) continue;

                int dx = x + rx;
                int dy = y + ry;
                int dz = z + rz;

                if (isValid(dx, dy, dz)) {
                    data_[index(dx, dy, dz)] = mat;
                }
            }
        }
    }
    meshDirty_ = true;
}

// =============================================================================
// Navigation Projection - Milestone 12
// =============================================================================

VoxelGrid::NavInfo VoxelGrid::projectColumn(int x, int z, int headroom) const {
    NavInfo info;
    info.height = 0.0f;
    info.walkable = false;
    info.transparent = true;
    info.pathCost = 1.0f;

    // Out of bounds check
    if (x < 0 || x >= width_ || z < 0 || z >= depth_) {
        return info;
    }

    // Scan from top to bottom, find first solid with air above (floor)
    int floorY = -1;
    for (int y = height_ - 1; y >= 0; y--) {
        uint8_t mat = get(x, y, z);
        if (mat != 0) {
            // Found solid - check if it's a floor (air above) or ceiling
            bool hasAirAbove = (y == height_ - 1) || (get(x, y + 1, z) == 0);
            if (hasAirAbove) {
                floorY = y;
                break;
            }
        }
    }

    if (floorY >= 0) {
        // Found a floor
        info.height = (floorY + 1) * cellSize_;  // Top of floor voxel
        info.walkable = true;

        // Check headroom (need enough air voxels above floor)
        int airCount = 0;
        for (int y = floorY + 1; y < height_; y++) {
            if (get(x, y, z) == 0) {
                airCount++;
            } else {
                break;
            }
        }
        if (airCount < headroom) {
            info.walkable = false;  // Can't fit entity
        }

        // Get path cost from floor material
        uint8_t floorMat = get(x, floorY, z);
        info.pathCost = getMaterial(floorMat).pathCost;
    }

    // Check transparency: any non-transparent solid in column blocks FOV
    for (int y = 0; y < height_; y++) {
        uint8_t mat = get(x, y, z);
        if (mat != 0 && !getMaterial(mat).transparent) {
            info.transparent = false;
            break;
        }
    }

    return info;
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
    if (greedyMeshing_) {
        VoxelMesher::generateGreedyMesh(*this, cachedVertices_);
    } else {
        VoxelMesher::generateMesh(*this, cachedVertices_);
    }
    meshDirty_ = false;
}

// =============================================================================
// Serialization - Milestone 14
// =============================================================================

// File format:
// Magic "MCVG" (4 bytes)
// Version (1 byte) - currently 1
// Width, Height, Depth (3 x int32 = 12 bytes)
// Cell Size (float32 = 4 bytes)
// Material count (uint8 = 1 byte)
// For each material:
//   Name length (uint16) + name bytes
//   Color RGBA (4 bytes)
//   Sprite index (int32)
//   Transparent (uint8)
//   Path cost (float32)
// Voxel data length (uint32)
// Voxel data: RLE encoded (run_length: uint8, material: uint8) pairs
//   If run_length == 255, read extended_length: uint16 for longer runs

namespace {
    const char MAGIC[4] = {'M', 'C', 'V', 'G'};
    const uint8_t FORMAT_VERSION = 1;

    // Write helpers
    void writeU8(std::vector<uint8_t>& buf, uint8_t v) {
        buf.push_back(v);
    }

    void writeU16(std::vector<uint8_t>& buf, uint16_t v) {
        buf.push_back(static_cast<uint8_t>(v & 0xFF));
        buf.push_back(static_cast<uint8_t>((v >> 8) & 0xFF));
    }

    void writeI32(std::vector<uint8_t>& buf, int32_t v) {
        buf.push_back(static_cast<uint8_t>(v & 0xFF));
        buf.push_back(static_cast<uint8_t>((v >> 8) & 0xFF));
        buf.push_back(static_cast<uint8_t>((v >> 16) & 0xFF));
        buf.push_back(static_cast<uint8_t>((v >> 24) & 0xFF));
    }

    void writeU32(std::vector<uint8_t>& buf, uint32_t v) {
        buf.push_back(static_cast<uint8_t>(v & 0xFF));
        buf.push_back(static_cast<uint8_t>((v >> 8) & 0xFF));
        buf.push_back(static_cast<uint8_t>((v >> 16) & 0xFF));
        buf.push_back(static_cast<uint8_t>((v >> 24) & 0xFF));
    }

    void writeF32(std::vector<uint8_t>& buf, float v) {
        static_assert(sizeof(float) == 4, "Expected 4-byte float");
        const uint8_t* bytes = reinterpret_cast<const uint8_t*>(&v);
        buf.insert(buf.end(), bytes, bytes + 4);
    }

    void writeString(std::vector<uint8_t>& buf, const std::string& s) {
        uint16_t len = static_cast<uint16_t>(std::min(s.size(), size_t(65535)));
        writeU16(buf, len);
        buf.insert(buf.end(), s.begin(), s.begin() + len);
    }

    // Read helpers
    class Reader {
        const uint8_t* data_;
        size_t size_;
        size_t pos_;
    public:
        Reader(const uint8_t* data, size_t size) : data_(data), size_(size), pos_(0) {}

        bool hasBytes(size_t n) const { return pos_ + n <= size_; }
        size_t position() const { return pos_; }

        bool readU8(uint8_t& v) {
            if (!hasBytes(1)) return false;
            v = data_[pos_++];
            return true;
        }

        bool readU16(uint16_t& v) {
            if (!hasBytes(2)) return false;
            v = static_cast<uint16_t>(data_[pos_]) |
                (static_cast<uint16_t>(data_[pos_ + 1]) << 8);
            pos_ += 2;
            return true;
        }

        bool readI32(int32_t& v) {
            if (!hasBytes(4)) return false;
            v = static_cast<int32_t>(data_[pos_]) |
                (static_cast<int32_t>(data_[pos_ + 1]) << 8) |
                (static_cast<int32_t>(data_[pos_ + 2]) << 16) |
                (static_cast<int32_t>(data_[pos_ + 3]) << 24);
            pos_ += 4;
            return true;
        }

        bool readU32(uint32_t& v) {
            if (!hasBytes(4)) return false;
            v = static_cast<uint32_t>(data_[pos_]) |
                (static_cast<uint32_t>(data_[pos_ + 1]) << 8) |
                (static_cast<uint32_t>(data_[pos_ + 2]) << 16) |
                (static_cast<uint32_t>(data_[pos_ + 3]) << 24);
            pos_ += 4;
            return true;
        }

        bool readF32(float& v) {
            if (!hasBytes(4)) return false;
            static_assert(sizeof(float) == 4, "Expected 4-byte float");
            std::memcpy(&v, data_ + pos_, 4);
            pos_ += 4;
            return true;
        }

        bool readString(std::string& s) {
            uint16_t len;
            if (!readU16(len)) return false;
            if (!hasBytes(len)) return false;
            s.assign(reinterpret_cast<const char*>(data_ + pos_), len);
            pos_ += len;
            return true;
        }

        bool readBytes(uint8_t* out, size_t n) {
            if (!hasBytes(n)) return false;
            std::memcpy(out, data_ + pos_, n);
            pos_ += n;
            return true;
        }
    };

    // RLE encode voxel data
    void rleEncode(const std::vector<uint8_t>& data, std::vector<uint8_t>& out) {
        if (data.empty()) return;

        size_t i = 0;
        while (i < data.size()) {
            uint8_t mat = data[i];
            size_t runStart = i;

            // Count consecutive same materials
            while (i < data.size() && data[i] == mat && (i - runStart) < 65535 + 255) {
                i++;
            }

            size_t runLen = i - runStart;

            if (runLen < 255) {
                writeU8(out, static_cast<uint8_t>(runLen));
            } else {
                // Extended run: 255 marker + uint16 length
                writeU8(out, 255);
                writeU16(out, static_cast<uint16_t>(runLen - 255));
            }
            writeU8(out, mat);
        }
    }

    // RLE decode voxel data
    bool rleDecode(Reader& reader, std::vector<uint8_t>& data, size_t expectedSize) {
        data.clear();
        data.reserve(expectedSize);

        while (data.size() < expectedSize) {
            uint8_t runLen8;
            if (!reader.readU8(runLen8)) return false;

            size_t runLen = runLen8;
            if (runLen8 == 255) {
                uint16_t extLen;
                if (!reader.readU16(extLen)) return false;
                runLen = 255 + extLen;
            }

            uint8_t mat;
            if (!reader.readU8(mat)) return false;

            for (size_t j = 0; j < runLen && data.size() < expectedSize; j++) {
                data.push_back(mat);
            }
        }

        return data.size() == expectedSize;
    }
}

bool VoxelGrid::saveToBuffer(std::vector<uint8_t>& buffer) const {
    buffer.clear();
    buffer.reserve(1024 + data_.size());  // Rough estimate

    // Magic
    buffer.insert(buffer.end(), MAGIC, MAGIC + 4);

    // Version
    writeU8(buffer, FORMAT_VERSION);

    // Dimensions
    writeI32(buffer, width_);
    writeI32(buffer, height_);
    writeI32(buffer, depth_);

    // Cell size
    writeF32(buffer, cellSize_);

    // Materials
    writeU8(buffer, static_cast<uint8_t>(materials_.size()));
    for (const auto& mat : materials_) {
        writeString(buffer, mat.name);
        writeU8(buffer, mat.color.r);
        writeU8(buffer, mat.color.g);
        writeU8(buffer, mat.color.b);
        writeU8(buffer, mat.color.a);
        writeI32(buffer, mat.spriteIndex);
        writeU8(buffer, mat.transparent ? 1 : 0);
        writeF32(buffer, mat.pathCost);
    }

    // RLE encode voxel data
    std::vector<uint8_t> rleData;
    rleEncode(data_, rleData);

    // Write RLE data length and data
    writeU32(buffer, static_cast<uint32_t>(rleData.size()));
    buffer.insert(buffer.end(), rleData.begin(), rleData.end());

    return true;
}

bool VoxelGrid::loadFromBuffer(const uint8_t* data, size_t size) {
    Reader reader(data, size);

    // Check magic
    uint8_t magic[4];
    if (!reader.readBytes(magic, 4)) return false;
    if (std::memcmp(magic, MAGIC, 4) != 0) return false;

    // Check version
    uint8_t version;
    if (!reader.readU8(version)) return false;
    if (version != FORMAT_VERSION) return false;

    // Read dimensions
    int32_t w, h, d;
    if (!reader.readI32(w) || !reader.readI32(h) || !reader.readI32(d)) return false;
    if (w <= 0 || h <= 0 || d <= 0) return false;

    // Read cell size
    float cs;
    if (!reader.readF32(cs)) return false;
    if (cs <= 0.0f) return false;

    // Read materials
    uint8_t matCount;
    if (!reader.readU8(matCount)) return false;

    std::vector<VoxelMaterial> newMaterials;
    newMaterials.reserve(matCount);
    for (uint8_t i = 0; i < matCount; i++) {
        VoxelMaterial mat;
        if (!reader.readString(mat.name)) return false;

        uint8_t r, g, b, a;
        if (!reader.readU8(r) || !reader.readU8(g) || !reader.readU8(b) || !reader.readU8(a))
            return false;
        mat.color = sf::Color(r, g, b, a);

        int32_t sprite;
        if (!reader.readI32(sprite)) return false;
        mat.spriteIndex = sprite;

        uint8_t transp;
        if (!reader.readU8(transp)) return false;
        mat.transparent = (transp != 0);

        if (!reader.readF32(mat.pathCost)) return false;

        newMaterials.push_back(mat);
    }

    // Read RLE data length
    uint32_t rleLen;
    if (!reader.readU32(rleLen)) return false;

    // Decode voxel data
    size_t expectedVoxels = static_cast<size_t>(w) * h * d;
    std::vector<uint8_t> newData;
    if (!rleDecode(reader, newData, expectedVoxels)) return false;

    // Success - update the grid
    width_ = w;
    height_ = h;
    depth_ = d;
    cellSize_ = cs;
    materials_ = std::move(newMaterials);
    data_ = std::move(newData);
    meshDirty_ = true;

    return true;
}

bool VoxelGrid::save(const std::string& path) const {
    std::vector<uint8_t> buffer;
    if (!saveToBuffer(buffer)) return false;

    std::ofstream file(path, std::ios::binary);
    if (!file) return false;

    file.write(reinterpret_cast<const char*>(buffer.data()), buffer.size());
    return file.good();
}

bool VoxelGrid::load(const std::string& path) {
    std::ifstream file(path, std::ios::binary | std::ios::ate);
    if (!file) return false;

    std::streamsize size = file.tellg();
    if (size <= 0) return false;

    file.seekg(0, std::ios::beg);

    std::vector<uint8_t> buffer(static_cast<size_t>(size));
    if (!file.read(reinterpret_cast<char*>(buffer.data()), size)) return false;

    return loadFromBuffer(buffer.data(), buffer.size());
}

} // namespace mcrf
