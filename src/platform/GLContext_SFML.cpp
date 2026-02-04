// GLContext_SFML.cpp - SFML backend for OpenGL context abstraction
// Uses GLAD for GL function loading

#ifndef MCRF_SDL2
#ifndef MCRF_HEADLESS

#include "GLContext.h"
#include <glad/glad.h>
#include <SFML/OpenGL.hpp>
#include <vector>
#include <cstdio>

namespace mcrf {
namespace gl {

// =============================================================================
// State tracking
// =============================================================================

static bool s_gladInitialized = false;

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
    if (s_gladInitialized) {
        return true;
    }

    // Load GL function pointers via GLAD
    // Note: SFML must have created an OpenGL context before this is called
    if (!gladLoadGL()) {
        fprintf(stderr, "GLContext_SFML: Failed to initialize GLAD\n");
        return false;
    }

    s_gladInitialized = true;
    printf("GLContext_SFML: GLAD initialized - OpenGL %d.%d\n", GLVersion.major, GLVersion.minor);
    return true;
}

bool isGLReady() {
    return s_gladInitialized;
}

// =============================================================================
// FBO Management
// =============================================================================

unsigned int createFramebuffer(int width, int height, unsigned int* colorTex, unsigned int* depthRB) {
    if (!s_gladInitialized) return 0;

    GLuint fbo, tex, depth = 0;

    // Create FBO
    glGenFramebuffers(1, &fbo);
    glBindFramebuffer(GL_FRAMEBUFFER, fbo);

    // Create color texture
    glGenTextures(1, &tex);
    glBindTexture(GL_TEXTURE_2D, tex);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, nullptr);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tex, 0);

    // Create depth renderbuffer if requested
    if (depthRB) {
        glGenRenderbuffers(1, &depth);
        glBindRenderbuffer(GL_RENDERBUFFER, depth);
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, width, height);
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, depth);
        *depthRB = depth;
    }

    // Check completeness
    GLenum status = glCheckFramebufferStatus(GL_FRAMEBUFFER);
    if (status != GL_FRAMEBUFFER_COMPLETE) {
        fprintf(stderr, "GLContext_SFML: Framebuffer incomplete: 0x%x\n", status);
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
    if (s_gladInitialized) {
        glBindFramebuffer(GL_FRAMEBUFFER, fbo);
    }
}

void bindDefaultFramebuffer() {
    if (s_gladInitialized) {
        glBindFramebuffer(GL_FRAMEBUFFER, 0);
    }
}

void deleteFramebuffer(unsigned int fbo, unsigned int colorTex, unsigned int depthRB) {
    if (!s_gladInitialized) return;

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
    if (!s_gladInitialized) return 0;

    GLuint shader = glCreateShader(type);
    glShaderSource(shader, 1, &source, nullptr);
    glCompileShader(shader);

    GLint success;
    glGetShaderiv(shader, GL_COMPILE_STATUS, &success);
    if (!success) {
        GLchar infoLog[512];
        glGetShaderInfoLog(shader, 512, nullptr, infoLog);
        fprintf(stderr, "GLContext_SFML: Shader compilation failed:\n%s\n", infoLog);
        glDeleteShader(shader);
        return 0;
    }

    return shader;
}

unsigned int linkProgram(unsigned int vertShader, unsigned int fragShader) {
    if (!s_gladInitialized) return 0;

    GLuint program = glCreateProgram();
    glAttachShader(program, vertShader);
    glAttachShader(program, fragShader);
    glLinkProgram(program);

    GLint success;
    glGetProgramiv(program, GL_LINK_STATUS, &success);
    if (!success) {
        GLchar infoLog[512];
        glGetProgramInfoLog(program, 512, nullptr, infoLog);
        fprintf(stderr, "GLContext_SFML: Program linking failed:\n%s\n", infoLog);
        glDeleteProgram(program);
        return 0;
    }

    return program;
}

void deleteProgram(unsigned int program) {
    if (s_gladInitialized && program) {
        glDeleteProgram(program);
    }
}

// =============================================================================
// State Management
// =============================================================================

void pushState() {
    if (!s_gladInitialized) return;

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
    if (!s_gladInitialized || stateStack.empty()) return;

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
    if (!s_gladInitialized) return;

    glEnable(GL_DEPTH_TEST);
    glDepthMask(GL_TRUE);
    glDepthFunc(GL_LESS);
    glEnable(GL_CULL_FACE);
    glCullFace(GL_BACK);
}

void restore2DState() {
    if (!s_gladInitialized) return;

    glDisable(GL_DEPTH_TEST);
    glDisable(GL_CULL_FACE);
}

// =============================================================================
// Depth Operations
// =============================================================================

void setDepthTest(bool enable) {
    if (!s_gladInitialized) return;
    if (enable) glEnable(GL_DEPTH_TEST);
    else glDisable(GL_DEPTH_TEST);
}

void setDepthWrite(bool enable) {
    if (!s_gladInitialized) return;
    glDepthMask(enable ? GL_TRUE : GL_FALSE);
}

void setDepthFunc(unsigned int func) {
    if (!s_gladInitialized) return;
    glDepthFunc(func);
}

void clearDepth() {
    if (!s_gladInitialized) return;
    glClear(GL_DEPTH_BUFFER_BIT);
}

// =============================================================================
// Culling
// =============================================================================

void setCulling(bool enable) {
    if (!s_gladInitialized) return;
    if (enable) glEnable(GL_CULL_FACE);
    else glDisable(GL_CULL_FACE);
}

void setCullFace(unsigned int face) {
    if (!s_gladInitialized) return;
    glCullFace(face);
}

// =============================================================================
// Error Handling
// =============================================================================

const char* getErrorString() {
    if (!s_gladInitialized) return "GLAD not initialized";

    GLenum err = glGetError();
    switch (err) {
        case GL_NO_ERROR: return nullptr;
        case GL_INVALID_ENUM: return "GL_INVALID_ENUM";
        case GL_INVALID_VALUE: return "GL_INVALID_VALUE";
        case GL_INVALID_OPERATION: return "GL_INVALID_OPERATION";
        case GL_OUT_OF_MEMORY: return "GL_OUT_OF_MEMORY";
        case GL_INVALID_FRAMEBUFFER_OPERATION: return "GL_INVALID_FRAMEBUFFER_OPERATION";
        default: return "Unknown GL error";
    }
}

bool checkError(const char* operation) {
    const char* err = getErrorString();
    if (err) {
        fprintf(stderr, "GLContext_SFML: GL error after %s: %s\n", operation, err);
        return false;
    }
    return true;
}

} // namespace gl
} // namespace mcrf

#endif // MCRF_HEADLESS
#endif // MCRF_SDL2
