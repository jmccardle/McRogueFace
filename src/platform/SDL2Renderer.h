// SDL2Renderer.h - OpenGL ES 2 rendering implementation for SDL2 backend
// This file provides the actual rendering implementation for the SDL2 types
// defined in SDL2Types.h. It handles:
// - OpenGL ES 2 context management
// - Shader compilation and management
// - Texture loading (via stb_image)
// - Font rendering (via stb_truetype)
// - Framebuffer object management
//
// Part of the renderer abstraction layer

#pragma once

#ifdef MCRF_SDL2

#include <string>
#include <vector>
#include <unordered_map>
#include <memory>

// Forward declarations to avoid SDL header in this header
struct SDL_Window;
typedef void* SDL_GLContext;

namespace sf {

// Forward declarations
class RenderTarget;
class Texture;
class Shader;

// =============================================================================
// SDL2 Renderer - Singleton managing OpenGL ES 2 state
// =============================================================================

class SDL2Renderer {
public:
    // Singleton access
    static SDL2Renderer& getInstance();

    // Initialization/shutdown
    bool init();         // Initialize SDL2 (call before window creation)
    bool initGL();       // Initialize OpenGL resources (call after GL context exists)
    void shutdown();
    bool isInitialized() const { return initialized_; }
    bool isGLInitialized() const { return glInitialized_; }

    // Built-in shader programs
    enum class ShaderType {
        Shape,      // For RectangleShape, CircleShape, etc.
        Sprite,     // For textured sprites
        Text,       // For text rendering
        Custom      // User-provided shaders
    };

    // Get a built-in shader program
    unsigned int getShaderProgram(ShaderType type) const;

    // Compile a custom shader program
    unsigned int compileShader(const std::string& vertexSource, const std::string& fragmentSource);
    void deleteShaderProgram(unsigned int programId);

    // Texture management
    unsigned int createTexture(unsigned int width, unsigned int height, const unsigned char* pixels = nullptr);
    void updateTexture(unsigned int textureId, unsigned int x, unsigned int y,
                       unsigned int width, unsigned int height, const unsigned char* pixels);
    void deleteTexture(unsigned int textureId);
    void setTextureSmooth(unsigned int textureId, bool smooth);
    void setTextureRepeated(unsigned int textureId, bool repeated);

    // FBO management
    unsigned int createFBO(unsigned int width, unsigned int height, unsigned int& colorTexture);
    void deleteFBO(unsigned int fboId);
    void bindFBO(unsigned int fboId);
    void unbindFBO();

    // Render state management
    void setViewport(int x, int y, unsigned int width, unsigned int height);
    void setProjection(float left, float right, float bottom, float top);
    void clear(float r, float g, float b, float a);

    // Drawing primitives
    void drawTriangles(const float* vertices, size_t vertexCount,
                       const float* colors, const float* texCoords,
                       unsigned int textureId = 0);

    // Projection matrix access (for shaders)
    const float* getProjectionMatrix() const { return projectionMatrix_; }

private:
    SDL2Renderer() = default;
    ~SDL2Renderer() = default;
    SDL2Renderer(const SDL2Renderer&) = delete;
    SDL2Renderer& operator=(const SDL2Renderer&) = delete;

    bool initialized_ = false;
    bool glInitialized_ = false;

    // Built-in shader programs
    unsigned int shapeProgram_ = 0;
    unsigned int spriteProgram_ = 0;
    unsigned int textProgram_ = 0;

    // Current projection matrix (4x4 orthographic)
    float projectionMatrix_[16] = {0};

    // FBO stack for nested render-to-texture
    std::vector<unsigned int> fboStack_;

    // Helper functions
    bool compileAndLinkProgram(const char* vertexSrc, const char* fragmentSrc, unsigned int& programOut);
    unsigned int compileShaderStage(unsigned int type, const char* source);
    void initBuiltinShaders();
};

// =============================================================================
// Keyboard/Mouse SDL2 Implementation helpers
// =============================================================================

// SDL2 scancode to sf::Keyboard::Key mapping
int sdlScancodeToSfKey(int sdlScancode);
int sfKeyToSdlScancode(int sfKey);

// SDL2 mouse button to sf::Mouse::Button mapping
int sdlButtonToSfButton(int sdlButton);
int sfButtonToSdlButton(int sfButton);

// =============================================================================
// Event translation
// =============================================================================

// Translate SDL_Event to sf::Event
// Returns true if the event was translated, false if it should be ignored
bool translateSDLEvent(const void* sdlEvent, void* sfEvent);

// =============================================================================
// Font Atlas for text rendering
// =============================================================================

class FontAtlas {
public:
    FontAtlas();
    ~FontAtlas();

    // Load font data
    bool load(const unsigned char* fontData, size_t dataSize, float fontSize);

    // Get texture atlas
    unsigned int getTextureId() const { return textureId_; }

    // Get glyph info for rendering
    struct GlyphInfo {
        float u0, v0, u1, v1;   // Texture coordinates
        float xoff, yoff;        // Offset from cursor
        float xadvance;          // How far to advance cursor
        float width, height;     // Glyph dimensions in pixels
    };

    bool getGlyph(uint32_t codepoint, GlyphInfo& info) const;

    // Get font metrics
    float getAscent() const { return ascent_; }
    float getDescent() const { return descent_; }
    float getLineHeight() const { return lineHeight_; }

private:
    unsigned int textureId_ = 0;
    float fontSize_ = 0;
    float ascent_ = 0;
    float descent_ = 0;
    float lineHeight_ = 0;

    // Glyph cache - maps codepoint to glyph info
    std::unordered_map<uint32_t, GlyphInfo> glyphCache_;

    // stb_truetype font info (opaque pointer to avoid header inclusion)
    void* stbFontInfo_ = nullptr;
};

} // namespace sf

#endif // MCRF_SDL2
