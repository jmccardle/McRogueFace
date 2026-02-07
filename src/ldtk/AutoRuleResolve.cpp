#include "AutoRuleResolve.h"
#include <functional>

namespace mcrf {
namespace ldtk {

// ============================================================
// Deterministic hash for pseudo-random decisions
// ============================================================

static uint32_t hashCell(uint32_t seed, int x, int y, int rule_uid) {
    // Simple but deterministic hash combining seed, position, and rule
    uint32_t h = seed;
    h ^= static_cast<uint32_t>(x) * 374761393u;
    h ^= static_cast<uint32_t>(y) * 668265263u;
    h ^= static_cast<uint32_t>(rule_uid) * 2654435761u;
    h = (h ^ (h >> 13)) * 1274126177u;
    h = h ^ (h >> 16);
    return h;
}

// ============================================================
// IntGrid access with out-of-bounds handling
// ============================================================

static inline int getIntGrid(const int* data, int w, int h, int x, int y, int oob_value) {
    if (x < 0 || x >= w || y < 0 || y >= h) {
        return (oob_value == -1) ? 0 : oob_value;
    }
    return data[y * w + x];
}

// ============================================================
// Pattern matching
// ============================================================

static bool matchPattern(const int* intgrid, int w, int h,
                         int cx, int cy,
                         const std::vector<int>& pattern, int size,
                         int oob_value)
{
    int half = size / 2;
    for (int py = 0; py < size; py++) {
        for (int px = 0; px < size; px++) {
            int pattern_val = pattern[py * size + px];
            if (pattern_val == 0) continue; // Wildcard

            int gx = cx + (px - half);
            int gy = cy + (py - half);
            int cell_val = getIntGrid(intgrid, w, h, gx, gy, oob_value);

            if (pattern_val > 0) {
                if (pattern_val >= 1000000) {
                    // LDtk IntGrid group reference: 1000001 = "any non-empty value"
                    // (group-based matching; for now treat as "any non-zero")
                    if (cell_val == 0) return false;
                } else {
                    // Must match this exact value
                    if (cell_val != pattern_val) return false;
                }
            } else if (pattern_val < 0) {
                if (pattern_val <= -1000000) {
                    // Negated group reference: -1000001 = "NOT any non-empty" = "must be empty"
                    if (cell_val != 0) return false;
                } else {
                    // Must NOT be this value (negative = negation)
                    if (cell_val == -pattern_val) return false;
                }
            }
        }
    }
    return true;
}

// ============================================================
// Flip pattern generation
// ============================================================

static std::vector<int> flipPatternX(const std::vector<int>& pattern, int size) {
    std::vector<int> result(pattern.size());
    for (int y = 0; y < size; y++) {
        for (int x = 0; x < size; x++) {
            result[y * size + (size - 1 - x)] = pattern[y * size + x];
        }
    }
    return result;
}

static std::vector<int> flipPatternY(const std::vector<int>& pattern, int size) {
    std::vector<int> result(pattern.size());
    for (int y = 0; y < size; y++) {
        for (int x = 0; x < size; x++) {
            result[(size - 1 - y) * size + x] = pattern[y * size + x];
        }
    }
    return result;
}

// ============================================================
// Resolution engine
// ============================================================

std::vector<AutoTileResult> resolveAutoRules(
    const int* intgrid_data, int width, int height,
    const AutoRuleSet& ruleset, uint32_t seed)
{
    int total = width * height;
    std::vector<AutoTileResult> result(total, {-1, 0});

    for (const auto& group : ruleset.groups) {
        if (!group.active) continue;

        // Per-group break mask: once a cell is matched by a breakOnMatch rule,
        // skip it for subsequent rules in this group
        std::vector<bool> break_mask(total, false);

        for (const auto& rule : group.rules) {
            if (!rule.active) continue;
            if (rule.tile_ids.empty()) continue;
            if (rule.pattern.empty()) continue;

            // Build flip variants: (pattern, flip_bits)
            struct Variant {
                std::vector<int> pattern;
                int flip_bits;
            };
            std::vector<Variant> variants;
            variants.push_back({rule.pattern, 0});

            if (rule.flipX) {
                std::vector<int> fx = flipPatternX(rule.pattern, rule.size);
                variants.push_back({fx, 1});
            }
            if (rule.flipY) {
                std::vector<int> fy = flipPatternY(rule.pattern, rule.size);
                variants.push_back({fy, 2});
            }
            if (rule.flipX && rule.flipY) {
                std::vector<int> fxy = flipPatternY(
                    flipPatternX(rule.pattern, rule.size), rule.size);
                variants.push_back({fxy, 3});
            }

            for (int y = 0; y < height; y++) {
                for (int x = 0; x < width; x++) {
                    int idx = y * width + x;
                    if (break_mask[idx]) continue;

                    // Probability check (deterministic)
                    if (rule.chance < 1.0f) {
                        uint32_t h = hashCell(seed, x, y, rule.uid);
                        float roll = static_cast<float>(h & 0xFFFF) / 65535.0f;
                        if (roll >= rule.chance) continue;
                    }

                    // Try each variant (first match wins)
                    for (const auto& variant : variants) {
                        if (matchPattern(intgrid_data, width, height,
                                         x, y, variant.pattern, rule.size,
                                         rule.outOfBoundsValue))
                        {
                            // Pick tile (deterministic from seed)
                            int tile_idx = 0;
                            if (rule.tile_ids.size() > 1) {
                                uint32_t h = hashCell(seed, x, y, rule.uid + 1);
                                tile_idx = h % rule.tile_ids.size();
                            }

                            result[idx].tile_id = rule.tile_ids[tile_idx];
                            result[idx].flip = variant.flip_bits;

                            if (rule.breakOnMatch) {
                                break_mask[idx] = true;
                            }
                            break; // First matching variant wins
                        }
                    }
                }
            }
        }
    }

    return result;
}

} // namespace ldtk
} // namespace mcrf
