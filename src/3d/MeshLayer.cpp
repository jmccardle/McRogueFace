// MeshLayer.cpp - Static 3D geometry layer implementation

#include "MeshLayer.h"
#include "Shader3D.h"
#include "../platform/GLContext.h"

// GL headers based on backend
#if defined(MCRF_SDL2)
    #ifdef __EMSCRIPTEN__
        #include <GLES2/gl2.h>
    #else
        #include <GL/gl.h>
        #include <GL/glext.h>
    #endif
    #define MCRF_HAS_GL 1
#elif !defined(MCRF_HEADLESS)
    #include <glad/glad.h>
    #define MCRF_HAS_GL 1
#endif

namespace mcrf {

// =============================================================================
// Constructor / Destructor
// =============================================================================

MeshLayer::MeshLayer()
    : name_("unnamed")
    , zIndex_(0)
    , visible_(true)
{}

MeshLayer::MeshLayer(const std::string& name, int zIndex)
    : name_(name)
    , zIndex_(zIndex)
    , visible_(true)
{}

MeshLayer::~MeshLayer() {
    cleanupGPU();
}

MeshLayer::MeshLayer(MeshLayer&& other) noexcept
    : name_(std::move(other.name_))
    , zIndex_(other.zIndex_)
    , visible_(other.visible_)
    , vertices_(std::move(other.vertices_))
    , heightData_(std::move(other.heightData_))
    , heightmapWidth_(other.heightmapWidth_)
    , heightmapHeight_(other.heightmapHeight_)
    , vbo_(other.vbo_)
    , dirty_(other.dirty_)
    , texture_(other.texture_)
    , tilesPerRow_(other.tilesPerRow_)
    , tilesPerCol_(other.tilesPerCol_)
    , modelMatrix_(other.modelMatrix_)
{
    other.vbo_ = 0;  // Prevent cleanup in moved-from object
}

MeshLayer& MeshLayer::operator=(MeshLayer&& other) noexcept {
    if (this != &other) {
        cleanupGPU();

        name_ = std::move(other.name_);
        zIndex_ = other.zIndex_;
        visible_ = other.visible_;
        vertices_ = std::move(other.vertices_);
        heightData_ = std::move(other.heightData_);
        heightmapWidth_ = other.heightmapWidth_;
        heightmapHeight_ = other.heightmapHeight_;
        vbo_ = other.vbo_;
        dirty_ = other.dirty_;
        texture_ = other.texture_;
        tilesPerRow_ = other.tilesPerRow_;
        tilesPerCol_ = other.tilesPerCol_;
        modelMatrix_ = other.modelMatrix_;

        other.vbo_ = 0;
    }
    return *this;
}

// =============================================================================
// Configuration
// =============================================================================

void MeshLayer::setSpriteSheetLayout(int tilesPerRow, int tilesPerCol) {
    tilesPerRow_ = tilesPerRow > 0 ? tilesPerRow : 1;
    tilesPerCol_ = tilesPerCol > 0 ? tilesPerCol : 1;
}

// =============================================================================
// Mesh Generation - HeightMap
// =============================================================================

void MeshLayer::buildFromHeightmap(TCOD_heightmap_t* heightmap, float yScale, float cellSize) {
    if (!heightmap || heightmap->w < 2 || heightmap->h < 2) {
        return;
    }

    int w = heightmap->w;
    int h = heightmap->h;

    // Store heightmap dimensions and data for later texture range application
    heightmapWidth_ = w;
    heightmapHeight_ = h;
    heightData_.resize(w * h);
    for (int i = 0; i < w * h; i++) {
        heightData_[i] = heightmap->values[i];
    }

    // Calculate grid vertices
    // For an NxM heightmap, we create (N-1)×(M-1) quads = 2×(N-1)×(M-1) triangles
    int numQuadsX = w - 1;
    int numQuadsZ = h - 1;
    int numTriangles = numQuadsX * numQuadsZ * 2;
    int numVertices = numTriangles * 3;

    vertices_.clear();
    vertices_.reserve(numVertices);

    // Generate triangles for each quad
    for (int z = 0; z < numQuadsZ; z++) {
        for (int x = 0; x < numQuadsX; x++) {
            // Get heights at quad corners (in heightmap, z is row index, x is column)
            float h00 = heightmap->values[z * w + x] * yScale;
            float h10 = heightmap->values[z * w + (x + 1)] * yScale;
            float h01 = heightmap->values[(z + 1) * w + x] * yScale;
            float h11 = heightmap->values[(z + 1) * w + (x + 1)] * yScale;

            // World positions
            vec3 p00(x * cellSize, h00, z * cellSize);
            vec3 p10((x + 1) * cellSize, h10, z * cellSize);
            vec3 p01(x * cellSize, h01, (z + 1) * cellSize);
            vec3 p11((x + 1) * cellSize, h11, (z + 1) * cellSize);

            // UVs (tiled across terrain, will be adjusted by applyTextureRanges)
            vec2 uv00(static_cast<float>(x), static_cast<float>(z));
            vec2 uv10(static_cast<float>(x + 1), static_cast<float>(z));
            vec2 uv01(static_cast<float>(x), static_cast<float>(z + 1));
            vec2 uv11(static_cast<float>(x + 1), static_cast<float>(z + 1));

            // Default color (white, will be modulated by texture)
            vec4 color(1.0f, 1.0f, 1.0f, 1.0f);

            // Triangle 1: p00 -> p01 -> p10 (counter-clockwise from above)
            // This ensures the normal points UP (+Y) for proper backface culling
            vec3 n1 = computeFaceNormal(p00, p01, p10);
            vertices_.emplace_back(p00, uv00, n1, color);
            vertices_.emplace_back(p01, uv01, n1, color);
            vertices_.emplace_back(p10, uv10, n1, color);

            // Triangle 2: p10 -> p01 -> p11 (counter-clockwise from above)
            vec3 n2 = computeFaceNormal(p10, p01, p11);
            vertices_.emplace_back(p10, uv10, n2, color);
            vertices_.emplace_back(p01, uv01, n2, color);
            vertices_.emplace_back(p11, uv11, n2, color);
        }
    }

    // Compute smooth vertex normals (average adjacent face normals)
    computeVertexNormals();

    dirty_ = true;
}

// =============================================================================
// Mesh Generation - Plane
// =============================================================================

void MeshLayer::buildPlane(float width, float depth, float y) {
    vertices_.clear();
    vertices_.reserve(6);  // 2 triangles

    // Clear height data (plane has no height variation)
    heightData_.clear();
    heightmapWidth_ = 0;
    heightmapHeight_ = 0;

    float halfW = width * 0.5f;
    float halfD = depth * 0.5f;

    vec3 p00(-halfW, y, -halfD);
    vec3 p10(halfW, y, -halfD);
    vec3 p01(-halfW, y, halfD);
    vec3 p11(halfW, y, halfD);

    vec3 normal(0, 1, 0);  // Facing up
    vec4 color(1, 1, 1, 1);

    // Triangle 1
    vertices_.emplace_back(p00, vec2(0, 0), normal, color);
    vertices_.emplace_back(p10, vec2(1, 0), normal, color);
    vertices_.emplace_back(p01, vec2(0, 1), normal, color);

    // Triangle 2
    vertices_.emplace_back(p10, vec2(1, 0), normal, color);
    vertices_.emplace_back(p11, vec2(1, 1), normal, color);
    vertices_.emplace_back(p01, vec2(0, 1), normal, color);

    dirty_ = true;
}

// =============================================================================
// Texture Ranges
// =============================================================================

void MeshLayer::applyTextureRanges(const std::vector<TextureRange>& ranges) {
    if (ranges.empty() || heightData_.empty() || vertices_.empty()) {
        return;
    }

    // Calculate tile UV size
    float tileU = 1.0f / tilesPerRow_;
    float tileV = 1.0f / tilesPerCol_;

    // For each vertex, find its height and apply the appropriate texture
    // Vertices are stored as triangles, 6 per quad (2 triangles × 3 vertices)
    int numQuadsX = heightmapWidth_ - 1;
    int numQuadsZ = heightmapHeight_ - 1;

    for (int z = 0; z < numQuadsZ; z++) {
        for (int x = 0; x < numQuadsX; x++) {
            int quadIndex = z * numQuadsX + x;
            int baseVertex = quadIndex * 6;

            // Get heights at quad corners (normalized 0-1)
            float h00 = heightData_[z * heightmapWidth_ + x];
            float h10 = heightData_[z * heightmapWidth_ + (x + 1)];
            float h01 = heightData_[(z + 1) * heightmapWidth_ + x];
            float h11 = heightData_[(z + 1) * heightmapWidth_ + (x + 1)];

            // Use average height to select texture
            float avgHeight = (h00 + h10 + h01 + h11) * 0.25f;

            // Find matching range
            int spriteIndex = 0;
            for (const auto& range : ranges) {
                if (avgHeight >= range.minHeight && avgHeight <= range.maxHeight) {
                    spriteIndex = range.spriteIndex;
                    break;
                }
            }

            // Calculate sprite UV offset in sprite sheet
            int tileX = spriteIndex % tilesPerRow_;
            int tileY = spriteIndex / tilesPerRow_;
            float uOffset = tileX * tileU;
            float vOffset = tileY * tileV;

            // Update UVs for all 6 vertices of this quad
            // Triangle 1: p00, p10, p01
            if (baseVertex + 5 < static_cast<int>(vertices_.size())) {
                // Local UV within quad (0-1) scaled to tile size and offset
                vertices_[baseVertex + 0].texcoord = vec2(uOffset, vOffset);
                vertices_[baseVertex + 1].texcoord = vec2(uOffset + tileU, vOffset);
                vertices_[baseVertex + 2].texcoord = vec2(uOffset, vOffset + tileV);

                // Triangle 2: p10, p11, p01
                vertices_[baseVertex + 3].texcoord = vec2(uOffset + tileU, vOffset);
                vertices_[baseVertex + 4].texcoord = vec2(uOffset + tileU, vOffset + tileV);
                vertices_[baseVertex + 5].texcoord = vec2(uOffset, vOffset + tileV);
            }
        }
    }

    dirty_ = true;
}

// =============================================================================
// Color Map
// =============================================================================

void MeshLayer::applyColorMap(TCOD_heightmap_t* rMap, TCOD_heightmap_t* gMap, TCOD_heightmap_t* bMap) {
    if (!rMap || !gMap || !bMap) {
        return;
    }

    if (vertices_.empty() || heightmapWidth_ < 2 || heightmapHeight_ < 2) {
        return;
    }

    // Verify color maps match terrain dimensions
    if (rMap->w != heightmapWidth_ || rMap->h != heightmapHeight_ ||
        gMap->w != heightmapWidth_ || gMap->h != heightmapHeight_ ||
        bMap->w != heightmapWidth_ || bMap->h != heightmapHeight_) {
        return;  // Dimension mismatch
    }

    int numQuadsX = heightmapWidth_ - 1;
    int numQuadsZ = heightmapHeight_ - 1;

    for (int z = 0; z < numQuadsZ; z++) {
        for (int x = 0; x < numQuadsX; x++) {
            int quadIndex = z * numQuadsX + x;
            int baseVertex = quadIndex * 6;

            if (baseVertex + 5 >= static_cast<int>(vertices_.size())) {
                continue;
            }

            // Sample RGB at each corner of the quad
            // Corner indices in heightmap
            int idx00 = z * heightmapWidth_ + x;
            int idx10 = z * heightmapWidth_ + (x + 1);
            int idx01 = (z + 1) * heightmapWidth_ + x;
            int idx11 = (z + 1) * heightmapWidth_ + (x + 1);

            // Build colors for each corner (clamped to 0-1)
            auto clamp01 = [](float v) { return v < 0.0f ? 0.0f : (v > 1.0f ? 1.0f : v); };

            vec4 c00(clamp01(rMap->values[idx00]), clamp01(gMap->values[idx00]), clamp01(bMap->values[idx00]), 1.0f);
            vec4 c10(clamp01(rMap->values[idx10]), clamp01(gMap->values[idx10]), clamp01(bMap->values[idx10]), 1.0f);
            vec4 c01(clamp01(rMap->values[idx01]), clamp01(gMap->values[idx01]), clamp01(bMap->values[idx01]), 1.0f);
            vec4 c11(clamp01(rMap->values[idx11]), clamp01(gMap->values[idx11]), clamp01(bMap->values[idx11]), 1.0f);

            // Triangle 1: p00, p01, p10 (vertices 0, 1, 2)
            vertices_[baseVertex + 0].color = c00;
            vertices_[baseVertex + 1].color = c01;
            vertices_[baseVertex + 2].color = c10;

            // Triangle 2: p10, p01, p11 (vertices 3, 4, 5)
            vertices_[baseVertex + 3].color = c10;
            vertices_[baseVertex + 4].color = c01;
            vertices_[baseVertex + 5].color = c11;
        }
    }

    dirty_ = true;
}

// =============================================================================
// Clear
// =============================================================================

void MeshLayer::clear() {
    vertices_.clear();
    heightData_.clear();
    heightmapWidth_ = 0;
    heightmapHeight_ = 0;
    dirty_ = true;
}

// =============================================================================
// GPU Upload
// =============================================================================

void MeshLayer::uploadToGPU() {
#ifdef MCRF_HAS_GL
    if (!gl::isGLReady()) {
        return;
    }

    // Create VBO if needed
    if (vbo_ == 0) {
        glGenBuffers(1, &vbo_);
    }

    // Upload vertex data
    glBindBuffer(GL_ARRAY_BUFFER, vbo_);
    if (!vertices_.empty()) {
        glBufferData(GL_ARRAY_BUFFER,
                     vertices_.size() * sizeof(MeshVertex),
                     vertices_.data(),
                     GL_STATIC_DRAW);
    } else {
        glBufferData(GL_ARRAY_BUFFER, 0, nullptr, GL_STATIC_DRAW);
    }
    glBindBuffer(GL_ARRAY_BUFFER, 0);

    dirty_ = false;
#endif
}

// =============================================================================
// Rendering
// =============================================================================

void MeshLayer::render(const mat4& model, const mat4& view, const mat4& projection) {
#ifdef MCRF_HAS_GL
    if (!gl::isGLReady() || vertices_.empty()) {
        return;
    }

    // Upload to GPU if needed
    if (dirty_ || vbo_ == 0) {
        uploadToGPU();
    }

    if (vbo_ == 0) {
        return;
    }

    // Bind VBO
    glBindBuffer(GL_ARRAY_BUFFER, vbo_);

    // Vertex format: pos(3) + texcoord(2) + normal(3) + color(4) = 12 floats = 48 bytes
    int stride = sizeof(MeshVertex);

    // Set up vertex attributes
    glEnableVertexAttribArray(Shader3D::ATTRIB_POSITION);
    glVertexAttribPointer(Shader3D::ATTRIB_POSITION, 3, GL_FLOAT, GL_FALSE,
                          stride, reinterpret_cast<void*>(offsetof(MeshVertex, position)));

    glEnableVertexAttribArray(Shader3D::ATTRIB_TEXCOORD);
    glVertexAttribPointer(Shader3D::ATTRIB_TEXCOORD, 2, GL_FLOAT, GL_FALSE,
                          stride, reinterpret_cast<void*>(offsetof(MeshVertex, texcoord)));

    glEnableVertexAttribArray(Shader3D::ATTRIB_NORMAL);
    glVertexAttribPointer(Shader3D::ATTRIB_NORMAL, 3, GL_FLOAT, GL_FALSE,
                          stride, reinterpret_cast<void*>(offsetof(MeshVertex, normal)));

    glEnableVertexAttribArray(Shader3D::ATTRIB_COLOR);
    glVertexAttribPointer(Shader3D::ATTRIB_COLOR, 4, GL_FLOAT, GL_FALSE,
                          stride, reinterpret_cast<void*>(offsetof(MeshVertex, color)));

    // Draw triangles
    glDrawArrays(GL_TRIANGLES, 0, static_cast<int>(vertices_.size()));

    // Cleanup
    glDisableVertexAttribArray(Shader3D::ATTRIB_POSITION);
    glDisableVertexAttribArray(Shader3D::ATTRIB_TEXCOORD);
    glDisableVertexAttribArray(Shader3D::ATTRIB_NORMAL);
    glDisableVertexAttribArray(Shader3D::ATTRIB_COLOR);
    glBindBuffer(GL_ARRAY_BUFFER, 0);
#endif
}

// =============================================================================
// Private Helpers
// =============================================================================

void MeshLayer::cleanupGPU() {
#ifdef MCRF_HAS_GL
    if (vbo_ != 0 && gl::isGLReady()) {
        glDeleteBuffers(1, &vbo_);
        vbo_ = 0;
    }
#endif
}

vec3 MeshLayer::computeFaceNormal(const vec3& v0, const vec3& v1, const vec3& v2) {
    vec3 edge1 = v1 - v0;
    vec3 edge2 = v2 - v0;
    return edge1.cross(edge2).normalized();
}

void MeshLayer::computeVertexNormals() {
    // For terrain mesh, we can average normals at shared positions
    // This is a simplified approach - works well for regular grids

    if (vertices_.empty() || heightmapWidth_ < 2 || heightmapHeight_ < 2) {
        return;
    }

    // Create a grid of accumulated normals for each heightmap point
    std::vector<vec3> accumulatedNormals(heightmapWidth_ * heightmapHeight_, vec3(0, 0, 0));
    std::vector<int> normalCounts(heightmapWidth_ * heightmapHeight_, 0);

    // Each quad contributes to its 4 corners
    int numQuadsX = heightmapWidth_ - 1;
    int numQuadsZ = heightmapHeight_ - 1;

    for (int z = 0; z < numQuadsZ; z++) {
        for (int x = 0; x < numQuadsX; x++) {
            int quadIndex = z * numQuadsX + x;
            int baseVertex = quadIndex * 6;

            // Get face normals from the two triangles
            if (baseVertex + 5 < static_cast<int>(vertices_.size())) {
                vec3 n1 = vertices_[baseVertex].normal;
                vec3 n2 = vertices_[baseVertex + 3].normal;

                // Corners: (x,z), (x+1,z), (x,z+1), (x+1,z+1)
                int idx00 = z * heightmapWidth_ + x;
                int idx10 = z * heightmapWidth_ + (x + 1);
                int idx01 = (z + 1) * heightmapWidth_ + x;
                int idx11 = (z + 1) * heightmapWidth_ + (x + 1);

                // Triangle 1 (p00, p01, p10) contributes n1 to those corners
                accumulatedNormals[idx00] += n1;
                normalCounts[idx00]++;
                accumulatedNormals[idx01] += n1;
                normalCounts[idx01]++;
                accumulatedNormals[idx10] += n1;
                normalCounts[idx10]++;

                // Triangle 2 (p10, p01, p11) contributes n2 to those corners
                accumulatedNormals[idx10] += n2;
                normalCounts[idx10]++;
                accumulatedNormals[idx01] += n2;
                normalCounts[idx01]++;
                accumulatedNormals[idx11] += n2;
                normalCounts[idx11]++;
            }
        }
    }

    // Normalize accumulated normals
    for (size_t i = 0; i < accumulatedNormals.size(); i++) {
        if (normalCounts[i] > 0) {
            accumulatedNormals[i] = accumulatedNormals[i].normalized();
        } else {
            accumulatedNormals[i] = vec3(0, 1, 0);  // Default up
        }
    }

    // Apply averaged normals back to vertices
    for (int z = 0; z < numQuadsZ; z++) {
        for (int x = 0; x < numQuadsX; x++) {
            int quadIndex = z * numQuadsX + x;
            int baseVertex = quadIndex * 6;

            int idx00 = z * heightmapWidth_ + x;
            int idx10 = z * heightmapWidth_ + (x + 1);
            int idx01 = (z + 1) * heightmapWidth_ + x;
            int idx11 = (z + 1) * heightmapWidth_ + (x + 1);

            if (baseVertex + 5 < static_cast<int>(vertices_.size())) {
                // Triangle 1: p00, p01, p10
                vertices_[baseVertex + 0].normal = accumulatedNormals[idx00];
                vertices_[baseVertex + 1].normal = accumulatedNormals[idx01];
                vertices_[baseVertex + 2].normal = accumulatedNormals[idx10];

                // Triangle 2: p10, p01, p11
                vertices_[baseVertex + 3].normal = accumulatedNormals[idx10];
                vertices_[baseVertex + 4].normal = accumulatedNormals[idx01];
                vertices_[baseVertex + 5].normal = accumulatedNormals[idx11];
            }
        }
    }
}

} // namespace mcrf
