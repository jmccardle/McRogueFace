// SDL2Renderer.cpp - OpenGL ES 2 rendering implementation for SDL2 backend
// Implements the SDL2 types defined in SDL2Types.h using SDL2 and OpenGL ES 2

#ifdef MCRF_SDL2

#include "SDL2Renderer.h"
#include "SDL2Types.h"

#include <iostream>
#include <cstring>
#include <cmath>
#include <map>

// SDL2 and OpenGL ES 2 headers
#ifdef __EMSCRIPTEN__
#include <emscripten.h>
#include <emscripten/html5.h>
// Emscripten's USE_SDL=2 port puts headers directly in include path
#include <SDL.h>
#include <SDL_mixer.h>
#include <GLES2/gl2.h>
#else
#include <SDL2/SDL.h>
#include <SDL2/SDL_mixer.h>
#include <SDL2/SDL_opengl.h>
// Desktop OpenGL - we'll use GL 2.1 compatible subset that matches GLES2
#define GL_GLEXT_PROTOTYPES
#include <GL/gl.h>
#endif

// stb_image for image loading (from deps/stb/)
#define STB_IMAGE_IMPLEMENTATION
#include <stb_image.h>

// FreeType for font loading and text rendering with proper outline support
#include <ft2build.h>
#include FT_FREETYPE_H
#include FT_GLYPH_H
#include FT_STROKER_H
#include FT_OUTLINE_H

namespace sf {

// =============================================================================
// Built-in Shaders (GLSL ES 2.0 / GLSL 1.20 compatible)
// =============================================================================

static const char* SHAPE_VERTEX_SHADER = R"(
#ifdef GL_ES
precision mediump float;
#endif
attribute vec2 a_position;
attribute vec4 a_color;
uniform mat4 u_projection;
varying vec4 v_color;

void main() {
    gl_Position = u_projection * vec4(a_position, 0.0, 1.0);
    v_color = a_color;
}
)";

static const char* SHAPE_FRAGMENT_SHADER = R"(
#ifdef GL_ES
precision mediump float;
#endif
varying vec4 v_color;

void main() {
    gl_FragColor = v_color;
}
)";

static const char* SPRITE_VERTEX_SHADER = R"(
#ifdef GL_ES
precision mediump float;
#endif
attribute vec2 a_position;
attribute vec4 a_color;
attribute vec2 a_texcoord;
uniform mat4 u_projection;
varying vec4 v_color;
varying vec2 v_texcoord;

void main() {
    gl_Position = u_projection * vec4(a_position, 0.0, 1.0);
    v_color = a_color;
    v_texcoord = a_texcoord;
}
)";

static const char* SPRITE_FRAGMENT_SHADER = R"(
#ifdef GL_ES
precision mediump float;
#endif
varying vec4 v_color;
varying vec2 v_texcoord;
uniform sampler2D u_texture;

void main() {
    gl_FragColor = texture2D(u_texture, v_texcoord) * v_color;
}
)";

// Text shader - uses alpha from texture, color from vertex
static const char* TEXT_VERTEX_SHADER = SPRITE_VERTEX_SHADER;
static const char* TEXT_FRAGMENT_SHADER = R"(
#ifdef GL_ES
precision mediump float;
#endif
varying vec4 v_color;
varying vec2 v_texcoord;
uniform sampler2D u_texture;

void main() {
    // Font atlas stores glyph alpha in texture alpha channel
    // RGB is white (255,255,255), alpha varies per glyph pixel
    vec4 texSample = texture2D(u_texture, v_texcoord);
    // Use vertex color for RGB, texture alpha for transparency
    gl_FragColor = vec4(v_color.rgb, v_color.a * texSample.a);
}
)";

// =============================================================================
// SDL2Renderer Implementation
// =============================================================================

SDL2Renderer& SDL2Renderer::getInstance() {
    static SDL2Renderer instance;
    return instance;
}

bool SDL2Renderer::init() {
    if (initialized_) return true;

    // Initialize SDL2 if not already done
    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_EVENTS | SDL_INIT_AUDIO) < 0) {
        std::cerr << "SDL2Renderer: Failed to initialize SDL: " << SDL_GetError() << std::endl;
        return false;
    }

    // Initialize SDL2_mixer for audio (non-fatal if it fails)
    if (Mix_OpenAudio(44100, MIX_DEFAULT_FORMAT, 2, 2048) < 0) {
        std::cerr << "SDL2Renderer: Failed to initialize audio: " << Mix_GetError() << std::endl;
        std::cerr << "SDL2Renderer: Continuing without audio support" << std::endl;
    } else {
        Mix_AllocateChannels(16);
        Mix_ChannelFinished(Sound::onChannelFinished);
        audioInitialized_ = true;
        std::cout << "SDL2Renderer: Audio initialized (16 channels, 44100 Hz)" << std::endl;
    }

    // Note: Shaders are initialized in initGL() after GL context is created

    // Set up initial projection matrix (identity)
    memset(projectionMatrix_, 0, sizeof(projectionMatrix_));
    projectionMatrix_[0] = 1.0f;
    projectionMatrix_[5] = 1.0f;
    projectionMatrix_[10] = 1.0f;
    projectionMatrix_[15] = 1.0f;

    initialized_ = true;
    return true;
}

bool SDL2Renderer::initGL() {
    if (glInitialized_) return true;

    // Initialize built-in shaders (requires active GL context)
    initBuiltinShaders();

    glInitialized_ = true;
    return true;
}

void SDL2Renderer::shutdown() {
    if (!initialized_) return;

    // Delete built-in shader programs
    if (shapeProgram_) glDeleteProgram(shapeProgram_);
    if (spriteProgram_) glDeleteProgram(spriteProgram_);
    if (textProgram_) glDeleteProgram(textProgram_);

    shapeProgram_ = spriteProgram_ = textProgram_ = 0;

    // Close audio before SDL_Quit
    if (audioInitialized_) {
        Mix_CloseAudio();
        audioInitialized_ = false;
    }

    SDL_Quit();
    initialized_ = false;
}

void SDL2Renderer::initBuiltinShaders() {
    // Compile shape shader
    if (!compileAndLinkProgram(SHAPE_VERTEX_SHADER, SHAPE_FRAGMENT_SHADER, shapeProgram_)) {
        std::cerr << "SDL2Renderer: Failed to compile shape shader" << std::endl;
    }

    // Compile sprite shader
    if (!compileAndLinkProgram(SPRITE_VERTEX_SHADER, SPRITE_FRAGMENT_SHADER, spriteProgram_)) {
        std::cerr << "SDL2Renderer: Failed to compile sprite shader" << std::endl;
    }

    // Compile text shader
    if (!compileAndLinkProgram(TEXT_VERTEX_SHADER, TEXT_FRAGMENT_SHADER, textProgram_)) {
        std::cerr << "SDL2Renderer: Failed to compile text shader" << std::endl;
    }
}

unsigned int SDL2Renderer::compileShaderStage(unsigned int type, const char* source) {
    unsigned int shader = glCreateShader(type);
    glShaderSource(shader, 1, &source, nullptr);
    glCompileShader(shader);

    int success;
    glGetShaderiv(shader, GL_COMPILE_STATUS, &success);
    if (!success) {
        char infoLog[512];
        glGetShaderInfoLog(shader, 512, nullptr, infoLog);
        std::cerr << "SDL2Renderer: Shader compilation failed: " << infoLog << std::endl;
        glDeleteShader(shader);
        return 0;
    }

    return shader;
}

bool SDL2Renderer::compileAndLinkProgram(const char* vertexSrc, const char* fragmentSrc, unsigned int& programOut) {
    unsigned int vertexShader = compileShaderStage(GL_VERTEX_SHADER, vertexSrc);
    if (!vertexShader) return false;

    unsigned int fragmentShader = compileShaderStage(GL_FRAGMENT_SHADER, fragmentSrc);
    if (!fragmentShader) {
        glDeleteShader(vertexShader);
        return false;
    }

    unsigned int program = glCreateProgram();
    glAttachShader(program, vertexShader);
    glAttachShader(program, fragmentShader);

    // Bind attribute locations before linking
    glBindAttribLocation(program, 0, "a_position");
    glBindAttribLocation(program, 1, "a_color");
    glBindAttribLocation(program, 2, "a_texcoord");

    glLinkProgram(program);

    // Shaders can be deleted after linking
    glDeleteShader(vertexShader);
    glDeleteShader(fragmentShader);

    int success;
    glGetProgramiv(program, GL_LINK_STATUS, &success);
    if (!success) {
        char infoLog[512];
        glGetProgramInfoLog(program, 512, nullptr, infoLog);
        std::cerr << "SDL2Renderer: Program linking failed: " << infoLog << std::endl;
        glDeleteProgram(program);
        return false;
    }

    programOut = program;
    return true;
}

unsigned int SDL2Renderer::getShaderProgram(ShaderType type) const {
    switch (type) {
        case ShaderType::Shape: return shapeProgram_;
        case ShaderType::Sprite: return spriteProgram_;
        case ShaderType::Text: return textProgram_;
        default: return 0;
    }
}

unsigned int SDL2Renderer::compileShader(const std::string& vertexSource, const std::string& fragmentSource) {
    unsigned int program = 0;
    if (compileAndLinkProgram(vertexSource.c_str(), fragmentSource.c_str(), program)) {
        return program;
    }
    return 0;
}

void SDL2Renderer::deleteShaderProgram(unsigned int programId) {
    if (programId) {
        glDeleteProgram(programId);
    }
}

unsigned int SDL2Renderer::createTexture(unsigned int width, unsigned int height, const unsigned char* pixels) {
    unsigned int textureId;
    glGenTextures(1, &textureId);
    glBindTexture(GL_TEXTURE_2D, textureId);

    // Set default texture parameters
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);

    // Upload pixel data (RGBA format)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, pixels);

    return textureId;
}

void SDL2Renderer::updateTexture(unsigned int textureId, unsigned int x, unsigned int y,
                                  unsigned int width, unsigned int height, const unsigned char* pixels) {
    glBindTexture(GL_TEXTURE_2D, textureId);
    glTexSubImage2D(GL_TEXTURE_2D, 0, x, y, width, height, GL_RGBA, GL_UNSIGNED_BYTE, pixels);
}

void SDL2Renderer::deleteTexture(unsigned int textureId) {
    if (textureId) {
        glDeleteTextures(1, &textureId);
    }
}

void SDL2Renderer::setTextureSmooth(unsigned int textureId, bool smooth) {
    glBindTexture(GL_TEXTURE_2D, textureId);
    GLint filter = smooth ? GL_LINEAR : GL_NEAREST;
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, filter);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, filter);
}

void SDL2Renderer::setTextureRepeated(unsigned int textureId, bool repeated) {
    glBindTexture(GL_TEXTURE_2D, textureId);
    GLint wrap = repeated ? GL_REPEAT : GL_CLAMP_TO_EDGE;
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, wrap);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, wrap);
}

unsigned int SDL2Renderer::createFBO(unsigned int width, unsigned int height, unsigned int& colorTexture) {
    // Create color texture
    colorTexture = createTexture(width, height, nullptr);

    // Create FBO
    unsigned int fbo;
    glGenFramebuffers(1, &fbo);
    glBindFramebuffer(GL_FRAMEBUFFER, fbo);

    // Attach color texture
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, colorTexture, 0);

    // Check completeness
    if (glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE) {
        std::cerr << "SDL2Renderer: FBO is not complete" << std::endl;
        glBindFramebuffer(GL_FRAMEBUFFER, 0);
        glDeleteFramebuffers(1, &fbo);
        deleteTexture(colorTexture);
        return 0;
    }

    glBindFramebuffer(GL_FRAMEBUFFER, 0);
    return fbo;
}

void SDL2Renderer::deleteFBO(unsigned int fboId) {
    if (fboId) {
        glDeleteFramebuffers(1, &fboId);
    }
}

void SDL2Renderer::bindFBO(unsigned int fboId) {
    fboStack_.push_back(fboId);
    glBindFramebuffer(GL_FRAMEBUFFER, fboId);
}

void SDL2Renderer::unbindFBO() {
    if (!fboStack_.empty()) {
        fboStack_.pop_back();
    }
    unsigned int fbo = fboStack_.empty() ? 0 : fboStack_.back();
    glBindFramebuffer(GL_FRAMEBUFFER, fbo);
}

void SDL2Renderer::setViewport(int x, int y, unsigned int width, unsigned int height) {
    glViewport(x, y, width, height);
}

void SDL2Renderer::setProjection(float left, float right, float bottom, float top) {
    // Build orthographic projection matrix
    float near = -1.0f;
    float far = 1.0f;

    memset(projectionMatrix_, 0, sizeof(projectionMatrix_));
    projectionMatrix_[0] = 2.0f / (right - left);
    projectionMatrix_[5] = 2.0f / (top - bottom);
    projectionMatrix_[10] = -2.0f / (far - near);
    projectionMatrix_[12] = -(right + left) / (right - left);
    projectionMatrix_[13] = -(top + bottom) / (top - bottom);
    projectionMatrix_[14] = -(far + near) / (far - near);
    projectionMatrix_[15] = 1.0f;
}

void SDL2Renderer::clear(float r, float g, float b, float a) {
    glClearColor(r, g, b, a);
    glClear(GL_COLOR_BUFFER_BIT);
}

void SDL2Renderer::pushRenderState(unsigned int width, unsigned int height) {
    RenderState state;

    // Save current viewport
    glGetIntegerv(GL_VIEWPORT, state.viewport);

    // Save current projection
    memcpy(state.projection, projectionMatrix_, sizeof(projectionMatrix_));

    renderStateStack_.push_back(state);

    // Set new viewport and projection for FBO
    glViewport(0, 0, width, height);
    setProjection(0, static_cast<float>(width), static_cast<float>(height), 0);
}

void SDL2Renderer::popRenderState() {
    if (renderStateStack_.empty()) return;

    RenderState& state = renderStateStack_.back();

    // Restore viewport
    glViewport(state.viewport[0], state.viewport[1], state.viewport[2], state.viewport[3]);

    // Restore projection
    memcpy(projectionMatrix_, state.projection, sizeof(projectionMatrix_));

    renderStateStack_.pop_back();
}

void SDL2Renderer::drawTriangles(const float* vertices, size_t vertexCount,
                                  const float* colors, const float* texCoords,
                                  unsigned int textureId, ShaderType shaderType) {
    if (vertexCount == 0) return;

    // Select shader based on type parameter
    unsigned int program;
    switch (shaderType) {
        case ShaderType::Text:
            program = textProgram_;
            break;
        case ShaderType::Sprite:
            program = spriteProgram_;
            break;
        case ShaderType::Shape:
        default:
            // Auto-select based on texture
            program = textureId ? spriteProgram_ : shapeProgram_;
            break;
    }
    glUseProgram(program);

    // Set projection uniform
    int projLoc = glGetUniformLocation(program, "u_projection");
    glUniformMatrix4fv(projLoc, 1, GL_FALSE, projectionMatrix_);

    // Enable blending
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

    // Set up vertex attributes
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, vertices);

    if (colors) {
        glEnableVertexAttribArray(1);
        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 0, colors);
    }

    if (texCoords && textureId) {
        glEnableVertexAttribArray(2);
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, texCoords);

        glActiveTexture(GL_TEXTURE0);
        glBindTexture(GL_TEXTURE_2D, textureId);
        int texLoc = glGetUniformLocation(program, "u_texture");
        glUniform1i(texLoc, 0);
    }

    // Draw
    glDrawArrays(GL_TRIANGLES, 0, vertexCount);

    // Clean up
    glDisableVertexAttribArray(0);
    if (colors) glDisableVertexAttribArray(1);
    if (texCoords && textureId) glDisableVertexAttribArray(2);
}

// =============================================================================
// sf::RenderWindow Implementation
// =============================================================================

RenderWindow::~RenderWindow() {
    close();
}

void RenderWindow::create(VideoMode mode, const std::string& title, uint32_t style) {
    // Close any existing window
    close();

    // Initialize SDL2 renderer
    if (!SDL2Renderer::getInstance().init()) {
        std::cerr << "RenderWindow: Failed to initialize SDL2Renderer" << std::endl;
        return;
    }

    // Set OpenGL attributes for ES2/WebGL compatibility
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 2);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 0);
#ifdef __EMSCRIPTEN__
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_ES);
#else
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_COMPATIBILITY);
#endif
    SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1);
    SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, 0);

    // Convert sf::Style to SDL window flags
    Uint32 sdlFlags = SDL_WINDOW_OPENGL | SDL_WINDOW_SHOWN;
    if (style & Style::Fullscreen) {
        sdlFlags |= SDL_WINDOW_FULLSCREEN;
    }
    if (style & Style::Resize) {
        sdlFlags |= SDL_WINDOW_RESIZABLE;
    }
    if (!(style & Style::Titlebar)) {
        sdlFlags |= SDL_WINDOW_BORDERLESS;
    }

#ifdef __EMSCRIPTEN__
    // For Emscripten, tell SDL2 which canvas element to use
    // SDL_HINT_EMSCRIPTEN_CANVAS_SELECTOR = "SDL_EMSCRIPTEN_CANVAS_SELECTOR"
    SDL_SetHint("SDL_EMSCRIPTEN_CANVAS_SELECTOR", "#canvas");

    // Set the canvas size explicitly before creating the window
    emscripten_set_canvas_element_size("#canvas", mode.width, mode.height);
#endif

    // Create window
    SDL_Window* window = SDL_CreateWindow(
        title.c_str(),
        SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
        mode.width, mode.height,
        sdlFlags
    );

    if (!window) {
        std::cerr << "RenderWindow: Failed to create window: " << SDL_GetError() << std::endl;
        return;
    }

    // Create OpenGL context
    SDL_GLContext context = SDL_GL_CreateContext(window);
    if (!context) {
        std::cerr << "RenderWindow: Failed to create GL context: " << SDL_GetError() << std::endl;
        SDL_DestroyWindow(window);
        return;
    }

    sdlWindow_ = window;
    glContext_ = context;
    size_ = Vector2u(mode.width, mode.height);
    title_ = title;
    open_ = true;

#ifdef __EMSCRIPTEN__
    // Force canvas backing buffer size AFTER SDL window creation (SDL may have reset it)
    // CSS display size is controlled by the HTML shell template (fullscreen or layout-constrained)
    emscripten_set_canvas_element_size("#canvas", mode.width, mode.height);

    // Re-make context current after canvas resize
    SDL_GL_MakeCurrent(window, context);
#endif

    // Initialize OpenGL resources now that we have a context
    if (!SDL2Renderer::getInstance().initGL()) {
        std::cerr << "RenderWindow: Failed to initialize OpenGL resources" << std::endl;
    }

    // Set up initial view
    view_ = View(FloatRect(0, 0, static_cast<float>(mode.width), static_cast<float>(mode.height)));
    defaultView_ = view_;

    // Set up OpenGL state
    glViewport(0, 0, mode.width, mode.height);
    SDL2Renderer::getInstance().setProjection(0, mode.width, mode.height, 0);

    // Enable blending for transparency
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

    // Initial clear
    glClearColor(0.2f, 0.3f, 0.4f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT);
    SDL_GL_SwapWindow(window);
}

void RenderWindow::close() {
    if (glContext_) {
        SDL_GL_DeleteContext(static_cast<SDL_GLContext>(glContext_));
        glContext_ = nullptr;
    }
    if (sdlWindow_) {
        SDL_DestroyWindow(static_cast<SDL_Window*>(sdlWindow_));
        sdlWindow_ = nullptr;
    }
    open_ = false;
}

void RenderWindow::clear(const Color& color) {
    SDL2Renderer::getInstance().clear(
        color.r / 255.0f,
        color.g / 255.0f,
        color.b / 255.0f,
        color.a / 255.0f
    );
}

void RenderWindow::display() {
    SDL_GL_SwapWindow(static_cast<SDL_Window*>(sdlWindow_));
}

void RenderWindow::setTitle(const std::string& title) {
    title_ = title;
    if (sdlWindow_) {
        SDL_SetWindowTitle(static_cast<SDL_Window*>(sdlWindow_), title.c_str());
    }
}

void RenderWindow::setFramerateLimit(unsigned int limit) {
    // SDL2 doesn't have built-in framerate limiting
    // We'd need to implement this manually with timing
    // For now, VSync is the recommended approach
}

void RenderWindow::setVerticalSyncEnabled(bool enabled) {
    SDL_GL_SetSwapInterval(enabled ? 1 : 0);
}

void RenderWindow::setVisible(bool visible) {
    if (sdlWindow_) {
        if (visible) {
            SDL_ShowWindow(static_cast<SDL_Window*>(sdlWindow_));
        } else {
            SDL_HideWindow(static_cast<SDL_Window*>(sdlWindow_));
        }
    }
}

void RenderWindow::setMouseCursorVisible(bool visible) {
    SDL_ShowCursor(visible ? SDL_ENABLE : SDL_DISABLE);
}

void RenderWindow::setMouseCursorGrabbed(bool grabbed) {
    if (sdlWindow_) {
        SDL_SetWindowGrab(static_cast<SDL_Window*>(sdlWindow_), grabbed ? SDL_TRUE : SDL_FALSE);
    }
}

Vector2i RenderWindow::getPosition() const {
    int x = 0, y = 0;
    if (sdlWindow_) {
        SDL_GetWindowPosition(static_cast<SDL_Window*>(sdlWindow_), &x, &y);
    }
    return Vector2i(x, y);
}

void RenderWindow::setPosition(const Vector2i& position) {
    if (sdlWindow_) {
        SDL_SetWindowPosition(static_cast<SDL_Window*>(sdlWindow_), position.x, position.y);
    }
}

void RenderWindow::setSize(const Vector2u& size) {
    size_ = size;
    if (sdlWindow_) {
        SDL_SetWindowSize(static_cast<SDL_Window*>(sdlWindow_), size.x, size.y);
        glViewport(0, 0, size.x, size.y);
#ifdef __EMSCRIPTEN__
        emscripten_set_canvas_element_size("#canvas", size.x, size.y);
#endif
    }
}

// Event polling - translate SDL events to sf::Event
bool RenderWindow::pollEvent(Event& event) {
    SDL_Event sdlEvent;
    while (SDL_PollEvent(&sdlEvent)) {
        if (translateSDLEvent(&sdlEvent, &event)) {
            return true;
        }
    }
    return false;
}

bool RenderWindow::waitEvent(Event& event) {
    SDL_Event sdlEvent;
    if (SDL_WaitEvent(&sdlEvent)) {
        return translateSDLEvent(&sdlEvent, &event);
    }
    return false;
}

// =============================================================================
// VideoMode Implementation
// =============================================================================

VideoMode VideoMode::getDesktopMode() {
    SDL_DisplayMode mode;
    if (SDL_GetDesktopDisplayMode(0, &mode) == 0) {
        return VideoMode(mode.w, mode.h, SDL_BITSPERPIXEL(mode.format));
    }
    return VideoMode(1920, 1080, 32);
}

const std::vector<VideoMode>& VideoMode::getFullscreenModes() {
    static std::vector<VideoMode> modes;
    static bool initialized = false;

    if (!initialized) {
        int numModes = SDL_GetNumDisplayModes(0);
        for (int i = 0; i < numModes; ++i) {
            SDL_DisplayMode mode;
            if (SDL_GetDisplayMode(0, i, &mode) == 0) {
                modes.push_back(VideoMode(mode.w, mode.h, SDL_BITSPERPIXEL(mode.format)));
            }
        }
        initialized = true;
    }

    return modes;
}

// =============================================================================
// Event Translation
// =============================================================================

// SDL scancode to sf::Keyboard::Key mapping table
static const Keyboard::Key SDL_SCANCODE_TO_SF_KEY[] = {
    // This is a simplified mapping - full implementation would have all keys
    Keyboard::Unknown  // Placeholder
};

bool translateSDLEvent(const void* sdlEventPtr, void* sfEventPtr) {
    const SDL_Event& sdlEvent = *static_cast<const SDL_Event*>(sdlEventPtr);
    Event& sfEvent = *static_cast<Event*>(sfEventPtr);

    switch (sdlEvent.type) {
        case SDL_QUIT:
            sfEvent.type = Event::Closed;
            return true;

        case SDL_WINDOWEVENT:
            switch (sdlEvent.window.event) {
                case SDL_WINDOWEVENT_RESIZED:
                case SDL_WINDOWEVENT_SIZE_CHANGED:
                    sfEvent.type = Event::Resized;
                    sfEvent.size.width = sdlEvent.window.data1;
                    sfEvent.size.height = sdlEvent.window.data2;
                    return true;
                case SDL_WINDOWEVENT_FOCUS_GAINED:
                    sfEvent.type = Event::GainedFocus;
                    return true;
                case SDL_WINDOWEVENT_FOCUS_LOST:
                    sfEvent.type = Event::LostFocus;
                    return true;
                case SDL_WINDOWEVENT_ENTER:
                    sfEvent.type = Event::MouseEntered;
                    return true;
                case SDL_WINDOWEVENT_LEAVE:
                    sfEvent.type = Event::MouseLeft;
                    return true;
            }
            break;

        case SDL_KEYDOWN:
        case SDL_KEYUP:
            sfEvent.type = sdlEvent.type == SDL_KEYDOWN ? Event::KeyPressed : Event::KeyReleased;
            sfEvent.key.code = static_cast<Keyboard::Key>(sdlScancodeToSfKey(sdlEvent.key.keysym.scancode));
            sfEvent.key.alt = (sdlEvent.key.keysym.mod & KMOD_ALT) != 0;
            sfEvent.key.control = (sdlEvent.key.keysym.mod & KMOD_CTRL) != 0;
            sfEvent.key.shift = (sdlEvent.key.keysym.mod & KMOD_SHIFT) != 0;
            sfEvent.key.system = (sdlEvent.key.keysym.mod & KMOD_GUI) != 0;
            return true;

        case SDL_TEXTINPUT:
            sfEvent.type = Event::TextEntered;
            // Convert UTF-8 to single codepoint (simplified - only handles ASCII and simple UTF-8)
            sfEvent.text.unicode = static_cast<unsigned char>(sdlEvent.text.text[0]);
            return true;

        case SDL_MOUSEMOTION:
            sfEvent.type = Event::MouseMoved;
            sfEvent.mouseMove.x = sdlEvent.motion.x;
            sfEvent.mouseMove.y = sdlEvent.motion.y;
            return true;

        case SDL_MOUSEBUTTONDOWN:
        case SDL_MOUSEBUTTONUP:
            sfEvent.type = sdlEvent.type == SDL_MOUSEBUTTONDOWN ? Event::MouseButtonPressed : Event::MouseButtonReleased;
            sfEvent.mouseButton.button = static_cast<Mouse::Button>(sdlButtonToSfButton(sdlEvent.button.button));
            sfEvent.mouseButton.x = sdlEvent.button.x;
            sfEvent.mouseButton.y = sdlEvent.button.y;
            return true;

        case SDL_MOUSEWHEEL:
            sfEvent.type = Event::MouseWheelScrolled;
            sfEvent.mouseWheelScroll.wheel = sdlEvent.wheel.x != 0 ? Mouse::HorizontalWheel : Mouse::VerticalWheel;
            sfEvent.mouseWheelScroll.delta = sdlEvent.wheel.x != 0 ? sdlEvent.wheel.x : sdlEvent.wheel.y;
            // Get current mouse position
            SDL_GetMouseState(&sfEvent.mouseWheelScroll.x, &sfEvent.mouseWheelScroll.y);
            return true;
    }

    return false;
}

// =============================================================================
// Keyboard/Mouse Implementation
// =============================================================================

int sdlScancodeToSfKey(int sdlScancode) {
    // Simplified mapping - covers most common keys
    switch (sdlScancode) {
        case SDL_SCANCODE_A: return Keyboard::A;
        case SDL_SCANCODE_B: return Keyboard::B;
        case SDL_SCANCODE_C: return Keyboard::C;
        case SDL_SCANCODE_D: return Keyboard::D;
        case SDL_SCANCODE_E: return Keyboard::E;
        case SDL_SCANCODE_F: return Keyboard::F;
        case SDL_SCANCODE_G: return Keyboard::G;
        case SDL_SCANCODE_H: return Keyboard::H;
        case SDL_SCANCODE_I: return Keyboard::I;
        case SDL_SCANCODE_J: return Keyboard::J;
        case SDL_SCANCODE_K: return Keyboard::K;
        case SDL_SCANCODE_L: return Keyboard::L;
        case SDL_SCANCODE_M: return Keyboard::M;
        case SDL_SCANCODE_N: return Keyboard::N;
        case SDL_SCANCODE_O: return Keyboard::O;
        case SDL_SCANCODE_P: return Keyboard::P;
        case SDL_SCANCODE_Q: return Keyboard::Q;
        case SDL_SCANCODE_R: return Keyboard::R;
        case SDL_SCANCODE_S: return Keyboard::S;
        case SDL_SCANCODE_T: return Keyboard::T;
        case SDL_SCANCODE_U: return Keyboard::U;
        case SDL_SCANCODE_V: return Keyboard::V;
        case SDL_SCANCODE_W: return Keyboard::W;
        case SDL_SCANCODE_X: return Keyboard::X;
        case SDL_SCANCODE_Y: return Keyboard::Y;
        case SDL_SCANCODE_Z: return Keyboard::Z;
        case SDL_SCANCODE_0: return Keyboard::Num0;
        case SDL_SCANCODE_1: return Keyboard::Num1;
        case SDL_SCANCODE_2: return Keyboard::Num2;
        case SDL_SCANCODE_3: return Keyboard::Num3;
        case SDL_SCANCODE_4: return Keyboard::Num4;
        case SDL_SCANCODE_5: return Keyboard::Num5;
        case SDL_SCANCODE_6: return Keyboard::Num6;
        case SDL_SCANCODE_7: return Keyboard::Num7;
        case SDL_SCANCODE_8: return Keyboard::Num8;
        case SDL_SCANCODE_9: return Keyboard::Num9;
        case SDL_SCANCODE_ESCAPE: return Keyboard::Escape;
        case SDL_SCANCODE_LCTRL: return Keyboard::LControl;
        case SDL_SCANCODE_LSHIFT: return Keyboard::LShift;
        case SDL_SCANCODE_LALT: return Keyboard::LAlt;
        case SDL_SCANCODE_LGUI: return Keyboard::LSystem;
        case SDL_SCANCODE_RCTRL: return Keyboard::RControl;
        case SDL_SCANCODE_RSHIFT: return Keyboard::RShift;
        case SDL_SCANCODE_RALT: return Keyboard::RAlt;
        case SDL_SCANCODE_RGUI: return Keyboard::RSystem;
        case SDL_SCANCODE_SPACE: return Keyboard::Space;
        case SDL_SCANCODE_RETURN: return Keyboard::Enter;
        case SDL_SCANCODE_BACKSPACE: return Keyboard::Backspace;
        case SDL_SCANCODE_TAB: return Keyboard::Tab;
        case SDL_SCANCODE_LEFT: return Keyboard::Left;
        case SDL_SCANCODE_RIGHT: return Keyboard::Right;
        case SDL_SCANCODE_UP: return Keyboard::Up;
        case SDL_SCANCODE_DOWN: return Keyboard::Down;
        case SDL_SCANCODE_F1: return Keyboard::F1;
        case SDL_SCANCODE_F2: return Keyboard::F2;
        case SDL_SCANCODE_F3: return Keyboard::F3;
        case SDL_SCANCODE_F4: return Keyboard::F4;
        case SDL_SCANCODE_F5: return Keyboard::F5;
        case SDL_SCANCODE_F6: return Keyboard::F6;
        case SDL_SCANCODE_F7: return Keyboard::F7;
        case SDL_SCANCODE_F8: return Keyboard::F8;
        case SDL_SCANCODE_F9: return Keyboard::F9;
        case SDL_SCANCODE_F10: return Keyboard::F10;
        case SDL_SCANCODE_F11: return Keyboard::F11;
        case SDL_SCANCODE_F12: return Keyboard::F12;
        default: return Keyboard::Unknown;
    }
}

int sfKeyToSdlScancode(int sfKey) {
    // Reverse mapping (simplified)
    switch (sfKey) {
        case Keyboard::A: return SDL_SCANCODE_A;
        case Keyboard::W: return SDL_SCANCODE_W;
        case Keyboard::S: return SDL_SCANCODE_S;
        case Keyboard::D: return SDL_SCANCODE_D;
        case Keyboard::Space: return SDL_SCANCODE_SPACE;
        case Keyboard::Escape: return SDL_SCANCODE_ESCAPE;
        // Add more as needed
        default: return SDL_SCANCODE_UNKNOWN;
    }
}

int sdlButtonToSfButton(int sdlButton) {
    switch (sdlButton) {
        case SDL_BUTTON_LEFT: return Mouse::Left;
        case SDL_BUTTON_RIGHT: return Mouse::Right;
        case SDL_BUTTON_MIDDLE: return Mouse::Middle;
        case SDL_BUTTON_X1: return Mouse::XButton1;
        case SDL_BUTTON_X2: return Mouse::XButton2;
        default: return Mouse::Left;
    }
}

int sfButtonToSdlButton(int sfButton) {
    switch (sfButton) {
        case Mouse::Left: return SDL_BUTTON_LEFT;
        case Mouse::Right: return SDL_BUTTON_RIGHT;
        case Mouse::Middle: return SDL_BUTTON_MIDDLE;
        case Mouse::XButton1: return SDL_BUTTON_X1;
        case Mouse::XButton2: return SDL_BUTTON_X2;
        default: return SDL_BUTTON_LEFT;
    }
}

bool Keyboard::isKeyPressed(Key key) {
    const Uint8* state = SDL_GetKeyboardState(nullptr);
    int scancode = sfKeyToSdlScancode(key);
    return scancode != SDL_SCANCODE_UNKNOWN && state[scancode];
}

bool Mouse::isButtonPressed(Button button) {
    Uint32 state = SDL_GetMouseState(nullptr, nullptr);
    return state & SDL_BUTTON(sfButtonToSdlButton(button));
}

Vector2i Mouse::getPosition() {
    int x, y;
    SDL_GetMouseState(&x, &y);
    return Vector2i(x, y);
}

Vector2i Mouse::getPosition(const RenderWindow& relativeTo) {
    // For now, same as global position (would need window-relative in multi-window setup)
    return getPosition();
}

void Mouse::setPosition(const Vector2i& position) {
    SDL_WarpMouseGlobal(position.x, position.y);
}

void Mouse::setPosition(const Vector2i& position, const RenderWindow& relativeTo) {
    SDL_WarpMouseInWindow(
        static_cast<SDL_Window*>(relativeTo.getNativeWindowHandle()),
        position.x, position.y
    );
}

// =============================================================================
// RenderTarget Implementation
// =============================================================================

void RenderTarget::clear(const Color& color) {
    SDL2Renderer::getInstance().clear(
        color.r / 255.0f,
        color.g / 255.0f,
        color.b / 255.0f,
        color.a / 255.0f
    );
}

void RenderTarget::draw(const Vertex* vertices, size_t vertexCount, PrimitiveType type, const RenderStates& states) {
    // TODO: Implement with proper vertex buffer handling
}

void RenderTarget::draw(const VertexArray& vertices, const RenderStates& states) {
    draw(&vertices[0], vertices.getVertexCount(), vertices.getPrimitiveType(), states);
}

void RenderTarget::setView(const View& view) {
    view_ = view;

    // Apply the view's viewport (normalized 0-1 coords) to OpenGL
    auto vp = view.getViewport();
    int px = static_cast<int>(vp.left * size_.x);
    // OpenGL viewport origin is bottom-left, SFML is top-left
    int py = static_cast<int>((1.0f - vp.top - vp.height) * size_.y);
    int pw = static_cast<int>(vp.width * size_.x);
    int ph = static_cast<int>(vp.height * size_.y);
    glViewport(px, py, pw, ph);

    // Set projection to map view center/size to the viewport
    auto center = view.getCenter();
    auto sz = view.getSize();
    float left = center.x - sz.x / 2.0f;
    float right = center.x + sz.x / 2.0f;
    float top = center.y - sz.y / 2.0f;
    float bottom = center.y + sz.y / 2.0f;
    SDL2Renderer::getInstance().setProjection(left, right, bottom, top);
}

IntRect RenderTarget::getViewport(const View& view) const {
    auto vp = view.getViewport();
    return IntRect(
        static_cast<int>(vp.left * size_.x),
        static_cast<int>(vp.top * size_.y),
        static_cast<int>(vp.width * size_.x),
        static_cast<int>(vp.height * size_.y)
    );
}

Vector2f RenderTarget::mapPixelToCoords(const Vector2i& point) const {
    return mapPixelToCoords(point, view_);
}

Vector2f RenderTarget::mapPixelToCoords(const Vector2i& point, const View& view) const {
    // Convert pixel position to world coordinates through the view
    auto viewport = getViewport(view);
    auto center = view.getCenter();
    auto sz = view.getSize();

    // Normalize point within viewport (0-1)
    float nx = (static_cast<float>(point.x) - viewport.left) / viewport.width;
    float ny = (static_cast<float>(point.y) - viewport.top) / viewport.height;

    // Map to view coordinates
    return Vector2f(
        center.x + sz.x * (nx - 0.5f),
        center.y + sz.y * (ny - 0.5f)
    );
}

Vector2i RenderTarget::mapCoordsToPixel(const Vector2f& point) const {
    return mapCoordsToPixel(point, view_);
}

Vector2i RenderTarget::mapCoordsToPixel(const Vector2f& point, const View& view) const {
    // Convert world coordinates to pixel position through the view
    auto viewport = getViewport(view);
    auto center = view.getCenter();
    auto sz = view.getSize();

    // Normalize within view (0-1)
    float nx = (point.x - center.x) / sz.x + 0.5f;
    float ny = (point.y - center.y) / sz.y + 0.5f;

    // Map to pixel coordinates within viewport
    return Vector2i(
        static_cast<int>(viewport.left + nx * viewport.width),
        static_cast<int>(viewport.top + ny * viewport.height)
    );
}

// =============================================================================
// RenderTexture Implementation
// =============================================================================

RenderTexture::~RenderTexture() {
    if (fboId_) {
        SDL2Renderer::getInstance().deleteFBO(fboId_);
    }
}

bool RenderTexture::create(unsigned int width, unsigned int height) {
    size_ = Vector2u(width, height);

    unsigned int colorTexture = 0;
    fboId_ = SDL2Renderer::getInstance().createFBO(width, height, colorTexture);

    if (!fboId_) {
        return false;
    }

    // Set up internal texture to point to FBO color attachment
    texture_.setNativeHandle(colorTexture);
    texture_.setSize(width, height);  // Critical: Sprite::draw needs texture size for UV calc
    texture_.setFlippedY(true);       // FBO textures are Y-flipped in OpenGL

    view_ = View(FloatRect(0, 0, static_cast<float>(width), static_cast<float>(height)));
    defaultView_ = view_;

    return true;
}

void RenderTexture::clear(const Color& color) {
    SDL2Renderer::getInstance().bindFBO(fboId_);
    SDL2Renderer::getInstance().pushRenderState(size_.x, size_.y);
    RenderTarget::clear(color);
}

void RenderTexture::display() {
    SDL2Renderer::getInstance().popRenderState();
    SDL2Renderer::getInstance().unbindFBO();
}

// =============================================================================
// Texture Implementation
// =============================================================================

Texture::~Texture() {
    if (textureId_) {
        SDL2Renderer::getInstance().deleteTexture(textureId_);
    }
}

Texture::Texture(const Texture& other)
    : size_(other.size_), smooth_(other.smooth_), repeated_(other.repeated_) {
    if (other.textureId_) {
        // Create new texture with same properties
        textureId_ = SDL2Renderer::getInstance().createTexture(size_.x, size_.y, nullptr);
        // Note: Would need to copy pixel data for full implementation
    }
}

Texture& Texture::operator=(const Texture& other) {
    if (this != &other) {
        if (textureId_) {
            SDL2Renderer::getInstance().deleteTexture(textureId_);
        }
        size_ = other.size_;
        smooth_ = other.smooth_;
        repeated_ = other.repeated_;
        if (other.textureId_) {
            textureId_ = SDL2Renderer::getInstance().createTexture(size_.x, size_.y, nullptr);
        }
    }
    return *this;
}

bool Texture::create(unsigned int width, unsigned int height) {
    if (textureId_) {
        SDL2Renderer::getInstance().deleteTexture(textureId_);
    }
    size_ = Vector2u(width, height);
    textureId_ = SDL2Renderer::getInstance().createTexture(width, height, nullptr);
    return textureId_ != 0;
}

bool Texture::loadFromFile(const std::string& filename) {
    int width, height, channels;
    unsigned char* data = stbi_load(filename.c_str(), &width, &height, &channels, 4);

    if (!data) {
        std::cerr << "Texture: Failed to load " << filename << ": " << stbi_failure_reason() << std::endl;
        return false;
    }

    if (textureId_) {
        SDL2Renderer::getInstance().deleteTexture(textureId_);
    }

    size_ = Vector2u(width, height);
    textureId_ = SDL2Renderer::getInstance().createTexture(width, height, data);

    stbi_image_free(data);
    return textureId_ != 0;
}

bool Texture::loadFromMemory(const void* data, size_t size) {
    int width, height, channels;
    unsigned char* pixels = stbi_load_from_memory(
        static_cast<const unsigned char*>(data), size, &width, &height, &channels, 4);

    if (!pixels) {
        return false;
    }

    if (textureId_) {
        SDL2Renderer::getInstance().deleteTexture(textureId_);
    }

    size_ = Vector2u(width, height);
    textureId_ = SDL2Renderer::getInstance().createTexture(width, height, pixels);

    stbi_image_free(pixels);
    return textureId_ != 0;
}

bool Texture::loadFromImage(const Image& image) {
    if (textureId_) {
        SDL2Renderer::getInstance().deleteTexture(textureId_);
    }
    auto imgSize = image.getSize();
    size_ = imgSize;
    textureId_ = SDL2Renderer::getInstance().createTexture(
        imgSize.x, imgSize.y, image.getPixelsPtr());
    return textureId_ != 0;
}

void Texture::setSmooth(bool smooth) {
    smooth_ = smooth;
    if (textureId_) {
        SDL2Renderer::getInstance().setTextureSmooth(textureId_, smooth);
    }
}

void Texture::setRepeated(bool repeated) {
    repeated_ = repeated;
    if (textureId_) {
        SDL2Renderer::getInstance().setTextureRepeated(textureId_, repeated);
    }
}

Image Texture::copyToImage() const {
    Image img;
    img.create(size_.x, size_.y);
    // TODO: Read back from GPU texture
    return img;
}

void Texture::update(const RenderWindow& window) {
    // TODO: Copy window contents to texture
}

void Texture::update(const Uint8* pixels) {
    if (textureId_ && pixels) {
        SDL2Renderer::getInstance().updateTexture(textureId_, 0, 0, size_.x, size_.y, pixels);
    }
}

void Texture::update(const Uint8* pixels, unsigned int width, unsigned int height, unsigned int x, unsigned int y) {
    if (textureId_ && pixels) {
        SDL2Renderer::getInstance().updateTexture(textureId_, x, y, width, height, pixels);
    }
}

// =============================================================================
// Image Implementation
// =============================================================================

bool Image::loadFromFile(const std::string& filename) {
    int width, height, channels;
    unsigned char* data = stbi_load(filename.c_str(), &width, &height, &channels, 4);

    if (!data) {
        return false;
    }

    size_ = Vector2u(width, height);
    pixels_.resize(width * height * 4);
    memcpy(pixels_.data(), data, pixels_.size());

    stbi_image_free(data);
    return true;
}

bool Image::saveToFile(const std::string& filename) const {
    // TODO: Use stb_image_write
    return false;
}

// =============================================================================
// Font Implementation (FreeType-based)
// =============================================================================

Font::~Font() {
    if (ftStroker_) {
        FT_Stroker_Done(static_cast<FT_Stroker>(ftStroker_));
        ftStroker_ = nullptr;
    }
    if (ftFace_) {
        FT_Done_Face(static_cast<FT_Face>(ftFace_));
        ftFace_ = nullptr;
    }
    if (ftLibrary_) {
        FT_Done_FreeType(static_cast<FT_Library>(ftLibrary_));
        ftLibrary_ = nullptr;
    }
}

bool Font::loadFromFile(const std::string& filename) {
    // Read file into memory first (FreeType needs persistent data)
    FILE* file = fopen(filename.c_str(), "rb");
    if (!file) {
        std::cerr << "Font: Failed to open file: " << filename << std::endl;
        return false;
    }

    fseek(file, 0, SEEK_END);
    size_t size = ftell(file);
    fseek(file, 0, SEEK_SET);

    fontData_.resize(size);
    fread(fontData_.data(), 1, size, file);
    fclose(file);

    // Initialize FreeType library
    FT_Library library;
    if (FT_Init_FreeType(&library) != 0) {
        std::cerr << "Font: Failed to initialize FreeType library" << std::endl;
        return false;
    }
    ftLibrary_ = library;

    // Create face from memory (font data must persist!)
    FT_Face face;
    if (FT_New_Memory_Face(library, fontData_.data(), fontData_.size(), 0, &face) != 0) {
        std::cerr << "Font: Failed to create FreeType face from: " << filename << std::endl;
        FT_Done_FreeType(library);
        ftLibrary_ = nullptr;
        return false;
    }
    ftFace_ = face;

    // Select Unicode charmap
    FT_Select_Charmap(face, FT_ENCODING_UNICODE);

    // Create stroker for outline rendering
    FT_Stroker stroker;
    if (FT_Stroker_New(library, &stroker) != 0) {
        std::cerr << "Font: Failed to create FreeType stroker" << std::endl;
        FT_Done_Face(face);
        FT_Done_FreeType(library);
        ftFace_ = nullptr;
        ftLibrary_ = nullptr;
        return false;
    }
    ftStroker_ = stroker;

    loaded_ = true;
    return true;
}

bool Font::loadFromMemory(const void* data, size_t sizeInBytes) {
    fontData_.resize(sizeInBytes);
    memcpy(fontData_.data(), data, sizeInBytes);

    // Initialize FreeType library
    FT_Library library;
    if (FT_Init_FreeType(&library) != 0) {
        std::cerr << "Font: Failed to initialize FreeType library" << std::endl;
        return false;
    }
    ftLibrary_ = library;

    // Create face from memory
    FT_Face face;
    if (FT_New_Memory_Face(library, fontData_.data(), fontData_.size(), 0, &face) != 0) {
        std::cerr << "Font: Failed to create FreeType face from memory" << std::endl;
        FT_Done_FreeType(library);
        ftLibrary_ = nullptr;
        return false;
    }
    ftFace_ = face;

    // Select Unicode charmap
    FT_Select_Charmap(face, FT_ENCODING_UNICODE);

    // Create stroker for outline rendering
    FT_Stroker stroker;
    if (FT_Stroker_New(library, &stroker) != 0) {
        std::cerr << "Font: Failed to create FreeType stroker" << std::endl;
        FT_Done_Face(face);
        FT_Done_FreeType(library);
        ftFace_ = nullptr;
        ftLibrary_ = nullptr;
        return false;
    }
    ftStroker_ = stroker;

    loaded_ = true;
    return true;
}

// =============================================================================
// Shape Drawing (Stubs - implement with vertex generation)
// =============================================================================

void Shape::draw(RenderTarget& target, RenderStates states) const {
    size_t pointCount = getPointCount();
    if (pointCount < 3) return;

    // Get the combined transform
    Transform combinedTransform = states.transform * getTransform();

    // Build vertex data for fill (triangle fan from center)
    std::vector<float> vertices;
    std::vector<float> colors;

    // Calculate center point
    Vector2f center(0, 0);
    for (size_t i = 0; i < pointCount; ++i) {
        center.x += getPoint(i).x;
        center.y += getPoint(i).y;
    }
    center.x /= pointCount;
    center.y /= pointCount;

    // Transform center
    Vector2f transformedCenter = combinedTransform.transformPoint(center);

    // Build triangles (fan from center)
    Color fill = getFillColor();
    float fr = fill.r / 255.0f;
    float fg = fill.g / 255.0f;
    float fb = fill.b / 255.0f;
    float fa = fill.a / 255.0f;

    for (size_t i = 0; i < pointCount; ++i) {
        size_t next = (i + 1) % pointCount;

        Vector2f p1 = combinedTransform.transformPoint(getPoint(i));
        Vector2f p2 = combinedTransform.transformPoint(getPoint(next));

        // Triangle: center, p1, p2
        vertices.push_back(transformedCenter.x);
        vertices.push_back(transformedCenter.y);
        vertices.push_back(p1.x);
        vertices.push_back(p1.y);
        vertices.push_back(p2.x);
        vertices.push_back(p2.y);

        // Colors for each vertex
        for (int v = 0; v < 3; ++v) {
            colors.push_back(fr);
            colors.push_back(fg);
            colors.push_back(fb);
            colors.push_back(fa);
        }
    }

    // Draw fill
    if (fill.a > 0 && !vertices.empty()) {
        SDL2Renderer::getInstance().drawTriangles(
            vertices.data(), vertices.size() / 2,
            colors.data(), nullptr, 0
        );
    }

    // Draw outline if thickness > 0
    float outlineThickness = getOutlineThickness();
    if (outlineThickness > 0) {
        Color outline = getOutlineColor();
        if (outline.a > 0) {
            float or_ = outline.r / 255.0f;
            float og = outline.g / 255.0f;
            float ob = outline.b / 255.0f;
            float oa = outline.a / 255.0f;

            // Build outline as quads (two triangles per edge)
            vertices.clear();
            colors.clear();

            for (size_t i = 0; i < pointCount; ++i) {
                size_t next = (i + 1) % pointCount;

                Vector2f p1 = combinedTransform.transformPoint(getPoint(i));
                Vector2f p2 = combinedTransform.transformPoint(getPoint(next));

                // Calculate normal direction
                Vector2f dir(p2.x - p1.x, p2.y - p1.y);
                float len = std::sqrt(dir.x * dir.x + dir.y * dir.y);
                if (len > 0) {
                    dir.x /= len;
                    dir.y /= len;
                }
                Vector2f normal(-dir.y * outlineThickness, dir.x * outlineThickness);

                // Outer points
                Vector2f p1o(p1.x + normal.x, p1.y + normal.y);
                Vector2f p2o(p2.x + normal.x, p2.y + normal.y);

                // Two triangles for quad
                // Triangle 1: p1, p2, p1o
                vertices.push_back(p1.x); vertices.push_back(p1.y);
                vertices.push_back(p2.x); vertices.push_back(p2.y);
                vertices.push_back(p1o.x); vertices.push_back(p1o.y);
                // Triangle 2: p2, p2o, p1o
                vertices.push_back(p2.x); vertices.push_back(p2.y);
                vertices.push_back(p2o.x); vertices.push_back(p2o.y);
                vertices.push_back(p1o.x); vertices.push_back(p1o.y);

                for (int v = 0; v < 6; ++v) {
                    colors.push_back(or_);
                    colors.push_back(og);
                    colors.push_back(ob);
                    colors.push_back(oa);
                }
            }

            if (!vertices.empty()) {
                SDL2Renderer::getInstance().drawTriangles(
                    vertices.data(), vertices.size() / 2,
                    colors.data(), nullptr, 0
                );
            }
        }
    }
}

void VertexArray::draw(RenderTarget& target, RenderStates states) const {
    if (vertices_.empty()) return;

    // Convert vertex array to flat arrays based on primitive type
    std::vector<float> positions;
    std::vector<float> colors;
    std::vector<float> texcoords;

    auto addVertex = [&](const Vertex& v) {
        Vector2f p = states.transform.transformPoint(v.position);
        positions.push_back(p.x);
        positions.push_back(p.y);
        colors.push_back(v.color.r / 255.0f);
        colors.push_back(v.color.g / 255.0f);
        colors.push_back(v.color.b / 255.0f);
        colors.push_back(v.color.a / 255.0f);
        texcoords.push_back(v.texCoords.x);
        texcoords.push_back(v.texCoords.y);
    };

    switch (primitiveType_) {
        case Triangles:
            // Already in triangle format
            for (size_t i = 0; i < vertices_.size(); ++i) {
                addVertex(vertices_[i]);
            }
            break;

        case TriangleFan:
            // Convert fan to triangles: v0, v1, v2, then v0, v2, v3, etc.
            if (vertices_.size() >= 3) {
                for (size_t i = 1; i < vertices_.size() - 1; ++i) {
                    addVertex(vertices_[0]);
                    addVertex(vertices_[i]);
                    addVertex(vertices_[i + 1]);
                }
            }
            break;

        case TriangleStrip:
            // Convert strip to triangles
            if (vertices_.size() >= 3) {
                for (size_t i = 0; i < vertices_.size() - 2; ++i) {
                    if (i % 2 == 0) {
                        addVertex(vertices_[i]);
                        addVertex(vertices_[i + 1]);
                        addVertex(vertices_[i + 2]);
                    } else {
                        // Flip winding for odd triangles
                        addVertex(vertices_[i + 1]);
                        addVertex(vertices_[i]);
                        addVertex(vertices_[i + 2]);
                    }
                }
            }
            break;

        case Quads:
            // Convert quads to triangles (4 vertices -> 2 triangles)
            for (size_t i = 0; i + 3 < vertices_.size(); i += 4) {
                // Triangle 1: v0, v1, v2
                addVertex(vertices_[i]);
                addVertex(vertices_[i + 1]);
                addVertex(vertices_[i + 2]);
                // Triangle 2: v0, v2, v3
                addVertex(vertices_[i]);
                addVertex(vertices_[i + 2]);
                addVertex(vertices_[i + 3]);
            }
            break;

        case Lines:
            // Draw lines as thin quads (2 triangles per line)
            for (size_t i = 0; i + 1 < vertices_.size(); i += 2) {
                Vector2f p1 = states.transform.transformPoint(vertices_[i].position);
                Vector2f p2 = states.transform.transformPoint(vertices_[i + 1].position);

                // Calculate perpendicular for line thickness (1 pixel)
                Vector2f dir(p2.x - p1.x, p2.y - p1.y);
                float len = std::sqrt(dir.x * dir.x + dir.y * dir.y);
                if (len > 0) {
                    dir.x /= len;
                    dir.y /= len;
                }
                Vector2f perp(-dir.y * 0.5f, dir.x * 0.5f);

                // Build thin quad
                Vector2f v0(p1.x - perp.x, p1.y - perp.y);
                Vector2f v1(p1.x + perp.x, p1.y + perp.y);
                Vector2f v2(p2.x + perp.x, p2.y + perp.y);
                Vector2f v3(p2.x - perp.x, p2.y - perp.y);

                const Vertex& vert1 = vertices_[i];
                const Vertex& vert2 = vertices_[i + 1];

                // Triangle 1
                positions.insert(positions.end(), {v0.x, v0.y, v1.x, v1.y, v2.x, v2.y});
                for (int j = 0; j < 2; ++j) {
                    colors.insert(colors.end(), {vert1.color.r/255.f, vert1.color.g/255.f, vert1.color.b/255.f, vert1.color.a/255.f});
                }
                colors.insert(colors.end(), {vert2.color.r/255.f, vert2.color.g/255.f, vert2.color.b/255.f, vert2.color.a/255.f});
                texcoords.insert(texcoords.end(), {0, 0, 0, 0, 0, 0});

                // Triangle 2
                positions.insert(positions.end(), {v0.x, v0.y, v2.x, v2.y, v3.x, v3.y});
                colors.insert(colors.end(), {vert1.color.r/255.f, vert1.color.g/255.f, vert1.color.b/255.f, vert1.color.a/255.f});
                colors.insert(colors.end(), {vert2.color.r/255.f, vert2.color.g/255.f, vert2.color.b/255.f, vert2.color.a/255.f});
                colors.insert(colors.end(), {vert2.color.r/255.f, vert2.color.g/255.f, vert2.color.b/255.f, vert2.color.a/255.f});
                texcoords.insert(texcoords.end(), {0, 0, 0, 0, 0, 0});
            }
            break;

        case LineStrip:
            // Similar to Lines but connected
            for (size_t i = 0; i + 1 < vertices_.size(); ++i) {
                Vector2f p1 = states.transform.transformPoint(vertices_[i].position);
                Vector2f p2 = states.transform.transformPoint(vertices_[i + 1].position);

                Vector2f dir(p2.x - p1.x, p2.y - p1.y);
                float len = std::sqrt(dir.x * dir.x + dir.y * dir.y);
                if (len > 0) {
                    dir.x /= len;
                    dir.y /= len;
                }
                Vector2f perp(-dir.y * 0.5f, dir.x * 0.5f);

                Vector2f v0(p1.x - perp.x, p1.y - perp.y);
                Vector2f v1(p1.x + perp.x, p1.y + perp.y);
                Vector2f v2(p2.x + perp.x, p2.y + perp.y);
                Vector2f v3(p2.x - perp.x, p2.y - perp.y);

                const Vertex& vert1 = vertices_[i];
                const Vertex& vert2 = vertices_[i + 1];

                positions.insert(positions.end(), {v0.x, v0.y, v1.x, v1.y, v2.x, v2.y});
                for (int j = 0; j < 2; ++j) {
                    colors.insert(colors.end(), {vert1.color.r/255.f, vert1.color.g/255.f, vert1.color.b/255.f, vert1.color.a/255.f});
                }
                colors.insert(colors.end(), {vert2.color.r/255.f, vert2.color.g/255.f, vert2.color.b/255.f, vert2.color.a/255.f});
                texcoords.insert(texcoords.end(), {0, 0, 0, 0, 0, 0});

                positions.insert(positions.end(), {v0.x, v0.y, v2.x, v2.y, v3.x, v3.y});
                colors.insert(colors.end(), {vert1.color.r/255.f, vert1.color.g/255.f, vert1.color.b/255.f, vert1.color.a/255.f});
                colors.insert(colors.end(), {vert2.color.r/255.f, vert2.color.g/255.f, vert2.color.b/255.f, vert2.color.a/255.f});
                colors.insert(colors.end(), {vert2.color.r/255.f, vert2.color.g/255.f, vert2.color.b/255.f, vert2.color.a/255.f});
                texcoords.insert(texcoords.end(), {0, 0, 0, 0, 0, 0});
            }
            break;

        case Points:
            // Draw points as small quads
            for (size_t i = 0; i < vertices_.size(); ++i) {
                Vector2f p = states.transform.transformPoint(vertices_[i].position);
                const Vertex& v = vertices_[i];

                // 2x2 pixel quad centered on point
                positions.insert(positions.end(), {
                    p.x - 1, p.y - 1,  p.x + 1, p.y - 1,  p.x + 1, p.y + 1,
                    p.x - 1, p.y - 1,  p.x + 1, p.y + 1,  p.x - 1, p.y + 1
                });
                for (int j = 0; j < 6; ++j) {
                    colors.insert(colors.end(), {v.color.r/255.f, v.color.g/255.f, v.color.b/255.f, v.color.a/255.f});
                }
                texcoords.insert(texcoords.end(), {0,0, 0,0, 0,0, 0,0, 0,0, 0,0});
            }
            break;
    }

    if (!positions.empty()) {
        // Use shape shader (no texture)
        glUseProgram(SDL2Renderer::getInstance().getShaderProgram(SDL2Renderer::ShaderType::Shape));
        SDL2Renderer::getInstance().drawTriangles(
            positions.data(), positions.size() / 2,
            colors.data(), nullptr, 0
        );
    }
}

void Sprite::draw(RenderTarget& target, RenderStates states) const {
    if (!texture_) return;

    Transform combined = states.transform * getTransform();

    // Get texture rectangle (use full texture if not set)
    IntRect rect = textureRect_;
    if (rect.width == 0 || rect.height == 0) {
        rect = IntRect(0, 0, texture_->getSize().x, texture_->getSize().y);
    }

    // Four corners of sprite in local space
    Vector2f p0 = combined.transformPoint(0, 0);
    Vector2f p1 = combined.transformPoint(static_cast<float>(rect.width), 0);
    Vector2f p2 = combined.transformPoint(static_cast<float>(rect.width), static_cast<float>(rect.height));
    Vector2f p3 = combined.transformPoint(0, static_cast<float>(rect.height));

    // Texture coordinates (normalized)
    Vector2u texSize = texture_->getSize();
    if (texSize.x == 0 || texSize.y == 0) return;

    float u0 = rect.left / static_cast<float>(texSize.x);
    float v0 = rect.top / static_cast<float>(texSize.y);
    float u1 = (rect.left + rect.width) / static_cast<float>(texSize.x);
    float v1 = (rect.top + rect.height) / static_cast<float>(texSize.y);

    // For RenderTexture (FBO) textures, flip V coordinates
    // OpenGL FBOs store content with Y=0 at bottom, but we sample assuming Y=0 at top
    if (texture_->isFlippedY()) {
        v0 = 1.0f - v0;
        v1 = 1.0f - v1;
    }

    // Two triangles forming a quad (6 vertices)
    float vertices[] = {
        p0.x, p0.y,  p1.x, p1.y,  p2.x, p2.y,  // Triangle 1
        p0.x, p0.y,  p2.x, p2.y,  p3.x, p3.y   // Triangle 2
    };

    float texcoords[] = {
        u0, v0,  u1, v0,  u1, v1,  // Triangle 1
        u0, v0,  u1, v1,  u0, v1   // Triangle 2
    };

    // Color tint for all 6 vertices
    float colors[24];
    float r = color_.r / 255.0f;
    float g = color_.g / 255.0f;
    float b = color_.b / 255.0f;
    float a = color_.a / 255.0f;
    for (int i = 0; i < 6; ++i) {
        colors[i * 4 + 0] = r;
        colors[i * 4 + 1] = g;
        colors[i * 4 + 2] = b;
        colors[i * 4 + 3] = a;
    }

    // Use sprite shader and draw
    SDL2Renderer::getInstance().drawTriangles(vertices, 6, colors, texcoords,
        texture_->getNativeHandle(), SDL2Renderer::ShaderType::Sprite);
}

// Static cache for font atlases - keyed by (font pointer, character size)
static std::map<std::pair<const Font*, unsigned int>, FontAtlas> s_fontAtlasCache;

void Text::draw(RenderTarget& target, RenderStates states) const {
    if (!font_ || string_.empty() || !font_->isLoaded()) return;

    // Get or create font atlas for this font + size combination
    auto key = std::make_pair(font_, characterSize_);
    auto it = s_fontAtlasCache.find(key);
    if (it == s_fontAtlasCache.end()) {
        FontAtlas atlas;
        // Use the new Font-based loader if FreeType is available, fall back to legacy
        if (font_->getFTFace()) {
            if (!atlas.load(font_, static_cast<float>(characterSize_))) {
                return;  // Failed to create atlas
            }
        } else {
            if (!atlas.load(font_->getData(), font_->getDataSize(), static_cast<float>(characterSize_))) {
                return;  // Failed to create atlas
            }
        }
        it = s_fontAtlasCache.emplace(key, std::move(atlas)).first;
    }
    FontAtlas& atlas = it->second;  // Non-const for on-demand glyph loading

    Transform combined = states.transform * getTransform();

    // Helper lambda to build glyph geometry with a given color and outline thickness
    auto buildGlyphs = [&](const Color& color, float outlineThickness,
                           std::vector<float>& verts, std::vector<float>& uvs, std::vector<float>& cols) {
        float x = 0;
        float y = atlas.getAscent();

        float r = color.r / 255.0f;
        float g = color.g / 255.0f;
        float b = color.b / 255.0f;
        float a = color.a / 255.0f;

        for (size_t i = 0; i < string_.size(); ++i) {
            char c = string_[i];

            if (c == '\n') {
                x = 0;
                y += atlas.getLineHeight();
                continue;
            }

            FontAtlas::GlyphInfo glyph;
            // Use stroked glyph lookup for outlines, regular for fill
            bool found = false;
            if (outlineThickness > 0) {
                found = atlas.getGlyph(static_cast<uint32_t>(c), outlineThickness, glyph);
            } else {
                found = atlas.getGlyph(static_cast<uint32_t>(c), glyph);
            }

            if (!found) {
                // Try space as fallback
                if (outlineThickness > 0) {
                    found = atlas.getGlyph(' ', outlineThickness, glyph);
                } else {
                    found = atlas.getGlyph(' ', glyph);
                }
                if (!found) continue;
            }

            if (glyph.width == 0 || glyph.height == 0) {
                // Invisible character (space), just advance
                x += glyph.xadvance;
                continue;
            }

            // Calculate quad corners
            // For stroked glyphs, the bitmap is larger and offset differently
            float x0 = x + glyph.xoff;
            float y0 = y + glyph.yoff;
            float x1 = x0 + glyph.width;
            float y1 = y0 + glyph.height;

            // Transform to world space
            Vector2f p0 = combined.transformPoint(x0, y0);
            Vector2f p1 = combined.transformPoint(x1, y0);
            Vector2f p2 = combined.transformPoint(x1, y1);
            Vector2f p3 = combined.transformPoint(x0, y1);

            verts.insert(verts.end(), {
                p0.x, p0.y,  p1.x, p1.y,  p2.x, p2.y,
                p0.x, p0.y,  p2.x, p2.y,  p3.x, p3.y
            });

            uvs.insert(uvs.end(), {
                glyph.u0, glyph.v0,  glyph.u1, glyph.v0,  glyph.u1, glyph.v1,
                glyph.u0, glyph.v0,  glyph.u1, glyph.v1,  glyph.u0, glyph.v1
            });

            for (int v = 0; v < 6; ++v) {
                cols.insert(cols.end(), {r, g, b, a});
            }

            x += glyph.xadvance;
        }
    };

    // Draw outline first using stroked glyphs (if any)
    if (outlineThickness_ > 0 && outlineColor_.a > 0) {
        std::vector<float> outlineVerts, outlineUVs, outlineCols;

        // Use FreeType stroker for proper vector-based outlines
        buildGlyphs(outlineColor_, outlineThickness_, outlineVerts, outlineUVs, outlineCols);

        if (!outlineVerts.empty()) {
            SDL2Renderer::getInstance().drawTriangles(
                outlineVerts.data(), outlineVerts.size() / 2,
                outlineCols.data(), outlineUVs.data(),
                atlas.getTextureId(),
                SDL2Renderer::ShaderType::Text
            );
        }
    }

    // Draw fill text on top using regular (non-stroked) glyphs
    std::vector<float> vertices, texcoords, colors;
    buildGlyphs(fillColor_, 0.0f, vertices, texcoords, colors);

    if (!vertices.empty()) {
        SDL2Renderer::getInstance().drawTriangles(
            vertices.data(), vertices.size() / 2,
            colors.data(), texcoords.data(),
            atlas.getTextureId(),
            SDL2Renderer::ShaderType::Text
        );
    }
}

FloatRect Text::getLocalBounds() const {
    if (!font_ || string_.empty() || !font_->isLoaded()) {
        return FloatRect(0, 0, 0, 0);
    }

    // Get or create font atlas for this font + size combination
    auto key = std::make_pair(font_, characterSize_);
    auto it = s_fontAtlasCache.find(key);
    if (it == s_fontAtlasCache.end()) {
        FontAtlas atlas;
        // Use the new Font-based loader if FreeType is available
        if (font_->getFTFace()) {
            if (!atlas.load(font_, static_cast<float>(characterSize_))) {
                return FloatRect(0, 0, 0, 0);
            }
        } else {
            if (!atlas.load(font_->getData(), font_->getDataSize(), static_cast<float>(characterSize_))) {
                return FloatRect(0, 0, 0, 0);
            }
        }
        it = s_fontAtlasCache.emplace(key, std::move(atlas)).first;
    }
    const FontAtlas& atlas = it->second;

    float x = 0;
    float maxX = 0;
    float minY = 0;
    float maxY = atlas.getLineHeight();
    int lineCount = 1;

    for (size_t i = 0; i < string_.size(); ++i) {
        char c = string_[i];

        if (c == '\n') {
            maxX = std::max(maxX, x);
            x = 0;
            lineCount++;
            continue;
        }

        FontAtlas::GlyphInfo glyph;
        if (atlas.getGlyph(static_cast<uint32_t>(c), glyph)) {
            x += glyph.xadvance;
        }
    }

    maxX = std::max(maxX, x);
    maxY = atlas.getLineHeight() * lineCount;

    return FloatRect(0, 0, maxX, maxY);
}

FloatRect Text::getGlobalBounds() const {
    FloatRect local = getLocalBounds();
    Transform t = getTransform();
    return t.transformRect(local);
}

// =============================================================================
// Shader Implementation
// =============================================================================

Shader::~Shader() {
    if (programId_) {
        SDL2Renderer::getInstance().deleteShaderProgram(programId_);
    }
}

bool Shader::loadFromFile(const std::string& filename, Type type) {
    // TODO: Load shader from file
    return false;
}

bool Shader::loadFromFile(const std::string& vertexFile, const std::string& fragmentFile) {
    // TODO: Load shaders from files
    return false;
}

bool Shader::loadFromMemory(const std::string& shader, Type type) {
    // For fragment-only shaders, use default vertex shader
    if (type == Fragment) {
        std::string defaultVertex = R"(
            attribute vec2 a_position;
            attribute vec4 a_color;
            attribute vec2 a_texcoord;
            uniform mat4 u_projection;
            varying vec4 v_color;
            varying vec2 v_texcoord;
            void main() {
                gl_Position = u_projection * vec4(a_position, 0.0, 1.0);
                v_color = a_color;
                v_texcoord = a_texcoord;
            }
        )";
        programId_ = SDL2Renderer::getInstance().compileShader(defaultVertex, shader);
        loaded_ = programId_ != 0;
        return loaded_;
    }
    return false;
}

void Shader::setUniform(const std::string& name, float x) {
    if (programId_) {
        glUseProgram(programId_);
        int loc = glGetUniformLocation(programId_, name.c_str());
        if (loc >= 0) glUniform1f(loc, x);
    }
}

void Shader::setUniform(const std::string& name, const Vector2f& v) {
    if (programId_) {
        glUseProgram(programId_);
        int loc = glGetUniformLocation(programId_, name.c_str());
        if (loc >= 0) glUniform2f(loc, v.x, v.y);
    }
}

void Shader::setUniform(const std::string& name, const Color& color) {
    if (programId_) {
        glUseProgram(programId_);
        int loc = glGetUniformLocation(programId_, name.c_str());
        if (loc >= 0) glUniform4f(loc, color.r/255.f, color.g/255.f, color.b/255.f, color.a/255.f);
    }
}

void Shader::setUniform(const std::string& name, const Texture& texture) {
    // Texture binding is handled during draw
}

void Shader::setUniform(const std::string& name, const Glsl::Vec3& v) {
    if (programId_) {
        glUseProgram(programId_);
        int loc = glGetUniformLocation(programId_, name.c_str());
        if (loc >= 0) glUniform3f(loc, v.x, v.y, v.z);
    }
}

void Shader::setUniform(const std::string& name, const Glsl::Vec4& v) {
    if (programId_) {
        glUseProgram(programId_);
        int loc = glGetUniformLocation(programId_, name.c_str());
        if (loc >= 0) glUniform4f(loc, v.x, v.y, v.z, v.w);
    }
}

void Shader::setUniform(const std::string& name, CurrentTextureType) {
    // Handled during draw
}

bool Shader::isAvailable() {
    return SDL2Renderer::getInstance().isInitialized();
}

// =============================================================================
// FontAtlas Implementation (FreeType-based)
// =============================================================================

FontAtlas::FontAtlas() = default;

FontAtlas::FontAtlas(FontAtlas&& other) noexcept
    : textureId_(other.textureId_)
    , fontSize_(other.fontSize_)
    , ascent_(other.ascent_)
    , descent_(other.descent_)
    , lineHeight_(other.lineHeight_)
    , font_(other.font_)
    , atlasPixels_(std::move(other.atlasPixels_))
    , atlasX_(other.atlasX_)
    , atlasY_(other.atlasY_)
    , atlasRowHeight_(other.atlasRowHeight_)
    , glyphCache_(std::move(other.glyphCache_))
    , simpleGlyphCache_(std::move(other.simpleGlyphCache_))
{
    // Clear source to prevent double-deletion
    other.textureId_ = 0;
    other.font_ = nullptr;
}

FontAtlas& FontAtlas::operator=(FontAtlas&& other) noexcept {
    if (this != &other) {
        // Clean up existing resources
        if (textureId_) {
            SDL2Renderer::getInstance().deleteTexture(textureId_);
        }

        // Transfer ownership
        textureId_ = other.textureId_;
        fontSize_ = other.fontSize_;
        ascent_ = other.ascent_;
        descent_ = other.descent_;
        lineHeight_ = other.lineHeight_;
        font_ = other.font_;
        atlasPixels_ = std::move(other.atlasPixels_);
        atlasX_ = other.atlasX_;
        atlasY_ = other.atlasY_;
        atlasRowHeight_ = other.atlasRowHeight_;
        glyphCache_ = std::move(other.glyphCache_);
        simpleGlyphCache_ = std::move(other.simpleGlyphCache_);

        // Clear source to prevent double-deletion
        other.textureId_ = 0;
        other.font_ = nullptr;
    }
    return *this;
}

FontAtlas::~FontAtlas() {
    if (textureId_) {
        SDL2Renderer::getInstance().deleteTexture(textureId_);
    }
}

uint64_t FontAtlas::makeKey(uint32_t codepoint, float outlineThickness) {
    // Quantize outline thickness to 0.5px increments for cache key
    uint32_t outlineKey = static_cast<uint32_t>(outlineThickness * 2.0f);
    return (static_cast<uint64_t>(outlineKey) << 32) | codepoint;
}

bool FontAtlas::load(const Font* font, float fontSize) {
    if (!font || !font->isLoaded() || !font->getFTFace()) {
        std::cerr << "FontAtlas: Invalid font or font not loaded" << std::endl;
        return false;
    }

    font_ = font;
    fontSize_ = fontSize;

    FT_Face face = static_cast<FT_Face>(font->getFTFace());

    // Set pixel size
    if (FT_Set_Pixel_Sizes(face, 0, static_cast<FT_UInt>(fontSize)) != 0) {
        std::cerr << "FontAtlas: Failed to set pixel size" << std::endl;
        return false;
    }

    // Get font metrics (in 26.6 fixed-point format)
    ascent_ = face->size->metrics.ascender / 64.0f;
    descent_ = face->size->metrics.descender / 64.0f;
    lineHeight_ = face->size->metrics.height / 64.0f;

    // Initialize atlas
    atlasPixels_.resize(ATLAS_SIZE * ATLAS_SIZE, 0);
    atlasX_ = 1;
    atlasY_ = 1;
    atlasRowHeight_ = 0;

    // Pre-load ASCII glyphs without outline (directly, not via loadGlyph to avoid texture updates)
    for (uint32_t c = 32; c < 128; ++c) {
        FT_UInt glyphIndex = FT_Get_Char_Index(face, c);
        if (glyphIndex == 0) continue;

        if (FT_Load_Glyph(face, glyphIndex, FT_LOAD_RENDER) != 0) continue;

        FT_Bitmap& bitmap = face->glyph->bitmap;
        int w = bitmap.width;
        int h = bitmap.rows;

        GlyphInfo info;
        if (w == 0 || h == 0) {
            info.u0 = info.v0 = info.u1 = info.v1 = 0;
            info.xoff = 0;
            info.yoff = 0;
            info.xadvance = face->glyph->advance.x / 64.0f;
            info.width = 0;
            info.height = 0;
        } else {
            if (atlasX_ + w + 1 >= ATLAS_SIZE) {
                atlasX_ = 1;
                atlasY_ += atlasRowHeight_ + 1;
                atlasRowHeight_ = 0;
            }
            if (atlasY_ + h + 1 >= ATLAS_SIZE) break;

            for (int y = 0; y < h; ++y) {
                for (int x = 0; x < w; ++x) {
                    atlasPixels_[(atlasY_ + y) * ATLAS_SIZE + atlasX_ + x] = bitmap.buffer[y * bitmap.pitch + x];
                }
            }

            info.u0 = atlasX_ / (float)ATLAS_SIZE;
            info.v0 = atlasY_ / (float)ATLAS_SIZE;
            info.u1 = (atlasX_ + w) / (float)ATLAS_SIZE;
            info.v1 = (atlasY_ + h) / (float)ATLAS_SIZE;
            info.xoff = face->glyph->bitmap_left;
            info.yoff = -face->glyph->bitmap_top;
            info.xadvance = face->glyph->advance.x / 64.0f;
            info.width = w;
            info.height = h;

            atlasX_ += w + 1;
            atlasRowHeight_ = std::max(atlasRowHeight_, h);
        }

        simpleGlyphCache_[c] = info;
        glyphCache_[makeKey(c, 0.0f)] = info;
    }

    // Convert single-channel to RGBA and create texture ONCE
    std::vector<unsigned char> rgbaPixels(ATLAS_SIZE * ATLAS_SIZE * 4);
    for (int i = 0; i < ATLAS_SIZE * ATLAS_SIZE; ++i) {
        rgbaPixels[i * 4 + 0] = 255;
        rgbaPixels[i * 4 + 1] = 255;
        rgbaPixels[i * 4 + 2] = 255;
        rgbaPixels[i * 4 + 3] = atlasPixels_[i];
    }

    textureId_ = SDL2Renderer::getInstance().createTexture(ATLAS_SIZE, ATLAS_SIZE, rgbaPixels.data());
    return true;
}

// Legacy interface using raw font data - creates temporary FreeType objects
// Note: This path doesn't support on-demand stroked glyph loading since FreeType
// objects are freed after initialization. Use Font-based load() for full features.
bool FontAtlas::load(const unsigned char* fontData, size_t dataSize, float fontSize) {
    fontSize_ = fontSize;

    // Initialize FreeType for this atlas
    FT_Library library;
    if (FT_Init_FreeType(&library) != 0) {
        std::cerr << "FontAtlas: Failed to initialize FreeType" << std::endl;
        return false;
    }

    FT_Face face;
    if (FT_New_Memory_Face(library, fontData, dataSize, 0, &face) != 0) {
        std::cerr << "FontAtlas: Failed to create FreeType face" << std::endl;
        FT_Done_FreeType(library);
        return false;
    }

    // Set pixel size
    FT_Set_Pixel_Sizes(face, 0, static_cast<FT_UInt>(fontSize));

    // Get font metrics
    ascent_ = face->size->metrics.ascender / 64.0f;
    descent_ = face->size->metrics.descender / 64.0f;
    lineHeight_ = face->size->metrics.height / 64.0f;

    // Create glyph atlas - pre-load all ASCII glyphs
    atlasPixels_.resize(ATLAS_SIZE * ATLAS_SIZE, 0);
    atlasX_ = 1;
    atlasY_ = 1;
    atlasRowHeight_ = 0;

    for (uint32_t c = 32; c < 128; ++c) {
        FT_UInt glyphIndex = FT_Get_Char_Index(face, c);
        if (glyphIndex == 0) continue;

        if (FT_Load_Glyph(face, glyphIndex, FT_LOAD_RENDER) != 0) continue;

        FT_Bitmap& bitmap = face->glyph->bitmap;
        int w = bitmap.width;
        int h = bitmap.rows;

        GlyphInfo glyph;
        if (w == 0 || h == 0) {
            glyph.u0 = glyph.v0 = glyph.u1 = glyph.v1 = 0;
            glyph.xoff = 0;
            glyph.yoff = 0;
            glyph.xadvance = face->glyph->advance.x / 64.0f;
            glyph.width = 0;
            glyph.height = 0;
        } else {
            if (atlasX_ + w + 1 >= ATLAS_SIZE) {
                atlasX_ = 1;
                atlasY_ += atlasRowHeight_ + 1;
                atlasRowHeight_ = 0;
            }
            if (atlasY_ + h + 1 >= ATLAS_SIZE) break;

            for (int y = 0; y < h; ++y) {
                for (int x = 0; x < w; ++x) {
                    atlasPixels_[(atlasY_ + y) * ATLAS_SIZE + atlasX_ + x] = bitmap.buffer[y * bitmap.pitch + x];
                }
            }

            glyph.u0 = atlasX_ / (float)ATLAS_SIZE;
            glyph.v0 = atlasY_ / (float)ATLAS_SIZE;
            glyph.u1 = (atlasX_ + w) / (float)ATLAS_SIZE;
            glyph.v1 = (atlasY_ + h) / (float)ATLAS_SIZE;
            glyph.xoff = face->glyph->bitmap_left;
            glyph.yoff = -face->glyph->bitmap_top;
            glyph.xadvance = face->glyph->advance.x / 64.0f;
            glyph.width = w;
            glyph.height = h;

            atlasX_ += w + 1;
            atlasRowHeight_ = std::max(atlasRowHeight_, h);
        }

        simpleGlyphCache_[c] = glyph;
        glyphCache_[makeKey(c, 0.0f)] = glyph;
    }

    // Clean up temporary FreeType objects
    FT_Done_Face(face);
    FT_Done_FreeType(library);

    // Convert to RGBA and create texture ONCE
    std::vector<unsigned char> rgbaPixels(ATLAS_SIZE * ATLAS_SIZE * 4);
    for (int i = 0; i < ATLAS_SIZE * ATLAS_SIZE; ++i) {
        rgbaPixels[i * 4 + 0] = 255;
        rgbaPixels[i * 4 + 1] = 255;
        rgbaPixels[i * 4 + 2] = 255;
        rgbaPixels[i * 4 + 3] = atlasPixels_[i];
    }

    textureId_ = SDL2Renderer::getInstance().createTexture(ATLAS_SIZE, ATLAS_SIZE, rgbaPixels.data());
    return true;
}

bool FontAtlas::loadGlyph(uint32_t codepoint, float outlineThickness) {
    if (!font_ || !font_->getFTFace()) return false;

    FT_Face face = static_cast<FT_Face>(font_->getFTFace());

    // Make sure pixel size is set
    FT_Set_Pixel_Sizes(face, 0, static_cast<FT_UInt>(fontSize_));

    FT_UInt glyphIndex = FT_Get_Char_Index(face, codepoint);
    if (glyphIndex == 0) return false;

    // Load glyph without rendering (we may need to stroke it first)
    if (FT_Load_Glyph(face, glyphIndex, FT_LOAD_DEFAULT) != 0) return false;

    FT_Glyph glyph;
    if (FT_Get_Glyph(face->glyph, &glyph) != 0) return false;

    // Apply stroking if outline thickness > 0
    if (outlineThickness > 0.0f && glyph->format == FT_GLYPH_FORMAT_OUTLINE) {
        FT_Stroker stroker = static_cast<FT_Stroker>(font_->getFTStroker());
        if (stroker) {
            // Set stroker parameters (thickness is in 26.6 fixed-point)
            FT_Stroker_Set(stroker,
                           static_cast<FT_Fixed>(outlineThickness * 64.0f),
                           FT_STROKER_LINECAP_ROUND,
                           FT_STROKER_LINEJOIN_ROUND,
                           0);

            // Stroke the glyph outline (replaces outline with stroked version)
            FT_Glyph_Stroke(&glyph, stroker, 1);
        }
    }

    // Convert to bitmap
    if (FT_Glyph_To_Bitmap(&glyph, FT_RENDER_MODE_NORMAL, nullptr, 1) != 0) {
        FT_Done_Glyph(glyph);
        return false;
    }

    FT_BitmapGlyph bitmapGlyph = reinterpret_cast<FT_BitmapGlyph>(glyph);
    FT_Bitmap& bitmap = bitmapGlyph->bitmap;

    int w = bitmap.width;
    int h = bitmap.rows;

    GlyphInfo info;

    if (w == 0 || h == 0) {
        // Space or invisible character
        info.u0 = info.v0 = info.u1 = info.v1 = 0;
        info.xoff = 0;
        info.yoff = 0;
        info.xadvance = face->glyph->advance.x / 64.0f;
        info.width = 0;
        info.height = 0;
    } else {
        // Check if we need to move to next row
        if (atlasX_ + w + 1 >= ATLAS_SIZE) {
            atlasX_ = 1;
            atlasY_ += atlasRowHeight_ + 1;
            atlasRowHeight_ = 0;
        }

        if (atlasY_ + h + 1 >= ATLAS_SIZE) {
            std::cerr << "FontAtlas: Atlas full" << std::endl;
            FT_Done_Glyph(glyph);
            return false;
        }

        // Copy bitmap to atlas pixel buffer
        for (int y = 0; y < h; ++y) {
            for (int x = 0; x < w; ++x) {
                atlasPixels_[(atlasY_ + y) * ATLAS_SIZE + atlasX_ + x] = bitmap.buffer[y * bitmap.pitch + x];
            }
        }

        info.u0 = atlasX_ / (float)ATLAS_SIZE;
        info.v0 = atlasY_ / (float)ATLAS_SIZE;
        info.u1 = (atlasX_ + w) / (float)ATLAS_SIZE;
        info.v1 = (atlasY_ + h) / (float)ATLAS_SIZE;
        info.xoff = bitmapGlyph->left;
        info.yoff = -bitmapGlyph->top;  // FreeType uses bottom-up
        info.xadvance = face->glyph->advance.x / 64.0f;
        info.width = w;
        info.height = h;

        // Update ONLY the region of the texture that changed (not the whole atlas!)
        if (textureId_) {
            // Convert just this glyph region to RGBA
            std::vector<unsigned char> glyphRGBA(w * h * 4);
            for (int y = 0; y < h; ++y) {
                for (int x = 0; x < w; ++x) {
                    int srcIdx = (atlasY_ + y) * ATLAS_SIZE + atlasX_ + x;
                    int dstIdx = (y * w + x) * 4;
                    glyphRGBA[dstIdx + 0] = 255;
                    glyphRGBA[dstIdx + 1] = 255;
                    glyphRGBA[dstIdx + 2] = 255;
                    glyphRGBA[dstIdx + 3] = atlasPixels_[srcIdx];
                }
            }
            // Use glTexSubImage2D to update just the glyph region
            SDL2Renderer::getInstance().updateTexture(textureId_, atlasX_, atlasY_, w, h, glyphRGBA.data());
        }

        atlasX_ += w + 1;
        atlasRowHeight_ = std::max(atlasRowHeight_, h);
    }

    // Store in appropriate cache
    if (outlineThickness == 0.0f) {
        simpleGlyphCache_[codepoint] = info;
    }
    uint64_t key = makeKey(codepoint, outlineThickness);
    glyphCache_[key] = info;

    FT_Done_Glyph(glyph);
    return true;
}

bool FontAtlas::getGlyph(uint32_t codepoint, float outlineThickness, GlyphInfo& info) {
    uint64_t key = makeKey(codepoint, outlineThickness);

    auto it = glyphCache_.find(key);
    if (it != glyphCache_.end()) {
        info = it->second;
        return true;
    }

    // Try to load the glyph on-demand
    if (loadGlyph(codepoint, outlineThickness)) {
        it = glyphCache_.find(key);
        if (it != glyphCache_.end()) {
            info = it->second;
            return true;
        }
    }

    return false;
}

bool FontAtlas::getGlyph(uint32_t codepoint, GlyphInfo& info) const {
    auto it = simpleGlyphCache_.find(codepoint);
    if (it != simpleGlyphCache_.end()) {
        info = it->second;
        return true;
    }
    return false;
}

} // namespace sf

#endif // MCRF_SDL2
