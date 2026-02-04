// PS1-style fragment shader for OpenGL 3.2+
// Implements affine texture mapping, fog, color quantization, and dithering

#version 150 core

// Uniforms - texturing
uniform sampler2D u_texture;
uniform bool u_has_texture;   // Whether to use texture or just vertex color

// Uniforms - PS1 effects
uniform bool u_enable_dither; // Enable ordered dithering
uniform vec3 u_fog_color;     // Fog color (usually matches background)

// Varyings from vertex shader
in vec4 v_color;              // Gouraud-shaded vertex color
noperspective in vec2 v_texcoord;  // Texture coordinates (affine interpolation!)
in float v_fog;               // Fog factor

// Output
out vec4 fragColor;

// =========================================================================
// 4x4 Bayer Dithering Matrix
// Used to add ordered noise for color quantization, reducing banding
// =========================================================================
const int bayerMatrix[16] = int[16](
     0,  8,  2, 10,
    12,  4, 14,  6,
     3, 11,  1,  9,
    15,  7, 13,  5
);

float getBayerValue(vec2 fragCoord) {
    int x = int(mod(fragCoord.x, 4.0));
    int y = int(mod(fragCoord.y, 4.0));
    return float(bayerMatrix[y * 4 + x]) / 16.0;
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
    // Sample texture or use vertex color
    vec4 color;
    if (u_has_texture) {
        vec4 texColor = texture(u_texture, v_texcoord);

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

    fragColor = color;
}
