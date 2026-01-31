// SDL2Renderer.cpp - OpenGL ES 2 rendering implementation for SDL2 backend
// Implements the SDL2 types defined in SDL2Types.h using SDL2 and OpenGL ES 2

#ifdef MCRF_SDL2

#include "SDL2Renderer.h"
#include "SDL2Types.h"

#include <iostream>
#include <cstring>
#include <cmath>

// SDL2 and OpenGL ES 2 headers
#ifdef __EMSCRIPTEN__
#include <emscripten.h>
#include <emscripten/html5.h>
// Emscripten's USE_SDL=2 port puts headers directly in include path
#include <SDL.h>
#include <GLES2/gl2.h>
#else
#include <SDL2/SDL.h>
#include <SDL2/SDL_opengl.h>
// Desktop OpenGL - we'll use GL 2.1 compatible subset that matches GLES2
#define GL_GLEXT_PROTOTYPES
#include <GL/gl.h>
#endif

// stb libraries for image/font loading (from deps/stb/)
#define STB_IMAGE_IMPLEMENTATION
#include <stb_image.h>

#define STB_TRUETYPE_IMPLEMENTATION
#include <stb_truetype.h>

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

// Text shader is same as sprite for now
static const char* TEXT_VERTEX_SHADER = SPRITE_VERTEX_SHADER;
static const char* TEXT_FRAGMENT_SHADER = R"(
#ifdef GL_ES
precision mediump float;
#endif
varying vec4 v_color;
varying vec2 v_texcoord;
uniform sampler2D u_texture;

void main() {
    // Text rendering: use texture alpha as coverage
    float alpha = texture2D(u_texture, v_texcoord).a;
    gl_FragColor = vec4(v_color.rgb, v_color.a * alpha);
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
    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_EVENTS) < 0) {
        std::cerr << "SDL2Renderer: Failed to initialize SDL: " << SDL_GetError() << std::endl;
        return false;
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

void SDL2Renderer::drawTriangles(const float* vertices, size_t vertexCount,
                                  const float* colors, const float* texCoords,
                                  unsigned int textureId) {
    if (vertexCount == 0) return;

    unsigned int program = textureId ? spriteProgram_ : shapeProgram_;
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
    // For Emscripten, we need to set the canvas size explicitly
    // The canvas element with id="canvas" is used by default
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

    // Initial clear to a visible color to confirm GL is working
    glClearColor(0.2f, 0.3f, 0.4f, 1.0f);  // Blue-gray
    glClear(GL_COLOR_BUFFER_BIT);
    SDL_GL_SwapWindow(window);

    std::cout << "RenderWindow: Created " << mode.width << "x" << mode.height << " window" << std::endl;
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

    view_ = View(FloatRect(0, 0, static_cast<float>(width), static_cast<float>(height)));
    defaultView_ = view_;

    return true;
}

void RenderTexture::clear(const Color& color) {
    SDL2Renderer::getInstance().bindFBO(fboId_);
    RenderTarget::clear(color);
}

void RenderTexture::display() {
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
// Font Implementation
// =============================================================================

bool Font::loadFromFile(const std::string& filename) {
    FILE* file = fopen(filename.c_str(), "rb");
    if (!file) {
        return false;
    }

    fseek(file, 0, SEEK_END);
    size_t size = ftell(file);
    fseek(file, 0, SEEK_SET);

    fontData_.resize(size);
    fread(fontData_.data(), 1, size, file);
    fclose(file);

    loaded_ = true;
    return true;
}

bool Font::loadFromMemory(const void* data, size_t sizeInBytes) {
    fontData_.resize(sizeInBytes);
    memcpy(fontData_.data(), data, sizeInBytes);
    loaded_ = true;
    return true;
}

// =============================================================================
// Shape Drawing (Stubs - implement with vertex generation)
// =============================================================================

void Shape::draw(RenderTarget& target, RenderStates states) const {
    // TODO: Generate vertices and draw using SDL2Renderer
}

void VertexArray::draw(RenderTarget& target, RenderStates states) const {
    // TODO: Draw using SDL2Renderer
}

void Sprite::draw(RenderTarget& target, RenderStates states) const {
    // TODO: Draw textured quad
}

void Text::draw(RenderTarget& target, RenderStates states) const {
    // TODO: Draw text using font atlas
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
// FontAtlas Implementation
// =============================================================================

FontAtlas::FontAtlas() = default;

FontAtlas::~FontAtlas() {
    if (textureId_) {
        SDL2Renderer::getInstance().deleteTexture(textureId_);
    }
    if (stbFontInfo_) {
        delete static_cast<stbtt_fontinfo*>(stbFontInfo_);
    }
}

bool FontAtlas::load(const unsigned char* fontData, size_t dataSize, float fontSize) {
    fontSize_ = fontSize;

    stbtt_fontinfo* info = new stbtt_fontinfo();
    if (!stbtt_InitFont(info, fontData, 0)) {
        delete info;
        return false;
    }

    stbFontInfo_ = info;

    // Get font metrics
    int ascent, descent, lineGap;
    stbtt_GetFontVMetrics(info, &ascent, &descent, &lineGap);

    float scale = stbtt_ScaleForPixelHeight(info, fontSize);
    ascent_ = ascent * scale;
    descent_ = descent * scale;
    lineHeight_ = (ascent - descent + lineGap) * scale;

    // Create glyph atlas (simple ASCII for now)
    const int atlasSize = 512;
    std::vector<unsigned char> atlasPixels(atlasSize * atlasSize, 0);

    int x = 1, y = 1;
    int rowHeight = 0;

    for (uint32_t c = 32; c < 128; ++c) {
        int advance, lsb;
        stbtt_GetCodepointHMetrics(info, c, &advance, &lsb);

        int x0, y0, x1, y1;
        stbtt_GetCodepointBitmapBox(info, c, scale, scale, &x0, &y0, &x1, &y1);

        int w = x1 - x0;
        int h = y1 - y0;

        if (x + w + 1 >= atlasSize) {
            x = 1;
            y += rowHeight + 1;
            rowHeight = 0;
        }

        if (y + h + 1 >= atlasSize) {
            break;  // Atlas full
        }

        // Render glyph to atlas
        stbtt_MakeCodepointBitmap(info, &atlasPixels[y * atlasSize + x], w, h, atlasSize, scale, scale, c);

        GlyphInfo glyph;
        glyph.u0 = x / (float)atlasSize;
        glyph.v0 = y / (float)atlasSize;
        glyph.u1 = (x + w) / (float)atlasSize;
        glyph.v1 = (y + h) / (float)atlasSize;
        glyph.xoff = x0;
        glyph.yoff = y0;
        glyph.xadvance = advance * scale;
        glyph.width = w;
        glyph.height = h;

        glyphCache_[c] = glyph;

        x += w + 1;
        rowHeight = std::max(rowHeight, h);
    }

    // Convert single-channel to RGBA
    std::vector<unsigned char> rgbaPixels(atlasSize * atlasSize * 4);
    for (int i = 0; i < atlasSize * atlasSize; ++i) {
        rgbaPixels[i * 4 + 0] = 255;
        rgbaPixels[i * 4 + 1] = 255;
        rgbaPixels[i * 4 + 2] = 255;
        rgbaPixels[i * 4 + 3] = atlasPixels[i];
    }

    textureId_ = SDL2Renderer::getInstance().createTexture(atlasSize, atlasSize, rgbaPixels.data());

    return true;
}

bool FontAtlas::getGlyph(uint32_t codepoint, GlyphInfo& info) const {
    auto it = glyphCache_.find(codepoint);
    if (it != glyphCache_.end()) {
        info = it->second;
        return true;
    }
    return false;
}

} // namespace sf

#endif // MCRF_SDL2
