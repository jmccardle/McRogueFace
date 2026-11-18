#pragma once
// #550: TerminalLayer -- a TileLayer whose cells are a terminal screen, driven by
// libghostty-vt. Bytes go in through write(); bytes for the program (query replies,
// encoded input) come out through on_output. The layer does no I/O of its own.
// EXPERIMENTAL (not part of the 1.0 freeze).
//
// The emulator is the single source of truth: every write to the cells (write(), the
// curses-style helpers, and the inherited set/fill/fill_rect/apply_*) is terminal input.
// The inherited `tiles` vector holds the tile each cell shows (face resolved), and the
// layer keeps the per-cell colours and attributes beside it. They are refreshed from
// libghostty's render state lazily: when the layer is drawn, and before any read
// (prepareRead()).
//
// This header does not include the libghostty-vt headers.
#include "GridLayers.h"
#include <cstdint>
#include <string>
#include <vector>

struct GhosttyTerminalImpl;
struct GhosttyRenderStateImpl;
struct GhosttyRenderStateRowIteratorImpl;
struct GhosttyRenderStateRowCellsImpl;
struct GhosttyKeyEncoderImpl;
struct GhosttyKeyEventImpl;
struct GhosttyMouseEncoderImpl;
struct GhosttyMouseEventImpl;

class TerminalLayer : public TileLayer, public std::enable_shared_from_this<TerminalLayer> {
public:
    // Per-cell drawing flags (what the chunk painter needs; colours are already resolved).
    enum CellFlag : uint16_t {
        CF_DEFAULT_BG  = 1u << 0,   // background is the terminal's default: drawn only if `background` is set
        CF_FAKE_BOLD   = 1u << 1,   // bold, and the atlas has no bold glyph: draw twice, 1 px apart
        CF_FAKE_ITALIC = 1u << 2,   // italic, and the atlas has no italic glyph: shear the quad
        CF_INVISIBLE   = 1u << 3,   // SGR 8: no glyph, no lines
        CF_BLINK       = 1u << 4,   // SGR 5/6: glyph and lines hidden in the off phase
        CF_UNDERLINE   = 1u << 5,
        CF_UNDERLINE2  = 1u << 6,   // double underline (with CF_UNDERLINE)
        CF_STRIKE      = 1u << 7,
        CF_OVERLINE    = 1u << 8,
    };

    // Throws std::runtime_error naming the libghostty call that failed.
    TerminalLayer(int z_index, int cols, int rows, std::shared_ptr<PyTexture> texture, size_t scrollback);
    ~TerminalLayer() override;
    TerminalLayer(const TerminalLayer&) = delete;
    TerminalLayer& operator=(const TerminalLayer&) = delete;

    // ---- GridLayer / TileLayer --------------------------------------------------------
    void resize(int new_grid_x, int new_grid_y) override;
    void renderChunkToTexture(int chunk_x, int chunk_y, int cell_width, int cell_height) override;
    void render(sf::RenderTarget& target,
               float left_spritepixels, float top_spritepixels,
               int left_edge, int top_edge, int x_limit, int y_limit,
               float zoom, int cell_width, int cell_height) override;
    void prepareRead() override;

    // ---- terminal ---------------------------------------------------------------------
    bool hasTerminal() const { return term_ != nullptr; }
    size_t scrollback() const { return scrollback_; }
    // Program output in. Requires hasTerminal(). Replies collect in pending_output.
    void feed(const uint8_t* data, size_t len);
    void feed(const std::string& s) { feed(reinterpret_cast<const uint8_t*>(s.data()), s.size()); }

    // Refresh the cells from the emulator if anything changed since the last sync.
    // `notify`: report changed chunks to the grid (false inside the render pass).
    void sync(bool notify);

    // Input encoders. Each appends the bytes for the program to pending_output and
    // returns them nowhere else. mods are GHOSTTY_MODS_* bits.
    void encodeKey(int ghostty_key, int action, unsigned mods, const std::string& utf8, uint32_t unshifted);
    // `action`: 0 press, 1 release, 2 motion. `button`: GhosttyMouseButton, 0 = none.
    void encodeMouse(float cell_x, float cell_y, int button, int action, unsigned mods);
    void encodeFocus(bool gained);
    // Returns the GhosttyResult (GHOSTTY_REJECTED for an unsafe paste refused).
    int paste(const std::string& utf8, bool allow_unsafe);
    bool modeEnabled(uint16_t mode, bool ansi) const;
    unsigned kittyKeyboardFlags() const;

    std::string title() const;
    // Visible rows as UTF-8, trailing blanks removed, joined by '\n'.
    std::string screenText();
    size_t scrollbackRows() const;
    // Rows the viewport is scrolled back from the live screen (0 = live).
    long scrollOffset() const;
    void scrollBy(long rows_back);
    void setScrollOffset(long rows_back);

    // Palette: the current 256 colours (OSC 4 overrides included); setting replaces the
    // default palette (an empty vector restores the built-in one).
    std::vector<sf::Color> palette() const;
    void setPalette(const std::vector<sf::Color>& colours);

    // Default background: unset (nullptr) leaves default-background cells undrawn.
    bool hasBackground() const { return has_background_; }
    sf::Color background() const { return background_; }
    void setBackground(const sf::Color* colour);

    // Blink: seconds per phase, 0 = steady.
    double blinkInterval() const { return blink_interval_ms_ / 1000.0; }
    void setBlinkInterval(double seconds);
    bool blinkOn() const { return blink_on_; }

    // Cursor state from the last sync.
    bool cursorInViewport() const { return cursor_in_view_; }
    int cursorX() const { return cursor_x_; }
    int cursorY() const { return cursor_y_; }
    bool cursorVisible() const { return cursor_visible_; }   // DECTCEM
    bool cursorBlinking() const { return cursor_blinking_; }
    int cursorStyle() const { return cursor_style_; }         // GhosttyCursorStyle
    bool show_cursor = true;                                  // drawn by the layer at all

    // Cell attributes (stored beside `tiles`), for tests and the painter.
    const std::vector<sf::Color>& fgColours() const { return fg_; }
    const std::vector<sf::Color>& bgColours() const { return bg_; }
    const std::vector<uint16_t>& cellFlags() const { return flags_; }

    // A texture swap: every cell is mapped to the new atlas at the next sync.
    void textureChanged();

    // Bytes for the program, waiting to be handed to on_output (TerminalLayer.cpp).
    std::string pending_output;
    bool flushing = false;
    PyObject* on_output = nullptr;   // strong ref, or nullptr

    // Debug counter: chunk textures this layer has repainted.
    uint64_t chunk_repaints = 0;

    // Blink clock (#550): called once per simulation frame by the engine with the clock
    // its timers run on. Only layers with blinking cells (or a blinking cursor) are
    // registered, so this costs nothing while none blinks.
    static void tickAll(int now_ms);

private:
    void createTerminal(int cols, int rows);
    void freeAll() noexcept;
    void updateBlinkRegistration();
    void tick(int now_ms);
    void endHold();
    void fillChunkVertices(int chunk_x, int chunk_y, float cell_w, float cell_h,
                           float origin_x, float origin_y, float scale,
                           std::vector<sf::Vertex>& verts) const;
    void drawCursor(sf::RenderTarget& target, float left_spritepixels, float top_spritepixels,
                    float zoom, int cell_width, int cell_height);

    struct Callbacks;

    GhosttyTerminalImpl* term_ = nullptr;
    GhosttyRenderStateImpl* rs_ = nullptr;
    GhosttyRenderStateRowIteratorImpl* row_it_ = nullptr;
    GhosttyRenderStateRowCellsImpl* cells_ = nullptr;
    GhosttyKeyEncoderImpl* key_enc_ = nullptr;
    GhosttyKeyEventImpl* key_ev_ = nullptr;
    GhosttyMouseEncoderImpl* mouse_enc_ = nullptr;
    GhosttyMouseEventImpl* mouse_ev_ = nullptr;
    int term_cols_ = 0, term_rows_ = 0;
    size_t scrollback_;

    std::vector<sf::Color> fg_, bg_;
    std::vector<uint16_t> flags_;
    std::vector<int> chunk_blink_;   // blinking cells per chunk
    int blink_cells_ = 0;

    bool callback_failed_ = false;   // a library callback could not do its job (reported by the caller)
    bool needs_sync_ = true;
    bool force_full_ = true;
    bool screen_reverse_ = false;
    bool held_ = false;              // synchronized output (mode 2026) hold
    int hold_start_ms_ = 0;

    bool has_background_ = false;
    sf::Color background_ = sf::Color::Transparent;
    sf::Color default_fg_ = sf::Color::White, default_bg_ = sf::Color::Black, cursor_colour_ = sf::Color::White;

    int blink_interval_ms_ = 500;
    bool blink_on_ = true;
    bool registered_ = false;

    bool cursor_in_view_ = false, cursor_visible_ = true, cursor_blinking_ = false, cursor_wide_ = false;
    int cursor_x_ = 0, cursor_y_ = 0, cursor_style_ = 1;

    unsigned mouse_buttons_down_ = 0;
};

namespace mcrfpydef {
    extern PyTypeObject PyTerminalLayerType;
}

// Python-facing pieces GridLayers.cpp and UIGridPoint.cpp need.
namespace TerminalLayerAPI {
    // Print the codepoint of `index` at (x, y) through the terminal (a GridPoint write).
    // Returns false with a Python error set.
    bool set_cell(const std::shared_ptr<TerminalLayer>& layer, int x, int y, long long index);
    // Hand pending_output to on_output where no Python caller can receive an error (a
    // resize from the grid): a failure is reported as engine callbacks report theirs.
    void flush_from_engine(const std::shared_ptr<TerminalLayer>& layer);
}
