// Model3D.h - 3D model resource for McRogueFace
// Supports loading from glTF 2.0 (.glb) files and procedural primitives

#pragma once

#include "Common.h"
#include "Math3D.h"
#include "MeshLayer.h"  // For MeshVertex
#include "Python.h"
#include "structmember.h"
#include <memory>
#include <string>
#include <vector>

namespace mcrf {

// Forward declarations
class Shader3D;

// =============================================================================
// Bone - Single bone in a skeleton
// =============================================================================

struct Bone {
    std::string name;
    int parent_index = -1;       // -1 for root bones
    mat4 inverse_bind_matrix;    // Transforms from model space to bone space
    mat4 local_transform;        // Default local transform (rest pose)
};

// =============================================================================
// Skeleton - Bone hierarchy for skeletal animation
// =============================================================================

struct Skeleton {
    std::vector<Bone> bones;
    std::vector<int> root_bones;  // Indices of bones with parent_index == -1

    /// Find bone by name, returns -1 if not found
    int findBone(const std::string& name) const {
        for (size_t i = 0; i < bones.size(); i++) {
            if (bones[i].name == name) return static_cast<int>(i);
        }
        return -1;
    }

    /// Compute global (model-space) transforms for all bones
    void computeGlobalTransforms(const std::vector<mat4>& local_transforms,
                                  std::vector<mat4>& global_out) const {
        global_out.resize(bones.size());
        for (size_t i = 0; i < bones.size(); i++) {
            if (bones[i].parent_index < 0) {
                global_out[i] = local_transforms[i];
            } else {
                global_out[i] = global_out[bones[i].parent_index] * local_transforms[i];
            }
        }
    }

    /// Compute final bone matrices for shader (global * inverse_bind)
    void computeBoneMatrices(const std::vector<mat4>& global_transforms,
                              std::vector<mat4>& matrices_out) const {
        matrices_out.resize(bones.size());
        for (size_t i = 0; i < bones.size(); i++) {
            matrices_out[i] = global_transforms[i] * bones[i].inverse_bind_matrix;
        }
    }
};

// =============================================================================
// AnimationChannel - Animates a single property of a single bone
// =============================================================================

struct AnimationChannel {
    int bone_index = -1;

    enum class Path {
        Translation,
        Rotation,
        Scale
    } path = Path::Translation;

    // Keyframe times (shared for all values in this channel)
    std::vector<float> times;

    // Keyframe values (only one of these is populated based on path)
    std::vector<vec3> translations;
    std::vector<quat> rotations;
    std::vector<vec3> scales;

    /// Sample the channel at a given time, returning the interpolated transform component
    /// For Translation/Scale: writes to trans_out
    /// For Rotation: writes to rot_out
    void sample(float time, vec3& trans_out, quat& rot_out, vec3& scale_out) const;
};

// =============================================================================
// AnimationClip - Named animation containing multiple channels
// =============================================================================

struct AnimationClip {
    std::string name;
    float duration = 0.0f;
    std::vector<AnimationChannel> channels;

    /// Sample the animation at a given time, producing bone local transforms
    /// @param time Current time in the animation
    /// @param num_bones Total number of bones (for output sizing)
    /// @param default_transforms Default local transforms for bones without animation
    /// @param local_out Output: interpolated local transforms for each bone
    void sample(float time, size_t num_bones,
                const std::vector<mat4>& default_transforms,
                std::vector<mat4>& local_out) const;
};

// =============================================================================
// SkinnedVertex - Vertex with bone weights for skeletal animation
// =============================================================================

struct SkinnedVertex {
    vec3 position;
    vec2 texcoord;
    vec3 normal;
    vec4 color;
    vec4 bone_ids;      // Up to 4 bone indices (as floats for GLES2 compatibility)
    vec4 bone_weights;  // Corresponding weights (should sum to 1.0)
};

// =============================================================================
// SkinnedMesh - Submesh with skinning data
// =============================================================================

struct SkinnedMesh {
    unsigned int vbo = 0;
    unsigned int ebo = 0;
    int vertex_count = 0;
    int index_count = 0;
    int material_index = -1;
    bool is_skinned = false;    // True if this mesh has bone weights

    SkinnedMesh() = default;
    ~SkinnedMesh() = default;

    SkinnedMesh(const SkinnedMesh&) = delete;
    SkinnedMesh& operator=(const SkinnedMesh&) = delete;
    SkinnedMesh(SkinnedMesh&& other) noexcept;
    SkinnedMesh& operator=(SkinnedMesh&& other) noexcept;
};

// =============================================================================
// ModelMesh - Single submesh within a Model3D (legacy non-skinned)
// =============================================================================

struct ModelMesh {
    unsigned int vbo = 0;      // Vertex buffer object
    unsigned int ebo = 0;      // Element (index) buffer object
    int vertex_count = 0;      // Number of vertices
    int index_count = 0;       // Number of indices (0 if non-indexed)
    int material_index = -1;   // Index into materials array (-1 = no material)

    ModelMesh() = default;
    ~ModelMesh() = default;

    // Move only
    ModelMesh(const ModelMesh&) = delete;
    ModelMesh& operator=(const ModelMesh&) = delete;
    ModelMesh(ModelMesh&& other) noexcept;
    ModelMesh& operator=(ModelMesh&& other) noexcept;
};

// =============================================================================
// Model3D - 3D model resource
// =============================================================================

class Model3D : public std::enable_shared_from_this<Model3D> {
public:
    // Python integration
    PyObject* self = nullptr;
    uint64_t serial_number = 0;

    Model3D();
    ~Model3D();

    // No copy, allow move
    Model3D(const Model3D&) = delete;
    Model3D& operator=(const Model3D&) = delete;
    Model3D(Model3D&& other) noexcept;
    Model3D& operator=(Model3D&& other) noexcept;

    // =========================================================================
    // Loading
    // =========================================================================

    /// Load model from glTF 2.0 binary file (.glb)
    /// @param path Path to the .glb file
    /// @return Shared pointer to loaded model, or nullptr on failure
    static std::shared_ptr<Model3D> load(const std::string& path);

    /// Get last error message from load()
    static const std::string& getLastError() { return lastError_; }

    // =========================================================================
    // Procedural Primitives
    // =========================================================================

    /// Create a unit cube (1x1x1 centered at origin)
    static std::shared_ptr<Model3D> cube(float size = 1.0f);

    /// Create a flat plane
    /// @param width Size along X axis
    /// @param depth Size along Z axis
    /// @param segments Subdivisions (1 = single quad)
    static std::shared_ptr<Model3D> plane(float width = 1.0f, float depth = 1.0f, int segments = 1);

    /// Create a UV sphere
    /// @param radius Sphere radius
    /// @param segments Horizontal segments (longitude)
    /// @param rings Vertical rings (latitude)
    static std::shared_ptr<Model3D> sphere(float radius = 0.5f, int segments = 16, int rings = 12);

    // =========================================================================
    // Model Information
    // =========================================================================

    /// Get model name (from file or "primitive")
    const std::string& getName() const { return name_; }
    void setName(const std::string& n) { name_ = n; }

    /// Get total vertex count across all meshes
    int getVertexCount() const;

    /// Get total triangle count across all meshes
    int getTriangleCount() const;

    /// Get axis-aligned bounding box
    /// @return Pair of (min, max) corners
    std::pair<vec3, vec3> getBounds() const { return {bounds_min_, bounds_max_}; }

    /// Check if model has skeletal animation data
    bool hasSkeleton() const { return has_skeleton_; }

    /// Get number of submeshes (regular + skinned)
    size_t getMeshCount() const { return meshes_.size() + skinned_meshes_.size(); }

    // =========================================================================
    // Skeleton & Animation
    // =========================================================================

    /// Get skeleton (may be empty if no skeleton)
    const Skeleton& getSkeleton() const { return skeleton_; }

    /// Get number of bones
    size_t getBoneCount() const { return skeleton_.bones.size(); }

    /// Get animation clips
    const std::vector<AnimationClip>& getAnimationClips() const { return animation_clips_; }

    /// Get animation clip names
    std::vector<std::string> getAnimationClipNames() const {
        std::vector<std::string> names;
        for (const auto& clip : animation_clips_) {
            names.push_back(clip.name);
        }
        return names;
    }

    /// Find animation clip by name (returns nullptr if not found)
    const AnimationClip* findClip(const std::string& name) const {
        for (const auto& clip : animation_clips_) {
            if (clip.name == name) return &clip;
        }
        return nullptr;
    }

    /// Get default bone transforms (rest pose)
    const std::vector<mat4>& getDefaultBoneTransforms() const { return default_bone_transforms_; }

    // =========================================================================
    // Rendering
    // =========================================================================

    /// Render all meshes
    /// @param shader Shader program handle (already bound)
    /// @param model Model transformation matrix
    /// @param view View matrix
    /// @param projection Projection matrix
    void render(unsigned int shader, const mat4& model, const mat4& view, const mat4& projection);

    /// Render with skeletal animation
    /// @param shader Shader program handle (already bound, should be skinned shader)
    /// @param model Model transformation matrix
    /// @param view View matrix
    /// @param projection Projection matrix
    /// @param bone_matrices Final bone matrices (global * inverse_bind)
    void renderSkinned(unsigned int shader, const mat4& model, const mat4& view,
                       const mat4& projection, const std::vector<mat4>& bone_matrices);

    // =========================================================================
    // Python API
    // =========================================================================

    static int init(PyObject* self, PyObject* args, PyObject* kwds);
    static PyObject* repr(PyObject* self);

    // Class methods (static constructors)
    static PyObject* py_cube(PyObject* cls, PyObject* args, PyObject* kwds);
    static PyObject* py_plane(PyObject* cls, PyObject* args, PyObject* kwds);
    static PyObject* py_sphere(PyObject* cls, PyObject* args, PyObject* kwds);

    // Property getters
    static PyObject* get_vertex_count(PyObject* self, void* closure);
    static PyObject* get_triangle_count(PyObject* self, void* closure);
    static PyObject* get_has_skeleton(PyObject* self, void* closure);
    static PyObject* get_bounds(PyObject* self, void* closure);
    static PyObject* get_name(PyObject* self, void* closure);
    static PyObject* get_mesh_count(PyObject* self, void* closure);
    static PyObject* get_bone_count(PyObject* self, void* closure);
    static PyObject* get_animation_clips(PyObject* self, void* closure);

    static PyMethodDef methods[];
    static PyGetSetDef getsetters[];

private:
    // Model data
    std::string name_;
    std::vector<ModelMesh> meshes_;
    std::vector<SkinnedMesh> skinned_meshes_;  // Skinned meshes with bone weights

    // Bounds
    vec3 bounds_min_ = vec3(0, 0, 0);
    vec3 bounds_max_ = vec3(0, 0, 0);

    // Skeletal animation data
    bool has_skeleton_ = false;
    Skeleton skeleton_;
    std::vector<AnimationClip> animation_clips_;
    std::vector<mat4> default_bone_transforms_;  // Rest pose local transforms

    // Error handling
    static std::string lastError_;

    // Helper methods
    void cleanupGPU();
    void computeBounds(const std::vector<MeshVertex>& vertices);

    /// Create VBO/EBO from vertex and index data
    /// @return ModelMesh with GPU resources allocated
    static ModelMesh createMesh(const std::vector<MeshVertex>& vertices,
                                const std::vector<uint32_t>& indices);

    /// Create VBO/EBO from skinned vertex and index data
    static SkinnedMesh createSkinnedMesh(const std::vector<SkinnedVertex>& vertices,
                                          const std::vector<uint32_t>& indices);

    // glTF loading helpers
    void loadSkeleton(void* cgltf_data);     // void* to avoid header dependency
    void loadAnimations(void* cgltf_data);
    int findJointIndex(void* cgltf_skin, void* node);
};

} // namespace mcrf

// =============================================================================
// Python type definition
// =============================================================================

typedef struct PyModel3DObject {
    PyObject_HEAD
    std::shared_ptr<mcrf::Model3D> data;
    PyObject* weakreflist;
} PyModel3DObject;

namespace mcrfpydef {

inline PyTypeObject PyModel3DType = {
    .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
    .tp_name = "mcrfpy.Model3D",
    .tp_basicsize = sizeof(PyModel3DObject),
    .tp_itemsize = 0,
    .tp_dealloc = (destructor)[](PyObject* self)
    {
        PyModel3DObject* obj = (PyModel3DObject*)self;
        PyObject_GC_UnTrack(self);
        if (obj->weakreflist != NULL) {
            PyObject_ClearWeakRefs(self);
        }
        obj->data.reset();
        Py_TYPE(self)->tp_free(self);
    },
    .tp_repr = mcrf::Model3D::repr,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC,
    .tp_doc = PyDoc_STR(
        "Model3D(path=None)\n\n"
        "A 3D model resource that can be rendered by Entity3D.\n\n"
        "Args:\n"
        "    path (str, optional): Path to .glb file to load. If None, creates empty model.\n\n"
        "Class Methods:\n"
        "    cube(size=1.0) -> Model3D: Create a unit cube\n"
        "    plane(width=1.0, depth=1.0, segments=1) -> Model3D: Create a flat plane\n"
        "    sphere(radius=0.5, segments=16, rings=12) -> Model3D: Create a UV sphere\n\n"
        "Properties:\n"
        "    name (str, read-only): Model name\n"
        "    vertex_count (int, read-only): Total vertices across all meshes\n"
        "    triangle_count (int, read-only): Total triangles across all meshes\n"
        "    has_skeleton (bool, read-only): Whether model has skeletal animation data\n"
        "    bounds (tuple, read-only): AABB as ((min_x, min_y, min_z), (max_x, max_y, max_z))\n"
        "    mesh_count (int, read-only): Number of submeshes\n"
        "    bone_count (int, read-only): Number of bones in skeleton\n"
        "    animation_clips (list, read-only): List of animation clip names"
    ),
    .tp_traverse = [](PyObject* self, visitproc visit, void* arg) -> int {
        return 0;
    },
    .tp_clear = [](PyObject* self) -> int {
        return 0;
    },
    .tp_methods = mcrf::Model3D::methods,
    .tp_getset = mcrf::Model3D::getsetters,
    .tp_init = mcrf::Model3D::init,
    .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
    {
        PyModel3DObject* self = (PyModel3DObject*)type->tp_alloc(type, 0);
        if (self) {
            self->data = std::make_shared<mcrf::Model3D>();
            self->weakreflist = nullptr;
        }
        return (PyObject*)self;
    }
};

} // namespace mcrfpydef
