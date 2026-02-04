// PS1-style vertex shader for OpenGL ES 2.0 / WebGL 1.0
// Implements vertex snapping, Gouraud shading, and fog distance calculation

precision mediump float;

// Uniforms - transform matrices
uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_projection;

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

// Varyings - passed to fragment shader
varying vec4 v_color;         // Gouraud-shaded vertex color
varying vec2 v_texcoord;      // Texture coordinates (multiplied by w for affine trick)
varying float v_w;            // Clip space w for affine mapping restoration
varying float v_fog;          // Fog factor (0 = no fog, 1 = full fog)

void main() {
    // Transform vertex to clip space
    vec4 worldPos = u_model * vec4(a_position, 1.0);
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
    vec3 worldNormal = mat3(u_model) * a_normal;
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
