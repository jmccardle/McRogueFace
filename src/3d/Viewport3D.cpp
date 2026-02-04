// Viewport3D.cpp - 3D rendering viewport implementation

#include "Viewport3D.h"
#include "Shader3D.h"
#include "MeshLayer.h"
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
{
    position = sf::Vector2f(0, 0);
    camera_.setAspect(size_.x / size_.y);
}

Viewport3D::Viewport3D(float x, float y, float width, float height)
    : size_(width, height)
{
    position = sf::Vector2f(x, y);
    camera_.setAspect(size_.x / size_.y);
}

Viewport3D::~Viewport3D() {
    cleanupTestGeometry();
    cleanupFBO();
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
        target.pushGLStates();
    }

    // Render 3D content to FBO
    render3DContent();

    // Restore SFML's GL state after our GL calls
    if (gl::isGLReady()) {
        target.popGLStates();
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
    for (auto* layer : sortedLayers) {
        // Set model matrix for this layer
        shader_->setUniform("u_model", layer->getModelMatrix());

        // Render the layer's geometry
        layer->render(layer->getModelMatrix(), view, projection);
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
    {NULL}  // Sentinel
};
