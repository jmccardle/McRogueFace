"""#550 TerminalLayer drawing: pixels through a real Grid, blink on the engine clock, the cursor
outside the chunk cache, and dirty tracking (EXPERIMENTAL API).

Every scene is a Grid whose cells are the atlas's cells (1:1), a blue ColorLayer under the
TerminalLayer, and a screenshot read back with tests/regression/_png.py. Chunks composite
premultiplied (#562), so an opaque pixel reads back exactly. Glyph shapes are compared with the
same atlas tile drawn by a plain TileLayer in the same scene, or by coverage relations (bold
faked by a second draw 1 px right covers the regular glyph and its shift).
"""
import atexit
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "regression"))
import _png  # noqa: E402
import mcrfpy  # noqa: E402
from mcrfpy import automation  # noqa: E402

errors = []
TMP = tempfile.mkdtemp(prefix="mcrf550_")
atexit.register(shutil.rmtree, TMP, True)


def test(name, cond, msg=""):
    if cond:
        print(f"  PASS: {name}")
    else:
        errors.append(f"{name} {msg}")
        print(f"  FAIL: {name} {msg}")


FONT = mcrfpy.Font("assets/JetbrainsMono.ttf")
FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "fonts")
BOLD = mcrfpy.Font(os.path.join(FONTS, "DejaVuSansMono-Bold.ttf"))
ITAL = mcrfpy.Font(os.path.join(FONTS, "DejaVuSansMono-Oblique.ttf"))
CPS = [(0x20, 0x7E), (0x2500, 0x259F)]   # ASCII, box drawing, block elements (U+2588 FULL BLOCK)
TEX = mcrfpy.Texture.from_font(FONT, 16, codepoints=CPS)
CW, CH = TEX.sprite_width, TEX.sprite_height
BLUE = (0, 0, 255)
FULL = "█"

_n = [0]


def scene_with(term, cols, rows, extra=()):
    """A scene holding a Grid of cols x rows atlas cells: blue ColorLayer, then `term`, then `extra` layers."""
    _n[0] += 1
    sc = mcrfpy.Scene(f"t550_{_n[0]}")
    bg = mcrfpy.ColorLayer(z_index=-3, name="bg")
    g = mcrfpy.Grid(grid_size=(cols, rows), pos=(0, 0), size=(cols * CW, rows * CH), texture=term.texture,
                    layers=[bg, term, *extra])
    g.center = (cols * CW / 2, rows * CH / 2)
    bg.fill(mcrfpy.Color(*BLUE))
    sc.children.append(g)
    mcrfpy.current_scene = sc
    return g


def shot():
    _n[0] += 1
    path = os.path.join(TMP, f"s{_n[0]}.png")
    mcrfpy.step(0)
    automation.screenshot(path)
    return _png.read_png(path, crop_w=640, crop_h=64)  # every scene is in the top-left 640x64


def px(img, x, y):
    w, h, ch, data = img
    i = (y * w + x) * ch
    return tuple(data[i:i + 3])


def cell_px(img, cx, cy, x, y):
    return px(img, cx * CW + x, cy * CH + y)


def cell_block(img, cx, cy):
    return [[cell_px(img, cx, cy, x, y) for x in range(CW)] for y in range(CH)]


def lit(block, thresh=128):
    """Pixels of a white-on-blue glyph: R is the coverage."""
    return {(x, y) for y, row in enumerate(block) for x, p in enumerate(row) if p[0] >= thresh}


MID = (CW // 2, CH // 2)

# --- colours -------------------------------------------------------------------------------
print("=== colours ===")
t = mcrfpy.TerminalLayer(texture=TEX, grid_size=(12, 3), z_index=-1)
scene_with(t, 12, 3)
t.show_cursor = False
t.write(f"\x1b[38;2;10;200;30m{FULL}\x1b[0m".encode())                          # (0,0) truecolor fg
t.write(f"\x1b[48;2;200;0;0m \x1b[0m".encode())                                 # (1,0) truecolor bg
t.write(f"\x1b[38;5;196m{FULL}\x1b[0m".encode())                                # (2,0) 256-colour fg
t.write(f"\x1b[31m{FULL}\x1b[0m".encode())                                      # (3,0) 16-colour fg
t.write(b"\x1b[7m \x1b[0m")                                                      # (4,0) inverse of defaults
t.write(f"\x1b[38;2;10;200;30;48;2;100;0;0;7m{FULL}\x1b[0m".encode())             # (5,0) inverse of set colours
t.write(f"\x1b[38;2;200;100;50;2m{FULL}\x1b[0m".encode())                        # (6,0) faint
t.write(f"\x1b[8m{FULL}\x1b[0m".encode())                                       # (7,0) invisible
t.write(f"\x1b[48;2;0;90;0;8m{FULL}\x1b[0m".encode())                           # (8,0) invisible keeps its bg
img = shot()
pal = t.palette
test("truecolor fg exact", cell_px(img, 0, 0, *MID) == (10, 200, 30), f"{cell_px(img, 0, 0, *MID)}")
test("truecolor bg fills the cell", cell_px(img, 1, 0, 0, 0) == (200, 0, 0) and cell_px(img, 1, 0, CW - 1, CH - 1) == (200, 0, 0))
test("256-colour fg through the palette", cell_px(img, 2, 0, *MID) == (pal[196].r, pal[196].g, pal[196].b))
test("16-colour fg through the palette", cell_px(img, 3, 0, *MID) == (pal[1].r, pal[1].g, pal[1].b),
     f"{cell_px(img, 3, 0, *MID)} vs {pal[1]}")
test("inverse of the defaults: the default foreground as background", cell_px(img, 4, 0, *MID) == (255, 255, 255),
     f"{cell_px(img, 4, 0, *MID)}")
test("inverse swaps set colours (glyph in the old bg)", cell_px(img, 5, 0, *MID) == (100, 0, 0),
     f"{cell_px(img, 5, 0, *MID)}")
test("faint halves the foreground", cell_px(img, 6, 0, *MID) == (100, 50, 25), f"{cell_px(img, 6, 0, *MID)}")
test("invisible draws no glyph", cell_px(img, 7, 0, *MID) == BLUE, f"{cell_px(img, 7, 0, *MID)}")
test("invisible keeps its background", cell_px(img, 8, 0, *MID) == (0, 90, 0), f"{cell_px(img, 8, 0, *MID)}")
test("default background is transparent (the blue layer shows)", cell_px(img, 11, 2, *MID) == BLUE)
t.background = mcrfpy.Color(10, 20, 30)
img = shot()
test("background=Color draws default-background cells", cell_px(img, 11, 2, *MID) == (10, 20, 30),
     f"{cell_px(img, 11, 2, *MID)}")
test("...explicit backgrounds are unchanged", cell_px(img, 1, 0, 0, 0) == (200, 0, 0))
t.background = None
img = shot()
test("background=None is transparent again", cell_px(img, 11, 2, *MID) == BLUE)

pal = t.palette
pal[1] = mcrfpy.Color(1, 2, 3)
t.palette = pal
t.write(f"\x1b[3;1H\x1b[31m{FULL}\x1b[0m".encode())
img = shot()
test("a palette change recolours palette cells", cell_px(img, 0, 2, *MID) == (1, 2, 3) and
     cell_px(img, 3, 0, *MID) == (1, 2, 3), f"{cell_px(img, 0, 2, *MID)} {cell_px(img, 3, 0, *MID)}")
t.write(b"\x1b[?5h")   # DECSCNM: the whole screen in reverse video
img = shot()
test("DECSCNM: default cells show the default foreground as background", cell_px(img, 11, 2, *MID) == (255, 255, 255),
     f"{cell_px(img, 11, 2, *MID)}")
t.write(b"\x1b[?5l")
img = shot()
test("DECSCNM off: transparent again", cell_px(img, 11, 2, *MID) == BLUE)

# --- lines ---------------------------------------------------------------------------------
print("=== underline / strike / overline ===")
t = mcrfpy.TerminalLayer(texture=TEX, grid_size=(6, 1), z_index=-1)
scene_with(t, 6, 1)
t.show_cursor = False
on = "\x1b[38;2;255;0;0;48;2;0;0;80m"
t.write(f"{on}\x1b[4m \x1b[0m{on}\x1b[4:2m \x1b[0m{on}\x1b[9m \x1b[0m{on}\x1b[53m \x1b[0m{on} \x1b[0m".encode())
img = shot()
UL, ULT = TEX.underline_position, TEX.underline_thickness
ST, STT = TEX.strikethrough_position, TEX.strikethrough_thickness
RED, BG = (255, 0, 0), (0, 0, 80)
col = lambda cx, y: cell_px(img, cx, 0, CW // 2, y)  # noqa: E731
test("underline rows at the stored metrics", all(col(0, UL + k) == RED for k in range(ULT)), f"{[col(0, y) for y in range(CH)]}")
test("underline is only those rows", sum(col(0, y) == RED for y in range(CH)) == ULT)
test("no underline on the plain cell", all(col(4, y) == BG for y in range(CH)))
dbl = [y for y in range(CH) if col(1, y) == RED]
second = UL + 2 * ULT if UL + 3 * ULT <= CH else max(0, UL - 2 * ULT)   # below, or above when no room
test("double underline is two stripes a stripe apart",
     dbl == sorted(set(range(UL, UL + ULT)) | set(range(second, second + ULT))), f"{dbl} (position {UL}, thickness {ULT}, cell {CH})")
test("strike rows at the stored metrics", [y for y in range(CH) if col(2, y) == RED] == list(range(ST, ST + STT)),
     f"{[y for y in range(CH) if col(2, y) == RED]}")
test("overline is the top stripe", [y for y in range(CH) if col(3, y) == RED] == list(range(0, ULT)))

# --- bold and italic -------------------------------------------------------------------------
print("=== bold / italic ===")
ref = mcrfpy.TileLayer(z_index=0, texture=TEX)
t = mcrfpy.TerminalLayer(texture=TEX, grid_size=(6, 2), z_index=-1)
scene_with(t, 6, 2, extra=[ref])
t.show_cursor = False
t.write(b"l\x1b[1ml\x1b[0mH\x1b[3mH\x1b[0m")
ref.fill(-1)
ref.set((0, 1), TEX.index("l"))
img = shot()
regular, ref_l = lit(cell_block(img, 0, 0)), lit(cell_block(img, 0, 1))
test("regular glyph equals the same tile drawn by a TileLayer", regular == ref_l and regular)
fake = lit(cell_block(img, 1, 0))
test("fake bold covers the glyph and its 1 px shift",
     all((x, y) in fake for (x, y) in regular) and all((x + 1, y) in fake for (x, y) in regular if x + 1 < CW),
     f"{len(regular)} vs {len(fake)}")
test("fake bold is wider", len(fake) > len(regular))


def centroid_x(pixels, y0, y1):
    xs = [x for (x, y) in pixels if y0 <= y < y1]
    return sum(xs) / len(xs) if xs else None


up, it_ = lit(cell_block(img, 2, 0)), lit(cell_block(img, 3, 0))
third = CH // 3
lean_regular = centroid_x(up, 0, third + 2) - centroid_x(up, CH - third - 2, CH)
lean_italic = centroid_x(it_, 0, third + 2) - centroid_x(it_, CH - third - 2, CH)
test("fake italic shears the top right", lean_italic > lean_regular + 1.0, f"{lean_regular:.2f} vs {lean_italic:.2f}")

# with bold and italic faces in the atlas, those glyphs are drawn as they are
TBI = mcrfpy.Texture.from_font(FONT, 16, codepoints="lH", bold=BOLD, italic=ITAL)
ref2 = mcrfpy.TileLayer(z_index=0, texture=TBI)
t2 = mcrfpy.TerminalLayer(texture=TBI, grid_size=(4, 2), z_index=-1)
scene_with(t2, 4, 2, extra=[ref2])
t2.show_cursor = False
t2.write(b"\x1b[1ml\x1b[0m\x1b[3mH\x1b[0m")
ref2.fill(-1)
ref2.set((0, 1), TBI.index("l", bold=True))
ref2.set((1, 1), TBI.index("H", italic=True))
img = shot()
test("bold face: the bold tile, drawn once", lit(cell_block(img, 0, 0)) == lit(cell_block(img, 0, 1)))
test("italic face: the italic tile, not sheared", lit(cell_block(img, 1, 0)) == lit(cell_block(img, 1, 1)))

# --- blink -------------------------------------------------------------------------------------
print("=== blink ===")
SMALL = mcrfpy.Texture.from_font(FONT, 6, codepoints=CPS)
CW0, CH0 = CW, CH
CW, CH = SMALL.sprite_width, SMALL.sprite_height
MID = (CW // 2, CH // 2)
t = mcrfpy.TerminalLayer(texture=SMALL, grid_size=(130, 2), z_index=-1)   # three chunks across (64 cells each)
scene_with(t, 130, 2)
t.show_cursor = False
t.write(f"\x1b[5m{FULL}\x1b[0m".encode())  # blinking, in chunk 0
t.write(f"\x1b[1;100H{FULL}".encode())       # steady, in chunk 1
shot()


def clock():
    return mcrfpy.get_metrics()["simulation_time_ms"]


def phase_start(on):
    """Step the engine clock to the start of a blink phase (0.5 s phases)."""
    now = clock()
    target = (now // 500 + 1) * 500
    if ((target // 500) % 2 == 0) != on:
        target += 500
    mcrfpy.step((target - now) / 1000.0)


phase_start(True)
before = t.chunk_repaints
img = shot()
test("blink on: drawn", cell_px(img, 0, 0, *MID) == (255, 255, 255), f"{cell_px(img, 0, 0, *MID)}")
phase_start(False)
img = shot()
test("blink off: hidden", cell_px(img, 0, 0, *MID) == BLUE, f"{cell_px(img, 0, 0, *MID)}")
test("steady cell unaffected", cell_px(img, 99, 0, *MID) == (255, 255, 255))
test("one flip repaints one chunk (the one with the blinking cell)", t.chunk_repaints - before == 1,
     f"{t.chunk_repaints - before}")
before = t.chunk_repaints
mcrfpy.step(0.1)
shot()
test("no flip, no repaint", t.chunk_repaints == before, f"{t.chunk_repaints - before}")
t.blink_interval = None
img = shot()
test("blink_interval None: drawn steady", cell_px(img, 0, 0, *MID) == (255, 255, 255))
phase_start(False)
img = shot()
test("...whatever the clock says", cell_px(img, 0, 0, *MID) == (255, 255, 255))
t.blink_interval = 0.5

# --- dirty tracking -----------------------------------------------------------------------------
print("=== dirty tracking ===")
t.write(b"\x1b[5m\x1b[0m\x1b[2J")   # no blinking cells left
shot()
before = t.chunk_repaints
shot()
test("an idle frame repaints nothing", t.chunk_repaints == before, f"{t.chunk_repaints - before}")
t.write(b"\x1b[1;71HX")
shot()
test("writing one cell repaints one chunk", t.chunk_repaints - before == 1, f"{t.chunk_repaints - before}")
before = t.chunk_repaints
t.write(b"\x1b[2;3H")   # cursor only
shot()
test("moving the cursor repaints no chunk", t.chunk_repaints == before, f"{t.chunk_repaints - before}")
t.write(b"\x1b[1;71HX")  # the same character again: no change
shot()
test("rewriting identical content repaints nothing", t.chunk_repaints == before, f"{t.chunk_repaints - before}")

# A synchronized-output hold the program never ends: the clock ends it and the view redraws,
# with nothing written and nothing read in between.
t.write(b"\x1b[2J\x1b[H\x1b[5m\x1b[0m")
t.write(f"\x1b[?2026h{FULL}".encode())
img = shot()
test("held frame shown", cell_px(img, 0, 0, *MID) == BLUE, f"{cell_px(img, 0, 0, *MID)}")
mcrfpy.step(1.1)
img = shot()
test("hold ended by the engine clock, frame redrawn", cell_px(img, 0, 0, *MID) == (255, 255, 255),
     f"{cell_px(img, 0, 0, *MID)}")

# --- cursor ---------------------------------------------------------------------------------------
print("=== cursor ===")
CW, CH = CW0, CH0
MID = (CW // 2, CH // 2)
t = mcrfpy.TerminalLayer(texture=TEX, grid_size=(6, 2), z_index=-1)
scene_with(t, 6, 2)
t.blink_interval = None
t.write(b"ab")
img = shot()
test("block cursor is drawn in the default foreground", cell_px(img, 2, 0, *MID) == (255, 255, 255), f"{cell_px(img, 2, 0, *MID)}")
before = t.chunk_repaints
t.write(b"\x1b[1;1H")
img = shot()
test("cursor moved: drawn at the new cell", cell_px(img, 2, 0, *MID) == BLUE and cell_px(img, 0, 0, 0, 0) == (255, 255, 255))
test("block cursor redraws the glyph in the background colour", any(cell_px(img, 0, 0, x, y)[0] < 128
                                                                   for y in range(CH) for x in range(CW)))
test("cursor changes repaint no chunk", t.chunk_repaints == before, f"{t.chunk_repaints - before}")
t.write(b"\x1b[6 q\x1b[2;3H")
img = shot()
test("bar cursor: left column only", cell_px(img, 2, 1, 0, MID[1]) == (255, 255, 255) and cell_px(img, 2, 1, CW - 1, MID[1]) == BLUE)
t.write(b"\x1b[4 q")
img = shot()
test("underline cursor: bottom row only", cell_px(img, 2, 1, MID[0], CH - 1) == (255, 255, 255) and cell_px(img, 2, 1, *MID) == BLUE)
t.write(b"\x1b[?25l")
img = shot()
test("hidden by the program (DECTCEM)", cell_px(img, 2, 1, MID[0], CH - 1) == BLUE)
t.write(b"\x1b[?25h")
t.show_cursor = False
img = shot()
test("hidden by show_cursor", cell_px(img, 2, 1, MID[0], CH - 1) == BLUE)
test("still no chunk repaints", t.chunk_repaints == before, f"{t.chunk_repaints - before}")
t.show_cursor = True
t.blink_interval = 0.5
t.write(b"\x1b[2 q\x1b[?12h")   # steady block, then blinking on
phase_start(True)
img = shot()
on_px = cell_px(img, 2, 1, *MID)
phase_start(False)
img = shot()
off_px = cell_px(img, 2, 1, *MID)
test("a blinking cursor follows the blink phase", on_px == (255, 255, 255) and off_px == BLUE, f"{on_px} {off_px}")
test("...without repainting chunks", t.chunk_repaints == before, f"{t.chunk_repaints - before}")

# --- the cursor over a cell whose stored tile is not in a smaller, swapped-in atlas ---------------
print("=== texture swap under the cursor ===")
t = mcrfpy.TerminalLayer(texture=TEX, grid_size=(6, 2), z_index=-1)
scene_with(t, 6, 2)
t.blink_interval = None
t.write(b"}~\x1b[H")
shot()
tiny = mcrfpy.Texture.from_font(FONT, 16, codepoints="}~")
mcrfpy.TileLayer.texture.__set__(t, tiny)   # the unbound base setter: dispatched to the terminal's
img = shot()
test("the block cursor over a re-mapped cell draws (no stale index read)", cell_px(img, 0, 0, 0, 0) == (255, 255, 255),
     f"{cell_px(img, 0, 0, 0, 0)}")
test("cells re-mapped to the new atlas", t.at(0, 0) == tiny.index("}") and t.at(1, 0) == tiny.index("~"))

print()
if errors:
    print(f"FAIL: {len(errors)} check(s) failed")
    for e in errors:
        print("  -", e)
    sys.exit(1)
print("PASS")
sys.exit(0)
