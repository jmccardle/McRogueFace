// GLContext.h - OpenGL context abstraction for McRogueFace 3D
// Provides uniform GL access across SFML and SDL2 backends

#pragma once

#include "../3d/Math3D.h"

namespace mcrf {
namespace gl {

// =============================================================================
// Initialization
// =============================================================================

// Initialize OpenGL function pointers if needed (GLAD for desktop SFML)
// Returns true if GL is ready to use
bool initGL();

// Check if GL is initialized and ready
bool isGLReady();

// =============================================================================
// Framebuffer Object (FBO) Management
// =============================================================================

// Create a framebuffer with color texture and optional depth renderbuffer
// Returns FBO id, sets colorTex to the color attachment texture
// depthRB is optional - pass nullptr if depth buffer not needed
unsigned int createFramebuffer(int width, int height, unsigned int* colorTex, unsigned int* depthRB = nullptr);

// Bind a framebuffer for rendering
void bindFramebuffer(unsigned int fbo);

// Bind the default framebuffer (screen)
void bindDefaultFramebuffer();

// Delete a framebuffer and its attachments
void deleteFramebuffer(unsigned int fbo, unsigned int colorTex, unsigned int depthRB);

// =============================================================================
// Shader Compilation
// =============================================================================

// Compile a vertex or fragment shader from source
// type should be GL_VERTEX_SHADER or GL_FRAGMENT_SHADER
unsigned int compileShader(unsigned int type, const char* source);

// Link vertex and fragment shaders into a program
// Returns program id, or 0 on failure
unsigned int linkProgram(unsigned int vertShader, unsigned int fragShader);

// Delete a shader program
void deleteProgram(unsigned int program);

// =============================================================================
// GL State Management (for mixing with SFML rendering)
// =============================================================================

// Save current OpenGL state before custom 3D rendering
// This includes blend mode, depth test, culling, bound textures, etc.
void pushState();

// Restore OpenGL state after custom 3D rendering
void popState();

// =============================================================================
// 3D Rendering State Setup
// =============================================================================

// Set up GL state for 3D rendering (depth test, culling, etc.)
void setup3DState();

// Restore GL state for 2D rendering (disable depth, etc.)
void restore2DState();

// =============================================================================
// Depth Buffer Operations
// =============================================================================

// Enable/disable depth testing
void setDepthTest(bool enable);

// Enable/disable depth writing
void setDepthWrite(bool enable);

// Set depth test function (GL_LESS, GL_LEQUAL, etc.)
void setDepthFunc(unsigned int func);

// Clear the depth buffer
void clearDepth();

// =============================================================================
// Face Culling
// =============================================================================

// Enable/disable face culling
void setCulling(bool enable);

// Set which face to cull (GL_BACK, GL_FRONT, GL_FRONT_AND_BACK)
void setCullFace(unsigned int face);

// =============================================================================
// Utility
// =============================================================================

// Get last GL error as string (for debugging)
const char* getErrorString();

// Check for GL errors and log them
bool checkError(const char* operation);

} // namespace gl
} // namespace mcrf
