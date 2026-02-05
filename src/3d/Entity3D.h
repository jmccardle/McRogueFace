// Entity3D.h - 3D game entity for McRogueFace
// Represents a game object that exists on the VoxelPoint navigation grid

#pragma once

#include "Common.h"
#include "Python.h"
#include "structmember.h"
#include "Math3D.h"
#include <memory>
#include <queue>
#include <vector>
#include <string>
#include <functional>

namespace mcrf {

// Forward declarations
class Viewport3D;
class Model3D;

} // namespace mcrf

// Python object struct forward declaration
typedef struct PyEntity3DObject PyEntity3DObject;

namespace mcrf {

// =============================================================================
// VoxelPointState - Per-entity visibility state for a grid cell
// =============================================================================

struct VoxelPointState {
    bool visible = false;      // Currently in FOV
    bool discovered = false;   // Ever seen
};

// =============================================================================
// Entity3D - 3D game entity on the navigation grid
// =============================================================================

class Entity3D : public std::enable_shared_from_this<Entity3D> {
public:
    // Python integration
    PyObject* self = nullptr;  // Reference to Python object
    uint64_t serial_number = 0;  // For object cache

    Entity3D();
    Entity3D(int grid_x, int grid_z);
    ~Entity3D();

    // =========================================================================
    // Position
    // =========================================================================

    /// Get grid position (logical game coordinates)
    int getGridX() const { return grid_x_; }
    int getGridZ() const { return grid_z_; }
    std::pair<int, int> getGridPos() const { return {grid_x_, grid_z_}; }

    /// Set grid position (triggers movement if animated)
    void setGridPos(int x, int z, bool animate = true);

    /// Teleport to grid position (instant, no animation)
    void teleportTo(int x, int z);

    /// Get world position (render coordinates, includes animation interpolation)
    vec3 getWorldPos() const { return world_pos_; }

    /// Get terrain height at current grid position
    float getTerrainHeight() const;

    // =========================================================================
    // Rotation and Scale
    // =========================================================================

    float getRotation() const { return rotation_; }  // Y-axis rotation in degrees
    void setRotation(float degrees) { rotation_ = degrees; }

    vec3 getScale() const { return scale_; }
    void setScale(const vec3& s) { scale_ = s; }
    void setScale(float uniform) { scale_ = vec3(uniform, uniform, uniform); }

    // =========================================================================
    // Appearance
    // =========================================================================

    bool isVisible() const { return visible_; }
    void setVisible(bool v) { visible_ = v; }

    // Color for placeholder cube rendering
    sf::Color getColor() const { return color_; }
    void setColor(const sf::Color& c) { color_ = c; }

    // Sprite index (for future texture atlas support)
    int getSpriteIndex() const { return sprite_index_; }
    void setSpriteIndex(int idx) { sprite_index_ = idx; }

    // 3D model (if null, uses placeholder cube)
    std::shared_ptr<Model3D> getModel() const { return model_; }
    void setModel(std::shared_ptr<Model3D> m) { model_ = m; }

    // =========================================================================
    // Viewport Integration
    // =========================================================================

    /// Get owning viewport (may be null)
    std::shared_ptr<Viewport3D> getViewport() const { return viewport_.lock(); }

    /// Set owning viewport (called when added to viewport)
    void setViewport(std::shared_ptr<Viewport3D> vp);

    /// Update cell registration (call when grid position changes)
    void updateCellRegistration();

    // =========================================================================
    // Visibility / FOV
    // =========================================================================

    /// Update visibility state from current FOV
    void updateVisibility();

    /// Get visibility state for a cell from this entity's perspective
    const VoxelPointState& getVoxelState(int x, int z) const;

    /// Check if a cell is currently visible to this entity
    bool canSee(int x, int z) const;

    /// Check if a cell has been discovered by this entity
    bool hasDiscovered(int x, int z) const;

    // =========================================================================
    // Pathfinding
    // =========================================================================

    /// Compute path to target position
    std::vector<std::pair<int, int>> pathTo(int target_x, int target_z);

    /// Follow a path (queue movement steps)
    void followPath(const std::vector<std::pair<int, int>>& path);

    /// Check if entity is currently moving
    bool isMoving() const { return !move_queue_.empty() || is_animating_; }

    /// Clear movement queue
    void clearPath() { while (!move_queue_.empty()) move_queue_.pop(); }

    // =========================================================================
    // Animation / Update
    // =========================================================================

    /// Update entity state (called each frame)
    /// @param dt Delta time in seconds
    void update(float dt);

    /// Property system for animation
    bool setProperty(const std::string& name, float value);
    bool setProperty(const std::string& name, int value);
    bool getProperty(const std::string& name, float& value) const;
    bool hasProperty(const std::string& name) const;

    // =========================================================================
    // Skeletal Animation
    // =========================================================================

    /// Get current animation clip name
    const std::string& getAnimClip() const { return anim_clip_; }

    /// Set animation clip by name (starts playing)
    void setAnimClip(const std::string& name);

    /// Get/set animation time (position in clip)
    float getAnimTime() const { return anim_time_; }
    void setAnimTime(float t) { anim_time_ = t; }

    /// Get/set playback speed (1.0 = normal)
    float getAnimSpeed() const { return anim_speed_; }
    void setAnimSpeed(float s) { anim_speed_ = s; }

    /// Get/set looping state
    bool getAnimLoop() const { return anim_loop_; }
    void setAnimLoop(bool l) { anim_loop_ = l; }

    /// Get/set pause state
    bool getAnimPaused() const { return anim_paused_; }
    void setAnimPaused(bool p) { anim_paused_ = p; }

    /// Get current animation frame (approximate)
    int getAnimFrame() const;

    /// Update skeletal animation (call before render)
    void updateAnimation(float dt);

    /// Get computed bone matrices for shader
    const std::vector<mat4>& getBoneMatrices() const { return bone_matrices_; }

    /// Animation complete callback type
    using AnimCompleteCallback = std::function<void(Entity3D*, const std::string&)>;

    /// Set animation complete callback
    void setOnAnimComplete(AnimCompleteCallback cb) { on_anim_complete_ = cb; }

    /// Auto-animate settings (play walk/idle based on movement)
    bool getAutoAnimate() const { return auto_animate_; }
    void setAutoAnimate(bool a) { auto_animate_ = a; }

    const std::string& getWalkClip() const { return walk_clip_; }
    void setWalkClip(const std::string& c) { walk_clip_ = c; }

    const std::string& getIdleClip() const { return idle_clip_; }
    void setIdleClip(const std::string& c) { idle_clip_ = c; }

    // =========================================================================
    // Rendering
    // =========================================================================

    /// Get model matrix for rendering
    mat4 getModelMatrix() const;

    /// Render the entity (called by Viewport3D)
    void render(const mat4& view, const mat4& proj, unsigned int shader);

    // =========================================================================
    // Python API
    // =========================================================================

    static int init(PyEntity3DObject* self, PyObject* args, PyObject* kwds);
    static PyObject* repr(PyEntity3DObject* self);

    // Property getters/setters
    static PyObject* get_pos(PyEntity3DObject* self, void* closure);
    static int set_pos(PyEntity3DObject* self, PyObject* value, void* closure);
    static PyObject* get_world_pos(PyEntity3DObject* self, void* closure);
    static PyObject* get_grid_pos(PyEntity3DObject* self, void* closure);
    static int set_grid_pos(PyEntity3DObject* self, PyObject* value, void* closure);
    static PyObject* get_rotation(PyEntity3DObject* self, void* closure);
    static int set_rotation(PyEntity3DObject* self, PyObject* value, void* closure);
    static PyObject* get_scale(PyEntity3DObject* self, void* closure);
    static int set_scale(PyEntity3DObject* self, PyObject* value, void* closure);
    static PyObject* get_visible(PyEntity3DObject* self, void* closure);
    static int set_visible(PyEntity3DObject* self, PyObject* value, void* closure);
    static PyObject* get_color(PyEntity3DObject* self, void* closure);
    static int set_color(PyEntity3DObject* self, PyObject* value, void* closure);
    static PyObject* get_viewport(PyEntity3DObject* self, void* closure);
    static PyObject* get_model(PyEntity3DObject* self, void* closure);
    static int set_model(PyEntity3DObject* self, PyObject* value, void* closure);

    // Animation property getters/setters
    static PyObject* get_anim_clip(PyEntity3DObject* self, void* closure);
    static int set_anim_clip(PyEntity3DObject* self, PyObject* value, void* closure);
    static PyObject* get_anim_time(PyEntity3DObject* self, void* closure);
    static int set_anim_time(PyEntity3DObject* self, PyObject* value, void* closure);
    static PyObject* get_anim_speed(PyEntity3DObject* self, void* closure);
    static int set_anim_speed(PyEntity3DObject* self, PyObject* value, void* closure);
    static PyObject* get_anim_loop(PyEntity3DObject* self, void* closure);
    static int set_anim_loop(PyEntity3DObject* self, PyObject* value, void* closure);
    static PyObject* get_anim_paused(PyEntity3DObject* self, void* closure);
    static int set_anim_paused(PyEntity3DObject* self, PyObject* value, void* closure);
    static PyObject* get_anim_frame(PyEntity3DObject* self, void* closure);
    static PyObject* get_on_anim_complete(PyEntity3DObject* self, void* closure);
    static int set_on_anim_complete(PyEntity3DObject* self, PyObject* value, void* closure);
    static PyObject* get_auto_animate(PyEntity3DObject* self, void* closure);
    static int set_auto_animate(PyEntity3DObject* self, PyObject* value, void* closure);
    static PyObject* get_walk_clip(PyEntity3DObject* self, void* closure);
    static int set_walk_clip(PyEntity3DObject* self, PyObject* value, void* closure);
    static PyObject* get_idle_clip(PyEntity3DObject* self, void* closure);
    static int set_idle_clip(PyEntity3DObject* self, PyObject* value, void* closure);

    // Methods
    static PyObject* py_path_to(PyEntity3DObject* self, PyObject* args, PyObject* kwds);
    static PyObject* py_teleport(PyEntity3DObject* self, PyObject* args, PyObject* kwds);
    static PyObject* py_at(PyEntity3DObject* self, PyObject* args, PyObject* kwds);
    static PyObject* py_update_visibility(PyEntity3DObject* self, PyObject* args);
    static PyObject* py_animate(PyEntity3DObject* self, PyObject* args, PyObject* kwds);

    static PyMethodDef methods[];
    static PyGetSetDef getsetters[];

private:
    // Grid position (logical game coordinates)
    int grid_x_ = 0;
    int grid_z_ = 0;
    int old_grid_x_ = -1;  // For cell registration tracking
    int old_grid_z_ = -1;

    // World position (render coordinates, smoothly interpolated)
    vec3 world_pos_;
    vec3 target_world_pos_;  // Animation target

    // Rotation (Y-axis, in degrees)
    float rotation_ = 0.0f;

    // Scale
    vec3 scale_ = vec3(1.0f, 1.0f, 1.0f);

    // Appearance
    bool visible_ = true;
    sf::Color color_ = sf::Color(200, 100, 50);  // Default orange
    int sprite_index_ = 0;
    std::shared_ptr<Model3D> model_;  // 3D model (null = placeholder cube)

    // Viewport (weak reference to avoid cycles)
    std::weak_ptr<Viewport3D> viewport_;

    // Visibility state per cell (lazy initialized)
    mutable std::vector<VoxelPointState> voxel_state_;
    mutable bool voxel_state_initialized_ = false;

    // Movement animation
    std::queue<std::pair<int, int>> move_queue_;
    bool is_animating_ = false;
    float move_progress_ = 0.0f;
    float move_speed_ = 5.0f;  // Cells per second
    vec3 move_start_pos_;

    // Skeletal animation state
    std::string anim_clip_;                 // Current animation clip name
    float anim_time_ = 0.0f;                // Current time in animation
    float anim_speed_ = 1.0f;               // Playback speed multiplier
    bool anim_loop_ = true;                 // Loop animation
    bool anim_paused_ = false;              // Pause playback
    std::vector<mat4> bone_matrices_;       // Computed bone matrices for shader
    AnimCompleteCallback on_anim_complete_; // Callback when animation ends

    // Auto-animate state
    bool auto_animate_ = true;              // Auto-play walk/idle based on movement
    std::string walk_clip_ = "walk";        // Clip to play when moving
    std::string idle_clip_ = "idle";        // Clip to play when stopped
    bool was_moving_ = false;               // Track movement state for auto-animate

    // Python callback for animation complete
    PyObject* py_anim_callback_ = nullptr;

    // Helper to initialize voxel state
    void initVoxelState() const;

    // Helper to update world position from grid position
    void updateWorldPosFromGrid();

    // Process next move in queue
    void processNextMove();

    // Static VBO for placeholder cube
    static unsigned int cubeVBO_;
    static unsigned int cubeVertexCount_;
    static bool cubeInitialized_;
    static void initCubeGeometry();
};

} // namespace mcrf

// =============================================================================
// Python type definition
// =============================================================================

typedef struct PyEntity3DObject {
    PyObject_HEAD
    std::shared_ptr<mcrf::Entity3D> data;
    PyObject* weakreflist;
} PyEntity3DObject;

// Forward declaration of methods array
extern PyMethodDef Entity3D_methods[];

namespace mcrfpydef {

inline PyTypeObject PyEntity3DType = {
    .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
    .tp_name = "mcrfpy.Entity3D",
    .tp_basicsize = sizeof(PyEntity3DObject),
    .tp_itemsize = 0,
    .tp_dealloc = (destructor)[](PyObject* self)
    {
        PyEntity3DObject* obj = (PyEntity3DObject*)self;
        PyObject_GC_UnTrack(self);
        if (obj->weakreflist != NULL) {
            PyObject_ClearWeakRefs(self);
        }
        obj->data.reset();
        Py_TYPE(self)->tp_free(self);
    },
    .tp_repr = (reprfunc)mcrf::Entity3D::repr,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC,
    .tp_doc = PyDoc_STR("Entity3D(pos=None, **kwargs)\n\n"
                        "A 3D game entity that exists on a Viewport3D's navigation grid.\n\n"
                        "Args:\n"
                        "    pos (tuple, optional): Grid position as (x, z). Default: (0, 0)\n\n"
                        "Keyword Args:\n"
                        "    viewport (Viewport3D): Viewport to attach entity to. Default: None\n"
                        "    rotation (float): Y-axis rotation in degrees. Default: 0\n"
                        "    scale (float or tuple): Scale factor. Default: 1.0\n"
                        "    visible (bool): Visibility state. Default: True\n"
                        "    color (Color): Entity color. Default: orange\n\n"
                        "Attributes:\n"
                        "    pos (tuple): Grid position (x, z) - setting triggers movement\n"
                        "    grid_pos (tuple): Same as pos (read-only)\n"
                        "    world_pos (tuple): Current world coordinates (x, y, z) (read-only)\n"
                        "    rotation (float): Y-axis rotation in degrees\n"
                        "    scale (float): Uniform scale factor\n"
                        "    visible (bool): Visibility state\n"
                        "    color (Color): Entity render color\n"
                        "    viewport (Viewport3D): Owning viewport (read-only)"),
    .tp_traverse = [](PyObject* self, visitproc visit, void* arg) -> int {
        // No Python objects to visit currently
        return 0;
    },
    .tp_clear = [](PyObject* self) -> int {
        return 0;
    },
    .tp_methods = mcrf::Entity3D::methods,
    .tp_getset = mcrf::Entity3D::getsetters,
    .tp_init = (initproc)mcrf::Entity3D::init,
    .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
    {
        PyEntity3DObject* self = (PyEntity3DObject*)type->tp_alloc(type, 0);
        if (self) {
            self->data = std::make_shared<mcrf::Entity3D>();
            self->weakreflist = nullptr;
        }
        return (PyObject*)self;
    }
};

} // namespace mcrfpydef
