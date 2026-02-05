// Model3D.cpp - 3D model resource implementation

#include "Model3D.h"
#include "Shader3D.h"
#include "cgltf.h"
#include "../platform/GLContext.h"

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
    #include <glad/glad.h>
    #define MCRF_HAS_GL 1
#endif

#include <cmath>
#include <algorithm>

namespace mcrf {

// Static members
std::string Model3D::lastError_;

// =============================================================================
// ModelMesh Implementation
// =============================================================================

ModelMesh::ModelMesh(ModelMesh&& other) noexcept
    : vbo(other.vbo)
    , ebo(other.ebo)
    , vertex_count(other.vertex_count)
    , index_count(other.index_count)
    , material_index(other.material_index)
{
    other.vbo = 0;
    other.ebo = 0;
    other.vertex_count = 0;
    other.index_count = 0;
}

ModelMesh& ModelMesh::operator=(ModelMesh&& other) noexcept
{
    if (this != &other) {
        vbo = other.vbo;
        ebo = other.ebo;
        vertex_count = other.vertex_count;
        index_count = other.index_count;
        material_index = other.material_index;
        other.vbo = 0;
        other.ebo = 0;
        other.vertex_count = 0;
        other.index_count = 0;
    }
    return *this;
}

// =============================================================================
// Model3D Implementation
// =============================================================================

Model3D::Model3D()
    : name_("unnamed")
{
}

Model3D::~Model3D()
{
    cleanupGPU();
}

Model3D::Model3D(Model3D&& other) noexcept
    : name_(std::move(other.name_))
    , meshes_(std::move(other.meshes_))
    , bounds_min_(other.bounds_min_)
    , bounds_max_(other.bounds_max_)
    , has_skeleton_(other.has_skeleton_)
{
}

Model3D& Model3D::operator=(Model3D&& other) noexcept
{
    if (this != &other) {
        cleanupGPU();
        name_ = std::move(other.name_);
        meshes_ = std::move(other.meshes_);
        bounds_min_ = other.bounds_min_;
        bounds_max_ = other.bounds_max_;
        has_skeleton_ = other.has_skeleton_;
    }
    return *this;
}

void Model3D::cleanupGPU()
{
#ifdef MCRF_HAS_GL
    if (gl::isGLReady()) {
        for (auto& mesh : meshes_) {
            if (mesh.vbo) {
                glDeleteBuffers(1, &mesh.vbo);
                mesh.vbo = 0;
            }
            if (mesh.ebo) {
                glDeleteBuffers(1, &mesh.ebo);
                mesh.ebo = 0;
            }
        }
    }
#endif
    meshes_.clear();
}

void Model3D::computeBounds(const std::vector<MeshVertex>& vertices)
{
    if (vertices.empty()) {
        bounds_min_ = vec3(0, 0, 0);
        bounds_max_ = vec3(0, 0, 0);
        return;
    }

    bounds_min_ = vertices[0].position;
    bounds_max_ = vertices[0].position;

    for (const auto& v : vertices) {
        bounds_min_.x = std::min(bounds_min_.x, v.position.x);
        bounds_min_.y = std::min(bounds_min_.y, v.position.y);
        bounds_min_.z = std::min(bounds_min_.z, v.position.z);
        bounds_max_.x = std::max(bounds_max_.x, v.position.x);
        bounds_max_.y = std::max(bounds_max_.y, v.position.y);
        bounds_max_.z = std::max(bounds_max_.z, v.position.z);
    }
}

ModelMesh Model3D::createMesh(const std::vector<MeshVertex>& vertices,
                               const std::vector<uint32_t>& indices)
{
    ModelMesh mesh;
    mesh.vertex_count = static_cast<int>(vertices.size());
    mesh.index_count = static_cast<int>(indices.size());

#ifdef MCRF_HAS_GL
    // Only create GPU resources if GL is ready
    if (!gl::isGLReady()) {
        return mesh;
    }

    // Create VBO
    glGenBuffers(1, &mesh.vbo);
    glBindBuffer(GL_ARRAY_BUFFER, mesh.vbo);
    glBufferData(GL_ARRAY_BUFFER,
                 vertices.size() * sizeof(MeshVertex),
                 vertices.data(),
                 GL_STATIC_DRAW);

    // Create EBO if indexed
    if (!indices.empty()) {
        glGenBuffers(1, &mesh.ebo);
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, mesh.ebo);
        glBufferData(GL_ELEMENT_ARRAY_BUFFER,
                     indices.size() * sizeof(uint32_t),
                     indices.data(),
                     GL_STATIC_DRAW);
    }

    glBindBuffer(GL_ARRAY_BUFFER, 0);
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0);
#endif

    return mesh;
}

// =============================================================================
// Model Information
// =============================================================================

int Model3D::getVertexCount() const
{
    int total = 0;
    for (const auto& mesh : meshes_) {
        total += mesh.vertex_count;
    }
    return total;
}

int Model3D::getTriangleCount() const
{
    int total = 0;
    for (const auto& mesh : meshes_) {
        if (mesh.index_count > 0) {
            total += mesh.index_count / 3;
        } else {
            total += mesh.vertex_count / 3;
        }
    }
    return total;
}

// =============================================================================
// Rendering
// =============================================================================

void Model3D::render(unsigned int shader, const mat4& model,
                     const mat4& view, const mat4& projection)
{
#ifdef MCRF_HAS_GL
    if (!gl::isGLReady()) return;

    // Calculate MVP
    mat4 mvp = projection * view * model;

    // Set uniforms (shader should already be bound)
    int mvpLoc = glGetUniformLocation(shader, "u_mvp");
    int modelLoc = glGetUniformLocation(shader, "u_model");

    if (mvpLoc >= 0) glUniformMatrix4fv(mvpLoc, 1, GL_FALSE, mvp.data());
    if (modelLoc >= 0) glUniformMatrix4fv(modelLoc, 1, GL_FALSE, model.data());

    // Render each mesh
    for (const auto& mesh : meshes_) {
        if (mesh.vertex_count == 0) continue;

        glBindBuffer(GL_ARRAY_BUFFER, mesh.vbo);

        // Set up vertex attributes (matching MeshVertex layout)
        // Position (location 0)
        glEnableVertexAttribArray(Shader3D::ATTRIB_POSITION);
        glVertexAttribPointer(Shader3D::ATTRIB_POSITION, 3, GL_FLOAT, GL_FALSE,
                              sizeof(MeshVertex), (void*)offsetof(MeshVertex, position));

        // Texcoord (location 1)
        glEnableVertexAttribArray(Shader3D::ATTRIB_TEXCOORD);
        glVertexAttribPointer(Shader3D::ATTRIB_TEXCOORD, 2, GL_FLOAT, GL_FALSE,
                              sizeof(MeshVertex), (void*)offsetof(MeshVertex, texcoord));

        // Normal (location 2)
        glEnableVertexAttribArray(Shader3D::ATTRIB_NORMAL);
        glVertexAttribPointer(Shader3D::ATTRIB_NORMAL, 3, GL_FLOAT, GL_FALSE,
                              sizeof(MeshVertex), (void*)offsetof(MeshVertex, normal));

        // Color (location 3)
        glEnableVertexAttribArray(Shader3D::ATTRIB_COLOR);
        glVertexAttribPointer(Shader3D::ATTRIB_COLOR, 4, GL_FLOAT, GL_FALSE,
                              sizeof(MeshVertex), (void*)offsetof(MeshVertex, color));

        // Draw
        if (mesh.index_count > 0) {
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, mesh.ebo);
            glDrawElements(GL_TRIANGLES, mesh.index_count, GL_UNSIGNED_INT, 0);
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0);
        } else {
            glDrawArrays(GL_TRIANGLES, 0, mesh.vertex_count);
        }

        // Cleanup
        glDisableVertexAttribArray(Shader3D::ATTRIB_POSITION);
        glDisableVertexAttribArray(Shader3D::ATTRIB_TEXCOORD);
        glDisableVertexAttribArray(Shader3D::ATTRIB_NORMAL);
        glDisableVertexAttribArray(Shader3D::ATTRIB_COLOR);
    }

    glBindBuffer(GL_ARRAY_BUFFER, 0);
#endif
}

// =============================================================================
// Procedural Primitives
// =============================================================================

std::shared_ptr<Model3D> Model3D::cube(float size)
{
    auto model = std::make_shared<Model3D>();
    model->name_ = "cube";

    float s = size * 0.5f;

    // 24 vertices (4 per face for proper normals)
    std::vector<MeshVertex> vertices;
    vertices.reserve(24);

    // Helper to add a face
    auto addFace = [&](vec3 p0, vec3 p1, vec3 p2, vec3 p3, vec3 normal) {
        MeshVertex v;
        v.normal = normal;
        v.color = vec4(1, 1, 1, 1);

        v.position = p0; v.texcoord = vec2(0, 0); vertices.push_back(v);
        v.position = p1; v.texcoord = vec2(1, 0); vertices.push_back(v);
        v.position = p2; v.texcoord = vec2(1, 1); vertices.push_back(v);
        v.position = p3; v.texcoord = vec2(0, 1); vertices.push_back(v);
    };

    // Front face (+Z)
    addFace(vec3(-s, -s,  s), vec3( s, -s,  s), vec3( s,  s,  s), vec3(-s,  s,  s), vec3(0, 0, 1));
    // Back face (-Z)
    addFace(vec3( s, -s, -s), vec3(-s, -s, -s), vec3(-s,  s, -s), vec3( s,  s, -s), vec3(0, 0, -1));
    // Right face (+X)
    addFace(vec3( s, -s,  s), vec3( s, -s, -s), vec3( s,  s, -s), vec3( s,  s,  s), vec3(1, 0, 0));
    // Left face (-X)
    addFace(vec3(-s, -s, -s), vec3(-s, -s,  s), vec3(-s,  s,  s), vec3(-s,  s, -s), vec3(-1, 0, 0));
    // Top face (+Y)
    addFace(vec3(-s,  s,  s), vec3( s,  s,  s), vec3( s,  s, -s), vec3(-s,  s, -s), vec3(0, 1, 0));
    // Bottom face (-Y)
    addFace(vec3(-s, -s, -s), vec3( s, -s, -s), vec3( s, -s,  s), vec3(-s, -s,  s), vec3(0, -1, 0));

    // Indices for 6 faces (2 triangles each)
    std::vector<uint32_t> indices;
    indices.reserve(36);
    for (int face = 0; face < 6; ++face) {
        uint32_t base = face * 4;
        indices.push_back(base + 0);
        indices.push_back(base + 1);
        indices.push_back(base + 2);
        indices.push_back(base + 0);
        indices.push_back(base + 2);
        indices.push_back(base + 3);
    }

    model->meshes_.push_back(createMesh(vertices, indices));
    model->bounds_min_ = vec3(-s, -s, -s);
    model->bounds_max_ = vec3(s, s, s);

    return model;
}

std::shared_ptr<Model3D> Model3D::plane(float width, float depth, int segments)
{
    auto model = std::make_shared<Model3D>();
    model->name_ = "plane";

    segments = std::max(1, segments);
    float hw = width * 0.5f;
    float hd = depth * 0.5f;

    std::vector<MeshVertex> vertices;
    std::vector<uint32_t> indices;

    // Generate grid of vertices
    int cols = segments + 1;
    int rows = segments + 1;
    vertices.reserve(cols * rows);

    for (int z = 0; z < rows; ++z) {
        for (int x = 0; x < cols; ++x) {
            MeshVertex v;
            float u = static_cast<float>(x) / segments;
            float w = static_cast<float>(z) / segments;

            v.position = vec3(
                -hw + u * width,
                0.0f,
                -hd + w * depth
            );
            v.texcoord = vec2(u, w);
            v.normal = vec3(0, 1, 0);
            v.color = vec4(1, 1, 1, 1);

            vertices.push_back(v);
        }
    }

    // Generate indices
    indices.reserve(segments * segments * 6);
    for (int z = 0; z < segments; ++z) {
        for (int x = 0; x < segments; ++x) {
            uint32_t i0 = z * cols + x;
            uint32_t i1 = i0 + 1;
            uint32_t i2 = i0 + cols;
            uint32_t i3 = i2 + 1;

            indices.push_back(i0);
            indices.push_back(i2);
            indices.push_back(i1);

            indices.push_back(i1);
            indices.push_back(i2);
            indices.push_back(i3);
        }
    }

    model->meshes_.push_back(createMesh(vertices, indices));
    model->bounds_min_ = vec3(-hw, 0, -hd);
    model->bounds_max_ = vec3(hw, 0, hd);

    return model;
}

std::shared_ptr<Model3D> Model3D::sphere(float radius, int segments, int rings)
{
    auto model = std::make_shared<Model3D>();
    model->name_ = "sphere";

    segments = std::max(3, segments);
    rings = std::max(2, rings);

    std::vector<MeshVertex> vertices;
    std::vector<uint32_t> indices;

    // Generate vertices
    for (int y = 0; y <= rings; ++y) {
        float v = static_cast<float>(y) / rings;
        float phi = v * PI;

        for (int x = 0; x <= segments; ++x) {
            float u = static_cast<float>(x) / segments;
            float theta = u * 2.0f * PI;

            MeshVertex vert;
            vert.normal = vec3(
                std::sin(phi) * std::cos(theta),
                std::cos(phi),
                std::sin(phi) * std::sin(theta)
            );
            vert.position = vert.normal * radius;
            vert.texcoord = vec2(u, v);
            vert.color = vec4(1, 1, 1, 1);

            vertices.push_back(vert);
        }
    }

    // Generate indices
    for (int y = 0; y < rings; ++y) {
        for (int x = 0; x < segments; ++x) {
            uint32_t i0 = y * (segments + 1) + x;
            uint32_t i1 = i0 + 1;
            uint32_t i2 = i0 + (segments + 1);
            uint32_t i3 = i2 + 1;

            indices.push_back(i0);
            indices.push_back(i2);
            indices.push_back(i1);

            indices.push_back(i1);
            indices.push_back(i2);
            indices.push_back(i3);
        }
    }

    model->meshes_.push_back(createMesh(vertices, indices));
    model->bounds_min_ = vec3(-radius, -radius, -radius);
    model->bounds_max_ = vec3(radius, radius, radius);

    return model;
}

// =============================================================================
// glTF Loading
// =============================================================================

std::shared_ptr<Model3D> Model3D::load(const std::string& path)
{
    lastError_.clear();

    cgltf_options options = {};
    cgltf_data* data = nullptr;

    // Parse the file
    cgltf_result result = cgltf_parse_file(&options, path.c_str(), &data);
    if (result != cgltf_result_success) {
        lastError_ = "Failed to parse glTF file: " + path;
        return nullptr;
    }

    // Load buffers
    result = cgltf_load_buffers(&options, data, path.c_str());
    if (result != cgltf_result_success) {
        lastError_ = "Failed to load glTF buffers: " + path;
        cgltf_free(data);
        return nullptr;
    }

    auto model = std::make_shared<Model3D>();

    // Extract filename for model name
    size_t lastSlash = path.find_last_of("/\\");
    if (lastSlash != std::string::npos) {
        model->name_ = path.substr(lastSlash + 1);
    } else {
        model->name_ = path;
    }

    // Remove extension
    size_t dot = model->name_.rfind('.');
    if (dot != std::string::npos) {
        model->name_ = model->name_.substr(0, dot);
    }

    // Check for skeleton
    model->has_skeleton_ = (data->skins_count > 0);

    // Track all vertices for bounds calculation
    std::vector<MeshVertex> allVertices;

    // Process each mesh
    for (size_t i = 0; i < data->meshes_count; ++i) {
        cgltf_mesh* mesh = &data->meshes[i];

        for (size_t j = 0; j < mesh->primitives_count; ++j) {
            cgltf_primitive* prim = &mesh->primitives[j];

            // Only support triangles
            if (prim->type != cgltf_primitive_type_triangles) {
                continue;
            }

            std::vector<vec3> positions;
            std::vector<vec3> normals;
            std::vector<vec2> texcoords;
            std::vector<vec4> colors;

            // Extract attributes
            for (size_t k = 0; k < prim->attributes_count; ++k) {
                cgltf_attribute* attr = &prim->attributes[k];
                cgltf_accessor* accessor = attr->data;

                if (attr->type == cgltf_attribute_type_position) {
                    positions.resize(accessor->count);
                    for (size_t v = 0; v < accessor->count; ++v) {
                        cgltf_accessor_read_float(accessor, v, &positions[v].x, 3);
                    }
                }
                else if (attr->type == cgltf_attribute_type_normal) {
                    normals.resize(accessor->count);
                    for (size_t v = 0; v < accessor->count; ++v) {
                        cgltf_accessor_read_float(accessor, v, &normals[v].x, 3);
                    }
                }
                else if (attr->type == cgltf_attribute_type_texcoord && attr->index == 0) {
                    texcoords.resize(accessor->count);
                    for (size_t v = 0; v < accessor->count; ++v) {
                        cgltf_accessor_read_float(accessor, v, &texcoords[v].x, 2);
                    }
                }
                else if (attr->type == cgltf_attribute_type_color && attr->index == 0) {
                    colors.resize(accessor->count);
                    for (size_t v = 0; v < accessor->count; ++v) {
                        // Color can be vec3 or vec4
                        if (accessor->type == cgltf_type_vec4) {
                            cgltf_accessor_read_float(accessor, v, &colors[v].x, 4);
                        } else {
                            cgltf_accessor_read_float(accessor, v, &colors[v].x, 3);
                            colors[v].w = 1.0f;
                        }
                    }
                }
            }

            // Skip if no positions
            if (positions.empty()) {
                continue;
            }

            // Fill in defaults for missing attributes
            size_t vertCount = positions.size();
            if (normals.empty()) {
                normals.resize(vertCount, vec3(0, 1, 0));
            }
            if (texcoords.empty()) {
                texcoords.resize(vertCount, vec2(0, 0));
            }
            if (colors.empty()) {
                colors.resize(vertCount, vec4(1, 1, 1, 1));
            }

            // Interleave vertex data
            std::vector<MeshVertex> vertices;
            vertices.reserve(vertCount);
            for (size_t v = 0; v < vertCount; ++v) {
                MeshVertex mv;
                mv.position = positions[v];
                mv.texcoord = texcoords[v];
                mv.normal = normals[v];
                mv.color = colors[v];
                vertices.push_back(mv);
                allVertices.push_back(mv);
            }

            // Extract indices
            std::vector<uint32_t> indices;
            if (prim->indices) {
                cgltf_accessor* accessor = prim->indices;
                indices.resize(accessor->count);
                for (size_t idx = 0; idx < accessor->count; ++idx) {
                    indices[idx] = static_cast<uint32_t>(cgltf_accessor_read_index(accessor, idx));
                }
            }

            // Create mesh
            model->meshes_.push_back(createMesh(vertices, indices));
        }
    }

    // Compute bounds from all vertices
    model->computeBounds(allVertices);

    cgltf_free(data);
    return model;
}

// =============================================================================
// Python API Implementation
// =============================================================================

int Model3D::init(PyObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"path", NULL};

    const char* path = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|s", const_cast<char**>(kwlist), &path)) {
        return -1;
    }

    PyModel3DObject* obj = (PyModel3DObject*)self;

    if (path && path[0] != '\0') {
        // Load from file
        obj->data = Model3D::load(path);
        if (!obj->data) {
            PyErr_SetString(PyExc_RuntimeError, Model3D::getLastError().c_str());
            return -1;
        }
    } else {
        // Empty model
        obj->data = std::make_shared<Model3D>();
    }

    return 0;
}

PyObject* Model3D::repr(PyObject* self)
{
    PyModel3DObject* obj = (PyModel3DObject*)self;
    if (!obj->data) {
        return PyUnicode_FromString("<Model3D (null)>");
    }

    char buf[256];
    snprintf(buf, sizeof(buf), "<Model3D '%s' verts=%d tris=%d%s>",
             obj->data->getName().c_str(),
             obj->data->getVertexCount(),
             obj->data->getTriangleCount(),
             obj->data->hasSkeleton() ? " skeletal" : "");
    return PyUnicode_FromString(buf);
}

PyObject* Model3D::py_cube(PyObject* cls, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"size", NULL};
    float size = 1.0f;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|f", const_cast<char**>(kwlist), &size)) {
        return NULL;
    }

    // Create new Python object
    PyTypeObject* type = (PyTypeObject*)cls;
    PyModel3DObject* obj = (PyModel3DObject*)type->tp_alloc(type, 0);
    if (!obj) return NULL;

    obj->data = Model3D::cube(size);
    obj->weakreflist = nullptr;

    return (PyObject*)obj;
}

PyObject* Model3D::py_plane(PyObject* cls, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"width", "depth", "segments", NULL};
    float width = 1.0f;
    float depth = 1.0f;
    int segments = 1;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|ffi", const_cast<char**>(kwlist),
            &width, &depth, &segments)) {
        return NULL;
    }

    PyTypeObject* type = (PyTypeObject*)cls;
    PyModel3DObject* obj = (PyModel3DObject*)type->tp_alloc(type, 0);
    if (!obj) return NULL;

    obj->data = Model3D::plane(width, depth, segments);
    obj->weakreflist = nullptr;

    return (PyObject*)obj;
}

PyObject* Model3D::py_sphere(PyObject* cls, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"radius", "segments", "rings", NULL};
    float radius = 0.5f;
    int segments = 16;
    int rings = 12;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|fii", const_cast<char**>(kwlist),
            &radius, &segments, &rings)) {
        return NULL;
    }

    PyTypeObject* type = (PyTypeObject*)cls;
    PyModel3DObject* obj = (PyModel3DObject*)type->tp_alloc(type, 0);
    if (!obj) return NULL;

    obj->data = Model3D::sphere(radius, segments, rings);
    obj->weakreflist = nullptr;

    return (PyObject*)obj;
}

PyObject* Model3D::get_vertex_count(PyObject* self, void* closure)
{
    PyModel3DObject* obj = (PyModel3DObject*)self;
    if (!obj->data) {
        Py_RETURN_NONE;
    }
    return PyLong_FromLong(obj->data->getVertexCount());
}

PyObject* Model3D::get_triangle_count(PyObject* self, void* closure)
{
    PyModel3DObject* obj = (PyModel3DObject*)self;
    if (!obj->data) {
        Py_RETURN_NONE;
    }
    return PyLong_FromLong(obj->data->getTriangleCount());
}

PyObject* Model3D::get_has_skeleton(PyObject* self, void* closure)
{
    PyModel3DObject* obj = (PyModel3DObject*)self;
    if (!obj->data) {
        Py_RETURN_FALSE;
    }
    return PyBool_FromLong(obj->data->hasSkeleton());
}

PyObject* Model3D::get_bounds(PyObject* self, void* closure)
{
    PyModel3DObject* obj = (PyModel3DObject*)self;
    if (!obj->data) {
        Py_RETURN_NONE;
    }

    auto [min, max] = obj->data->getBounds();
    PyObject* minTuple = Py_BuildValue("(fff)", min.x, min.y, min.z);
    PyObject* maxTuple = Py_BuildValue("(fff)", max.x, max.y, max.z);

    if (!minTuple || !maxTuple) {
        Py_XDECREF(minTuple);
        Py_XDECREF(maxTuple);
        return NULL;
    }

    PyObject* result = PyTuple_Pack(2, minTuple, maxTuple);
    Py_DECREF(minTuple);
    Py_DECREF(maxTuple);
    return result;
}

PyObject* Model3D::get_name(PyObject* self, void* closure)
{
    PyModel3DObject* obj = (PyModel3DObject*)self;
    if (!obj->data) {
        Py_RETURN_NONE;
    }
    return PyUnicode_FromString(obj->data->getName().c_str());
}

PyObject* Model3D::get_mesh_count(PyObject* self, void* closure)
{
    PyModel3DObject* obj = (PyModel3DObject*)self;
    if (!obj->data) {
        return PyLong_FromLong(0);
    }
    return PyLong_FromLong(static_cast<long>(obj->data->getMeshCount()));
}

// Method and property tables
PyMethodDef Model3D::methods[] = {
    {"cube", (PyCFunction)py_cube, METH_VARARGS | METH_KEYWORDS | METH_CLASS,
     "cube(size=1.0) -> Model3D\n\nCreate a unit cube centered at origin."},
    {"plane", (PyCFunction)py_plane, METH_VARARGS | METH_KEYWORDS | METH_CLASS,
     "plane(width=1.0, depth=1.0, segments=1) -> Model3D\n\nCreate a flat plane."},
    {"sphere", (PyCFunction)py_sphere, METH_VARARGS | METH_KEYWORDS | METH_CLASS,
     "sphere(radius=0.5, segments=16, rings=12) -> Model3D\n\nCreate a UV sphere."},
    {NULL}
};

PyGetSetDef Model3D::getsetters[] = {
    {"vertex_count", get_vertex_count, NULL, "Total vertex count across all meshes (read-only)", NULL},
    {"triangle_count", get_triangle_count, NULL, "Total triangle count across all meshes (read-only)", NULL},
    {"has_skeleton", get_has_skeleton, NULL, "Whether model has skeletal animation data (read-only)", NULL},
    {"bounds", get_bounds, NULL, "AABB as ((min_x, min_y, min_z), (max_x, max_y, max_z)) (read-only)", NULL},
    {"name", get_name, NULL, "Model name (read-only)", NULL},
    {"mesh_count", get_mesh_count, NULL, "Number of submeshes (read-only)", NULL},
    {NULL}
};

} // namespace mcrf
