// Billboard.h - Camera-facing 3D sprite for McRogueFace
// Supports camera-facing rotation modes for trees, items, particles, etc.

#pragma once

#include "Common.h"
#include "Math3D.h"
#include "Python.h"
#include "structmember.h"
#include <memory>

// Forward declaration
class PyTexture;

namespace mcrf {

// =============================================================================
// BillboardFacing - Billboard rotation mode
// =============================================================================

enum class BillboardFacing {
    Camera,     // Full rotation to always face camera
    CameraY,    // Only Y-axis rotation (stays upright)
    Fixed       // No automatic rotation, uses theta/phi angles
};

// =============================================================================
// Billboard - Camera-facing 3D sprite
// =============================================================================

class Billboard : public std::enable_shared_from_this<Billboard> {
public:
    // Python integration
    PyObject* self = nullptr;
    uint64_t serial_number = 0;

    Billboard();
    Billboard(std::shared_ptr<PyTexture> texture, int spriteIndex, const vec3& pos,
              float scale = 1.0f, BillboardFacing facing = BillboardFacing::CameraY);
    ~Billboard();

    // No copy, allow move
    Billboard(const Billboard&) = delete;
    Billboard& operator=(const Billboard&) = delete;

    // =========================================================================
    // Properties
    // =========================================================================

    std::shared_ptr<PyTexture> getTexture() const { return texture_; }
    void setTexture(std::shared_ptr<PyTexture> tex) { texture_ = tex; }

    int getSpriteIndex() const { return spriteIndex_; }
    void setSpriteIndex(int idx) { spriteIndex_ = idx; }

    vec3 getPosition() const { return position_; }
    void setPosition(const vec3& pos) { position_ = pos; }

    float getScale() const { return scale_; }
    void setScale(float s) { scale_ = s; }

    BillboardFacing getFacing() const { return facing_; }
    void setFacing(BillboardFacing f) { facing_ = f; }

    // Fixed facing angles (radians)
    float getTheta() const { return theta_; }
    void setTheta(float t) { theta_ = t; }

    float getPhi() const { return phi_; }
    void setPhi(float p) { phi_ = p; }

    float getOpacity() const { return opacity_; }
    void setOpacity(float o) { opacity_ = o < 0 ? 0 : (o > 1 ? 1 : o); }

    bool isVisible() const { return visible_; }
    void setVisible(bool v) { visible_ = v; }

    // Sprite sheet configuration
    void setSpriteSheetLayout(int tilesPerRow, int tilesPerCol);
    int getTilesPerRow() const { return tilesPerRow_; }
    int getTilesPerCol() const { return tilesPerCol_; }

    // =========================================================================
    // Rendering
    // =========================================================================

    /// Render the billboard
    /// @param shader Shader program handle
    /// @param view View matrix
    /// @param projection Projection matrix
    /// @param cameraPos Camera world position (for facing computation)
    void render(unsigned int shader, const mat4& view, const mat4& projection,
                const vec3& cameraPos);

    // =========================================================================
    // Static Initialization
    // =========================================================================

    /// Initialize shared quad geometry (call once at startup)
    static void initSharedGeometry();

    /// Cleanup shared geometry (call at shutdown)
    static void cleanupSharedGeometry();

    // =========================================================================
    // Python API
    // =========================================================================

    static int init(PyObject* self, PyObject* args, PyObject* kwds);
    static PyObject* repr(PyObject* self);

    static PyObject* get_texture(PyObject* self, void* closure);
    static int set_texture(PyObject* self, PyObject* value, void* closure);
    static PyObject* get_sprite_index(PyObject* self, void* closure);
    static int set_sprite_index(PyObject* self, PyObject* value, void* closure);
    static PyObject* get_pos(PyObject* self, void* closure);
    static int set_pos(PyObject* self, PyObject* value, void* closure);
    static PyObject* get_scale(PyObject* self, void* closure);
    static int set_scale(PyObject* self, PyObject* value, void* closure);
    static PyObject* get_facing(PyObject* self, void* closure);
    static int set_facing(PyObject* self, PyObject* value, void* closure);
    static PyObject* get_theta(PyObject* self, void* closure);
    static int set_theta(PyObject* self, PyObject* value, void* closure);
    static PyObject* get_phi(PyObject* self, void* closure);
    static int set_phi(PyObject* self, PyObject* value, void* closure);
    static PyObject* get_opacity(PyObject* self, void* closure);
    static int set_opacity(PyObject* self, PyObject* value, void* closure);
    static PyObject* get_visible(PyObject* self, void* closure);
    static int set_visible(PyObject* self, PyObject* value, void* closure);

    static PyGetSetDef getsetters[];

private:
    std::shared_ptr<PyTexture> texture_;  // Texture wrapper
    int spriteIndex_ = 0;
    vec3 position_;
    float scale_ = 1.0f;
    BillboardFacing facing_ = BillboardFacing::CameraY;
    float theta_ = 0.0f;  // Horizontal rotation for Fixed mode
    float phi_ = 0.0f;    // Vertical tilt for Fixed mode
    float opacity_ = 1.0f;
    bool visible_ = true;

    // Sprite sheet configuration
    int tilesPerRow_ = 1;
    int tilesPerCol_ = 1;

    // Shared quad geometry (one VBO for all billboards)
    static unsigned int sharedVBO_;
    static unsigned int sharedEBO_;
    static bool geometryInitialized_;

    // Compute billboard model matrix based on facing mode
    mat4 computeModelMatrix(const vec3& cameraPos, const mat4& view);
};

} // namespace mcrf

// =============================================================================
// Python type definition
// =============================================================================

typedef struct PyBillboardObject {
    PyObject_HEAD
    std::shared_ptr<mcrf::Billboard> data;
    PyObject* weakreflist;
} PyBillboardObject;

namespace mcrfpydef {

inline PyTypeObject PyBillboardType = {
    .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
    .tp_name = "mcrfpy.Billboard",
    .tp_basicsize = sizeof(PyBillboardObject),
    .tp_itemsize = 0,
    .tp_dealloc = (destructor)[](PyObject* self)
    {
        PyBillboardObject* obj = (PyBillboardObject*)self;
        PyObject_GC_UnTrack(self);
        if (obj->weakreflist != NULL) {
            PyObject_ClearWeakRefs(self);
        }
        obj->data.reset();
        Py_TYPE(self)->tp_free(self);
    },
    .tp_repr = mcrf::Billboard::repr,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC,
    .tp_doc = PyDoc_STR(
        "Billboard(texture=None, sprite_index=0, pos=(0,0,0), scale=1.0, facing='camera_y')\n\n"
        "A camera-facing 3D sprite for trees, items, particles, etc.\n\n"
        "Args:\n"
        "    texture (Texture, optional): Sprite sheet texture. Default: None\n"
        "    sprite_index (int): Index into sprite sheet. Default: 0\n"
        "    pos (tuple): World position (x, y, z). Default: (0, 0, 0)\n"
        "    scale (float): Uniform scale factor. Default: 1.0\n"
        "    facing (str): Facing mode - 'camera', 'camera_y', or 'fixed'. Default: 'camera_y'\n\n"
        "Properties:\n"
        "    texture (Texture): Sprite sheet texture\n"
        "    sprite_index (int): Index into sprite sheet\n"
        "    pos (tuple): World position (x, y, z)\n"
        "    scale (float): Uniform scale factor\n"
        "    facing (str): Facing mode - 'camera', 'camera_y', or 'fixed'\n"
        "    theta (float): Horizontal rotation for 'fixed' mode (radians)\n"
        "    phi (float): Vertical tilt for 'fixed' mode (radians)\n"
        "    opacity (float): Opacity 0.0 (transparent) to 1.0 (opaque)\n"
        "    visible (bool): Visibility state"
    ),
    .tp_traverse = [](PyObject* self, visitproc visit, void* arg) -> int {
        return 0;
    },
    .tp_clear = [](PyObject* self) -> int {
        return 0;
    },
    .tp_getset = mcrf::Billboard::getsetters,
    .tp_init = mcrf::Billboard::init,
    .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
    {
        PyBillboardObject* self = (PyBillboardObject*)type->tp_alloc(type, 0);
        if (self) {
            // Use placement new to properly construct the shared_ptr
            // tp_alloc zeroes memory but doesn't call C++ constructors
            new (&self->data) std::shared_ptr<mcrf::Billboard>(std::make_shared<mcrf::Billboard>());
            self->weakreflist = nullptr;
        }
        return (PyObject*)self;
    }
};

} // namespace mcrfpydef
