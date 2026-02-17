// Billboard.cpp - Camera-facing 3D sprite implementation

#include "Billboard.h"
#include "Shader3D.h"
#include "MeshLayer.h"  // For MeshVertex
#include "../platform/GLContext.h"
#include "../PyTexture.h"
#include <cmath>
#include <iostream>

// GL headers based on backend
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

namespace mcrf {

// Static members
unsigned int Billboard::sharedVBO_ = 0;
unsigned int Billboard::sharedEBO_ = 0;
bool Billboard::geometryInitialized_ = false;

// =============================================================================
// Constructor / Destructor
// =============================================================================

Billboard::Billboard()
    : texture_()
    , spriteIndex_(0)
    , position_(0, 0, 0)
    , scale_(1.0f)
    , facing_(BillboardFacing::CameraY)
    , theta_(0.0f)
    , phi_(0.0f)
    , opacity_(1.0f)
    , visible_(true)
    , tilesPerRow_(1)
    , tilesPerCol_(1)
{}

Billboard::Billboard(std::shared_ptr<PyTexture> texture, int spriteIndex, const vec3& pos,
                     float scale, BillboardFacing facing)
    : texture_(texture)
    , spriteIndex_(spriteIndex)
    , position_(pos)
    , scale_(scale)
    , facing_(facing)
    , theta_(0.0f)
    , phi_(0.0f)
    , opacity_(1.0f)
    , visible_(true)
    , tilesPerRow_(1)
    , tilesPerCol_(1)
{}

Billboard::~Billboard() {
    // Texture is not owned, don't delete it
}

// =============================================================================
// Configuration
// =============================================================================

void Billboard::setSpriteSheetLayout(int tilesPerRow, int tilesPerCol) {
    tilesPerRow_ = tilesPerRow > 0 ? tilesPerRow : 1;
    tilesPerCol_ = tilesPerCol > 0 ? tilesPerCol : 1;
}

// =============================================================================
// Static Geometry Management
// =============================================================================

void Billboard::initSharedGeometry() {
#ifdef MCRF_HAS_GL
    if (geometryInitialized_ || !gl::isGLReady()) {
        return;
    }

    // Create a unit quad centered at origin, facing +Z
    // Vertices: position (3) + texcoord (2) + normal (3) + color (4) = 12 floats
    MeshVertex vertices[4] = {
        // Bottom-left
        MeshVertex(vec3(-0.5f, -0.5f, 0.0f), vec2(0, 1), vec3(0, 0, 1), vec4(1, 1, 1, 1)),
        // Bottom-right
        MeshVertex(vec3( 0.5f, -0.5f, 0.0f), vec2(1, 1), vec3(0, 0, 1), vec4(1, 1, 1, 1)),
        // Top-right
        MeshVertex(vec3( 0.5f,  0.5f, 0.0f), vec2(1, 0), vec3(0, 0, 1), vec4(1, 1, 1, 1)),
        // Top-left
        MeshVertex(vec3(-0.5f,  0.5f, 0.0f), vec2(0, 0), vec3(0, 0, 1), vec4(1, 1, 1, 1)),
    };

    unsigned short indices[6] = {
        0, 1, 2,  // First triangle
        2, 3, 0   // Second triangle
    };

    glGenBuffers(1, &sharedVBO_);
    glBindBuffer(GL_ARRAY_BUFFER, sharedVBO_);
    glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STATIC_DRAW);
    glBindBuffer(GL_ARRAY_BUFFER, 0);

    glGenBuffers(1, &sharedEBO_);
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, sharedEBO_);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, sizeof(indices), indices, GL_STATIC_DRAW);
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0);

    geometryInitialized_ = true;
#endif
}

void Billboard::cleanupSharedGeometry() {
#ifdef MCRF_HAS_GL
    if (sharedVBO_ != 0 && gl::isGLReady()) {
        glDeleteBuffers(1, &sharedVBO_);
        sharedVBO_ = 0;
    }
    if (sharedEBO_ != 0 && gl::isGLReady()) {
        glDeleteBuffers(1, &sharedEBO_);
        sharedEBO_ = 0;
    }
    geometryInitialized_ = false;
#endif
}

// =============================================================================
// Rendering
// =============================================================================

mat4 Billboard::computeModelMatrix(const vec3& cameraPos, const mat4& view) {
    mat4 model = mat4::identity();

    // First translate to world position
    model = model * mat4::translate(position_);

    // Apply rotation based on facing mode
    switch (facing_) {
        case BillboardFacing::Camera: {
            // Full rotation to face camera
            // Extract camera right and up vectors from view matrix
            vec3 right(view.m[0], view.m[4], view.m[8]);
            vec3 up(view.m[1], view.m[5], view.m[9]);

            // Build rotation matrix that makes the quad face the camera
            // The quad is initially facing +Z, we need to rotate it
            mat4 rotation;
            rotation.m[0] = right.x;   rotation.m[4] = up.x;   rotation.m[8]  = -view.m[2];  rotation.m[12] = 0;
            rotation.m[1] = right.y;   rotation.m[5] = up.y;   rotation.m[9]  = -view.m[6];  rotation.m[13] = 0;
            rotation.m[2] = right.z;   rotation.m[6] = up.z;   rotation.m[10] = -view.m[10]; rotation.m[14] = 0;
            rotation.m[3] = 0;         rotation.m[7] = 0;      rotation.m[11] = 0;           rotation.m[15] = 1;

            model = model * rotation;
            break;
        }

        case BillboardFacing::CameraY: {
            // Only Y-axis rotation to face camera (stays upright)
            vec3 toCamera(cameraPos.x - position_.x, 0, cameraPos.z - position_.z);
            float length = std::sqrt(toCamera.x * toCamera.x + toCamera.z * toCamera.z);
            if (length > 0.001f) {
                float angle = std::atan2(toCamera.x, toCamera.z);
                model = model * mat4::rotateY(angle);
            }
            break;
        }

        case BillboardFacing::Fixed: {
            // Use theta (Y rotation) and phi (X tilt)
            model = model * mat4::rotateY(theta_);
            model = model * mat4::rotateX(phi_);
            break;
        }
    }

    // Apply scale
    model = model * mat4::scale(vec3(scale_, scale_, scale_));

    return model;
}

void Billboard::render(unsigned int shader, const mat4& view, const mat4& projection,
                       const vec3& cameraPos) {
#ifdef MCRF_HAS_GL
    if (!visible_ || !gl::isGLReady()) {
        return;
    }

    // Initialize shared geometry if needed
    if (!geometryInitialized_) {
        initSharedGeometry();
    }

    if (sharedVBO_ == 0 || sharedEBO_ == 0) {
        return;
    }

    // Compute model matrix
    mat4 model = computeModelMatrix(cameraPos, view);

    // Set model matrix uniform
    int modelLoc = glGetUniformLocation(shader, "u_model");
    if (modelLoc >= 0) {
        glUniformMatrix4fv(modelLoc, 1, GL_FALSE, model.m);
    }

    // Set entity color uniform (for tinting/opacity)
    int colorLoc = glGetUniformLocation(shader, "u_entityColor");
    if (colorLoc >= 0) {
        glUniform4f(colorLoc, 1.0f, 1.0f, 1.0f, opacity_);
    }

    // Handle texture
    bool hasTexture = (texture_ != nullptr);
    int hasTexLoc = glGetUniformLocation(shader, "u_has_texture");
    if (hasTexLoc >= 0) {
        glUniform1i(hasTexLoc, hasTexture ? 1 : 0);
    }

    if (hasTexture) {
        // Bind texture using PyTexture's underlying sf::Texture
        const sf::Texture* sfTexture = texture_->getSFMLTexture();
        if (sfTexture) {
            glBindTexture(GL_TEXTURE_2D, sfTexture->getNativeHandle());

            // Use PyTexture's sprite sheet configuration
            int sheetW = texture_->sprite_width > 0 ? texture_->sprite_width : 1;
            int sheetH = texture_->sprite_height > 0 ? texture_->sprite_height : 1;
            sf::Vector2u texSize = sfTexture->getSize();
            int tilesPerRow = texSize.x / sheetW;
            int tilesPerCol = texSize.y / sheetH;
            if (tilesPerRow < 1) tilesPerRow = 1;
            if (tilesPerCol < 1) tilesPerCol = 1;

            // Calculate sprite UV offset
            float tileU = 1.0f / tilesPerRow;
            float tileV = 1.0f / tilesPerCol;
            int tileX = spriteIndex_ % tilesPerRow;
            int tileY = spriteIndex_ / tilesPerRow;

            // Set UV offset/scale uniforms if available
            int uvOffsetLoc = glGetUniformLocation(shader, "u_uv_offset");
            int uvScaleLoc = glGetUniformLocation(shader, "u_uv_scale");
            if (uvOffsetLoc >= 0) {
                glUniform2f(uvOffsetLoc, tileX * tileU, tileY * tileV);
            }
            if (uvScaleLoc >= 0) {
                glUniform2f(uvScaleLoc, tileU, tileV);
            }
        }
    }

    // Bind VBO
    glBindBuffer(GL_ARRAY_BUFFER, sharedVBO_);

    // Set up vertex attributes
    int stride = sizeof(MeshVertex);

    glEnableVertexAttribArray(Shader3D::ATTRIB_POSITION);
    glVertexAttribPointer(Shader3D::ATTRIB_POSITION, 3, GL_FLOAT, GL_FALSE,
                          stride, reinterpret_cast<void*>(offsetof(MeshVertex, position)));

    glEnableVertexAttribArray(Shader3D::ATTRIB_TEXCOORD);
    glVertexAttribPointer(Shader3D::ATTRIB_TEXCOORD, 2, GL_FLOAT, GL_FALSE,
                          stride, reinterpret_cast<void*>(offsetof(MeshVertex, texcoord)));

    glEnableVertexAttribArray(Shader3D::ATTRIB_NORMAL);
    glVertexAttribPointer(Shader3D::ATTRIB_NORMAL, 3, GL_FLOAT, GL_FALSE,
                          stride, reinterpret_cast<void*>(offsetof(MeshVertex, normal)));

    glEnableVertexAttribArray(Shader3D::ATTRIB_COLOR);
    glVertexAttribPointer(Shader3D::ATTRIB_COLOR, 4, GL_FLOAT, GL_FALSE,
                          stride, reinterpret_cast<void*>(offsetof(MeshVertex, color)));

    // Bind EBO and draw
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, sharedEBO_);
    glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_SHORT, 0);

    // Cleanup
    glDisableVertexAttribArray(Shader3D::ATTRIB_POSITION);
    glDisableVertexAttribArray(Shader3D::ATTRIB_TEXCOORD);
    glDisableVertexAttribArray(Shader3D::ATTRIB_NORMAL);
    glDisableVertexAttribArray(Shader3D::ATTRIB_COLOR);
    glBindBuffer(GL_ARRAY_BUFFER, 0);
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0);

    // Unbind texture
    if (hasTexture) {
        glBindTexture(GL_TEXTURE_2D, 0);
    }

    // Reset UV uniforms
    int uvOffsetLoc = glGetUniformLocation(shader, "u_uv_offset");
    int uvScaleLoc = glGetUniformLocation(shader, "u_uv_scale");
    if (uvOffsetLoc >= 0) {
        glUniform2f(uvOffsetLoc, 0.0f, 0.0f);
    }
    if (uvScaleLoc >= 0) {
        glUniform2f(uvScaleLoc, 1.0f, 1.0f);
    }
#endif
}

// =============================================================================
// Python API
// =============================================================================

PyGetSetDef Billboard::getsetters[] = {
    {"texture", Billboard::get_texture, Billboard::set_texture,
     "Sprite sheet texture (Texture or None)", NULL},
    {"sprite_index", Billboard::get_sprite_index, Billboard::set_sprite_index,
     "Index into sprite sheet (int)", NULL},
    {"pos", Billboard::get_pos, Billboard::set_pos,
     "World position as (x, y, z) tuple", NULL},
    {"scale", Billboard::get_scale, Billboard::set_scale,
     "Uniform scale factor (float)", NULL},
    {"facing", Billboard::get_facing, Billboard::set_facing,
     "Facing mode: 'camera', 'camera_y', or 'fixed' (str)", NULL},
    {"theta", Billboard::get_theta, Billboard::set_theta,
     "Horizontal rotation for 'fixed' mode in radians (float)", NULL},
    {"phi", Billboard::get_phi, Billboard::set_phi,
     "Vertical tilt for 'fixed' mode in radians (float)", NULL},
    {"opacity", Billboard::get_opacity, Billboard::set_opacity,
     "Opacity from 0.0 (transparent) to 1.0 (opaque) (float)", NULL},
    {"visible", Billboard::get_visible, Billboard::set_visible,
     "Visibility state (bool)", NULL},
    {NULL}
};

int Billboard::init(PyObject* self, PyObject* args, PyObject* kwds) {
    PyBillboardObject* selfObj = (PyBillboardObject*)self;

    static const char* kwlist[] = {"texture", "sprite_index", "pos", "scale", "facing", "opacity", "visible", NULL};

    PyObject* textureObj = nullptr;
    int spriteIndex = 0;
    PyObject* posObj = nullptr;
    float scale = 1.0f;
    const char* facingStr = "camera_y";
    float opacity = 1.0f;
    int visible = 1;  // Default to True

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OiOfsfp", const_cast<char**>(kwlist),
                                     &textureObj, &spriteIndex, &posObj, &scale, &facingStr, &opacity, &visible)) {
        return -1;
    }

    // Handle texture
    if (textureObj && textureObj != Py_None) {
        PyTypeObject* textureType = &mcrfpydef::PyTextureType;
        if (PyObject_IsInstance(textureObj, (PyObject*)textureType)) {
            PyTextureObject* texPy = (PyTextureObject*)textureObj;
            if (texPy->data) {
                selfObj->data->setTexture(texPy->data);
            }
        } else {
            PyErr_SetString(PyExc_TypeError, "texture must be a Texture object or None");
            return -1;
        }
    }

    selfObj->data->setSpriteIndex(spriteIndex);
    selfObj->data->setScale(scale);

    // Handle position
    if (posObj && posObj != Py_None) {
        if (PyTuple_Check(posObj) && PyTuple_Size(posObj) >= 3) {
            float x = static_cast<float>(PyFloat_AsDouble(PyTuple_GetItem(posObj, 0)));
            float y = static_cast<float>(PyFloat_AsDouble(PyTuple_GetItem(posObj, 1)));
            float z = static_cast<float>(PyFloat_AsDouble(PyTuple_GetItem(posObj, 2)));
            if (!PyErr_Occurred()) {
                selfObj->data->setPosition(vec3(x, y, z));
            }
        } else {
            PyErr_SetString(PyExc_TypeError, "pos must be a tuple of (x, y, z)");
            return -1;
        }
    }

    // Handle facing mode
    std::string facing(facingStr);
    if (facing == "camera") {
        selfObj->data->setFacing(BillboardFacing::Camera);
    } else if (facing == "camera_y") {
        selfObj->data->setFacing(BillboardFacing::CameraY);
    } else if (facing == "fixed") {
        selfObj->data->setFacing(BillboardFacing::Fixed);
    } else {
        PyErr_SetString(PyExc_ValueError, "facing must be 'camera', 'camera_y', or 'fixed'");
        return -1;
    }

    // Apply opacity and visibility
    selfObj->data->setOpacity(opacity);
    selfObj->data->setVisible(visible != 0);

    return 0;
}

PyObject* Billboard::repr(PyObject* self) {
    PyBillboardObject* obj = (PyBillboardObject*)self;
    if (!obj->data) {
        return PyUnicode_FromString("<Billboard (invalid)>");
    }

    vec3 pos = obj->data->getPosition();
    const char* facingStr = "unknown";
    switch (obj->data->getFacing()) {
        case BillboardFacing::Camera: facingStr = "camera"; break;
        case BillboardFacing::CameraY: facingStr = "camera_y"; break;
        case BillboardFacing::Fixed: facingStr = "fixed"; break;
    }

    // PyUnicode_FromFormat doesn't support %f, so use snprintf
    char buffer[256];
    snprintf(buffer, sizeof(buffer), "<Billboard pos=(%.2f, %.2f, %.2f) scale=%.2f facing='%s'>",
             pos.x, pos.y, pos.z, obj->data->getScale(), facingStr);
    return PyUnicode_FromString(buffer);
}

// Property implementations
PyObject* Billboard::get_texture(PyObject* self, void* closure) {
    PyBillboardObject* obj = (PyBillboardObject*)self;
    std::shared_ptr<PyTexture> tex = obj->data->getTexture();
    if (!tex) {
        Py_RETURN_NONE;
    }
    // Return the PyTexture's Python object
    return tex->pyObject();
}

int Billboard::set_texture(PyObject* self, PyObject* value, void* closure) {
    PyBillboardObject* obj = (PyBillboardObject*)self;
    if (value == Py_None) {
        obj->data->setTexture(nullptr);
        return 0;
    }
    PyTypeObject* textureType = &mcrfpydef::PyTextureType;
    if (PyObject_IsInstance(value, (PyObject*)textureType)) {
        PyTextureObject* texPy = (PyTextureObject*)value;
        if (texPy->data) {
            obj->data->setTexture(texPy->data);
            return 0;
        }
    }
    PyErr_SetString(PyExc_TypeError, "texture must be a Texture object or None");
    return -1;
}

PyObject* Billboard::get_sprite_index(PyObject* self, void* closure) {
    PyBillboardObject* obj = (PyBillboardObject*)self;
    return PyLong_FromLong(obj->data->getSpriteIndex());
}

int Billboard::set_sprite_index(PyObject* self, PyObject* value, void* closure) {
    PyBillboardObject* obj = (PyBillboardObject*)self;
    if (!PyLong_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "sprite_index must be an integer");
        return -1;
    }
    obj->data->setSpriteIndex(static_cast<int>(PyLong_AsLong(value)));
    return 0;
}

PyObject* Billboard::get_pos(PyObject* self, void* closure) {
    PyBillboardObject* obj = (PyBillboardObject*)self;
    vec3 pos = obj->data->getPosition();
    return Py_BuildValue("(fff)", pos.x, pos.y, pos.z);
}

int Billboard::set_pos(PyObject* self, PyObject* value, void* closure) {
    PyBillboardObject* obj = (PyBillboardObject*)self;
    if (!PyTuple_Check(value) || PyTuple_Size(value) < 3) {
        PyErr_SetString(PyExc_TypeError, "pos must be a tuple of (x, y, z)");
        return -1;
    }
    float x = static_cast<float>(PyFloat_AsDouble(PyTuple_GetItem(value, 0)));
    float y = static_cast<float>(PyFloat_AsDouble(PyTuple_GetItem(value, 1)));
    float z = static_cast<float>(PyFloat_AsDouble(PyTuple_GetItem(value, 2)));
    if (PyErr_Occurred()) return -1;
    obj->data->setPosition(vec3(x, y, z));
    return 0;
}

PyObject* Billboard::get_scale(PyObject* self, void* closure) {
    PyBillboardObject* obj = (PyBillboardObject*)self;
    return PyFloat_FromDouble(obj->data->getScale());
}

int Billboard::set_scale(PyObject* self, PyObject* value, void* closure) {
    PyBillboardObject* obj = (PyBillboardObject*)self;
    float scale = static_cast<float>(PyFloat_AsDouble(value));
    if (PyErr_Occurred()) return -1;
    obj->data->setScale(scale);
    return 0;
}

PyObject* Billboard::get_facing(PyObject* self, void* closure) {
    PyBillboardObject* obj = (PyBillboardObject*)self;
    switch (obj->data->getFacing()) {
        case BillboardFacing::Camera: return PyUnicode_FromString("camera");
        case BillboardFacing::CameraY: return PyUnicode_FromString("camera_y");
        case BillboardFacing::Fixed: return PyUnicode_FromString("fixed");
    }
    return PyUnicode_FromString("unknown");
}

int Billboard::set_facing(PyObject* self, PyObject* value, void* closure) {
    PyBillboardObject* obj = (PyBillboardObject*)self;
    if (!PyUnicode_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "facing must be a string");
        return -1;
    }
    const char* str = PyUnicode_AsUTF8(value);
    std::string facing(str);
    if (facing == "camera") {
        obj->data->setFacing(BillboardFacing::Camera);
    } else if (facing == "camera_y") {
        obj->data->setFacing(BillboardFacing::CameraY);
    } else if (facing == "fixed") {
        obj->data->setFacing(BillboardFacing::Fixed);
    } else {
        PyErr_SetString(PyExc_ValueError, "facing must be 'camera', 'camera_y', or 'fixed'");
        return -1;
    }
    return 0;
}

PyObject* Billboard::get_theta(PyObject* self, void* closure) {
    PyBillboardObject* obj = (PyBillboardObject*)self;
    return PyFloat_FromDouble(obj->data->getTheta());
}

int Billboard::set_theta(PyObject* self, PyObject* value, void* closure) {
    PyBillboardObject* obj = (PyBillboardObject*)self;
    float theta = static_cast<float>(PyFloat_AsDouble(value));
    if (PyErr_Occurred()) return -1;
    obj->data->setTheta(theta);
    return 0;
}

PyObject* Billboard::get_phi(PyObject* self, void* closure) {
    PyBillboardObject* obj = (PyBillboardObject*)self;
    return PyFloat_FromDouble(obj->data->getPhi());
}

int Billboard::set_phi(PyObject* self, PyObject* value, void* closure) {
    PyBillboardObject* obj = (PyBillboardObject*)self;
    float phi = static_cast<float>(PyFloat_AsDouble(value));
    if (PyErr_Occurred()) return -1;
    obj->data->setPhi(phi);
    return 0;
}

PyObject* Billboard::get_opacity(PyObject* self, void* closure) {
    PyBillboardObject* obj = (PyBillboardObject*)self;
    return PyFloat_FromDouble(obj->data->getOpacity());
}

int Billboard::set_opacity(PyObject* self, PyObject* value, void* closure) {
    PyBillboardObject* obj = (PyBillboardObject*)self;
    float opacity = static_cast<float>(PyFloat_AsDouble(value));
    if (PyErr_Occurred()) return -1;
    obj->data->setOpacity(opacity);
    return 0;
}

PyObject* Billboard::get_visible(PyObject* self, void* closure) {
    PyBillboardObject* obj = (PyBillboardObject*)self;
    return PyBool_FromLong(obj->data->isVisible());
}

int Billboard::set_visible(PyObject* self, PyObject* value, void* closure) {
    PyBillboardObject* obj = (PyBillboardObject*)self;
    if (!PyBool_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "visible must be a boolean");
        return -1;
    }
    obj->data->setVisible(value == Py_True);
    return 0;
}

} // namespace mcrf
