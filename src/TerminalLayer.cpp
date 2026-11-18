// #550: TerminalLayer -- see TerminalLayer.h. EXPERIMENTAL (not part of the 1.0 freeze).
#include "TerminalLayer.h"

#include <ghostty/vt.h>

#include <algorithm>
#include <climits>
#include <cmath>
#include <sstream>
#include <stdexcept>
#include <unordered_set>

#include "EastAsianWide.h"
#include "GameEngine.h"
#include "GridData.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"
#include "PyColor.h"
#include "PyInputState.h"
#include "PyKey.h"
#include "PyMouseButton.h"
#include "PyPositionHelper.h"
#include "PyFont.h"
#include "PyTexture.h"
#include "PyWrap.h"
#include "Resources.h"
#include "UIGridView.h"

static_assert(TerminalLayer::CF_OVERLINE < (1u << 16), "cell flags fit 16 bits");

// =============================================================================
// Helpers
// =============================================================================

namespace {

// Every library result goes through here: anything but success throws, naming the call.
void ck(GhosttyResult r, const char* call) {
    if (r != GHOSTTY_SUCCESS)
        throw std::runtime_error(std::string("libghostty-vt: ") + call + " failed with GhosttyResult " +
                                 std::to_string(static_cast<int>(r)));
}

sf::Color rgb(const GhosttyColorRgb& c) { return sf::Color(c.r, c.g, c.b, 255); }

// The engine clock the timers run on (headless: the simulation clock step() advances).
int engineNowMs() {
    GameEngine* g = Resources::game;
    if (!g) return 0;
    return g->isHeadless() ? g->getSimulationTime() : g->runtime.getElapsedTime().asMilliseconds();
}

constexpr int kHoldTimeoutMs = 1000;   // a synchronized-output hold longer than this is ended

void appendUtf8(std::string& out, uint32_t cp) {
    if (cp < 0x80) out += static_cast<char>(cp);
    else if (cp < 0x800) {
        out += static_cast<char>(0xC0 | (cp >> 6));
        out += static_cast<char>(0x80 | (cp & 0x3F));
    } else if (cp < 0x10000) {
        out += static_cast<char>(0xE0 | (cp >> 12));
        out += static_cast<char>(0x80 | ((cp >> 6) & 0x3F));
        out += static_cast<char>(0x80 | (cp & 0x3F));
    } else {
        out += static_cast<char>(0xF0 | (cp >> 18));
        out += static_cast<char>(0x80 | ((cp >> 12) & 0x3F));
        out += static_cast<char>(0x80 | ((cp >> 6) & 0x3F));
        out += static_cast<char>(0x80 | (cp & 0x3F));
    }
}

// Never destroyed: a layer released during interpreter teardown, after static destructors
// have started, must still find it.
std::unordered_set<TerminalLayer*>& blinkRegistry() {
    static auto* layers = new std::unordered_set<TerminalLayer*>();
    return *layers;
}

// The tile a cell shows for codepoint `cp` in the requested style. Sets CF_FAKE_* when the
// atlas has no glyph in that face (the painter fakes the style instead).
int resolveTile(const FontAtlasData& fa, uint32_t cp, bool bold, bool italic, uint16_t& flags) {
    if (bold && fa.has_bold) {
        auto it = fa.index.find(FontAtlasData::key(FontAtlasData::BOLD, cp));
        if (it != fa.index.end()) {
            if (italic) flags |= TerminalLayer::CF_FAKE_ITALIC;
            return it->second;
        }
    }
    if (italic && fa.has_italic) {
        auto it = fa.index.find(FontAtlasData::key(FontAtlasData::ITALIC, cp));
        if (it != fa.index.end()) {
            if (bold) flags |= TerminalLayer::CF_FAKE_BOLD;
            return it->second;
        }
    }
    auto it = fa.index.find(FontAtlasData::key(FontAtlasData::REGULAR, cp));
    if (it == fa.index.end()) return fa.box_tile;   // a codepoint the atlas lacks: the box
    if (bold) flags |= TerminalLayer::CF_FAKE_BOLD;
    if (italic) flags |= TerminalLayer::CF_FAKE_ITALIC;
    return it->second;
}

}  // namespace

// =============================================================================
// libghostty callbacks: plain C, run synchronously inside library calls. Nothing may
// unwind through the library, so failures are recorded and reported by the caller.
// =============================================================================

struct TerminalLayer::Callbacks {
    static void writePty(GhosttyTerminal, void* userdata, const uint8_t* data, size_t len) {
        auto* self = static_cast<TerminalLayer*>(userdata);
        try {
            self->pending_output.append(reinterpret_cast<const char*>(data), len);
        } catch (...) {
            self->callback_failed_ = true;
        }
    }
    static void renderHold(GhosttyTerminal, void* userdata, bool held) {
        auto* self = static_cast<TerminalLayer*>(userdata);
        if (held) {
            // Capture the frame the program wants left on screen while it draws the next one.
            if (ghostty_render_state_update(self->rs_, self->term_) != GHOSTTY_SUCCESS) {
                self->callback_failed_ = true;
                return;
            }
            self->hold_start_ms_ = engineNowMs();
        }
        self->held_ = held;
        self->needs_sync_ = true;
    }
};

// =============================================================================
// Lifecycle
// =============================================================================

TerminalLayer::TerminalLayer(int z_index, int cols, int rows, std::shared_ptr<PyTexture> tex, size_t scrollback)
    : TileLayer(z_index, cols, rows, nullptr, std::move(tex)), scrollback_(scrollback)
{
    fg_.assign(static_cast<size_t>(cols) * rows, sf::Color::White);
    bg_.assign(static_cast<size_t>(cols) * rows, sf::Color::Black);
    flags_.assign(static_cast<size_t>(cols) * rows, CF_DEFAULT_BG);
    chunk_blink_.assign(chunk_dirty.size(), 0);
    if (cols > 0 && rows > 0) createTerminal(cols, rows);
}

TerminalLayer::~TerminalLayer() {
    if (registered_) blinkRegistry().erase(this);
    freeAll();
    if (on_output && mcrf::python_alive()) Py_CLEAR(on_output);
}

void TerminalLayer::freeAll() noexcept {
    // Each handle is freed once and nulled; every free accepts NULL.
    ghostty_mouse_event_free(reinterpret_cast<GhosttyMouseEvent>(mouse_ev_));
    ghostty_mouse_encoder_free(reinterpret_cast<GhosttyMouseEncoder>(mouse_enc_));
    ghostty_key_event_free(key_ev_);
    ghostty_key_encoder_free(key_enc_);
    ghostty_render_state_row_cells_free(cells_);
    ghostty_render_state_row_iterator_free(row_it_);
    ghostty_render_state_free(rs_);
    ghostty_terminal_free(term_);
    mouse_ev_ = nullptr; mouse_enc_ = nullptr; key_ev_ = nullptr; key_enc_ = nullptr;
    cells_ = nullptr; row_it_ = nullptr; rs_ = nullptr; term_ = nullptr;
}

void TerminalLayer::createTerminal(int cols, int rows) {
    if (cols > UINT16_MAX || rows > UINT16_MAX)
        throw std::invalid_argument("TerminalLayer: columns and rows must be at most 65535");
    try {
        ck(ghostty_terminal_new(nullptr, &term_, static_cast<uint16_t>(cols), static_cast<uint16_t>(rows)),
           "ghostty_terminal_new");
        ck(ghostty_terminal_set(term_, GHOSTTY_TERMINAL_OPT_USERDATA, this), "ghostty_terminal_set(USERDATA)");
        // Callback options take the function pointer itself as the value.
        ck(ghostty_terminal_set(term_, GHOSTTY_TERMINAL_OPT_WRITE_PTY,
                                reinterpret_cast<const void*>(&Callbacks::writePty)),
           "ghostty_terminal_set(WRITE_PTY)");
        ck(ghostty_terminal_set(term_, GHOSTTY_TERMINAL_OPT_RENDER_HOLD,
                                reinterpret_cast<const void*>(&Callbacks::renderHold)),
           "ghostty_terminal_set(RENDER_HOLD)");
        // Two limits apply, whichever is reached first; lift the byte limit when lines are asked for.
        size_t max_bytes = scrollback_ == 0 ? 0 : SIZE_MAX;
        ck(ghostty_terminal_set(term_, GHOSTTY_TERMINAL_OPT_SCROLLBACK_MAX_BYTES, &max_bytes),
           "ghostty_terminal_set(SCROLLBACK_MAX_BYTES)");
        if (scrollback_ != 0) {
            size_t lines = scrollback_;
            ck(ghostty_terminal_set(term_, GHOSTTY_TERMINAL_OPT_SCROLLBACK_MAX_LINES, &lines),
               "ghostty_terminal_set(SCROLLBACK_MAX_LINES)");
        }
        // No images are drawn, so the Kitty graphics protocol is switched off (its query
        // then gets no reply instead of a false OK).
        uint64_t limit = 0;
        GhosttyResult r = ghostty_terminal_set(term_, GHOSTTY_TERMINAL_OPT_KITTY_IMAGE_STORAGE_LIMIT, &limit);
        if (r != GHOSTTY_UNSUPPORTED) ck(r, "ghostty_terminal_set(KITTY_IMAGE_STORAGE_LIMIT)");
        if (texture) {
            ck(ghostty_terminal_resize(term_, static_cast<uint16_t>(cols), static_cast<uint16_t>(rows),
                                       static_cast<uint32_t>(texture->sprite_width),
                                       static_cast<uint32_t>(texture->sprite_height)),
               "ghostty_terminal_resize");
        }
        ck(ghostty_render_state_new(nullptr, &rs_), "ghostty_render_state_new");
        // The colours the library draws by default, made explicit: a program asking for the
        // default foreground, background or cursor colour (OSC 10/11/12 ?) gets an answer
        // only for colours that are set.
        ck(ghostty_render_state_update(rs_, term_), "ghostty_render_state_update");
        GhosttyRenderStateColors colors = GHOSTTY_INIT_SIZED(GhosttyRenderStateColors);
        ck(ghostty_render_state_get(rs_, GHOSTTY_RENDER_STATE_DATA_COLORS, &colors), "ghostty_render_state_get(COLORS)");
        nominal_fg_ = Rgb{colors.foreground.r, colors.foreground.g, colors.foreground.b};
        nominal_bg_ = Rgb{colors.background.r, colors.background.g, colors.background.b};
        applyDefaultColours();
        ck(ghostty_render_state_row_iterator_new(nullptr, &row_it_), "ghostty_render_state_row_iterator_new");
        ck(ghostty_render_state_row_cells_new(nullptr, &cells_), "ghostty_render_state_row_cells_new");
        ck(ghostty_key_encoder_new(nullptr, &key_enc_), "ghostty_key_encoder_new");
        ck(ghostty_key_event_new(nullptr, &key_ev_), "ghostty_key_event_new");
        GhosttyMouseEncoder menc = nullptr;
        ck(ghostty_mouse_encoder_new(nullptr, &menc), "ghostty_mouse_encoder_new");
        mouse_enc_ = reinterpret_cast<GhosttyMouseEncoderImpl*>(menc);
        GhosttyMouseEvent mev = nullptr;
        ck(ghostty_mouse_event_new(nullptr, &mev), "ghostty_mouse_event_new");
        mouse_ev_ = reinterpret_cast<GhosttyMouseEventImpl*>(mev);
    } catch (...) {
        freeAll();
        throw;
    }
    term_cols_ = cols;
    term_rows_ = rows;
    needs_sync_ = true;
    force_full_ = true;
}

void TerminalLayer::resize(int new_grid_x, int new_grid_y) {
    TileLayer::resize(new_grid_x, new_grid_y);
    // Reflow moves content, so nothing is kept: the next sync repaints every cell.
    std::fill(tiles.begin(), tiles.end(), -1);
    const size_t n = static_cast<size_t>(new_grid_x) * new_grid_y;
    fg_.assign(n, default_fg_);
    bg_.assign(n, default_bg_);
    flags_.assign(n, CF_DEFAULT_BG);
    chunk_blink_.assign(chunk_dirty.size(), 0);
    blink_cells_ = 0;
    force_full_ = true;
    needs_sync_ = true;
    try {
    if (new_grid_x > 0 && new_grid_y > 0) {
        if (!term_) {
            createTerminal(new_grid_x, new_grid_y);
        } else {
            if (new_grid_x > UINT16_MAX || new_grid_y > UINT16_MAX)
                throw std::invalid_argument("TerminalLayer: columns and rows must be at most 65535");
            ck(ghostty_terminal_resize(term_, static_cast<uint16_t>(new_grid_x), static_cast<uint16_t>(new_grid_y),
                                       texture ? static_cast<uint32_t>(texture->sprite_width) : 0,
                                       texture ? static_cast<uint32_t>(texture->sprite_height) : 0),
               "ghostty_terminal_resize");
            term_cols_ = new_grid_x;
            term_rows_ = new_grid_y;
        }
    }
    } catch (const std::exception& e) {
        // resize() is reached from grid setters that cannot fail, so this is reported like a
        // failing engine callback; the layer then reports the size mismatch when drawn.
        PyErr_Format(PyExc_RuntimeError, "TerminalLayer '%s': %s", name.c_str(), e.what());
        mcrf::print_callback_exception();
        if (McRFPy_API::game && McRFPy_API::game->getConfig().exit_on_exception) McRFPy_API::signalPythonException();
    }
    // A size of 0 keeps the emulator (and its contents) at its last size; nothing is shown
    // and write() raises until the layer has a size again.
    updateBlinkRegistration();
    notifyGrid();
    // A resize can produce output (an in-band size report, mode 2048). No Python caller
    // gets it from here, so it is delivered the way an engine callback is (last: the
    // callback may drop the last reference to this layer).
    if (!pending_output.empty()) TerminalLayerAPI::flush_from_engine(shared_from_this());
}

void TerminalLayer::textureChanged() {
    force_full_ = true;
    needs_sync_ = true;
    if (term_ && texture && grid_x > 0 && grid_y > 0) {
        // Same cells, new pixel size (reported to programs that ask, and used for mouse pixels).
        ck(ghostty_terminal_resize(term_, static_cast<uint16_t>(grid_x), static_cast<uint16_t>(grid_y),
                                   static_cast<uint32_t>(texture->sprite_width),
                                   static_cast<uint32_t>(texture->sprite_height)),
           "ghostty_terminal_resize");
    }
    markDirty();
}

// =============================================================================
// Emulator I/O
// =============================================================================

void TerminalLayer::feed(const uint8_t* data, size_t len) {
    if (!term_) throw std::logic_error("TerminalLayer has no size yet");
    if (len == 0) return;
    ghostty_terminal_vt_write(term_, data, len);   // never fails: malformed input is absorbed
    needs_sync_ = true;
    updateBlinkRegistration();   // a synchronized-output hold may have begun or ended
    if (callback_failed_) {
        callback_failed_ = false;
        throw std::runtime_error("libghostty-vt: a terminal callback failed (out of memory?)");
    }
    notifyGrid();
}

bool TerminalLayer::modeEnabled(uint16_t mode, bool ansi) const {
    if (!term_) return false;
    GhosttyTerminalModeConfig cfg{ghostty_mode_new(mode, ansi), false};
    ck(ghostty_terminal_get(term_, GHOSTTY_TERMINAL_DATA_MODE, &cfg), "ghostty_terminal_get(MODE)");
    return cfg.value;
}

unsigned TerminalLayer::kittyKeyboardFlags() const {
    if (!term_) return 0;
    uint8_t flags = 0;
    ck(ghostty_terminal_get(term_, GHOSTTY_TERMINAL_DATA_KITTY_KEYBOARD_FLAGS, &flags),
       "ghostty_terminal_get(KITTY_KEYBOARD_FLAGS)");
    return flags;
}

void TerminalLayer::endHold() {
    if (!held_) return;
    // Setting the mode ourselves does not invoke the hold callback, so clear the flag here.
    GhosttyTerminalModeConfig mode{GHOSTTY_MODE_SYNCHRONIZED_OUTPUT, false};
    ck(ghostty_terminal_set(term_, GHOSTTY_TERMINAL_OPT_MODE, &mode), "ghostty_terminal_set(MODE 2026)");
    held_ = false;
}

void TerminalLayer::sync(bool notify) {
    if (!term_ || grid_x <= 0 || grid_y <= 0) return;
    if (!needs_sync_ && !force_full_) return;
    if (held_ && engineNowMs() - hold_start_ms_ >= kHoldTimeoutMs) endHold();
    if (!held_) ck(ghostty_render_state_update(rs_, term_), "ghostty_render_state_update");

    const bool reverse = modeEnabled(5, false);   // DECSCNM: the whole screen in reverse video
    if (reverse != screen_reverse_) { screen_reverse_ = reverse; force_full_ = true; }

    uint16_t cols = 0, rows = 0;
    ck(ghostty_render_state_get(rs_, GHOSTTY_RENDER_STATE_DATA_COLS, &cols), "ghostty_render_state_get(COLS)");
    ck(ghostty_render_state_get(rs_, GHOSTTY_RENDER_STATE_DATA_ROWS, &rows), "ghostty_render_state_get(ROWS)");
    if (cols != grid_x || rows != grid_y)
        throw std::runtime_error("TerminalLayer: render state is " + std::to_string(cols) + "x" +
                                 std::to_string(rows) + ", layer is " + std::to_string(grid_x) + "x" +
                                 std::to_string(grid_y));

    GhosttyRenderStateDirty dirty = GHOSTTY_RENDER_STATE_DIRTY_FALSE;
    ck(ghostty_render_state_get(rs_, GHOSTTY_RENDER_STATE_DATA_DIRTY, &dirty), "ghostty_render_state_get(DIRTY)");
    GhosttyRenderStateColors colors = GHOSTTY_INIT_SIZED(GhosttyRenderStateColors);
    ck(ghostty_render_state_get(rs_, GHOSTTY_RENDER_STATE_DATA_COLORS, &colors), "ghostty_render_state_get(COLORS)");
    const sf::Color dfg = rgb(colors.foreground), dbg = rgb(colors.background);
    if (dfg != default_fg_ || dbg != default_bg_) { default_fg_ = dfg; default_bg_ = dbg; force_full_ = true; }
    cursor_colour_ = colors.cursor_has_value ? rgb(colors.cursor) : default_fg_;

    const bool full = force_full_ || dirty == GHOSTTY_RENDER_STATE_DIRTY_FULL;
    bool cells_changed = false;

    if (full || dirty != GHOSTTY_RENDER_STATE_DIRTY_FALSE) {
        ck(ghostty_render_state_get(rs_, GHOSTTY_RENDER_STATE_DATA_ROW_ITERATOR, &row_it_),
           "ghostty_render_state_get(ROW_ITERATOR)");
        const FontAtlasData* fa = texture ? texture->font_atlas.get() : nullptr;
        if (!fa) throw std::runtime_error("TerminalLayer: its texture is not a font atlas");
        const int atlas_tiles = static_cast<int>(fa->tiles.size());

        static const GhosttyRenderStateRowCellsData cell_keys[3] = {
            GHOSTTY_RENDER_STATE_ROW_CELLS_DATA_RAW,
            GHOSTTY_RENDER_STATE_ROW_CELLS_DATA_STYLE,
            GHOSTTY_RENDER_STATE_ROW_CELLS_DATA_GRAPHEMES_BUF,
        };
        static const GhosttyCellData raw_keys[2] = {GHOSTTY_CELL_DATA_WIDE, GHOSTTY_CELL_DATA_CONTENT_TAG};

        int rows_seen = 0;
        for (;;) {
            int y;
            if (full) {
                if (!ghostty_render_state_row_iterator_next(row_it_)) break;
                int32_t vy = 0;
                ck(ghostty_render_state_row_get(row_it_, GHOSTTY_RENDER_STATE_ROW_DATA_VIEWPORT_Y, &vy),
                   "ghostty_render_state_row_get(VIEWPORT_Y)");
                y = vy;
            } else {
                uint16_t dy = 0;
                if (!ghostty_render_state_row_iterator_next_dirty(row_it_, &dy)) break;
                y = dy;
            }
            if (y < 0 || y >= grid_y)
                throw std::runtime_error("TerminalLayer: render state row " + std::to_string(y) + " is outside the layer");
            ++rows_seen;
            ck(ghostty_render_state_row_get(row_it_, GHOSTTY_RENDER_STATE_ROW_DATA_CELLS, &cells_),
               "ghostty_render_state_row_get(CELLS)");

            int x = 0, span0 = INT_MAX, span1 = -1;
            int prev_tile = -1;
            bool prev_wide = false;
            while (ghostty_render_state_row_cells_next(cells_)) {
                if (x >= grid_x)
                    throw std::runtime_error("TerminalLayer: render state row has more cells than columns");
                GhosttyCell raw = 0;
                GhosttyStyle style;
                uint32_t cp_buf[1] = {0};
                GhosttyCodepointBuffer graphemes{cp_buf, 1, 0};
                void* vals[3] = {&raw, &style, &graphemes};
                GhosttyResult r = ghostty_render_state_row_cells_get_multi(cells_, 3, cell_keys, vals, nullptr);
                // OUT_OF_SPACE: a combining sequence; the base codepoint is there.
                if (r != GHOSTTY_OUT_OF_SPACE) ck(r, "ghostty_render_state_row_cells_get_multi");
                GhosttyCellWide wide = GHOSTTY_CELL_WIDE_NARROW;
                GhosttyCellContentTag tag = GHOSTTY_CELL_CONTENT_CODEPOINT;
                void* raw_vals[2] = {&wide, &tag};
                ck(ghostty_cell_get_multi(raw, 2, raw_keys, raw_vals, nullptr), "ghostty_cell_get_multi");

                const uint16_t sflags = style.flags;
                uint16_t fl = 0;
                const bool bold = sflags & GHOSTTY_STYLE_FLAG_BOLD;
                const bool italic = sflags & GHOSTTY_STYLE_FLAG_ITALIC;
                if (sflags & GHOSTTY_STYLE_FLAG_INVISIBLE) fl |= CF_INVISIBLE;
                if (sflags & GHOSTTY_STYLE_FLAG_BLINK) fl |= CF_BLINK;
                if (sflags & GHOSTTY_STYLE_FLAG_STRIKETHROUGH) fl |= CF_STRIKE;
                if (sflags & GHOSTTY_STYLE_FLAG_OVERLINE) fl |= CF_OVERLINE;
                const int ul = GHOSTTY_STYLE_UNDERLINE(style);
                if (ul != GHOSTTY_SGR_UNDERLINE_NONE) fl |= CF_UNDERLINE;
                if (ul == GHOSTTY_SGR_UNDERLINE_DOUBLE) fl |= CF_UNDERLINE2;

                // Tile: the glyph in the face the style asks for.
                int tile = -1;
                bool this_wide = false;
                if (wide == GHOSTTY_CELL_WIDE_SPACER_TAIL) {
                    // The right half of the wide glyph to the left, if the atlas has one.
                    if (prev_wide && prev_tile >= 0 && prev_tile + 1 < atlas_tiles &&
                        fa->tiles[prev_tile + 1].kind == FontAtlasData::Tile::GLYPH_RIGHT)
                        tile = prev_tile + 1;
                } else if (wide != GHOSTTY_CELL_WIDE_SPACER_HEAD && graphemes.len > 0) {
                    tile = resolveTile(*fa, cp_buf[0], bold, italic, fl);
                    this_wide = (wide == GHOSTTY_CELL_WIDE_WIDE);
                }
                prev_tile = tile;
                prev_wide = this_wide;

                // Colours: the style's, else a background stored in the cell, else the defaults.
                sf::Color fg = default_fg_, bg = default_bg_;
                bool default_bg = false;
                auto style_colour = [&](const GhosttyStyleColor& c, sf::Color& out) -> bool {
                    switch (c.tag) {
                        case GHOSTTY_STYLE_COLOR_NONE: return false;
                        case GHOSTTY_STYLE_COLOR_PALETTE: out = rgb(colors.palette[c.value.palette]); return true;
                        case GHOSTTY_STYLE_COLOR_RGB: out = rgb(c.value.rgb); return true;
                    }
                    throw std::runtime_error("TerminalLayer: unknown GhosttyStyleColor tag " + std::to_string(c.tag));
                };
                style_colour(style.fg_color, fg);
                if (!style_colour(style.bg_color, bg)) {
                    if (tag == GHOSTTY_CELL_CONTENT_BG_COLOR_PALETTE) {
                        GhosttyColorPaletteIndex idx = 0;
                        ck(ghostty_cell_get(raw, GHOSTTY_CELL_DATA_COLOR_PALETTE, &idx), "ghostty_cell_get(COLOR_PALETTE)");
                        bg = rgb(colors.palette[idx]);
                    } else if (tag == GHOSTTY_CELL_CONTENT_BG_COLOR_RGB) {
                        GhosttyColorRgb c{};
                        ck(ghostty_cell_get(raw, GHOSTTY_CELL_DATA_COLOR_RGB, &c), "ghostty_cell_get(COLOR_RGB)");
                        bg = rgb(c);
                    } else {
                        default_bg = true;
                    }
                }
                // Inverse: swap at fill time. The swapped-in background is a real colour, so it
                // is always drawn. DECSCNM (the whole screen reversed) the library applies to the
                // default colours it reports; the default background is then the foreground
                // colour, so it is drawn too.
                if (sflags & GHOSTTY_STYLE_FLAG_INVERSE) {
                    std::swap(fg, bg);
                    default_bg = false;
                }
                if (screen_reverse_) default_bg = false;
                if (default_bg) fl |= CF_DEFAULT_BG;
                if (sflags & GHOSTTY_STYLE_FLAG_FAINT) {
                    fg.r = static_cast<sf::Uint8>(fg.r / 2);
                    fg.g = static_cast<sf::Uint8>(fg.g / 2);
                    fg.b = static_cast<sf::Uint8>(fg.b / 2);
                }

                const size_t i = static_cast<size_t>(y) * grid_x + x;
                if (tiles[i] != tile || fg_[i] != fg || bg_[i] != bg || flags_[i] != fl) {
                    const bool was_blink = flags_[i] & CF_BLINK, is_blink = fl & CF_BLINK;
                    if (was_blink != is_blink) {
                        const int c = getChunkIndex(x, y);
                        chunk_blink_[c] += is_blink ? 1 : -1;
                        blink_cells_ += is_blink ? 1 : -1;
                    }
                    tiles[i] = tile; fg_[i] = fg; bg_[i] = bg; flags_[i] = fl;
                    span0 = std::min(span0, x);
                    span1 = std::max(span1, x);
                }
                ++x;
            }
            if (x != grid_x)
                throw std::runtime_error("TerminalLayer: render state row has fewer cells than columns");
            if (span1 >= 0) {
                cells_changed = true;
                for (int cx = span0 / CHUNK_SIZE; cx <= span1 / CHUNK_SIZE; ++cx)
                    chunk_dirty[(y / CHUNK_SIZE) * chunks_x + cx] = true;
            }
        }
        if (full && rows_seen != grid_y)
            throw std::runtime_error("TerminalLayer: render state iterated " + std::to_string(rows_seen) +
                                     " rows, expected " + std::to_string(grid_y));
    }

    // The cursor lives outside the cells: a change here repaints no chunk.
    GhosttyRenderStateCursor cur = GHOSTTY_INIT_SIZED(GhosttyRenderStateCursor);
    ck(ghostty_render_state_get(rs_, GHOSTTY_RENDER_STATE_DATA_CURSOR, &cur), "ghostty_render_state_get(CURSOR)");
    const bool in_view = cur.viewport_has_value;
    const int cx = in_view ? cur.viewport_x : 0, cy = in_view ? cur.viewport_y : 0;
    const bool cursor_changed = in_view != cursor_in_view_ || cx != cursor_x_ || cy != cursor_y_ ||
                                cur.visible != cursor_visible_ || cur.blinking != cursor_blinking_ ||
                                static_cast<int>(cur.visual_style) != cursor_style_ || cur.wide_tail != cursor_wide_;
    cursor_in_view_ = in_view;
    cursor_x_ = cx;
    cursor_y_ = cy;
    cursor_visible_ = cur.visible;
    cursor_blinking_ = cur.blinking;
    cursor_style_ = static_cast<int>(cur.visual_style);
    cursor_wide_ = cur.wide_tail;

    if (!held_) ck(ghostty_render_state_clean(rs_), "ghostty_render_state_clean");
    needs_sync_ = held_;   // a held frame is re-checked (the hold may time out)
    force_full_ = false;
    updateBlinkRegistration();
    if (notify && (cells_changed || cursor_changed)) notifyGrid();
}

// Reached from read paths that cannot fail (GridPoint attributes, edit() views); the
// TerminalLayer's own Python methods call sync() and raise instead.
void TerminalLayer::prepareRead() {
    try {
        sync(true);
    } catch (const std::exception& e) {
        PyErr_Format(PyExc_RuntimeError, "TerminalLayer '%s': %s", name.c_str(), e.what());
        mcrf::print_callback_exception();
        if (McRFPy_API::game && McRFPy_API::game->getConfig().exit_on_exception) McRFPy_API::signalPythonException();
    }
}

// =============================================================================
// Blink clock
// =============================================================================

void TerminalLayer::updateBlinkRegistration() {
    // Ticked while something depends on the clock: blinking cells, a blinking cursor, or a
    // synchronized-output hold that must end after kHoldTimeoutMs even if nothing is written.
    const bool want = held_ || (blink_interval_ms_ > 0 && (blink_cells_ > 0 || (cursor_blinking_ && show_cursor)));
    if (want == registered_) return;
    registered_ = want;
    if (want) {
        blinkRegistry().insert(this);
    } else {
        blinkRegistry().erase(this);
        if (!blink_on_) {
            // Leaving the clock in the off phase: show the blinking cells again.
            blink_on_ = true;
            for (size_t c = 0; c < chunk_blink_.size(); ++c)
                if (chunk_blink_[c] > 0) chunk_dirty[c] = true;
            notifyGrid();
        }
    }
}

void TerminalLayer::tick(int now_ms) {
    // Must not change the registry (tickAll is iterating it): registration follows at the next sync.
    if (held_ && now_ms - hold_start_ms_ >= kHoldTimeoutMs) {
        try {
            endHold();
        } catch (const std::exception& e) {
            PyErr_Format(PyExc_RuntimeError, "TerminalLayer '%s': %s", name.c_str(), e.what());
            mcrf::print_callback_exception();
        }
        needs_sync_ = true;
        notifyGrid();
    }
    if (blink_interval_ms_ <= 0) return;
    const bool on = ((now_ms / blink_interval_ms_) % 2) == 0;
    if (on == blink_on_) return;
    blink_on_ = on;
    for (size_t c = 0; c < chunk_blink_.size(); ++c)
        if (chunk_blink_[c] > 0) chunk_dirty[c] = true;
    notifyGrid();   // the cursor (if it blinks) is redrawn with the view; no chunk needed for it
}

void TerminalLayer::tickAll(int now_ms) {
    auto& reg = blinkRegistry();
    if (reg.empty()) return;
    // tick() never changes the registry, so iterating it directly is safe.
    for (TerminalLayer* layer : reg) layer->tick(now_ms);
}

void TerminalLayer::setBlinkInterval(double seconds) {
    blink_interval_ms_ = seconds > 0 ? std::max(1, static_cast<int>(std::lround(seconds * 1000.0))) : 0;
    if (blink_interval_ms_ == 0 && !blink_on_) {
        blink_on_ = true;
        for (size_t c = 0; c < chunk_blink_.size(); ++c)
            if (chunk_blink_[c] > 0) chunk_dirty[c] = true;
        notifyGrid();
    }
    updateBlinkRegistration();
}

// =============================================================================
// Colours, title, text, scrolling
// =============================================================================

// Foreground, background and cursor defaults, always set. With no `background` the
// background reported is the library's nominal one (black), though nothing is drawn there.
void TerminalLayer::applyDefaultColours() {
    GhosttyColorRgb fg{nominal_fg_.r, nominal_fg_.g, nominal_fg_.b};
    GhosttyColorRgb bg = has_background_ ? GhosttyColorRgb{background_.r, background_.g, background_.b}
                                         : GhosttyColorRgb{nominal_bg_.r, nominal_bg_.g, nominal_bg_.b};
    ck(ghostty_terminal_set(term_, GHOSTTY_TERMINAL_OPT_COLOR_FOREGROUND, &fg), "ghostty_terminal_set(COLOR_FOREGROUND)");
    ck(ghostty_terminal_set(term_, GHOSTTY_TERMINAL_OPT_COLOR_BACKGROUND, &bg), "ghostty_terminal_set(COLOR_BACKGROUND)");
    ck(ghostty_terminal_set(term_, GHOSTTY_TERMINAL_OPT_COLOR_CURSOR, &fg), "ghostty_terminal_set(COLOR_CURSOR)");
}

void TerminalLayer::setBackground(const sf::Color* colour) {
    has_background_ = colour != nullptr;
    background_ = colour ? *colour : sf::Color::Transparent;
    if (term_) applyDefaultColours();
    force_full_ = true;
    needs_sync_ = true;
    markDirty();
}

std::vector<sf::Color> TerminalLayer::palette() const {
    GhosttyColorRgb pal[256];
    ck(ghostty_terminal_get(term_, GHOSTTY_TERMINAL_DATA_COLOR_PALETTE, pal), "ghostty_terminal_get(COLOR_PALETTE)");
    std::vector<sf::Color> out;
    out.reserve(256);
    for (const auto& c : pal) out.push_back(rgb(c));
    return out;
}

void TerminalLayer::setPalette(const std::vector<sf::Color>& colours) {
    if (colours.empty()) {
        ck(ghostty_terminal_set(term_, GHOSTTY_TERMINAL_OPT_COLOR_PALETTE, nullptr),
           "ghostty_terminal_set(COLOR_PALETTE)");
    } else {
        if (colours.size() != 256) throw std::invalid_argument("palette needs exactly 256 colours");
        GhosttyColorRgb pal[256];
        for (size_t i = 0; i < 256; ++i) pal[i] = GhosttyColorRgb{colours[i].r, colours[i].g, colours[i].b};
        ck(ghostty_terminal_set(term_, GHOSTTY_TERMINAL_OPT_COLOR_PALETTE, pal),
           "ghostty_terminal_set(COLOR_PALETTE)");
    }
    force_full_ = true;
    needs_sync_ = true;
    notifyGrid();
}

std::string TerminalLayer::title() const {
    if (!term_) return std::string();
    GhosttyString s{nullptr, 0};
    ck(ghostty_terminal_get(term_, GHOSTTY_TERMINAL_DATA_TITLE, &s), "ghostty_terminal_get(TITLE)");
    return s.len ? std::string(reinterpret_cast<const char*>(s.ptr), s.len) : std::string();
}

std::string TerminalLayer::screenText() {
    if (!term_ || grid_x <= 0 || grid_y <= 0) return std::string();
    sync(true);   // the render state now holds what is shown
    ck(ghostty_render_state_get(rs_, GHOSTTY_RENDER_STATE_DATA_ROW_ITERATOR, &row_it_),
       "ghostty_render_state_get(ROW_ITERATOR)");
    std::string out;
    std::vector<uint8_t> buf(32);
    bool first = true;
    while (ghostty_render_state_row_iterator_next(row_it_)) {
        ck(ghostty_render_state_row_get(row_it_, GHOSTTY_RENDER_STATE_ROW_DATA_CELLS, &cells_),
           "ghostty_render_state_row_get(CELLS)");
        std::string line;
        while (ghostty_render_state_row_cells_next(cells_)) {
            GhosttyCell raw = 0;
            ck(ghostty_render_state_row_cells_get(cells_, GHOSTTY_RENDER_STATE_ROW_CELLS_DATA_RAW, &raw),
               "ghostty_render_state_row_cells_get(RAW)");
            GhosttyCellWide wide = GHOSTTY_CELL_WIDE_NARROW;
            ck(ghostty_cell_get(raw, GHOSTTY_CELL_DATA_WIDE, &wide), "ghostty_cell_get(WIDE)");
            if (wide == GHOSTTY_CELL_WIDE_SPACER_TAIL) continue;
            GhosttyBuffer gb{buf.data(), buf.size(), 0};
            GhosttyResult r = ghostty_render_state_row_cells_get(cells_, GHOSTTY_RENDER_STATE_ROW_CELLS_DATA_GRAPHEMES_UTF8, &gb);
            if (r == GHOSTTY_OUT_OF_SPACE) {
                buf.resize(gb.len);
                gb = GhosttyBuffer{buf.data(), buf.size(), 0};
                r = ghostty_render_state_row_cells_get(cells_, GHOSTTY_RENDER_STATE_ROW_CELLS_DATA_GRAPHEMES_UTF8, &gb);
            }
            ck(r, "ghostty_render_state_row_cells_get(GRAPHEMES_UTF8)");
            if (gb.len == 0) line.push_back(' ');
            else line.append(reinterpret_cast<const char*>(buf.data()), gb.len);
        }
        while (!line.empty() && line.back() == ' ') line.pop_back();
        if (!first) out.push_back('\n');
        out += line;
        first = false;
    }
    return out;
}

size_t TerminalLayer::scrollbackRows() const {
    if (!term_) return 0;
    size_t n = 0;
    ck(ghostty_terminal_get(term_, GHOSTTY_TERMINAL_DATA_SCROLLBACK_ROWS, &n), "ghostty_terminal_get(SCROLLBACK_ROWS)");
    return n;
}

long long TerminalLayer::scrollOffset() const {
    if (!term_) return 0;
    GhosttyTerminalScrollbar sb{};
    ck(ghostty_terminal_get(term_, GHOSTTY_TERMINAL_DATA_SCROLLBAR, &sb), "ghostty_terminal_get(SCROLLBAR)");
    const uint64_t live = sb.total > sb.len ? sb.total - sb.len : 0;
    return sb.offset >= live ? 0 : static_cast<long long>(live - sb.offset);
}

void TerminalLayer::scrollBy(long long rows_back) {
    if (!term_) throw std::logic_error("TerminalLayer has no size yet");
    // Clamped before it is negated (-LLONG_MIN overflows): no scrollback is anywhere near 2^30 rows.
    constexpr long long kMax = 1LL << 30;
    rows_back = std::clamp(rows_back, -kMax, kMax);
    GhosttyTerminalScrollViewport sv{};
    sv.tag = GHOSTTY_TERMINAL_SCROLL_VIEWPORT_DELTA;
    sv.value.delta = -static_cast<intptr_t>(rows_back);   // the library's up is negative
    ck(ghostty_terminal_scroll_viewport(term_, sv), "ghostty_terminal_scroll_viewport");
    needs_sync_ = true;
    notifyGrid();
}

void TerminalLayer::setScrollOffset(long long rows_back) {
    if (!term_) throw std::logic_error("TerminalLayer has no size yet");
    GhosttyTerminalScrollViewport sv{};
    if (rows_back <= 0) {
        sv.tag = GHOSTTY_TERMINAL_SCROLL_VIEWPORT_BOTTOM;
    } else {
        GhosttyTerminalScrollbar sb{};
        ck(ghostty_terminal_get(term_, GHOSTTY_TERMINAL_DATA_SCROLLBAR, &sb), "ghostty_terminal_get(SCROLLBAR)");
        const uint64_t live = sb.total > sb.len ? sb.total - sb.len : 0;
        sv.tag = GHOSTTY_TERMINAL_SCROLL_VIEWPORT_ROW;
        sv.value.row = static_cast<uint64_t>(rows_back) >= live ? 0 : static_cast<size_t>(live - rows_back);
    }
    ck(ghostty_terminal_scroll_viewport(term_, sv), "ghostty_terminal_scroll_viewport");
    needs_sync_ = true;
    notifyGrid();
}

// =============================================================================
// Input encoders
// =============================================================================

void TerminalLayer::encodeKey(int ghostty_key, int action, unsigned mods, const std::string& utf8, uint32_t unshifted) {
    if (!term_) throw std::logic_error("TerminalLayer has no size yet");
    ck(ghostty_key_encoder_set_from_terminal(key_enc_, term_), "ghostty_key_encoder_set_from_terminal");
    ck(ghostty_key_event_set_action(key_ev_, static_cast<GhosttyKeyAction>(action)), "ghostty_key_event_set_action");
    ck(ghostty_key_event_set_key(key_ev_, static_cast<GhosttyKey>(ghostty_key)), "ghostty_key_event_set_key");
    ck(ghostty_key_event_set_mods(key_ev_, static_cast<GhosttyMods>(mods)), "ghostty_key_event_set_mods");
    ck(ghostty_key_event_set_unshifted_codepoint(key_ev_, unshifted), "ghostty_key_event_set_unshifted_codepoint");
    // The event borrows the text: cleared again below, before `utf8` can go away.
    GhosttyString s{reinterpret_cast<const uint8_t*>(utf8.data()), utf8.size()};
    ck(ghostty_key_event_set_utf8(key_ev_, s), "ghostty_key_event_set_utf8");
    uint8_t buf[128];
    size_t n = 0;
    GhosttyResult r = ghostty_key_encoder_encode(key_enc_, key_ev_, buf, sizeof buf, &n);
    GhosttyResult cleared = ghostty_key_event_set_utf8(key_ev_, GhosttyString{nullptr, 0});
    ck(r, "ghostty_key_encoder_encode");
    ck(cleared, "ghostty_key_event_set_utf8(clear)");
    pending_output.append(reinterpret_cast<const char*>(buf), n);
}

void TerminalLayer::encodeMouse(float cell_x, float cell_y, int button, int action, unsigned mods) {
    if (!term_) throw std::logic_error("TerminalLayer has no size yet");
    auto menc = reinterpret_cast<GhosttyMouseEncoder>(mouse_enc_);
    auto mev = reinterpret_cast<GhosttyMouseEvent>(mouse_ev_);
    const uint32_t cw = texture ? static_cast<uint32_t>(std::max(1, texture->sprite_width)) : 1;
    const uint32_t ch = texture ? static_cast<uint32_t>(std::max(1, texture->sprite_height)) : 1;
    // Wheel "buttons" (4-7) are not held; the others are tracked for motion reports.
    const bool wheel = button >= GHOSTTY_MOUSE_BUTTON_FOUR && button <= GHOSTTY_MOUSE_BUTTON_SEVEN;
    if (!wheel && button > 0 && button < 32) {
        if (action == GHOSTTY_MOUSE_ACTION_PRESS) mouse_buttons_down_ |= 1u << button;
        else if (action == GHOSTTY_MOUSE_ACTION_RELEASE) mouse_buttons_down_ &= ~(1u << button);
    }
    ck(ghostty_mouse_encoder_set_from_terminal(menc, term_), "ghostty_mouse_encoder_set_from_terminal");
    GhosttyMouseEncoderSize size = GHOSTTY_INIT_SIZED(GhosttyMouseEncoderSize);
    size.screen_width = cw * static_cast<uint32_t>(grid_x);
    size.screen_height = ch * static_cast<uint32_t>(grid_y);
    size.cell_width = cw;
    size.cell_height = ch;
    ck(ghostty_mouse_encoder_set(menc, GHOSTTY_MOUSE_ENCODER_OPT_SIZE, &size), "ghostty_mouse_encoder_set(SIZE)");
    bool any = mouse_buttons_down_ != 0;
    ck(ghostty_mouse_encoder_set(menc, GHOSTTY_MOUSE_ENCODER_OPT_ANY_BUTTON_PRESSED, &any),
       "ghostty_mouse_encoder_set(ANY_BUTTON_PRESSED)");
    ck(ghostty_mouse_event_set_action(mev, static_cast<GhosttyMouseAction>(action)), "ghostty_mouse_event_set_action");
    if (button > 0) ck(ghostty_mouse_event_set_button(mev, static_cast<GhosttyMouseButton>(button)), "ghostty_mouse_event_set_button");
    else ck(ghostty_mouse_event_clear_button(mev), "ghostty_mouse_event_clear_button");
    ck(ghostty_mouse_event_set_mods(mev, static_cast<GhosttyMods>(mods)), "ghostty_mouse_event_set_mods");
    // Clamped to the layer: a drag that leaves it reports the edge cell, as terminals do.
    const float px = std::clamp(cell_x * static_cast<float>(cw), 0.0f, static_cast<float>(size.screen_width) - 1.0f);
    const float py = std::clamp(cell_y * static_cast<float>(ch), 0.0f, static_cast<float>(size.screen_height) - 1.0f);
    ck(ghostty_mouse_event_set_position(mev, GhosttyMousePosition{px, py}),
       "ghostty_mouse_event_set_position");
    uint8_t buf[128];
    size_t n = 0;
    ck(ghostty_mouse_encoder_encode(menc, mev, buf, sizeof buf, &n), "ghostty_mouse_encoder_encode");
    pending_output.append(reinterpret_cast<const char*>(buf), n);
}

void TerminalLayer::encodeFocus(bool gained) {
    if (!term_) throw std::logic_error("TerminalLayer has no size yet");
    if (!modeEnabled(1004, false)) return;   // focus reporting off: nothing to send
    uint8_t buf[16];
    size_t n = 0;
    ck(ghostty_focus_encode(gained ? GHOSTTY_FOCUS_GAINED : GHOSTTY_FOCUS_LOST, buf, sizeof buf, &n),
       "ghostty_focus_encode");
    pending_output.append(reinterpret_cast<const char*>(buf), n);
}

namespace {
struct PasteSource {
    const std::string* text;
    static bool read(void* userdata, GhosttyString, GhosttyWriter writer) {
        auto* self = static_cast<PasteSource*>(userdata);
        if (self->text->empty()) return true;
        return writer.write(writer.userdata, reinterpret_cast<const uint8_t*>(self->text->data()), self->text->size());
    }
};
}  // namespace

int TerminalLayer::paste(const std::string& utf8, bool allow_unsafe) {
    if (!term_) throw std::logic_error("TerminalLayer has no size yet");
    static const char kMime[] = "text/plain;charset=utf-8";
    GhosttyString mime{reinterpret_cast<const uint8_t*>(kMime), sizeof(kMime) - 1};
    PasteSource src{&utf8};
    GhosttyPaste p = GHOSTTY_INIT_SIZED(GhosttyPaste);
    p.location = GHOSTTY_CLIPBOARD_LOCATION_STANDARD;
    p.source = GHOSTTY_PASTE_SOURCE_CLIPBOARD;
    p.mimes = &mime;
    p.mimes_len = 1;
    p.reader = GhosttyMimeReader{&PasteSource::read, &src};
    p.allow_unsafe = allow_unsafe;
    bool pasted = false;
    GhosttyResult r = ghostty_terminal_paste(term_, &p, &pasted);
    if (callback_failed_) {
        callback_failed_ = false;
        throw std::runtime_error("libghostty-vt: a terminal callback failed (out of memory?)");
    }
    if (r == GHOSTTY_REJECTED) return r;
    ck(r, "ghostty_terminal_paste");
    return r;
}

// =============================================================================
// Drawing
// =============================================================================

void TerminalLayer::fillChunkVertices(int chunk_x, int chunk_y, float cw, float ch,
                                      float ox, float oy, float s, std::vector<sf::Vertex>& verts) const {
    const PyTexture& tex = *texture;
    const FontAtlasData& fa = *tex.font_atlas;
    const int sheet_w = tex.getSheetWidth();
    const int sprite_count = tex.getSpriteCount();
    const float sw = static_cast<float>(tex.sprite_width), sh = static_cast<float>(tex.sprite_height);
    const float fit_x = cw / sw, fit_y = ch / sh;
    // The middle of the white tile: no neighbouring texel is sampled at any filtering.
    const float wu = (fa.white_tile % sheet_w) * sw + sw * 0.5f;
    const float wv = (fa.white_tile / sheet_w) * sh + sh * 0.5f;

    int start_x, start_y, end_x, end_y;
    getChunkBounds(chunk_x, chunk_y, start_x, start_y, end_x, end_y);

    auto solid = [&](float x0, float y0, float x1, float y1, sf::Color c) {
        const sf::Vector2f uv(wu, wv);
        const sf::Vector2f a(ox + x0 * s, oy + y0 * s), b(ox + x1 * s, oy + y0 * s);
        const sf::Vector2f d(ox + x0 * s, oy + y1 * s), e(ox + x1 * s, oy + y1 * s);
        verts.emplace_back(a, c, uv); verts.emplace_back(d, c, uv); verts.emplace_back(b, c, uv);
        verts.emplace_back(b, c, uv); verts.emplace_back(d, c, uv); verts.emplace_back(e, c, uv);
    };
    auto glyph = [&](int tile, float x0, float y0, float shear_top, float shear_bottom, sf::Color c) {
        const float u = static_cast<float>((tile % sheet_w) * tex.sprite_width);
        const float v = static_cast<float>((tile / sheet_w) * tex.sprite_height);
        const sf::Vector2f a(ox + (x0 + shear_top) * s, oy + y0 * s), b(ox + (x0 + cw + shear_top) * s, oy + y0 * s);
        const sf::Vector2f d(ox + (x0 + shear_bottom) * s, oy + (y0 + ch) * s);
        const sf::Vector2f e(ox + (x0 + cw + shear_bottom) * s, oy + (y0 + ch) * s);
        verts.emplace_back(a, c, sf::Vector2f(u, v)); verts.emplace_back(d, c, sf::Vector2f(u, v + sh));
        verts.emplace_back(b, c, sf::Vector2f(u + sw, v));
        verts.emplace_back(b, c, sf::Vector2f(u + sw, v)); verts.emplace_back(d, c, sf::Vector2f(u, v + sh));
        verts.emplace_back(e, c, sf::Vector2f(u + sw, v + sh));
    };

    const bool hide_blink = blink_interval_ms_ > 0 && !blink_on_;
    // Pass 1: backgrounds. Default-background cells only when `background` is set.
    for (int y = start_y; y < end_y; ++y) {
        const float py = (y - start_y) * ch;
        for (int x = start_x; x < end_x; ++x) {
            const size_t i = static_cast<size_t>(y) * grid_x + x;
            const float px = (x - start_x) * cw;
            if (!(flags_[i] & CF_DEFAULT_BG)) solid(px, py, px + cw, py + ch, bg_[i]);
            else if (has_background_ && background_.a > 0) solid(px, py, px + cw, py + ch, background_);
        }
    }
    // Pass 2: glyphs (bold faked by a second quad 1 atlas pixel right, italic by shearing).
    const float ascent = fa.ascent * fit_y;
    const float bold_dx = fit_x;
    for (int y = start_y; y < end_y; ++y) {
        const float py = (y - start_y) * ch;
        for (int x = start_x; x < end_x; ++x) {
            const size_t i = static_cast<size_t>(y) * grid_x + x;
            const int tile = tiles[i];
            const uint16_t fl = flags_[i];
            if (tile < 0 || tile >= sprite_count) continue;
            if (fl & CF_INVISIBLE) continue;
            if ((fl & CF_BLINK) && hide_blink) continue;
            const float px = (x - start_x) * cw;
            float st = 0.f, sb = 0.f;
            if (fl & CF_FAKE_ITALIC) { st = ascent * 0.2f; sb = -(ch - ascent) * 0.2f; }
            glyph(tile, px, py, st, sb, fg_[i]);
            if (fl & CF_FAKE_BOLD) glyph(tile, px + bold_dx, py, st, sb, fg_[i]);
        }
    }
    // Pass 3: lines, in the foreground colour, at the font's metrics.
    const float ul_h = std::max(1.0f, std::round(fa.underline_thickness * fit_y));
    const float ul_y = std::min(fa.underline_position * fit_y, ch - ul_h);
    // Double underline: a second stripe one stripe-gap below, or above when the cell has no room.
    const float ul2_y = (ul_y + 3 * ul_h <= ch) ? ul_y + 2 * ul_h : std::max(0.0f, ul_y - 2 * ul_h);
    const float st_h = std::max(1.0f, std::round(fa.strikethrough_thickness * fit_y));
    const float st_y = std::min(fa.strikethrough_position * fit_y, ch - st_h);
    for (int y = start_y; y < end_y; ++y) {
        const float py = (y - start_y) * ch;
        for (int x = start_x; x < end_x; ++x) {
            const size_t i = static_cast<size_t>(y) * grid_x + x;
            const uint16_t fl = flags_[i];
            if (!(fl & (CF_UNDERLINE | CF_STRIKE | CF_OVERLINE))) continue;
            if (fl & CF_INVISIBLE) continue;
            if ((fl & CF_BLINK) && hide_blink) continue;
            const float px = (x - start_x) * cw;
            const sf::Color c = fg_[i];
            if (fl & CF_UNDERLINE) {
                solid(px, py + ul_y, px + cw, py + ul_y + ul_h, c);
                if (fl & CF_UNDERLINE2) solid(px, py + ul2_y, px + cw, py + ul2_y + ul_h, c);
            }
            if (fl & CF_STRIKE) solid(px, py + st_y, px + cw, py + st_y + st_h, c);
            if (fl & CF_OVERLINE) solid(px, py, px + cw, py + ul_h, c);
        }
    }
}

// One buffer for every terminal layer: a chunk is built and drawn before the next one starts.
static std::vector<sf::Vertex>& terminalVertexScratch() {
    static std::vector<sf::Vertex> verts;
    return verts;
}

void TerminalLayer::renderChunkToTexture(int chunk_x, int chunk_y, int cell_width, int cell_height) {
    if (!texture || !texture->font_atlas) return;
    const int chunk_idx = chunk_y * chunks_x + chunk_x;
    if (chunk_idx < 0 || chunk_idx >= static_cast<int>(chunk_textures.size())) return;
    ensureChunkTexture(chunk_idx, cell_width, cell_height);
    if (!chunk_texture_initialized[chunk_idx]) return;

    auto& rt = *chunk_textures[chunk_idx];
    rt.clear(sf::Color::Transparent);
    auto& verts = terminalVertexScratch();
    verts.clear();
    fillChunkVertices(chunk_x, chunk_y, static_cast<float>(cell_width), static_cast<float>(cell_height),
                      0.f, 0.f, 1.f, verts);
    if (!verts.empty()) {
        sf::RenderStates states(&texture->sfTexture());
        states.blendMode = kCachePaintBlend;
        rt.draw(verts.data(), verts.size(), sf::Triangles, states);
    }
    rt.display();
    chunk_dirty[chunk_idx] = false;
    ++chunk_repaints;
    if (Resources::game) ++Resources::game->metrics.gridChunksRepainted;
}

void TerminalLayer::drawCursor(sf::RenderTarget& target, float left_spritepixels, float top_spritepixels,
                               float zoom, int cell_width, int cell_height) {
    if (!show_cursor || !cursor_in_view_ || !cursor_visible_) return;
    if (cursor_blinking_ && blink_interval_ms_ > 0 && !blink_on_) return;
    if (cursor_x_ >= grid_x || cursor_y_ >= grid_y) return;
    const PyTexture& tex = *texture;
    const FontAtlasData& fa = *tex.font_atlas;
    const int sheet_w = tex.getSheetWidth();
    const float sw = static_cast<float>(tex.sprite_width), sh = static_cast<float>(tex.sprite_height);
    const float cw = static_cast<float>(cell_width), ch = static_cast<float>(cell_height);
    const float fit_x = cw / sw, fit_y = ch / sh;
    const float wu = (fa.white_tile % sheet_w) * sw + sw * 0.5f, wv = (fa.white_tile / sheet_w) * sh + sh * 0.5f;

    // On the right half of a wide glyph the cursor covers the glyph (both cells).
    int x0 = cursor_x_;
    if (cursor_wide_ && x0 > 0) --x0;
    const size_t i0 = static_cast<size_t>(cursor_y_) * grid_x + x0;
    int span = 1;
    // Every stored index is checked against the atlas before it is used to look anything up.
    const int atlas_tiles = static_cast<int>(fa.tiles.size());
    if (x0 + 1 < grid_x && tiles[i0] >= 0 && tiles[i0] + 1 < atlas_tiles && tiles[i0 + 1] == tiles[i0] + 1 &&
        fa.tiles[tiles[i0] + 1].kind == FontAtlasData::Tile::GLYPH_RIGHT)
        span = 2;
    const float ox = (x0 * cw - left_spritepixels) * zoom, oy = (cursor_y_ * ch - top_spritepixels) * zoom;
    const float w = cw * span;

    std::vector<sf::Vertex> v;
    auto solid = [&](float a, float b, float c, float d, sf::Color col) {
        const sf::Vector2f uv(wu, wv);
        const sf::Vector2f p0(ox + a * zoom, oy + b * zoom), p1(ox + c * zoom, oy + b * zoom);
        const sf::Vector2f p2(ox + a * zoom, oy + d * zoom), p3(ox + c * zoom, oy + d * zoom);
        v.emplace_back(p0, col, uv); v.emplace_back(p2, col, uv); v.emplace_back(p1, col, uv);
        v.emplace_back(p1, col, uv); v.emplace_back(p2, col, uv); v.emplace_back(p3, col, uv);
    };
    const float thin_x = std::max(1.0f, std::round(fit_x));
    const float thin_y = std::max(1.0f, std::round(fa.underline_thickness * fit_y));
    switch (cursor_style_) {
        case GHOSTTY_CURSOR_STYLE_BAR:
            solid(0, 0, std::max(thin_x, std::round(cw / 8)), ch, cursor_colour_);
            break;
        case GHOSTTY_CURSOR_STYLE_UNDERLINE:
            solid(0, ch - thin_y, w, ch, cursor_colour_);
            break;
        case GHOSTTY_CURSOR_STYLE_BLOCK_HOLLOW:
            solid(0, 0, w, thin_y, cursor_colour_);
            solid(0, ch - thin_y, w, ch, cursor_colour_);
            solid(0, 0, thin_x, ch, cursor_colour_);
            solid(w - thin_x, 0, w, ch, cursor_colour_);
            break;
        default: {   // block: the cell in the cursor colour, its glyph redrawn in the background colour
            solid(0, 0, w, ch, cursor_colour_);
            for (int k = 0; k < span; ++k) {
                const size_t i = i0 + k;
                const int tile = tiles[i];
                if (tile < 0 || tile >= tex.getSpriteCount() || (flags_[i] & CF_INVISIBLE)) continue;
                const sf::Color under = (flags_[i] & CF_DEFAULT_BG) ? default_bg_ : bg_[i];
                const float u = static_cast<float>((tile % sheet_w) * tex.sprite_width);
                const float tv = static_cast<float>((tile / sheet_w) * tex.sprite_height);
                const float gx = ox + k * cw * zoom;
                const sf::Vector2f p0(gx, oy), p1(gx + cw * zoom, oy), p2(gx, oy + ch * zoom), p3(gx + cw * zoom, oy + ch * zoom);
                v.emplace_back(p0, under, sf::Vector2f(u, tv)); v.emplace_back(p2, under, sf::Vector2f(u, tv + sh));
                v.emplace_back(p1, under, sf::Vector2f(u + sw, tv));
                v.emplace_back(p1, under, sf::Vector2f(u + sw, tv)); v.emplace_back(p2, under, sf::Vector2f(u, tv + sh));
                v.emplace_back(p3, under, sf::Vector2f(u + sw, tv + sh));
            }
            break;
        }
    }
    if (!v.empty()) target.draw(v.data(), v.size(), sf::Triangles, sf::RenderStates(&tex.sfTexture()));
}

void TerminalLayer::render(sf::RenderTarget& target,
                           float left_spritepixels, float top_spritepixels,
                           int left_edge, int top_edge, int x_limit, int y_limit,
                           float zoom, int cell_width, int cell_height) {
    try {
        sync(false);
    } catch (const std::exception& e) {
        // Inside the render pass there is no Python caller to raise to: report it the
        // way a failing engine callback is reported.
        PyErr_Format(PyExc_RuntimeError, "TerminalLayer '%s': %s", name.c_str(), e.what());
        mcrf::print_callback_exception();
        if (McRFPy_API::game && McRFPy_API::game->getConfig().exit_on_exception) McRFPy_API::signalPythonException();
        return;
    }
    if (!visible || !texture || !texture->font_atlas) return;
    if (drawn_with.lock() != texture) {
        std::fill(chunk_dirty.begin(), chunk_dirty.end(), true);
        drawn_with = texture;
    }
    if (x_limit <= 0 || y_limit <= 0) return;
    const int chunk_left = std::max(0, left_edge / CHUNK_SIZE);
    const int chunk_top = std::max(0, top_edge / CHUNK_SIZE);
    const int chunk_right = std::min(chunks_x - 1, (x_limit - 1) / CHUNK_SIZE);
    const int chunk_bottom = std::min(chunks_y - 1, (y_limit - 1) / CHUNK_SIZE);

    for (int cy = chunk_top; cy <= chunk_bottom; ++cy) {
        for (int cx = chunk_left; cx <= chunk_right; ++cx) {
            const int chunk_idx = cy * chunks_x + cx;
            if (chunk_dirty[chunk_idx] || !chunk_texture_initialized[chunk_idx])
                renderChunkToTexture(cx, cy, cell_width, cell_height);
            int start_x, start_y, end_x, end_y;
            getChunkBounds(cx, cy, start_x, start_y, end_x, end_y);
            const float dest_x = (start_x * cell_width - left_spritepixels) * zoom;
            const float dest_y = (start_y * cell_height - top_spritepixels) * zoom;
            if (!chunk_texture_initialized[chunk_idx]) {
                // No chunk texture (#470): the same vertices, straight onto the target.
                auto& verts = terminalVertexScratch();
                verts.clear();
                fillChunkVertices(cx, cy, static_cast<float>(cell_width), static_cast<float>(cell_height),
                                  dest_x, dest_y, zoom, verts);
                if (!verts.empty())
                    target.draw(verts.data(), verts.size(), sf::Triangles, sf::RenderStates(&texture->sfTexture()));
                continue;
            }
            sf::Sprite chunk_sprite(chunk_textures[chunk_idx]->getTexture());
            chunk_sprite.setPosition(sf::Vector2f(dest_x, dest_y));
            chunk_sprite.setScale(sf::Vector2f(zoom, zoom));
            target.draw(chunk_sprite, kPremultipliedBlend);
        }
    }
    // The cursor is drawn over the cached chunks, never into them.
    drawCursor(target, left_spritepixels, top_spritepixels, zoom, cell_width, cell_height);
}

// =============================================================================
// Python API
// =============================================================================

namespace {

// The TerminalLayer behind a wrapper; RuntimeError when there is none (or when
// TileLayer.__init__ was run on the wrapper and replaced it with a plain TileLayer).
std::shared_ptr<TerminalLayer> layer_of(PyObject* self) {
    auto* o = reinterpret_cast<PyTileLayerObject*>(self);
    auto L = std::dynamic_pointer_cast<TerminalLayer>(o->data);
    if (!L) PyErr_SetString(PyExc_RuntimeError, "TerminalLayer is not initialized");
    return L;
}

// A C++ exception from the emulator layer as the matching Python exception.
void raise_from(const std::exception& e) {
    if (dynamic_cast<const std::invalid_argument*>(&e)) PyErr_SetString(PyExc_ValueError, e.what());
    else PyErr_SetString(PyExc_RuntimeError, e.what());
}

bool require_size(const std::shared_ptr<TerminalLayer>& L) {
    if (L->hasTerminal() && L->grid_x > 0 && L->grid_y > 0) return true;
    PyErr_SetString(PyExc_RuntimeError,
                    "TerminalLayer has no size yet: give grid_size= or attach it to a Grid");
    return false;
}

// Deliver pending output to on_output, in order. Re-entrant: a write() from inside the
// callback only queues its replies, and this loop hands them over after the callback
// returns. Holds the callable for the length of each call (the callback may replace it).
// Returns false with the callback's exception set; output queued during that failed call
// stays queued for the next delivery.
bool flush(const std::shared_ptr<TerminalLayer>& L) {
    if (L->flushing) return true;
    L->flushing = true;
    bool ok = true;
    while (!L->pending_output.empty()) {
        std::string chunk;
        chunk.swap(L->pending_output);
        PyObject* cb = L->on_output;
        if (!cb) continue;   // no on_output: the bytes are dropped (documented)
        Py_INCREF(cb);
        PyObject* data = PyBytes_FromStringAndSize(chunk.data(), static_cast<Py_ssize_t>(chunk.size()));
        PyObject* r = data ? PyObject_CallOneArg(cb, data) : nullptr;
        Py_XDECREF(data);
        Py_DECREF(cb);
        if (!r) { ok = false; break; }
        Py_DECREF(r);
    }
    L->flushing = false;
    return ok;
}

// Feed terminal input, then deliver whatever the terminal answered.
bool feed_and_flush(const std::shared_ptr<TerminalLayer>& L, const std::string& bytes) {
    if (!require_size(L)) return false;
    try {
        L->feed(bytes);
    } catch (const std::exception& e) {
        raise_from(e);
        return false;
    }
    return flush(L);
}

void utf8_append(std::string& out, uint32_t cp) { appendUtf8(out, cp); }

// The terminal's width for a codepoint (the table Texture.from_font shares, generated from
// libghostty-vt's rule: see tools/generate_east_asian_wide.py).
bool terminal_wide(uint32_t cp) {
    const auto* first = EAST_ASIAN_WIDE_RANGES;
    const auto* last = first + sizeof(EAST_ASIAN_WIDE_RANGES) / sizeof(EAST_ASIAN_WIDE_RANGES[0]);
    const auto* it = std::lower_bound(first, last, cp,
        [](const EastAsianWideRange& r, uint32_t c) { return r.hi < c; });
    return it != last && cp >= it->lo;
}

// Zero width in a terminal cell (same generator and rule): a combining mark, ZWJ, variation
// selector, ... attaches to the cell before it and cannot occupy a cell by itself.
bool terminal_zero_width(uint32_t cp) {
    const auto* first = ZERO_WIDTH_RANGES;
    const auto* last = first + sizeof(ZERO_WIDTH_RANGES) / sizeof(ZERO_WIDTH_RANGES[0]);
    const auto* it = std::lower_bound(first, last, cp,
        [](const EastAsianWideRange& r, uint32_t c) { return r.hi < c; });
    return it != last && cp >= it->lo;
}

// A codepoint the layer may print as text: not a C0 control, DEL or a C1 control.
bool printable_cp(uint32_t cp) {
    return !(cp < 0x20 || (cp >= 0x7F && cp <= 0x9F));
}

// The codepoint and face of a tile index on a font texture. ValueError for an index that
// has none: -1, out of range, the box, the white tile, a right half, padding.
bool glyph_of(const std::shared_ptr<TerminalLayer>& L, long long index, uint32_t* cp, int* face, bool* wide) {
    const FontAtlasData* fa = L->texture ? L->texture->font_atlas.get() : nullptr;
    if (!fa) {
        PyErr_SetString(PyExc_RuntimeError, "TerminalLayer's texture is not a font atlas");
        return false;
    }
    const long long n = static_cast<long long>(fa->tiles.size());
    if (index < 0 || index >= n || fa->tiles[index].kind != FontAtlasData::Tile::GLYPH) {
        const char* what = "outside the texture's tiles";
        if (index >= 0 && index < n) {
            switch (fa->tiles[index].kind) {
                case FontAtlasData::Tile::BOX: what = "the box tile"; break;
                case FontAtlasData::Tile::WHITE: what = "the white tile"; break;
                case FontAtlasData::Tile::GLYPH_RIGHT: what = "the right half of a wide glyph"; break;
                default: what = "a padding tile"; break;
            }
        }
        PyErr_Format(PyExc_ValueError,
                     "tile index %lld has no codepoint (%s); a TerminalLayer cell can only show a glyph "
                     "of its texture", index, what);
        return false;
    }
    *cp = fa->tiles[index].codepoint;
    *face = fa->tiles[index].face;
    if (!printable_cp(*cp)) {
        PyErr_Format(PyExc_ValueError,
                     "tile index %lld is the control character U+%04X, which a terminal does not print "
                     "(send control sequences with write())", index, static_cast<unsigned>(*cp));
        return false;
    }
    if (terminal_zero_width(*cp)) {
        PyErr_Format(PyExc_ValueError,
                     "tile index %lld is U+%04X, which has zero width: it combines with the character "
                     "before it and cannot occupy a cell by itself", index, static_cast<unsigned>(*cp));
        return false;
    }
    *wide = index + 1 < n && fa->tiles[index + 1].kind == FontAtlasData::Tile::GLYPH_RIGHT;
    return true;
}

// Wrap terminal input written by the layer (not by the program) so that it lands at
// absolute cells in plain ASCII, never writes outside the cells it targets and leaves no
// trace: the cursor, its attributes, origin mode and the character set are saved (DECSC)
// and restored (DECRC); insert mode and autowrap (DECAWM), which DECSC does not save, are
// switched off and back on. With autowrap off nothing placed can wrap or scroll the screen.
// Ask the terminal something and take its reply out of the output queue (it is the layer's
// question, not the program's): DECRQSS for the left/right margins.
std::string ask(const std::shared_ptr<TerminalLayer>& L, const std::string& query) {
    const size_t before = L->pending_output.size();
    L->feed(query);
    std::string reply = L->pending_output.substr(before);
    L->pending_output.resize(before);
    return reply;
}

struct Placement {
    std::string pre, post;
    explicit Placement(const std::shared_ptr<TerminalLayer>& L) {
        const bool origin = L->modeEnabled(6, false);
        const bool insert = L->modeEnabled(4, true);
        const bool autowrap = L->modeEnabled(7, false);
        const bool lr_margins = L->modeEnabled(69, false);
        std::string margins;   // "l;r", restored exactly
        if (lr_margins) {
            const std::string reply = ask(L, "\x1bP$qs\x1b\\");   // DCS 1 $ r Pl ; Pr s ST
            const size_t a = reply.find("$r"), b = reply.find('s', a == std::string::npos ? 0 : a);
            if (a == std::string::npos || b == std::string::npos || reply.compare(0, 3, "\x1bP1") != 0)
                throw std::runtime_error("TerminalLayer: the terminal did not report its left/right margins");
            margins = reply.substr(a + 2, b - a - 2);
        }
        pre = "\x1b" "7";   // DECSC: position, pen, protection, pending wrap, origin, charsets
        if (origin) pre += "\x1b[?6l";
        if (insert) pre += "\x1b[4l";
        if (autowrap) pre += "\x1b[?7l";
        if (lr_margins) pre += "\x1b[?69l";   // margins off: full width
        pre += "\x1b[0\"q";                    // DECSCA off: placed cells are unprotected
        pre += "\x1b(B\x0f";
        if (lr_margins) post += "\x1b[?69h\x1b[" + margins + "s";   // DECSLRM homes; DECRC moves back
        if (insert) post += "\x1b[4h";
        if (autowrap) post += "\x1b[?7h";
        post += "\x1b" "8";
    }
};


std::string cup(int x, int y) {
    return "\x1b[" + std::to_string(y + 1) + ";" + std::to_string(x + 1) + "H";
}

std::string face_sgr(int face) {
    if (face == FontAtlasData::BOLD) return "\x1b[0;1m";
    if (face == FontAtlasData::ITALIC) return "\x1b[0;3m";
    return "\x1b[0m";
}

// Print the glyph of `index` over the rectangle [x1, x2) x [y1, y2) (already clipped),
// one CUP + glyph + REP per row.
bool fill_through_terminal(const std::shared_ptr<TerminalLayer>& L, int x1, int y1, int x2, int y2, long long index) {
    uint32_t cp; int face; bool wide;
    if (!glyph_of(L, index, &cp, &face, &wide)) return false;
    if (x2 <= x1 || y2 <= y1) return true;
    const int w = x2 - x1;
    // A wide glyph fills the rectangle in pairs of cells; an odd last column is blanked.
    const bool odd_tail = wide && (w % 2) != 0;
    std::string glyph;
    utf8_append(glyph, cp);
    const int count = wide ? w / 2 : w;
    std::string seq;
    try {
        Placement p(L);
        seq = p.pre + face_sgr(face);
        for (int y = y1; y < y2; ++y) {
            seq += cup(x1, y);
            if (count > 0) {
                seq += glyph;
                if (count > 1) seq += "\x1b[" + std::to_string(count - 1) + "b";   // REP
            }
            if (odd_tail) seq += cup(x2 - 1, y) + "\x1b[0m \x1b[0" + face_sgr(face).substr(3);
        }
        seq += p.post;
    } catch (const std::exception& e) {
        raise_from(e);
        return false;
    }
    return feed_and_flush(L, seq);
}

bool check_cell(const std::shared_ptr<TerminalLayer>& L, int x, int y) {
    if (x < 0 || x >= L->grid_x || y < 0 || y >= L->grid_y) {
        PyErr_Format(PyExc_IndexError, "Position (%d, %d) out of bounds for TerminalLayer of size (%d, %d)",
                     x, y, L->grid_x, L->grid_y);
        return false;
    }
    return true;
}

// set(): one cell (two for a wide glyph, which must fit).
bool set_through_terminal(const std::shared_ptr<TerminalLayer>& L, int x, int y, long long index) {
    if (!check_cell(L, x, y)) return false;
    uint32_t cp; int face; bool wide;
    if (!glyph_of(L, index, &cp, &face, &wide)) return false;
    if (wide && x + 1 >= L->grid_x) {
        PyErr_Format(PyExc_ValueError, "tile index %lld is a wide glyph and does not fit at the last column", index);
        return false;
    }
    return fill_through_terminal(L, x, y, x + (wide ? 2 : 1), y + 1, index);
}

// mods: None (the modifiers of the key event being handled), a str like "ctrl+shift", or an
// iterable of names. Result in GHOSTTY_MODS_* bits.
bool parse_mods(PyObject* obj, unsigned* out) {
    *out = 0;
    if (!obj || obj == Py_None) {
        if (McRFPy_API::game) {
            const auto& m = McRFPy_API::game->keyModifiers();
            if (m.shift) *out |= GHOSTTY_MODS_SHIFT;
            if (m.ctrl) *out |= GHOSTTY_MODS_CTRL;
            if (m.alt) *out |= GHOSTTY_MODS_ALT;
            if (m.system) *out |= GHOSTTY_MODS_SUPER;
        }
        return true;
    }
    auto add = [&](const std::string& name) -> bool {
        if (name == "shift") *out |= GHOSTTY_MODS_SHIFT;
        else if (name == "ctrl") *out |= GHOSTTY_MODS_CTRL;
        else if (name == "alt") *out |= GHOSTTY_MODS_ALT;
        else if (name == "super" || name == "system") *out |= GHOSTTY_MODS_SUPER;
        else {
            PyErr_Format(PyExc_ValueError, "unknown modifier '%s' (use shift, ctrl, alt, super)", name.c_str());
            return false;
        }
        return true;
    };
    if (PyUnicode_Check(obj)) {
        const char* s = PyUnicode_AsUTF8(obj);
        if (!s) return false;
        std::string all(s), part;
        std::stringstream ss(all);
        while (std::getline(ss, part, '+')) {
            if (part.empty()) continue;
            if (!add(part)) return false;
        }
        return true;
    }
    PyObject* it = PyObject_GetIter(obj);
    if (!it) {
        PyErr_SetString(PyExc_TypeError, "mods must be None, a str such as 'ctrl+shift', or an iterable of str");
        return false;
    }
    PyObject* item;
    while ((item = PyIter_Next(it))) {
        if (!PyUnicode_Check(item)) {
            Py_DECREF(item); Py_DECREF(it);
            PyErr_SetString(PyExc_TypeError, "mods must contain only str");
            return false;
        }
        const char* s = PyUnicode_AsUTF8(item);
        bool ok = s && add(s);
        Py_DECREF(item);
        if (!ok) { Py_DECREF(it); return false; }
    }
    Py_DECREF(it);
    return !PyErr_Occurred();
}

// InputState member (or its int value): 0 PRESSED, 1 RELEASED, 2 REPEATED.
bool parse_state(PyObject* obj, int* out) {
    PyObject* v = nullptr;
    if (PyInputState::input_state_enum_class && PyObject_TypeCheck(obj, (PyTypeObject*)PyInputState::input_state_enum_class)) {
        v = PyObject_GetAttrString(obj, "value");
        if (!v) return false;
    } else if (PyLong_Check(obj) && !PyBool_Check(obj)) {
        v = Py_NewRef(obj);
    } else {
        PyErr_SetString(PyExc_TypeError, "state must be an InputState");
        return false;
    }
    long s = PyLong_AsLong(v);
    Py_DECREF(v);
    if (s == -1 && PyErr_Occurred()) return false;
    if (s < 0 || s > 2) {
        PyErr_Format(PyExc_ValueError, "invalid InputState value %ld", s);
        return false;
    }
    *out = static_cast<int>(s);
    return true;
}

// sf::Keyboard key -> libghostty key, and the character the key types unshifted (0 for keys
// that type nothing).
struct KeyEntry { int sf_key; int gkey; uint32_t text; };

bool lookup_key(sf::Keyboard::Key k, KeyEntry* out) {
    static const KeyEntry table[] = {
        {sf::Keyboard::Escape, GHOSTTY_KEY_ESCAPE, 0},
        {sf::Keyboard::LControl, GHOSTTY_KEY_CONTROL_LEFT, 0}, {sf::Keyboard::RControl, GHOSTTY_KEY_CONTROL_RIGHT, 0},
        {sf::Keyboard::LShift, GHOSTTY_KEY_SHIFT_LEFT, 0}, {sf::Keyboard::RShift, GHOSTTY_KEY_SHIFT_RIGHT, 0},
        {sf::Keyboard::LAlt, GHOSTTY_KEY_ALT_LEFT, 0}, {sf::Keyboard::RAlt, GHOSTTY_KEY_ALT_RIGHT, 0},
        {sf::Keyboard::LSystem, GHOSTTY_KEY_META_LEFT, 0}, {sf::Keyboard::RSystem, GHOSTTY_KEY_META_RIGHT, 0},
        {sf::Keyboard::Menu, GHOSTTY_KEY_CONTEXT_MENU, 0},
        {sf::Keyboard::LBracket, GHOSTTY_KEY_BRACKET_LEFT, '['}, {sf::Keyboard::RBracket, GHOSTTY_KEY_BRACKET_RIGHT, ']'},
        {sf::Keyboard::Semicolon, GHOSTTY_KEY_SEMICOLON, ';'}, {sf::Keyboard::Comma, GHOSTTY_KEY_COMMA, ','},
        {sf::Keyboard::Period, GHOSTTY_KEY_PERIOD, '.'}, {sf::Keyboard::Apostrophe, GHOSTTY_KEY_QUOTE, '\''},
        {sf::Keyboard::Slash, GHOSTTY_KEY_SLASH, '/'}, {sf::Keyboard::Backslash, GHOSTTY_KEY_BACKSLASH, '\\'},
        {sf::Keyboard::Grave, GHOSTTY_KEY_BACKQUOTE, '`'}, {sf::Keyboard::Equal, GHOSTTY_KEY_EQUAL, '='},
        {sf::Keyboard::Hyphen, GHOSTTY_KEY_MINUS, '-'}, {sf::Keyboard::Space, GHOSTTY_KEY_SPACE, ' '},
        {sf::Keyboard::Enter, GHOSTTY_KEY_ENTER, 0}, {sf::Keyboard::Backspace, GHOSTTY_KEY_BACKSPACE, 0},
        {sf::Keyboard::Tab, GHOSTTY_KEY_TAB, 0},
        {sf::Keyboard::PageUp, GHOSTTY_KEY_PAGE_UP, 0}, {sf::Keyboard::PageDown, GHOSTTY_KEY_PAGE_DOWN, 0},
        {sf::Keyboard::End, GHOSTTY_KEY_END, 0}, {sf::Keyboard::Home, GHOSTTY_KEY_HOME, 0},
        {sf::Keyboard::Insert, GHOSTTY_KEY_INSERT, 0}, {sf::Keyboard::Delete, GHOSTTY_KEY_DELETE, 0},
        {sf::Keyboard::Add, GHOSTTY_KEY_NUMPAD_ADD, '+'}, {sf::Keyboard::Subtract, GHOSTTY_KEY_NUMPAD_SUBTRACT, '-'},
        {sf::Keyboard::Multiply, GHOSTTY_KEY_NUMPAD_MULTIPLY, '*'}, {sf::Keyboard::Divide, GHOSTTY_KEY_NUMPAD_DIVIDE, '/'},
        {sf::Keyboard::Left, GHOSTTY_KEY_ARROW_LEFT, 0}, {sf::Keyboard::Right, GHOSTTY_KEY_ARROW_RIGHT, 0},
        {sf::Keyboard::Up, GHOSTTY_KEY_ARROW_UP, 0}, {sf::Keyboard::Down, GHOSTTY_KEY_ARROW_DOWN, 0},
        {sf::Keyboard::Pause, GHOSTTY_KEY_PAUSE, 0},
    };
    const int kv = static_cast<int>(k);
    if (kv >= sf::Keyboard::A && kv <= sf::Keyboard::Z) {
        *out = {kv, GHOSTTY_KEY_A + (kv - sf::Keyboard::A), static_cast<uint32_t>('a' + (kv - sf::Keyboard::A))};
        return true;
    }
    if (kv >= sf::Keyboard::Num0 && kv <= sf::Keyboard::Num9) {
        *out = {kv, GHOSTTY_KEY_DIGIT_0 + (kv - sf::Keyboard::Num0), static_cast<uint32_t>('0' + (kv - sf::Keyboard::Num0))};
        return true;
    }
    if (kv >= sf::Keyboard::Numpad0 && kv <= sf::Keyboard::Numpad9) {
        *out = {kv, GHOSTTY_KEY_NUMPAD_0 + (kv - sf::Keyboard::Numpad0), static_cast<uint32_t>('0' + (kv - sf::Keyboard::Numpad0))};
        return true;
    }
    if (kv >= sf::Keyboard::F1 && kv <= sf::Keyboard::F15) {
        *out = {kv, GHOSTTY_KEY_F1 + (kv - sf::Keyboard::F1), 0};
        return true;
    }
    for (const auto& e : table) {
        if (e.sf_key == kv) { *out = e; return true; }
    }
    return false;
}

// One SGR parameter group for print()'s fg=/bg=: an int 0-255 is a palette index,
// anything a Color accepts is truecolor. Terminal colours are opaque.
bool colour_sgr(PyObject* value, bool fg, std::string& out) {
    if (PyLong_Check(value) && !PyBool_Check(value)) {
        long n = PyLong_AsLong(value);
        if (n == -1 && PyErr_Occurred()) return false;
        if (n < 0 || n > 255) {
            PyErr_Format(PyExc_ValueError, "palette index must be 0-255 (got %ld)", n);
            return false;
        }
        out += fg ? ";38;5;" : ";48;5;";
        out += std::to_string(n);
        return true;
    }
    sf::Color c;
    if (!PyColor::to_color(value, c)) return false;
    if (c.a != 255) {
        PyErr_Format(PyExc_ValueError, "terminal colours are opaque (got alpha %d)", c.a);
        return false;
    }
    out += fg ? ";38;2;" : ";48;2;";
    out += std::to_string(c.r) + ";" + std::to_string(c.g) + ";" + std::to_string(c.b);
    return true;
}

}  // namespace

namespace TerminalLayerAPI {

bool set_cell(const std::shared_ptr<TerminalLayer>& layer, int x, int y, long long index) {
    if (!require_size(layer)) return false;
    return set_through_terminal(layer, x, y, index);
}

void flush_from_engine(const std::shared_ptr<TerminalLayer>& layer) {
    // Keep any exception the caller has pending: this delivery is not part of it.
    PyObject *t, *v, *tb;
    PyErr_Fetch(&t, &v, &tb);
    if (!flush(layer)) {
        mcrf::print_callback_exception();
        if (McRFPy_API::game && McRFPy_API::game->getConfig().exit_on_exception) McRFPy_API::signalPythonException();
    }
    PyErr_Restore(t, v, tb);
}

}  // namespace TerminalLayerAPI

// ---- methods -------------------------------------------------------------------------

static PyObject* TL_write(PyObject* self, PyObject* arg) {
    auto L = layer_of(self);
    if (!L) return nullptr;
    std::string bytes;
    if (PyUnicode_Check(arg)) {
        Py_ssize_t n = 0;
        const char* s = PyUnicode_AsUTF8AndSize(arg, &n);
        if (!s) return nullptr;
        bytes.assign(s, static_cast<size_t>(n));
    } else {
        Py_buffer view;
        if (PyObject_GetBuffer(arg, &view, PyBUF_SIMPLE) < 0) {
            PyErr_Clear();
            PyErr_Format(PyExc_TypeError, "write() takes bytes, a bytes-like object or str, not %s",
                         Py_TYPE(arg)->tp_name);
            return nullptr;
        }
        bytes.assign(static_cast<const char*>(view.buf), static_cast<size_t>(view.len));
        PyBuffer_Release(&view);
    }
    if (!feed_and_flush(L, bytes)) return nullptr;
    Py_RETURN_NONE;
}

static PyObject* TL_key(PyObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"key", "state", "mods", NULL};
    PyObject *key_obj, *state_obj = nullptr, *mods_obj = nullptr;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OO", const_cast<char**>(kwlist), &key_obj, &state_obj, &mods_obj))
        return nullptr;
    sf::Keyboard::Key key;
    if (!PyKey::from_arg(key_obj, &key)) return nullptr;
    int state = 0;
    if (state_obj && state_obj != Py_None && !parse_state(state_obj, &state)) return nullptr;
    unsigned mods = 0;
    if (!parse_mods(mods_obj, &mods)) return nullptr;
    auto L = layer_of(self);
    if (!L || !require_size(L)) return nullptr;
    KeyEntry e;
    if (!lookup_key(key, &e)) {
        PyErr_Format(PyExc_ValueError, "key %d has no terminal encoding", static_cast<int>(key));
        return nullptr;
    }
    const int action = state == 1 ? GHOSTTY_KEY_ACTION_RELEASE : state == 2 ? GHOSTTY_KEY_ACTION_REPEAT
                                                                            : GHOSTTY_KEY_ACTION_PRESS;
    try {
        if (e.text) {
            // A key that types a character sends it through text() (on_text); here it is
            // encoded only as a combination (Ctrl, Alt, Super), as the encoder derives it
            // from the key, so typing is never sent twice.
            if (!(mods & (GHOSTTY_MODS_CTRL | GHOSTTY_MODS_ALT | GHOSTTY_MODS_SUPER))) Py_RETURN_NONE;
            if ((mods & GHOSTTY_MODS_SHIFT) && L->kittyKeyboardFlags() == 0) mods &= ~GHOSTTY_MODS_SHIFT;
            std::string t;
            utf8_append(t, e.text);
            L->encodeKey(e.gkey, action, mods, t, e.text);
        } else {
            L->encodeKey(e.gkey, action, mods, std::string(), 0);
        }
    } catch (const std::exception& ex) {
        raise_from(ex);
        return nullptr;
    }
    if (!flush(L)) return nullptr;
    Py_RETURN_NONE;
}

static PyObject* TL_text(PyObject* self, PyObject* arg) {
    if (!PyUnicode_Check(arg)) {
        PyErr_Format(PyExc_TypeError, "text() takes a str, not %s", Py_TYPE(arg)->tp_name);
        return nullptr;
    }
    auto L = layer_of(self);
    if (!L || !require_size(L)) return nullptr;
    const Py_ssize_t n = PyUnicode_GET_LENGTH(arg);
    for (Py_ssize_t i = 0; i < n; ++i) {
        const Py_UCS4 cp = PyUnicode_READ_CHAR(arg, i);
        if (cp < 0x20 || (cp >= 0x7F && cp <= 0x9F)) {
            PyErr_Format(PyExc_ValueError, "text() takes printable text; U+%04X is a key (use key())",
                         static_cast<unsigned>(cp));
            return nullptr;
        }
        if (cp >= 0xD800 && cp <= 0xDFFF) {
            PyErr_SetString(PyExc_ValueError, "text() cannot send a lone surrogate");
            return nullptr;
        }
    }
    try {
        for (Py_ssize_t i = 0; i < n; ++i) {
            const Py_UCS4 cp = PyUnicode_READ_CHAR(arg, i);
            std::string t;
            utf8_append(t, cp);
            // No key identity: text from an input method or a layout we know nothing about.
            L->encodeKey(GHOSTTY_KEY_UNIDENTIFIED, GHOSTTY_KEY_ACTION_PRESS, 0, t, cp);
        }
    } catch (const std::exception& e) {
        raise_from(e);
        return nullptr;
    }
    if (!flush(L)) return nullptr;
    Py_RETURN_NONE;
}

static PyObject* TL_mouse(PyObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"pos", "button", "state", "mods", NULL};
    PyObject *pos_obj, *button_obj = nullptr, *state_obj = nullptr, *mods_obj = nullptr;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OOO", const_cast<char**>(kwlist),
                                     &pos_obj, &button_obj, &state_obj, &mods_obj))
        return nullptr;
    float x, y;
    if (!PyPosition_FromObject(pos_obj, &x, &y, "pos")) return nullptr;
    int button = 0;
    if (button_obj && button_obj != Py_None) {
        // The MouseButton value as an int: the wheel values (10-13) are not sf::Mouse::Button
        // enumerators, so they are never loaded through that enum type.
        long b = -1;
        if (PyMouseButton::mouse_button_enum_class &&
            PyObject_TypeCheck(button_obj, (PyTypeObject*)PyMouseButton::mouse_button_enum_class)) {
            PyObject* v = PyObject_GetAttrString(button_obj, "value");
            if (!v) return nullptr;
            b = PyLong_AsLong(v);
            Py_DECREF(v);
            if (b == -1 && PyErr_Occurred()) return nullptr;
        } else {
            PyErr_SetString(PyExc_TypeError, "button must be a MouseButton or None");
            return nullptr;
        }
        switch (b) {
            case sf::Mouse::Left: button = GHOSTTY_MOUSE_BUTTON_LEFT; break;
            case sf::Mouse::Right: button = GHOSTTY_MOUSE_BUTTON_RIGHT; break;
            case sf::Mouse::Middle: button = GHOSTTY_MOUSE_BUTTON_MIDDLE; break;
            case sf::Mouse::XButton1: button = GHOSTTY_MOUSE_BUTTON_EIGHT; break;
            case sf::Mouse::XButton2: button = GHOSTTY_MOUSE_BUTTON_NINE; break;
            case 10: button = GHOSTTY_MOUSE_BUTTON_FOUR; break;    // SCROLL_UP
            case 11: button = GHOSTTY_MOUSE_BUTTON_FIVE; break;    // SCROLL_DOWN
            case 12: button = GHOSTTY_MOUSE_BUTTON_SIX; break;     // SCROLL_LEFT
            case 13: button = GHOSTTY_MOUSE_BUTTON_SEVEN; break;   // SCROLL_RIGHT
            default:
                PyErr_SetString(PyExc_ValueError, "unknown MouseButton");
                return nullptr;
        }
    }
    int action = GHOSTTY_MOUSE_ACTION_MOTION;
    if (state_obj && state_obj != Py_None) {
        int st = 0;
        if (!parse_state(state_obj, &st)) return nullptr;
        if (st == 2) {
            PyErr_SetString(PyExc_ValueError, "a mouse button has no REPEATED state");
            return nullptr;
        }
        action = st == 0 ? GHOSTTY_MOUSE_ACTION_PRESS : GHOSTTY_MOUSE_ACTION_RELEASE;
    } else if (button >= GHOSTTY_MOUSE_BUTTON_FOUR && button <= GHOSTTY_MOUSE_BUTTON_SEVEN) {
        action = GHOSTTY_MOUSE_ACTION_PRESS;   // a wheel step is a press
    }
    unsigned mods = 0;
    if (!parse_mods(mods_obj, &mods)) return nullptr;
    auto L = layer_of(self);
    if (!L || !require_size(L)) return nullptr;
    try {
        L->encodeMouse(x, y, button, action, mods);
    } catch (const std::exception& e) {
        raise_from(e);
        return nullptr;
    }
    if (!flush(L)) return nullptr;
    Py_RETURN_NONE;
}

static PyObject* TL_paste(PyObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"text", "allow_unsafe", NULL};
    PyObject* text_obj;
    int allow_unsafe = 0;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "U|p", const_cast<char**>(kwlist), &text_obj, &allow_unsafe))
        return nullptr;
    Py_ssize_t n = 0;
    const char* s = PyUnicode_AsUTF8AndSize(text_obj, &n);
    if (!s) return nullptr;
    auto L = layer_of(self);
    if (!L || !require_size(L)) return nullptr;
    int r;
    try {
        r = L->paste(std::string(s, static_cast<size_t>(n)), allow_unsafe != 0);
    } catch (const std::exception& e) {
        raise_from(e);
        return nullptr;
    }
    if (r == GHOSTTY_REJECTED) {
        PyErr_SetString(PyExc_ValueError,
                        "paste refused: the text could run commands (a line break outside bracketed paste "
                        "mode, or a bracketed-paste end sequence); pass allow_unsafe=True to send it anyway");
        return nullptr;
    }
    if (!flush(L)) return nullptr;
    Py_RETURN_NONE;
}

static PyObject* TL_focus(PyObject* self, PyObject* arg) {
    int gained = PyObject_IsTrue(arg);
    if (gained < 0) return nullptr;
    auto L = layer_of(self);
    if (!L || !require_size(L)) return nullptr;
    try {
        L->encodeFocus(gained != 0);
    } catch (const std::exception& e) {
        raise_from(e);
        return nullptr;
    }
    if (!flush(L)) return nullptr;
    Py_RETURN_NONE;
}

static PyObject* TL_move(PyObject* self, PyObject* args, PyObject* kwds) {
    int x, y;
    if (!PyPosition_ParseInt(args, kwds, &x, &y)) return nullptr;
    auto L = layer_of(self);
    if (!L || !require_size(L) || !check_cell(L, x, y)) return nullptr;
    if (!feed_and_flush(L, cup(x, y))) return nullptr;
    Py_RETURN_NONE;
}

static PyObject* TL_print(PyObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"text", "pos", "fg", "bg", "bold", "italic", "underline", "blink",
                                   "inverse", "strike", "faint", NULL};
    PyObject *text_obj, *pos_obj = nullptr, *fg_obj = nullptr, *bg_obj = nullptr;
    int bold = 0, italic = 0, underline = 0, blink = 0, inverse = 0, strike = 0, faint = 0;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "U|OOOppppppp", const_cast<char**>(kwlist),
                                     &text_obj, &pos_obj, &fg_obj, &bg_obj, &bold, &italic, &underline,
                                     &blink, &inverse, &strike, &faint))
        return nullptr;
    // Convert every argument before looking at the layer (user code may run in conversions).
    int px = 0, py = 0;
    const bool has_pos = pos_obj && pos_obj != Py_None;
    if (has_pos && !PyPosition_FromObjectInt(pos_obj, &px, &py, "pos")) return nullptr;
    std::string sgr = "\x1b[0";
    if (bold) sgr += ";1";
    if (faint) sgr += ";2";
    if (italic) sgr += ";3";
    if (underline) sgr += ";4";
    if (blink) sgr += ";5";
    if (inverse) sgr += ";7";
    if (strike) sgr += ";9";
    if (fg_obj && fg_obj != Py_None && !colour_sgr(fg_obj, true, sgr)) return nullptr;
    if (bg_obj && bg_obj != Py_None && !colour_sgr(bg_obj, false, sgr)) return nullptr;
    sgr += "m";
    // Text only: printable characters, "\n" and "\t". Anything else would be a control
    // sequence (a title change, a mode switch, a query whose reply the program would read as
    // input); write() is the path for raw bytes.
    std::vector<std::vector<uint32_t>> lines(1);
    const Py_ssize_t n = PyUnicode_GET_LENGTH(text_obj);
    for (Py_ssize_t i = 0; i < n; ++i) {
        const Py_UCS4 cp = PyUnicode_READ_CHAR(text_obj, i);
        if (cp == '\n') { lines.emplace_back(); continue; }
        if ((cp != '\t' && !printable_cp(cp)) || (cp >= 0xD800 && cp <= 0xDFFF)) {
            PyErr_Format(PyExc_ValueError,
                         "print() takes text: U+%04X at index %zd is a control character "
                         "(use write() for raw terminal sequences)", static_cast<unsigned>(cp), i);
            return nullptr;
        }
        // A zero-width codepoint combines with the character before it; with none (start of
        // the text, of a line, or after a tab) it would attach to whatever is on screen there.
        if (terminal_zero_width(cp) && (lines.back().empty() || lines.back().back() == '\t')) {
            PyErr_Format(PyExc_ValueError,
                         "print() text: U+%04X at index %zd has zero width and nothing before it to "
                         "combine with", static_cast<unsigned>(cp), i);
            return nullptr;
        }
        lines.back().push_back(cp);
    }

    auto L = layer_of(self);
    if (!L || !require_size(L)) return nullptr;
    if (has_pos && !check_cell(L, px, py)) return nullptr;
    std::string seq;
    try {
        if (has_pos) {
            // Placed text stays inside the layer: each line starts at pos's column on the next
            // row, a line is clipped at the right edge, and lines below the bottom row are dropped.
            Placement p(L);
            seq = p.pre + sgr;
            for (size_t k = 0; k < lines.size() && py + static_cast<int>(k) < L->grid_y; ++k) {
                seq += cup(px, py + static_cast<int>(k));
                // A tab is spaces to the next multiple of 8 columns from the line's start (the
                // program's tab stops do not apply). Zero-width codepoints follow their base
                // character: kept with it, dropped with it, and they take no column.
                int col = px;
                bool clipped = false;
                for (uint32_t cp : lines[k]) {
                    if (cp == '\t') {
                        const int to = col + (8 - (col - px) % 8);
                        while (col < to && col < L->grid_x) { seq += ' '; ++col; }
                        if (col < to) break;
                        continue;
                    }
                    if (terminal_zero_width(cp)) {
                        if (!clipped) utf8_append(seq, cp);
                        continue;
                    }
                    const int adv = terminal_wide(cp) ? 2 : 1;
                    if (col + adv > L->grid_x) { clipped = true; break; }
                    utf8_append(seq, cp);
                    col += adv;
                }
            }
            seq += p.post;
        } else {
            // At the cursor the terminal's own wrapping, scrolling and tab stops apply (a tab is
            // sent as HT); "\n" is CR LF.
            seq = sgr;
            for (size_t k = 0; k < lines.size(); ++k) {
                if (k) seq += "\r\n";
                for (uint32_t cp : lines[k]) utf8_append(seq, cp);
            }
            seq += "\x1b[0m";
        }
    } catch (const std::exception& e) {
        raise_from(e);
        return nullptr;
    }
    if (!feed_and_flush(L, seq)) return nullptr;
    Py_RETURN_NONE;
}

static PyObject* TL_clear(PyObject* self, PyObject* Py_UNUSED(args)) {
    auto L = layer_of(self);
    if (!L) return nullptr;
    if (!feed_and_flush(L, "\x1b[0m\x1b[H\x1b[2J")) return nullptr;
    Py_RETURN_NONE;
}

static PyObject* TL_clear_line(PyObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"y", NULL};
    PyObject* y_obj = nullptr;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|O", const_cast<char**>(kwlist), &y_obj)) return nullptr;
    long y = -1;
    const bool has_y = y_obj && y_obj != Py_None;
    if (has_y) {
        if (!PyLong_Check(y_obj) || PyBool_Check(y_obj)) {
            PyErr_SetString(PyExc_TypeError, "y must be an int or None");
            return nullptr;
        }
        y = PyLong_AsLong(y_obj);
        if (y == -1 && PyErr_Occurred()) return nullptr;
    }
    auto L = layer_of(self);
    if (!L || !require_size(L)) return nullptr;
    if (has_y && (y < 0 || y >= L->grid_y)) {
        PyErr_Format(PyExc_IndexError, "line %ld is outside 0..%d", y, L->grid_y - 1);
        return nullptr;
    }
    std::string seq;
    try {
        Placement p(L);
        seq = p.pre + (has_y ? cup(0, static_cast<int>(y)) : std::string()) + "\x1b[0m\x1b[2K" + p.post;
    } catch (const std::exception& e) {
        raise_from(e);
        return nullptr;
    }
    if (!feed_and_flush(L, seq)) return nullptr;
    Py_RETURN_NONE;
}

static PyObject* TL_screen_text(PyObject* self, PyObject* Py_UNUSED(args)) {
    auto L = layer_of(self);
    if (!L) return nullptr;
    std::string s;
    try {
        s = L->screenText();
    } catch (const std::exception& e) {
        raise_from(e);
        return nullptr;
    }
    return PyUnicode_DecodeUTF8(s.data(), static_cast<Py_ssize_t>(s.size()), "replace");
}

// An int argument, saturated to the long long range (scrolling clamps anyway).
static bool saturated_ll(PyObject* v, long long* out) {
    int overflow = 0;
    *out = PyLong_AsLongLongAndOverflow(v, &overflow);
    if (overflow) *out = overflow > 0 ? LLONG_MAX : LLONG_MIN;
    return !(*out == -1 && PyErr_Occurred());
}

static PyObject* TL_scroll(PyObject* self, PyObject* arg) {
    if (!PyLong_Check(arg) || PyBool_Check(arg)) {
        PyErr_SetString(PyExc_TypeError, "scroll() takes an int");
        return nullptr;
    }
    long long n;
    if (!saturated_ll(arg, &n)) return nullptr;
    auto L = layer_of(self);
    if (!L || !require_size(L)) return nullptr;
    try {
        L->scrollBy(n);
    } catch (const std::exception& e) {
        raise_from(e);
        return nullptr;
    }
    Py_RETURN_NONE;
}

// ---- inherited TileLayer methods, through the terminal ---------------------------------

static PyObject* TL_at(PyObject* self, PyObject* args, PyObject* kwds) {
    auto L = layer_of(self);
    if (!L) return nullptr;
    try { L->sync(true); } catch (const std::exception& e) { raise_from(e); return nullptr; }
    return PyGridLayerAPI::TileLayer_at(reinterpret_cast<PyTileLayerObject*>(self), args, kwds);
}

static PyObject* TL_set(PyObject* self, PyObject* args) {
    PyObject* pos_obj;
    long long index;
    if (!PyArg_ParseTuple(args, "OL", &pos_obj, &index)) return nullptr;
    int x, y;
    if (!PyPosition_FromObjectInt(pos_obj, &x, &y)) return nullptr;
    auto L = layer_of(self);
    if (!L || !require_size(L)) return nullptr;
    if (!set_through_terminal(L, x, y, index)) return nullptr;
    Py_RETURN_NONE;
}

static PyObject* TL_fill(PyObject* self, PyObject* args) {
    long long index;
    if (!PyArg_ParseTuple(args, "L", &index)) return nullptr;
    auto L = layer_of(self);
    if (!L || !require_size(L)) return nullptr;
    if (!fill_through_terminal(L, 0, 0, L->grid_x, L->grid_y, index)) return nullptr;
    Py_RETURN_NONE;
}

static PyObject* TL_fill_rect(PyObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"pos", "size", "index", NULL};
    PyObject *pos_obj, *size_obj;
    long long index;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OOL", const_cast<char**>(kwlist), &pos_obj, &size_obj, &index))
        return nullptr;
    int x, y, w, h;
    if (!PyPosition_FromObjectInt(pos_obj, &x, &y, "pos")) return nullptr;
    if (!PyPosition_FromObjectInt(size_obj, &w, &h, "size")) return nullptr;
    auto L = layer_of(self);
    if (!L || !require_size(L)) return nullptr;
    // Clipped like TileLayer.fill_rect (64-bit far edge, clamped on both sides).
    const int x1 = std::max(0, x), y1 = std::max(0, y);
    const int x2 = static_cast<int>(std::clamp<long long>(static_cast<long long>(x) + w, 0, L->grid_x));
    const int y2 = static_cast<int>(std::clamp<long long>(static_cast<long long>(y) + h, 0, L->grid_y));
    if (!fill_through_terminal(L, x1, y1, x2, y2, index)) return nullptr;
    Py_RETURN_NONE;
}

// apply_threshold / apply_ranges: run TileLayer's own implementation, take the indices it
// wrote, put the shown tiles back, and print the changed cells through the terminal.
template <PyObject* (*Base)(PyTileLayerObject*, PyObject*, PyObject*)>
static PyObject* TL_apply(PyObject* self, PyObject* args, PyObject* kwds) {
    auto L = layer_of(self);
    if (!L || !require_size(L)) return nullptr;
    try { L->sync(true); } catch (const std::exception& e) { raise_from(e); return nullptr; }
    const std::vector<int> shown = L->tiles;
    PyObject* r = Base(reinterpret_cast<PyTileLayerObject*>(self), args, kwds);
    std::vector<int> wanted;
    wanted.swap(L->tiles);
    L->tiles = shown;
    L->markDirty();
    if (!r) return nullptr;
    if (wanted.size() != shown.size()) {
        Py_DECREF(r);
        PyErr_SetString(PyExc_RuntimeError, "TerminalLayer changed size during apply");
        return nullptr;
    }
    // Validate every index before anything is printed.
    std::vector<std::pair<int, int>> cells;
    for (size_t i = 0; i < wanted.size(); ++i) {
        if (wanted[i] == shown[i]) continue;
        uint32_t cp; int face; bool wide;
        if (!glyph_of(L, wanted[i], &cp, &face, &wide)) { Py_DECREF(r); return nullptr; }
        if (wide) {
            Py_DECREF(r);
            PyErr_Format(PyExc_ValueError,
                         "tile index %d is a wide glyph (two cells); apply_threshold/apply_ranges set cells "
                         "one by one and cannot place it (nothing was printed)", wanted[i]);
            return nullptr;
        }
        cells.emplace_back(static_cast<int>(i % L->grid_x), static_cast<int>(i / L->grid_x));
    }
    for (const auto& c : cells) {
        const int index = wanted[static_cast<size_t>(c.second) * L->grid_x + c.first];
        if (!set_through_terminal(L, c.first, c.second, index)) { Py_DECREF(r); return nullptr; }
    }
    return r;
}

// TileLayer.apply_ranges takes no keywords; same shape as apply_threshold for TL_apply.
static PyObject* apply_ranges_kw(PyTileLayerObject* self, PyObject* args, PyObject* kwds) {
    if (kwds && PyDict_GET_SIZE(kwds) > 0) {
        PyErr_SetString(PyExc_TypeError, "apply_ranges() takes no keyword arguments");
        return nullptr;
    }
    return PyGridLayerAPI::TileLayer_apply_ranges_impl(self, args);
}

static PyObject* TL_edit(PyObject* self, PyObject* Py_UNUSED(args)) {
    auto L = layer_of(self);
    if (!L) return nullptr;
    try { L->sync(true); } catch (const std::exception& e) { raise_from(e); return nullptr; }
    return PyGridLayerAPI::TileLayer_edit(reinterpret_cast<PyTileLayerObject*>(self), nullptr);
}

static PyObject* TL_subscript(PyObject* self, PyObject* key) {
    auto L = layer_of(self);
    if (!L) return nullptr;
    try { L->sync(true); } catch (const std::exception& e) { raise_from(e); return nullptr; }
    return PyGridLayerAPI::TileLayer_subscript(reinterpret_cast<PyTileLayerObject*>(self), key);
}

static int TL_ass_subscript(PyObject* self, PyObject* key, PyObject* value) {
    if (!value) {
        PyErr_SetString(PyExc_TypeError, "cannot delete TerminalLayer cells");
        return -1;
    }
    int x, y;
    if (!PyPosition_FromObjectInt(key, &x, &y, "Layer index")) return -1;
    if (!PyLong_Check(value) || PyBool_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "tile index must be an int");
        return -1;
    }
    long long index = PyLong_AsLongLong(value);
    if (index == -1 && PyErr_Occurred()) return -1;
    auto L = layer_of(self);
    if (!L || !require_size(L)) return -1;
    return set_through_terminal(L, x, y, index) ? 0 : -1;
}

static PyMappingMethods TL_mapping = {
    .mp_length = nullptr,
    .mp_subscript = TL_subscript,
    .mp_ass_subscript = TL_ass_subscript,
};

// ---- properties ----------------------------------------------------------------------

static PyObject* TL_get_on_output(PyObject* self, void*) {
    auto L = layer_of(self);
    if (!L) return nullptr;
    return Py_NewRef(L->on_output ? L->on_output : Py_None);
}

static int TL_set_on_output(PyObject* self, PyObject* value, void*) {
    auto L = layer_of(self);
    if (!L) return -1;
    if (!value || value == Py_None) {
        Py_CLEAR(L->on_output);
        return 0;
    }
    if (!PyCallable_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "on_output must be callable or None");
        return -1;
    }
    Py_XSETREF(L->on_output, Py_NewRef(value));
    return 0;
}

static PyObject* TL_get_title(PyObject* self, void*) {
    auto L = layer_of(self);
    if (!L) return nullptr;
    try {
        const std::string t = L->title();
        return PyUnicode_DecodeUTF8(t.data(), static_cast<Py_ssize_t>(t.size()), "replace");
    } catch (const std::exception& e) { raise_from(e); return nullptr; }
}

static PyObject* TL_get_cursor(PyObject* self, void*) {
    auto L = layer_of(self);
    if (!L) return nullptr;
    try { L->sync(true); } catch (const std::exception& e) { raise_from(e); return nullptr; }
    if (!L->hasTerminal() || !L->cursorInViewport()) Py_RETURN_NONE;
    return Py_BuildValue("(ii)", L->cursorX(), L->cursorY());
}

static PyObject* TL_get_cursor_style(PyObject* self, void*) {
    auto L = layer_of(self);
    if (!L) return nullptr;
    try { L->sync(true); } catch (const std::exception& e) { raise_from(e); return nullptr; }
    switch (L->cursorStyle()) {
        case GHOSTTY_CURSOR_STYLE_BAR: return PyUnicode_FromString("bar");
        case GHOSTTY_CURSOR_STYLE_UNDERLINE: return PyUnicode_FromString("underline");
        case GHOSTTY_CURSOR_STYLE_BLOCK_HOLLOW: return PyUnicode_FromString("block_hollow");
        default: return PyUnicode_FromString("block");
    }
}

static PyObject* TL_get_cursor_visible(PyObject* self, void*) {
    auto L = layer_of(self);
    if (!L) return nullptr;
    try { L->sync(true); } catch (const std::exception& e) { raise_from(e); return nullptr; }
    return PyBool_FromLong(L->cursorVisible());
}

static PyObject* TL_get_show_cursor(PyObject* self, void*) {
    auto L = layer_of(self);
    if (!L) return nullptr;
    return PyBool_FromLong(L->show_cursor);
}

static int TL_set_show_cursor(PyObject* self, PyObject* value, void*) {
    auto L = layer_of(self);
    if (!L) return -1;
    if (!value) { PyErr_SetString(PyExc_TypeError, "cannot delete show_cursor"); return -1; }
    int v = PyObject_IsTrue(value);
    if (v < 0) return -1;
    if (static_cast<bool>(v) != L->show_cursor) {
        L->show_cursor = v;
        L->notifyGrid();   // the cursor is drawn over the chunks: no chunk repaints
    }
    return 0;
}

static PyObject* TL_get_palette(PyObject* self, void*) {
    auto L = layer_of(self);
    if (!L || !require_size(L)) return nullptr;
    std::vector<sf::Color> pal;
    try { pal = L->palette(); } catch (const std::exception& e) { raise_from(e); return nullptr; }
    PyObject* list = PyList_New(static_cast<Py_ssize_t>(pal.size()));
    if (!list) return nullptr;
    for (size_t i = 0; i < pal.size(); ++i) {
        PyObject* c = PyColor(pal[i]).pyObject();
        if (!c) { Py_DECREF(list); return nullptr; }
        PyList_SET_ITEM(list, static_cast<Py_ssize_t>(i), c);
    }
    return list;
}

static int TL_set_palette(PyObject* self, PyObject* value, void*) {
    std::vector<sf::Color> pal;
    if (value && value != Py_None) {
        PyObject* seq = PySequence_Fast(value, "palette must be a sequence of 256 colours or None");
        if (!seq) return -1;
        const Py_ssize_t n = PySequence_Fast_GET_SIZE(seq);
        if (n != 256) {
            Py_DECREF(seq);
            PyErr_Format(PyExc_ValueError, "palette needs exactly 256 colours (got %zd)", n);
            return -1;
        }
        pal.resize(256);
        for (Py_ssize_t i = 0; i < n; ++i) {
            if (!PyColor::to_color(PySequence_Fast_GET_ITEM(seq, i), pal[static_cast<size_t>(i)])) {
                Py_DECREF(seq);
                return -1;
            }
        }
        Py_DECREF(seq);
    }
    auto L = layer_of(self);
    if (!L || !require_size(L)) return -1;
    try { L->setPalette(pal); } catch (const std::exception& e) { raise_from(e); return -1; }
    return 0;
}

static PyObject* TL_get_background(PyObject* self, void*) {
    auto L = layer_of(self);
    if (!L) return nullptr;
    if (!L->hasBackground()) Py_RETURN_NONE;
    return PyColor(L->background()).pyObject();
}

static int TL_set_background(PyObject* self, PyObject* value, void*) {
    sf::Color c;
    const bool set = value && value != Py_None;
    if (set && !PyColor::to_color(value, c)) return -1;
    auto L = layer_of(self);
    if (!L) return -1;
    try { L->setBackground(set ? &c : nullptr); } catch (const std::exception& e) { raise_from(e); return -1; }
    return 0;
}

static PyObject* TL_get_blink_interval(PyObject* self, void*) {
    auto L = layer_of(self);
    if (!L) return nullptr;
    if (L->blinkInterval() <= 0) Py_RETURN_NONE;
    return PyFloat_FromDouble(L->blinkInterval());
}

static int TL_set_blink_interval(PyObject* self, PyObject* value, void*) {
    double seconds = 0;
    if (value && value != Py_None) {
        if (!PyNumber_Check(value) || PyBool_Check(value)) {
            PyErr_SetString(PyExc_TypeError, "blink_interval must be a number of seconds or None");
            return -1;
        }
        seconds = PyFloat_AsDouble(value);
        if (seconds == -1.0 && PyErr_Occurred()) return -1;
        if (!(seconds > 0) || !std::isfinite(seconds) || seconds > 3600) {
            PyErr_Format(PyExc_ValueError, "blink_interval must be a positive number of seconds up to 3600, or None");
            return -1;
        }
    }
    auto L = layer_of(self);
    if (!L) return -1;
    L->setBlinkInterval(seconds);
    return 0;
}

static PyObject* TL_get_scroll_offset(PyObject* self, void*) {
    auto L = layer_of(self);
    if (!L) return nullptr;
    try { return PyLong_FromLongLong(L->scrollOffset()); } catch (const std::exception& e) { raise_from(e); return nullptr; }
}

static int TL_set_scroll_offset(PyObject* self, PyObject* value, void*) {
    if (!value || !PyLong_Check(value) || PyBool_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "scroll_offset must be an int");
        return -1;
    }
    long long n;
    if (!saturated_ll(value, &n)) return -1;
    if (n < 0) {
        PyErr_SetString(PyExc_ValueError, "scroll_offset counts rows back from the live screen and cannot be negative");
        return -1;
    }
    auto L = layer_of(self);
    if (!L || !require_size(L)) return -1;
    try { L->setScrollOffset(n); } catch (const std::exception& e) { raise_from(e); return -1; }
    return 0;
}

static PyObject* TL_get_scrollback(PyObject* self, void*) {
    auto L = layer_of(self);
    if (!L) return nullptr;
    return PyLong_FromSize_t(L->scrollback());
}

static PyObject* TL_get_scrollback_rows(PyObject* self, void*) {
    auto L = layer_of(self);
    if (!L) return nullptr;
    try { return PyLong_FromSize_t(L->scrollbackRows()); } catch (const std::exception& e) { raise_from(e); return nullptr; }
}

static PyObject* TL_get_chunk_repaints(PyObject* self, void*) {
    auto L = layer_of(self);
    if (!L) return nullptr;
    return PyLong_FromUnsignedLongLong(L->chunk_repaints);
}

static PyObject* TL_get_texture(PyObject* self, void*) {
    auto L = layer_of(self);
    if (!L) return nullptr;
    return PyTexture::pyobject_for(L->texture);
}

// RuntimeError(msg) with the pending exception as its cause.
static void raise_with_cause(const char* msg) {
    PyObject* cause = PyErr_GetRaisedException();
    PyErr_SetString(PyExc_RuntimeError, msg);
    PyObject* err = PyErr_GetRaisedException();
    if (cause) {
        PyException_SetContext(err, Py_NewRef(cause));
        PyException_SetCause(err, cause);
    }
    PyErr_SetRaisedException(err);
}

// The atlas a TerminalLayer gets when it is given none: mcrfpy.default_font at 16 px with
// Texture.from_font's default codepoints. Shared by every layer that uses it while one is
// alive (the cache holds it weakly, so nothing outlives the layers); a new default_font
// gets a new atlas.
static bool default_atlas(std::shared_ptr<PyTexture>* out) {
    static std::weak_ptr<PyTexture> cached;
    static std::weak_ptr<PyFont> cached_font;
    PyObject* mod = PyImport_ImportModule("mcrfpy");
    if (!mod) return false;
    PyObject* font = PyObject_GetAttrString(mod, "default_font");
    Py_DECREF(mod);
    if (!font) {
        raise_with_cause("TerminalLayer: no texture= given, and the engine's default font "
                         "(mcrfpy.default_font) is not available; pass a Texture.from_font atlas");
        return false;
    }
    if (!PyObject_TypeCheck(font, &mcrfpydef::PyFontType)) {
        Py_DECREF(font);
        PyErr_SetString(PyExc_RuntimeError, "TerminalLayer: no texture= given and mcrfpy.default_font is not a Font");
        return false;
    }
    std::shared_ptr<PyFont> font_ptr = reinterpret_cast<PyFontObject*>(font)->data;
    if (auto hit = cached.lock(); hit && cached_font.lock() == font_ptr) {
        Py_DECREF(font);
        *out = hit;
        return true;
    }
    PyObject* tex = PyObject_CallMethod(reinterpret_cast<PyObject*>(&mcrfpydef::PyTextureType), "from_font", "Oi", font, 16);
    Py_DECREF(font);
    if (!tex) {
        raise_with_cause("TerminalLayer: no texture= given, and the default atlas could not be built "
                         "from mcrfpy.default_font; pass a Texture.from_font atlas");
        return false;
    }
    *out = reinterpret_cast<PyTextureObject*>(tex)->data;
    Py_DECREF(tex);
    cached = *out;
    cached_font = font_ptr;
    return true;
}

// A font texture (Texture.from_font): anything else has no codepoint <-> tile tables.
// None (or no texture at all) is the shared default atlas.
static bool font_texture(PyObject* value, std::shared_ptr<PyTexture>* out) {
    if (!value || value == Py_None) return default_atlas(out);
    if (!PyObject_TypeCheck(value, &mcrfpydef::PyTextureType)) {
        PyErr_SetString(PyExc_TypeError, "texture must be a Texture built by Texture.from_font");
        return false;
    }
    auto tex = reinterpret_cast<PyTextureObject*>(value)->data;
    if (!tex || !tex->font_atlas) {
        PyErr_SetString(PyExc_ValueError,
                        "a TerminalLayer needs a texture built by Texture.from_font (this one has no glyph tables)");
        return false;
    }
    *out = tex;
    return true;
}

static int TL_set_texture(PyObject* self, PyObject* value, void*) {
    std::shared_ptr<PyTexture> tex;
    if (!font_texture(value, &tex)) return -1;
    auto L = layer_of(self);
    if (!L) return -1;
    L->texture = tex;
    try { L->textureChanged(); } catch (const std::exception& e) { raise_from(e); return -1; }
    return 0;
}

// ---- type ----------------------------------------------------------------------------

static int TL_init(PyObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"name", "z_index", "texture", "grid_size", "grid", "scrollback",
                                   "on_output", NULL};
    const char* name_str = nullptr;
    int z_index = -1;
    PyObject *texture_obj = nullptr, *grid_size_obj = nullptr, *grid_obj = nullptr, *on_output = nullptr;
    long long scrollback = 1000;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|ziOOOLO", const_cast<char**>(kwlist), &name_str, &z_index,
                                     &texture_obj, &grid_size_obj, &grid_obj, &scrollback, &on_output))
        return -1;
    if (grid_obj && grid_obj != Py_None && !PyObject_TypeCheck(grid_obj, &mcrfpydef::PyGridDataType) &&
        !PyObject_TypeCheck(grid_obj, &mcrfpydef::PyUIGridViewType)) {
        PyErr_SetString(PyExc_TypeError, "grid must be a mcrfpy.Grid instance");
        return -1;
    }
    std::shared_ptr<PyTexture> tex;
    if (!font_texture(texture_obj, &tex)) return -1;
    int cols = 0, rows = 0;
    if (grid_size_obj && grid_size_obj != Py_None) {
        if (!PyPosition_FromObjectInt(grid_size_obj, &cols, &rows, "grid_size")) return -1;
        if (cols < 0 || rows < 0) {
            PyErr_SetString(PyExc_ValueError, "TerminalLayer dimensions cannot be negative (0 means size from the grid)");
            return -1;
        }
        if (cols > GRID_MAX || rows > GRID_MAX) {
            PyErr_Format(PyExc_ValueError, "TerminalLayer dimensions cannot exceed %d (got %dx%d)", GRID_MAX, cols, rows);
            return -1;
        }
    }
    if (scrollback < 0) {
        PyErr_SetString(PyExc_ValueError, "scrollback must be 0 or more lines");
        return -1;
    }
    if (on_output && on_output != Py_None && !PyCallable_Check(on_output)) {
        PyErr_SetString(PyExc_TypeError, "on_output must be callable or None");
        return -1;
    }

    auto* o = reinterpret_cast<PyTileLayerObject*>(self);
    std::shared_ptr<TerminalLayer> layer;
    try {
        layer = std::make_shared<TerminalLayer>(z_index, cols, rows, tex, static_cast<size_t>(scrollback));
    } catch (const std::exception& e) {
        raise_from(e);
        return -1;
    }
    if (name_str) layer->name = name_str;
    if (on_output && on_output != Py_None) layer->on_output = Py_NewRef(on_output);
    // #430: a re-run __init__ replaces the layer; the old one must no longer resolve here.
    if (o->data && o->data->serial_number != 0) mcrf::unregister_wrapper(o->data->serial_number);
    o->data = layer;
    o->grid.reset();
    if (mcrf::register_wrapper(o->data->serial_number, self) < 0) return -1;
    if (grid_obj && grid_obj != Py_None) {
        PyObject* r = PyObject_CallMethod(grid_obj, "add_layer", "O", self);
        if (!r) return -1;
        Py_DECREF(r);
    }
    return 0;
}

static PyObject* TL_repr(PyObject* self) {
    auto* o = reinterpret_cast<PyTileLayerObject*>(self);
    auto L = std::dynamic_pointer_cast<TerminalLayer>(o->data);
    std::ostringstream ss;
    if (!L) {
        ss << "<TerminalLayer (invalid)>";
    } else {
        ss << "<TerminalLayer";
        if (!L->name.empty()) ss << " '" << L->name << "'";
        ss << " z_index=" << L->z_index << " size=(" << L->grid_x << "x" << L->grid_y << ")"
           << " visible=" << (L->visible ? "True" : "False") << ">";
    }
    return PyUnicode_FromString(ss.str().c_str());
}

static void TL_dealloc(PyObject* self) {
    PyObject_GC_UnTrack(self);
    auto* o = reinterpret_cast<PyTileLayerObject*>(self);
    if (o->weakreflist) PyObject_ClearWeakRefs(self);
    using LayerPtr = std::shared_ptr<TileLayer>;
    using GridPtr = std::shared_ptr<GridData>;
    o->data.~LayerPtr();
    o->grid.~GridPtr();
    Py_TYPE(self)->tp_free(self);
}

// The layer owns on_output. Reported only while this wrapper is the layer's sole owner
// (#441): a grid that holds the layer keeps calling the callback after the wrapper dies.
static int TL_traverse(PyObject* self, visitproc visit, void* arg) {
    auto* o = reinterpret_cast<PyTileLayerObject*>(self);
    if (!o->data || !mcrf::owns_exclusively(o->data.use_count(), 0)) return 0;
    auto* L = dynamic_cast<TerminalLayer*>(o->data.get());
    if (L) Py_VISIT(L->on_output);
    return 0;
}

static int TL_clear_refs(PyObject* self) {
    auto* o = reinterpret_cast<PyTileLayerObject*>(self);
    if (!o->data || !mcrf::owns_exclusively(o->data.use_count(), 0)) return 0;
    auto* L = dynamic_cast<TerminalLayer*>(o->data.get());
    if (L) Py_CLEAR(L->on_output);
    return 0;
}

static PyObject* TL_new(PyTypeObject* type, PyObject*, PyObject*) {
    auto* self = reinterpret_cast<PyTileLayerObject*>(type->tp_alloc(type, 0));
    if (!self) return nullptr;
    new (&self->data) std::shared_ptr<TileLayer>();
    new (&self->grid) std::shared_ptr<GridData>();
    return reinterpret_cast<PyObject*>(self);
}

static PyMethodDef TL_methods[] = {
    {"write", (PyCFunction)TL_write, METH_O,
     MCRF_METHOD(TerminalLayer, write,
         MCRF_SIG("(data: bytes | str)", "None"),
         MCRF_DESC("Feed program output to the terminal: bytes (or any bytes-like object), or a str sent as UTF-8. "
                   "Replies to queries in it (cursor position, device attributes, ...) go to on_output before this returns."),
         MCRF_ARGS_START
         MCRF_ARG("data", "Bytes from the program")
         MCRF_RAISES("RuntimeError", "The layer has no size yet (no grid_size= and not attached to a Grid)")
         MCRF_NOTE("An exception raised by on_output propagates out of write(). Delivery is at most once: the bytes handed to a callback that raises are not delivered again. on_output may call write() itself: its replies are delivered after the callback returns, in order.")
     )},
    {"key", (PyCFunction)TL_key, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(TerminalLayer, key,
         MCRF_SIG("(key: Key, state: InputState = InputState.PRESSED, mods=None)", "None"),
         MCRF_DESC("Encode a key event for the modes the program has set (application cursor keys, the Kitty keyboard protocol, ...) and send it through on_output. "
                   "Keys that type a character (letters, digits, punctuation, space) are sent only as Ctrl/Alt/Super combinations: their text comes through text(), from on_text."),
         MCRF_ARGS_START
         MCRF_ARG("key", "A Key, as on_key receives it")
         MCRF_ARG("state", "PRESSED, REPEATED or RELEASED (a release sends nothing unless the program asked for release events)")
         MCRF_ARG("mods", "None for the modifiers of the key event being handled (mcrfpy.keyboard), a str like 'ctrl+shift', or an iterable of 'shift', 'ctrl', 'alt', 'super'")
         MCRF_RAISES("ValueError", "The key has no terminal encoding, or a modifier name is unknown")
         MCRF_NOTE("The encoded bytes go to on_output; with on_output None they are dropped.")
     )},
    {"text", (PyCFunction)TL_text, METH_O,
     MCRF_METHOD(TerminalLayer, text,
         MCRF_SIG("(text: str)", "None"),
         MCRF_DESC("Send typed text (what on_text receives) to the program through on_output, encoded for its keyboard mode."),
         MCRF_ARGS_START
         MCRF_ARG("text", "Printable text")
         MCRF_RAISES("ValueError", "text contains a control character (send keys with key())")
     )},
    {"mouse", (PyCFunction)TL_mouse, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(TerminalLayer, mouse,
         MCRF_SIG("(pos, button: MouseButton = None, state: InputState = None, mods=None)", "None"),
         MCRF_DESC("Report a mouse event to the program, if it turned mouse reporting on, in the format it chose (X10, UTF-8 1005, SGR 1006, URxvt 1015, SGR-pixels 1016). Sent through on_output; nothing is sent while reporting is off. A position outside the layer reports the nearest edge cell."),
         MCRF_ARGS_START
         MCRF_ARG("pos", "Cell position (x, y); fractions address pixels within the cell; clamped to the layer")
         MCRF_ARG("button", "The button, a SCROLL_* wheel direction, or None for motion with no button")
         MCRF_ARG("state", "PRESSED or RELEASED for a button event; None for motion (a wheel step is a press)")
         MCRF_ARG("mods", "As for key()")
         MCRF_RAISES("ValueError", "pos is not finite (NaN or infinite)")
     )},
    {"paste", (PyCFunction)TL_paste, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(TerminalLayer, paste,
         MCRF_SIG("(text: str, allow_unsafe: bool = False)", "None"),
         MCRF_DESC("Paste text into the program through on_output: bracketed if the program turned bracketed paste on, with line breaks sent as Enter otherwise."),
         MCRF_ARGS_START
         MCRF_ARG("text", "The text to paste")
         MCRF_ARG("allow_unsafe", "Send text that could run commands (see Raises)")
         MCRF_RAISES("ValueError", "The text could run commands (a line break while bracketed paste is off, or a bracketed-paste end sequence) and allow_unsafe is False; nothing is sent")
     )},
    {"focus", (PyCFunction)TL_focus, METH_O,
     MCRF_METHOD(TerminalLayer, focus,
         MCRF_SIG("(gained: bool)", "None"),
         MCRF_DESC("Report focus gained or lost to the program through on_output, if it turned focus reporting on (mode 1004); otherwise nothing is sent."),
         MCRF_ARGS_START
         MCRF_ARG("gained", "True when the terminal gained focus")
     )},
    {"move", (PyCFunction)TL_move, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(TerminalLayer, move,
         MCRF_SIG("(pos)", "None"),
         MCRF_DESC("Move the cursor to a cell, as a terminal control sequence (CUP) written to the terminal."),
         MCRF_ARGS_START
         MCRF_ARG("pos", "Cell (x, y) as a tuple or Vector, or move(x, y)")
         MCRF_RAISES("IndexError", "The cell is outside the layer")
     )},
    {"print", (PyCFunction)TL_print, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(TerminalLayer, print,
         MCRF_SIG("(text: str, pos=None, fg=None, bg=None, bold=False, italic=False, underline=False, blink=False, inverse=False, strike=False, faint=False)", "None"),
         MCRF_DESC("Draw text from game code, as terminal control sequences written to the terminal: at the cursor (which moves past it; the terminal wraps and scrolls as usual), or at pos with the cursor saved and restored around it. Attributes apply to this text only."),
         MCRF_ARGS_START
         MCRF_ARG("text", "Printable text, newlines and tabs. Zero-width codepoints (combining marks, ZWJ, ...) combine with the character before them and take no column; one with nothing before it raises. At the cursor a newline continues at column 0 of the next line")
         MCRF_ARG("pos", "Cell (x, y) to print at, leaving the cursor where it was; None prints at the cursor. Placed text never wraps or scrolls: each line is clipped at the right edge, a newline continues at pos's column on the next row, lines below the bottom row are dropped, and a tab is spaces to the next multiple of 8 columns counted from pos's column (at the cursor a tab is HT, so the program's tab stops apply)")
         MCRF_ARG("fg", "Foreground: a Color, (r, g, b) tuple or colour name (truecolor), or a palette index 0-255; None for the default")
         MCRF_ARG("bg", "Background, as fg")
         MCRF_ARG("bold", "Bold (the atlas's bold face, else drawn twice)")
         MCRF_ARG("italic", "Italic (the atlas's italic face, else sheared)")
         MCRF_ARG("underline", "Underlined")
         MCRF_ARG("blink", "Blinking (see blink_interval)")
         MCRF_ARG("inverse", "Foreground and background swapped")
         MCRF_ARG("strike", "Struck through")
         MCRF_ARG("faint", "Foreground at half brightness")
         MCRF_RAISES("ValueError", "text holds a control character other than newline and tab (send raw sequences with write()), a colour has alpha below 255, or a palette index is outside 0-255")
         MCRF_RAISES("IndexError", "pos is outside the layer")
     )},
    {"clear", (PyCFunction)TL_clear, METH_NOARGS,
     MCRF_METHOD(TerminalLayer, clear,
         MCRF_SIG("()", "None"),
         MCRF_DESC("Reset attributes, erase the screen to the default background and move the cursor home, as terminal control sequences.")
     )},
    {"clear_line", (PyCFunction)TL_clear_line, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(TerminalLayer, clear_line,
         MCRF_SIG("(y: int = None)", "None"),
         MCRF_DESC("Erase a whole line to the default background, as terminal control sequences; the cursor and attributes are left as they were."),
         MCRF_ARGS_START
         MCRF_ARG("y", "The line to erase; None for the cursor's line")
         MCRF_RAISES("IndexError", "y is outside the layer")
     )},
    {"screen_text", (PyCFunction)TL_screen_text, METH_NOARGS,
     MCRF_METHOD(TerminalLayer, screen_text,
         MCRF_SIG("()", "str"),
         MCRF_DESC("The text on screen (the viewport, so scrolled-back history when scroll_offset > 0): one line per row joined by newlines, trailing blanks removed, a wide character once."),
         MCRF_RETURNS("str")
     )},
    {"scroll", (PyCFunction)TL_scroll, METH_O,
     MCRF_METHOD(TerminalLayer, scroll,
         MCRF_SIG("(rows: int)", "None"),
         MCRF_DESC("Scroll the viewport through the scrollback: positive rows go back into history, negative toward the live screen. Clamped at both ends."),
         MCRF_ARGS_START
         MCRF_ARG("rows", "Rows to scroll")
         MCRF_NOTE("While scrolled back, new output leaves the viewport where it is; scroll_offset = 0 returns to the live screen.")
     )},
    {"at", (PyCFunction)TL_at, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(TerminalLayer, at,
         MCRF_SIG("(pos)", "int"),
         MCRF_DESC("The tile index a cell shows (the glyph's tile in its face; the right half of a wide glyph is index + 1; -1 for a cell with no text)."),
         MCRF_ARGS_START
         MCRF_ARG("pos", "Cell as (x, y) tuple, list, or Vector; or pass x and y separately")
         MCRF_RETURNS("Tile index, or -1")
         MCRF_RAISES("IndexError", "If coordinates are out of bounds")
     )},
    {"set", (PyCFunction)TL_set, METH_VARARGS,
     MCRF_METHOD(TerminalLayer, set,
         MCRF_SIG("(pos, index: int)", "None"),
         MCRF_DESC("Print the glyph of a tile index at a cell, through the terminal (cursor and attributes are left as they were), so it stays until the program overwrites it. A bold or italic tile prints in that style."),
         MCRF_ARGS_START
         MCRF_ARG("pos", "Cell as (x, y) tuple, list, or Vector")
         MCRF_ARG("index", "A glyph tile of the layer's texture")
         MCRF_RAISES("ValueError", "The index has no codepoint (-1, the box, the white tile, a right half, out of range), its codepoint has zero width (a combining mark cannot occupy a cell) or is a control, or it is a wide glyph at the last column")
         MCRF_RAISES("IndexError", "If coordinates are out of bounds")
     )},
    {"fill", (PyCFunction)TL_fill, METH_VARARGS,
     MCRF_METHOD(TerminalLayer, fill,
         MCRF_SIG("(index: int)", "None"),
         MCRF_DESC("Print the glyph of a tile index in every cell, through the terminal, as fill_rect over the whole layer."),
         MCRF_ARGS_START
         MCRF_ARG("index", "A glyph tile of the layer's texture")
         MCRF_RAISES("ValueError", "As for set()")
     )},
    {"fill_rect", (PyCFunction)TL_fill_rect, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(TerminalLayer, fill_rect,
         MCRF_SIG("(pos: tuple, size: tuple, index: int)", "None"),
         MCRF_DESC("Print the glyph of a tile index over a rectangle (clipped to the layer), through the terminal: one cursor move and a repeated character (REP) per row, with cursor, attributes and autowrap saved and restored. A wide glyph fills the rectangle in pairs of cells; an odd last column is left blank."),
         MCRF_ARGS_START
         MCRF_ARG("pos", "Top-left corner: (x, y) tuple, list or Vector")
         MCRF_ARG("size", "Dimensions: (width, height) tuple, list or Vector")
         MCRF_ARG("index", "A glyph tile of the layer's texture")
         MCRF_RAISES("ValueError", "As for set()")
     )},
    {"apply_threshold", (PyCFunction)TL_apply<PyGridLayerAPI::TileLayer_apply_threshold_impl>, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(TerminalLayer, apply_threshold,
         MCRF_SIG("(source: HeightMap, range: tuple, tile: int)", "TerminalLayer"),
         MCRF_DESC("As TileLayer.apply_threshold, with every changed cell printed through the terminal."),
         MCRF_ARGS_START
         MCRF_ARG("source", "Source heightmap (must match layer dimensions)")
         MCRF_ARG("range", "Value range as (min, max) inclusive")
         MCRF_ARG("tile", "A glyph tile of the layer's texture")
         MCRF_RETURNS("self for method chaining")
         MCRF_RAISES("ValueError", "The tile has no codepoint, has zero width, or is a wide glyph (cells are set one by one); nothing is printed")
     )},
    {"apply_ranges", (PyCFunction)TL_apply<apply_ranges_kw>, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(TerminalLayer, apply_ranges,
         MCRF_SIG("(source: HeightMap, ranges: list)", "TerminalLayer"),
         MCRF_DESC("As TileLayer.apply_ranges, with every changed cell printed through the terminal."),
         MCRF_ARGS_START
         MCRF_ARG("source", "Source heightmap (must match layer dimensions)")
         MCRF_ARG("ranges", "List of ((min, max), tile_index) tuples")
         MCRF_RETURNS("self for method chaining")
         MCRF_RAISES("ValueError", "A tile has no codepoint, has zero width, or is a wide glyph; nothing is printed")
     )},
    {"edit", (PyCFunction)TL_edit, METH_NOARGS,
     MCRF_METHOD(TerminalLayer, edit,
         MCRF_SIG("()", "context manager"),
         MCRF_DESC("Context manager yielding a READ-ONLY (height, width) int32 view of the tile indices on screen. The terminal owns the cells: write through write(), print() or set()."),
         MCRF_NOTE("Asking the view for a writable buffer (e.g. numpy with write access) raises BufferError.")
     )},
    {NULL}
};

static PyGetSetDef TL_getsetters[] = {
    {"on_output", TL_get_on_output, TL_set_on_output,
     MCRF_PROPERTY(on_output, "Where the terminal's bytes for the program go (Callable | None): called with one bytes argument for the replies to queries during write, and for the input encoded by key, text, mouse, paste and focus. None drops them."), NULL},
    {"texture", TL_get_texture, TL_set_texture,
     MCRF_PROPERTY(texture, "The font atlas the cells are drawn from (Texture). Must be built by Texture.from_font; a new one re-maps every cell. None assigns the shared default atlas (mcrfpy.default_font at 16 px)."), NULL},
    {"title", TL_get_title, NULL,
     MCRF_PROPERTY(title, "The window title the program set with OSC 0/2 (str, read-only). The emulator keeps at most 1024 bytes of it; an OSC sequence of about 4 KB or more, or a title that is not valid UTF-8, is ignored and the previous title stays."), NULL},
    {"cursor", TL_get_cursor, NULL,
     MCRF_PROPERTY(cursor, "The cursor's cell (x, y), or None when it is not in the viewport (scrolled back) (tuple | None, read-only)."), NULL},
    {"cursor_style", TL_get_cursor_style, NULL,
     MCRF_PROPERTY(cursor_style, "The cursor shape the program asked for: 'block', 'bar', 'underline' or 'block_hollow' (str, read-only)."), NULL},
    {"cursor_visible", TL_get_cursor_visible, NULL,
     MCRF_PROPERTY(cursor_visible, "Whether the program shows the cursor, set with DECTCEM (bool, read-only)."), NULL},
    {"show_cursor", TL_get_show_cursor, TL_set_show_cursor,
     MCRF_PROPERTY(show_cursor, "Whether the layer draws the cursor at all (bool). Default True."), NULL},
    {"palette", TL_get_palette, TL_set_palette,
     MCRF_PROPERTY(palette, "The 256-colour palette in use, OSC 4 changes included (list, of 256 Color). Setting a sequence of 256 colours replaces the default palette; None restores the built-in one."), NULL},
    {"background", TL_get_background, TL_set_background,
     MCRF_PROPERTY(background, "The terminal's default background (Color | None). None (default): cells with the default background draw nothing, so what is under the layer shows; a background query (OSC 11) is then answered with the emulator's nominal black. A Color is drawn for them and is what OSC 11 reports. Explicit SGR backgrounds always draw. OSC 10 and 12 report the default foreground."), NULL},
    {"blink_interval", TL_get_blink_interval, TL_set_blink_interval,
     MCRF_PROPERTY(blink_interval, "Seconds per blink phase on the engine clock (float | None). None draws blinking cells and a blinking cursor steady. Default 0.5. Costs nothing while nothing blinks."), NULL},
    {"scroll_offset", TL_get_scroll_offset, TL_set_scroll_offset,
     MCRF_PROPERTY(scroll_offset, "Rows the viewport is scrolled back into history (int); 0 is the live screen."), NULL},
    {"scrollback", TL_get_scrollback, NULL,
     MCRF_PROPERTY(scrollback, "Lines of history asked for at construction (int, read-only). Approximate: the emulator trims history by memory page, so it can hold many more rows than this (scrollback=1 held about 2000 short rows); 0 keeps none. Very large values are bounded only by memory."), NULL},
    {"scrollback_rows", TL_get_scrollback_rows, NULL,
     MCRF_PROPERTY(scrollback_rows, "Rows of history currently held (int, read-only)."), NULL},
    {"chunk_repaints", TL_get_chunk_repaints, NULL,
     MCRF_PROPERTY(chunk_repaints, "Chunk textures this layer has repainted since it was made (int, read-only); for checking that output repaints only what changed."), NULL},
    {NULL}
};

namespace TerminalLayerAPI {
PyObject* py_set(PyObject* self, PyObject* args) { return TL_set(self, args); }
PyObject* py_fill(PyObject* self, PyObject* args) { return TL_fill(self, args); }
PyObject* py_fill_rect(PyObject* self, PyObject* args, PyObject* kwds) { return TL_fill_rect(self, args, kwds); }
int py_ass_subscript(PyObject* self, PyObject* key, PyObject* value) { return TL_ass_subscript(self, key, value); }
PyObject* py_apply_threshold(PyObject* self, PyObject* args, PyObject* kwds) {
    return TL_apply<PyGridLayerAPI::TileLayer_apply_threshold_impl>(self, args, kwds);
}
PyObject* py_apply_ranges(PyObject* self, PyObject* args) { return TL_apply<apply_ranges_kw>(self, args, nullptr); }
int py_set_texture(PyObject* self, PyObject* value) { return TL_set_texture(self, value, nullptr); }
}  // namespace TerminalLayerAPI

PyTypeObject mcrfpydef::PyTerminalLayerType = {
    .ob_base = PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "mcrfpy.TerminalLayer",
    .tp_basicsize = sizeof(PyTileLayerObject),
    .tp_itemsize = 0,
    .tp_dealloc = TL_dealloc,
    .tp_repr = TL_repr,
    .tp_as_mapping = &TL_mapping,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,
    .tp_doc = PyDoc_STR(
        "TerminalLayer(name=None, z_index=-1, texture=None, grid_size=None, grid=None, scrollback=1000, on_output=None)\n\n"
        "EXPERIMENTAL (not part of the 1.0 freeze). A TileLayer whose cells are a terminal screen,\n"
        "emulated by libghostty-vt: bytes in through write(), cells out, bytes for the program\n"
        "through on_output. The layer does no I/O: run a program by connecting a PTY (in Python)\n"
        "to write() and on_output.\n\n"
        "Every change to the cells is terminal input. The curses-style helpers (move, print,\n"
        "clear, clear_line) write control sequences; the inherited set, fill, fill_rect, layer[x, y] = i\n"
        "and apply_* print the tile's glyph through the terminal; edit() is read-only.\n\n"
        "Args:\n"
        "    name (str): Layer name for Grid.layer(name) lookup. Default: None\n"
        "    z_index (int): Render order relative to entities. Default: -1\n"
        "    texture (Texture): A font atlas from Texture.from_font; its cell is the terminal's. Default: None,\n"
        "        a shared atlas of mcrfpy.default_font at 16 px with from_font's default codepoints.\n"
        "    grid_size (tuple): (columns, rows). None or (0, 0): the size of the Grid it is attached to.\n"
        "    grid (Grid): Attach to this Grid at construction. Default: None\n"
        "    scrollback (int): Lines of history to keep (approximate, see scrollback). Default: 1000\n"
        "    on_output (callable): Receives the bytes for the program. Default: None (dropped)\n\n"
        "Drawing: one vertex array per chunk from the one atlas (backgrounds, glyphs, lines). Inverse swaps\n"
        "colours, faint halves the foreground, bold/italic use the atlas's faces or are faked (drawn twice /\n"
        "sheared), underline (single, double) / strike / overline are quads at the font's metrics, blink\n"
        "follows blink_interval on the engine clock. The cursor is drawn over the cached chunks.\n"
        "Glyph coverage: code page 437 is the baseline; glyphs beyond it are extras. Test the ones your\n"
        "program uses (Texture.missing / clipped) and ship a prebuilt texture if a font does not convert\n"
        "cleanly; a codepoint the atlas lacks draws the box tile.\n"
        "Default-background cells are transparent unless background is set. Reverse video (DECSCNM) swaps\n"
        "the default colours only; cells with explicit colours keep them (as Ghostty draws it).\n\n"
        "Placed drawing (set, fill, fill_rect, apply_*, print(pos=), clear_line) saves and restores the\n"
        "cursor, pen, protection, charsets, origin, insert, autowrap and left/right margins, and never\n"
        "wraps or scrolls. Known limits, from what the emulator's API exposes: it uses DECSC/DECRC, so\n"
        "the program's own saved cursor (ESC 7) is replaced by the placement's; REP after a placement\n"
        "repeats the placed character; placed cells take an open OSC 8 hyperlink. While a synchronized-\n"
        "output hold (mode 2026) lasts, reads (at, screen_text, cursor, edit, GridPoint) show the held\n"
        "frame, what is on screen, until it ends (by the program, or after 1 s of engine time).\n\n"
        "Example:\n"
        "    term = mcrfpy.TerminalLayer(grid_size=(80, 24))\n"
        "    grid = mcrfpy.Grid(grid_size=(80, 24), texture=term.texture, layers=[term])\n"
        "    term.print('HP 12/20', pos=(0, 23), fg='green')\n"
        "    term.write(b'\\x1b[1mbold\\x1b[0m')"),
    .tp_traverse = TL_traverse,
    .tp_clear = TL_clear_refs,
    .tp_weaklistoffset = offsetof(PyTileLayerObject, weakreflist),
    .tp_methods = TL_methods,
    .tp_getset = TL_getsetters,
    .tp_base = &mcrfpydef::PyTileLayerType,
    .tp_init = TL_init,
    .tp_new = TL_new,
    .tp_free = PyObject_GC_Del,
};
