// MeshLayer.h - Static 3D geometry layer for Viewport3D
// Supports terrain generation from HeightMap and height-based texture mapping

#pragma once

#include "Common.h"
#include "Math3D.h"
#include <memory>
#include <string>
#include <vector>
#include <libtcod.h>  // For TCOD_heightmap_t

// Forward declarations
namespace mcrf {
class Viewport3D;
class Model3D;
}

namespace mcrf {

// =============================================================================
// MeshVertex - Vertex format matching Viewport3D's shader attributes
// =============================================================================

struct MeshVertex {
    vec3 position;   // 12 bytes
    vec2 texcoord;   // 8 bytes
    vec3 normal;     // 12 bytes
    vec4 color;      // 16 bytes (RGBA as floats 0-1)
    // Total: 48 bytes per vertex

    MeshVertex()
        : position(0, 0, 0)
        , texcoord(0, 0)
        , normal(0, 1, 0)
        , color(1, 1, 1, 1)
    {}

    MeshVertex(const vec3& pos, const vec2& uv, const vec3& norm, const vec4& col)
        : position(pos), texcoord(uv), normal(norm), color(col)
    {}
};

// =============================================================================
// TextureRange - Height-based texture selection from sprite sheet
// =============================================================================

struct TextureRange {
    float minHeight;        // Minimum normalized height (0-1)
    float maxHeight;        // Maximum normalized height (0-1)
    int spriteIndex;        // Index into sprite sheet

    TextureRange() : minHeight(0), maxHeight(1), spriteIndex(0) {}
    TextureRange(float min, float max, int index)
        : minHeight(min), maxHeight(max), spriteIndex(index) {}
};

// =============================================================================
// MeshInstance - Instance of a Model3D placed in the world
// =============================================================================

struct MeshInstance {
    std::shared_ptr<Model3D> model;       // The model to render
    vec3 position;                         // World position
    float rotation = 0.0f;                 // Y-axis rotation in degrees
    vec3 scale = vec3(1.0f, 1.0f, 1.0f);  // Scale factors

    MeshInstance()
        : model(nullptr), position(0, 0, 0), rotation(0.0f), scale(1.0f, 1.0f, 1.0f)
    {}

    MeshInstance(std::shared_ptr<Model3D> m, const vec3& pos, float rot = 0.0f, const vec3& s = vec3(1, 1, 1))
        : model(m), position(pos), rotation(rot), scale(s)
    {}
};

// =============================================================================
// MeshLayer - Container for static 3D geometry
// =============================================================================

class MeshLayer {
public:
    MeshLayer();
    MeshLayer(const std::string& name, int zIndex = 0);
    ~MeshLayer();

    // No copy, allow move
    MeshLayer(const MeshLayer&) = delete;
    MeshLayer& operator=(const MeshLayer&) = delete;
    MeshLayer(MeshLayer&& other) noexcept;
    MeshLayer& operator=(MeshLayer&& other) noexcept;

    // =========================================================================
    // Core Properties
    // =========================================================================

    const std::string& getName() const { return name_; }
    void setName(const std::string& name) { name_ = name; }

    int getZIndex() const { return zIndex_; }
    void setZIndex(int z) { zIndex_ = z; }

    bool isVisible() const { return visible_; }
    void setVisible(bool v) { visible_ = v; }

    // Texture (sprite sheet for height-based mapping)
    void setTexture(sf::Texture* tex) { texture_ = tex; }
    sf::Texture* getTexture() const { return texture_; }

    // Sprite sheet configuration (for texture ranges)
    void setSpriteSheetLayout(int tilesPerRow, int tilesPerCol);

    // =========================================================================
    // Mesh Generation
    // =========================================================================

    /// Build terrain mesh from HeightMap
    /// @param heightmap libtcod heightmap pointer
    /// @param yScale Vertical exaggeration factor
    /// @param cellSize World-space size of each grid cell
    void buildFromHeightmap(TCOD_heightmap_t* heightmap, float yScale, float cellSize);

    /// Build a flat plane (for floors, water, etc.)
    /// @param width World-space width (X axis)
    /// @param depth World-space depth (Z axis)
    /// @param y World-space height
    void buildPlane(float width, float depth, float y = 0.0f);

    /// Apply height-based texture ranges
    /// Updates vertex UVs based on stored height data
    void applyTextureRanges(const std::vector<TextureRange>& ranges);

    /// Apply per-vertex colors from RGB heightmaps
    /// Each heightmap provides one color channel (values 0-1 map to intensity)
    /// @param rMap Red channel heightmap (must match terrain dimensions)
    /// @param gMap Green channel heightmap
    /// @param bMap Blue channel heightmap
    void applyColorMap(TCOD_heightmap_t* rMap, TCOD_heightmap_t* gMap, TCOD_heightmap_t* bMap);

    /// Clear all geometry
    void clear();

    // =========================================================================
    // Mesh Instances (Model3D placement)
    // =========================================================================

    /// Add a Model3D instance at a world position
    /// @param model The Model3D to render
    /// @param pos World position
    /// @param rotation Y-axis rotation in degrees
    /// @param scale Scale factor (uniform or per-axis)
    /// @return Instance index for later removal
    size_t addMesh(std::shared_ptr<Model3D> model, const vec3& pos,
                   float rotation = 0.0f, const vec3& scale = vec3(1, 1, 1));

    /// Remove a mesh instance by index
    /// @param index Index returned by addMesh()
    void removeMesh(size_t index);

    /// Clear all mesh instances
    void clearMeshes();

    /// Get number of mesh instances
    size_t getMeshInstanceCount() const { return meshInstances_.size(); }

    /// Get mesh instance by index (for Python access)
    MeshInstance* getMeshInstance(size_t index);
    const MeshInstance* getMeshInstance(size_t index) const;

    // =========================================================================
    // Collision Helpers
    // =========================================================================

    /// Set parent viewport (for collision marking)
    void setViewport(Viewport3D* vp) { viewport_ = vp; }
    Viewport3D* getViewport() const { return viewport_; }

    /// Mark grid cells as blocking for pathfinding/FOV
    /// @param gridX Grid X coordinate (top-left of footprint)
    /// @param gridZ Grid Z coordinate (top-left of footprint)
    /// @param footprintW Footprint width in cells
    /// @param footprintD Footprint depth in cells
    /// @param walkable Set cells walkable state
    /// @param transparent Set cells transparent state
    void placeBlocking(int gridX, int gridZ, int footprintW, int footprintD,
                       bool walkable = false, bool transparent = false);

    /// Auto-detect footprint from model bounds and place blocking
    /// @param model The model to compute footprint from
    /// @param worldPos World position of the model
    /// @param rotation Y-axis rotation of the model
    /// @param walkable Set cells walkable state
    /// @param transparent Set cells transparent state
    void placeBlockingAuto(std::shared_ptr<Model3D> model, const vec3& worldPos,
                           float rotation, bool walkable = false, bool transparent = false);

    // =========================================================================
    // GPU Upload and Rendering
    // =========================================================================

    /// Upload vertex data to GPU
    /// Call after modifying vertices or when dirty_ flag is set
    void uploadToGPU();

    /// Render this layer
    /// @param shader Shader program handle (for mesh instances)
    /// @param model Model transformation matrix
    /// @param view View matrix from camera
    /// @param projection Projection matrix from camera
    void render(unsigned int shader, const mat4& model, const mat4& view, const mat4& projection);

    /// Get model matrix (identity by default, override for positioned layers)
    mat4 getModelMatrix() const { return modelMatrix_; }
    void setModelMatrix(const mat4& m) { modelMatrix_ = m; }

    // =========================================================================
    // Statistics
    // =========================================================================

    size_t getVertexCount() const { return vertices_.size(); }
    bool isDirty() const { return dirty_; }

private:
    // Identity
    std::string name_;
    int zIndex_ = 0;
    bool visible_ = true;

    // Geometry data (CPU side)
    std::vector<MeshVertex> vertices_;
    std::vector<float> heightData_;  // Original heights for texture range re-application
    int heightmapWidth_ = 0;
    int heightmapHeight_ = 0;

    // GPU resources
    unsigned int vbo_ = 0;
    bool dirty_ = false;  // Needs GPU re-upload

    // Texture
    sf::Texture* texture_ = nullptr;  // Not owned
    int tilesPerRow_ = 1;
    int tilesPerCol_ = 1;

    // Transform
    mat4 modelMatrix_ = mat4::identity();

    // Mesh instances (Model3D placements)
    std::vector<MeshInstance> meshInstances_;

    // Parent viewport for collision helpers
    Viewport3D* viewport_ = nullptr;

    // Helper methods
    void cleanupGPU();
    vec3 computeFaceNormal(const vec3& v0, const vec3& v1, const vec3& v2);
    void computeVertexNormals();

    // Render mesh instances
    void renderMeshInstances(unsigned int shader, const mat4& view, const mat4& projection);
};

} // namespace mcrf
