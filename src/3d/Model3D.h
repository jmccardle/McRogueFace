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
// ModelMesh - Single submesh within a Model3D
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

    /// Get number of submeshes
    size_t getMeshCount() const { return meshes_.size(); }

    // =========================================================================
    // Rendering
    // =========================================================================

    /// Render all meshes
    /// @param shader Shader program handle (already bound)
    /// @param model Model transformation matrix
    /// @param view View matrix
    /// @param projection Projection matrix
    void render(unsigned int shader, const mat4& model, const mat4& view, const mat4& projection);

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

    static PyMethodDef methods[];
    static PyGetSetDef getsetters[];

private:
    // Model data
    std::string name_;
    std::vector<ModelMesh> meshes_;

    // Bounds
    vec3 bounds_min_ = vec3(0, 0, 0);
    vec3 bounds_max_ = vec3(0, 0, 0);

    // Future: skeletal animation data
    bool has_skeleton_ = false;

    // Error handling
    static std::string lastError_;

    // Helper methods
    void cleanupGPU();
    void computeBounds(const std::vector<MeshVertex>& vertices);

    /// Create VBO/EBO from vertex and index data
    /// @return ModelMesh with GPU resources allocated
    static ModelMesh createMesh(const std::vector<MeshVertex>& vertices,
                                const std::vector<uint32_t>& indices);
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
        "    mesh_count (int, read-only): Number of submeshes"
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
