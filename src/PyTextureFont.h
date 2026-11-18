#pragma once
// #547: the data a Texture built by Texture.from_font carries besides its pixels:
// the codepoint <-> tile tables, the reserved tiles and the font's line metrics.
// EXPERIMENTAL (not part of the 1.0 freeze).
#include <cstdint>
#include <unordered_map>
#include <vector>

struct FontAtlasData {
    // Faces, in the order their tiles appear in the atlas. Values are stable (used in keys).
    enum Face : uint8_t { REGULAR = 0, BOLD = 1, ITALIC = 2 };

    // What one tile holds.
    struct Tile {
        enum Kind : uint8_t { BOX, WHITE, GLYPH, GLYPH_RIGHT, UNUSED } kind = UNUSED;
        uint32_t codepoint = 0;   // GLYPH / GLYPH_RIGHT
        Face face = REGULAR;      // GLYPH / GLYPH_RIGHT
    };

    int cell_w = 0, cell_h = 0;
    // Line metrics in pixels, measured from the top of a cell (so they can be drawn directly).
    int ascent = 0;                // top of the cell to the baseline
    int underline_position = 0;    // top of the underline stripe
    int underline_thickness = 1;
    int strikethrough_position = 0;
    int strikethrough_thickness = 1;

    int box_tile = 0;
    int white_tile = 1;
    bool has_bold = false, has_italic = false;

    std::vector<Tile> tiles;                       // indexed by tile; padding tiles are UNUSED
    std::unordered_map<uint64_t, int> index;       // (face, codepoint) -> tile (left half if wide)

    // Regular face only; ascending, deduplicated.
    std::vector<uint32_t> missing, clipped;
    // Faces other than regular.
    struct VariantEntry { uint32_t codepoint; Face face; };
    std::vector<VariantEntry> variant_missing, variant_clipped;

    static uint64_t key(Face f, uint32_t cp) { return ((uint64_t)f << 32) | cp; }
};
