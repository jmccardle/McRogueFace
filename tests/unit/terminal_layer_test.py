"""#550 TerminalLayer: bytes in, cells out (EXPERIMENTAL API).

State checks only (no pixels; see terminal_layer_render_test.py): the emulator's screen as
screen_text(), cursor and the per-cell tile indices that the inherited accessors return;
replies and encoded input through on_output; the curses-style helpers; the inherited TileLayer
writes that go through the terminal; lifecycle. Fonts are vendored in tests/assets/fonts/ and
the test fails, not skips, if one is missing.
"""
import gc
import os
import sys
import weakref

import mcrfpy

errors = []


def test(name, cond, msg=""):
    if cond:
        print(f"  PASS: {name}")
    else:
        errors.append(f"{name} {msg}")
        print(f"  FAIL: {name} {msg}")


def raises(name, exc, fn, needle=None):
    try:
        fn()
    except exc as e:
        test(name, needle is None or needle in str(e), f"message {e!r} lacks {needle!r}")
    except Exception as e:  # wrong type
        test(name, False, f"raised {type(e).__name__}: {e}")
    else:
        test(name, False, "did not raise")


FONT = mcrfpy.Font("assets/JetbrainsMono.ttf")
FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "fonts")
BOLD = mcrfpy.Font(os.path.join(FONTS, "DejaVuSansMono-Bold.ttf"))
WIDE = mcrfpy.Font(os.path.join(FONTS, "DroidSansFallback-subset.ttf"))
TEX = mcrfpy.Texture.from_font(FONT, 16)
I = TEX.index


def term(cols=20, rows=5, **kw):
    out = []
    t = mcrfpy.TerminalLayer(texture=TEX, grid_size=(cols, rows), on_output=out.append, **kw)
    return t, out


def lines(t):
    return t.screen_text().split("\n")


# --- construction ----------------------------------------------------------------------
print("=== construction ===")
t, out = term()
test("is a TileLayer", isinstance(t, mcrfpy.TileLayer))
test("grid_size", t.grid_size == (20, 5), f"{t.grid_size}")
test("texture is the one given", t.texture is TEX)
test("empty screen", t.screen_text() == "\n" * 4, repr(t.screen_text()))
test("cursor home", t.cursor == (0, 0), f"{t.cursor}")
test("empty cell has no tile", t.at(0, 0) == -1, f"{t.at(0, 0)}")
test("scrollback default 1000", t.scrollback == 1000)
test("blink_interval default 0.5", t.blink_interval == 0.5)
test("background default None", t.background is None)
test("show_cursor default True", t.show_cursor is True)
d1 = mcrfpy.TerminalLayer(grid_size=(4, 4))
d2 = mcrfpy.TerminalLayer(texture=None, grid_size=(4, 4))
test("no texture: a default atlas from default_font", d1.texture.white_tile == 1 and d1.texture.index("A") > 1)
test("...shared by every layer that uses it", d1.texture is d2.texture)
test("...16 px", d1.texture.sprite_height == mcrfpy.Texture.from_font(mcrfpy.default_font, 16).sprite_height)
d1.write(b"ok")
test("...and it works", d1.screen_text().startswith("ok") and d1.at(0, 0) == d1.texture.index("o"))
raises("a non-font texture is refused", ValueError,
       lambda: mcrfpy.TerminalLayer(texture=mcrfpy.default_texture, grid_size=(4, 4)), "from_font")
raises("negative scrollback", ValueError, lambda: mcrfpy.TerminalLayer(texture=TEX, grid_size=(4, 4), scrollback=-1))
raises("on_output must be callable", TypeError,
       lambda: mcrfpy.TerminalLayer(texture=TEX, grid_size=(4, 4), on_output=3))
unsized = mcrfpy.TerminalLayer(texture=TEX)
test("unsized layer is 0x0", unsized.grid_size == (0, 0))
raises("write on an unsized layer", RuntimeError, lambda: unsized.write(b"x"), "no size")
test("unsized screen_text is empty", unsized.screen_text() == "")

# --- plain text, cursor movement --------------------------------------------------------
print("=== text and cursor ===")
t, out = term()
t.write(b"Hello\r\nworld")
test("two lines", lines(t)[:2] == ["Hello", "world"], repr(t.screen_text()))
test("cursor after text", t.cursor == (5, 1), f"{t.cursor}")
test("at() is the glyph's tile", t.at(0, 0) == I("H") and t.at(4, 1) == I("d"), f"{t.at(0, 0)}")
test("subscript too", t[1, 0] == I("e"))
t.write("\x1b[3;5HXY")  # str is sent as UTF-8
test("CUP then text", lines(t)[2] == "    XY", repr(lines(t)[2]))
t.write(b"\x1b[A\x1b[2D!")  # cursor (6, 2) -> up 1, left 2 -> (4, 1)
test("CUU/CUB", lines(t)[1] == "worl!", repr(lines(t)[1]))
t.write(b"\x1b[2D\x1b[K")
test("EL erases from the cursor (3, 1) to the end of the line", lines(t)[1] == "wor", repr(lines(t)[1]))
t.write(b"\x1b[2J\x1b[H")
test("ED 2 clears", t.screen_text() == "\n" * 4, repr(t.screen_text()))
test("bytearray and memoryview accepted", (t.write(bytearray(b"a")), t.write(memoryview(b"b")))[0] is None
     and lines(t)[0] == "ab")
raises("write(int) is a TypeError", TypeError, lambda: t.write(5))

# --- SGR colours and attributes -----------------------------------------------------------
print("=== SGR ===")
t, out = term()
pal = t.palette
test("palette has 256 colours", len(pal) == 256 and isinstance(pal[0], mcrfpy.Color))
test("palette 196 is pure red", (pal[196].r, pal[196].g, pal[196].b) == (255, 0, 0), f"{pal[196]}")
t.write(b"\x1b[1mB\x1b[0m\x1b[3mI\x1b[0m")
test("bold without a bold face keeps the regular tile", t.at(0, 0) == I("B"))
test("italic without an italic face keeps the regular tile", t.at(1, 0) == I("I"))
tb = mcrfpy.Texture.from_font(FONT, 16, codepoints="AB", bold=BOLD)
tbl = mcrfpy.TerminalLayer(texture=tb, grid_size=(4, 1))
tbl.write(b"A\x1b[1mA\x1b[0mA")
test("bold face tile from the atlas", tbl.at(1, 0) == tb.index("A", bold=True) and tbl.at(0, 0) == tb.index("A"),
     f"{tbl.at(1, 0)} vs {tb.index('A', bold=True)}")
test("unknown codepoint draws the box", (tbl.write(b"\r\x1b[2C?"), tbl.at(2, 0))[1] == tb.box_tile)

# --- erase, scroll regions, alternate screen ---------------------------------------------
print("=== erase / regions / alt screen ===")
t, out = term(10, 5)
t.write(b"1\r\n2\r\n3\r\n4\r\n5")
t.write(b"\x1b[2;4r\x1b[4;1H\n")  # scroll region rows 2-4, LF at its bottom scrolls only it
test("scroll region scrolls only rows 2-4", lines(t) == ["1", "3", "4", "", "5"], repr(lines(t)))
t.write(b"\x1b[r")
t2, _ = term(10, 3)
t2.write(b"main")
t2.write(b"\x1b[?1049h")
test("alternate screen starts empty", t2.screen_text() == "\n\n", repr(t2.screen_text()))
t2.write(b"alt")
t2.write(b"\x1b[?1049l")
test("leaving it restores the main screen", lines(t2)[0] == "main", repr(t2.screen_text()))

# --- wide characters ---------------------------------------------------------------------
print("=== wide ===")
tw2 = mcrfpy.Texture.from_font(WIDE, 16, codepoints=[(0x20, 0x7E), 0x65E5])
w = mcrfpy.TerminalLayer(texture=tw2, grid_size=(6, 1))
w.write("a日b")
test("wide glyph left half", w.at(1, 0) == tw2.index(0x65E5), f"{w.at(1, 0)} vs {tw2.index(0x65E5)}")
test("spacer cell shows the right half (index + 1)", w.at(2, 0) == tw2.index(0x65E5) + 1, f"{w.at(2, 0)}")
test("next character two cells on", w.at(3, 0) == tw2.index("b"))
test("screen_text has the wide character once", w.screen_text() == "a日b", repr(w.screen_text()))
test("cursor after it", w.cursor == (4, 0), f"{w.cursor}")

# --- size from the grid -------------------------------------------------------------------
# A Grid's size is fixed, so a layer is resized exactly once: from (0, 0) when it is attached.
print("=== size ===")
g = mcrfpy.Grid(grid_size=(10, 3), texture=TEX, layers=[])
r = mcrfpy.TerminalLayer(texture=TEX)
g.add_layer(r)
test("adopts the grid's size on attach", r.grid_size == (10, 3), f"{r.grid_size}")
r.write(b"0123456789abcde")
test("wraps at the grid's width", lines(r)[:2] == ["0123456789", "abcde"], repr(r.screen_text()))
test("cells follow the screen", r.at(0, 1) == I("a"), f"{r.at(0, 1)}")
raises("a sized layer must match the grid", ValueError,
       lambda: mcrfpy.Grid(grid_size=(10, 3), texture=TEX, layers=[mcrfpy.TerminalLayer(texture=TEX, grid_size=(4, 4))]))
via_kw = mcrfpy.TerminalLayer(texture=TEX, grid=mcrfpy.Grid(grid_size=(7, 2), texture=TEX, layers=[]))
test("grid= at construction sizes it", via_kw.grid_size == (7, 2))

# --- scrollback ---------------------------------------------------------------------------
print("=== scrollback ===")
s, _ = term(10, 3, scrollback=100)
s.write(b"\r\n".join(b"line%d" % i for i in range(10)))
test("live screen shows the last 3", lines(s) == ["line7", "line8", "line9"], repr(s.screen_text()))
test("history rows", s.scrollback_rows == 7, f"{s.scrollback_rows}")
test("scroll_offset 0 is live", s.scroll_offset == 0)
s.scroll(2)
test("scroll(2) goes back 2 rows", lines(s) == ["line5", "line6", "line7"] and s.scroll_offset == 2,
     f"{s.screen_text()!r} {s.scroll_offset}")
test("cursor (on the bottom live row) is off a viewport scrolled back 2", s.cursor is None, f"{s.cursor}")
s.scroll(100)
test("clamped at the top", lines(s)[0] == "line0" and s.scroll_offset == 7, f"{s.scroll_offset}")
s.scroll(-3)
test("negative scrolls toward live", s.scroll_offset == 4, f"{s.scroll_offset}")
s.write(b"\r\nnew")
test("new output leaves a scrolled-back viewport where it was", s.scroll_offset >= 4 and "line" in lines(s)[0],
     f"{s.scroll_offset} {s.screen_text()!r}")
s.scroll_offset = 0
test("scroll_offset = 0 returns live", lines(s)[-1] == "new", repr(s.screen_text()))
s.scroll_offset = 3
test("scroll_offset setter", s.scroll_offset == 3, f"{s.scroll_offset}")
raises("negative scroll_offset", ValueError, lambda: setattr(s, "scroll_offset", -1))
s0, _ = term(10, 3, scrollback=0)
s0.write(b"\r\n".join(b"x%d" % i for i in range(10)))
test("scrollback=0 keeps no history", s0.scrollback_rows == 0, f"{s0.scrollback_rows}")

# --- title, cursor style -------------------------------------------------------------------
print("=== title / cursor ===")
t, out = term()
t.write(b"\x1b]2;my title\x07")
test("OSC 2 title", t.title == "my title", repr(t.title))
t.write(b"\x1b[6 q")
test("DECSCUSR bar", t.cursor_style == "bar", t.cursor_style)
t.write(b"\x1b[4 q")
test("DECSCUSR underline", t.cursor_style == "underline")
t.write(b"\x1b[?25l")
test("DECTCEM hides", t.cursor_visible is False)
t.write(b"\x1b[?25h")
test("DECTCEM shows", t.cursor_visible is True)

# --- synchronized output (mode 2026) ----------------------------------------------------------
print("=== synchronized output ===")
t, out = term()
t.write(b"before")
t.write(b"\x1b[?2026h\r\x1b[Kduring")
test("while the program holds the frame, the old one is shown", lines(t)[0] == "before", repr(lines(t)[0]))
test("...and the cells match it", t.at(0, 0) == I("b"))
t.write(b"\x1b[?2026l")
test("released: the new frame", lines(t)[0] == "during", repr(lines(t)[0]))
t.write(b"\x1b[?2026h\r\x1b[Knever released")
test("held again", lines(t)[0] == "during")
g_hold = mcrfpy.Grid(grid_size=(20, 5), texture=TEX, layers=[t])
mcrfpy.step(1.1)
test("a hold longer than 1 s of engine time is ended by the clock (nothing written)",
     t.at(0, 0) == I("n") and lines(t)[0] == "never released", repr(lines(t)[0]))

# --- palette ------------------------------------------------------------------------------------
print("=== palette ===")
t, out = term()
p = t.palette
p[1] = mcrfpy.Color(1, 2, 3)
t.palette = p
test("palette setter", (t.palette[1].r, t.palette[1].g, t.palette[1].b) == (1, 2, 3))
raises("palette needs 256 colours", ValueError, lambda: setattr(t, "palette", p[:10]))
t.palette = None
test("palette None restores the built-in one", t.palette[1] != mcrfpy.Color(1, 2, 3))
t.write(b"\x1b]4;2;rgb:10/20/30\x1b\\")
test("OSC 4 changes show in palette", (t.palette[2].r, t.palette[2].g, t.palette[2].b) == (0x10, 0x20, 0x30),
     f"{t.palette[2]}")

# --- on_output: replies, re-entrancy, exceptions -------------------------------------------
print("=== on_output ===")
t, out = term()
t.write(b"ab\x1b[6n")
test("DSR cursor report", out == [b"\x1b[1;3R"], f"{out}")
out.clear()
t.write(b"\x1b[c")
test("DA reply", len(out) == 1 and out[0].startswith(b"\x1b[?") and out[0].endswith(b"c"), f"{out}")
out.clear()
t.background = mcrfpy.Color(10, 20, 30)
t.write(b"\x1b]11;?\x1b\\")
test("a background query answers with background", out and b"rgb:0a0a/1414/1e1e" in out[0], f"{out}")
t.background = None
t.on_output = None
t.write(b"\x1b[6n")  # dropped
test("on_output None drops replies", t.on_output is None)

log = []


def reentrant(data):
    log.append(data)
    if data == b"\x1b[1;1R":
        t.write(b"X\x1b[6n")  # writes from inside the callback; its reply comes after this one


t, _ = term()
t.on_output = reentrant
t.write(b"\x1b[6n")
test("re-entrant write is applied", lines(t)[0] == "X", repr(t.screen_text()))
test("its reply is delivered after, in order", log == [b"\x1b[1;1R", b"\x1b[1;2R"], f"{log}")


class Boom(Exception):
    pass


def boom(data):
    raise Boom("on_output failed")


t, _ = term()
t.on_output = boom
raises("an exception in on_output propagates out of write()", Boom, lambda: t.write(b"\x1b[6n"))
raises("and out of key()", Boom, lambda: t.key(mcrfpy.Key.ENTER))
t.on_output = None


def drop_self(data):
    holder.clear()
    gc.collect()


holder = [mcrfpy.TerminalLayer(texture=TEX, grid_size=(4, 1))]
ref = weakref.ref(holder[0])
holder[0].on_output = drop_self
holder[0].write(b"\x1b[6n")
gc.collect()
test("layer whose last reference goes in its callback is freed afterwards", ref() is None)

# a cycle through on_output is collected
c = mcrfpy.TerminalLayer(texture=TEX, grid_size=(4, 1))
c.on_output = lambda d, c=c: None
cref = weakref.ref(c)
del c
gc.collect()
test("cycle layer -> on_output -> layer is collected", cref() is None)

# --- input encoding -------------------------------------------------------------------------
print("=== input ===")
K, S = mcrfpy.Key, mcrfpy.InputState
t, out = term()


def sent(fn):
    out.clear()
    fn()
    return b"".join(out)


test("Enter is CR", sent(lambda: t.key(K.ENTER, S.PRESSED, ())) == b"\r")
test("Up arrow (normal mode)", sent(lambda: t.key(K.UP, S.PRESSED, ())) == b"\x1b[A")
test("Shift+Up", sent(lambda: t.key(K.UP, S.PRESSED, "shift")) == b"\x1b[1;2A")
test("Ctrl+Right", sent(lambda: t.key(K.RIGHT, S.PRESSED, {"ctrl"})) == b"\x1b[1;5C")
test("F1", sent(lambda: t.key(K.F1, S.PRESSED, ())) == b"\x1bOP")
test("F5", sent(lambda: t.key(K.F5, S.PRESSED, ())) == b"\x1b[15~")
test("Ctrl+F5", sent(lambda: t.key(K.F5, S.PRESSED, "ctrl")) == b"\x1b[15;5~")
test("Ctrl+C", sent(lambda: t.key(K.C, S.PRESSED, "ctrl")) == b"\x03")
test("Alt+x", sent(lambda: t.key(K.X, S.PRESSED, "alt")) == b"\x1bx")
test("a plain letter key sends nothing (its text comes from text())", sent(lambda: t.key(K.A, S.PRESSED, ())) == b"")
test("a release sends nothing in legacy mode", sent(lambda: t.key(K.UP, S.RELEASED, ())) == b"")
test("REPEATED sends like PRESSED", sent(lambda: t.key(K.UP, S.REPEATED, ())) == b"\x1b[A")
test("Backspace", sent(lambda: t.key(K.BACKSPACE, S.PRESSED, ())) == b"\x7f")
test("Tab", sent(lambda: t.key(K.TAB, S.PRESSED, ())) == b"\t")
test("Escape", sent(lambda: t.key(K.ESCAPE, S.PRESSED, ())) == b"\x1b")
test("Home", sent(lambda: t.key(K.HOME, S.PRESSED, ())) in (b"\x1b[H", b"\x1bOH"))
t.write(b"\x1b[?1h")  # DECCKM: application cursor keys
test("Up arrow (application mode)", sent(lambda: t.key(K.UP, S.PRESSED, ())) == b"\x1bOA")
test("Shift+Up (application mode)", sent(lambda: t.key(K.UP, S.PRESSED, "shift")) == b"\x1b[1;2A")
t.write(b"\x1b[?1l")
test("default state is PRESSED, mods from the keyboard", sent(lambda: t.key(K.DOWN)) == b"\x1b[B")
raises("unknown modifier", ValueError, lambda: t.key(K.UP, S.PRESSED, "hyper"))
raises("unmapped key", ValueError, lambda: t.key(K.UNKNOWN, S.PRESSED, ()))
test("text a", sent(lambda: t.text("a")) == b"a")
test("text unicode", sent(lambda: t.text("é日")) == "é日".encode())
raises("text control char", ValueError, lambda: t.text("\r"))

# mouse
test("mouse with reporting off sends nothing", sent(lambda: t.mouse((3, 2), mcrfpy.MouseButton.LEFT, S.PRESSED)) == b"")
t.write(b"\x1b[?1000h\x1b[?1006h")  # normal tracking, SGR format
test("SGR press", sent(lambda: t.mouse((3, 2), mcrfpy.MouseButton.LEFT, S.PRESSED)) == b"\x1b[<0;4;3M",
     repr(sent(lambda: None)))
test("SGR release", sent(lambda: t.mouse((3, 2), mcrfpy.MouseButton.LEFT, S.RELEASED)) == b"\x1b[<0;4;3m")
test("SGR wheel up", sent(lambda: t.mouse((0, 0), mcrfpy.MouseButton.SCROLL_UP)) == b"\x1b[<64;1;1M")
test("SGR right with ctrl", sent(lambda: t.mouse((1, 1), mcrfpy.MouseButton.RIGHT, S.PRESSED, "ctrl")) == b"\x1b[<18;2;2M")
test("motion without button tracking sends nothing", sent(lambda: t.mouse((5, 1))) == b"")
t.write(b"\x1b[?1000l\x1b[?1006l")

# paste
test("paste without bracketed mode", sent(lambda: t.paste("hello")) == b"hello")
raises("multi-line paste outside bracketed mode is refused", ValueError, lambda: t.paste("a\nb"), "allow_unsafe")
test("allow_unsafe sends it with CR", sent(lambda: t.paste("a\nb", allow_unsafe=True)) == b"a\rb")
t.write(b"\x1b[?2004h")
test("bracketed paste", sent(lambda: t.paste("a\nb")) == b"\x1b[200~a\nb\x1b[201~")
t.write(b"\x1b[?2004l")

# focus
test("focus with reporting off sends nothing", sent(lambda: t.focus(True)) == b"")
t.write(b"\x1b[?1004h")
test("focus gained", sent(lambda: t.focus(True)) == b"\x1b[I")
test("focus lost", sent(lambda: t.focus(False)) == b"\x1b[O")

# --- curses-style helpers --------------------------------------------------------------------
print("=== helpers ===")
t, out = term(20, 5)
t.move(3, 1)
test("move(x, y)", t.cursor == (3, 1))
t.move((5, 2))
test("move((x, y))", t.cursor == (5, 2))
raises("move outside", IndexError, lambda: t.move(20, 0))
t.print("hi", fg=(255, 0, 0), bold=True)
test("print at the cursor", lines(t)[2] == "     hi" and t.cursor == (7, 2), f"{t.screen_text()!r} {t.cursor}")
t.write(b"z")
# the attributes were reset after print: 'z' has the default style (regular tile)
test("attributes reset after print", t.at(7, 2) == I("z"))
t.move(1, 1)
t.write(b"\x1b[4m")  # the program's own underline is in effect
t.print("HP 12/20", pos=(0, 4), fg="green")
test("print at pos", lines(t)[4] == "HP 12/20", repr(lines(t)[4]))
test("cursor restored around print(pos=)", t.cursor == (1, 1), f"{t.cursor}")
t.write(b"\x1b[0m")
t.print("a\nb", pos=(10, 0))
test("with pos=, a newline continues at pos's column", lines(t)[0][10:] == "a" and lines(t)[1][10:11] == "b",
     repr(t.screen_text()))
t.move(0, 3)
t.print("c\nd")
test("at the cursor, a newline continues at column 0", lines(t)[3] == "c" and lines(t)[4].startswith("d"),
     repr(t.screen_text()))
t.print("p", pos=(0, 0), fg=200, bg=mcrfpy.Color(1, 2, 3))
raises("palette index range", ValueError, lambda: t.print("x", fg=256))
raises("translucent colour refused", ValueError, lambda: t.print("x", fg=(1, 2, 3, 4)))
raises("print pos outside", IndexError, lambda: t.print("x", pos=(0, 5)))
t.move(2, 3)
t.clear_line()
test("clear_line erases the cursor line", lines(t)[3] == "", repr(lines(t)[3]))
test("clear_line leaves the cursor", t.cursor == (2, 3))
t.clear_line(4)
test("clear_line(y)", lines(t)[4] == "" and t.cursor == (2, 3))
t.clear()
test("clear empties the screen and homes", t.screen_text() == "\n" * 4 and t.cursor == (0, 0))

# helpers in a program's modes: origin mode + scroll region, insert mode, DEC graphics charset
t, out = term(10, 4)
t.write(b"\x1b[2;3r\x1b[?6h\x1b[4h\x1b(0")  # region 2-3, origin mode, insert mode, line drawing
t.print("q", pos=(0, 0))
t.set((1, 0), I("q"))
test("pos= is absolute and plain ASCII despite origin mode and DEC graphics", lines(t)[0] == "qq",
     repr(t.screen_text()))
t.write(b"q")
test("the program's charset is restored (q is a line in DEC graphics)", lines(t)[1][0:1] not in ("q", ""),
     repr(t.screen_text()))

# --- inherited TileLayer methods -------------------------------------------------------------
print("=== inherited ===")
t, out = term(10, 3)
t.move(9, 2)
t.set((1, 1), I("@"))
test("set() prints the glyph", lines(t)[1] == " @" and t.at(1, 1) == I("@"))
test("set() leaves the cursor", t.cursor == (9, 2))
t[2, 1] = I("#")
test("layer[x, y] = i", t.at(2, 1) == I("#"))
raises("set(-1)", ValueError, lambda: t.set((0, 0), -1), "no codepoint")
raises("set(box)", ValueError, lambda: t.set((0, 0), TEX.box_tile), "box")
raises("set(white)", ValueError, lambda: t.set((0, 0), TEX.white_tile), "white")
raises("set(out of range)", ValueError, lambda: t.set((0, 0), TEX.sprite_count + 5))
raises("set outside", IndexError, lambda: t.set((10, 0), I("a")))
t.fill_rect((1, 0), (3, 2), I("*"))
test("fill_rect", lines(t)[0] == " ***" and lines(t)[1] == " ***", repr(t.screen_text()))
t.fill_rect((8, 2), (5, 5), I("+"))
test("fill_rect clips", lines(t)[2] == "        ++", repr(lines(t)[2]))
raises("fill_rect(-1)", ValueError, lambda: t.fill_rect((0, 0), (2, 2), -1))
t.fill(I("."))
test("fill", t.screen_text() == "\n".join(["." * 10] * 3), repr(t.screen_text()))
test("fill leaves the cursor", t.cursor == (9, 2))
gp_grid = mcrfpy.Grid(grid_size=(10, 3), texture=TEX, layers=[])
gp_grid.add_layer(t)
t2 = mcrfpy.TerminalLayer(name="term", texture=TEX)
gp_grid.add_layer(t2)
gp_grid.at(4, 1).term = I("Q")
test("GridPoint write goes through the terminal", lines(t2)[1] == "    Q", repr(t2.screen_text()))
test("GridPoint read", gp_grid.at(4, 1).term == I("Q"))
raises("GridPoint write of an index with no codepoint", ValueError, lambda: setattr(gp_grid.at(0, 0), "term", -1))
hm = mcrfpy.HeightMap((10, 3))
hm.fill(0.5)
t2.apply_threshold(hm, (0.0, 1.0), I("~"))
test("apply_threshold through the terminal", lines(t2)[0] == "~" * 10, repr(t2.screen_text()))
t2.apply_ranges(hm, [((0.0, 1.0), I("="))])
test("apply_ranges through the terminal", lines(t2)[2] == "=" * 10, repr(t2.screen_text()))
raises("apply_threshold with an index with no codepoint", ValueError, lambda: t2.apply_threshold(hm, (0.0, 1.0), -1))
test("...prints nothing", lines(t2)[0] == "=" * 10)

with t2.edit() as view:
    test("edit() view is read-only", view.readonly)
    test("edit() view has the tiles", view[1 * 10 + 4] if view.ndim == 1 else view[1, 4] == I("="))
    raises("writing the view fails", TypeError, lambda: view.__setitem__((0, 0), 1))
import io  # noqa: E402
# A writable request fails in the buffer export (BufferError); argument parsers report it as TypeError.
raises("asking for a writable buffer raises", (BufferError, TypeError), lambda: io.BytesIO(b"xxxx").readinto(t2.edit()))

# Tiled / LDtk writers put tile indices straight into a layer's storage: a TerminalLayer is refused.
HERE = os.path.dirname(os.path.abspath(__file__))
tl_ws = mcrfpy.TerminalLayer(texture=TEX, grid_size=(5, 5))
proj = mcrfpy.LdtkProject(os.path.join(HERE, "..", "fixtures", "test_project.ldtk"))
raises("AutoRuleSet.apply refuses a TerminalLayer", TypeError,
       lambda: proj.ruleset("Terrain").apply(mcrfpy.DiscreteMap((5, 5), fill=0), tl_ws, seed=0), "TerminalLayer")
ws = mcrfpy.TileSetFile(os.path.join(HERE, "..", "assets", "tiled", "test_tileset.tsx")).wang_set("terrain")
raises("WangSet.apply refuses a TerminalLayer", TypeError,
       lambda: ws.apply(mcrfpy.DiscreteMap((5, 5)), tl_ws), "TerminalLayer")
tm = mcrfpy.TileMapFile(os.path.join(HERE, "..", "assets", "tiled", "test_map.tmx"))
raises("TileMapFile.apply_to_tile_layer refuses a TerminalLayer", TypeError,
       lambda: tm.apply_to_tile_layer(tl_ws, "Ground"), "TerminalLayer")

# --- lifecycle ----------------------------------------------------------------------------------
print("=== lifecycle ===")
g = mcrfpy.Grid(grid_size=(8, 2), texture=TEX, layers=[])
lt = mcrfpy.TerminalLayer(name="lt", texture=TEX, grid=g)
lt.write(b"keep")
lref = weakref.ref(lt)
del lt
gc.collect()
back = g.layer("lt")
test("the grid keeps the layer; the wrapper comes back as a TerminalLayer", isinstance(back, mcrfpy.TerminalLayer))
test("and its screen", lines(back)[0] == "keep")
g.remove_layer(back)
test("detached layer keeps working", (back.write(b"!"), lines(back)[0])[1] == "keep!")
g.add_layer(back)
test("re-attached", g.layer("lt") is back)
z = mcrfpy.TerminalLayer(texture=TEX, grid_size=(4, 2))
z.write(b"zz")
# texture swap: a new font atlas re-maps every cell; anything else is refused
tex2 = mcrfpy.Texture.from_font(FONT, 20)
z.texture = tex2
test("texture swap re-maps the cells", z.at(0, 0) == tex2.index("z"), f"{z.at(0, 0)} vs {tex2.index('z')}")
raises("a non-font texture is refused", ValueError, lambda: setattr(z, "texture", mcrfpy.default_texture))
z.texture = None
test("texture None assigns the shared default atlas", z.texture is d1.texture and z.at(0, 0) == d1.texture.index("z"))
# re-running TileLayer.__init__ on the wrapper turns it into a plain TileLayer: its methods say so
odd = mcrfpy.TerminalLayer(texture=TEX, grid_size=(2, 2))
mcrfpy.TileLayer.__init__(odd, grid_size=(2, 2))
raises("TerminalLayer methods on a re-initialised wrapper", RuntimeError, lambda: odd.write(b"x"), "not initialized")
# many layers created and dropped: each terminal is freed (exercised under ASan)
for _ in range(50):
    tmp = mcrfpy.TerminalLayer(texture=TEX, grid_size=(80, 24))
    tmp.write(b"x" * 100)
del tmp
gc.collect()

# --- review fixes: no path writes cells around the terminal ---------------------------------
print("=== TileLayer methods on a TerminalLayer ===")


def consistent(t):
    """Every cell's tile is the one its character on screen maps to (narrow text only)."""
    rows = t.screen_text().split("\n")
    for y in range(t.grid_size[1]):
        row = rows[y] if y < len(rows) else ""
        for x in range(t.grid_size[0]):
            ch = row[x] if x < len(row) else None
            want = TEX.index(ch) if ch not in (None, " ") else None
            got = t.at(x, y)
            if want is None and got not in (-1, TEX.index(" ")):
                return False
            if want is not None and got != want:
                return False
    return True


TL = mcrfpy.TileLayer
t, out = term(10, 3)
t.write(b"abc")
raises("TileLayer.set(term, huge index) refuses like set()", ValueError, lambda: TL.set(t, (0, 0), 10**7), "no codepoint")
raises("TileLayer.set(term, -1)", ValueError, lambda: TL.set(t, (1, 0), -1))
TL.set(t, (4, 1), I("Q"))
test("TileLayer.set(term) prints through the terminal", lines(t)[1] == "    Q" and consistent(t), repr(t.screen_text()))
TL.fill_rect(t, (0, 2), (3, 1), I("#"))
test("TileLayer.fill_rect(term)", lines(t)[2] == "###" and consistent(t), repr(t.screen_text()))
TL.__setitem__(t, (9, 0), I("Z"))
test("TileLayer.__setitem__(term)", lines(t)[0].endswith("Z") and consistent(t), repr(t.screen_text()))
hm2 = mcrfpy.HeightMap((10, 3))
hm2.fill(0.5)
TL.apply_threshold(t, hm2, (0.0, 1.0), I("~"))
test("TileLayer.apply_threshold(term)", lines(t)[0] == "~" * 10 and consistent(t), repr(t.screen_text()))
TL.apply_ranges(t, hm2, [((0.0, 1.0), I("="))])
test("TileLayer.apply_ranges(term)", lines(t)[1] == "=" * 10 and consistent(t), repr(t.screen_text()))
TL.fill(t, I("."))
test("TileLayer.fill(term)", t.screen_text() == "\n".join(["." * 10] * 3) and consistent(t))
tiny = mcrfpy.Texture.from_font(FONT, 16, codepoints="}~")
t.write(b"\x1b[2J\x1b[H}~\x1b[H")
TL.texture.__set__(t, tiny)
test("TileLayer.texture setter on a terminal re-maps the cells", t.texture is tiny and t.at(0, 0) == tiny.index("}"),
     f"{t.at(0, 0)}")
raises("TileLayer.texture setter refuses a non-font texture", ValueError, lambda: TL.texture.__set__(t, mcrfpy.default_texture))
TL.texture.__set__(t, TEX)
test("TileLayer.at(term) reads the synced cells", (t.write(b"\x1b[2;2HR"), TL.at(t, 1, 1))[1] == I("R"))

print("=== print() is text only ===")
t, out = term(10, 3)
raises("print() refuses ESC", ValueError, lambda: t.print("\x1b]2;pwned\x07\x1b[?1049h\x1b[6n", pos=(0, 0)), "write()")
test("...and sends nothing", t.title == "" and out == [] and t.screen_text() == "\n\n")
raises("print() refuses BEL", ValueError, lambda: t.print("a\x07"), "U+0007")
raises("print() refuses DEL", ValueError, lambda: t.print("\x7f"))
raises("print() refuses C1 CSI", ValueError, lambda: t.print("\x9b6n"), "U+009B")
raises("print() refuses CR", ValueError, lambda: t.print("a\rb"))
t.print("a\tb", pos=(0, 0))
test("tab is allowed", lines(t)[0] == "a       b", repr(lines(t)[0]))
# (A tile whose codepoint is a control character is refused by set()/fill_rect too; no font has a
# glyph for one, so from_font never makes such a tile and that check cannot be reached from here.)

print("=== placed text never wraps or scrolls ===")
t, out = term(6, 3)
t.write(b"top\r\nmid\r\nbot")
t.set((5, 2), I("x"))
test("set() at the bottom-right corner does not scroll", lines(t) == ["top", "mid", "bot  x"], repr(t.screen_text()))
t.print("0123456789", pos=(4, 0))
test("print(pos=) is clipped at the right edge", lines(t)[0] == "top 01" and lines(t)[1] == "mid", repr(t.screen_text()))
t.print("A\nB\nC\nD", pos=(2, 1))
test("print(pos=) lines stop at the bottom row (no scroll)",
     lines(t) == ["top 01", "miA", "boB  x"], repr(t.screen_text()))
t, out = term(10, 3)
t.write(b"line0")
t.print("0123456789ABCDEF", pos=(5, 2))
test("a 10-column layer keeps line0 when placed text is too long", lines(t)[0] == "line0" and lines(t)[2] == "     01234",
     repr(t.screen_text()))
t.write(b"\x1b[3;1H")
t.write(b"0123456789ABC")
test("the program's own autowrap is restored afterwards (13 chars on the last row wrap and scroll)",
     lines(t) == ["", "0123456789", "ABC"], repr(t.screen_text()))
t2, _ = term(10, 3)
t2.write(b"\x1b[?7l")
t2.set((0, 0), I("q"))
t2.write(b"\x1b[1;9H0123")
test("...and a program's autowrap-off stays off", lines(t2)[0] == "q       03" and lines(t2)[1] == "", repr(t2.screen_text()))

print("=== wide fill_rect ===")
TW = mcrfpy.Texture.from_font(WIDE, 16, codepoints=[(0x20, 0x7E), 0x65E5])
wt = mcrfpy.TerminalLayer(texture=TW, grid_size=(6, 2))
wt.write(b"zzzzzz")
wt.fill_rect((0, 0), (5, 1), TW.index(0x65E5))
test("a wide glyph fills pairs; the odd last column is blank", wt.screen_text().split("\n")[0] == "\u65e5\u65e5 z",
     repr(wt.screen_text()))
test("...cells: left, right, left, right, blank", [wt.at(x, 0) for x in range(5)] ==
     [TW.index(0x65E5), TW.index(0x65E5) + 1, TW.index(0x65E5), TW.index(0x65E5) + 1, TW.index(" ")],
     f"{[wt.at(x, 0) for x in range(6)]}")

print("=== default colour queries ===")
for label, bg in (("background=None", None), ("background=Color", mcrfpy.Color(10, 20, 30))):
    t, out = term(4, 1)
    t.background = bg
    for q in (b"\x1b]10;?\x1b\\", b"\x1b]11;?\x1b\\", b"\x1b]12;?\x1b\\"):
        t.write(q)
    want_bg = b"rgb:0000/0000/0000" if bg is None else b"rgb:0a0a/1414/1e1e"
    test(f"OSC 10/11/12 answered ({label})", len(out) == 3 and b"10;rgb:ffff/ffff/ffff" in out[0] and
         want_bg in out[1] and b"12;rgb:ffff/ffff/ffff" in out[2], f"{out}")
    out.clear()
    p = t.palette
    p[0] = mcrfpy.Color(5, 5, 5)
    t.palette = p
    for q in (b"\x1b]10;?\x1b\\", b"\x1b]11;?\x1b\\", b"\x1b]12;?\x1b\\"):
        t.write(q)
    test(f"...still answered after a palette change ({label})", len(out) == 3 and want_bg in out[1], f"{out}")

print("=== extremes ===")
s, _ = term(10, 3, scrollback=100)
s.write(b"\r\n".join(b"l%d" % i for i in range(20)))
for n, want in ((2**63, 17), (10**30, 17), (-(2**63), 0), (-(10**30), 0), (2**63 - 1, 17), (-(2**63) + 1, 0)):
    s.scroll_offset = 0
    s.scroll(5)
    s.scroll(n)
    test(f"scroll({n}) clamps", s.scroll_offset == want, f"{s.scroll_offset}")
for n in (2**63, 10**30):
    s.scroll_offset = n
    test(f"scroll_offset = {n} clamps to the top", s.scroll_offset == 17, f"{s.scroll_offset}")
raises("scroll_offset = -2**63", ValueError, lambda: setattr(s, "scroll_offset", -(2**63)))
m, out = term(10, 5)
m.write(b"\x1b[?1000h\x1b[?1006h")
for pos, want in (((1e9, 1e9), b"\x1b[<0;10;5M"), ((-1e9, -5), b"\x1b[<0;1;1M"), ((3e38, 2), b"\x1b[<0;10;3M"),
                  ((-3e38, 3e38), b"\x1b[<0;1;5M")):
    out.clear()
    m.mouse(pos, mcrfpy.MouseButton.LEFT, mcrfpy.InputState.PRESSED)
    test(f"mouse({pos}) clamps to the edge cell", out == [want], f"{out}")
# Non-finite positions are refused by the engine's position conversion (#540), like every pos=.
raises("mouse(NaN)", ValueError, lambda: m.mouse((float("nan"), 0), mcrfpy.MouseButton.LEFT, mcrfpy.InputState.PRESSED), "finite")
raises("mouse(inf)", ValueError, lambda: m.mouse((float("inf"), 0), mcrfpy.MouseButton.LEFT, mcrfpy.InputState.PRESSED), "finite")
m.write(b"\x1b[?1006l\x1b[?1015h")
out.clear()
m.mouse((1, 1), mcrfpy.MouseButton.LEFT, mcrfpy.InputState.PRESSED)
test("URxvt (1015) format", out == [b"\x1b[32;2;2M"], f"{out}")

# --- re-review: placement leaves the program's state alone ----------------------------------
# The test shape: the same program state on two terminals, the placed draw on one only, the
# program's output continued on both; the screens must agree outside the drawn cells, and so must
# the terminal's answers about its state (cursor report, DECRQSS pen and margins, DECRQM modes).
print("=== placement and program state ===")
STATE_QUERIES = [b"\x1b[6n", b"\x1bP$qm\x1b\\", b"\x1bP$qr\x1b\\", b"\x1bP$qs\x1b\\"] + \
                [b"\x1b[?%d$p" % m for m in (6, 7, 69, 25, 1)] + [b"\x1b[4$p"]


def answers(t, out):
    got = []
    for q in STATE_QUERIES:
        out.clear()
        t.write(q)
        got.append(b"".join(out))
    return got


def twin(setup, draw, after, drawn, cols=20, rows=6):
    a, out_a = term(cols, rows)
    b, out_b = term(cols, rows)
    for t in (a, b):
        t.write(setup)
    draw(a)
    for t in (a, b):
        t.write(after)
    sa, sb = lines(a), lines(b)
    diff = [(x, y) for y in range(rows) for x in range(cols)
            if (sa[y][x:x + 1] or " ") != (sb[y][x:x + 1] or " ") and (x, y) not in drawn]
    return diff, answers(a, out_a) == answers(b, out_b), a, b


MODES = {
    "plain": b"",
    "origin+region": b"\x1b[2;5r\x1b[?6h",
    "insert": b"\x1b[4h",
    "autowrap off": b"\x1b[?7l",
    "left/right margins": b"\x1b[?69h\x1b[5;10s",
    "DEC graphics": b"\x1b(0",
    "pen set": b"\x1b[1;4;31;42m",
    "pending wrap": b"\x1b[1;20HZ",
    "everything": b"\x1b[2;5r\x1b[?6h\x1b[4h\x1b[?69h\x1b[5;10s\x1b(0\x1b[1;31m",
}
for label, setup in MODES.items():
    # The draws go to rows 0 and 5, which the program's own output below never reaches.
    drawn = {(x, 0) for x in range(20)} | {(x, 5) for x in range(20)}
    placed = []

    def draw(t):
        t.fill_rect((0, 5), (20, 1), I("@"))
        t.print("0123456789ABCDEFGHIJ", pos=(0, 0))
        placed.extend([lines(t)[0], lines(t)[5]])

    diff, same, a, b = twin(setup + b"\x1b[3;7H", draw, b"qrs\r\nnext", drawn)
    test(f"{label}: the program continues exactly as without the draw", diff == [], f"{diff}")
    test(f"{label}: cursor, pen, margins and modes report the same", same)
    test(f"{label}: the placed cells are all drawn, full width",
         placed == ["0123456789ABCDEFGHIJ", "@" * 20], f"{placed}")

# protection: placed cells are unprotected; the program's protection is as before
diff, same, a, b = twin(b"\x1b[1\"q", lambda t: t.set((5, 1), I("@")), b"P\x1b[2;1H", {(5, 1)})
test("a protected pen does not protect placed cells", (a.write(b"\x1b[?2J"), lines(a)[1])[1].strip() == "", repr(lines(a)[1]))
test("...and the program's protection stays on", lines(a)[0][:1] == "P" and same, repr(lines(a)[0]))

# tabs in print(pos=) are the layer's 8 columns from pos, not the program's stops
t, out = term(20, 2)
t.write(b"\x1b[3g\x1bH")   # clear all tab stops, set one at column 0 only
t.write(b"xxxxxxxxxxxxxxxxxxxx")
t.print("a\tb", pos=(3, 1))
test("print(pos=) expands a tab to spaces up to 8 columns from its start", lines(t)[1] == "   a       b", repr(lines(t)[1]))
t.write(b"\x1b[2;1H")
t.print("\tc")
test("print() at the cursor sends HT: the program's tab stops apply (none after column 0: the last column)",
     lines(t)[1][19:] == "c", repr(lines(t)[1]))

# --- zero-width codepoints -------------------------------------------------------------------------
print("=== zero width ===")
TZ = mcrfpy.Texture.from_font(BOLD, 16, codepoints=[(0x20, 0x7E), 0x301])   # DejaVu has U+0301
z, out = term(10, 2)
z = mcrfpy.TerminalLayer(texture=TZ, grid_size=(10, 2))
z.write(b"ABCDEFG")
raises("set() of a combining mark", ValueError, lambda: z.set((5, 0), TZ.index(0x301)), "zero width")
raises("fill_rect() of a combining mark", ValueError, lambda: z.fill_rect((0, 1), (3, 1), TZ.index(0x301)), "zero width")
test("...nothing changed", z.screen_text().split("\n")[0] == "ABCDEFG")
raises("print() starting with a combining mark", ValueError, lambda: z.print("\u0301", pos=(5, 0)), "zero width")
raises("...or one after a newline", ValueError, lambda: z.print("a\n\u0301b", pos=(5, 0)))
raises("...or after a tab", ValueError, lambda: z.print("a\t\u0301"))
z.print("AB\u200dCD", pos=(7, 1))
test("a zero-width codepoint after a base takes no column when clipping", z.screen_text().split("\n")[1] == "       AB\u200dC",
     repr(z.screen_text().split("\n")[1]))
z.print("e\u0301", pos=(0, 1))
test("a combining mark after its base is kept", z.screen_text().split("\n")[1].startswith("e\u0301"),
     repr(z.screen_text().split("\n")[1]))

# --- apply_* is all-or-nothing --------------------------------------------------------------------
print("=== apply_* atomic ===")
aw = mcrfpy.TerminalLayer(texture=TW, grid_size=(5, 2))
aw.write(b"abcde\r\nfghij")
hm_full = mcrfpy.HeightMap((5, 2))
hm_full.fill(0.5)
raises("apply_threshold with a wide glyph raises up front", ValueError,
       lambda: aw.apply_threshold(hm_full, (0.0, 1.0), TW.index(0x65E5)), "wide")
test("...and prints nothing", aw.screen_text() == "abcde\nfghij", repr(aw.screen_text()))
raises("apply_ranges with a wide glyph", ValueError, lambda: aw.apply_ranges(hm_full, [((0.0, 1.0), TW.index(0x65E5))]))
test("...prints nothing", aw.screen_text() == "abcde\nfghij")

print()
if errors:
    print(f"FAIL: {len(errors)} check(s) failed")
    for e in errors:
        print("  -", e)
    sys.exit(1)
print("PASS")
sys.exit(0)
