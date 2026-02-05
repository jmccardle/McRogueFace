// PS1-style skinned vertex shader for OpenGL ES 2.0 / WebGL 1.0
// Implements skeletal animation, vertex snapping, Gouraud shading, and fog

precision mediump float;

// Uniforms - transform matrices
uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_projection;

// Uniforms - skeletal animation (max 64 bones)
// GLES2 doesn't guarantee support for arrays > 128 vec4s in vertex shaders
// 64 bones * 4 vec4s = 256 vec4s, so we use 32 bones for safety
uniform mat4 u_bones[32];

// Uniforms - PS1 effects
uniform vec2 u_resolution;    // Internal render resolution for vertex snapping
uniform bool u_enable_snap;   // Enable vertex snapping to pixel grid
uniform float u_fog_start;    // Fog start distance
uniform float u_fog_end;      // Fog end distance

// Uniforms - lighting
uniform vec3 u_light_dir;     // Directional light direction (normalized)
uniform vec3 u_ambient;       // Ambient light color

// Attributes
attribute vec3 a_position;
attribute vec2 a_texcoord;
attribute vec3 a_normal;
attribute vec4 a_color;
attribute vec4 a_bone_ids;       // Up to 4 bone indices (as floats)
attribute vec4 a_bone_weights;   // Corresponding weights

// Varyings - passed to fragment shader
varying vec4 v_color;         // Gouraud-shaded vertex color
varying vec2 v_texcoord;      // Texture coordinates (multiplied by w for affine trick)
varying float v_w;            // Clip space w for affine mapping restoration
varying float v_fog;          // Fog factor (0 = no fog, 1 = full fog)

// Helper to get bone matrix by index (GLES2 doesn't support dynamic array indexing well)
mat4 getBoneMatrix(int index) {
    // GLES2 workaround: use if-chain for dynamic indexing
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
    return mat4(1.0);  // Identity fallback
}

void main() {
    // =========================================================================
    // Skeletal Animation: Vertex Skinning
    // Transform vertex and normal by weighted bone matrices
    // =========================================================================
    int b0 = int(a_bone_ids.x);
    int b1 = int(a_bone_ids.y);
    int b2 = int(a_bone_ids.z);
    int b3 = int(a_bone_ids.w);

    // Compute skinned position and normal
    mat4 skin_matrix =
        getBoneMatrix(b0) * a_bone_weights.x +
        getBoneMatrix(b1) * a_bone_weights.y +
        getBoneMatrix(b2) * a_bone_weights.z +
        getBoneMatrix(b3) * a_bone_weights.w;

    vec4 skinned_pos = skin_matrix * vec4(a_position, 1.0);
    vec3 skinned_normal = mat3(skin_matrix[0].xyz, skin_matrix[1].xyz, skin_matrix[2].xyz) * a_normal;

    // Transform vertex to clip space
    vec4 worldPos = u_model * skinned_pos;
    vec4 viewPos = u_view * worldPos;
    vec4 clipPos = u_projection * viewPos;

    // =========================================================================
    // PS1 Effect: Vertex Snapping
    // The PS1 had limited precision for vertex positions, causing vertices
    // to "snap" to a grid, creating the characteristic jittery look.
    // =========================================================================
    if (u_enable_snap) {
        // Convert to NDC
        vec4 ndc = clipPos;
        ndc.xyz /= ndc.w;

        // Snap to pixel grid based on render resolution
        vec2 grid = u_resolution * 0.5;
        ndc.xy = floor(ndc.xy * grid + 0.5) / grid;

        // Convert back to clip space
        ndc.xyz *= clipPos.w;
        clipPos = ndc;
    }

    gl_Position = clipPos;

    // =========================================================================
    // PS1 Effect: Gouraud Shading
    // Per-vertex lighting was used on PS1 due to hardware limitations.
    // This creates characteristic flat-shaded polygons.
    // =========================================================================
    vec3 worldNormal = mat3(u_model[0].xyz, u_model[1].xyz, u_model[2].xyz) * skinned_normal;
    worldNormal = normalize(worldNormal);

    // Simple directional light + ambient
    float diffuse = max(dot(worldNormal, -u_light_dir), 0.0);
    vec3 lighting = u_ambient + vec3(diffuse);

    // Apply lighting to vertex color
    v_color = vec4(a_color.rgb * lighting, a_color.a);

    // =========================================================================
    // PS1 Effect: Affine Texture Mapping Trick
    // GLES2 doesn't have 'noperspective' interpolation, so we manually
    // multiply texcoords by w here and divide by w in fragment shader.
    // This creates the characteristic texture warping on large polygons.
    // =========================================================================
    v_texcoord = a_texcoord * clipPos.w;
    v_w = clipPos.w;

    // =========================================================================
    // Fog Distance Calculation
    // Calculate linear fog factor based on view-space depth
    // =========================================================================
    float depth = -viewPos.z;  // View space depth (positive)
    v_fog = clamp((depth - u_fog_start) / (u_fog_end - u_fog_start), 0.0, 1.0);
}
