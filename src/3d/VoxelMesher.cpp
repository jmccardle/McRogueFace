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
