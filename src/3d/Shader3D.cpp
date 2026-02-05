// Shader3D.cpp - Shader management implementation

#include "Shader3D.h"
#include "../platform/GLContext.h"

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
// Embedded Shader Sources
// =============================================================================

namespace shaders {

const char* PS1_VERTEX_ES2 = R"(
// PS1-style vertex shader for OpenGL ES 2.0 / WebGL 1.0
precision mediump float;

uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_projection;
uniform vec2 u_resolution;
uniform bool u_enable_snap;
uniform float u_fog_start;
uniform float u_fog_end;
uniform vec3 u_light_dir;
uniform vec3 u_ambient;

attribute vec3 a_position;
attribute vec2 a_texcoord;
attribute vec3 a_normal;
attribute vec4 a_color;

varying vec4 v_color;
varying vec2 v_texcoord;
varying float v_w;
varying float v_fog;

void main() {
    vec4 worldPos = u_model * vec4(a_position, 1.0);
    vec4 viewPos = u_view * worldPos;
    vec4 clipPos = u_projection * viewPos;

    if (u_enable_snap) {
        vec4 ndc = clipPos;
        ndc.xyz /= ndc.w;
        vec2 grid = u_resolution * 0.5;
        ndc.xy = floor(ndc.xy * grid + 0.5) / grid;
        ndc.xyz *= clipPos.w;
        clipPos = ndc;
    }

    gl_Position = clipPos;

    vec3 worldNormal = normalize(mat3(u_model) * a_normal);
    float diffuse = max(dot(worldNormal, -u_light_dir), 0.0);
    vec3 lighting = u_ambient + vec3(diffuse);
    v_color = vec4(a_color.rgb * lighting, a_color.a);

    v_texcoord = a_texcoord * clipPos.w;
    v_w = clipPos.w;

    float depth = -viewPos.z;
    v_fog = clamp((depth - u_fog_start) / (u_fog_end - u_fog_start), 0.0, 1.0);
}
)";

const char* PS1_FRAGMENT_ES2 = R"(
// PS1-style fragment shader for OpenGL ES 2.0 / WebGL 1.0
precision mediump float;

uniform sampler2D u_texture;
uniform bool u_has_texture;
uniform bool u_enable_dither;
uniform vec3 u_fog_color;

varying vec4 v_color;
varying vec2 v_texcoord;
varying float v_w;
varying float v_fog;

float getBayerValue(vec2 fragCoord) {
    int x = int(mod(fragCoord.x, 4.0));
    int y = int(mod(fragCoord.y, 4.0));
    if (y == 0) {
        if (x == 0) return  0.0/16.0;
        if (x == 1) return  8.0/16.0;
        if (x == 2) return  2.0/16.0;
        return 10.0/16.0;
    }
    if (y == 1) {
        if (x == 0) return 12.0/16.0;
        if (x == 1) return  4.0/16.0;
        if (x == 2) return 14.0/16.0;
        return  6.0/16.0;
    }
    if (y == 2) {
        if (x == 0) return  3.0/16.0;
        if (x == 1) return 11.0/16.0;
        if (x == 2) return  1.0/16.0;
        return  9.0/16.0;
    }
    if (x == 0) return 15.0/16.0;
    if (x == 1) return  7.0/16.0;
    if (x == 2) return 13.0/16.0;
    return  5.0/16.0;
}

vec3 quantize15bit(vec3 color) {
    return floor(color * 31.0 + 0.5) / 31.0;
}

void main() {
    vec2 uv = v_texcoord / v_w;

    vec4 color;
    if (u_has_texture) {
        vec4 texColor = texture2D(u_texture, uv);
        if (texColor.a < 0.5) discard;
        color = texColor * v_color;
    } else {
        color = v_color;
    }

    if (u_enable_dither) {
        float threshold = getBayerValue(gl_FragCoord.xy);
        vec3 dithered = color.rgb + (threshold - 0.5) / 31.0;
        color.rgb = quantize15bit(dithered);
    } else {
        color.rgb = quantize15bit(color.rgb);
    }

    color.rgb = mix(color.rgb, u_fog_color, v_fog);
    gl_FragColor = color;
}
)";

const char* PS1_VERTEX = R"(
#version 150 core
uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_projection;
uniform vec2 u_resolution;
uniform bool u_enable_snap;
uniform float u_fog_start;
uniform float u_fog_end;
uniform vec3 u_light_dir;
uniform vec3 u_ambient;

in vec3 a_position;
in vec2 a_texcoord;
in vec3 a_normal;
in vec4 a_color;

out vec4 v_color;
noperspective out vec2 v_texcoord;
out float v_fog;

void main() {
    vec4 worldPos = u_model * vec4(a_position, 1.0);
    vec4 viewPos = u_view * worldPos;
    vec4 clipPos = u_projection * viewPos;

    if (u_enable_snap) {
        vec4 ndc = clipPos;
        ndc.xyz /= ndc.w;
        vec2 grid = u_resolution * 0.5;
        ndc.xy = floor(ndc.xy * grid + 0.5) / grid;
        ndc.xyz *= clipPos.w;
        clipPos = ndc;
    }

    gl_Position = clipPos;

    vec3 worldNormal = normalize(mat3(u_model) * a_normal);
    float diffuse = max(dot(worldNormal, -u_light_dir), 0.0);
    vec3 lighting = u_ambient + vec3(diffuse);
    v_color = vec4(a_color.rgb * lighting, a_color.a);
    v_texcoord = a_texcoord;

    float depth = -viewPos.z;
    v_fog = clamp((depth - u_fog_start) / (u_fog_end - u_fog_start), 0.0, 1.0);
}
)";

const char* PS1_FRAGMENT = R"(
#version 150 core
uniform sampler2D u_texture;
uniform bool u_has_texture;
uniform bool u_enable_dither;
uniform vec3 u_fog_color;

in vec4 v_color;
noperspective in vec2 v_texcoord;
in float v_fog;

out vec4 fragColor;

const int bayerMatrix[16] = int[16](0,8,2,10,12,4,14,6,3,11,1,9,15,7,13,5);

float getBayerValue(vec2 fragCoord) {
    int x = int(mod(fragCoord.x, 4.0));
    int y = int(mod(fragCoord.y, 4.0));
    return float(bayerMatrix[y * 4 + x]) / 16.0;
}

vec3 quantize15bit(vec3 color) {
    return floor(color * 31.0 + 0.5) / 31.0;
}

void main() {
    vec4 color;
    if (u_has_texture) {
        vec4 texColor = texture(u_texture, v_texcoord);
        if (texColor.a < 0.5) discard;
        color = texColor * v_color;
    } else {
        color = v_color;
    }

    if (u_enable_dither) {
        float threshold = getBayerValue(gl_FragCoord.xy);
        vec3 dithered = color.rgb + (threshold - 0.5) / 31.0;
        color.rgb = quantize15bit(dithered);
    } else {
        color.rgb = quantize15bit(color.rgb);
    }

    color.rgb = mix(color.rgb, u_fog_color, v_fog);
    fragColor = color;
}
)";

// =============================================================================
// Skinned Vertex Shaders (for skeletal animation)
// =============================================================================

const char* PS1_SKINNED_VERTEX_ES2 = R"(
// PS1-style skinned vertex shader for OpenGL ES 2.0 / WebGL 1.0
precision mediump float;

uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_projection;
uniform mat4 u_bones[32];
uniform vec2 u_resolution;
uniform bool u_enable_snap;
uniform float u_fog_start;
uniform float u_fog_end;
uniform vec3 u_light_dir;
uniform vec3 u_ambient;

attribute vec3 a_position;
attribute vec2 a_texcoord;
attribute vec3 a_normal;
attribute vec4 a_color;
attribute vec4 a_bone_ids;
attribute vec4 a_bone_weights;

varying vec4 v_color;
varying vec2 v_texcoord;
varying float v_w;
varying float v_fog;

mat4 getBoneMatrix(int index) {
    if (index < 8) {
        if (index < 4) {
            if (index < 2) {
                if (index == 0) return u_bones[0];
                else return u_bones[1];
            } else {
                if (index == 2) return u_bones[2];
                else return u_bones[3];
            }
        } else {
            if (index < 6) {
                if (index == 4) return u_bones[4];
                else return u_bones[5];
            } else {
                if (index == 6) return u_bones[6];
                else return u_bones[7];
            }
        }
    } else if (index < 16) {
        if (index < 12) {
            if (index < 10) {
                if (index == 8) return u_bones[8];
                else return u_bones[9];
            } else {
                if (index == 10) return u_bones[10];
                else return u_bones[11];
            }
        } else {
            if (index < 14) {
                if (index == 12) return u_bones[12];
                else return u_bones[13];
            } else {
                if (index == 14) return u_bones[14];
                else return u_bones[15];
            }
        }
    } else if (index < 24) {
        if (index < 20) {
            if (index < 18) {
                if (index == 16) return u_bones[16];
                else return u_bones[17];
            } else {
                if (index == 18) return u_bones[18];
                else return u_bones[19];
            }
        } else {
            if (index < 22) {
                if (index == 20) return u_bones[20];
                else return u_bones[21];
            } else {
                if (index == 22) return u_bones[22];
                else return u_bones[23];
            }
        }
    } else {
        if (index < 28) {
            if (index < 26) {
                if (index == 24) return u_bones[24];
                else return u_bones[25];
            } else {
                if (index == 26) return u_bones[26];
                else return u_bones[27];
            }
        } else {
            if (index < 30) {
                if (index == 28) return u_bones[28];
                else return u_bones[29];
            } else {
                if (index == 30) return u_bones[30];
                else return u_bones[31];
            }
        }
    }
    return mat4(1.0);
}

void main() {
    int b0 = int(a_bone_ids.x);
    int b1 = int(a_bone_ids.y);
    int b2 = int(a_bone_ids.z);
    int b3 = int(a_bone_ids.w);

    mat4 skin_matrix =
        getBoneMatrix(b0) * a_bone_weights.x +
        getBoneMatrix(b1) * a_bone_weights.y +
        getBoneMatrix(b2) * a_bone_weights.z +
        getBoneMatrix(b3) * a_bone_weights.w;

    vec4 skinned_pos = skin_matrix * vec4(a_position, 1.0);
    vec3 skinned_normal = mat3(skin_matrix[0].xyz, skin_matrix[1].xyz, skin_matrix[2].xyz) * a_normal;

    vec4 worldPos = u_model * skinned_pos;
    vec4 viewPos = u_view * worldPos;
    vec4 clipPos = u_projection * viewPos;

    if (u_enable_snap) {
        vec4 ndc = clipPos;
        ndc.xyz /= ndc.w;
        vec2 grid = u_resolution * 0.5;
        ndc.xy = floor(ndc.xy * grid + 0.5) / grid;
        ndc.xyz *= clipPos.w;
        clipPos = ndc;
    }

    gl_Position = clipPos;

    vec3 worldNormal = mat3(u_model[0].xyz, u_model[1].xyz, u_model[2].xyz) * skinned_normal;
    worldNormal = normalize(worldNormal);
    float diffuse = max(dot(worldNormal, -u_light_dir), 0.0);
    vec3 lighting = u_ambient + vec3(diffuse);
    v_color = vec4(a_color.rgb * lighting, a_color.a);

    v_texcoord = a_texcoord * clipPos.w;
    v_w = clipPos.w;

    float depth = -viewPos.z;
    v_fog = clamp((depth - u_fog_start) / (u_fog_end - u_fog_start), 0.0, 1.0);
}
)";

const char* PS1_SKINNED_VERTEX = R"(
#version 150 core

uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_projection;
uniform mat4 u_bones[64];
uniform vec2 u_resolution;
uniform bool u_enable_snap;
uniform float u_fog_start;
uniform float u_fog_end;
uniform vec3 u_light_dir;
uniform vec3 u_ambient;

in vec3 a_position;
in vec2 a_texcoord;
in vec3 a_normal;
in vec4 a_color;
in vec4 a_bone_ids;
in vec4 a_bone_weights;

out vec4 v_color;
noperspective out vec2 v_texcoord;
out float v_fog;

void main() {
    ivec4 bone_ids = ivec4(a_bone_ids);

    mat4 skin_matrix =
        u_bones[bone_ids.x] * a_bone_weights.x +
        u_bones[bone_ids.y] * a_bone_weights.y +
        u_bones[bone_ids.z] * a_bone_weights.z +
        u_bones[bone_ids.w] * a_bone_weights.w;

    vec4 skinned_pos = skin_matrix * vec4(a_position, 1.0);
    vec3 skinned_normal = mat3(skin_matrix) * a_normal;

    vec4 worldPos = u_model * skinned_pos;
    vec4 viewPos = u_view * worldPos;
    vec4 clipPos = u_projection * viewPos;

    if (u_enable_snap) {
        vec4 ndc = clipPos;
        ndc.xyz /= ndc.w;
        vec2 grid = u_resolution * 0.5;
        ndc.xy = floor(ndc.xy * grid + 0.5) / grid;
        ndc.xyz *= clipPos.w;
        clipPos = ndc;
    }

    gl_Position = clipPos;

    vec3 worldNormal = mat3(u_model) * skinned_normal;
    worldNormal = normalize(worldNormal);
    float diffuse = max(dot(worldNormal, -u_light_dir), 0.0);
    vec3 lighting = u_ambient + vec3(diffuse);
    v_color = vec4(a_color.rgb * lighting, a_color.a);

    v_texcoord = a_texcoord;

    float depth = -viewPos.z;
    v_fog = clamp((depth - u_fog_start) / (u_fog_end - u_fog_start), 0.0, 1.0);
}
)";

} // namespace shaders

// =============================================================================
// Shader3D Implementation
// =============================================================================

Shader3D::Shader3D() = default;

Shader3D::~Shader3D() {
    if (program_ != 0) {
        gl::deleteProgram(program_);
    }
}

bool Shader3D::loadPS1Shaders() {
#ifdef MCRF_HAS_GL
#ifdef __EMSCRIPTEN__
    // Use GLES2 shaders for Emscripten/WebGL
    return load(shaders::PS1_VERTEX_ES2, shaders::PS1_FRAGMENT_ES2);
#else
    // Use desktop GL 3.2+ shaders
    return load(shaders::PS1_VERTEX, shaders::PS1_FRAGMENT);
#endif
#else
    // SFML backend - requires GLAD (not yet implemented)
    return false;
#endif
}

bool Shader3D::loadPS1SkinnedShaders() {
#ifdef MCRF_HAS_GL
#ifdef __EMSCRIPTEN__
    // Use GLES2 skinned shaders for Emscripten/WebGL
    return load(shaders::PS1_SKINNED_VERTEX_ES2, shaders::PS1_FRAGMENT_ES2);
#else
    // Use desktop GL 3.2+ skinned shaders
    return load(shaders::PS1_SKINNED_VERTEX, shaders::PS1_FRAGMENT);
#endif
#else
    return false;
#endif
}

bool Shader3D::load(const char* vertexSource, const char* fragmentSource) {
    if (!gl::isGLReady()) {
        return false;
    }

    // Compile vertex shader
#ifdef MCRF_HAS_GL
    unsigned int vertShader = gl::compileShader(GL_VERTEX_SHADER, vertexSource);
#else
    unsigned int vertShader = gl::compileShader(0x8B31, vertexSource); // GL_VERTEX_SHADER
#endif
    if (vertShader == 0) {
        return false;
    }

    // Compile fragment shader
#ifdef MCRF_HAS_GL
    unsigned int fragShader = gl::compileShader(GL_FRAGMENT_SHADER, fragmentSource);
#else
    unsigned int fragShader = gl::compileShader(0x8B30, fragmentSource); // GL_FRAGMENT_SHADER
#endif
    if (fragShader == 0) {
        return false;
    }

    // Link program
    program_ = gl::linkProgram(vertShader, fragShader);

    // Clean up individual shaders (they're now part of the program)
#ifdef MCRF_HAS_GL
    glDeleteShader(vertShader);
    glDeleteShader(fragShader);
#endif

    if (program_ == 0) {
        return false;
    }

    // Bind standard attribute locations
#ifdef MCRF_HAS_GL
    glBindAttribLocation(program_, ATTRIB_POSITION, "a_position");
    glBindAttribLocation(program_, ATTRIB_TEXCOORD, "a_texcoord");
    glBindAttribLocation(program_, ATTRIB_NORMAL, "a_normal");
    glBindAttribLocation(program_, ATTRIB_COLOR, "a_color");

    // Re-link after binding attributes
    glLinkProgram(program_);
#endif

    uniformCache_.clear();
    return true;
}

void Shader3D::bind() {
#ifdef MCRF_HAS_GL
    if (program_ != 0) {
        glUseProgram(program_);
    }
#endif
}

void Shader3D::unbind() {
#ifdef MCRF_HAS_GL
    glUseProgram(0);
#endif
}

int Shader3D::getUniformLocation(const std::string& name) {
    auto it = uniformCache_.find(name);
    if (it != uniformCache_.end()) {
        return it->second;
    }

#ifdef MCRF_HAS_GL
    int location = glGetUniformLocation(program_, name.c_str());
    uniformCache_[name] = location;
    return location;
#else
    return -1;
#endif
}

int Shader3D::getAttribLocation(const std::string& name) {
#ifdef MCRF_HAS_GL
    return glGetAttribLocation(program_, name.c_str());
#else
    return -1;
#endif
}

void Shader3D::setUniform(const std::string& name, float value) {
#ifdef MCRF_HAS_GL
    int loc = getUniformLocation(name);
    if (loc >= 0) {
        glUniform1f(loc, value);
    }
#endif
}

void Shader3D::setUniform(const std::string& name, int value) {
#ifdef MCRF_HAS_GL
    int loc = getUniformLocation(name);
    if (loc >= 0) {
        glUniform1i(loc, value);
    }
#endif
}

void Shader3D::setUniform(const std::string& name, bool value) {
#ifdef MCRF_HAS_GL
    int loc = getUniformLocation(name);
    if (loc >= 0) {
        glUniform1i(loc, value ? 1 : 0);
    }
#endif
}

void Shader3D::setUniform(const std::string& name, const vec2& value) {
#ifdef MCRF_HAS_GL
    int loc = getUniformLocation(name);
    if (loc >= 0) {
        glUniform2f(loc, value.x, value.y);
    }
#endif
}

void Shader3D::setUniform(const std::string& name, const vec3& value) {
#ifdef MCRF_HAS_GL
    int loc = getUniformLocation(name);
    if (loc >= 0) {
        glUniform3f(loc, value.x, value.y, value.z);
    }
#endif
}

void Shader3D::setUniform(const std::string& name, const vec4& value) {
#ifdef MCRF_HAS_GL
    int loc = getUniformLocation(name);
    if (loc >= 0) {
        glUniform4f(loc, value.x, value.y, value.z, value.w);
    }
#endif
}

void Shader3D::setUniform(const std::string& name, const mat4& value) {
#ifdef MCRF_HAS_GL
    int loc = getUniformLocation(name);
    if (loc >= 0) {
        glUniformMatrix4fv(loc, 1, GL_FALSE, value.m);
    }
#endif
}

} // namespace mcrf
