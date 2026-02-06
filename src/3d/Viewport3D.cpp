// Viewport3D.cpp - 3D rendering viewport implementation

#include "Viewport3D.h"
#include "Shader3D.h"
#include "MeshLayer.h"
#include "Entity3D.h"
#include "EntityCollection3D.h"
#include "Billboard.h"
#include "Model3D.h"
#include "VoxelGrid.h"
#include "PyVoxelGrid.h"
#include "../platform/GLContext.h"
#include "PyVector.h"
#include "PyColor.h"
#include "PyPositionHelper.h"
#include "McRFPy_Doc.h"
#include "PythonObjectCache.h"
#include "McRFPy_API.h"
#include "PyHeightMap.h"
#include <set>
#include <cstring>
#include <cmath>
#include <algorithm>

// Include appropriate GL headers based on backend
#if defined(MCRF_SDL2)
    #ifdef __EMSCRIPTEN__
        #include <GLES2/gl2.h>
    #else
        #include <GL/gl.h>
        #include <GL/glext.h>
    #endif
    #define MCRF_HAS_GL 1
#elif !defined(MCRF_HEADLESS)
    // SFML backend - use GLAD
    #include <glad/glad.h>
    #define MCRF_HAS_GL 1
#endif

namespace mcrf {

// =============================================================================
// Construction / Destruction
// =============================================================================

Viewport3D::Viewport3D()
    : size_(320.0f, 240.0f)
    , entities_(std::make_shared<std::list<std::shared_ptr<Entity3D>>>())
    , billboards_(std::make_shared<std::vector<std::shared_ptr<Billboard>>>())
{
    position = sf::Vector2f(0, 0);
    camera_.setAspect(size_.x / size_.y);
}

Viewport3D::Viewport3D(float x, float y, float width, float height)
    : size_(width, height)
    , entities_(std::make_shared<std::list<std::shared_ptr<Entity3D>>>())
    , billboards_(std::make_shared<std::vector<std::shared_ptr<Billboard>>>())
{
    position = sf::Vector2f(x, y);
    camera_.setAspect(size_.x / size_.y);
}

Viewport3D::~Viewport3D() {
    cleanupTestGeometry();
    cleanupFBO();

    // Clean up voxel VBO (Milestone 10)
#ifdef MCRF_HAS_GL
    if (voxelVBO_ != 0) {
        glDeleteBuffers(1, &voxelVBO_);
        voxelVBO_ = 0;
    }
#endif

    if (tcodMap_) {
        delete tcodMap_;
        tcodMap_ = nullptr;
    }
}

// =============================================================================
// UIDrawable Interface
// =============================================================================

void Viewport3D::render(sf::Vector2f offset, sf::RenderTarget& target) {
    if (!visible) return;

    // Initialize resources if needed (only on GL-ready backends)
    if (gl::isGLReady()) {
        if (fbo_ == 0) {
            initFBO();
        }
        if (!shader_) {
            initShader();
        }
        if (testVBO_ == 0) {
            initTestGeometry();
        }

        // Save SFML's GL state before raw GL rendering
        // This is REQUIRED when mixing SFML 2D and raw OpenGL
#ifndef MCRF_SDL2
        target.pushGLStates();
#endif
    }

    // Render 3D content to FBO
    render3DContent();

    // Restore SFML's GL state after our GL calls
    if (gl::isGLReady()) {
#ifndef MCRF_SDL2
        target.popGLStates();
#endif
    }

    // Blit FBO to screen (using SFML's drawing, so after state restore)
    blitToScreen(offset, target);
}

PyObjectsEnum Viewport3D::derived_type() {
    return PyObjectsEnum::UIVIEWPORT3D;
}

UIDrawable* Viewport3D::click_at(sf::Vector2f point) {
    sf::FloatRect bounds = get_bounds();
    if (bounds.contains(point)) {
        return this;
    }
    return nullptr;
}

sf::FloatRect Viewport3D::get_bounds() const {
    return sf::FloatRect(position.x, position.y, size_.x, size_.y);
}

void Viewport3D::move(float dx, float dy) {
    position.x += dx;
    position.y += dy;
}

void Viewport3D::resize(float w, float h) {
    size_.x = w;
    size_.y = h;
    camera_.setAspect(size_.x / size_.y);
}

// =============================================================================
// Size and Resolution
// =============================================================================

void Viewport3D::setSize(float width, float height) {
    size_.x = width;
    size_.y = height;
    camera_.setAspect(size_.x / size_.y);
}

void Viewport3D::setInternalResolution(int width, int height) {
    if (width != internalWidth_ || height != internalHeight_) {
        internalWidth_ = width;
        internalHeight_ = height;
        cleanupFBO();  // Force recreation on next render
    }
}

// =============================================================================
// Fog Settings
// =============================================================================

void Viewport3D::setFogColor(const sf::Color& color) {
    fogColor_ = vec3(color.r / 255.0f, color.g / 255.0f, color.b / 255.0f);
}

sf::Color Viewport3D::getFogColor() const {
    return sf::Color(
        static_cast<sf::Uint8>(fogColor_.x * 255),
        static_cast<sf::Uint8>(fogColor_.y * 255),
        static_cast<sf::Uint8>(fogColor_.z * 255)
    );
}

void Viewport3D::setFogRange(float nearDist, float farDist) {
    fogNear_ = nearDist;
    fogFar_ = farDist;
}

// =============================================================================
// Camera Helpers
// =============================================================================

void Viewport3D::orbitCamera(float angle, float distance, float height) {
    float x = std::cos(angle) * distance;
    float z = std::sin(angle) * distance;
    camera_.setPosition(vec3(x, height, z));
    camera_.setTarget(vec3(0, 0, 0));
}

vec3 Viewport3D::screenToWorld(float screenX, float screenY) {
    // Convert screen coordinates to normalized device coordinates (-1 to 1)
    // screenX/Y are relative to the viewport position
    float ndcX = (2.0f * screenX / size_.x) - 1.0f;
    float ndcY = 1.0f - (2.0f * screenY / size_.y);  // Flip Y for OpenGL

    // Get inverse matrices
    mat4 proj = camera_.getProjectionMatrix();
    mat4 view = camera_.getViewMatrix();
    mat4 invProj = proj.inverse();
    mat4 invView = view.inverse();

    // Unproject near plane point to get ray direction
    vec4 rayClip(ndcX, ndcY, -1.0f, 1.0f);
    vec4 rayEye = invProj * rayClip;
    rayEye = vec4(rayEye.x, rayEye.y, -1.0f, 0.0f);  // Direction in eye space

    vec4 rayWorld4 = invView * rayEye;
    vec3 rayDir = vec3(rayWorld4.x, rayWorld4.y, rayWorld4.z).normalized();
    vec3 rayOrigin = camera_.getPosition();

    // Intersect with Y=0 plane (ground level)
    // This is a simplification - for hilly terrain, you'd want ray-marching
    if (std::abs(rayDir.y) > 0.0001f) {
        float t = -rayOrigin.y / rayDir.y;
        if (t > 0) {
            return rayOrigin + rayDir * t;
        }
    }

    // Ray parallel to ground or pointing away - return invalid position
    return vec3(-1.0f, -1.0f, -1.0f);
}

void Viewport3D::followEntity(std::shared_ptr<Entity3D> entity, float distance, float height, float smoothing) {
    if (!entity) return;

    // Get entity's world position
    vec3 entityPos = entity->getWorldPos();

    // Calculate desired camera position behind and above entity
    float entityRotation = radians(entity->getRotation());
    float camX = entityPos.x - std::sin(entityRotation) * distance;
    float camZ = entityPos.z - std::cos(entityRotation) * distance;
    float camY = entityPos.y + height;

    vec3 desiredPos(camX, camY, camZ);
    vec3 currentPos = camera_.getPosition();

    // Smooth interpolation (smoothing is 0-1, where 1 = instant)
    if (smoothing >= 1.0f) {
        camera_.setPosition(desiredPos);
    } else {
        vec3 newPos = vec3::lerp(currentPos, desiredPos, smoothing);
        camera_.setPosition(newPos);
    }

    // Look at entity (slightly above ground)
    camera_.setTarget(vec3(entityPos.x, entityPos.y + 0.5f, entityPos.z));
}

// =============================================================================
// Mesh Layer Management
// =============================================================================

std::shared_ptr<MeshLayer> Viewport3D::addLayer(const std::string& name, int zIndex) {
    // Check if layer with this name already exists
    for (auto& layer : meshLayers_) {
        if (layer->getName() == name) {
            return layer;  // Return existing layer
        }
    }

    // Create new layer
    auto layer = std::make_shared<MeshLayer>(name, zIndex);
    layer->setViewport(this);  // Allow layer to mark cells as blocking
    meshLayers_.push_back(layer);

    // Disable test cube when layers are added
    renderTestCube_ = false;

    return layer;
}

std::shared_ptr<MeshLayer> Viewport3D::getLayer(const std::string& name) {
    for (auto& layer : meshLayers_) {
        if (layer->getName() == name) {
            return layer;
        }
    }
    return nullptr;
}

bool Viewport3D::removeLayer(const std::string& name) {
    for (auto it = meshLayers_.begin(); it != meshLayers_.end(); ++it) {
        if ((*it)->getName() == name) {
            meshLayers_.erase(it);
            return true;
        }
    }
    return false;
}

// =============================================================================
// Navigation Grid (VoxelPoint System)
// =============================================================================

void Viewport3D::setGridSize(int width, int depth) {
    if (width <= 0 || depth <= 0) {
        throw std::invalid_argument("Grid dimensions must be positive");
    }

    gridWidth_ = width;
    gridDepth_ = depth;

    // Resize and initialize grid
    navGrid_.resize(width * depth);
    for (int z = 0; z < depth; z++) {
        for (int x = 0; x < width; x++) {
            int idx = z * width + x;
            navGrid_[idx] = VoxelPoint(x, z, this);
        }
    }

    // Create/recreate TCODMap
    if (tcodMap_) {
        delete tcodMap_;
    }
    tcodMap_ = new TCODMap(width, depth);

    // Sync initial state
    syncToTCOD();
}

VoxelPoint& Viewport3D::at(int x, int z) {
    if (!isValidCell(x, z)) {
        throw std::out_of_range("Grid coordinates out of range");
    }
    return navGrid_[z * gridWidth_ + x];
}

const VoxelPoint& Viewport3D::at(int x, int z) const {
    if (!isValidCell(x, z)) {
        throw std::out_of_range("Grid coordinates out of range");
    }
    return navGrid_[z * gridWidth_ + x];
}

bool Viewport3D::isValidCell(int x, int z) const {
    return x >= 0 && x < gridWidth_ && z >= 0 && z < gridDepth_;
}

void Viewport3D::syncToTCOD() {
    if (!tcodMap_) return;

    for (int z = 0; z < gridDepth_; z++) {
        for (int x = 0; x < gridWidth_; x++) {
            const VoxelPoint& vp = at(x, z);
            tcodMap_->setProperties(x, z, vp.transparent, vp.walkable);
        }
    }
}

void Viewport3D::syncTCODCell(int x, int z) {
    if (!tcodMap_ || !isValidCell(x, z)) return;

    const VoxelPoint& vp = at(x, z);
    tcodMap_->setProperties(x, z, vp.transparent, vp.walkable);
}

void Viewport3D::applyHeightmap(TCOD_heightmap_t* hm, float yScale) {
    if (!hm) return;

    // Ensure grid matches heightmap dimensions
    if (gridWidth_ != hm->w || gridDepth_ != hm->h) {
        setGridSize(hm->w, hm->h);
    }

    // Apply heights
    for (int z = 0; z < gridDepth_; z++) {
        for (int x = 0; x < gridWidth_; x++) {
            int idx = z * hm->w + x;
            navGrid_[z * gridWidth_ + x].height = hm->values[idx] * yScale;
        }
    }
}

void Viewport3D::applyThreshold(TCOD_heightmap_t* hm, float minHeight, float maxHeight, bool walkable) {
    if (!hm) return;

    // Grid must match heightmap dimensions
    if (gridWidth_ != hm->w || gridDepth_ != hm->h) {
        return;  // Dimension mismatch
    }

    for (int z = 0; z < gridDepth_; z++) {
        for (int x = 0; x < gridWidth_; x++) {
            int idx = z * hm->w + x;
            float h = hm->values[idx];
            if (h >= minHeight && h <= maxHeight) {
                navGrid_[z * gridWidth_ + x].walkable = walkable;
            }
        }
    }

    syncToTCOD();
}

void Viewport3D::setSlopeCost(float maxSlope, float costMultiplier) {
    if (gridWidth_ < 2 || gridDepth_ < 2) return;

    // Neighbor offsets (4-directional)
    const int dx[] = {-1, 1, 0, 0};
    const int dz[] = {0, 0, -1, 1};

    for (int z = 0; z < gridDepth_; z++) {
        for (int x = 0; x < gridWidth_; x++) {
            VoxelPoint& vp = navGrid_[z * gridWidth_ + x];
            float maxNeighborDiff = 0.0f;

            // Check all neighbors
            for (int i = 0; i < 4; i++) {
                int nx = x + dx[i];
                int nz = z + dz[i];
                if (isValidCell(nx, nz)) {
                    float diff = std::abs(vp.height - at(nx, nz).height);
                    maxNeighborDiff = std::max(maxNeighborDiff, diff);
                }
            }

            // Mark unwalkable if too steep, otherwise set cost
            if (maxNeighborDiff > maxSlope) {
                vp.walkable = false;
            } else {
                vp.cost = 1.0f + maxNeighborDiff * costMultiplier;
            }
        }
    }

    syncToTCOD();
}

std::vector<std::pair<int, int>> Viewport3D::findPath(int startX, int startZ, int endX, int endZ) {
    std::vector<std::pair<int, int>> result;

    if (!tcodMap_ || !isValidCell(startX, startZ) || !isValidCell(endX, endZ)) {
        return result;
    }

    // Ensure TCOD is synced
    syncToTCOD();

    // Create path with cost callback
    struct PathUserData {
        Viewport3D* viewport;
    };
    PathUserData userData = {this};

    // Use TCODPath with diagonal movement
    TCODPath path(tcodMap_, 1.41f);

    // Compute path
    if (!path.compute(startX, startZ, endX, endZ)) {
        return result;  // No path found
    }

    // Extract path
    int x, z;
    while (path.walk(&x, &z, true)) {
        result.push_back({x, z});
    }

    return result;
}

std::vector<std::pair<int, int>> Viewport3D::computeFOV(int originX, int originZ, int radius) {
    std::vector<std::pair<int, int>> visible;

    if (!tcodMap_ || !isValidCell(originX, originZ)) {
        return visible;
    }

    // Thread-safe FOV computation
    std::lock_guard<std::mutex> lock(fovMutex_);

    // Ensure TCOD is synced
    syncToTCOD();

    // Compute FOV
    tcodMap_->computeFov(originX, originZ, radius, true, FOV_BASIC);

    // Collect visible cells
    for (int z = 0; z < gridDepth_; z++) {
        for (int x = 0; x < gridWidth_; x++) {
            if (tcodMap_->isInFov(x, z)) {
                visible.push_back({x, z});
            }
        }
    }

    return visible;
}

bool Viewport3D::isInFOV(int x, int z) const {
    if (!tcodMap_ || !isValidCell(x, z)) {
        return false;
    }

    std::lock_guard<std::mutex> lock(fovMutex_);
    return tcodMap_->isInFov(x, z);
}

// =============================================================================
// Entity3D Management
// =============================================================================

void Viewport3D::updateEntities(float dt) {
    if (!entities_) return;

    for (auto& entity : *entities_) {
        if (entity) {
            entity->update(dt);
        }
    }
}

void Viewport3D::renderEntities(const mat4& view, const mat4& proj) {
#ifdef MCRF_HAS_GL
    if (!entities_ || !shader_ || !shader_->isValid()) return;

    // Extract frustum for culling
    mat4 viewProj = proj * view;
    Frustum frustum;
    frustum.extractFromMatrix(viewProj);

    // Render non-skeletal entities first
    shader_->bind();
    for (auto& entity : *entities_) {
        if (entity && entity->isVisible()) {
            // Frustum culling - use entity position with generous bounding radius
            vec3 pos = entity->getWorldPos();
            float boundingRadius = entity->getScale().x * 2.0f;  // Approximate bounding sphere

            if (!frustum.containsSphere(pos, boundingRadius)) {
                continue;  // Skip this entity - outside view frustum
            }

            auto model = entity->getModel();
            if (!model || !model->hasSkeleton()) {
                entity->render(view, proj, shader_->getProgram());
            }
        }
    }
    shader_->unbind();

    // Then render skeletal entities with skinned shader
    if (skinnedShader_ && skinnedShader_->isValid()) {
        skinnedShader_->bind();

        // Set up common uniforms for skinned shader
        skinnedShader_->setUniform("u_view", view);
        skinnedShader_->setUniform("u_projection", proj);
        skinnedShader_->setUniform("u_resolution", vec2(static_cast<float>(internalWidth_),
                                                        static_cast<float>(internalHeight_)));
        skinnedShader_->setUniform("u_enable_snap", vertexSnapEnabled_);

        // Lighting
        vec3 lightDir = vec3(0.5f, -0.7f, 0.5f).normalized();
        skinnedShader_->setUniform("u_light_dir", lightDir);
        skinnedShader_->setUniform("u_ambient", vec3(0.3f, 0.3f, 0.3f));

        // Fog
        skinnedShader_->setUniform("u_fog_start", fogNear_);
        skinnedShader_->setUniform("u_fog_end", fogFar_);
        skinnedShader_->setUniform("u_fog_color", fogColor_);

        // Texture
        skinnedShader_->setUniform("u_has_texture", false);
        skinnedShader_->setUniform("u_enable_dither", ditheringEnabled_);

        for (auto& entity : *entities_) {
            if (entity && entity->isVisible()) {
                // Frustum culling for skeletal entities too
                vec3 pos = entity->getWorldPos();
                float boundingRadius = entity->getScale().x * 2.0f;

                if (!frustum.containsSphere(pos, boundingRadius)) {
                    continue;
                }

                auto model = entity->getModel();
                if (model && model->hasSkeleton()) {
                    entity->render(view, proj, skinnedShader_->getProgram());
                }
            }
        }
        skinnedShader_->unbind();
    }
#endif
}

// =============================================================================
// Billboard Management
// =============================================================================

void Viewport3D::addBillboard(std::shared_ptr<Billboard> bb) {
    if (billboards_ && bb) {
        billboards_->push_back(bb);
    }
}

void Viewport3D::removeBillboard(Billboard* bb) {
    if (!billboards_ || !bb) return;
    auto it = std::find_if(billboards_->begin(), billboards_->end(),
                           [bb](const std::shared_ptr<Billboard>& p) { return p.get() == bb; });
    if (it != billboards_->end()) {
        billboards_->erase(it);
    }
}

void Viewport3D::clearBillboards() {
    if (billboards_) {
        billboards_->clear();
    }
}

void Viewport3D::renderBillboards(const mat4& view, const mat4& proj) {
#ifdef MCRF_HAS_GL
    if (!billboards_ || billboards_->empty() || !shader_ || !shader_->isValid()) return;

    // Extract frustum for culling
    mat4 viewProj = proj * view;
    Frustum frustum;
    frustum.extractFromMatrix(viewProj);

    shader_->bind();
    unsigned int shaderProgram = shader_->getProgram();
    vec3 cameraPos = camera_.getPosition();

    // Enable blending for transparency
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

    // Disable depth write but keep depth test for proper ordering
    glDepthMask(GL_FALSE);

    for (auto& billboard : *billboards_) {
        if (billboard && billboard->isVisible()) {
            // Frustum culling for billboards
            vec3 pos = billboard->getPosition();
            float boundingRadius = billboard->getScale() * 2.0f;  // Approximate

            if (!frustum.containsSphere(pos, boundingRadius)) {
                continue;  // Skip - outside frustum
            }

            billboard->render(shaderProgram, view, proj, cameraPos);
        }
    }

    // Restore depth writing
    glDepthMask(GL_TRUE);
    glDisable(GL_BLEND);

    shader_->unbind();
#endif
}

// =============================================================================
// FBO Management
// =============================================================================

void Viewport3D::initFBO() {
    if (fbo_ != 0) return;  // Already initialized

    fbo_ = gl::createFramebuffer(internalWidth_, internalHeight_,
                                  &colorTexture_, &depthRenderbuffer_);

    // Create SFML texture wrapper for blitting
    // Note: We can't directly use the GL texture with SFML, so we'll
    // read pixels back for now. This is inefficient but works across backends.
    blitTexture_ = std::make_unique<sf::Texture>();
    blitTexture_->create(internalWidth_, internalHeight_);
}

void Viewport3D::cleanupFBO() {
    blitTexture_.reset();
    if (fbo_ != 0) {
        gl::deleteFramebuffer(fbo_, colorTexture_, depthRenderbuffer_);
        fbo_ = 0;
        colorTexture_ = 0;
        depthRenderbuffer_ = 0;
    }
}

// =============================================================================
// Shader and Geometry Initialization
// =============================================================================

void Viewport3D::initShader() {
    shader_ = std::make_unique<Shader3D>();
    if (!shader_->loadPS1Shaders()) {
        shader_.reset();  // Shader loading failed
    }

    // Also create skinned shader for skeletal animation
    skinnedShader_ = std::make_unique<Shader3D>();
    if (!skinnedShader_->loadPS1SkinnedShaders()) {
        skinnedShader_.reset();  // Skinned shader loading failed
    }
}

void Viewport3D::initTestGeometry() {
#ifdef MCRF_HAS_GL
    // Create a colored cube (no texture for now)
    // Each vertex: position (3) + texcoord (2) + normal (3) + color (4) = 12 floats
    // Cube has 6 faces * 2 triangles * 3 vertices = 36 vertices

    float cubeVertices[] = {
        // Front face (red) - normal (0, 0, 1)
        -1, -1,  1,  0, 0,  0, 0, 1,  1, 0.2f, 0.2f, 1,
         1, -1,  1,  1, 0,  0, 0, 1,  1, 0.2f, 0.2f, 1,
         1,  1,  1,  1, 1,  0, 0, 1,  1, 0.2f, 0.2f, 1,
        -1, -1,  1,  0, 0,  0, 0, 1,  1, 0.2f, 0.2f, 1,
         1,  1,  1,  1, 1,  0, 0, 1,  1, 0.2f, 0.2f, 1,
        -1,  1,  1,  0, 1,  0, 0, 1,  1, 0.2f, 0.2f, 1,

        // Back face (cyan) - normal (0, 0, -1)
         1, -1, -1,  0, 0,  0, 0,-1,  0.2f, 1, 1, 1,
        -1, -1, -1,  1, 0,  0, 0,-1,  0.2f, 1, 1, 1,
        -1,  1, -1,  1, 1,  0, 0,-1,  0.2f, 1, 1, 1,
         1, -1, -1,  0, 0,  0, 0,-1,  0.2f, 1, 1, 1,
        -1,  1, -1,  1, 1,  0, 0,-1,  0.2f, 1, 1, 1,
         1,  1, -1,  0, 1,  0, 0,-1,  0.2f, 1, 1, 1,

        // Top face (green) - normal (0, 1, 0)
        -1,  1,  1,  0, 0,  0, 1, 0,  0.2f, 1, 0.2f, 1,
         1,  1,  1,  1, 0,  0, 1, 0,  0.2f, 1, 0.2f, 1,
         1,  1, -1,  1, 1,  0, 1, 0,  0.2f, 1, 0.2f, 1,
        -1,  1,  1,  0, 0,  0, 1, 0,  0.2f, 1, 0.2f, 1,
         1,  1, -1,  1, 1,  0, 1, 0,  0.2f, 1, 0.2f, 1,
        -1,  1, -1,  0, 1,  0, 1, 0,  0.2f, 1, 0.2f, 1,

        // Bottom face (magenta) - normal (0, -1, 0)
        -1, -1, -1,  0, 0,  0,-1, 0,  1, 0.2f, 1, 1,
         1, -1, -1,  1, 0,  0,-1, 0,  1, 0.2f, 1, 1,
         1, -1,  1,  1, 1,  0,-1, 0,  1, 0.2f, 1, 1,
        -1, -1, -1,  0, 0,  0,-1, 0,  1, 0.2f, 1, 1,
         1, -1,  1,  1, 1,  0,-1, 0,  1, 0.2f, 1, 1,
        -1, -1,  1,  0, 1,  0,-1, 0,  1, 0.2f, 1, 1,

        // Right face (blue) - normal (1, 0, 0)
         1, -1,  1,  0, 0,  1, 0, 0,  0.2f, 0.2f, 1, 1,
         1, -1, -1,  1, 0,  1, 0, 0,  0.2f, 0.2f, 1, 1,
         1,  1, -1,  1, 1,  1, 0, 0,  0.2f, 0.2f, 1, 1,
         1, -1,  1,  0, 0,  1, 0, 0,  0.2f, 0.2f, 1, 1,
         1,  1, -1,  1, 1,  1, 0, 0,  0.2f, 0.2f, 1, 1,
         1,  1,  1,  0, 1,  1, 0, 0,  0.2f, 0.2f, 1, 1,

        // Left face (yellow) - normal (-1, 0, 0)
        -1, -1, -1,  0, 0, -1, 0, 0,  1, 1, 0.2f, 1,
        -1, -1,  1,  1, 0, -1, 0, 0,  1, 1, 0.2f, 1,
        -1,  1,  1,  1, 1, -1, 0, 0,  1, 1, 0.2f, 1,
        -1, -1, -1,  0, 0, -1, 0, 0,  1, 1, 0.2f, 1,
        -1,  1,  1,  1, 1, -1, 0, 0,  1, 1, 0.2f, 1,
        -1,  1, -1,  0, 1, -1, 0, 0,  1, 1, 0.2f, 1,
    };

    testVertexCount_ = 36;

    glGenBuffers(1, &testVBO_);
    glBindBuffer(GL_ARRAY_BUFFER, testVBO_);
    glBufferData(GL_ARRAY_BUFFER, sizeof(cubeVertices), cubeVertices, GL_STATIC_DRAW);
    glBindBuffer(GL_ARRAY_BUFFER, 0);
#endif
}

void Viewport3D::cleanupTestGeometry() {
#ifdef MCRF_HAS_GL
    if (testVBO_ != 0) {
        glDeleteBuffers(1, &testVBO_);
        testVBO_ = 0;
    }
#endif
}

// =============================================================================
// 3D Rendering
// =============================================================================

void Viewport3D::renderMeshLayers() {
#ifdef MCRF_HAS_GL
    if (meshLayers_.empty() || !shader_ || !shader_->isValid()) {
        return;
    }

    // Sort layers by z_index (lower = rendered first)
    std::vector<MeshLayer*> sortedLayers;
    sortedLayers.reserve(meshLayers_.size());
    for (auto& layer : meshLayers_) {
        if (layer && layer->isVisible()) {
            sortedLayers.push_back(layer.get());
        }
    }
    std::sort(sortedLayers.begin(), sortedLayers.end(),
              [](const MeshLayer* a, const MeshLayer* b) {
                  return a->getZIndex() < b->getZIndex();
              });

    shader_->bind();

    // Set up view and projection matrices (same for all layers)
    mat4 view = camera_.getViewMatrix();
    mat4 projection = camera_.getProjectionMatrix();

    shader_->setUniform("u_view", view);
    shader_->setUniform("u_projection", projection);

    // PS1 effect uniforms
    shader_->setUniform("u_resolution", vec2(static_cast<float>(internalWidth_),
                                               static_cast<float>(internalHeight_)));
    shader_->setUniform("u_enable_snap", vertexSnapEnabled_);
    shader_->setUniform("u_enable_dither", ditheringEnabled_);

    // Lighting
    vec3 lightDir = vec3(0.5f, -0.7f, 0.5f).normalized();
    shader_->setUniform("u_light_dir", lightDir);
    shader_->setUniform("u_ambient", vec3(0.3f, 0.3f, 0.3f));

    // Fog
    shader_->setUniform("u_fog_start", fogNear_);
    shader_->setUniform("u_fog_end", fogFar_);
    shader_->setUniform("u_fog_color", fogColor_);

    // For now, no textures on terrain (use vertex colors)
    shader_->setUniform("u_has_texture", false);

    // Render each layer
    unsigned int shaderProgram = shader_->getProgram();
    for (auto* layer : sortedLayers) {
        // Set model matrix for this layer
        shader_->setUniform("u_model", layer->getModelMatrix());

        // Render the layer's geometry (terrain + mesh instances)
        layer->render(shaderProgram, layer->getModelMatrix(), view, projection);
    }

    shader_->unbind();
#endif
}

// =============================================================================
// Voxel Layer Management (Milestone 10)
// =============================================================================

void Viewport3D::addVoxelLayer(std::shared_ptr<VoxelGrid> grid, int zIndex) {
    if (!grid) return;
    voxelLayers_.push_back({grid, zIndex});

    // Disable test cube when real content is added
    renderTestCube_ = false;
}

bool Viewport3D::removeVoxelLayer(std::shared_ptr<VoxelGrid> grid) {
    if (!grid) return false;

    auto it = std::find_if(voxelLayers_.begin(), voxelLayers_.end(),
                           [&grid](const auto& pair) { return pair.first == grid; });

    if (it != voxelLayers_.end()) {
        voxelLayers_.erase(it);
        return true;
    }
    return false;
}

// =============================================================================
// Voxel-to-Nav Projection (Milestone 12)
// =============================================================================

void Viewport3D::clearVoxelNavRegion(std::shared_ptr<VoxelGrid> grid) {
    if (!grid || navGrid_.empty()) return;

    // Get voxel grid offset in world space
    vec3 offset = grid->getOffset();
    float cellSize = grid->cellSize();

    // Calculate nav grid cell offset from voxel grid offset
    int navOffsetX = static_cast<int>(std::floor(offset.x / cellSize_));
    int navOffsetZ = static_cast<int>(std::floor(offset.z / cellSize_));

    // Clear nav cells corresponding to voxel grid footprint
    for (int vz = 0; vz < grid->depth(); vz++) {
        for (int vx = 0; vx < grid->width(); vx++) {
            int navX = navOffsetX + vx;
            int navZ = navOffsetZ + vz;

            if (isValidCell(navX, navZ)) {
                VoxelPoint& cell = at(navX, navZ);
                cell.walkable = true;
                cell.transparent = true;
                cell.height = 0.0f;
                cell.cost = 1.0f;
            }
        }
    }

    // Sync to TCOD
    syncToTCOD();
}

void Viewport3D::projectVoxelToNav(std::shared_ptr<VoxelGrid> grid, int headroom) {
    if (!grid || navGrid_.empty()) return;

    // Get voxel grid offset in world space
    vec3 offset = grid->getOffset();
    float voxelCellSize = grid->cellSize();

    // Calculate nav grid cell offset from voxel grid offset
    // Assuming nav cell size matches voxel cell size for 1:1 mapping
    int navOffsetX = static_cast<int>(std::floor(offset.x / cellSize_));
    int navOffsetZ = static_cast<int>(std::floor(offset.z / cellSize_));

    // Project each column of the voxel grid to the navigation grid
    for (int vz = 0; vz < grid->depth(); vz++) {
        for (int vx = 0; vx < grid->width(); vx++) {
            int navX = navOffsetX + vx;
            int navZ = navOffsetZ + vz;

            if (!isValidCell(navX, navZ)) continue;

            // Get projection info from voxel column
            VoxelGrid::NavInfo navInfo = grid->projectColumn(vx, vz, headroom);

            // Update nav cell
            VoxelPoint& cell = at(navX, navZ);
            cell.height = navInfo.height + offset.y;  // Add world Y offset
            cell.walkable = navInfo.walkable;
            cell.transparent = navInfo.transparent;
            cell.cost = navInfo.pathCost;

            // Sync this cell to TCOD
            syncTCODCell(navX, navZ);
        }
    }
}

void Viewport3D::projectAllVoxelsToNav(int headroom) {
    if (navGrid_.empty()) return;

    // First, reset all nav cells to default state
    for (auto& cell : navGrid_) {
        cell.walkable = true;
        cell.transparent = true;
        cell.height = 0.0f;
        cell.cost = 1.0f;
    }

    // Project each voxel layer in order (later layers overwrite earlier)
    // Sort by z_index so higher z_index layers take precedence
    std::vector<std::pair<std::shared_ptr<VoxelGrid>, int>> sortedLayers = voxelLayers_;
    std::sort(sortedLayers.begin(), sortedLayers.end(),
              [](const auto& a, const auto& b) { return a.second < b.second; });

    for (const auto& pair : sortedLayers) {
        if (pair.first) {
            projectVoxelToNav(pair.first, headroom);
        }
    }

    // Final sync to TCOD (redundant but ensures consistency)
    syncToTCOD();
}

void Viewport3D::renderVoxelLayers(const mat4& view, const mat4& proj) {
#ifdef MCRF_HAS_GL
    if (voxelLayers_.empty() || !shader_ || !shader_->isValid()) {
        return;
    }

    // Sort layers by z_index (lower = rendered first)
    std::vector<std::pair<VoxelGrid*, int>> sortedLayers;
    sortedLayers.reserve(voxelLayers_.size());
    for (auto& pair : voxelLayers_) {
        if (pair.first) {
            sortedLayers.push_back({pair.first.get(), pair.second});
        }
    }
    std::sort(sortedLayers.begin(), sortedLayers.end(),
              [](const auto& a, const auto& b) { return a.second < b.second; });

    shader_->bind();

    // Set up view and projection matrices
    shader_->setUniform("u_view", view);
    shader_->setUniform("u_projection", proj);

    // PS1 effect uniforms
    shader_->setUniform("u_resolution", vec2(static_cast<float>(internalWidth_),
                                               static_cast<float>(internalHeight_)));
    shader_->setUniform("u_enable_snap", vertexSnapEnabled_);
    shader_->setUniform("u_enable_dither", ditheringEnabled_);

    // Lighting
    vec3 lightDir = vec3(0.5f, -0.7f, 0.5f).normalized();
    shader_->setUniform("u_light_dir", lightDir);
    shader_->setUniform("u_ambient", vec3(0.3f, 0.3f, 0.3f));

    // Fog
    shader_->setUniform("u_fog_start", fogNear_);
    shader_->setUniform("u_fog_end", fogFar_);
    shader_->setUniform("u_fog_color", fogColor_);

    // No texture for voxels (use vertex colors)
    shader_->setUniform("u_has_texture", false);

    // Create VBO if needed
    if (voxelVBO_ == 0) {
        glGenBuffers(1, &voxelVBO_);
    }

    // Render each voxel grid
    for (auto& pair : sortedLayers) {
        VoxelGrid* grid = pair.first;

        // Skip invisible grids
        if (!grid->isVisible()) continue;

        // Get vertices (triggers rebuild if dirty)
        const std::vector<MeshVertex>& vertices = grid->getVertices();
        if (vertices.empty()) continue;

        // Set model matrix for this grid
        shader_->setUniform("u_model", grid->getModelMatrix());

        // Upload vertices to VBO
        glBindBuffer(GL_ARRAY_BUFFER, voxelVBO_);
        glBufferData(GL_ARRAY_BUFFER,
                     vertices.size() * sizeof(MeshVertex),
                     vertices.data(),
                     GL_DYNAMIC_DRAW);

        // Set up vertex attributes (same as MeshLayer)
        size_t stride = sizeof(MeshVertex);

        // Position
        glEnableVertexAttribArray(0);
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, (void*)offsetof(MeshVertex, position));

        // TexCoord
        glEnableVertexAttribArray(1);
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, (void*)offsetof(MeshVertex, texcoord));

        // Normal
        glEnableVertexAttribArray(2);
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, stride, (void*)offsetof(MeshVertex, normal));

        // Color
        glEnableVertexAttribArray(3);
        glVertexAttribPointer(3, 4, GL_FLOAT, GL_FALSE, stride, (void*)offsetof(MeshVertex, color));

        // Draw
        glDrawArrays(GL_TRIANGLES, 0, static_cast<GLsizei>(vertices.size()));

        // Cleanup
        glDisableVertexAttribArray(0);
        glDisableVertexAttribArray(1);
        glDisableVertexAttribArray(2);
        glDisableVertexAttribArray(3);
        glBindBuffer(GL_ARRAY_BUFFER, 0);
    }

    shader_->unbind();
#endif
}

void Viewport3D::render3DContent() {
    // GL not available in current backend - skip 3D rendering
    if (!gl::isGLReady() || fbo_ == 0) {
        return;
    }

#ifdef MCRF_HAS_GL
    // Calculate delta time for animation updates
    static sf::Clock frameClock;
    float currentTime = frameClock.getElapsedTime().asSeconds();
    float dt = firstFrame_ ? 0.016f : (currentTime - lastFrameTime_);
    lastFrameTime_ = currentTime;
    firstFrame_ = false;

    // Cap delta time to avoid huge jumps (e.g., after window minimize)
    if (dt > 0.1f) dt = 0.016f;

    // Update entity animations
    updateEntities(dt);

    // Save GL state
    gl::pushState();

    // Bind FBO
    gl::bindFramebuffer(fbo_);

    // Set viewport to internal resolution
    glViewport(0, 0, internalWidth_, internalHeight_);

    // Clear with background color
    glClearColor(bgColor_.r / 255.0f, bgColor_.g / 255.0f,
                 bgColor_.b / 255.0f, bgColor_.a / 255.0f);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

    // Set up 3D state
    gl::setup3DState();

    // Update test rotation for spinning geometry
    testRotation_ += 0.02f;

    // Render mesh layers first (terrain, etc.) - sorted by z_index
    renderMeshLayers();

    // Render voxel layers (Milestone 10)
    mat4 view = camera_.getViewMatrix();
    mat4 projection = camera_.getProjectionMatrix();
    renderVoxelLayers(view, projection);

    // Render entities
    renderEntities(view, projection);

    // Render billboards (after opaque geometry for proper transparency)
    renderBillboards(view, projection);

    // Render test cube if enabled (disabled when layers are added)
    if (renderTestCube_ && shader_ && shader_->isValid() && testVBO_ != 0) {
        shader_->bind();

        // Set up matrices
        mat4 model = mat4::rotateY(testRotation_) * mat4::rotateX(testRotation_ * 0.7f);
        mat4 view = camera_.getViewMatrix();
        mat4 projection = camera_.getProjectionMatrix();

        shader_->setUniform("u_model", model);
        shader_->setUniform("u_view", view);
        shader_->setUniform("u_projection", projection);

        // PS1 effect uniforms
        shader_->setUniform("u_resolution", vec2(static_cast<float>(internalWidth_),
                                                   static_cast<float>(internalHeight_)));
        shader_->setUniform("u_enable_snap", vertexSnapEnabled_);
        shader_->setUniform("u_enable_dither", ditheringEnabled_);

        // Lighting
        vec3 lightDir = vec3(0.5f, -0.7f, 0.5f).normalized();
        shader_->setUniform("u_light_dir", lightDir);
        shader_->setUniform("u_ambient", vec3(0.3f, 0.3f, 0.3f));

        // Fog
        shader_->setUniform("u_fog_start", fogNear_);
        shader_->setUniform("u_fog_end", fogFar_);
        shader_->setUniform("u_fog_color", fogColor_);

        // Texture (none for test geometry)
        shader_->setUniform("u_has_texture", false);

        // Bind VBO and set up attributes
        glBindBuffer(GL_ARRAY_BUFFER, testVBO_);

        // Vertex format: pos(3) + texcoord(2) + normal(3) + color(4) = 12 floats
        int stride = 12 * sizeof(float);

        glEnableVertexAttribArray(Shader3D::ATTRIB_POSITION);
        glVertexAttribPointer(Shader3D::ATTRIB_POSITION, 3, GL_FLOAT, GL_FALSE, stride, (void*)0);

        glEnableVertexAttribArray(Shader3D::ATTRIB_TEXCOORD);
        glVertexAttribPointer(Shader3D::ATTRIB_TEXCOORD, 2, GL_FLOAT, GL_FALSE, stride, (void*)(3 * sizeof(float)));

        glEnableVertexAttribArray(Shader3D::ATTRIB_NORMAL);
        glVertexAttribPointer(Shader3D::ATTRIB_NORMAL, 3, GL_FLOAT, GL_FALSE, stride, (void*)(5 * sizeof(float)));

        glEnableVertexAttribArray(Shader3D::ATTRIB_COLOR);
        glVertexAttribPointer(Shader3D::ATTRIB_COLOR, 4, GL_FLOAT, GL_FALSE, stride, (void*)(8 * sizeof(float)));

        // Draw cube
        glDrawArrays(GL_TRIANGLES, 0, testVertexCount_);

        // Cleanup
        glDisableVertexAttribArray(Shader3D::ATTRIB_POSITION);
        glDisableVertexAttribArray(Shader3D::ATTRIB_TEXCOORD);
        glDisableVertexAttribArray(Shader3D::ATTRIB_NORMAL);
        glDisableVertexAttribArray(Shader3D::ATTRIB_COLOR);
        glBindBuffer(GL_ARRAY_BUFFER, 0);

        shader_->unbind();
    }

    // Restore 2D state
    gl::restore2DState();

    // Unbind FBO
    gl::bindDefaultFramebuffer();

    // Restore GL state
    gl::popState();
#endif
}

void Viewport3D::blitToScreen(sf::Vector2f offset, sf::RenderTarget& target) {
    sf::Vector2f screenPos = position + offset;

    // If GL is not ready, just draw a placeholder rectangle
    if (!gl::isGLReady() || fbo_ == 0 || !blitTexture_) {
        sf::RectangleShape placeholder(size_);
        placeholder.setPosition(screenPos);
        placeholder.setFillColor(bgColor_);
        placeholder.setOutlineColor(sf::Color::White);
        placeholder.setOutlineThickness(1.0f);
        target.draw(placeholder);
        return;
    }

#ifdef MCRF_HAS_GL
    // Read pixels from FBO and update SFML texture
    // Note: This is inefficient but portable. Future optimization: use GL texture directly.
    std::vector<sf::Uint8> pixels(internalWidth_ * internalHeight_ * 4);

    gl::bindFramebuffer(fbo_);
    glReadPixels(0, 0, internalWidth_, internalHeight_, GL_RGBA, GL_UNSIGNED_BYTE, pixels.data());
    gl::bindDefaultFramebuffer();

    // Flip vertically (OpenGL vs SFML coordinate system)
    std::vector<sf::Uint8> flipped(pixels.size());
    for (int y = 0; y < internalHeight_; ++y) {
        int srcRow = (internalHeight_ - 1 - y) * internalWidth_ * 4;
        int dstRow = y * internalWidth_ * 4;
        memcpy(&flipped[dstRow], &pixels[srcRow], internalWidth_ * 4);
    }

    blitTexture_->update(flipped.data());

    // Draw to screen with nearest-neighbor scaling (PS1 style)
    sf::Sprite sprite(*blitTexture_);
    sprite.setPosition(screenPos);
    sprite.setScale(size_.x / internalWidth_, size_.y / internalHeight_);

    // Set nearest-neighbor filtering for that crispy PS1 look
    // Note: SFML 2.x doesn't have per-draw texture filtering, so this
    // affects the texture globally. In practice this is fine for our use.
    const_cast<sf::Texture*>(sprite.getTexture())->setSmooth(false);

    target.draw(sprite);
#else
    // Non-SDL2 fallback (SFML desktop without GL)
    sf::RectangleShape placeholder(size_);
    placeholder.setPosition(screenPos);
    placeholder.setFillColor(bgColor_);
    target.draw(placeholder);
#endif
}

// =============================================================================
// Animation Property System
// =============================================================================

bool Viewport3D::setProperty(const std::string& name, float value) {
    if (name == "x") { position.x = value; return true; }
    if (name == "y") { position.y = value; return true; }
    if (name == "w") { size_.x = value; camera_.setAspect(size_.x / size_.y); return true; }
    if (name == "h") { size_.y = value; camera_.setAspect(size_.x / size_.y); return true; }
    if (name == "fov") { camera_.setFOV(value); return true; }
    if (name == "fog_near") { fogNear_ = value; return true; }
    if (name == "fog_far") { fogFar_ = value; return true; }
    if (name == "opacity") { opacity = value; return true; }
    return false;
}

bool Viewport3D::setProperty(const std::string& name, const sf::Color& value) {
    if (name == "bg_color") { bgColor_ = value; return true; }
    if (name == "fog_color") { setFogColor(value); return true; }
    return false;
}

bool Viewport3D::setProperty(const std::string& name, const sf::Vector2f& value) {
    if (name == "pos") { position = value; return true; }
    if (name == "size") { size_ = value; camera_.setAspect(size_.x / size_.y); return true; }
    return false;
}

bool Viewport3D::getProperty(const std::string& name, float& value) const {
    if (name == "x") { value = position.x; return true; }
    if (name == "y") { value = position.y; return true; }
    if (name == "w") { value = size_.x; return true; }
    if (name == "h") { value = size_.y; return true; }
    if (name == "fov") { value = camera_.getFOV(); return true; }
    if (name == "fog_near") { value = fogNear_; return true; }
    if (name == "fog_far") { value = fogFar_; return true; }
    if (name == "opacity") { value = opacity; return true; }
    return false;
}

bool Viewport3D::getProperty(const std::string& name, sf::Color& value) const {
    if (name == "bg_color") { value = bgColor_; return true; }
    if (name == "fog_color") { value = getFogColor(); return true; }
    return false;
}

bool Viewport3D::getProperty(const std::string& name, sf::Vector2f& value) const {
    if (name == "pos") { value = position; return true; }
    if (name == "size") { value = size_; return true; }
    return false;
}

bool Viewport3D::hasProperty(const std::string& name) const {
    static const std::set<std::string> props = {
        "x", "y", "w", "h", "pos", "size",
        "fov", "fog_near", "fog_far", "opacity",
        "bg_color", "fog_color"
    };
    return props.count(name) > 0;
}

// =============================================================================
// Python API
// =============================================================================

// Use PyObjectType for UIBase.h macros
#define PyObjectType PyViewport3DObject

// Helper to get vec3 from Python tuple
static bool PyTuple_GetVec3(PyObject* tuple, mcrf::vec3& out) {
    if (!tuple || tuple == Py_None) return false;
    if (!PyTuple_Check(tuple) && !PyList_Check(tuple)) return false;

    Py_ssize_t size = PySequence_Size(tuple);
    if (size != 3) return false;

    PyObject* x = PySequence_GetItem(tuple, 0);
    PyObject* y = PySequence_GetItem(tuple, 1);
    PyObject* z = PySequence_GetItem(tuple, 2);

    bool ok = true;
    if (PyNumber_Check(x) && PyNumber_Check(y) && PyNumber_Check(z)) {
        out.x = static_cast<float>(PyFloat_AsDouble(PyNumber_Float(x)));
        out.y = static_cast<float>(PyFloat_AsDouble(PyNumber_Float(y)));
        out.z = static_cast<float>(PyFloat_AsDouble(PyNumber_Float(z)));
    } else {
        ok = false;
    }

    Py_DECREF(x);
    Py_DECREF(y);
    Py_DECREF(z);
    return ok;
}

// Helper to create Python tuple from vec3
static PyObject* PyTuple_FromVec3(const mcrf::vec3& v) {
    return Py_BuildValue("(fff)", v.x, v.y, v.z);
}

// Position getters/setters
static PyObject* Viewport3D_get_pos(PyViewport3DObject* self, void* closure) {
    return PyVector(self->data->position).pyObject();
}

static int Viewport3D_set_pos(PyViewport3DObject* self, PyObject* value, void* closure) {
    PyVectorObject* vec = PyVector::from_arg(value);
    if (!vec) {
        PyErr_SetString(PyExc_TypeError, "pos must be a Vector or (x, y) tuple");
        return -1;
    }
    self->data->position = vec->data;
    return 0;
}

static PyObject* Viewport3D_get_x(PyViewport3DObject* self, void* closure) {
    return PyFloat_FromDouble(self->data->position.x);
}

static int Viewport3D_set_x(PyViewport3DObject* self, PyObject* value, void* closure) {
    if (!PyNumber_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "x must be a number");
        return -1;
    }
    self->data->position.x = static_cast<float>(PyFloat_AsDouble(value));
    return 0;
}

static PyObject* Viewport3D_get_y(PyViewport3DObject* self, void* closure) {
    return PyFloat_FromDouble(self->data->position.y);
}

static int Viewport3D_set_y(PyViewport3DObject* self, PyObject* value, void* closure) {
    if (!PyNumber_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "y must be a number");
        return -1;
    }
    self->data->position.y = static_cast<float>(PyFloat_AsDouble(value));
    return 0;
}

// Size getters/setters
static PyObject* Viewport3D_get_w(PyViewport3DObject* self, void* closure) {
    return PyFloat_FromDouble(self->data->getWidth());
}

static int Viewport3D_set_w(PyViewport3DObject* self, PyObject* value, void* closure) {
    if (!PyNumber_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "w must be a number");
        return -1;
    }
    self->data->setSize(static_cast<float>(PyFloat_AsDouble(value)), self->data->getHeight());
    return 0;
}

static PyObject* Viewport3D_get_h(PyViewport3DObject* self, void* closure) {
    return PyFloat_FromDouble(self->data->getHeight());
}

static int Viewport3D_set_h(PyViewport3DObject* self, PyObject* value, void* closure) {
    if (!PyNumber_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "h must be a number");
        return -1;
    }
    self->data->setSize(self->data->getWidth(), static_cast<float>(PyFloat_AsDouble(value)));
    return 0;
}

// Render resolution
static PyObject* Viewport3D_get_render_resolution(PyViewport3DObject* self, void* closure) {
    return Py_BuildValue("(ii)", self->data->getInternalWidth(), self->data->getInternalHeight());
}

static int Viewport3D_set_render_resolution(PyViewport3DObject* self, PyObject* value, void* closure) {
    int w, h;
    if (!PyArg_ParseTuple(value, "ii", &w, &h)) {
        PyErr_SetString(PyExc_TypeError, "render_resolution must be (width, height)");
        return -1;
    }
    self->data->setInternalResolution(w, h);
    return 0;
}

// Camera position
static PyObject* Viewport3D_get_camera_pos(PyViewport3DObject* self, void* closure) {
    return PyTuple_FromVec3(self->data->getCameraPosition());
}

static int Viewport3D_set_camera_pos(PyViewport3DObject* self, PyObject* value, void* closure) {
    mcrf::vec3 pos;
    if (!PyTuple_GetVec3(value, pos)) {
        PyErr_SetString(PyExc_TypeError, "camera_pos must be (x, y, z)");
        return -1;
    }
    self->data->setCameraPosition(pos);
    return 0;
}

// Camera target
static PyObject* Viewport3D_get_camera_target(PyViewport3DObject* self, void* closure) {
    return PyTuple_FromVec3(self->data->getCameraTarget());
}

static int Viewport3D_set_camera_target(PyViewport3DObject* self, PyObject* value, void* closure) {
    mcrf::vec3 target;
    if (!PyTuple_GetVec3(value, target)) {
        PyErr_SetString(PyExc_TypeError, "camera_target must be (x, y, z)");
        return -1;
    }
    self->data->setCameraTarget(target);
    return 0;
}

// FOV
static PyObject* Viewport3D_get_fov(PyViewport3DObject* self, void* closure) {
    return PyFloat_FromDouble(self->data->getCamera().getFOV());
}

static int Viewport3D_set_fov(PyViewport3DObject* self, PyObject* value, void* closure) {
    if (!PyNumber_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "fov must be a number");
        return -1;
    }
    self->data->getCamera().setFOV(static_cast<float>(PyFloat_AsDouble(value)));
    return 0;
}

// Background color
static PyObject* Viewport3D_get_bg_color(PyViewport3DObject* self, void* closure) {
    return PyColor(self->data->getBackgroundColor()).pyObject();
}

static int Viewport3D_set_bg_color(PyViewport3DObject* self, PyObject* value, void* closure) {
    sf::Color color = PyColor::fromPy(value);
    if (PyErr_Occurred()) {
        return -1;
    }
    self->data->setBackgroundColor(color);
    return 0;
}

// PS1 effect toggles
static PyObject* Viewport3D_get_enable_vertex_snap(PyViewport3DObject* self, void* closure) {
    return PyBool_FromLong(self->data->isVertexSnapEnabled());
}

static int Viewport3D_set_enable_vertex_snap(PyViewport3DObject* self, PyObject* value, void* closure) {
    self->data->setVertexSnapEnabled(PyObject_IsTrue(value));
    return 0;
}

static PyObject* Viewport3D_get_enable_affine(PyViewport3DObject* self, void* closure) {
    return PyBool_FromLong(self->data->isAffineMappingEnabled());
}

static int Viewport3D_set_enable_affine(PyViewport3DObject* self, PyObject* value, void* closure) {
    self->data->setAffineMappingEnabled(PyObject_IsTrue(value));
    return 0;
}

static PyObject* Viewport3D_get_enable_dither(PyViewport3DObject* self, void* closure) {
    return PyBool_FromLong(self->data->isDitheringEnabled());
}

static int Viewport3D_set_enable_dither(PyViewport3DObject* self, PyObject* value, void* closure) {
    self->data->setDitheringEnabled(PyObject_IsTrue(value));
    return 0;
}

static PyObject* Viewport3D_get_enable_fog(PyViewport3DObject* self, void* closure) {
    return PyBool_FromLong(self->data->isFogEnabled());
}

static int Viewport3D_set_enable_fog(PyViewport3DObject* self, PyObject* value, void* closure) {
    self->data->setFogEnabled(PyObject_IsTrue(value));
    return 0;
}

// Fog color
static PyObject* Viewport3D_get_fog_color(PyViewport3DObject* self, void* closure) {
    return PyColor(self->data->getFogColor()).pyObject();
}

static int Viewport3D_set_fog_color(PyViewport3DObject* self, PyObject* value, void* closure) {
    sf::Color color = PyColor::fromPy(value);
    if (PyErr_Occurred()) {
        return -1;
    }
    self->data->setFogColor(color);
    return 0;
}

// Fog range
static PyObject* Viewport3D_get_fog_near(PyViewport3DObject* self, void* closure) {
    return PyFloat_FromDouble(self->data->getFogNear());
}

static int Viewport3D_set_fog_near(PyViewport3DObject* self, PyObject* value, void* closure) {
    if (!PyNumber_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "fog_near must be a number");
        return -1;
    }
    self->data->setFogRange(static_cast<float>(PyFloat_AsDouble(value)), self->data->getFogFar());
    return 0;
}

static PyObject* Viewport3D_get_fog_far(PyViewport3DObject* self, void* closure) {
    return PyFloat_FromDouble(self->data->getFogFar());
}

static int Viewport3D_set_fog_far(PyViewport3DObject* self, PyObject* value, void* closure) {
    if (!PyNumber_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "fog_far must be a number");
        return -1;
    }
    self->data->setFogRange(self->data->getFogNear(), static_cast<float>(PyFloat_AsDouble(value)));
    return 0;
}

// Navigation grid property getters/setters
static PyObject* Viewport3D_get_grid_size_prop(PyViewport3DObject* self, void* closure) {
    return Py_BuildValue("(ii)", self->data->getGridWidth(), self->data->getGridDepth());
}

static int Viewport3D_set_grid_size_prop(PyViewport3DObject* self, PyObject* value, void* closure) {
    if (!PyTuple_Check(value) || PyTuple_Size(value) != 2) {
        PyErr_SetString(PyExc_TypeError, "grid_size must be a tuple of (width, depth)");
        return -1;
    }

    int width, depth;
    if (!PyArg_ParseTuple(value, "ii", &width, &depth)) {
        return -1;
    }

    try {
        self->data->setGridSize(width, depth);
    } catch (const std::exception& e) {
        PyErr_SetString(PyExc_ValueError, e.what());
        return -1;
    }

    return 0;
}

static PyObject* Viewport3D_get_cell_size_prop(PyViewport3DObject* self, void* closure) {
    return PyFloat_FromDouble(self->data->getCellSize());
}

static int Viewport3D_set_cell_size_prop(PyViewport3DObject* self, PyObject* value, void* closure) {
    double size;
    if (PyFloat_Check(value)) {
        size = PyFloat_AsDouble(value);
    } else if (PyLong_Check(value)) {
        size = static_cast<double>(PyLong_AsLong(value));
    } else {
        PyErr_SetString(PyExc_TypeError, "cell_size must be a number");
        return -1;
    }

    if (size <= 0) {
        PyErr_SetString(PyExc_ValueError, "cell_size must be positive");
        return -1;
    }

    self->data->setCellSize(static_cast<float>(size));
    return 0;
}

// Entities collection property
static PyObject* Viewport3D_get_entities(PyViewport3DObject* self, void* closure) {
    // Create an EntityCollection3D wrapper for this viewport's entity list
    auto type = &mcrfpydef::PyEntityCollection3DType;
    auto obj = (PyEntityCollection3DObject*)type->tp_alloc(type, 0);
    if (!obj) return NULL;

    // Use placement new for shared_ptr members
    new (&obj->data) std::shared_ptr<std::list<std::shared_ptr<mcrf::Entity3D>>>(self->data->getEntities());
    new (&obj->viewport) std::shared_ptr<mcrf::Viewport3D>(self->data);

    return (PyObject*)obj;
}

PyGetSetDef Viewport3D::getsetters[] = {
    // Position and size
    {"x", (getter)Viewport3D_get_x, (setter)Viewport3D_set_x,
     MCRF_PROPERTY(x, "X position in pixels."), NULL},
    {"y", (getter)Viewport3D_get_y, (setter)Viewport3D_set_y,
     MCRF_PROPERTY(y, "Y position in pixels."), NULL},
    {"pos", (getter)Viewport3D_get_pos, (setter)Viewport3D_set_pos,
     MCRF_PROPERTY(pos, "Position as Vector (x, y)."), NULL},
    {"w", (getter)Viewport3D_get_w, (setter)Viewport3D_set_w,
     MCRF_PROPERTY(w, "Display width in pixels."), NULL},
    {"h", (getter)Viewport3D_get_h, (setter)Viewport3D_set_h,
     MCRF_PROPERTY(h, "Display height in pixels."), NULL},

    // Render resolution
    {"render_resolution", (getter)Viewport3D_get_render_resolution, (setter)Viewport3D_set_render_resolution,
     MCRF_PROPERTY(render_resolution, "Internal render resolution (width, height). Lower values for PS1 effect."), NULL},

    // Camera
    {"camera_pos", (getter)Viewport3D_get_camera_pos, (setter)Viewport3D_set_camera_pos,
     MCRF_PROPERTY(camera_pos, "Camera position as (x, y, z) tuple."), NULL},
    {"camera_target", (getter)Viewport3D_get_camera_target, (setter)Viewport3D_set_camera_target,
     MCRF_PROPERTY(camera_target, "Camera look-at target as (x, y, z) tuple."), NULL},
    {"fov", (getter)Viewport3D_get_fov, (setter)Viewport3D_set_fov,
     MCRF_PROPERTY(fov, "Camera field of view in degrees."), NULL},

    // Background
    {"bg_color", (getter)Viewport3D_get_bg_color, (setter)Viewport3D_set_bg_color,
     MCRF_PROPERTY(bg_color, "Background clear color."), NULL},

    // PS1 effects
    {"enable_vertex_snap", (getter)Viewport3D_get_enable_vertex_snap, (setter)Viewport3D_set_enable_vertex_snap,
     MCRF_PROPERTY(enable_vertex_snap, "Enable PS1-style vertex snapping (jittery vertices)."), NULL},
    {"enable_affine", (getter)Viewport3D_get_enable_affine, (setter)Viewport3D_set_enable_affine,
     MCRF_PROPERTY(enable_affine, "Enable PS1-style affine texture mapping (warped textures)."), NULL},
    {"enable_dither", (getter)Viewport3D_get_enable_dither, (setter)Viewport3D_set_enable_dither,
     MCRF_PROPERTY(enable_dither, "Enable PS1-style color dithering."), NULL},
    {"enable_fog", (getter)Viewport3D_get_enable_fog, (setter)Viewport3D_set_enable_fog,
     MCRF_PROPERTY(enable_fog, "Enable distance fog."), NULL},

    // Fog settings
    {"fog_color", (getter)Viewport3D_get_fog_color, (setter)Viewport3D_set_fog_color,
     MCRF_PROPERTY(fog_color, "Fog color."), NULL},
    {"fog_near", (getter)Viewport3D_get_fog_near, (setter)Viewport3D_set_fog_near,
     MCRF_PROPERTY(fog_near, "Fog start distance."), NULL},
    {"fog_far", (getter)Viewport3D_get_fog_far, (setter)Viewport3D_set_fog_far,
     MCRF_PROPERTY(fog_far, "Fog end distance."), NULL},

    // Navigation grid properties
    {"grid_size", (getter)Viewport3D_get_grid_size_prop, (setter)Viewport3D_set_grid_size_prop,
     MCRF_PROPERTY(grid_size, "Navigation grid dimensions as (width, depth) tuple."), NULL},
    {"cell_size", (getter)Viewport3D_get_cell_size_prop, (setter)Viewport3D_set_cell_size_prop,
     MCRF_PROPERTY(cell_size, "World units per navigation grid cell."), NULL},

    // Entity collection
    {"entities", (getter)Viewport3D_get_entities, NULL,
     MCRF_PROPERTY(entities, "Collection of Entity3D objects (read-only). Use append/remove to modify."), NULL},

    // Common UIDrawable properties
    UIDRAWABLE_GETSETTERS,
    UIDRAWABLE_PARENT_GETSETTERS(PyObjectsEnum::UIVIEWPORT3D),

    {NULL}  // Sentinel
};

PyObject* Viewport3D::repr(PyViewport3DObject* self) {
    char buffer[256];
    snprintf(buffer, sizeof(buffer), "<Viewport3D at (%.1f, %.1f) size (%.1f, %.1f) render %dx%d>",
        self->data->position.x, self->data->position.y,
        self->data->getWidth(), self->data->getHeight(),
        self->data->getInternalWidth(), self->data->getInternalHeight());
    return PyUnicode_FromString(buffer);
}

int Viewport3D::init(PyViewport3DObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {
        "pos", "size", "render_resolution", "fov",
        "camera_pos", "camera_target", "bg_color",
        "enable_vertex_snap", "enable_affine", "enable_dither", "enable_fog",
        "fog_color", "fog_near", "fog_far",
        "visible", "z_index", "name",
        NULL
    };

    PyObject* pos_obj = nullptr;
    PyObject* size_obj = nullptr;
    PyObject* render_res_obj = nullptr;
    float fov = 60.0f;
    PyObject* camera_pos_obj = nullptr;
    PyObject* camera_target_obj = nullptr;
    PyObject* bg_color_obj = nullptr;
    int enable_vertex_snap = 1;
    int enable_affine = 1;
    int enable_dither = 1;
    int enable_fog = 1;
    PyObject* fog_color_obj = nullptr;
    float fog_near = 10.0f;
    float fog_far = 100.0f;
    int visible = 1;
    int z_index = 0;
    const char* name = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OOOfOOOppppOffpis", const_cast<char**>(kwlist),
            &pos_obj, &size_obj, &render_res_obj, &fov,
            &camera_pos_obj, &camera_target_obj, &bg_color_obj,
            &enable_vertex_snap, &enable_affine, &enable_dither, &enable_fog,
            &fog_color_obj, &fog_near, &fog_far,
            &visible, &z_index, &name)) {
        return -1;
    }

    // Position
    if (pos_obj && pos_obj != Py_None) {
        PyVectorObject* vec = PyVector::from_arg(pos_obj);
        if (!vec) {
            PyErr_SetString(PyExc_TypeError, "pos must be a tuple (x, y)");
            return -1;
        }
        self->data->position = vec->data;
    }

    // Size
    if (size_obj && size_obj != Py_None) {
        float w, h;
        if (PyTuple_Check(size_obj) && PyTuple_Size(size_obj) == 2) {
            w = static_cast<float>(PyFloat_AsDouble(PyTuple_GetItem(size_obj, 0)));
            h = static_cast<float>(PyFloat_AsDouble(PyTuple_GetItem(size_obj, 1)));
            self->data->setSize(w, h);
        } else {
            PyErr_SetString(PyExc_TypeError, "size must be a tuple (width, height)");
            return -1;
        }
    }

    // Render resolution
    if (render_res_obj && render_res_obj != Py_None) {
        int rw, rh;
        if (PyTuple_Check(render_res_obj) && PyTuple_Size(render_res_obj) == 2) {
            rw = static_cast<int>(PyLong_AsLong(PyTuple_GetItem(render_res_obj, 0)));
            rh = static_cast<int>(PyLong_AsLong(PyTuple_GetItem(render_res_obj, 1)));
            self->data->setInternalResolution(rw, rh);
        }
    }

    // FOV
    self->data->getCamera().setFOV(fov);

    // Camera position
    if (camera_pos_obj && camera_pos_obj != Py_None) {
        mcrf::vec3 cam_pos;
        if (PyTuple_GetVec3(camera_pos_obj, cam_pos)) {
            self->data->setCameraPosition(cam_pos);
        }
    }

    // Camera target
    if (camera_target_obj && camera_target_obj != Py_None) {
        mcrf::vec3 cam_target;
        if (PyTuple_GetVec3(camera_target_obj, cam_target)) {
            self->data->setCameraTarget(cam_target);
        }
    }

    // Background color
    if (bg_color_obj && bg_color_obj != Py_None) {
        sf::Color bg = PyColor::fromPy(bg_color_obj);
        if (!PyErr_Occurred()) {
            self->data->setBackgroundColor(bg);
        }
    }

    // PS1 effects
    self->data->setVertexSnapEnabled(enable_vertex_snap);
    self->data->setAffineMappingEnabled(enable_affine);
    self->data->setDitheringEnabled(enable_dither);
    self->data->setFogEnabled(enable_fog);

    // Fog color
    if (fog_color_obj && fog_color_obj != Py_None) {
        sf::Color fc = PyColor::fromPy(fog_color_obj);
        if (!PyErr_Occurred()) {
            self->data->setFogColor(fc);
        }
    }

    // Fog range
    self->data->setFogRange(fog_near, fog_far);

    // Common properties
    self->data->visible = visible;
    self->data->z_index = z_index;
    if (name) {
        self->data->name = name;
    }

    // Register in Python object cache for scene explorer repr
    if (self->data->serial_number == 0) {
        self->data->serial_number = PythonObjectCache::getInstance().assignSerial();
        PyObject* weakref = PyWeakref_NewRef((PyObject*)self, NULL);
        if (weakref) {
            PythonObjectCache::getInstance().registerObject(self->data->serial_number, weakref);
            Py_DECREF(weakref);  // Cache owns the reference now
        }
    }

    // Check if this is a Python subclass (for callback method support)
    PyObject* viewport3d_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "Viewport3D");
    if (viewport3d_type) {
        self->data->is_python_subclass = (PyObject*)Py_TYPE(self) != viewport3d_type;
        Py_DECREF(viewport3d_type);
    }

    return 0;
}

// =============================================================================
// Python Methods for Layer Management
// =============================================================================

static PyObject* Viewport3D_add_layer(PyViewport3DObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"name", "z_index", NULL};
    const char* name = nullptr;
    int z_index = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "s|i", const_cast<char**>(kwlist), &name, &z_index)) {
        return NULL;
    }

    auto layer = self->data->addLayer(name, z_index);
    if (!layer) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to create layer");
        return NULL;
    }

    // Return a dictionary with layer info (simple approach)
    // TODO: Create proper PyMeshLayer type for full API
    return Py_BuildValue("{s:s, s:i, s:i, s:n}",
        "name", layer->getName().c_str(),
        "z_index", layer->getZIndex(),
        "vertex_count", static_cast<int>(layer->getVertexCount()),
        "layer_ptr", reinterpret_cast<Py_ssize_t>(layer.get()));
}

static PyObject* Viewport3D_get_layer(PyViewport3DObject* self, PyObject* args) {
    const char* name = nullptr;
    if (!PyArg_ParseTuple(args, "s", &name)) {
        return NULL;
    }

    auto layer = self->data->getLayer(name);
    if (!layer) {
        Py_RETURN_NONE;
    }

    return Py_BuildValue("{s:s, s:i, s:i, s:n}",
        "name", layer->getName().c_str(),
        "z_index", layer->getZIndex(),
        "vertex_count", static_cast<int>(layer->getVertexCount()),
        "layer_ptr", reinterpret_cast<Py_ssize_t>(layer.get()));
}

static PyObject* Viewport3D_remove_layer(PyViewport3DObject* self, PyObject* args) {
    const char* name = nullptr;
    if (!PyArg_ParseTuple(args, "s", &name)) {
        return NULL;
    }

    bool removed = self->data->removeLayer(name);
    return PyBool_FromLong(removed);
}

static PyObject* Viewport3D_orbit_camera(PyViewport3DObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"angle", "distance", "height", NULL};
    float angle = 0.0f;
    float distance = 10.0f;
    float height = 5.0f;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|fff", const_cast<char**>(kwlist),
                                      &angle, &distance, &height)) {
        return NULL;
    }

    self->data->orbitCamera(angle, distance, height);
    Py_RETURN_NONE;
}

static PyObject* Viewport3D_build_terrain(PyViewport3DObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"layer_name", "heightmap", "y_scale", "cell_size", NULL};
    const char* layer_name = nullptr;
    PyObject* heightmap_obj = nullptr;
    float y_scale = 1.0f;
    float cell_size = 1.0f;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "sO|ff", const_cast<char**>(kwlist),
                                      &layer_name, &heightmap_obj, &y_scale, &cell_size)) {
        return NULL;
    }

    // Get or create the layer
    auto layer = self->data->getLayer(layer_name);
    if (!layer) {
        layer = self->data->addLayer(layer_name, 0);
    }

    // Check if heightmap_obj is a PyHeightMapObject
    // Get the HeightMap type from the module
    PyObject* heightmap_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "HeightMap");
    if (!heightmap_type) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap type not found");
        return NULL;
    }

    if (!PyObject_IsInstance(heightmap_obj, heightmap_type)) {
        Py_DECREF(heightmap_type);
        PyErr_SetString(PyExc_TypeError, "heightmap must be a HeightMap object");
        return NULL;
    }
    Py_DECREF(heightmap_type);

    // Get the TCOD heightmap pointer from the Python object
    PyHeightMapObject* hm = reinterpret_cast<PyHeightMapObject*>(heightmap_obj);
    if (!hm->heightmap) {
        PyErr_SetString(PyExc_ValueError, "HeightMap has no data");
        return NULL;
    }

    // Build the terrain mesh
    layer->buildFromHeightmap(hm->heightmap, y_scale, cell_size);

    return Py_BuildValue("i", static_cast<int>(layer->getVertexCount()));
}

static PyObject* Viewport3D_apply_terrain_colors(PyViewport3DObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"layer_name", "r_map", "g_map", "b_map", NULL};
    const char* layer_name = nullptr;
    PyObject* r_obj = nullptr;
    PyObject* g_obj = nullptr;
    PyObject* b_obj = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "sOOO", const_cast<char**>(kwlist),
                                      &layer_name, &r_obj, &g_obj, &b_obj)) {
        return NULL;
    }

    // Get the layer
    auto layer = self->data->getLayer(layer_name);
    if (!layer) {
        PyErr_Format(PyExc_ValueError, "Layer '%s' not found", layer_name);
        return NULL;
    }

    // Validate all three are HeightMap objects
    PyObject* heightmap_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "HeightMap");
    if (!heightmap_type) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap type not found");
        return NULL;
    }

    if (!PyObject_IsInstance(r_obj, heightmap_type) ||
        !PyObject_IsInstance(g_obj, heightmap_type) ||
        !PyObject_IsInstance(b_obj, heightmap_type)) {
        Py_DECREF(heightmap_type);
        PyErr_SetString(PyExc_TypeError, "r_map, g_map, and b_map must all be HeightMap objects");
        return NULL;
    }
    Py_DECREF(heightmap_type);

    // Get the TCOD heightmap pointers
    PyHeightMapObject* r_hm = reinterpret_cast<PyHeightMapObject*>(r_obj);
    PyHeightMapObject* g_hm = reinterpret_cast<PyHeightMapObject*>(g_obj);
    PyHeightMapObject* b_hm = reinterpret_cast<PyHeightMapObject*>(b_obj);

    if (!r_hm->heightmap || !g_hm->heightmap || !b_hm->heightmap) {
        PyErr_SetString(PyExc_ValueError, "One or more HeightMap objects have no data");
        return NULL;
    }

    // Apply the color map
    layer->applyColorMap(r_hm->heightmap, g_hm->heightmap, b_hm->heightmap);

    Py_RETURN_NONE;
}

static PyObject* Viewport3D_layer_count(PyViewport3DObject* self, PyObject* Py_UNUSED(args)) {
    return PyLong_FromSize_t(self->data->getLayerCount());
}

// =============================================================================
// Navigation Grid Python Methods
// =============================================================================

static PyObject* Viewport3D_set_grid_size(PyViewport3DObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"width", "depth", NULL};
    int width = 0;
    int depth = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "ii", const_cast<char**>(kwlist),
                                      &width, &depth)) {
        return NULL;
    }

    try {
        self->data->setGridSize(width, depth);
    } catch (const std::exception& e) {
        PyErr_SetString(PyExc_ValueError, e.what());
        return NULL;
    }

    Py_RETURN_NONE;
}

static PyObject* Viewport3D_at(PyViewport3DObject* self, PyObject* args) {
    int x, z;

    if (!PyArg_ParseTuple(args, "ii", &x, &z)) {
        return NULL;
    }

    if (!self->data->isValidCell(x, z)) {
        PyErr_Format(PyExc_IndexError, "Grid coordinates (%d, %d) out of range", x, z);
        return NULL;
    }

    // Create Python VoxelPoint wrapper using tp_alloc to properly construct shared_ptr
    auto type = &mcrfpydef::PyVoxelPointType;
    auto vp_obj = (PyVoxelPointObject*)type->tp_alloc(type, 0);
    if (!vp_obj) {
        return NULL;
    }

    vp_obj->data = &(self->data->at(x, z));
    vp_obj->viewport = self->data;

    return (PyObject*)vp_obj;
}

static PyObject* Viewport3D_apply_heightmap(PyViewport3DObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"heightmap", "y_scale", NULL};
    PyObject* hm_obj = nullptr;
    float y_scale = 1.0f;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|f", const_cast<char**>(kwlist),
                                      &hm_obj, &y_scale)) {
        return NULL;
    }

    // Validate HeightMap type
    PyObject* heightmap_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "HeightMap");
    if (!heightmap_type) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap type not found");
        return NULL;
    }

    if (!PyObject_IsInstance(hm_obj, heightmap_type)) {
        Py_DECREF(heightmap_type);
        PyErr_SetString(PyExc_TypeError, "heightmap must be a HeightMap object");
        return NULL;
    }
    Py_DECREF(heightmap_type);

    PyHeightMapObject* hm = reinterpret_cast<PyHeightMapObject*>(hm_obj);
    if (!hm->heightmap) {
        PyErr_SetString(PyExc_ValueError, "HeightMap has no data");
        return NULL;
    }

    self->data->applyHeightmap(hm->heightmap, y_scale);
    Py_RETURN_NONE;
}

static PyObject* Viewport3D_apply_threshold(PyViewport3DObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"heightmap", "min_height", "max_height", "walkable", NULL};
    PyObject* hm_obj = nullptr;
    float min_height = 0.0f;
    float max_height = 1.0f;
    int walkable = 1;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "Off|p", const_cast<char**>(kwlist),
                                      &hm_obj, &min_height, &max_height, &walkable)) {
        return NULL;
    }

    // Validate HeightMap type
    PyObject* heightmap_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "HeightMap");
    if (!heightmap_type) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap type not found");
        return NULL;
    }

    if (!PyObject_IsInstance(hm_obj, heightmap_type)) {
        Py_DECREF(heightmap_type);
        PyErr_SetString(PyExc_TypeError, "heightmap must be a HeightMap object");
        return NULL;
    }
    Py_DECREF(heightmap_type);

    PyHeightMapObject* hm = reinterpret_cast<PyHeightMapObject*>(hm_obj);
    if (!hm->heightmap) {
        PyErr_SetString(PyExc_ValueError, "HeightMap has no data");
        return NULL;
    }

    self->data->applyThreshold(hm->heightmap, min_height, max_height, walkable != 0);
    Py_RETURN_NONE;
}

static PyObject* Viewport3D_set_slope_cost(PyViewport3DObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"max_slope", "cost_multiplier", NULL};
    float max_slope = 0.5f;
    float cost_multiplier = 1.0f;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|ff", const_cast<char**>(kwlist),
                                      &max_slope, &cost_multiplier)) {
        return NULL;
    }

    self->data->setSlopeCost(max_slope, cost_multiplier);
    Py_RETURN_NONE;
}

static PyObject* Viewport3D_find_path(PyViewport3DObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"start", "end", NULL};
    PyObject* start_obj = nullptr;
    PyObject* end_obj = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO", const_cast<char**>(kwlist),
                                      &start_obj, &end_obj)) {
        return NULL;
    }

    // Parse start tuple
    int start_x, start_z;
    if (!PyArg_ParseTuple(start_obj, "ii", &start_x, &start_z)) {
        PyErr_SetString(PyExc_TypeError, "start must be a tuple of (x, z) integers");
        return NULL;
    }

    // Parse end tuple
    int end_x, end_z;
    if (!PyArg_ParseTuple(end_obj, "ii", &end_x, &end_z)) {
        PyErr_SetString(PyExc_TypeError, "end must be a tuple of (x, z) integers");
        return NULL;
    }

    // Find path
    std::vector<std::pair<int, int>> path = self->data->findPath(start_x, start_z, end_x, end_z);

    // Convert to Python list
    PyObject* result = PyList_New(path.size());
    if (!result) {
        return NULL;
    }

    for (size_t i = 0; i < path.size(); i++) {
        PyObject* tuple = Py_BuildValue("(ii)", path[i].first, path[i].second);
        if (!tuple) {
            Py_DECREF(result);
            return NULL;
        }
        PyList_SET_ITEM(result, i, tuple);
    }

    return result;
}

static PyObject* Viewport3D_compute_fov(PyViewport3DObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"origin", "radius", NULL};
    PyObject* origin_obj = nullptr;
    int radius = 10;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|i", const_cast<char**>(kwlist),
                                      &origin_obj, &radius)) {
        return NULL;
    }

    // Parse origin tuple
    int origin_x, origin_z;
    if (!PyArg_ParseTuple(origin_obj, "ii", &origin_x, &origin_z)) {
        PyErr_SetString(PyExc_TypeError, "origin must be a tuple of (x, z) integers");
        return NULL;
    }

    // Compute FOV
    std::vector<std::pair<int, int>> visible = self->data->computeFOV(origin_x, origin_z, radius);

    // Convert to Python list
    PyObject* result = PyList_New(visible.size());
    if (!result) {
        return NULL;
    }

    for (size_t i = 0; i < visible.size(); i++) {
        PyObject* tuple = Py_BuildValue("(ii)", visible[i].first, visible[i].second);
        if (!tuple) {
            Py_DECREF(result);
            return NULL;
        }
        PyList_SET_ITEM(result, i, tuple);
    }

    return result;
}

static PyObject* Viewport3D_is_in_fov(PyViewport3DObject* self, PyObject* args) {
    int x, z;

    if (!PyArg_ParseTuple(args, "ii", &x, &z)) {
        return NULL;
    }

    return PyBool_FromLong(self->data->isInFOV(x, z));
}

// =============================================================================
// Mesh Instance Methods (Milestone 6)
// =============================================================================

static PyObject* Viewport3D_add_mesh(PyViewport3DObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"layer_name", "model", "pos", "rotation", "scale", NULL};

    const char* layerName = nullptr;
    PyObject* modelObj = nullptr;
    PyObject* posObj = nullptr;
    float rotation = 0.0f;
    float scale = 1.0f;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "sOO|ff", const_cast<char**>(kwlist),
                                     &layerName, &modelObj, &posObj, &rotation, &scale)) {
        return NULL;
    }

    // Validate model
    if (!PyObject_IsInstance(modelObj, (PyObject*)&mcrfpydef::PyModel3DType)) {
        PyErr_SetString(PyExc_TypeError, "model must be a Model3D object");
        return NULL;
    }
    PyModel3DObject* modelPy = (PyModel3DObject*)modelObj;
    if (!modelPy->data) {
        PyErr_SetString(PyExc_ValueError, "model is invalid");
        return NULL;
    }

    // Parse position
    if (!PyTuple_Check(posObj) || PyTuple_Size(posObj) < 3) {
        PyErr_SetString(PyExc_TypeError, "pos must be a tuple of (x, y, z)");
        return NULL;
    }
    float px = static_cast<float>(PyFloat_AsDouble(PyTuple_GetItem(posObj, 0)));
    float py = static_cast<float>(PyFloat_AsDouble(PyTuple_GetItem(posObj, 1)));
    float pz = static_cast<float>(PyFloat_AsDouble(PyTuple_GetItem(posObj, 2)));
    if (PyErr_Occurred()) return NULL;

    // Get or create layer
    auto layer = self->data->getLayer(layerName);
    if (!layer) {
        layer = self->data->addLayer(layerName, 0);
    }

    // Add mesh instance
    size_t index = layer->addMesh(modelPy->data, vec3(px, py, pz), rotation, vec3(scale, scale, scale));

    return PyLong_FromSize_t(index);
}

static PyObject* Viewport3D_place_blocking(PyViewport3DObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"grid_pos", "footprint", "walkable", "transparent", NULL};

    PyObject* gridPosObj = nullptr;
    PyObject* footprintObj = nullptr;
    int walkable = 0;  // Default: not walkable
    int transparent = 0;  // Default: not transparent

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO|pp", const_cast<char**>(kwlist),
                                     &gridPosObj, &footprintObj, &walkable, &transparent)) {
        return NULL;
    }

    // Parse grid_pos
    if (!PyTuple_Check(gridPosObj) || PyTuple_Size(gridPosObj) < 2) {
        PyErr_SetString(PyExc_TypeError, "grid_pos must be a tuple of (x, z)");
        return NULL;
    }
    int gridX = static_cast<int>(PyLong_AsLong(PyTuple_GetItem(gridPosObj, 0)));
    int gridZ = static_cast<int>(PyLong_AsLong(PyTuple_GetItem(gridPosObj, 1)));
    if (PyErr_Occurred()) return NULL;

    // Parse footprint
    if (!PyTuple_Check(footprintObj) || PyTuple_Size(footprintObj) < 2) {
        PyErr_SetString(PyExc_TypeError, "footprint must be a tuple of (width, depth)");
        return NULL;
    }
    int footW = static_cast<int>(PyLong_AsLong(PyTuple_GetItem(footprintObj, 0)));
    int footD = static_cast<int>(PyLong_AsLong(PyTuple_GetItem(footprintObj, 1)));
    if (PyErr_Occurred()) return NULL;

    // Mark cells
    for (int dz = 0; dz < footD; dz++) {
        for (int dx = 0; dx < footW; dx++) {
            int cx = gridX + dx;
            int cz = gridZ + dz;
            if (self->data->isValidCell(cx, cz)) {
                VoxelPoint& cell = self->data->at(cx, cz);
                cell.walkable = walkable != 0;
                cell.transparent = transparent != 0;
                self->data->syncTCODCell(cx, cz);
            }
        }
    }

    Py_RETURN_NONE;
}

static PyObject* Viewport3D_clear_meshes(PyViewport3DObject* self, PyObject* args) {
    const char* layerName = nullptr;

    if (!PyArg_ParseTuple(args, "s", &layerName)) {
        return NULL;
    }

    auto layer = self->data->getLayer(layerName);
    if (!layer) {
        PyErr_SetString(PyExc_ValueError, "Layer not found");
        return NULL;
    }

    layer->clearMeshes();
    Py_RETURN_NONE;
}

// =============================================================================
// Billboard Management Methods
// =============================================================================

static PyObject* Viewport3D_add_billboard(PyViewport3DObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"billboard", NULL};

    PyObject* billboardObj = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O", const_cast<char**>(kwlist), &billboardObj)) {
        return NULL;
    }

    // Check if it's a Billboard object
    if (!PyObject_IsInstance(billboardObj, (PyObject*)&mcrfpydef::PyBillboardType)) {
        PyErr_SetString(PyExc_TypeError, "Expected a Billboard object");
        return NULL;
    }

    PyBillboardObject* bbObj = (PyBillboardObject*)billboardObj;
    if (!bbObj->data) {
        PyErr_SetString(PyExc_ValueError, "Invalid Billboard object");
        return NULL;
    }

    self->data->addBillboard(bbObj->data);
    Py_RETURN_NONE;
}

static PyObject* Viewport3D_remove_billboard(PyViewport3DObject* self, PyObject* args) {
    PyObject* billboardObj = nullptr;

    if (!PyArg_ParseTuple(args, "O", &billboardObj)) {
        return NULL;
    }

    if (!PyObject_IsInstance(billboardObj, (PyObject*)&mcrfpydef::PyBillboardType)) {
        PyErr_SetString(PyExc_TypeError, "Expected a Billboard object");
        return NULL;
    }

    PyBillboardObject* bbObj = (PyBillboardObject*)billboardObj;
    if (bbObj->data) {
        self->data->removeBillboard(bbObj->data.get());
    }
    Py_RETURN_NONE;
}

static PyObject* Viewport3D_clear_billboards(PyViewport3DObject* self, PyObject* args) {
    self->data->clearBillboards();
    Py_RETURN_NONE;
}

static PyObject* Viewport3D_get_billboard(PyViewport3DObject* self, PyObject* args) {
    int index = 0;

    if (!PyArg_ParseTuple(args, "i", &index)) {
        return NULL;
    }

    auto billboards = self->data->getBillboards();
    if (index < 0 || index >= static_cast<int>(billboards->size())) {
        PyErr_SetString(PyExc_IndexError, "Billboard index out of range");
        return NULL;
    }

    auto bb = (*billboards)[index];

    // Create Python wrapper for billboard
    auto type = &mcrfpydef::PyBillboardType;
    auto obj = (PyBillboardObject*)type->tp_alloc(type, 0);
    if (!obj) return NULL;

    obj->data = bb;
    obj->weakreflist = nullptr;

    return (PyObject*)obj;
}

static PyObject* Viewport3D_billboard_count(PyViewport3DObject* self, PyObject* args) {
    auto billboards = self->data->getBillboards();
    return PyLong_FromLong(static_cast<long>(billboards->size()));
}

// =============================================================================
// Camera & Input Methods (Milestone 8)
// =============================================================================

static PyObject* Viewport3D_screen_to_world(PyViewport3DObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"x", "y", NULL};

    float x = 0.0f, y = 0.0f;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "ff", const_cast<char**>(kwlist), &x, &y)) {
        return NULL;
    }

    // Adjust for viewport position (user passes screen coords relative to viewport)
    vec3 worldPos = self->data->screenToWorld(x, y);

    // Return None if no intersection (ray parallel to ground or invalid)
    if (worldPos.x < 0 && worldPos.y < 0 && worldPos.z < 0) {
        Py_RETURN_NONE;
    }

    return Py_BuildValue("(fff)", worldPos.x, worldPos.y, worldPos.z);
}

static PyObject* Viewport3D_follow(PyViewport3DObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"entity", "distance", "height", "smoothing", NULL};

    PyObject* entityObj = nullptr;
    float distance = 10.0f;
    float height = 5.0f;
    float smoothing = 1.0f;  // Default to instant (for single-call positioning)

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|fff", const_cast<char**>(kwlist),
                                     &entityObj, &distance, &height, &smoothing)) {
        return NULL;
    }

    // Check if it's an Entity3D object
    if (!PyObject_IsInstance(entityObj, (PyObject*)&mcrfpydef::PyEntity3DType)) {
        PyErr_SetString(PyExc_TypeError, "Expected an Entity3D object");
        return NULL;
    }

    PyEntity3DObject* entObj = (PyEntity3DObject*)entityObj;
    if (!entObj->data) {
        PyErr_SetString(PyExc_ValueError, "Invalid Entity3D object");
        return NULL;
    }

    self->data->followEntity(entObj->data, distance, height, smoothing);
    Py_RETURN_NONE;
}

// =============================================================================
// Voxel Layer Methods (Milestone 10)
// =============================================================================

static PyObject* Viewport3D_add_voxel_layer(PyViewport3DObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"voxel_grid", "z_index", NULL};
    PyObject* voxel_grid_obj = nullptr;
    int z_index = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|i", const_cast<char**>(kwlist),
                                      &voxel_grid_obj, &z_index)) {
        return NULL;
    }

    // Check if it's a VoxelGrid object
    PyTypeObject* voxelGridType = (PyTypeObject*)PyObject_GetAttrString(
        McRFPy_API::mcrf_module, "VoxelGrid");
    if (!voxelGridType) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid type not found");
        return NULL;
    }

    if (!PyObject_IsInstance(voxel_grid_obj, (PyObject*)voxelGridType)) {
        Py_DECREF(voxelGridType);
        PyErr_SetString(PyExc_TypeError, "voxel_grid must be a VoxelGrid object");
        return NULL;
    }
    Py_DECREF(voxelGridType);

    PyVoxelGridObject* vg = (PyVoxelGridObject*)voxel_grid_obj;
    if (!vg->data) {
        PyErr_SetString(PyExc_ValueError, "VoxelGrid not initialized");
        return NULL;
    }

    self->data->addVoxelLayer(vg->data, z_index);
    Py_RETURN_NONE;
}

static PyObject* Viewport3D_remove_voxel_layer(PyViewport3DObject* self, PyObject* args) {
    PyObject* voxel_grid_obj = nullptr;

    if (!PyArg_ParseTuple(args, "O", &voxel_grid_obj)) {
        return NULL;
    }

    // Check if it's a VoxelGrid object
    PyTypeObject* voxelGridType = (PyTypeObject*)PyObject_GetAttrString(
        McRFPy_API::mcrf_module, "VoxelGrid");
    if (!voxelGridType) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid type not found");
        return NULL;
    }

    if (!PyObject_IsInstance(voxel_grid_obj, (PyObject*)voxelGridType)) {
        Py_DECREF(voxelGridType);
        PyErr_SetString(PyExc_TypeError, "voxel_grid must be a VoxelGrid object");
        return NULL;
    }
    Py_DECREF(voxelGridType);

    PyVoxelGridObject* vg = (PyVoxelGridObject*)voxel_grid_obj;
    if (!vg->data) {
        PyErr_SetString(PyExc_ValueError, "VoxelGrid not initialized");
        return NULL;
    }

    bool removed = self->data->removeVoxelLayer(vg->data);
    return PyBool_FromLong(removed);
}

static PyObject* Viewport3D_voxel_layer_count(PyViewport3DObject* self, PyObject* Py_UNUSED(args)) {
    return PyLong_FromSize_t(self->data->getVoxelLayerCount());
}

// =============================================================================
// Voxel-to-Nav Projection Methods (Milestone 12)
// =============================================================================

static PyObject* Viewport3D_project_voxel_to_nav(PyViewport3DObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"voxel_grid", "headroom", NULL};
    PyObject* voxel_grid_obj = nullptr;
    int headroom = 2;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|i", const_cast<char**>(kwlist),
                                      &voxel_grid_obj, &headroom)) {
        return NULL;
    }

    // Check if it's a VoxelGrid object
    PyTypeObject* voxelGridType = (PyTypeObject*)PyObject_GetAttrString(
        McRFPy_API::mcrf_module, "VoxelGrid");
    if (!voxelGridType) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid type not found");
        return NULL;
    }

    if (!PyObject_IsInstance(voxel_grid_obj, (PyObject*)voxelGridType)) {
        Py_DECREF(voxelGridType);
        PyErr_SetString(PyExc_TypeError, "voxel_grid must be a VoxelGrid object");
        return NULL;
    }
    Py_DECREF(voxelGridType);

    PyVoxelGridObject* vg = (PyVoxelGridObject*)voxel_grid_obj;
    if (!vg->data) {
        PyErr_SetString(PyExc_ValueError, "VoxelGrid not initialized");
        return NULL;
    }

    if (headroom < 0) {
        PyErr_SetString(PyExc_ValueError, "headroom must be non-negative");
        return NULL;
    }

    self->data->projectVoxelToNav(vg->data, headroom);
    Py_RETURN_NONE;
}

static PyObject* Viewport3D_project_all_voxels_to_nav(PyViewport3DObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"headroom", NULL};
    int headroom = 2;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|i", const_cast<char**>(kwlist), &headroom)) {
        return NULL;
    }

    if (headroom < 0) {
        PyErr_SetString(PyExc_ValueError, "headroom must be non-negative");
        return NULL;
    }

    self->data->projectAllVoxelsToNav(headroom);
    Py_RETURN_NONE;
}

static PyObject* Viewport3D_clear_voxel_nav_region(PyViewport3DObject* self, PyObject* args) {
    PyObject* voxel_grid_obj = nullptr;

    if (!PyArg_ParseTuple(args, "O", &voxel_grid_obj)) {
        return NULL;
    }

    // Check if it's a VoxelGrid object
    PyTypeObject* voxelGridType = (PyTypeObject*)PyObject_GetAttrString(
        McRFPy_API::mcrf_module, "VoxelGrid");
    if (!voxelGridType) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid type not found");
        return NULL;
    }

    if (!PyObject_IsInstance(voxel_grid_obj, (PyObject*)voxelGridType)) {
        Py_DECREF(voxelGridType);
        PyErr_SetString(PyExc_TypeError, "voxel_grid must be a VoxelGrid object");
        return NULL;
    }
    Py_DECREF(voxelGridType);

    PyVoxelGridObject* vg = (PyVoxelGridObject*)voxel_grid_obj;
    if (!vg->data) {
        PyErr_SetString(PyExc_ValueError, "VoxelGrid not initialized");
        return NULL;
    }

    self->data->clearVoxelNavRegion(vg->data);
    Py_RETURN_NONE;
}

} // namespace mcrf

// Methods array - outside namespace but PyObjectType still in scope via typedef
typedef PyViewport3DObject PyObjectType;

PyMethodDef Viewport3D_methods[] = {
    UIDRAWABLE_METHODS,
    {"add_layer", (PyCFunction)mcrf::Viewport3D_add_layer, METH_VARARGS | METH_KEYWORDS,
     "add_layer(name, z_index=0) -> dict\n\n"
     "Add a new mesh layer to the viewport.\n\n"
     "Args:\n"
     "    name: Unique identifier for the layer\n"
     "    z_index: Render order (lower = rendered first)"},
    {"get_layer", (PyCFunction)mcrf::Viewport3D_get_layer, METH_VARARGS,
     "get_layer(name) -> dict or None\n\n"
     "Get a layer by name."},
    {"remove_layer", (PyCFunction)mcrf::Viewport3D_remove_layer, METH_VARARGS,
     "remove_layer(name) -> bool\n\n"
     "Remove a layer by name. Returns True if found and removed."},
    {"orbit_camera", (PyCFunction)mcrf::Viewport3D_orbit_camera, METH_VARARGS | METH_KEYWORDS,
     "orbit_camera(angle=0, distance=10, height=5)\n\n"
     "Position camera to orbit around origin.\n\n"
     "Args:\n"
     "    angle: Orbit angle in radians\n"
     "    distance: Distance from origin\n"
     "    height: Camera height above XZ plane"},
    {"build_terrain", (PyCFunction)mcrf::Viewport3D_build_terrain, METH_VARARGS | METH_KEYWORDS,
     "build_terrain(layer_name, heightmap, y_scale=1.0, cell_size=1.0) -> int\n\n"
     "Build terrain mesh from HeightMap on specified layer.\n\n"
     "Args:\n"
     "    layer_name: Name of layer to build terrain on (created if doesn't exist)\n"
     "    heightmap: HeightMap object with height data\n"
     "    y_scale: Vertical exaggeration factor\n"
     "    cell_size: World-space size of each grid cell\n\n"
     "Returns:\n"
     "    Number of vertices in the generated mesh"},
    {"apply_terrain_colors", (PyCFunction)mcrf::Viewport3D_apply_terrain_colors, METH_VARARGS | METH_KEYWORDS,
     "apply_terrain_colors(layer_name, r_map, g_map, b_map)\n\n"
     "Apply per-vertex colors to terrain from RGB HeightMaps.\n\n"
     "Args:\n"
     "    layer_name: Name of terrain layer to colorize\n"
     "    r_map: HeightMap for red channel (0-1 values)\n"
     "    g_map: HeightMap for green channel (0-1 values)\n"
     "    b_map: HeightMap for blue channel (0-1 values)\n\n"
     "All HeightMaps must match the terrain's original dimensions."},
    {"layer_count", (PyCFunction)mcrf::Viewport3D_layer_count, METH_NOARGS,
     "layer_count() -> int\n\n"
     "Get the number of mesh layers."},

    // Navigation grid methods
    {"set_grid_size", (PyCFunction)mcrf::Viewport3D_set_grid_size, METH_VARARGS | METH_KEYWORDS,
     "set_grid_size(width, depth)\n\n"
     "Initialize navigation grid with specified dimensions.\n\n"
     "Args:\n"
     "    width: Grid width (X axis)\n"
     "    depth: Grid depth (Z axis)"},
    {"at", (PyCFunction)mcrf::Viewport3D_at, METH_VARARGS,
     "at(x, z) -> VoxelPoint\n\n"
     "Get VoxelPoint at grid coordinates.\n\n"
     "Args:\n"
     "    x: X coordinate in grid\n"
     "    z: Z coordinate in grid\n\n"
     "Returns:\n"
     "    VoxelPoint object for the cell"},
    {"apply_heightmap", (PyCFunction)mcrf::Viewport3D_apply_heightmap, METH_VARARGS | METH_KEYWORDS,
     "apply_heightmap(heightmap, y_scale=1.0)\n\n"
     "Set cell heights from HeightMap.\n\n"
     "Args:\n"
     "    heightmap: HeightMap object\n"
     "    y_scale: Vertical scale factor"},
    {"apply_threshold", (PyCFunction)mcrf::Viewport3D_apply_threshold, METH_VARARGS | METH_KEYWORDS,
     "apply_threshold(heightmap, min_height, max_height, walkable=True)\n\n"
     "Set cell walkability based on height thresholds.\n\n"
     "Args:\n"
     "    heightmap: HeightMap object\n"
     "    min_height: Minimum height (0-1)\n"
     "    max_height: Maximum height (0-1)\n"
     "    walkable: Walkability value for cells in range"},
    {"set_slope_cost", (PyCFunction)mcrf::Viewport3D_set_slope_cost, METH_VARARGS | METH_KEYWORDS,
     "set_slope_cost(max_slope=0.5, cost_multiplier=1.0)\n\n"
     "Calculate slope costs and mark steep cells unwalkable.\n\n"
     "Args:\n"
     "    max_slope: Maximum height difference before marking unwalkable\n"
     "    cost_multiplier: Cost increase per unit slope"},
    {"find_path", (PyCFunction)mcrf::Viewport3D_find_path, METH_VARARGS | METH_KEYWORDS,
     "find_path(start, end) -> list\n\n"
     "Find A* path between two points.\n\n"
     "Args:\n"
     "    start: Starting point as (x, z) tuple\n"
     "    end: End point as (x, z) tuple\n\n"
     "Returns:\n"
     "    List of (x, z) tuples forming the path, or empty list if no path"},
    {"compute_fov", (PyCFunction)mcrf::Viewport3D_compute_fov, METH_VARARGS | METH_KEYWORDS,
     "compute_fov(origin, radius=10) -> list\n\n"
     "Compute field of view from a position.\n\n"
     "Args:\n"
     "    origin: Origin point as (x, z) tuple\n"
     "    radius: FOV radius\n\n"
     "Returns:\n"
     "    List of visible (x, z) positions"},
    {"is_in_fov", (PyCFunction)mcrf::Viewport3D_is_in_fov, METH_VARARGS,
     "is_in_fov(x, z) -> bool\n\n"
     "Check if a cell is in the current FOV (after compute_fov).\n\n"
     "Args:\n"
     "    x: X coordinate\n"
     "    z: Z coordinate\n\n"
     "Returns:\n"
     "    True if the cell is visible"},

    // Mesh instance methods (Milestone 6)
    {"add_mesh", (PyCFunction)mcrf::Viewport3D_add_mesh, METH_VARARGS | METH_KEYWORDS,
     "add_mesh(layer_name, model, pos, rotation=0, scale=1.0) -> int\n\n"
     "Add a Model3D instance to a layer at the specified position.\n\n"
     "Args:\n"
     "    layer_name: Name of layer to add mesh to (created if needed)\n"
     "    model: Model3D object to place\n"
     "    pos: World position as (x, y, z) tuple\n"
     "    rotation: Y-axis rotation in degrees\n"
     "    scale: Uniform scale factor\n\n"
     "Returns:\n"
     "    Index of the mesh instance"},
    {"place_blocking", (PyCFunction)mcrf::Viewport3D_place_blocking, METH_VARARGS | METH_KEYWORDS,
     "place_blocking(grid_pos, footprint, walkable=False, transparent=False)\n\n"
     "Mark grid cells as blocking for pathfinding and FOV.\n\n"
     "Args:\n"
     "    grid_pos: Top-left grid position as (x, z) tuple\n"
     "    footprint: Size in cells as (width, depth) tuple\n"
     "    walkable: Whether cells should be walkable (default: False)\n"
     "    transparent: Whether cells should be transparent (default: False)"},
    {"clear_meshes", (PyCFunction)mcrf::Viewport3D_clear_meshes, METH_VARARGS,
     "clear_meshes(layer_name)\n\n"
     "Clear all mesh instances from a layer.\n\n"
     "Args:\n"
     "    layer_name: Name of layer to clear"},

    // Billboard methods (Milestone 6)
    {"add_billboard", (PyCFunction)mcrf::Viewport3D_add_billboard, METH_VARARGS | METH_KEYWORDS,
     "add_billboard(billboard)\n\n"
     "Add a Billboard to the viewport.\n\n"
     "Args:\n"
     "    billboard: Billboard object to add"},
    {"remove_billboard", (PyCFunction)mcrf::Viewport3D_remove_billboard, METH_VARARGS,
     "remove_billboard(billboard)\n\n"
     "Remove a Billboard from the viewport.\n\n"
     "Args:\n"
     "    billboard: Billboard object to remove"},
    {"clear_billboards", (PyCFunction)mcrf::Viewport3D_clear_billboards, METH_NOARGS,
     "clear_billboards()\n\n"
     "Remove all billboards from the viewport."},
    {"get_billboard", (PyCFunction)mcrf::Viewport3D_get_billboard, METH_VARARGS,
     "get_billboard(index) -> Billboard\n\n"
     "Get a Billboard by index.\n\n"
     "Args:\n"
     "    index: Index of the billboard\n\n"
     "Returns:\n"
     "    Billboard object"},
    {"billboard_count", (PyCFunction)mcrf::Viewport3D_billboard_count, METH_NOARGS,
     "billboard_count() -> int\n\n"
     "Get the number of billboards.\n\n"
     "Returns:\n"
     "    Number of billboards in the viewport"},

    // Camera & Input methods (Milestone 8)
    {"screen_to_world", (PyCFunction)mcrf::Viewport3D_screen_to_world, METH_VARARGS | METH_KEYWORDS,
     "screen_to_world(x, y) -> tuple or None\n\n"
     "Convert screen coordinates to world position via ray casting.\n\n"
     "Args:\n"
     "    x: Screen X coordinate relative to viewport\n"
     "    y: Screen Y coordinate relative to viewport\n\n"
     "Returns:\n"
     "    (x, y, z) world position tuple, or None if no intersection with ground plane"},
    {"follow", (PyCFunction)mcrf::Viewport3D_follow, METH_VARARGS | METH_KEYWORDS,
     "follow(entity, distance=10, height=5, smoothing=1.0)\n\n"
     "Position camera to follow an entity.\n\n"
     "Args:\n"
     "    entity: Entity3D to follow\n"
     "    distance: Distance behind entity\n"
     "    height: Camera height above entity\n"
     "    smoothing: Interpolation factor (0-1). 1 = instant, lower = smoother"},

    // Voxel layer methods (Milestone 10)
    {"add_voxel_layer", (PyCFunction)mcrf::Viewport3D_add_voxel_layer, METH_VARARGS | METH_KEYWORDS,
     "add_voxel_layer(voxel_grid, z_index=0)\n\n"
     "Add a VoxelGrid as a renderable layer.\n\n"
     "Args:\n"
     "    voxel_grid: VoxelGrid object to render\n"
     "    z_index: Render order (lower = rendered first)"},
    {"remove_voxel_layer", (PyCFunction)mcrf::Viewport3D_remove_voxel_layer, METH_VARARGS,
     "remove_voxel_layer(voxel_grid) -> bool\n\n"
     "Remove a VoxelGrid layer from the viewport.\n\n"
     "Args:\n"
     "    voxel_grid: VoxelGrid object to remove\n\n"
     "Returns:\n"
     "    True if the layer was found and removed"},
    {"voxel_layer_count", (PyCFunction)mcrf::Viewport3D_voxel_layer_count, METH_NOARGS,
     "voxel_layer_count() -> int\n\n"
     "Get the number of voxel layers.\n\n"
     "Returns:\n"
     "    Number of voxel layers in the viewport"},

    // Voxel-to-Nav projection methods (Milestone 12)
    {"project_voxel_to_nav", (PyCFunction)mcrf::Viewport3D_project_voxel_to_nav, METH_VARARGS | METH_KEYWORDS,
     "project_voxel_to_nav(voxel_grid, headroom=2)\n\n"
     "Project a VoxelGrid to the navigation grid.\n\n"
     "Scans each column of the voxel grid and updates corresponding\n"
     "navigation cells with walkability, transparency, height, and cost.\n\n"
     "Args:\n"
     "    voxel_grid: VoxelGrid to project\n"
     "    headroom: Required air voxels above floor for walkability (default: 2)"},
    {"project_all_voxels_to_nav", (PyCFunction)mcrf::Viewport3D_project_all_voxels_to_nav, METH_VARARGS | METH_KEYWORDS,
     "project_all_voxels_to_nav(headroom=2)\n\n"
     "Project all voxel layers to the navigation grid.\n\n"
     "Resets navigation grid and projects each voxel layer in z_index order.\n"
     "Later layers (higher z_index) overwrite earlier ones.\n\n"
     "Args:\n"
     "    headroom: Required air voxels above floor for walkability (default: 2)"},
    {"clear_voxel_nav_region", (PyCFunction)mcrf::Viewport3D_clear_voxel_nav_region, METH_VARARGS,
     "clear_voxel_nav_region(voxel_grid)\n\n"
     "Clear navigation cells in a voxel grid's footprint.\n\n"
     "Resets walkability, transparency, height, and cost to defaults\n"
     "for all nav cells corresponding to the voxel grid's XZ extent.\n\n"
     "Args:\n"
     "    voxel_grid: VoxelGrid whose nav region to clear"},
    {NULL}  // Sentinel
};
