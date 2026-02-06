// VoxelMesher.cpp - Face-culled mesh generation for VoxelGrid
// Part of McRogueFace 3D Extension - Milestone 10

#include "VoxelMesher.h"
#include <cmath>

namespace mcrf {

void VoxelMesher::generateMesh(const VoxelGrid& grid, std::vector<MeshVertex>& outVertices) {
    const float cs = grid.cellSize();

    for (int z = 0; z < grid.depth(); z++) {
        for (int y = 0; y < grid.height(); y++) {
            for (int x = 0; x < grid.width(); x++) {
                uint8_t mat = grid.get(x, y, z);
                if (mat == 0) continue;  // Skip air

                const VoxelMaterial& material = grid.getMaterial(mat);

                // Voxel center in local space
                vec3 center((x + 0.5f) * cs, (y + 0.5f) * cs, (z + 0.5f) * cs);

                // Check each face direction
                // +X face
                if (shouldGenerateFace(grid, x, y, z, x + 1, y, z)) {
                    emitFace(outVertices, center, vec3(1, 0, 0), cs, material);
                }
                // -X face
                if (shouldGenerateFace(grid, x, y, z, x - 1, y, z)) {
                    emitFace(outVertices, center, vec3(-1, 0, 0), cs, material);
                }
                // +Y face (top)
                if (shouldGenerateFace(grid, x, y, z, x, y + 1, z)) {
                    emitFace(outVertices, center, vec3(0, 1, 0), cs, material);
                }
                // -Y face (bottom)
                if (shouldGenerateFace(grid, x, y, z, x, y - 1, z)) {
                    emitFace(outVertices, center, vec3(0, -1, 0), cs, material);
                }
                // +Z face
                if (shouldGenerateFace(grid, x, y, z, x, y, z + 1)) {
                    emitFace(outVertices, center, vec3(0, 0, 1), cs, material);
                }
                // -Z face
                if (shouldGenerateFace(grid, x, y, z, x, y, z - 1)) {
                    emitFace(outVertices, center, vec3(0, 0, -1), cs, material);
                }
            }
        }
    }
}

bool VoxelMesher::shouldGenerateFace(const VoxelGrid& grid,
                                      int x, int y, int z,
                                      int nx, int ny, int nz) {
    // Out of bounds = air, so generate face
    if (!grid.isValid(nx, ny, nz)) {
        return true;
    }

    uint8_t neighbor = grid.get(nx, ny, nz);

    // Air neighbor = generate face
    if (neighbor == 0) {
        return true;
    }

    // Check if neighbor is transparent
    // Transparent materials allow faces to be visible behind them
    return grid.getMaterial(neighbor).transparent;
}

void VoxelMesher::emitQuad(std::vector<MeshVertex>& vertices,
                            const vec3& corner,
                            const vec3& uAxis,
                            const vec3& vAxis,
                            const vec3& normal,
                            const VoxelMaterial& material) {
    // 4 corners of the quad
    vec3 corners[4] = {
        corner,                    // 0: origin
        corner + uAxis,            // 1: +U
        corner + uAxis + vAxis,    // 2: +U+V
        corner + vAxis             // 3: +V
    };

    // Calculate UV based on quad size (for potential texture tiling)
    float uLen = uAxis.length();
    float vLen = vAxis.length();
    vec2 uvs[4] = {
        vec2(0, 0),       // 0
        vec2(uLen, 0),    // 1
        vec2(uLen, vLen), // 2
        vec2(0, vLen)     // 3
    };

    // Color from material
    vec4 color(
        material.color.r / 255.0f,
        material.color.g / 255.0f,
        material.color.b / 255.0f,
        material.color.a / 255.0f
    );

    // Emit 2 triangles (6 vertices) - CCW winding
    // Triangle 1: 0-2-1
    vertices.push_back(MeshVertex(corners[0], uvs[0], normal, color));
    vertices.push_back(MeshVertex(corners[2], uvs[2], normal, color));
    vertices.push_back(MeshVertex(corners[1], uvs[1], normal, color));

    // Triangle 2: 0-3-2
    vertices.push_back(MeshVertex(corners[0], uvs[0], normal, color));
    vertices.push_back(MeshVertex(corners[3], uvs[3], normal, color));
    vertices.push_back(MeshVertex(corners[2], uvs[2], normal, color));
}

void VoxelMesher::generateGreedyMesh(const VoxelGrid& grid, std::vector<MeshVertex>& outVertices) {
    const float cs = grid.cellSize();
    const int width = grid.width();
    const int height = grid.height();
    const int depth = grid.depth();

    // Process each face direction
    // Axis 0 = X, 1 = Y, 2 = Z
    // Direction: +1 = positive, -1 = negative

    for (int axis = 0; axis < 3; axis++) {
        for (int dir = -1; dir <= 1; dir += 2) {
            // Determine slice dimensions based on axis
            int sliceW, sliceH, sliceCount;
            if (axis == 0) { // X-axis: slices in YZ plane
                sliceW = depth;
                sliceH = height;
                sliceCount = width;
            } else if (axis == 1) { // Y-axis: slices in XZ plane
                sliceW = width;
                sliceH = depth;
                sliceCount = height;
            } else { // Z-axis: slices in XY plane
                sliceW = width;
                sliceH = height;
                sliceCount = depth;
            }

            // Create mask for this slice
            std::vector<uint8_t> mask(sliceW * sliceH);

            // Process each slice
            for (int sliceIdx = 0; sliceIdx < sliceCount; sliceIdx++) {
                // Fill mask with material IDs where faces should be generated
                std::fill(mask.begin(), mask.end(), 0);

                for (int v = 0; v < sliceH; v++) {
                    for (int u = 0; u < sliceW; u++) {
                        // Map (u, v, sliceIdx) to (x, y, z) based on axis
                        int x, y, z, nx, ny, nz;
                        if (axis == 0) {
                            x = sliceIdx; y = v; z = u;
                            nx = x + dir; ny = y; nz = z;
                        } else if (axis == 1) {
                            x = u; y = sliceIdx; z = v;
                            nx = x; ny = y + dir; nz = z;
                        } else {
                            x = u; y = v; z = sliceIdx;
                            nx = x; ny = y; nz = z + dir;
                        }

                        uint8_t mat = grid.get(x, y, z);
                        if (mat == 0) continue;

                        // Check if face should be generated
                        if (shouldGenerateFace(grid, x, y, z, nx, ny, nz)) {
                            mask[v * sliceW + u] = mat;
                        }
                    }
                }

                // Greedy rectangle merging
                for (int v = 0; v < sliceH; v++) {
                    for (int u = 0; u < sliceW; ) {
                        uint8_t mat = mask[v * sliceW + u];
                        if (mat == 0) {
                            u++;
                            continue;
                        }

                        // Find width of rectangle (extend along U)
                        int rectW = 1;
                        while (u + rectW < sliceW && mask[v * sliceW + u + rectW] == mat) {
                            rectW++;
                        }

                        // Find height of rectangle (extend along V)
                        int rectH = 1;
                        bool canExtend = true;
                        while (canExtend && v + rectH < sliceH) {
                            // Check if entire row matches
                            for (int i = 0; i < rectW; i++) {
                                if (mask[(v + rectH) * sliceW + u + i] != mat) {
                                    canExtend = false;
                                    break;
                                }
                            }
                            if (canExtend) rectH++;
                        }

                        // Clear mask for merged area
                        for (int dv = 0; dv < rectH; dv++) {
                            for (int du = 0; du < rectW; du++) {
                                mask[(v + dv) * sliceW + u + du] = 0;
                            }
                        }

                        // Emit quad for this merged rectangle
                        const VoxelMaterial& material = grid.getMaterial(mat);

                        // Calculate corner and axes based on face direction
                        vec3 corner, uAxis, vAxis, normal;

                        if (axis == 0) { // X-facing
                            float faceX = (dir > 0) ? (sliceIdx + 1) * cs : sliceIdx * cs;
                            corner = vec3(faceX, v * cs, u * cs);
                            uAxis = vec3(0, 0, rectW * cs);
                            vAxis = vec3(0, rectH * cs, 0);
                            normal = vec3(static_cast<float>(dir), 0, 0);
                            // Flip winding for back faces
                            if (dir < 0) std::swap(uAxis, vAxis);
                        } else if (axis == 1) { // Y-facing
                            float faceY = (dir > 0) ? (sliceIdx + 1) * cs : sliceIdx * cs;
                            corner = vec3(u * cs, faceY, v * cs);
                            uAxis = vec3(rectW * cs, 0, 0);
                            vAxis = vec3(0, 0, rectH * cs);
                            normal = vec3(0, static_cast<float>(dir), 0);
                            if (dir < 0) std::swap(uAxis, vAxis);
                        } else { // Z-facing
                            float faceZ = (dir > 0) ? (sliceIdx + 1) * cs : sliceIdx * cs;
                            corner = vec3(u * cs, v * cs, faceZ);
                            // Note: axes swapped vs X/Y cases to maintain CCW winding
                            // (vAxis × uAxis must equal +Z for front faces)
                            uAxis = vec3(0, rectH * cs, 0);
                            vAxis = vec3(rectW * cs, 0, 0);
                            normal = vec3(0, 0, static_cast<float>(dir));
                            if (dir < 0) std::swap(uAxis, vAxis);
                        }

                        emitQuad(outVertices, corner, uAxis, vAxis, normal, material);

                        u += rectW;
                    }
                }
            }
        }
    }
}

void VoxelMesher::emitFace(std::vector<MeshVertex>& vertices,
                            const vec3& center,
                            const vec3& normal,
                            float size,
                            const VoxelMaterial& material) {
    // Calculate face corners based on normal direction
    vec3 up, right;

    if (std::abs(normal.y) > 0.5f) {
        // Horizontal face (floor/ceiling)
        // For +Y (top), we want the face to look correct from above
        // For -Y (bottom), we want it to look correct from below
        up = vec3(0, 0, normal.y);    // Z direction based on face direction
        right = vec3(1, 0, 0);         // Always X axis for horizontal faces
    } else if (std::abs(normal.x) > 0.5f) {
        // X-facing wall
        up = vec3(0, 1, 0);            // Y axis is up
        right = vec3(0, 0, normal.x);  // Z direction based on face direction
    } else {
        // Z-facing wall
        up = vec3(0, 1, 0);            // Y axis is up
        right = vec3(-normal.z, 0, 0); // X direction based on face direction
    }

    float halfSize = size * 0.5f;
    vec3 faceCenter = center + normal * halfSize;

    // 4 corners of the face
    vec3 corners[4] = {
        faceCenter - right * halfSize - up * halfSize,  // Bottom-left
        faceCenter + right * halfSize - up * halfSize,  // Bottom-right
        faceCenter + right * halfSize + up * halfSize,  // Top-right
        faceCenter - right * halfSize + up * halfSize   // Top-left
    };

    // UV coordinates (solid color or single sprite tile)
    vec2 uvs[4] = {
        vec2(0, 0),  // Bottom-left
        vec2(1, 0),  // Bottom-right
        vec2(1, 1),  // Top-right
        vec2(0, 1)   // Top-left
    };

    // Color from material (convert 0-255 to 0-1)
    vec4 color(
        material.color.r / 255.0f,
        material.color.g / 255.0f,
        material.color.b / 255.0f,
        material.color.a / 255.0f
    );

    // Emit 2 triangles (6 vertices) - CCW winding for OpenGL front faces
    // Triangle 1: 0-2-1 (bottom-left, top-right, bottom-right) - CCW
    vertices.push_back(MeshVertex(corners[0], uvs[0], normal, color));
    vertices.push_back(MeshVertex(corners[2], uvs[2], normal, color));
    vertices.push_back(MeshVertex(corners[1], uvs[1], normal, color));

    // Triangle 2: 0-3-2 (bottom-left, top-left, top-right) - CCW
    vertices.push_back(MeshVertex(corners[0], uvs[0], normal, color));
    vertices.push_back(MeshVertex(corners[3], uvs[3], normal, color));
    vertices.push_back(MeshVertex(corners[2], uvs[2], normal, color));
}

} // namespace mcrf
