// PS1-style skinned vertex shader for OpenGL 3.2+
// Implements skeletal animation, vertex snapping, Gouraud shading, and fog

#version 150 core

// Uniforms - transform matrices
uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_projection;

// Uniforms - skeletal animation (max 64 bones)
uniform mat4 u_bones[64];

// Uniforms - PS1 effects
uniform vec2 u_resolution;    // Internal render resolution for vertex snapping
uniform bool u_enable_snap;   // Enable vertex snapping to pixel grid
uniform float u_fog_start;    // Fog start distance
uniform float u_fog_end;      // Fog end distance

// Uniforms - lighting
uniform vec3 u_light_dir;     // Directional light direction (normalized)
uniform vec3 u_ambient;       // Ambient light color

// Attributes
in vec3 a_position;
in vec2 a_texcoord;
in vec3 a_normal;
in vec4 a_color;
in vec4 a_bone_ids;       // Up to 4 bone indices (as float for compatibility)
in vec4 a_bone_weights;   // Corresponding weights

// Varyings - passed to fragment shader
out vec4 v_color;             // Gouraud-shaded vertex color
noperspective out vec2 v_texcoord;  // Texture coordinates (affine interpolation!)
out float v_fog;              // Fog factor (0 = no fog, 1 = full fog)

void main() {
    // =========================================================================
    // Skeletal Animation: Vertex Skinning
    // Transform vertex and normal by weighted bone matrices
    // =========================================================================
    ivec4 bone_ids = ivec4(a_bone_ids);  // Convert to integer indices

    // Compute skinned position and normal
    mat4 skin_matrix =
        u_bones[bone_ids.x] * a_bone_weights.x +
        u_bones[bone_ids.y] * a_bone_weights.y +
        u_bones[bone_ids.z] * a_bone_weights.z +
        u_bones[bone_ids.w] * a_bone_weights.w;

    vec4 skinned_pos = skin_matrix * vec4(a_position, 1.0);
    vec3 skinned_normal = mat3(skin_matrix) * a_normal;

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
    vec3 worldNormal = mat3(u_model) * skinned_normal;
    worldNormal = normalize(worldNormal);

    // Simple directional light + ambient
    float diffuse = max(dot(worldNormal, -u_light_dir), 0.0);
    vec3 lighting = u_ambient + vec3(diffuse);

    // Apply lighting to vertex color
    v_color = vec4(a_color.rgb * lighting, a_color.a);

    // =========================================================================
    // PS1 Effect: Affine Texture Mapping
    // Using 'noperspective' qualifier disables perspective-correct interpolation
    // This creates the characteristic texture warping on large polygons
    // =========================================================================
    v_texcoord = a_texcoord;

    // =========================================================================
    // Fog Distance Calculation
    // Calculate linear fog factor based on view-space depth
    // =========================================================================
    float depth = -viewPos.z;  // View space depth (positive)
    v_fog = clamp((depth - u_fog_start) / (u_fog_end - u_fog_start), 0.0, 1.0);
}
