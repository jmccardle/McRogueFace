// #547: Texture.from_font -- a static tile atlas rasterised from a Font, with codepoint <-> tile
// lookup, a reserved box tile and solid white tile, and the font's line metrics.
// EXPERIMENTAL: this surface is not part of the 1.0 freeze.
//
// Rasterisation is FreeType directly, on every backend: the SFML build opens a second FT_Face
// on the font file (PyFont::metrics_face) and the SDL2/web build already holds one in sf::Font
// (getFTFace()). Both are reached through PyFont::ftFace(). An MCRF_HEADLESS build has no
// rasteriser and raises.
#include "PyTexture.h"
#include "PyTextureFont.h"
#include "PyFont.h"
#include "EastAsianWide.h"
#include "Display.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"
#include <algorithm>
#include <cmath>
#include <set>

#if !defined(MCRF_HEADLESS)
#include <ft2build.h>
#include FT_FREETYPE_H
#include FT_TRUETYPE_TABLES_H
#endif

namespace {

constexpr uint32_t MAX_CODEPOINT = 0x10FFFF;

// Wide in a terminal cell (generated table, libghostty-vt's width rule; #550): these glyphs
// take two cells, a left and a right tile.
bool is_wide_codepoint(uint32_t cp)
{
    const auto* first = EAST_ASIAN_WIDE_RANGES;
    const auto* last = first + sizeof(EAST_ASIAN_WIDE_RANGES) / sizeof(EAST_ASIAN_WIDE_RANGES[0]);
    // first range whose hi >= cp
    const auto* it = std::lower_bound(first, last, cp,
        [](const EastAsianWideRange& r, uint32_t c) { return r.hi < c; });
    return it != last && cp >= it->lo;
}

// One codepoint: an int, or a str of exactly one character. Sets a Python error on failure.
bool parse_codepoint(PyObject* o, uint32_t& out, const char* what)
{
    if (PyBool_Check(o)) {
        PyErr_Format(PyExc_TypeError, "%s must be a single character or an int, not a bool", what);
        return false;
    }
    if (PyUnicode_Check(o)) {
        if (PyUnicode_GET_LENGTH(o) != 1) {
            PyErr_Format(PyExc_ValueError, "%s must be a single character or an int, got a str of length %zd",
                         what, PyUnicode_GET_LENGTH(o));
            return false;
        }
        out = PyUnicode_READ_CHAR(o, 0);
    } else if (PyLong_Check(o)) {
        long v = PyLong_AsLong(o);
        if (v == -1 && PyErr_Occurred()) return false;
        if (v < 0 || v > (long)MAX_CODEPOINT) {
            PyErr_Format(PyExc_ValueError, "%s 0x%lX is outside 0..0x10FFFF", what, v);
            return false;
        }
        out = (uint32_t)v;
    } else {
        PyErr_Format(PyExc_TypeError, "%s must be a single character or an int, not %.100s",
                     what, Py_TYPE(o)->tp_name);
        return false;
    }
    if (out >= 0xD800 && out <= 0xDFFF) {
        PyErr_Format(PyExc_ValueError, "%s 0x%X is a surrogate, not a character", what, out);
        return false;
    }
    return true;
}

// codepoints: a str (each character), or an iterable of items, each an int, a 1-char str, or a
// (first, last) pair (inclusive) of those.
bool parse_codepoints(PyObject* spec, std::set<uint32_t>& out)
{
    if (PyUnicode_Check(spec)) {
        for (Py_ssize_t i = 0; i < PyUnicode_GET_LENGTH(spec); i++) {
            uint32_t cp = PyUnicode_READ_CHAR(spec, i);
            if (cp >= 0xD800 && cp <= 0xDFFF) {
                PyErr_Format(PyExc_ValueError, "codepoints contains a surrogate 0x%X", cp);
                return false;
            }
            out.insert(cp);
        }
        return true;
    }
    if (PyTuple_Check(spec) && PyTuple_GET_SIZE(spec) == 2 &&
        !PySequence_Check(PyTuple_GET_ITEM(spec, 0)) && !PySequence_Check(PyTuple_GET_ITEM(spec, 1)) &&
        PyLong_Check(PyTuple_GET_ITEM(spec, 0)) && PyLong_Check(PyTuple_GET_ITEM(spec, 1))) {
        PyErr_SetString(PyExc_TypeError,
            "codepoints is a bare (a, b) tuple, which is ambiguous: write [(a, b)] for the range a..b, "
            "or [a, b] for the two codepoints a and b");
        return false;
    }
    PyObject* it = PyObject_GetIter(spec);
    if (!it) {
        PyErr_SetString(PyExc_TypeError,
            "codepoints must be a str or an iterable of ints, characters and (first, last) pairs");
        return false;
    }
    bool ok = true;
    while (ok) {
        PyObject* item = PyIter_Next(it);
        if (!item) { if (PyErr_Occurred()) ok = false; break; }
        if (PyTuple_Check(item) || PyList_Check(item)) {
            PyObject* seq = PySequence_Fast(item, "codepoints range");
            if (!seq) { ok = false; }
            else if (PySequence_Fast_GET_SIZE(seq) != 2) {
                PyErr_Format(PyExc_ValueError, "a codepoints range must be a (first, last) pair, got %zd items",
                             PySequence_Fast_GET_SIZE(seq));
                ok = false;
            } else {
                uint32_t lo, hi;
                ok = parse_codepoint(PySequence_Fast_GET_ITEM(seq, 0), lo, "range start")
                  && parse_codepoint(PySequence_Fast_GET_ITEM(seq, 1), hi, "range end");
                if (ok && lo > hi) {
                    PyErr_Format(PyExc_ValueError, "codepoints range 0x%X..0x%X is backwards", lo, hi);
                    ok = false;
                }
                if (ok) for (uint32_t c = lo; c <= hi; c++)
                    if (c < 0xD800 || c > 0xDFFF) out.insert(c);
            }
            Py_XDECREF(seq);
        } else {
            uint32_t cp;
            ok = parse_codepoint(item, cp, "codepoint");
            if (ok) out.insert(cp);
        }
        Py_DECREF(item);
    }
    Py_DECREF(it);
    if (ok && out.empty()) {
        PyErr_SetString(PyExc_ValueError, "codepoints is empty");
        return false;
    }
    return ok;
}

#if !defined(MCRF_HEADLESS)

// A font face being rasterised at one pixel size.
struct Rasteriser {
    FT_Face face = nullptr;
    PyFont* font = nullptr;
    const char* label = "";
    unsigned size = 0;

    bool select()
    {
        if (FT_Set_Pixel_Sizes(face, 0, size) != 0) {
            PyErr_Format(PyExc_ValueError, "%s font has no %u px size", label, size);
            return false;
        }
        return true;
    }
};

bool open_rasteriser(Rasteriser& r, PyObject* font_obj, const char* label, unsigned size)
{
    if (!PyObject_TypeCheck(font_obj, &mcrfpydef::PyFontType)) {
        PyErr_Format(PyExc_TypeError, "%s must be a Font, not %.100s", label, Py_TYPE(font_obj)->tp_name);
        return false;
    }
    auto& pf = ((PyFontObject*)font_obj)->data;
    if (!pf || !pf->loaded()) {
        PyErr_Format(PyExc_ValueError, "%s font did not load", label);
        return false;
    }
    r.font = pf.get();
    r.face = static_cast<FT_Face>(pf->ftFace());
    if (!r.face) {
        PyErr_Format(PyExc_RuntimeError, "%s font has no FreeType face to rasterise from", label);
        return false;
    }
    r.label = label;
    r.size = size;
    return r.select();
}

// A glyph rendered to 8-bit coverage in a canvas of `cells` cells.
struct Canvas {
    int w, h;
    std::vector<uint8_t> a;  // alpha only; the RGB of every glyph pixel is white
    Canvas(int w_, int h_) : w(w_), h(h_), a((size_t)w_ * h_, 0) {}
};

// Renders cp (glyph index gi) with its origin at (0, baseline). Sets *clipped when a visible
// pixel falls outside the canvas. False with a Python error on failure.
bool render_glyph(Rasteriser& r, uint32_t cp, FT_UInt gi, int baseline, Canvas& cv, bool* clipped)
{
    if (FT_Load_Glyph(r.face, gi, FT_LOAD_RENDER) != 0) {
        PyErr_Format(PyExc_ValueError, "%s font: could not rasterise U+%04X", r.label, cp);
        return false;
    }
    FT_GlyphSlot g = r.face->glyph;
    FT_Bitmap& bm = g->bitmap;
    if (bm.pixel_mode != FT_PIXEL_MODE_GRAY && bm.pixel_mode != FT_PIXEL_MODE_MONO) {
        if (bm.width == 0 || bm.rows == 0) return true;
        PyErr_Format(PyExc_ValueError,
            "%s font: U+%04X has a colour/unsupported bitmap format (pixel mode %d); "
            "from_font builds white-on-transparent glyphs from outline or gray/mono bitmaps",
            r.label, cp, (int)bm.pixel_mode);
        return false;
    }
    if (bm.pitch < 0) {
        PyErr_Format(PyExc_ValueError, "%s font: U+%04X bitmap is bottom-up", r.label, cp);
        return false;
    }
    *clipped = false;
    for (unsigned row = 0; row < bm.rows; row++) {
        const unsigned char* src = bm.buffer + (size_t)row * bm.pitch;
        for (unsigned col = 0; col < bm.width; col++) {
            uint8_t v = bm.pixel_mode == FT_PIXEL_MODE_GRAY
                      ? src[col] : ((src[col >> 3] & (0x80 >> (col & 7))) ? 255 : 0);
            if (!v) continue;
            int x = g->bitmap_left + (int)col;
            int y = baseline - g->bitmap_top + (int)row;
            if (x < 0 || y < 0 || x >= cv.w || y >= cv.h) { *clipped = true; continue; }
            cv.a[(size_t)y * cv.w + x] = v;
        }
    }
    return true;
}

#endif  // !MCRF_HEADLESS

const char* face_name(FontAtlasData::Face f)
{
    return f == FontAtlasData::BOLD ? "bold" : f == FontAtlasData::ITALIC ? "italic" : "regular";
}

}  // namespace

// ---------------------------------------------------------------------------
// Texture.from_font
// ---------------------------------------------------------------------------
std::shared_ptr<PyTexture> PyTexture::from_font_atlas(const sf::Image& img, std::unique_ptr<FontAtlasData> data,
                                                      const std::string& name)
{
    auto ptex = PyTexture::from_image(img, data->cell_w, data->cell_h, name);
    if (!ptex) return nullptr;
    ptex->font_atlas = std::move(data);
    return ptex;
}

PyObject* PyTexture::from_font(PyObject* cls, PyObject* args, PyObject* kwds)
{
    if (!mcrf::require_display_py("Texture.from_font()")) return NULL;  // #451: the atlas is a GL texture
    static const char* keywords[] = {"font", "size", "codepoints", "cell", "bold", "italic", nullptr};
    PyObject *font_obj, *cp_spec = nullptr, *cell_obj = nullptr, *bold_obj = nullptr, *italic_obj = nullptr;
    int size;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "Oi|OOOO", const_cast<char**>(keywords),
            &font_obj, &size, &cp_spec, &cell_obj, &bold_obj, &italic_obj))
        return NULL;
#if defined(MCRF_HEADLESS)
    PyErr_SetString(PyExc_RuntimeError, "Texture.from_font() is not available in an MCRF_HEADLESS build (no font rasterizer)");
    return NULL;
#else
    if (size < 1 || size > 2048) {
        PyErr_Format(PyExc_ValueError, "size must be between 1 and 2048 pixels, got %d", size);
        return NULL;
    }

    std::set<uint32_t> codepoints;
    if (!cp_spec || cp_spec == Py_None) {
        for (uint32_t c = 0x20; c <= 0x7E; c++) codepoints.insert(c);
        for (uint32_t c = 0x2500; c <= 0x257F; c++) codepoints.insert(c);
    } else if (!parse_codepoints(cp_spec, codepoints)) {
        return NULL;
    }

    int req_cell_w = 0, req_cell_h = 0;
    if (cell_obj && cell_obj != Py_None) {
        if (!(PyTuple_Check(cell_obj) || PyList_Check(cell_obj)) || PySequence_Size(cell_obj) != 2) {
            PyErr_SetString(PyExc_TypeError, "cell must be a (width, height) tuple of ints");
            return NULL;
        }
        PyObject* cw_o = PySequence_GetItem(cell_obj, 0);
        PyObject* ch_o = PySequence_GetItem(cell_obj, 1);
        bool good = cw_o && ch_o && PyLong_Check(cw_o) && PyLong_Check(ch_o) &&
                    !PyBool_Check(cw_o) && !PyBool_Check(ch_o);
        long lw = 0, lh = 0;
        int ovw = 0, ovh = 0;
        if (good) {
            lw = PyLong_AsLongAndOverflow(cw_o, &ovw);
            if (lw == -1 && PyErr_Occurred()) good = false;
            else {
                lh = PyLong_AsLongAndOverflow(ch_o, &ovh);
                if (lh == -1 && PyErr_Occurred()) good = false;
            }
        }
        Py_XDECREF(cw_o); Py_XDECREF(ch_o);
        if (!good) {
            if (!PyErr_Occurred()) PyErr_SetString(PyExc_TypeError, "cell must be a (width, height) tuple of ints");
            return NULL;
        }
        if (ovw || ovh || lw < 1 || lh < 1 || lw > 1024 || lh > 1024) {
            PyErr_SetString(PyExc_ValueError, "cell must be between 1x1 and 1024x1024 pixels");
            return NULL;
        }
        req_cell_w = (int)lw;
        req_cell_h = (int)lh;
    }

    Rasteriser faces[3];
    bool have[3] = {true, false, false};
    if (!open_rasteriser(faces[FontAtlasData::REGULAR], font_obj, "font", size)) return NULL;
    if (bold_obj && bold_obj != Py_None) {
        if (!open_rasteriser(faces[FontAtlasData::BOLD], bold_obj, "bold", size)) return NULL;
        have[FontAtlasData::BOLD] = true;
    }
    if (italic_obj && italic_obj != Py_None) {
        if (!open_rasteriser(faces[FontAtlasData::ITALIC], italic_obj, "italic", size)) return NULL;
        have[FontAtlasData::ITALIC] = true;
    }
    Rasteriser& reg = faces[FontAtlasData::REGULAR];

    // Glyph indices per face, advances from the regular face (they set the default cell width).
    struct Entry { uint32_t cp; bool wide; FT_UInt gi[3]; };
    std::vector<Entry> entries;
    auto data = std::make_unique<FontAtlasData>();
    double max_adv = 0, max_wide_adv = 0;
    for (uint32_t cp : codepoints) {
        Entry e{cp, is_wide_codepoint(cp), {0, 0, 0}};
        for (int f = 0; f < 3; f++)
            if (have[f]) e.gi[f] = FT_Get_Char_Index(faces[f].face, cp);
        if (!e.gi[0]) {
            data->missing.push_back(cp);
        } else {
            if (!reg.select()) return NULL;
            if (FT_Load_Glyph(reg.face, e.gi[0], FT_LOAD_DEFAULT) != 0) {
                PyErr_Format(PyExc_ValueError, "font: could not measure U+%04X", cp);
                return NULL;
            }
            double adv = reg.face->glyph->advance.x / 64.0;
            (e.wide ? max_wide_adv : max_adv) = std::max(e.wide ? max_wide_adv : max_adv, adv);
        }
        for (int f = 1; f < 3; f++)
            if (have[f] && !e.gi[f]) data->variant_missing.push_back({cp, (FontAtlasData::Face)f});
        entries.push_back(e);
    }
    {
        bool any = false;
        for (auto& e : entries) any = any || e.gi[0] || e.gi[1] || e.gi[2];
        if (!any) {
            PyErr_SetString(PyExc_ValueError, "none of the requested codepoints are in any of the fonts");
            return NULL;
        }
    }

    // Cell: line height x widest (single-cell) advance, unless given.
    if (!reg.select()) return NULL;
    PyFont::Metrics m;
    if (!reg.font->metricsOrRaise((unsigned)size, m)) return NULL;
    if (!reg.select()) return NULL;  // metrics() leaves the face at its own size; be explicit
    double adv_for_cell = max_adv > 0 ? max_adv : max_wide_adv / 2.0;
    if (adv_for_cell <= 0 && !req_cell_w) {
        PyErr_SetString(PyExc_ValueError, "no requested codepoint is in the font, so there is no advance to size the cell from; pass cell=");
        return NULL;
    }
    int cw = req_cell_w ? req_cell_w : (int)std::ceil(adv_for_cell);
    int ch = req_cell_h ? req_cell_h : (int)std::ceil(m.line_height);
    if (cw < 1) cw = 1;
    if (ch < 1) ch = 1;
    data->cell_w = cw;
    data->cell_h = ch;
    int baseline = (int)std::floor(m.ascent + (ch - m.line_height) / 2.0 + 0.5);
    data->ascent = baseline;

    // Line metrics, taken from the regular face at this size (px from the top of the cell).
    {
        FT_Face face = reg.face;
        if (!FT_IS_SCALABLE(face)) {
            PyErr_SetString(PyExc_ValueError, "font is not scalable: no line metrics");
            return NULL;
        }
        double y_scale = face->size->metrics.y_scale / 65536.0 / 64.0;  // font units -> px
        double ul_pos = face->underline_position * y_scale;
        double ul_th = face->underline_thickness * y_scale;
        data->underline_thickness = std::max(1, (int)std::lround(ul_th));
        data->underline_position = (int)std::lround(baseline - ul_pos - ul_th / 2.0);
        TT_OS2* os2 = static_cast<TT_OS2*>(FT_Get_Sfnt_Table(face, FT_SFNT_OS2));
        if (!os2) {
            PyErr_SetString(PyExc_ValueError,
                "font has no OS/2 table, so it has no strike-through metrics");
            return NULL;
        }
        data->strikethrough_thickness = std::max(1, (int)std::lround(os2->yStrikeoutSize * y_scale));
        data->strikethrough_position = (int)std::lround(baseline - os2->yStrikeoutPosition * y_scale);
        // The stripes are drawn inside a cell: keep them there (ascent stays truthful; glyph
        // overflow is reported through clipped).
        auto fit = [&](int& pos, int& thick) {
            thick = std::min(std::max(thick, 1), ch);
            pos = std::min(std::max(pos, 0), ch - thick);
        };
        fit(data->underline_position, data->underline_thickness);
        fit(data->strikethrough_position, data->strikethrough_thickness);
    }

    // Layout: tile 0 box, tile 1 white, then regular glyphs, bold glyphs, italic glyphs.
    struct Placed { size_t entry; FontAtlasData::Face face; int tile; };
    std::vector<Placed> placed;
    data->tiles.push_back({FontAtlasData::Tile::BOX});
    data->tiles.push_back({FontAtlasData::Tile::WHITE});
    data->box_tile = 0;
    data->white_tile = 1;
    for (int f = 0; f < 3; f++) {
        if (!have[f]) continue;
        for (size_t i = 0; i < entries.size(); i++) {
            if (!entries[i].gi[f]) continue;
            int tile = (int)data->tiles.size();
            data->index[FontAtlasData::key((FontAtlasData::Face)f, entries[i].cp)] = tile;
            data->tiles.push_back({FontAtlasData::Tile::GLYPH, entries[i].cp, (FontAtlasData::Face)f});
            if (entries[i].wide)
                data->tiles.push_back({FontAtlasData::Tile::GLYPH_RIGHT, entries[i].cp, (FontAtlasData::Face)f});
            placed.push_back({i, (FontAtlasData::Face)f, tile});
        }
    }
    data->has_bold = have[FontAtlasData::BOLD];
    data->has_italic = have[FontAtlasData::ITALIC];

    size_t n = data->tiles.size();
    unsigned max_tex = sf::Texture::getMaximumSize();
    int cols = (int)std::ceil(std::sqrt((double)n * ch / cw));
    cols = std::max(1, std::min(cols, (int)n));
    cols = std::min(cols, std::max(1, (int)(max_tex / cw)));
    int rows = (int)((n + cols - 1) / cols);
    if ((unsigned)cols * cw > max_tex || (unsigned)rows * ch > max_tex) {
        PyErr_Format(PyExc_ValueError,
            "%zu tiles of %dx%d px do not fit in a texture of at most %ux%u; request fewer codepoints or a smaller size",
            n, cw, ch, max_tex, max_tex);
        return NULL;
    }
    data->tiles.resize((size_t)cols * rows);  // padding tiles stay UNUSED

    sf::Image img;
    img.create((unsigned)cols * cw, (unsigned)rows * ch, sf::Color::Transparent);
    auto put = [&](int tile, int x, int y, uint8_t a) {
        img.setPixel((unsigned)((tile % cols) * cw + x), (unsigned)((tile / cols) * ch + y), sf::Color(255, 255, 255, a));
    };
    // box: a 1 px outline, inset one pixel when the cell is big enough
    {
        int inset = (cw >= 4 && ch >= 4) ? 1 : 0;
        for (int x = inset; x < cw - inset; x++) { put(0, x, inset, 255); put(0, x, ch - 1 - inset, 255); }
        for (int y = inset; y < ch - inset; y++) { put(0, inset, y, 255); put(0, cw - 1 - inset, y, 255); }
    }
    for (int y = 0; y < ch; y++) for (int x = 0; x < cw; x++) put(1, x, y, 255);

    for (auto& p : placed) {
        const Entry& e = entries[p.entry];
        Rasteriser& r = faces[p.face];
        if (!r.select()) return NULL;
        int ncells = e.wide ? 2 : 1;
        Canvas cv(cw * ncells, ch);
        bool clip = false;
        if (!render_glyph(r, e.cp, e.gi[p.face], baseline, cv, &clip)) return NULL;
        if (clip) {
            if (p.face == FontAtlasData::REGULAR) data->clipped.push_back(e.cp);
            else data->variant_clipped.push_back({e.cp, p.face});
        }
        for (int c = 0; c < ncells; c++)
            for (int y = 0; y < ch; y++) for (int x = 0; x < cw; x++) {
                uint8_t a = cv.a[(size_t)y * cv.w + c * cw + x];
                if (a) put(p.tile + c, x, y, a);
            }
    }

    std::string name = "<font:" + reg.font->sourcePath() + "@" + std::to_string(size) + ">";
    auto ptex = PyTexture::from_font_atlas(img, std::move(data), name);
    if (!ptex) return NULL;
    return PyTexture::pyobject_for(ptex);
#endif
}

// ---------------------------------------------------------------------------
// Lookups and reports
// ---------------------------------------------------------------------------
static FontAtlasData* font_atlas_or_raise(PyTextureObject* self)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Texture has invalid internal data");
        return nullptr;
    }
    if (!self->data->font_atlas) {
        PyErr_SetString(PyExc_ValueError, "this Texture was not built by Texture.from_font()");
        return nullptr;
    }
    return self->data->font_atlas.get();
}

// Properties are None on a texture that is not a font atlas.
#define FONT_ATLAS_OR_NONE(self) \
    if (!(self)->data) { PyErr_SetString(PyExc_RuntimeError, "Texture has invalid internal data"); return NULL; } \
    FontAtlasData* fa = (self)->data->font_atlas.get(); \
    if (!fa) Py_RETURN_NONE;

PyObject* PyTexture::py_index(PyTextureObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"codepoint", "bold", "italic", nullptr};
    PyObject* cp_obj;
    int bold = 0, italic = 0;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|pp", const_cast<char**>(keywords), &cp_obj, &bold, &italic))
        return NULL;
    FontAtlasData* fa = font_atlas_or_raise(self);
    if (!fa) return NULL;
    uint32_t cp;
    if (!parse_codepoint(cp_obj, cp, "codepoint")) return NULL;
    // Faces to try, best first. A face the texture lacks, or that lacks this codepoint, falls
    // through to the next: the regular tile comes back and the caller (TerminalLayer) fakes the
    // style, having checked glyph(tile) / variants. Bold wins over italic when both are asked for;
    // there is no bold-italic face. Only when no usable face has the glyph is it the box tile.
    FontAtlasData::Face order[3];
    int n = 0;
    if (bold && fa->has_bold) order[n++] = FontAtlasData::BOLD;
    if (italic && fa->has_italic) order[n++] = FontAtlasData::ITALIC;
    order[n++] = FontAtlasData::REGULAR;
    for (int i = 0; i < n; i++) {
        auto it = fa->index.find(FontAtlasData::key(order[i], cp));
        if (it != fa->index.end()) return PyLong_FromLong(it->second);
    }
    return PyLong_FromLong(fa->box_tile);
}

PyObject* PyTexture::py_glyph(PyTextureObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"tile", nullptr};
    int tile;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "i", const_cast<char**>(keywords), &tile)) return NULL;
    FontAtlasData* fa = font_atlas_or_raise(self);
    if (!fa) return NULL;
    if (tile < 0 || (size_t)tile >= fa->tiles.size()) {
        PyErr_Format(PyExc_IndexError, "tile %d is outside 0..%zu", tile, fa->tiles.size() - 1);
        return NULL;
    }
    const auto& t = fa->tiles[tile];
    if (t.kind != FontAtlasData::Tile::GLYPH) Py_RETURN_NONE;
    return Py_BuildValue("(IOO)", t.codepoint,
                         t.face == FontAtlasData::BOLD ? Py_True : Py_False,
                         t.face == FontAtlasData::ITALIC ? Py_True : Py_False);
}

PyObject* PyTexture::py_is_wide(PyTextureObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"codepoint", nullptr};
    PyObject* cp_obj;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O", const_cast<char**>(keywords), &cp_obj)) return NULL;
    FontAtlasData* fa = font_atlas_or_raise(self);
    if (!fa) return NULL;
    uint32_t cp;
    if (!parse_codepoint(cp_obj, cp, "codepoint")) return NULL;
    bool wide = is_wide_codepoint(cp);  // the codepoint only: the same answer whether or not the texture has the glyph
    return PyBool_FromLong(wide);
}

static PyObject* codepoint_list(const std::vector<uint32_t>& v)
{
    PyObject* l = PyList_New((Py_ssize_t)v.size());
    if (!l) return NULL;
    for (size_t i = 0; i < v.size(); i++) {
        PyObject* o = PyLong_FromUnsignedLong(v[i]);
        if (!o) { Py_DECREF(l); return NULL; }
        PyList_SET_ITEM(l, (Py_ssize_t)i, o);
    }
    return l;
}

static PyObject* variant_list(const std::vector<FontAtlasData::VariantEntry>& v)
{
    PyObject* l = PyList_New((Py_ssize_t)v.size());
    if (!l) return NULL;
    for (size_t i = 0; i < v.size(); i++) {
        PyObject* o = Py_BuildValue("(IOO)", v[i].codepoint,
                                    v[i].face == FontAtlasData::BOLD ? Py_True : Py_False,
                                    v[i].face == FontAtlasData::ITALIC ? Py_True : Py_False);
        if (!o) { Py_DECREF(l); return NULL; }
        PyList_SET_ITEM(l, (Py_ssize_t)i, o);
    }
    return l;
}

PyObject* PyTexture::get_missing(PyTextureObject* self, void*) { FONT_ATLAS_OR_NONE(self); return codepoint_list(fa->missing); }
PyObject* PyTexture::get_clipped(PyTextureObject* self, void*) { FONT_ATLAS_OR_NONE(self); return codepoint_list(fa->clipped); }
PyObject* PyTexture::get_variant_missing(PyTextureObject* self, void*) { FONT_ATLAS_OR_NONE(self); return variant_list(fa->variant_missing); }
PyObject* PyTexture::get_variant_clipped(PyTextureObject* self, void*) { FONT_ATLAS_OR_NONE(self); return variant_list(fa->variant_clipped); }
PyObject* PyTexture::get_white_tile(PyTextureObject* self, void*) { FONT_ATLAS_OR_NONE(self); return PyLong_FromLong(fa->white_tile); }
PyObject* PyTexture::get_box_tile(PyTextureObject* self, void*) { FONT_ATLAS_OR_NONE(self); return PyLong_FromLong(fa->box_tile); }
PyObject* PyTexture::get_ascent(PyTextureObject* self, void*) { FONT_ATLAS_OR_NONE(self); return PyLong_FromLong(fa->ascent); }
PyObject* PyTexture::get_underline_position(PyTextureObject* self, void*) { FONT_ATLAS_OR_NONE(self); return PyLong_FromLong(fa->underline_position); }
PyObject* PyTexture::get_underline_thickness(PyTextureObject* self, void*) { FONT_ATLAS_OR_NONE(self); return PyLong_FromLong(fa->underline_thickness); }
PyObject* PyTexture::get_strikethrough_position(PyTextureObject* self, void*) { FONT_ATLAS_OR_NONE(self); return PyLong_FromLong(fa->strikethrough_position); }
PyObject* PyTexture::get_strikethrough_thickness(PyTextureObject* self, void*) { FONT_ATLAS_OR_NONE(self); return PyLong_FromLong(fa->strikethrough_thickness); }

PyObject* PyTexture::get_variants(PyTextureObject* self, void*)
{
    FONT_ATLAS_OR_NONE(self);
    PyObject* t = PyTuple_New(1 + (fa->has_bold ? 1 : 0) + (fa->has_italic ? 1 : 0));
    if (!t) return NULL;
    Py_ssize_t i = 0;
    FontAtlasData::Face present[3] = {FontAtlasData::REGULAR, FontAtlasData::BOLD, FontAtlasData::ITALIC};
    bool has[3] = {true, fa->has_bold, fa->has_italic};
    for (int f = 0; f < 3; f++) {
        if (!has[f]) continue;
        PyObject* name = PyUnicode_FromString(face_name(present[f]));
        if (!name) { Py_DECREF(t); return NULL; }
        PyTuple_SET_ITEM(t, i++, name);
    }
    return t;
}
