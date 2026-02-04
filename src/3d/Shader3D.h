// Shader3D.h - Shader management for McRogueFace 3D
// Handles loading, compiling, and uniform management for PS1-style shaders

#pragma once

#include "Math3D.h"
#include <string>
#include <unordered_map>

namespace mcrf {

class Shader3D {
public:
    Shader3D();
    ~Shader3D();

    // Load and compile shaders from embedded source strings
    // Automatically selects desktop vs ES2 shaders based on platform
    bool loadPS1Shaders();

    // Load from custom source strings
    bool load(const char* vertexSource, const char* fragmentSource);

    // Bind/unbind shader for rendering
    void bind();
    void unbind();

    // Check if shader is valid
    bool isValid() const { return program_ != 0; }

    // Uniform setters (cached location lookup)
    void setUniform(const std::string& name, float value);
    void setUniform(const std::string& name, int value);
    void setUniform(const std::string& name, bool value);
    void setUniform(const std::string& name, const vec2& value);
    void setUniform(const std::string& name, const vec3& value);
    void setUniform(const std::string& name, const vec4& value);
    void setUniform(const std::string& name, const mat4& value);

    // Get attribute location for VBO setup
    int getAttribLocation(const std::string& name);

    // Standard attribute locations for PS1 shaders
    static constexpr int ATTRIB_POSITION = 0;
    static constexpr int ATTRIB_TEXCOORD = 1;
    static constexpr int ATTRIB_NORMAL = 2;
    static constexpr int ATTRIB_COLOR = 3;

private:
    unsigned int program_ = 0;
    std::unordered_map<std::string, int> uniformCache_;

    int getUniformLocation(const std::string& name);
};

// =============================================================================
// Embedded PS1 Shader Sources
// =============================================================================

namespace shaders {

// OpenGL ES 2.0 / WebGL 1.0 shaders
extern const char* PS1_VERTEX_ES2;
extern const char* PS1_FRAGMENT_ES2;

// OpenGL 3.2+ desktop shaders
extern const char* PS1_VERTEX;
extern const char* PS1_FRAGMENT;

} // namespace shaders

} // namespace mcrf
