// PS1-style fragment shader for OpenGL ES 2.0 / WebGL 1.0
// Implements affine texture mapping, fog, color quantization, and dithering

precision mediump float;

// Uniforms - texturing
uniform sampler2D u_texture;
uniform bool u_has_texture;   // Whether to use texture or just vertex color

// Uniforms - PS1 effects
uniform bool u_enable_dither; // Enable ordered dithering
uniform vec3 u_fog_color;     // Fog color (usually matches background)

// Varyings from vertex shader
varying vec4 v_color;         // Gouraud-shaded vertex color
varying vec2 v_texcoord;      // Texture coordinates (pre-multiplied by w)
varying float v_w;            // Clip space w for affine restoration
varying float v_fog;          // Fog factor

// =========================================================================
// 4x4 Bayer Dithering Matrix
// Used to add ordered noise for color quantization, reducing banding
// =========================================================================
const mat4 bayerMatrix = mat4(
     0.0/16.0,  8.0/16.0,  2.0/16.0, 10.0/16.0,
    12.0/16.0,  4.0/16.0, 14.0/16.0,  6.0/16.0,
     3.0/16.0, 11.0/16.0,  1.0/16.0,  9.0/16.0,
    15.0/16.0,  7.0/16.0, 13.0/16.0,  5.0/16.0
);

float getBayerValue(vec2 fragCoord) {
    int x = int(mod(fragCoord.x, 4.0));
    int y = int(mod(fragCoord.y, 4.0));

    // Manual matrix lookup (GLES2 doesn't support integer indexing of mat4)
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
    // y == 3
    if (x == 0) return 15.0/16.0;
    if (x == 1) return  7.0/16.0;
    if (x == 2) return 13.0/16.0;
    return  5.0/16.0;
}

// =========================================================================
// 15-bit Color Quantization
// PS1 had 15-bit color (5 bits per channel), creating visible color banding
// =========================================================================
vec3 quantize15bit(vec3 color) {
    // Quantize to 5 bits per channel (32 levels)
    return floor(color * 31.0 + 0.5) / 31.0;
}

void main() {
    // =========================================================================
    // PS1 Effect: Affine Texture Mapping
    // Divide by interpolated w to restore texture coordinates.
    // Because w was interpolated linearly (not perspectively), this creates
    // the characteristic texture warping on PS1.
    // =========================================================================
    vec2 uv = v_texcoord / v_w;

    // Sample texture or use vertex color
    vec4 color;
    if (u_has_texture) {
        vec4 texColor = texture2D(u_texture, uv);

        // Binary alpha test (PS1 style - no alpha blending)
        if (texColor.a < 0.5) {
            discard;
        }

        color = texColor * v_color;
    } else {
        color = v_color;
    }

    // =========================================================================
    // PS1 Effect: Color Quantization with Dithering
    // Reduce color depth to 15-bit, using dithering to reduce banding
    // =========================================================================
    if (u_enable_dither) {
        // Get Bayer dither threshold for this pixel
        float threshold = getBayerValue(gl_FragCoord.xy);

        // Apply dither before quantization
        // Threshold is in range [0, 1), we scale it to affect quantization
        vec3 dithered = color.rgb + (threshold - 0.5) / 31.0;

        // Quantize to 15-bit
        color.rgb = quantize15bit(dithered);
    } else {
        // Just quantize without dithering
        color.rgb = quantize15bit(color.rgb);
    }

    // =========================================================================
    // Fog Application
    // Linear fog blending based on depth
    // =========================================================================
    color.rgb = mix(color.rgb, u_fog_color, v_fog);

    gl_FragColor = color;
}
