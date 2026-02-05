// VoxelMesher.h - Face-culled mesh generation for VoxelGrid
// Part of McRogueFace 3D Extension - Milestones 10, 13
#pragma once

#include "VoxelGrid.h"
#include "MeshLayer.h"  // For MeshVertex
#include <vector>

namespace mcrf {

// =============================================================================
// VoxelMesher - Static class for generating triangle meshes from VoxelGrid
// =============================================================================

class VoxelMesher {
public:
    /// Generate face-culled mesh from voxel data (simple per-voxel faces)
    /// Output vertices in local space (model matrix applies world transform)
    /// @param grid The VoxelGrid to generate mesh from
    /// @param outVertices Output vector of vertices (appended to, not cleared)
    static void generateMesh(
        const VoxelGrid& grid,
        std::vector<MeshVertex>& outVertices
    );

    /// Generate mesh using greedy meshing algorithm (Milestone 13)
    /// Merges coplanar faces of the same material into larger rectangles,
    /// significantly reducing vertex count for uniform regions.
    /// @param grid The VoxelGrid to generate mesh from
    /// @param outVertices Output vector of vertices (appended to, not cleared)
    static void generateGreedyMesh(
        const VoxelGrid& grid,
        std::vector<MeshVertex>& outVertices
    );

private:
    /// Check if face should be generated (neighbor is air or transparent)
    /// @param grid The VoxelGrid
    /// @param x, y, z Current voxel position
    /// @param nx, ny, nz Neighbor voxel position
    /// @return true if face should be generated
    static bool shouldGenerateFace(
        const VoxelGrid& grid,
        int x, int y, int z,
        int nx, int ny, int nz
    );

    /// Generate a single face (2 triangles = 6 vertices)
    /// @param vertices Output vector to append vertices to
    /// @param center Center of the voxel
    /// @param normal Face normal direction
    /// @param size Voxel cell size
    /// @param material Material for coloring
    static void emitFace(
        std::vector<MeshVertex>& vertices,
        const vec3& center,
        const vec3& normal,
        float size,
        const VoxelMaterial& material
    );

    /// Generate a rectangular face (2 triangles = 6 vertices)
    /// Used by greedy meshing to emit merged quads
    /// @param vertices Output vector to append vertices to
    /// @param corner Base corner of the rectangle
    /// @param uAxis Direction and length along U axis
    /// @param vAxis Direction and length along V axis
    /// @param normal Face normal direction
    /// @param material Material for coloring
    static void emitQuad(
        std::vector<MeshVertex>& vertices,
        const vec3& corner,
        const vec3& uAxis,
        const vec3& vAxis,
        const vec3& normal,
        const VoxelMaterial& material
    );
};

} // namespace mcrf
