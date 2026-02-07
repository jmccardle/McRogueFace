#include "WangResolve.h"
#include <array>

namespace mcrf {
namespace tiled {

// Helper: get terrain at (x, y), return 0 for out-of-bounds
static inline int getTerrain(const uint8_t* data, int w, int h, int x, int y) {
    if (x < 0 || x >= w || y < 0 || y >= h) return 0;
    return data[y * w + x];
}

// For corner wang sets: each corner is at the junction of 4 cells.
// The corner terrain is the max index among those cells (standard Tiled convention:
// higher-index terrain "wins" at shared corners).
static inline int cornerTerrain(int a, int b, int c, int d) {
    int m = a;
    if (b > m) m = b;
    if (c > m) m = c;
    if (d > m) m = d;
    return m;
}

std::vector<int> resolveWangTerrain(
    const uint8_t* terrain_data, int width, int height,
    const WangSet& wang_set)
{
    std::vector<int> result(width * height, -1);

    if (wang_set.type == WangSetType::Corner) {
        // Corner set: wangid layout is [top, TR, right, BR, bottom, BL, left, TL]
        // For corner sets, only even indices matter: [_, TR, _, BR, _, BL, _, TL]
        // i.e. indices 1, 3, 5, 7
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                // Top-left corner: junction of (x-1,y-1), (x,y-1), (x-1,y), (x,y)
                int tl = cornerTerrain(
                    getTerrain(terrain_data, width, height, x-1, y-1),
                    getTerrain(terrain_data, width, height, x,   y-1),
                    getTerrain(terrain_data, width, height, x-1, y),
                    getTerrain(terrain_data, width, height, x,   y));

                // Top-right corner: junction of (x,y-1), (x+1,y-1), (x,y), (x+1,y)
                int tr = cornerTerrain(
                    getTerrain(terrain_data, width, height, x,   y-1),
                    getTerrain(terrain_data, width, height, x+1, y-1),
                    getTerrain(terrain_data, width, height, x,   y),
                    getTerrain(terrain_data, width, height, x+1, y));

                // Bottom-right corner: junction of (x,y), (x+1,y), (x,y+1), (x+1,y+1)
                int br = cornerTerrain(
                    getTerrain(terrain_data, width, height, x,   y),
                    getTerrain(terrain_data, width, height, x+1, y),
                    getTerrain(terrain_data, width, height, x,   y+1),
                    getTerrain(terrain_data, width, height, x+1, y+1));

                // Bottom-left corner: junction of (x-1,y), (x,y), (x-1,y+1), (x,y+1)
                int bl = cornerTerrain(
                    getTerrain(terrain_data, width, height, x-1, y),
                    getTerrain(terrain_data, width, height, x,   y),
                    getTerrain(terrain_data, width, height, x-1, y+1),
                    getTerrain(terrain_data, width, height, x,   y+1));

                // Pack: [0, TR, 0, BR, 0, BL, 0, TL]
                std::array<int, 8> wid = {0, tr, 0, br, 0, bl, 0, tl};
                uint64_t key = WangSet::packWangId(wid);

                auto it = wang_set.wang_lookup.find(key);
                if (it != wang_set.wang_lookup.end()) {
                    result[y * width + x] = it->second;
                }
            }
        }
    }
    else if (wang_set.type == WangSetType::Edge) {
        // Edge set: wangid layout is [top, TR, right, BR, bottom, BL, left, TL]
        // For edge sets, only even indices matter: [top, _, right, _, bottom, _, left, _]
        // i.e. indices 0, 2, 4, 6
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                int top    = getTerrain(terrain_data, width, height, x, y-1);
                int right  = getTerrain(terrain_data, width, height, x+1, y);
                int bottom = getTerrain(terrain_data, width, height, x, y+1);
                int left   = getTerrain(terrain_data, width, height, x-1, y);

                // Pack: [top, 0, right, 0, bottom, 0, left, 0]
                std::array<int, 8> wid = {top, 0, right, 0, bottom, 0, left, 0};
                uint64_t key = WangSet::packWangId(wid);

                auto it = wang_set.wang_lookup.find(key);
                if (it != wang_set.wang_lookup.end()) {
                    result[y * width + x] = it->second;
                }
            }
        }
    }
    else {
        // Mixed: use all 8 values (both edges and corners)
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                int top    = getTerrain(terrain_data, width, height, x, y-1);
                int right  = getTerrain(terrain_data, width, height, x+1, y);
                int bottom = getTerrain(terrain_data, width, height, x, y+1);
                int left   = getTerrain(terrain_data, width, height, x-1, y);

                int tl = cornerTerrain(
                    getTerrain(terrain_data, width, height, x-1, y-1),
                    getTerrain(terrain_data, width, height, x,   y-1),
                    getTerrain(terrain_data, width, height, x-1, y),
                    getTerrain(terrain_data, width, height, x,   y));
                int tr = cornerTerrain(
                    getTerrain(terrain_data, width, height, x,   y-1),
                    getTerrain(terrain_data, width, height, x+1, y-1),
                    getTerrain(terrain_data, width, height, x,   y),
                    getTerrain(terrain_data, width, height, x+1, y));
                int br = cornerTerrain(
                    getTerrain(terrain_data, width, height, x,   y),
                    getTerrain(terrain_data, width, height, x+1, y),
                    getTerrain(terrain_data, width, height, x,   y+1),
                    getTerrain(terrain_data, width, height, x+1, y+1));
                int bl = cornerTerrain(
                    getTerrain(terrain_data, width, height, x-1, y),
                    getTerrain(terrain_data, width, height, x,   y),
                    getTerrain(terrain_data, width, height, x-1, y+1),
                    getTerrain(terrain_data, width, height, x,   y+1));

                std::array<int, 8> wid = {top, tr, right, br, bottom, bl, left, tl};
                uint64_t key = WangSet::packWangId(wid);

                auto it = wang_set.wang_lookup.find(key);
                if (it != wang_set.wang_lookup.end()) {
                    result[y * width + x] = it->second;
                }
            }
        }
    }

    return result;
}

} // namespace tiled
} // namespace mcrf
