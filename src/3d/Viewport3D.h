// Viewport3D.h - 3D rendering viewport for McRogueFace
// A UIDrawable that renders a 3D scene to an FBO and displays it

#pragma once

#include "Common.h"
#include "Python.h"
#include "structmember.h"
#include "UIDrawable.h"
#include "UIBase.h"
#include "PyDrawable.h"
#include "Math3D.h"
#include "Camera3D.h"
#include "VoxelPoint.h"
#include <memory>
#include <vector>
#include <list>
#include <algorithm>
#include <mutex>
#include <libtcod.h>

// Forward declaration
namespace mcrf {
class Entity3D;
}

namespace mcrf {

// Forward declarations
class Viewport3D;
class Shader3D;
class MeshLayer;
class Billboard;

} // namespace mcrf

// Python object struct
typedef struct {
    PyObject_HEAD
    std::shared_ptr<mcrf::Viewport3D> data;
    PyObject* weakreflist;
} PyViewport3DObject;

namespace mcrf {

// =============================================================================
// Viewport3D - 3D rendering viewport as a UIDrawable
// Renders 3D content to an FBO, then blits to screen at display size
// =============================================================================

class Viewport3D : public UIDrawable {
public:
    Viewport3D();
    Viewport3D(float x, float y, float width, float height);
    ~Viewport3D();

    // UIDrawable interface
    void render(sf::Vector2f offset, sf::RenderTarget& target) override final;
    PyObjectsEnum derived_type() override final;
    UIDrawable* click_at(sf::Vector2f point) override final;
    sf::FloatRect get_bounds() const override;
    void move(float dx, float dy) override;
    void resize(float w, float h) override;

    // Size (screen display size)
    void setSize(float width, float height);
    float getWidth() const { return size_.x; }
    float getHeight() const { return size_.y; }

    // Internal resolution (PS1 style: render at low res, upscale)
    void setInternalResolution(int width, int height);
    int getInternalWidth() const { return internalWidth_; }
    int getInternalHeight() const { return internalHeight_; }

    // Camera access
    Camera3D& getCamera() { return camera_; }
    const Camera3D& getCamera() const { return camera_; }

    // Camera convenience methods (exposed to Python)
    void setCameraPosition(const vec3& pos) { camera_.setPosition(pos); }
    void setCameraTarget(const vec3& target) { camera_.setTarget(target); }
    vec3 getCameraPosition() const { return camera_.getPosition(); }
    vec3 getCameraTarget() const { return camera_.getTarget(); }

    // Camera orbit helper for demos
    void orbitCamera(float angle, float distance, float height);

    /// Convert screen coordinates to world position via ray casting
    /// @param screenX X position relative to viewport
    /// @param screenY Y position relative to viewport
    /// @return World position on Y=0 plane, or (-1,-1,-1) if no intersection
    vec3 screenToWorld(float screenX, float screenY);

    /// Position camera to follow an entity
    /// @param entity Entity to follow
    /// @param distance Distance behind entity
    /// @param height Height above entity
    /// @param smoothing Interpolation factor (0-1, where 1 = instant)
    void followEntity(std::shared_ptr<Entity3D> entity, float distance, float height, float smoothing = 1.0f);

    // =========================================================================
    // Mesh Layer Management
    // =========================================================================

    /// Add a new mesh layer
    /// @param name Unique identifier for the layer
    /// @param zIndex Render order (lower = rendered first, behind higher values)
    /// @return Pointer to the new layer (owned by Viewport3D)
    std::shared_ptr<MeshLayer> addLayer(const std::string& name, int zIndex = 0);

    /// Get a layer by name
    /// @return Pointer to layer, or nullptr if not found
    std::shared_ptr<MeshLayer> getLayer(const std::string& name);

    /// Remove a layer by name
    /// @return true if layer was found and removed
    bool removeLayer(const std::string& name);

    /// Get all layers (read-only)
    const std::vector<std::shared_ptr<MeshLayer>>& getLayers() const { return meshLayers_; }

    /// Get number of layers
    size_t getLayerCount() const { return meshLayers_.size(); }

    // =========================================================================
    // Navigation Grid (VoxelPoint System)
    // =========================================================================

    /// Set navigation grid dimensions
    /// @param width Grid width (X axis)
    /// @param depth Grid depth (Z axis)
    void setGridSize(int width, int depth);

    /// Get grid dimensions
    int getGridWidth() const { return gridWidth_; }
    int getGridDepth() const { return gridDepth_; }

    /// Access a VoxelPoint at grid coordinates
    /// @throws std::out_of_range if coordinates are invalid
    VoxelPoint& at(int x, int z);
    const VoxelPoint& at(int x, int z) const;

    /// Check if coordinates are within grid bounds
    bool isValidCell(int x, int z) const;

    /// Set cell size (world units per grid cell)
    void setCellSize(float size) { cellSize_ = size; }
    float getCellSize() const { return cellSize_; }

    /// Synchronize all cells to libtcod TCODMap
    void syncToTCOD();

    /// Synchronize a single cell to TCODMap
    void syncTCODCell(int x, int z);

    /// Apply heights from HeightMap to navigation grid
    /// @param hm HeightMap to read heights from
    /// @param yScale Scale factor for Y values
    void applyHeightmap(TCOD_heightmap_t* hm, float yScale);

    /// Set cell walkability by height threshold
    /// @param hm HeightMap to sample
    /// @param minHeight Minimum height for threshold
    /// @param maxHeight Maximum height for threshold
    /// @param walkable Walkability value to set for cells in range
    void applyThreshold(TCOD_heightmap_t* hm, float minHeight, float maxHeight, bool walkable);

    /// Calculate slope costs and mark steep cells unwalkable
    /// @param maxSlope Maximum height difference before marking unwalkable
    /// @param costMultiplier Cost increase per unit slope
    void setSlopeCost(float maxSlope, float costMultiplier);

    /// Find path using A* pathfinding
    /// @param startX Start X coordinate
    /// @param startZ Start Z coordinate
    /// @param endX End X coordinate
    /// @param endZ End Z coordinate
    /// @return Vector of (x, z) positions, or empty if no path
    std::vector<std::pair<int, int>> findPath(int startX, int startZ, int endX, int endZ);

    /// Compute field of view from a position
    /// @param originX Origin X coordinate
    /// @param originZ Origin Z coordinate
    /// @param radius FOV radius
    /// @return Set of visible (x, z) positions
    std::vector<std::pair<int, int>> computeFOV(int originX, int originZ, int radius);

    /// Check if a cell is in current FOV (after computeFOV call)
    bool isInFOV(int x, int z) const;

    /// Get TCODMap pointer (for advanced usage)
    TCODMap* getTCODMap() const { return tcodMap_; }

    // =========================================================================
    // Entity3D Management
    // =========================================================================

    /// Get the entity list (for EntityCollection3D)
    std::shared_ptr<std::list<std::shared_ptr<Entity3D>>> getEntities() { return entities_; }

    /// Update all entities (call once per frame)
    void updateEntities(float dt);

    /// Render all entities
    void renderEntities(const mat4& view, const mat4& proj);

    // =========================================================================
    // Billboard Management
    // =========================================================================

    /// Get the billboard list
    std::shared_ptr<std::vector<std::shared_ptr<Billboard>>> getBillboards() { return billboards_; }

    /// Add a billboard
    void addBillboard(std::shared_ptr<Billboard> bb);

    /// Remove a billboard by pointer
    void removeBillboard(Billboard* bb);

    /// Clear all billboards
    void clearBillboards();

    /// Get billboard count
    size_t getBillboardCount() const { return billboards_ ? billboards_->size() : 0; }

    /// Render all billboards
    void renderBillboards(const mat4& view, const mat4& proj);

    // Background color
    void setBackgroundColor(const sf::Color& color) { bgColor_ = color; }
    sf::Color getBackgroundColor() const { return bgColor_; }

    // PS1 effect settings
    void setVertexSnapEnabled(bool enable) { vertexSnapEnabled_ = enable; }
    bool isVertexSnapEnabled() const { return vertexSnapEnabled_; }

    void setAffineMappingEnabled(bool enable) { affineMappingEnabled_ = enable; }
    bool isAffineMappingEnabled() const { return affineMappingEnabled_; }

    void setDitheringEnabled(bool enable) { ditheringEnabled_ = enable; }
    bool isDitheringEnabled() const { return ditheringEnabled_; }

    void setFogEnabled(bool enable) { fogEnabled_ = enable; }
    bool isFogEnabled() const { return fogEnabled_; }
    void setFogColor(const sf::Color& color);
    sf::Color getFogColor() const;
    void setFogRange(float nearDist, float farDist);
    float getFogNear() const { return fogNear_; }
    float getFogFar() const { return fogFar_; }

    // Animation property system
    bool setProperty(const std::string& name, float value) override;
    bool setProperty(const std::string& name, const sf::Color& value) override;
    bool setProperty(const std::string& name, const sf::Vector2f& value) override;

    bool getProperty(const std::string& name, float& value) const override;
    bool getProperty(const std::string& name, sf::Color& value) const override;
    bool getProperty(const std::string& name, sf::Vector2f& value) const override;

    bool hasProperty(const std::string& name) const override;

    // Python API
    static PyGetSetDef getsetters[];
    static PyObject* repr(PyViewport3DObject* self);
    static int init(PyViewport3DObject* self, PyObject* args, PyObject* kwds);

private:
    // Display size (screen coordinates)
    sf::Vector2f size_;

    // Internal render target dimensions (PS1 was 320x240)
    int internalWidth_ = 320;
    int internalHeight_ = 240;

    // FBO for render-to-texture
    unsigned int fbo_ = 0;
    unsigned int colorTexture_ = 0;
    unsigned int depthRenderbuffer_ = 0;

    // Camera
    Camera3D camera_;

    // Background color
    sf::Color bgColor_ = sf::Color(25, 25, 50);

    // PS1 effect flags
    bool vertexSnapEnabled_ = true;
    bool affineMappingEnabled_ = true;
    bool ditheringEnabled_ = true;
    bool fogEnabled_ = true;

    // Fog parameters
    vec3 fogColor_ = vec3(0.5f, 0.5f, 0.6f);
    float fogNear_ = 10.0f;
    float fogFar_ = 100.0f;

    // Render test geometry (temporary, will be replaced by layers)
    float testRotation_ = 0.0f;
    bool renderTestCube_ = true;  // Set to false when layers are added

    // Animation timing
    float lastFrameTime_ = 0.0f;
    bool firstFrame_ = true;

    // Mesh layers for terrain, static geometry
    std::vector<std::shared_ptr<MeshLayer>> meshLayers_;

    // Navigation grid (VoxelPoint system)
    std::vector<VoxelPoint> navGrid_;
    int gridWidth_ = 0;
    int gridDepth_ = 0;
    float cellSize_ = 1.0f;
    TCODMap* tcodMap_ = nullptr;
    mutable std::mutex fovMutex_;

    // Entity3D storage
    std::shared_ptr<std::list<std::shared_ptr<Entity3D>>> entities_;

    // Billboard storage
    std::shared_ptr<std::vector<std::shared_ptr<Billboard>>> billboards_;

    // Shader for PS1-style rendering
    std::unique_ptr<Shader3D> shader_;
    std::unique_ptr<Shader3D> skinnedShader_;  // For skeletal animation

    // Test geometry VBO (cube)
    unsigned int testVBO_ = 0;
    unsigned int testVertexCount_ = 0;

    // SFML texture for blitting (wraps GL texture)
    std::unique_ptr<sf::Texture> blitTexture_;

    // Initialize/cleanup FBO
    void initFBO();
    void cleanupFBO();

    // Initialize shader and test geometry
    void initShader();
    void initTestGeometry();
    void cleanupTestGeometry();

    // Render 3D content to FBO
    void render3DContent();

    // Render all mesh layers
    void renderMeshLayers();

    // Blit FBO to screen
    void blitToScreen(sf::Vector2f offset, sf::RenderTarget& target);
};

} // namespace mcrf

// Forward declaration of methods array
extern PyMethodDef Viewport3D_methods[];

namespace mcrfpydef {

static PyTypeObject PyViewport3DType = {
    .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
    .tp_name = "mcrfpy.Viewport3D",
    .tp_basicsize = sizeof(PyViewport3DObject),
    .tp_itemsize = 0,
    .tp_dealloc = (destructor)[](PyObject* self)
    {
        PyViewport3DObject* obj = (PyViewport3DObject*)self;
        PyObject_GC_UnTrack(self);
        if (obj->weakreflist != NULL) {
            PyObject_ClearWeakRefs(self);
        }
        if (obj->data) {
            obj->data->click_unregister();
            obj->data->on_enter_unregister();
            obj->data->on_exit_unregister();
            obj->data->on_move_unregister();
        }
        obj->data.reset();
        Py_TYPE(self)->tp_free(self);
    },
    .tp_repr = (reprfunc)mcrf::Viewport3D::repr,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC,
    .tp_doc = PyDoc_STR("Viewport3D(pos=None, size=None, **kwargs)\n\n"
                        "A 3D rendering viewport that displays a 3D scene as a UI element.\n\n"
                        "Args:\n"
                        "    pos (tuple, optional): Position as (x, y) tuple. Default: (0, 0)\n"
                        "    size (tuple, optional): Display size as (width, height). Default: (320, 240)\n\n"
                        "Keyword Args:\n"
                        "    render_resolution (tuple): Internal render resolution (width, height). Default: (320, 240)\n"
                        "    fov (float): Camera field of view in degrees. Default: 60\n"
                        "    camera_pos (tuple): Camera position (x, y, z). Default: (0, 0, 5)\n"
                        "    camera_target (tuple): Camera look-at point (x, y, z). Default: (0, 0, 0)\n"
                        "    bg_color (Color): Background clear color. Default: (25, 25, 50)\n"
                        "    enable_vertex_snap (bool): PS1-style vertex snapping. Default: True\n"
                        "    enable_affine (bool): PS1-style affine texture mapping. Default: True\n"
                        "    enable_dither (bool): PS1-style color dithering. Default: True\n"
                        "    enable_fog (bool): Distance fog. Default: True\n"
                        "    fog_color (Color): Fog color. Default: (128, 128, 153)\n"
                        "    fog_near (float): Fog start distance. Default: 10\n"
                        "    fog_far (float): Fog end distance. Default: 100\n"),
    .tp_traverse = [](PyObject* self, visitproc visit, void* arg) -> int {
        PyViewport3DObject* obj = (PyViewport3DObject*)self;
        if (obj->data) {
            if (obj->data->click_callable) {
                PyObject* callback = obj->data->click_callable->borrow();
                if (callback && callback != Py_None) {
                    Py_VISIT(callback);
                }
            }
            if (obj->data->on_enter_callable) {
                PyObject* callback = obj->data->on_enter_callable->borrow();
                if (callback && callback != Py_None) {
                    Py_VISIT(callback);
                }
            }
            if (obj->data->on_exit_callable) {
                PyObject* callback = obj->data->on_exit_callable->borrow();
                if (callback && callback != Py_None) {
                    Py_VISIT(callback);
                }
            }
            if (obj->data->on_move_callable) {
                PyObject* callback = obj->data->on_move_callable->borrow();
                if (callback && callback != Py_None) {
                    Py_VISIT(callback);
                }
            }
        }
        return 0;
    },
    .tp_clear = [](PyObject* self) -> int {
        PyViewport3DObject* obj = (PyViewport3DObject*)self;
        if (obj->data) {
            obj->data->click_unregister();
            obj->data->on_enter_unregister();
            obj->data->on_exit_unregister();
            obj->data->on_move_unregister();
        }
        return 0;
    },
    .tp_methods = Viewport3D_methods,
    .tp_getset = mcrf::Viewport3D::getsetters,
    .tp_base = &mcrfpydef::PyDrawableType,
    .tp_init = (initproc)mcrf::Viewport3D::init,
    .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
    {
        PyViewport3DObject* self = (PyViewport3DObject*)type->tp_alloc(type, 0);
        if (self) {
            self->data = std::make_shared<mcrf::Viewport3D>();
            self->weakreflist = nullptr;
        }
        return (PyObject*)self;
    }
};

} // namespace mcrfpydef
