// GLContext_SDL2.cpp - SDL2 backend for OpenGL context abstraction
// Leverages existing SDL2Renderer infrastructure

#ifdef MCRF_SDL2

#include "GLContext.h"
#include "SDL2Renderer.h"

#ifdef __EMSCRIPTEN__
#include <GLES2/gl2.h>
#else
#include <GL/gl.h>
#include <GL/glext.h>
#endif

#include <vector>

namespace mcrf {
namespace gl {

// =============================================================================
// State tracking structures (same as SFML version)
// =============================================================================

struct GLState {
    GLboolean depthTest;
    GLboolean depthWrite;
    GLenum depthFunc;
    GLboolean cullFace;
    GLenum cullMode;
    GLboolean blend;
    GLenum blendSrc;
    GLenum blendDst;
    GLint viewport[4];
    GLint boundFBO;
    GLint boundProgram;
    GLint boundTexture;
};

static std::vector<GLState> stateStack;

// =============================================================================
// Initialization
// =============================================================================

bool initGL() {
    // SDL2Renderer handles GL initialization
    auto& renderer = sf::SDL2Renderer::getInstance();
    return renderer.isGLInitialized();
}

bool isGLReady() {
    auto& renderer = sf::SDL2Renderer::getInstance();
    return renderer.isGLInitialized();
}

// =============================================================================
// FBO Management
// =============================================================================

unsigned int createFramebuffer(int width, int height, unsigned int* colorTex, unsigned int* depthRB) {
    GLuint fbo, tex, depth = 0;

    // Create FBO
    glGenFramebuffers(1, &fbo);
    glBindFramebuffer(GL_FRAMEBUFFER, fbo);

    // Create color texture
    glGenTextures(1, &tex);
    glBindTexture(GL_TEXTURE_2D, tex);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, nullptr);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tex, 0);

    // Create depth renderbuffer if requested
    // Note: GLES2 uses GL_DEPTH_COMPONENT16 instead of GL_DEPTH_COMPONENT24
    if (depthRB) {
        glGenRenderbuffers(1, &depth);
        glBindRenderbuffer(GL_RENDERBUFFER, depth);
#ifdef __EMSCRIPTEN__
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT16, width, height);
#else
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, width, height);
#endif
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, depth);
        *depthRB = depth;
    }

    // Check completeness
    if (glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE) {
        glBindFramebuffer(GL_FRAMEBUFFER, 0);
        if (depth) glDeleteRenderbuffers(1, &depth);
        glDeleteTextures(1, &tex);
        glDeleteFramebuffers(1, &fbo);
        return 0;
    }

    glBindFramebuffer(GL_FRAMEBUFFER, 0);
    *colorTex = tex;
    return fbo;
}

void bindFramebuffer(unsigned int fbo) {
    glBindFramebuffer(GL_FRAMEBUFFER, fbo);
}

void bindDefaultFramebuffer() {
    glBindFramebuffer(GL_FRAMEBUFFER, 0);
}

void deleteFramebuffer(unsigned int fbo, unsigned int colorTex, unsigned int depthRB) {
    if (depthRB) {
        GLuint rb = depthRB;
        glDeleteRenderbuffers(1, &rb);
    }
    if (colorTex) {
        GLuint tex = colorTex;
        glDeleteTextures(1, &tex);
    }
    if (fbo) {
        GLuint f = fbo;
        glDeleteFramebuffers(1, &f);
    }
}

// =============================================================================
// Shader Compilation
// =============================================================================

unsigned int compileShader(unsigned int type, const char* source) {
    GLuint shader = glCreateShader(type);
    glShaderSource(shader, 1, &source, nullptr);
    glCompileShader(shader);

    GLint success;
    glGetShaderiv(shader, GL_COMPILE_STATUS, &success);
    if (!success) {
        GLchar infoLog[512];
        glGetShaderInfoLog(shader, 512, nullptr, infoLog);
        // TODO: Log error
        glDeleteShader(shader);
        return 0;
    }

    return shader;
}

unsigned int linkProgram(unsigned int vertShader, unsigned int fragShader) {
    GLuint program = glCreateProgram();
    glAttachShader(program, vertShader);
    glAttachShader(program, fragShader);
    glLinkProgram(program);

    GLint success;
    glGetProgramiv(program, GL_LINK_STATUS, &success);
    if (!success) {
        GLchar infoLog[512];
        glGetProgramInfoLog(program, 512, nullptr, infoLog);
        // TODO: Log error
        glDeleteProgram(program);
        return 0;
    }

    return program;
}

void deleteProgram(unsigned int program) {
    glDeleteProgram(program);
}

// =============================================================================
// State Management
// =============================================================================

void pushState() {
    GLState state;

    state.depthTest = glIsEnabled(GL_DEPTH_TEST);
    glGetBooleanv(GL_DEPTH_WRITEMASK, &state.depthWrite);
    glGetIntegerv(GL_DEPTH_FUNC, (GLint*)&state.depthFunc);

    state.cullFace = glIsEnabled(GL_CULL_FACE);
    glGetIntegerv(GL_CULL_FACE_MODE, (GLint*)&state.cullMode);

    state.blend = glIsEnabled(GL_BLEND);
    glGetIntegerv(GL_BLEND_SRC_ALPHA, (GLint*)&state.blendSrc);
    glGetIntegerv(GL_BLEND_DST_ALPHA, (GLint*)&state.blendDst);

    glGetIntegerv(GL_VIEWPORT, state.viewport);
    glGetIntegerv(GL_FRAMEBUFFER_BINDING, &state.boundFBO);
    glGetIntegerv(GL_CURRENT_PROGRAM, &state.boundProgram);
    glGetIntegerv(GL_TEXTURE_BINDING_2D, &state.boundTexture);

    stateStack.push_back(state);
}

void popState() {
    if (stateStack.empty()) return;

    GLState& state = stateStack.back();

    if (state.depthTest) glEnable(GL_DEPTH_TEST);
    else glDisable(GL_DEPTH_TEST);
    glDepthMask(state.depthWrite);
    glDepthFunc(state.depthFunc);

    if (state.cullFace) glEnable(GL_CULL_FACE);
    else glDisable(GL_CULL_FACE);
    glCullFace(state.cullMode);

    if (state.blend) glEnable(GL_BLEND);
    else glDisable(GL_BLEND);
    glBlendFunc(state.blendSrc, state.blendDst);

    glViewport(state.viewport[0], state.viewport[1], state.viewport[2], state.viewport[3]);
    glBindFramebuffer(GL_FRAMEBUFFER, state.boundFBO);
    glUseProgram(state.boundProgram);
    glBindTexture(GL_TEXTURE_2D, state.boundTexture);

    stateStack.pop_back();
}

// =============================================================================
// 3D State Setup
// =============================================================================

void setup3DState() {
    glEnable(GL_DEPTH_TEST);
    glDepthMask(GL_TRUE);
    glDepthFunc(GL_LESS);
    glEnable(GL_CULL_FACE);
    glCullFace(GL_BACK);
}

void restore2DState() {
    glDisable(GL_DEPTH_TEST);
    glDisable(GL_CULL_FACE);
}

// =============================================================================
// Depth Operations
// =============================================================================

void setDepthTest(bool enable) {
    if (enable) glEnable(GL_DEPTH_TEST);
    else glDisable(GL_DEPTH_TEST);
}

void setDepthWrite(bool enable) {
    glDepthMask(enable ? GL_TRUE : GL_FALSE);
}

void setDepthFunc(unsigned int func) {
    glDepthFunc(func);
}

void clearDepth() {
    glClear(GL_DEPTH_BUFFER_BIT);
}

// =============================================================================
// Culling
// =============================================================================

void setCulling(bool enable) {
    if (enable) glEnable(GL_CULL_FACE);
    else glDisable(GL_CULL_FACE);
}

void setCullFace(unsigned int face) {
    glCullFace(face);
}

// =============================================================================
// Error Handling
// =============================================================================

const char* getErrorString() {
    GLenum err = glGetError();
    switch (err) {
        case GL_NO_ERROR: return nullptr;
        case GL_INVALID_ENUM: return "GL_INVALID_ENUM";
        case GL_INVALID_VALUE: return "GL_INVALID_VALUE";
        case GL_INVALID_OPERATION: return "GL_INVALID_OPERATION";
        case GL_OUT_OF_MEMORY: return "GL_OUT_OF_MEMORY";
        default: return "Unknown GL error";
    }
}

bool checkError(const char* operation) {
    const char* err = getErrorString();
    if (err) {
        // TODO: Log error with operation name
        return false;
    }
    return true;
}

} // namespace gl
} // namespace mcrf

#endif // MCRF_SDL2
