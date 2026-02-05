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
// SkinnedMesh Implementation
// =============================================================================

SkinnedMesh::SkinnedMesh(SkinnedMesh&& other) noexcept
    : vbo(other.vbo)
    , ebo(other.ebo)
    , vertex_count(other.vertex_count)
    , index_count(other.index_count)
    , material_index(other.material_index)
    , is_skinned(other.is_skinned)
{
    other.vbo = 0;
    other.ebo = 0;
    other.vertex_count = 0;
    other.index_count = 0;
}

SkinnedMesh& SkinnedMesh::operator=(SkinnedMesh&& other) noexcept
{
    if (this != &other) {
        vbo = other.vbo;
        ebo = other.ebo;
        vertex_count = other.vertex_count;
        index_count = other.index_count;
        material_index = other.material_index;
        is_skinned = other.is_skinned;
        other.vbo = 0;
        other.ebo = 0;
        other.vertex_count = 0;
        other.index_count = 0;
    }
    return *this;
}

// =============================================================================
// AnimationChannel Implementation
// =============================================================================

void AnimationChannel::sample(float time, vec3& trans_out, quat& rot_out, vec3& scale_out) const
{
    if (times.empty()) return;

    // Clamp time to animation range
    float t = std::max(times.front(), std::min(time, times.back()));

    // Find surrounding keyframes
    size_t k0 = 0, k1 = 0;
    float blend = 0.0f;

    for (size_t i = 0; i < times.size() - 1; i++) {
        if (t >= times[i] && t <= times[i + 1]) {
            k0 = i;
            k1 = i + 1;
            float dt = times[k1] - times[k0];
            blend = (dt > 0.0001f) ? (t - times[k0]) / dt : 0.0f;
            break;
        }
    }

    // If time is past the last keyframe, use last keyframe
    if (t >= times.back()) {
        k0 = k1 = times.size() - 1;
        blend = 0.0f;
    }

    // Interpolate based on path type
    switch (path) {
        case Path::Translation:
            if (!translations.empty()) {
                trans_out = vec3::lerp(translations[k0], translations[k1], blend);
            }
            break;

        case Path::Rotation:
            if (!rotations.empty()) {
                rot_out = quat::slerp(rotations[k0], rotations[k1], blend);
            }
            break;

        case Path::Scale:
            if (!scales.empty()) {
                scale_out = vec3::lerp(scales[k0], scales[k1], blend);
            }
            break;
    }
}

// =============================================================================
// AnimationClip Implementation
// =============================================================================

void AnimationClip::sample(float time, size_t num_bones,
                           const std::vector<mat4>& default_transforms,
                           std::vector<mat4>& local_out) const
{
    // Initialize with default transforms
    local_out.resize(num_bones);
    for (size_t i = 0; i < num_bones && i < default_transforms.size(); i++) {
        local_out[i] = default_transforms[i];
    }

    // Track which components have been animated per bone
    struct BoneAnimState {
        vec3 translation = vec3(0, 0, 0);
        quat rotation;
        vec3 scale = vec3(1, 1, 1);
        bool has_translation = false;
        bool has_rotation = false;
        bool has_scale = false;
    };
    std::vector<BoneAnimState> bone_states(num_bones);

    // Sample all channels
    for (const auto& channel : channels) {
        if (channel.bone_index < 0 || channel.bone_index >= static_cast<int>(num_bones)) {
            continue;
        }

        auto& state = bone_states[channel.bone_index];
        vec3 trans_dummy, scale_dummy;
        quat rot_dummy;

        channel.sample(time, trans_dummy, rot_dummy, scale_dummy);

        switch (channel.path) {
            case AnimationChannel::Path::Translation:
                state.translation = trans_dummy;
                state.has_translation = true;
                break;
            case AnimationChannel::Path::Rotation:
                state.rotation = rot_dummy;
                state.has_rotation = true;
                break;
            case AnimationChannel::Path::Scale:
                state.scale = scale_dummy;
                state.has_scale = true;
                break;
        }
    }

    // Build final local transforms for animated bones
    for (size_t i = 0; i < num_bones; i++) {
        const auto& state = bone_states[i];

        // Only rebuild if at least one component was animated
        if (state.has_translation || state.has_rotation || state.has_scale) {
            // Extract default values from default transform if not animated
            // (simplified: assume default is identity or use stored values)
            vec3 t = state.has_translation ? state.translation : vec3(0, 0, 0);
            quat r = state.has_rotation ? state.rotation : quat();
            vec3 s = state.has_scale ? state.scale : vec3(1, 1, 1);

            // If not fully animated, try to extract from default transform
            if (!state.has_translation || !state.has_rotation || !state.has_scale) {
                // For now, assume default transform contains the rest pose
                // A more complete implementation would decompose default_transforms[i]
                if (!state.has_translation) {
                    t = vec3(default_transforms[i].at(3, 0),
                             default_transforms[i].at(3, 1),
                             default_transforms[i].at(3, 2));
                }
            }

            // Compose: T * R * S
            local_out[i] = mat4::translate(t) * r.toMatrix() * mat4::scale(s);
        }
    }
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
    , skinned_meshes_(std::move(other.skinned_meshes_))
    , bounds_min_(other.bounds_min_)
    , bounds_max_(other.bounds_max_)
    , has_skeleton_(other.has_skeleton_)
    , skeleton_(std::move(other.skeleton_))
    , animation_clips_(std::move(other.animation_clips_))
    , default_bone_transforms_(std::move(other.default_bone_transforms_))
{
}

Model3D& Model3D::operator=(Model3D&& other) noexcept
{
    if (this != &other) {
        cleanupGPU();
        name_ = std::move(other.name_);
        meshes_ = std::move(other.meshes_);
        skinned_meshes_ = std::move(other.skinned_meshes_);
        bounds_min_ = other.bounds_min_;
        bounds_max_ = other.bounds_max_;
        has_skeleton_ = other.has_skeleton_;
        skeleton_ = std::move(other.skeleton_);
        animation_clips_ = std::move(other.animation_clips_);
        default_bone_transforms_ = std::move(other.default_bone_transforms_);
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
        for (auto& mesh : skinned_meshes_) {
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
    skinned_meshes_.clear();
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
    for (const auto& mesh : skinned_meshes_) {
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
    for (const auto& mesh : skinned_meshes_) {
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
            std::vector<vec4> joints;   // Bone indices (as floats for shader compatibility)
            std::vector<vec4> weights;  // Bone weights

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
                else if (attr->type == cgltf_attribute_type_joints && attr->index == 0) {
                    // Bone indices - can be unsigned byte or unsigned short
                    joints.resize(accessor->count);
                    for (size_t v = 0; v < accessor->count; ++v) {
                        // Read as uint then convert to float for shader compatibility
                        cgltf_uint indices[4] = {0, 0, 0, 0};
                        cgltf_accessor_read_uint(accessor, v, indices, 4);
                        joints[v].x = static_cast<float>(indices[0]);
                        joints[v].y = static_cast<float>(indices[1]);
                        joints[v].z = static_cast<float>(indices[2]);
                        joints[v].w = static_cast<float>(indices[3]);
                    }
                }
                else if (attr->type == cgltf_attribute_type_weights && attr->index == 0) {
                    // Bone weights
                    weights.resize(accessor->count);
                    for (size_t v = 0; v < accessor->count; ++v) {
                        cgltf_accessor_read_float(accessor, v, &weights[v].x, 4);
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

            // Extract indices
            std::vector<uint32_t> indices;
            if (prim->indices) {
                cgltf_accessor* accessor = prim->indices;
                indices.resize(accessor->count);
                for (size_t idx = 0; idx < accessor->count; ++idx) {
                    indices[idx] = static_cast<uint32_t>(cgltf_accessor_read_index(accessor, idx));
                }
            }

            // Check if this is a skinned mesh (has joints and weights)
            bool isSkinned = !joints.empty() && !weights.empty() && model->has_skeleton_;

            if (isSkinned) {
                // Create skinned mesh with bone data
                std::vector<SkinnedVertex> skinnedVertices;
                skinnedVertices.reserve(vertCount);
                for (size_t v = 0; v < vertCount; ++v) {
                    SkinnedVertex sv;
                    sv.position = positions[v];
                    sv.texcoord = texcoords[v];
                    sv.normal = normals[v];
                    sv.color = colors[v];
                    sv.bone_ids = joints[v];
                    sv.bone_weights = weights[v];
                    skinnedVertices.push_back(sv);

                    // Also track for bounds calculation
                    MeshVertex mv;
                    mv.position = positions[v];
                    mv.texcoord = texcoords[v];
                    mv.normal = normals[v];
                    mv.color = colors[v];
                    allVertices.push_back(mv);
                }
                model->skinned_meshes_.push_back(model->createSkinnedMesh(skinnedVertices, indices));
            } else {
                // Interleave vertex data for regular mesh
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
                model->meshes_.push_back(createMesh(vertices, indices));
            }
        }
    }

    // Compute bounds from all vertices
    model->computeBounds(allVertices);

    // Load skeleton and animations if present
    if (model->has_skeleton_) {
        model->loadSkeleton(data);
        model->loadAnimations(data);
    }

    cgltf_free(data);
    return model;
}

// =============================================================================
// Skeleton Loading from glTF
// =============================================================================

int Model3D::findJointIndex(void* cgltf_skin_ptr, void* node_ptr)
{
    cgltf_skin* skin = static_cast<cgltf_skin*>(cgltf_skin_ptr);
    cgltf_node* node = static_cast<cgltf_node*>(node_ptr);

    if (!skin || !node) return -1;

    for (size_t i = 0; i < skin->joints_count; i++) {
        if (skin->joints[i] == node) {
            return static_cast<int>(i);
        }
    }
    return -1;
}

void Model3D::loadSkeleton(void* cgltf_data_ptr)
{
    cgltf_data* data = static_cast<cgltf_data*>(cgltf_data_ptr);
    if (!data || data->skins_count == 0) {
        has_skeleton_ = false;
        return;
    }

    cgltf_skin* skin = &data->skins[0];  // Use first skin

    // Resize skeleton
    skeleton_.bones.resize(skin->joints_count);
    default_bone_transforms_.resize(skin->joints_count);

    // Load inverse bind matrices
    if (skin->inverse_bind_matrices) {
        cgltf_accessor* ibm = skin->inverse_bind_matrices;
        for (size_t i = 0; i < skin->joints_count && i < ibm->count; i++) {
            float mat_data[16];
            cgltf_accessor_read_float(ibm, i, mat_data, 16);

            // cgltf gives us column-major matrices (same as our mat4)
            for (int j = 0; j < 16; j++) {
                skeleton_.bones[i].inverse_bind_matrix.m[j] = mat_data[j];
            }
        }
    }

    // Load bone hierarchy
    for (size_t i = 0; i < skin->joints_count; i++) {
        cgltf_node* joint = skin->joints[i];
        Bone& bone = skeleton_.bones[i];

        // Name
        bone.name = joint->name ? joint->name : ("bone_" + std::to_string(i));

        // Find parent index
        bone.parent_index = findJointIndex(skin, joint->parent);

        // Track root bones
        if (bone.parent_index < 0) {
            skeleton_.root_bones.push_back(static_cast<int>(i));
        }

        // Local transform
        if (joint->has_matrix) {
            for (int j = 0; j < 16; j++) {
                bone.local_transform.m[j] = joint->matrix[j];
            }
        } else {
            // Compose from TRS
            vec3 t(0, 0, 0);
            quat r;
            vec3 s(1, 1, 1);

            if (joint->has_translation) {
                t = vec3(joint->translation[0], joint->translation[1], joint->translation[2]);
            }
            if (joint->has_rotation) {
                r = quat(joint->rotation[0], joint->rotation[1],
                         joint->rotation[2], joint->rotation[3]);
            }
            if (joint->has_scale) {
                s = vec3(joint->scale[0], joint->scale[1], joint->scale[2]);
            }

            bone.local_transform = mat4::translate(t) * r.toMatrix() * mat4::scale(s);
        }

        default_bone_transforms_[i] = bone.local_transform;
    }

    has_skeleton_ = true;
}

// =============================================================================
// Animation Loading from glTF
// =============================================================================

void Model3D::loadAnimations(void* cgltf_data_ptr)
{
    cgltf_data* data = static_cast<cgltf_data*>(cgltf_data_ptr);
    if (!data || data->skins_count == 0) return;

    cgltf_skin* skin = &data->skins[0];

    for (size_t i = 0; i < data->animations_count; i++) {
        cgltf_animation* anim = &data->animations[i];

        AnimationClip clip;
        clip.name = anim->name ? anim->name : ("animation_" + std::to_string(i));
        clip.duration = 0.0f;

        for (size_t j = 0; j < anim->channels_count; j++) {
            cgltf_animation_channel* chan = &anim->channels[j];
            cgltf_animation_sampler* sampler = chan->sampler;

            if (!sampler || !chan->target_node) continue;

            AnimationChannel channel;
            channel.bone_index = findJointIndex(skin, chan->target_node);

            if (channel.bone_index < 0) continue;  // Not a bone we're tracking

            // Determine path type
            switch (chan->target_path) {
                case cgltf_animation_path_type_translation:
                    channel.path = AnimationChannel::Path::Translation;
                    break;
                case cgltf_animation_path_type_rotation:
                    channel.path = AnimationChannel::Path::Rotation;
                    break;
                case cgltf_animation_path_type_scale:
                    channel.path = AnimationChannel::Path::Scale;
                    break;
                default:
                    continue;  // Skip unsupported paths (weights, etc.)
            }

            // Load keyframe times
            cgltf_accessor* input = sampler->input;
            if (input) {
                channel.times.resize(input->count);
                for (size_t k = 0; k < input->count; k++) {
                    cgltf_accessor_read_float(input, k, &channel.times[k], 1);
                }

                // Update clip duration
                if (!channel.times.empty() && channel.times.back() > clip.duration) {
                    clip.duration = channel.times.back();
                }
            }

            // Load keyframe values
            cgltf_accessor* output = sampler->output;
            if (output) {
                switch (channel.path) {
                    case AnimationChannel::Path::Translation:
                    case AnimationChannel::Path::Scale:
                    {
                        std::vector<vec3>& target = (channel.path == AnimationChannel::Path::Translation)
                            ? channel.translations : channel.scales;
                        target.resize(output->count);
                        for (size_t k = 0; k < output->count; k++) {
                            float v[3];
                            cgltf_accessor_read_float(output, k, v, 3);
                            target[k] = vec3(v[0], v[1], v[2]);
                        }
                        break;
                    }
                    case AnimationChannel::Path::Rotation:
                    {
                        channel.rotations.resize(output->count);
                        for (size_t k = 0; k < output->count; k++) {
                            float v[4];
                            cgltf_accessor_read_float(output, k, v, 4);
                            // glTF stores quaternions as (x, y, z, w)
                            channel.rotations[k] = quat(v[0], v[1], v[2], v[3]);
                        }
                        break;
                    }
                }
            }

            clip.channels.push_back(std::move(channel));
        }

        if (!clip.channels.empty()) {
            animation_clips_.push_back(std::move(clip));
        }
    }
}

// =============================================================================
// Skinned Mesh Creation
// =============================================================================

SkinnedMesh Model3D::createSkinnedMesh(const std::vector<SkinnedVertex>& vertices,
                                        const std::vector<uint32_t>& indices)
{
    SkinnedMesh mesh;
    mesh.vertex_count = static_cast<int>(vertices.size());
    mesh.index_count = static_cast<int>(indices.size());
    mesh.is_skinned = true;

#ifdef MCRF_HAS_GL
    if (!gl::isGLReady()) {
        return mesh;
    }

    // Create VBO
    glGenBuffers(1, &mesh.vbo);
    glBindBuffer(GL_ARRAY_BUFFER, mesh.vbo);
    glBufferData(GL_ARRAY_BUFFER,
                 vertices.size() * sizeof(SkinnedVertex),
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
// Skinned Rendering
// =============================================================================

void Model3D::renderSkinned(unsigned int shader, const mat4& model,
                            const mat4& view, const mat4& projection,
                            const std::vector<mat4>& bone_matrices)
{
#ifdef MCRF_HAS_GL
    if (!gl::isGLReady()) return;

    // Calculate MVP
    mat4 mvp = projection * view * model;

    // Set uniforms
    int mvpLoc = glGetUniformLocation(shader, "u_mvp");
    int modelLoc = glGetUniformLocation(shader, "u_model");
    int bonesLoc = glGetUniformLocation(shader, "u_bones");

    if (mvpLoc >= 0) glUniformMatrix4fv(mvpLoc, 1, GL_FALSE, mvp.data());
    if (modelLoc >= 0) glUniformMatrix4fv(modelLoc, 1, GL_FALSE, model.data());

    // Upload bone matrices (max 64 bones)
    if (bonesLoc >= 0 && !bone_matrices.empty()) {
        int count = std::min(static_cast<int>(bone_matrices.size()), 64);
        glUniformMatrix4fv(bonesLoc, count, GL_FALSE, bone_matrices[0].data());
    }

    // For now, fall back to regular rendering for non-skinned meshes
    // TODO: Add skinned mesh rendering with bone weight attributes

    // Render skinned meshes
    for (const auto& mesh : skinned_meshes_) {
        if (mesh.vertex_count == 0) continue;

        glBindBuffer(GL_ARRAY_BUFFER, mesh.vbo);

        // Position (location 0)
        glEnableVertexAttribArray(Shader3D::ATTRIB_POSITION);
        glVertexAttribPointer(Shader3D::ATTRIB_POSITION, 3, GL_FLOAT, GL_FALSE,
                              sizeof(SkinnedVertex), (void*)offsetof(SkinnedVertex, position));

        // Texcoord (location 1)
        glEnableVertexAttribArray(Shader3D::ATTRIB_TEXCOORD);
        glVertexAttribPointer(Shader3D::ATTRIB_TEXCOORD, 2, GL_FLOAT, GL_FALSE,
                              sizeof(SkinnedVertex), (void*)offsetof(SkinnedVertex, texcoord));

        // Normal (location 2)
        glEnableVertexAttribArray(Shader3D::ATTRIB_NORMAL);
        glVertexAttribPointer(Shader3D::ATTRIB_NORMAL, 3, GL_FLOAT, GL_FALSE,
                              sizeof(SkinnedVertex), (void*)offsetof(SkinnedVertex, normal));

        // Color (location 3)
        glEnableVertexAttribArray(Shader3D::ATTRIB_COLOR);
        glVertexAttribPointer(Shader3D::ATTRIB_COLOR, 4, GL_FLOAT, GL_FALSE,
                              sizeof(SkinnedVertex), (void*)offsetof(SkinnedVertex, color));

        // Bone IDs (location 4) - as vec4 float for GLES2 compatibility
        glEnableVertexAttribArray(4);
        glVertexAttribPointer(4, 4, GL_FLOAT, GL_FALSE,
                              sizeof(SkinnedVertex), (void*)offsetof(SkinnedVertex, bone_ids));

        // Bone Weights (location 5)
        glEnableVertexAttribArray(5);
        glVertexAttribPointer(5, 4, GL_FLOAT, GL_FALSE,
                              sizeof(SkinnedVertex), (void*)offsetof(SkinnedVertex, bone_weights));

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
        glDisableVertexAttribArray(4);
        glDisableVertexAttribArray(5);
    }

    // Also render regular meshes (may not have skinning)
    for (const auto& mesh : meshes_) {
        if (mesh.vertex_count == 0) continue;

        glBindBuffer(GL_ARRAY_BUFFER, mesh.vbo);

        glEnableVertexAttribArray(Shader3D::ATTRIB_POSITION);
        glVertexAttribPointer(Shader3D::ATTRIB_POSITION, 3, GL_FLOAT, GL_FALSE,
                              sizeof(MeshVertex), (void*)offsetof(MeshVertex, position));

        glEnableVertexAttribArray(Shader3D::ATTRIB_TEXCOORD);
        glVertexAttribPointer(Shader3D::ATTRIB_TEXCOORD, 2, GL_FLOAT, GL_FALSE,
                              sizeof(MeshVertex), (void*)offsetof(MeshVertex, texcoord));

        glEnableVertexAttribArray(Shader3D::ATTRIB_NORMAL);
        glVertexAttribPointer(Shader3D::ATTRIB_NORMAL, 3, GL_FLOAT, GL_FALSE,
                              sizeof(MeshVertex), (void*)offsetof(MeshVertex, normal));

        glEnableVertexAttribArray(Shader3D::ATTRIB_COLOR);
        glVertexAttribPointer(Shader3D::ATTRIB_COLOR, 4, GL_FLOAT, GL_FALSE,
                              sizeof(MeshVertex), (void*)offsetof(MeshVertex, color));

        if (mesh.index_count > 0) {
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, mesh.ebo);
            glDrawElements(GL_TRIANGLES, mesh.index_count, GL_UNSIGNED_INT, 0);
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0);
        } else {
            glDrawArrays(GL_TRIANGLES, 0, mesh.vertex_count);
        }

        glDisableVertexAttribArray(Shader3D::ATTRIB_POSITION);
        glDisableVertexAttribArray(Shader3D::ATTRIB_TEXCOORD);
        glDisableVertexAttribArray(Shader3D::ATTRIB_NORMAL);
        glDisableVertexAttribArray(Shader3D::ATTRIB_COLOR);
    }

    glBindBuffer(GL_ARRAY_BUFFER, 0);
#endif
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

PyObject* Model3D::get_bone_count(PyObject* self, void* closure)
{
    PyModel3DObject* obj = (PyModel3DObject*)self;
    if (!obj->data) {
        return PyLong_FromLong(0);
    }
    return PyLong_FromLong(static_cast<long>(obj->data->getBoneCount()));
}

PyObject* Model3D::get_animation_clips(PyObject* self, void* closure)
{
    PyModel3DObject* obj = (PyModel3DObject*)self;
    if (!obj->data) {
        return PyList_New(0);
    }

    auto names = obj->data->getAnimationClipNames();
    PyObject* list = PyList_New(names.size());
    if (!list) return NULL;

    for (size_t i = 0; i < names.size(); i++) {
        PyObject* name = PyUnicode_FromString(names[i].c_str());
        if (!name) {
            Py_DECREF(list);
            return NULL;
        }
        PyList_SET_ITEM(list, i, name);  // Steals reference
    }

    return list;
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
    {"bone_count", get_bone_count, NULL, "Number of bones in skeleton (read-only)", NULL},
    {"animation_clips", get_animation_clips, NULL, "List of animation clip names (read-only)", NULL},
    {NULL}
};

} // namespace mcrf
