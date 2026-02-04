// GLContext_Headless.cpp - Headless backend for OpenGL context abstraction
// Returns failure for all operations since there's no GPU

#ifdef MCRF_HEADLESS

#include "GLContext.h"

namespace mcrf {
namespace gl {

bool initGL() {
    return false;
}

bool isGLReady() {
    return false;
}

unsigned int createFramebuffer(int width, int height, unsigned int* colorTex, unsigned int* depthRB) {
    if (colorTex) *colorTex = 0;
    if (depthRB) *depthRB = 0;
    return 0;
}

void bindFramebuffer(unsigned int fbo) {}
void bindDefaultFramebuffer() {}
void deleteFramebuffer(unsigned int fbo, unsigned int colorTex, unsigned int depthRB) {}

unsigned int compileShader(unsigned int type, const char* source) {
    return 0;
}

unsigned int linkProgram(unsigned int vertShader, unsigned int fragShader) {
    return 0;
}

void deleteProgram(unsigned int program) {}
void pushState() {}
void popState() {}
void setup3DState() {}
void restore2DState() {}
void setDepthTest(bool enable) {}
void setDepthWrite(bool enable) {}
void setDepthFunc(unsigned int func) {}
void clearDepth() {}
void setCulling(bool enable) {}
void setCullFace(unsigned int face) {}

const char* getErrorString() {
    return "Headless mode - no GL context";
}

bool checkError(const char* operation) {
    return false;
}

} // namespace gl
} // namespace mcrf

#endif // MCRF_HEADLESS
