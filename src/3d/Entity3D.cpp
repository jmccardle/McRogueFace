// Entity3D.cpp - 3D game entity implementation

#include "Entity3D.h"
#include "Viewport3D.h"
#include "VoxelPoint.h"
#include "Model3D.h"
#include "Shader3D.h"
#include "PyVector.h"
#include "PyColor.h"
#include "PythonObjectCache.h"
#include <cstdio>

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

// Static members for placeholder cube
unsigned int Entity3D::cubeVBO_ = 0;
unsigned int Entity3D::cubeVertexCount_ = 0;
bool Entity3D::cubeInitialized_ = false;

// =============================================================================
// Constructor / Destructor
// =============================================================================

Entity3D::Entity3D()
    : grid_x_(0)
    , grid_z_(0)
    , world_pos_(0, 0, 0)
    , target_world_pos_(0, 0, 0)
{
}

Entity3D::Entity3D(int grid_x, int grid_z)
    : grid_x_(grid_x)
    , grid_z_(grid_z)
{
    updateWorldPosFromGrid();
    target_world_pos_ = world_pos_;
}

Entity3D::~Entity3D()
{
    // Cleanup cube geometry when last entity is destroyed?
    // For now, leave it - it's shared static data
}

// =============================================================================
// Position
// =============================================================================

void Entity3D::setGridPos(int x, int z, bool animate)
{
    if (x == grid_x_ && z == grid_z_) return;

    if (animate && !is_animating_) {
        // Queue the move for animation
        move_queue_.push({x, z});
        if (!is_animating_) {
            processNextMove();
        }
    } else if (!animate) {
        teleportTo(x, z);
    } else {
        // Already animating, queue this move
        move_queue_.push({x, z});
    }
}

void Entity3D::teleportTo(int x, int z)
{
    // Clear any pending moves
    clearPath();
    is_animating_ = false;

    grid_x_ = x;
    grid_z_ = z;
    updateCellRegistration();
    updateWorldPosFromGrid();
    target_world_pos_ = world_pos_;
}

float Entity3D::getTerrainHeight() const
{
    auto vp = viewport_.lock();
    if (!vp) return 0.0f;

    if (vp->isValidCell(grid_x_, grid_z_)) {
        return vp->at(grid_x_, grid_z_).height;
    }
    return 0.0f;
}

void Entity3D::updateWorldPosFromGrid()
{
    auto vp = viewport_.lock();
    float cellSize = vp ? vp->getCellSize() : 1.0f;

    world_pos_.x = grid_x_ * cellSize + cellSize * 0.5f;  // Center of cell
    world_pos_.z = grid_z_ * cellSize + cellSize * 0.5f;
    world_pos_.y = getTerrainHeight() + 0.5f;  // Slightly above terrain
}

// =============================================================================
// Viewport Integration
// =============================================================================

void Entity3D::setViewport(std::shared_ptr<Viewport3D> vp)
{
    viewport_ = vp;
    if (vp) {
        updateWorldPosFromGrid();
        target_world_pos_ = world_pos_;
        updateCellRegistration();
    }
}

void Entity3D::updateCellRegistration()
{
    // For now, just track the old position
    // VoxelPoint.entities list support will be added later
    old_grid_x_ = grid_x_;
    old_grid_z_ = grid_z_;
}

// =============================================================================
// Visibility / FOV
// =============================================================================

void Entity3D::initVoxelState() const
{
    auto vp = viewport_.lock();
    if (!vp) {
        voxel_state_.clear();
        voxel_state_initialized_ = false;
        return;
    }

    int w = vp->getGridWidth();
    int d = vp->getGridDepth();
    if (w <= 0 || d <= 0) {
        voxel_state_.clear();
        voxel_state_initialized_ = false;
        return;
    }

    voxel_state_.resize(w * d);
    for (auto& state : voxel_state_) {
        state.visible = false;
        state.discovered = false;
    }
    voxel_state_initialized_ = true;
}

void Entity3D::updateVisibility()
{
    auto vp = viewport_.lock();
    if (!vp) return;

    if (!voxel_state_initialized_) {
        initVoxelState();
    }

    int w = vp->getGridWidth();
    int d = vp->getGridDepth();

    // Reset visibility (keep discovered)
    for (auto& state : voxel_state_) {
        state.visible = false;
    }

    // Compute FOV from entity position
    auto visible_cells = vp->computeFOV(grid_x_, grid_z_, 10);  // Default radius 10

    // Mark visible cells
    for (const auto& cell : visible_cells) {
        int idx = cell.second * w + cell.first;
        if (idx >= 0 && idx < static_cast<int>(voxel_state_.size())) {
            voxel_state_[idx].visible = true;
            voxel_state_[idx].discovered = true;
        }
    }
}

const VoxelPointState& Entity3D::getVoxelState(int x, int z) const
{
    static VoxelPointState empty;

    auto vp = viewport_.lock();
    if (!vp) return empty;

    if (!voxel_state_initialized_) {
        initVoxelState();
    }

    int w = vp->getGridWidth();
    int idx = z * w + x;
    if (idx >= 0 && idx < static_cast<int>(voxel_state_.size())) {
        return voxel_state_[idx];
    }
    return empty;
}

bool Entity3D::canSee(int x, int z) const
{
    return getVoxelState(x, z).visible;
}

bool Entity3D::hasDiscovered(int x, int z) const
{
    return getVoxelState(x, z).discovered;
}

// =============================================================================
// Pathfinding
// =============================================================================

std::vector<std::pair<int, int>> Entity3D::pathTo(int target_x, int target_z)
{
    auto vp = viewport_.lock();
    if (!vp) return {};

    return vp->findPath(grid_x_, grid_z_, target_x, target_z);
}

void Entity3D::followPath(const std::vector<std::pair<int, int>>& path)
{
    for (const auto& step : path) {
        move_queue_.push(step);
    }
    if (!is_animating_ && !move_queue_.empty()) {
        processNextMove();
    }
}

void Entity3D::processNextMove()
{
    if (move_queue_.empty()) {
        is_animating_ = false;
        return;
    }

    auto next = move_queue_.front();
    move_queue_.pop();

    // Update grid position immediately (game logic)
    grid_x_ = next.first;
    grid_z_ = next.second;
    updateCellRegistration();

    // Set up animation
    move_start_pos_ = world_pos_;

    // Calculate target world position
    auto vp = viewport_.lock();
    float cellSize = vp ? vp->getCellSize() : 1.0f;
    float terrainHeight = getTerrainHeight();

    target_world_pos_.x = grid_x_ * cellSize + cellSize * 0.5f;
    target_world_pos_.z = grid_z_ * cellSize + cellSize * 0.5f;
    target_world_pos_.y = terrainHeight + 0.5f;

    is_animating_ = true;
    move_progress_ = 0.0f;
}

// =============================================================================
// Animation / Update
// =============================================================================

void Entity3D::update(float dt)
{
    if (!is_animating_) return;

    move_progress_ += dt * move_speed_;

    if (move_progress_ >= 1.0f) {
        // Animation complete
        world_pos_ = target_world_pos_;
        is_animating_ = false;

        // Process next move in queue
        if (!move_queue_.empty()) {
            processNextMove();
        }
    } else {
        // Interpolate position
        world_pos_ = vec3::lerp(move_start_pos_, target_world_pos_, move_progress_);
    }
}

bool Entity3D::setProperty(const std::string& name, float value)
{
    if (name == "x" || name == "world_x") {
        world_pos_.x = value;
        return true;
    }
    if (name == "y" || name == "world_y") {
        world_pos_.y = value;
        return true;
    }
    if (name == "z" || name == "world_z") {
        world_pos_.z = value;
        return true;
    }
    if (name == "rotation" || name == "rot_y") {
        rotation_ = value;
        return true;
    }
    if (name == "scale") {
        scale_ = vec3(value, value, value);
        return true;
    }
    if (name == "scale_x") {
        scale_.x = value;
        return true;
    }
    if (name == "scale_y") {
        scale_.y = value;
        return true;
    }
    if (name == "scale_z") {
        scale_.z = value;
        return true;
    }
    return false;
}

bool Entity3D::setProperty(const std::string& name, int value)
{
    if (name == "sprite_index") {
        sprite_index_ = value;
        return true;
    }
    if (name == "visible") {
        visible_ = value != 0;
        return true;
    }
    return false;
}

bool Entity3D::getProperty(const std::string& name, float& value) const
{
    if (name == "x" || name == "world_x") {
        value = world_pos_.x;
        return true;
    }
    if (name == "y" || name == "world_y") {
        value = world_pos_.y;
        return true;
    }
    if (name == "z" || name == "world_z") {
        value = world_pos_.z;
        return true;
    }
    if (name == "rotation" || name == "rot_y") {
        value = rotation_;
        return true;
    }
    if (name == "scale") {
        value = scale_.x;  // Return uniform scale
        return true;
    }
    return false;
}

bool Entity3D::hasProperty(const std::string& name) const
{
    return name == "x" || name == "y" || name == "z" ||
           name == "world_x" || name == "world_y" || name == "world_z" ||
           name == "rotation" || name == "rot_y" ||
           name == "scale" || name == "scale_x" || name == "scale_y" || name == "scale_z" ||
           name == "sprite_index" || name == "visible";
}

// =============================================================================
// Rendering
// =============================================================================

mat4 Entity3D::getModelMatrix() const
{
    mat4 model = mat4::identity();
    model = mat4::translate(world_pos_) * model;
    model = mat4::rotateY(rotation_ * DEG_TO_RAD) * model;
    model = mat4::scale(scale_) * model;
    return model;
}

void Entity3D::initCubeGeometry()
{
    if (cubeInitialized_) return;

    // Unit cube vertices (position + normal + color placeholder)
    // Each vertex: x, y, z, nx, ny, nz, r, g, b
    float vertices[] = {
        // Front face
        -0.5f, -0.5f,  0.5f,  0.0f, 0.0f, 1.0f,  1.0f, 0.5f, 0.25f,
         0.5f, -0.5f,  0.5f,  0.0f, 0.0f, 1.0f,  1.0f, 0.5f, 0.25f,
         0.5f,  0.5f,  0.5f,  0.0f, 0.0f, 1.0f,  1.0f, 0.5f, 0.25f,
        -0.5f, -0.5f,  0.5f,  0.0f, 0.0f, 1.0f,  1.0f, 0.5f, 0.25f,
         0.5f,  0.5f,  0.5f,  0.0f, 0.0f, 1.0f,  1.0f, 0.5f, 0.25f,
        -0.5f,  0.5f,  0.5f,  0.0f, 0.0f, 1.0f,  1.0f, 0.5f, 0.25f,

        // Back face
         0.5f, -0.5f, -0.5f,  0.0f, 0.0f, -1.0f,  0.8f, 0.4f, 0.2f,
        -0.5f, -0.5f, -0.5f,  0.0f, 0.0f, -1.0f,  0.8f, 0.4f, 0.2f,
        -0.5f,  0.5f, -0.5f,  0.0f, 0.0f, -1.0f,  0.8f, 0.4f, 0.2f,
         0.5f, -0.5f, -0.5f,  0.0f, 0.0f, -1.0f,  0.8f, 0.4f, 0.2f,
        -0.5f,  0.5f, -0.5f,  0.0f, 0.0f, -1.0f,  0.8f, 0.4f, 0.2f,
         0.5f,  0.5f, -0.5f,  0.0f, 0.0f, -1.0f,  0.8f, 0.4f, 0.2f,

        // Right face
         0.5f, -0.5f,  0.5f,  1.0f, 0.0f, 0.0f,  0.9f, 0.45f, 0.22f,
         0.5f, -0.5f, -0.5f,  1.0f, 0.0f, 0.0f,  0.9f, 0.45f, 0.22f,
         0.5f,  0.5f, -0.5f,  1.0f, 0.0f, 0.0f,  0.9f, 0.45f, 0.22f,
         0.5f, -0.5f,  0.5f,  1.0f, 0.0f, 0.0f,  0.9f, 0.45f, 0.22f,
         0.5f,  0.5f, -0.5f,  1.0f, 0.0f, 0.0f,  0.9f, 0.45f, 0.22f,
         0.5f,  0.5f,  0.5f,  1.0f, 0.0f, 0.0f,  0.9f, 0.45f, 0.22f,

        // Left face
        -0.5f, -0.5f, -0.5f, -1.0f, 0.0f, 0.0f,  0.7f, 0.35f, 0.17f,
        -0.5f, -0.5f,  0.5f, -1.0f, 0.0f, 0.0f,  0.7f, 0.35f, 0.17f,
        -0.5f,  0.5f,  0.5f, -1.0f, 0.0f, 0.0f,  0.7f, 0.35f, 0.17f,
        -0.5f, -0.5f, -0.5f, -1.0f, 0.0f, 0.0f,  0.7f, 0.35f, 0.17f,
        -0.5f,  0.5f,  0.5f, -1.0f, 0.0f, 0.0f,  0.7f, 0.35f, 0.17f,
        -0.5f,  0.5f, -0.5f, -1.0f, 0.0f, 0.0f,  0.7f, 0.35f, 0.17f,

        // Top face
        -0.5f,  0.5f,  0.5f,  0.0f, 1.0f, 0.0f,  1.0f, 0.6f, 0.3f,
         0.5f,  0.5f,  0.5f,  0.0f, 1.0f, 0.0f,  1.0f, 0.6f, 0.3f,
         0.5f,  0.5f, -0.5f,  0.0f, 1.0f, 0.0f,  1.0f, 0.6f, 0.3f,
        -0.5f,  0.5f,  0.5f,  0.0f, 1.0f, 0.0f,  1.0f, 0.6f, 0.3f,
         0.5f,  0.5f, -0.5f,  0.0f, 1.0f, 0.0f,  1.0f, 0.6f, 0.3f,
        -0.5f,  0.5f, -0.5f,  0.0f, 1.0f, 0.0f,  1.0f, 0.6f, 0.3f,

        // Bottom face
        -0.5f, -0.5f, -0.5f,  0.0f, -1.0f, 0.0f,  0.6f, 0.3f, 0.15f,
         0.5f, -0.5f, -0.5f,  0.0f, -1.0f, 0.0f,  0.6f, 0.3f, 0.15f,
         0.5f, -0.5f,  0.5f,  0.0f, -1.0f, 0.0f,  0.6f, 0.3f, 0.15f,
        -0.5f, -0.5f, -0.5f,  0.0f, -1.0f, 0.0f,  0.6f, 0.3f, 0.15f,
         0.5f, -0.5f,  0.5f,  0.0f, -1.0f, 0.0f,  0.6f, 0.3f, 0.15f,
        -0.5f, -0.5f,  0.5f,  0.0f, -1.0f, 0.0f,  0.6f, 0.3f, 0.15f,
    };

    cubeVertexCount_ = 36;

    glGenBuffers(1, &cubeVBO_);
    glBindBuffer(GL_ARRAY_BUFFER, cubeVBO_);
    glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STATIC_DRAW);
    glBindBuffer(GL_ARRAY_BUFFER, 0);

    cubeInitialized_ = true;
}

void Entity3D::render(const mat4& view, const mat4& proj, unsigned int shader)
{
    if (!visible_) return;

    // Set entity color uniform (used by Model3D and placeholder)
    int colorLoc = glGetUniformLocation(shader, "u_entityColor");
    if (colorLoc >= 0) {
        glUniform4f(colorLoc,
            color_.r / 255.0f,
            color_.g / 255.0f,
            color_.b / 255.0f,
            color_.a / 255.0f);
    }

    // If we have a model, use it
    if (model_) {
        mat4 model = getModelMatrix();
        model_->render(shader, model, view, proj);
        return;
    }

    // Otherwise, fall back to placeholder cube
    // Initialize cube geometry if needed
    if (!cubeInitialized_) {
        initCubeGeometry();
    }

    // Set model matrix uniform
    mat4 model = getModelMatrix();
    mat4 mvp = proj * view * model;

    // Get uniform locations (assuming shader is already bound)
    int mvpLoc = glGetUniformLocation(shader, "u_mvp");
    int modelLoc = glGetUniformLocation(shader, "u_model");

    if (mvpLoc >= 0) glUniformMatrix4fv(mvpLoc, 1, GL_FALSE, mvp.data());
    if (modelLoc >= 0) glUniformMatrix4fv(modelLoc, 1, GL_FALSE, model.data());

    // Bind VBO and set up attributes
    glBindBuffer(GL_ARRAY_BUFFER, cubeVBO_);

    // Position attribute (location 0)
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 9 * sizeof(float), (void*)0);

    // Normal attribute (location 1)
    glEnableVertexAttribArray(1);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 9 * sizeof(float), (void*)(3 * sizeof(float)));

    // Color attribute (location 2)
    glEnableVertexAttribArray(2);
    glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 9 * sizeof(float), (void*)(6 * sizeof(float)));

    // Draw
    glDrawArrays(GL_TRIANGLES, 0, cubeVertexCount_);

    // Cleanup
    glDisableVertexAttribArray(0);
    glDisableVertexAttribArray(1);
    glDisableVertexAttribArray(2);
    glBindBuffer(GL_ARRAY_BUFFER, 0);
}

// =============================================================================
// Python API Implementation
// =============================================================================

int Entity3D::init(PyEntity3DObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"pos", "viewport", "rotation", "scale", "visible", "color", NULL};

    PyObject* pos_obj = nullptr;
    PyObject* viewport_obj = nullptr;
    float rotation = 0.0f;
    PyObject* scale_obj = nullptr;
    int visible = 1;
    PyObject* color_obj = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OOfOpO", const_cast<char**>(kwlist),
            &pos_obj, &viewport_obj, &rotation, &scale_obj, &visible, &color_obj)) {
        return -1;
    }

    // Parse position
    int grid_x = 0, grid_z = 0;
    if (pos_obj && pos_obj != Py_None) {
        if (PyTuple_Check(pos_obj) && PyTuple_Size(pos_obj) >= 2) {
            grid_x = PyLong_AsLong(PyTuple_GetItem(pos_obj, 0));
            grid_z = PyLong_AsLong(PyTuple_GetItem(pos_obj, 1));
            if (PyErr_Occurred()) return -1;
        } else {
            PyErr_SetString(PyExc_TypeError, "pos must be a tuple of (x, z)");
            return -1;
        }
    }

    // Initialize entity
    self->data->grid_x_ = grid_x;
    self->data->grid_z_ = grid_z;
    self->data->rotation_ = rotation;
    self->data->visible_ = visible != 0;

    // Parse scale
    if (scale_obj && scale_obj != Py_None) {
        if (PyFloat_Check(scale_obj) || PyLong_Check(scale_obj)) {
            float s = (float)PyFloat_AsDouble(scale_obj);
            self->data->scale_ = vec3(s, s, s);
        } else if (PyTuple_Check(scale_obj) && PyTuple_Size(scale_obj) >= 3) {
            float sx = (float)PyFloat_AsDouble(PyTuple_GetItem(scale_obj, 0));
            float sy = (float)PyFloat_AsDouble(PyTuple_GetItem(scale_obj, 1));
            float sz = (float)PyFloat_AsDouble(PyTuple_GetItem(scale_obj, 2));
            self->data->scale_ = vec3(sx, sy, sz);
        }
    }

    // Parse color
    if (color_obj && color_obj != Py_None) {
        self->data->color_ = PyColor::fromPy(color_obj);
        if (PyErr_Occurred()) return -1;
    }

    // Attach to viewport if provided
    if (viewport_obj && viewport_obj != Py_None) {
        // Will be handled by EntityCollection3D when appending
        // For now, just validate it's the right type
        if (!PyObject_IsInstance(viewport_obj, (PyObject*)&mcrfpydef::PyViewport3DType)) {
            PyErr_SetString(PyExc_TypeError, "viewport must be a Viewport3D");
            return -1;
        }
    }

    // Register in object cache
    self->data->serial_number = PythonObjectCache::getInstance().assignSerial();
    self->data->self = (PyObject*)self;

    return 0;
}

PyObject* Entity3D::repr(PyEntity3DObject* self)
{
    if (!self->data) {
        return PyUnicode_FromString("<Entity3D (null)>");
    }

    char buffer[128];
    snprintf(buffer, sizeof(buffer),
        "<Entity3D at (%d, %d) world=(%.1f, %.1f, %.1f) rot=%.1f>",
        self->data->grid_x_, self->data->grid_z_,
        self->data->world_pos_.x, self->data->world_pos_.y, self->data->world_pos_.z,
        self->data->rotation_);
    return PyUnicode_FromString(buffer);
}

// Property getters/setters

PyObject* Entity3D::get_pos(PyEntity3DObject* self, void* closure)
{
    return Py_BuildValue("(ii)", self->data->grid_x_, self->data->grid_z_);
}

int Entity3D::set_pos(PyEntity3DObject* self, PyObject* value, void* closure)
{
    if (!PyTuple_Check(value) || PyTuple_Size(value) < 2) {
        PyErr_SetString(PyExc_TypeError, "pos must be a tuple of (x, z)");
        return -1;
    }

    int x = PyLong_AsLong(PyTuple_GetItem(value, 0));
    int z = PyLong_AsLong(PyTuple_GetItem(value, 1));
    if (PyErr_Occurred()) return -1;

    self->data->setGridPos(x, z, true);  // Animate by default
    return 0;
}

PyObject* Entity3D::get_world_pos(PyEntity3DObject* self, void* closure)
{
    vec3 wp = self->data->world_pos_;
    return Py_BuildValue("(fff)", wp.x, wp.y, wp.z);
}

PyObject* Entity3D::get_grid_pos(PyEntity3DObject* self, void* closure)
{
    return Py_BuildValue("(ii)", self->data->grid_x_, self->data->grid_z_);
}

int Entity3D::set_grid_pos(PyEntity3DObject* self, PyObject* value, void* closure)
{
    return set_pos(self, value, closure);
}

PyObject* Entity3D::get_rotation(PyEntity3DObject* self, void* closure)
{
    return PyFloat_FromDouble(self->data->rotation_);
}

int Entity3D::set_rotation(PyEntity3DObject* self, PyObject* value, void* closure)
{
    if (!PyNumber_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "rotation must be a number");
        return -1;
    }
    self->data->rotation_ = (float)PyFloat_AsDouble(value);
    return 0;
}

PyObject* Entity3D::get_scale(PyEntity3DObject* self, void* closure)
{
    return PyFloat_FromDouble(self->data->scale_.x);  // Return uniform scale
}

int Entity3D::set_scale(PyEntity3DObject* self, PyObject* value, void* closure)
{
    if (PyFloat_Check(value) || PyLong_Check(value)) {
        float s = (float)PyFloat_AsDouble(value);
        self->data->scale_ = vec3(s, s, s);
        return 0;
    } else if (PyTuple_Check(value) && PyTuple_Size(value) >= 3) {
        float sx = (float)PyFloat_AsDouble(PyTuple_GetItem(value, 0));
        float sy = (float)PyFloat_AsDouble(PyTuple_GetItem(value, 1));
        float sz = (float)PyFloat_AsDouble(PyTuple_GetItem(value, 2));
        self->data->scale_ = vec3(sx, sy, sz);
        return 0;
    }
    PyErr_SetString(PyExc_TypeError, "scale must be a number or (x, y, z) tuple");
    return -1;
}

PyObject* Entity3D::get_visible(PyEntity3DObject* self, void* closure)
{
    return PyBool_FromLong(self->data->visible_ ? 1 : 0);
}

int Entity3D::set_visible(PyEntity3DObject* self, PyObject* value, void* closure)
{
    self->data->visible_ = PyObject_IsTrue(value);
    return 0;
}

PyObject* Entity3D::get_color(PyEntity3DObject* self, void* closure)
{
    return PyColor(self->data->color_).pyObject();
}

int Entity3D::set_color(PyEntity3DObject* self, PyObject* value, void* closure)
{
    self->data->color_ = PyColor::fromPy(value);
    if (PyErr_Occurred()) return -1;
    return 0;
}

PyObject* Entity3D::get_viewport(PyEntity3DObject* self, void* closure)
{
    auto vp = self->data->viewport_.lock();
    if (!vp) {
        Py_RETURN_NONE;
    }
    // TODO: Return actual viewport Python object
    // For now, return None
    Py_RETURN_NONE;
}

PyObject* Entity3D::get_model(PyEntity3DObject* self, void* closure)
{
    auto model = self->data->getModel();
    if (!model) {
        Py_RETURN_NONE;
    }

    // Create Python Model3D object wrapping the shared_ptr
    PyTypeObject* type = &mcrfpydef::PyModel3DType;
    PyModel3DObject* obj = (PyModel3DObject*)type->tp_alloc(type, 0);
    if (!obj) return NULL;

    obj->data = model;
    obj->weakreflist = nullptr;

    return (PyObject*)obj;
}

int Entity3D::set_model(PyEntity3DObject* self, PyObject* value, void* closure)
{
    if (value == Py_None) {
        self->data->setModel(nullptr);
        return 0;
    }

    if (!PyObject_IsInstance(value, (PyObject*)&mcrfpydef::PyModel3DType)) {
        PyErr_SetString(PyExc_TypeError, "model must be a Model3D or None");
        return -1;
    }

    PyModel3DObject* model_obj = (PyModel3DObject*)value;
    self->data->setModel(model_obj->data);
    return 0;
}

// Methods

PyObject* Entity3D::py_path_to(PyEntity3DObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"x", "z", "pos", NULL};

    int x = -1, z = -1;
    PyObject* pos_obj = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|iiO", const_cast<char**>(kwlist),
            &x, &z, &pos_obj)) {
        return NULL;
    }

    // Parse position from tuple if provided
    if (pos_obj && pos_obj != Py_None) {
        if (PyTuple_Check(pos_obj) && PyTuple_Size(pos_obj) >= 2) {
            x = PyLong_AsLong(PyTuple_GetItem(pos_obj, 0));
            z = PyLong_AsLong(PyTuple_GetItem(pos_obj, 1));
            if (PyErr_Occurred()) return NULL;
        }
    }

    if (x < 0 || z < 0) {
        PyErr_SetString(PyExc_ValueError, "Target position required");
        return NULL;
    }

    auto path = self->data->pathTo(x, z);

    PyObject* path_list = PyList_New(path.size());
    for (size_t i = 0; i < path.size(); ++i) {
        PyObject* tuple = PyTuple_Pack(2,
            PyLong_FromLong(path[i].first),
            PyLong_FromLong(path[i].second));
        PyList_SET_ITEM(path_list, i, tuple);
    }
    return path_list;
}

PyObject* Entity3D::py_teleport(PyEntity3DObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"x", "z", "pos", NULL};

    int x = -1, z = -1;
    PyObject* pos_obj = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|iiO", const_cast<char**>(kwlist),
            &x, &z, &pos_obj)) {
        return NULL;
    }

    // Parse position from tuple if provided
    if (pos_obj && pos_obj != Py_None) {
        if (PyTuple_Check(pos_obj) && PyTuple_Size(pos_obj) >= 2) {
            x = PyLong_AsLong(PyTuple_GetItem(pos_obj, 0));
            z = PyLong_AsLong(PyTuple_GetItem(pos_obj, 1));
            if (PyErr_Occurred()) return NULL;
        }
    }

    if (x < 0 || z < 0) {
        PyErr_SetString(PyExc_ValueError, "Target position required");
        return NULL;
    }

    self->data->teleportTo(x, z);
    Py_RETURN_NONE;
}

PyObject* Entity3D::py_at(PyEntity3DObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"x", "z", NULL};

    int x, z;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "ii", const_cast<char**>(kwlist), &x, &z)) {
        return NULL;
    }

    const auto& state = self->data->getVoxelState(x, z);
    return Py_BuildValue("{s:O,s:O}",
        "visible", state.visible ? Py_True : Py_False,
        "discovered", state.discovered ? Py_True : Py_False);
}

PyObject* Entity3D::py_update_visibility(PyEntity3DObject* self, PyObject* args)
{
    self->data->updateVisibility();
    Py_RETURN_NONE;
}

PyObject* Entity3D::py_animate(PyEntity3DObject* self, PyObject* args, PyObject* kwds)
{
    // TODO: Implement animation shorthand similar to UIEntity
    // For now, return None
    PyErr_SetString(PyExc_NotImplementedError, "Entity3D.animate() not yet implemented");
    return NULL;
}

// Method and GetSet tables

PyMethodDef Entity3D::methods[] = {
    {"path_to", (PyCFunction)Entity3D::py_path_to, METH_VARARGS | METH_KEYWORDS,
     "path_to(x, z) or path_to(pos=(x, z)) -> list\n\n"
     "Compute A* path to target position.\n"
     "Returns list of (x, z) tuples, or empty list if no path exists."},
    {"teleport", (PyCFunction)Entity3D::py_teleport, METH_VARARGS | METH_KEYWORDS,
     "teleport(x, z) or teleport(pos=(x, z))\n\n"
     "Instantly move to target position without animation."},
    {"at", (PyCFunction)Entity3D::py_at, METH_VARARGS | METH_KEYWORDS,
     "at(x, z) -> dict\n\n"
     "Get visibility state for a cell from this entity's perspective.\n"
     "Returns dict with 'visible' and 'discovered' boolean keys."},
    {"update_visibility", (PyCFunction)Entity3D::py_update_visibility, METH_NOARGS,
     "update_visibility()\n\n"
     "Recompute field of view from current position."},
    {"animate", (PyCFunction)Entity3D::py_animate, METH_VARARGS | METH_KEYWORDS,
     "animate(property, target, duration, easing=None, callback=None)\n\n"
     "Animate a property over time. (Not yet implemented)"},
    {NULL}  // Sentinel
};

PyGetSetDef Entity3D::getsetters[] = {
    {"pos", (getter)Entity3D::get_pos, (setter)Entity3D::set_pos,
     "Grid position (x, z). Setting triggers smooth movement.", NULL},
    {"grid_pos", (getter)Entity3D::get_grid_pos, (setter)Entity3D::set_grid_pos,
     "Grid position (x, z). Same as pos.", NULL},
    {"world_pos", (getter)Entity3D::get_world_pos, NULL,
     "Current world position (x, y, z) (read-only). Includes animation interpolation.", NULL},
    {"rotation", (getter)Entity3D::get_rotation, (setter)Entity3D::set_rotation,
     "Y-axis rotation in degrees.", NULL},
    {"scale", (getter)Entity3D::get_scale, (setter)Entity3D::set_scale,
     "Uniform scale factor. Can also set as (x, y, z) tuple.", NULL},
    {"visible", (getter)Entity3D::get_visible, (setter)Entity3D::set_visible,
     "Visibility state.", NULL},
    {"color", (getter)Entity3D::get_color, (setter)Entity3D::set_color,
     "Entity render color.", NULL},
    {"viewport", (getter)Entity3D::get_viewport, NULL,
     "Owning Viewport3D (read-only).", NULL},
    {"model", (getter)Entity3D::get_model, (setter)Entity3D::set_model,
     "3D model (Model3D). If None, uses placeholder cube.", NULL},
    {NULL}  // Sentinel
};

} // namespace mcrf

// Methods array for PyTypeObject
PyMethodDef Entity3D_methods[] = {
    {NULL}  // Will be populated from Entity3D::methods
};
