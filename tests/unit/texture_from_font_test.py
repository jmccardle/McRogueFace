"""#547 Texture.from_font: a static glyph atlas with codepoint <-> tile lookup (EXPERIMENTAL API).

Pixels are checked by drawing tiles through a real TileLayer at 1:1 over a blue background and
reading the screenshot. White over blue gives R == G with B == 255 (#562: the chunk blend is
premultiplied, so a partial-alpha pixel keeps B at 255), and a transparent pixel reads exactly the
background (0, 0, 255). How R relates to the glyph's alpha is not pinned to an exact curve; checks use
R == G, B == 255, R == 0, R == 255 and "R takes several distinct values". The test fonts are vendored in
tests/assets/fonts/ and the test fails, not skips, if one is missing.
"""
import os
import struct
import sys
import zlib

import mcrfpy
from mcrfpy import automation

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
        ok = needle is None or needle in str(e)
        test(name, ok, f"message {e!r} lacks {needle!r}")
    except Exception as e:  # wrong type
        test(name, False, f"raised {type(e).__name__}: {e}")
    else:
        test(name, False, "did not raise")


# --- screenshot reading -------------------------------------------------------------------
def read_png(path):
    d = open(path, "rb").read()
    p, idat = 8, b""
    while p < len(d):
        n, = struct.unpack(">I", d[p:p + 4])
        typ, body = d[p + 4:p + 8], d[p + 8:p + 8 + n]
        p += 12 + n
        if typ == b"IHDR":
            w, h, _bd, ct = struct.unpack(">IIBB", body[:10])
        elif typ == b"IDAT":
            idat += body
    bpp = {2: 3, 6: 4}[ct]
    raw, stride, rows, prev, q = zlib.decompress(idat), w * bpp, [], bytearray(w * bpp), 0
    for _ in range(h):
        ft, line = raw[q], bytearray(raw[q + 1:q + 1 + w * bpp])
        q += 1 + stride
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if ft == 1: line[i] = (line[i] + a) & 255
            elif ft == 2: line[i] = (line[i] + b) & 255
            elif ft == 3: line[i] = (line[i] + ((a + b) >> 1)) & 255
            elif ft == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else (b if pb <= pc else c))) & 255
        rows.append(line)
        prev = line
    return w, h, bpp, rows


_shot = [0]
BAD_PIXELS = []


def render(tex, tiles, cols=8, rows=2):
    """Draw {(cx, cy): tile} through a TileLayer; returns {(cx, cy): [row of red values per pixel row]}."""
    cw, ch = tex.sprite_width, tex.sprite_height
    scene = mcrfpy.Scene(f"s547_{_shot[0]}")
    bg = mcrfpy.ColorLayer(z_index=-2, name="bg")
    tl = mcrfpy.TileLayer(z_index=-1, name="t", texture=tex)
    g = mcrfpy.Grid(grid_size=(cols, rows), pos=(0, 0), size=(cols * cw, rows * ch),
                    center_x=cols * cw / 2, center_y=rows * ch / 2, texture=tex, layers=[bg, tl])
    bg.fill(mcrfpy.Color(0, 0, 255))
    tl.fill(-1)
    for pos, idx in tiles.items():
        tl.set(pos, idx)
    scene.children.append(g)
    mcrfpy.current_scene = scene
    mcrfpy.step(0.1)
    path = f"test_547_{_shot[0]}.png"
    _shot[0] += 1
    automation.screenshot(path)
    _w, _h, bpp, px = read_png(path)
    out = {}
    for (cx, cy) in tiles:
        out[(cx, cy)] = [[px[cy * ch + y][(cx * cw + x) * bpp] for x in range(cw)] for y in range(ch)]
        # a white pixel of alpha a over blue has R == G and B == 255 (#562: premultiplied blend);
        # a transparent pixel is exactly (0, 0, 255). Anything else means the glyph pixel was not white
        for y in range(ch):
            for x in range(cw):
                r_, g_, b_ = (px[cy * ch + y][(cx * cw + x) * bpp + k] for k in range(3))
                if abs(r_ - g_) > 1 or b_ != 255:
                    BAD_PIXELS.append((cx, cy, x, y, r_, g_, b_))
    return out


def flat(t):
    return [v for row in t for v in row]


FONT = mcrfpy.Font("assets/JetbrainsMono.ttf")
SIZE = 16

# --- layout and defaults ------------------------------------------------------------------
print("=== layout ===")
tex = mcrfpy.Texture.from_font(FONT, SIZE)
test("returns a Texture", isinstance(tex, mcrfpy.Texture))
test("box tile is 0", tex.box_tile == 0)
test("white tile is 1", tex.white_tile == 1)
n_default = (0x7E - 0x20 + 1) + (0x257F - 0x2500 + 1)
test("tile 0, white tile, then the glyphs", tex.sprite_count >= n_default + 2,
     f"sprite_count {tex.sprite_count}")
test("nothing missing from JetBrains Mono's defaults", tex.missing == [], f"{tex.missing}")
fm = FONT.metrics(SIZE)
test("default cell height is the line height", tex.sprite_height == -(-int(fm[2] * 64) // 64) or
     abs(tex.sprite_height - fm[2]) < 1.0, f"{tex.sprite_height} vs {fm}")
test("monospace: cell width is the advance", 8 <= tex.sprite_width <= 12, f"{tex.sprite_width}")
test("variants are regular only", tex.variants == ("regular",), f"{tex.variants}")
test("space is the first glyph tile", tex.index(" ") == 2, f"{tex.index(' ')}")
test("glyph tiles are ascending in codepoint order",
     tex.index("A") == tex.index(" ") + (ord("A") - 0x20), f"{tex.index('A')}")
test("str and int agree", tex.index("A") == tex.index(65))
test("box-drawing range is present", tex.index(0x2500) not in (0,) and tex.index("╔") != 0)

print("=== codepoints spelling ===")
t2 = mcrfpy.Texture.from_font(FONT, SIZE, codepoints="AB")
test("str codepoints", t2.index("A") == 2 and t2.index("B") == 3 and t2.index("C") == 0)
t3 = mcrfpy.Texture.from_font(FONT, SIZE, codepoints=[(0x41, 0x43), 0x5A, "z"])
test("ranges, ints and chars mix", [t3.index(c) for c in "ABCZz"] == [2, 3, 4, 5, 6],
     f"{[t3.index(c) for c in 'ABCZz']}")
test("sprite_count covers tiles", t3.sprite_count >= 7)
test("duplicates collapse", mcrfpy.Texture.from_font(FONT, SIZE, codepoints=[0x41, 0x41, (0x41, 0x41)]).index("A") == 2)
test("a generator works", mcrfpy.Texture.from_font(FONT, SIZE, codepoints=(c for c in (65, 66))).index("B") == 3)

print("=== missing / clipped ===")
tm = mcrfpy.Texture.from_font(FONT, SIZE, codepoints=[(0x41, 0x43), 0x10FFFE])
test("codepoint absent from the font is in missing", tm.missing == [0x10FFFE], f"{tm.missing}")
test("index of a missing codepoint is the box tile", tm.index(0x10FFFE) == 0)
test("index of a codepoint never requested is the box tile", tm.index("Z") == 0)
test("present codepoints are not missing", 0x41 not in tm.missing)
tc = mcrfpy.Texture.from_font(FONT, SIZE, codepoints="AW", cell=(3, 4))
test("a glyph larger than the cell is clipped and listed", tc.clipped == [0x41, 0x57], f"{tc.clipped}")
test("explicit cell sets the tile size", (tc.sprite_width, tc.sprite_height) == (3, 4))
test("normal glyphs are not clipped", tex.clipped is not None and 0x41 not in tex.clipped and 0x20 not in tex.clipped)
tbig = mcrfpy.Texture.from_font(FONT, SIZE, codepoints="A", cell=(30, 40))
test("a roomy explicit cell clips nothing", tbig.clipped == [])

print("=== pixels ===")
r = render(tex, {(0, 0): tex.box_tile, (1, 0): tex.white_tile, (2, 0): tex.index("A"),
                 (3, 0): tex.index(" "), (4, 0): tex.index("W")})
box, white, glyph, space = flat(r[(0, 0)]), flat(r[(1, 0)]), flat(r[(2, 0)]), flat(r[(3, 0)])
test("box tile is non-empty", any(v > 0 for v in box))
test("box tile is an outline, not solid", any(v == 0 for v in box) and sum(1 for v in box if v > 250) < len(box) * 0.7)
test("white tile is fully white and opaque", all(v == 255 for v in white), f"min {min(white)}")
test("glyph tile has white pixels", any(v > 200 for v in glyph))
alphas = {v for v in glyph if v > 0}
test("glyph tile has varying (anti-aliased) alpha", len(alphas) > 3, f"{len(alphas)} levels")
test("glyph tile is transparent elsewhere", sum(1 for v in glyph if v == 0) > len(glyph) // 2)
test("the space tile is fully transparent", all(v == 0 for v in space))
# 'A' is left-right symmetric-ish and sits above the baseline: bottom rows below the baseline are empty
rowsA = r[(2, 0)]
test("A sits on the baseline (rows below it are transparent)",
     all(v == 0 for row in rowsA[tex.ascent + 1:] for v in row))
test("A reaches above the cell middle", any(v > 200 for v in rowsA[tex.ascent // 2]) or
     any(v > 200 for row in rowsA[:tex.ascent // 2] for v in row))

print("=== line metrics ===")
test("ascent within the cell", 0 < tex.ascent < tex.sprite_height, f"{tex.ascent}")
test("ascent matches the font's", abs(tex.ascent - fm[0]) <= 1.0, f"{tex.ascent} vs {fm[0]}")
for nm in ("underline", "strikethrough"):
    pos, th = getattr(tex, nm + "_position"), getattr(tex, nm + "_thickness")
    test(f"{nm} thickness >= 1", th >= 1, f"{th}")
    test(f"{nm} lies in the cell", 0 <= pos and pos + th <= tex.sprite_height, f"{pos}+{th}")
test("underline is below the baseline", tex.underline_position >= tex.ascent - 1, f"{tex.underline_position}")
test("strike-through is above the baseline", tex.strikethrough_position < tex.ascent)

print("=== stripes stay inside the cell ===")
for label, kw, sz in (("size 6", {}, 6), ("cell (10, 10) at size 16", {"cell": (10, 10)}, 16),
                      ("cell (10, 3) at size 16", {"cell": (10, 3)}, 16), ("cell (3, 1)", {"cell": (3, 1)}, 16)):
    ts = mcrfpy.Texture.from_font(FONT, sz, codepoints="A", **kw)
    for nm in ("underline", "strikethrough"):
        pos, th = getattr(ts, nm + "_position"), getattr(ts, nm + "_thickness")
        test(f"{label}: {nm} {pos}+{th} inside a {ts.sprite_height} px cell",
             pos >= 0 and 1 <= th <= ts.sprite_height and pos + th <= ts.sprite_height)
ts6 = mcrfpy.Texture.from_font(FONT, 6, codepoints="A")
test("size 6 gives the small cell the review reported", (ts6.sprite_width, ts6.sprite_height) == (4, 7), f"{ts6.sprite_width}x{ts6.sprite_height}")
test("ascent stays the font's even when the cell is shorter",
     mcrfpy.Texture.from_font(FONT, 16, codepoints="A", cell=(10, 3)).ascent > 3)

print("=== variants ===")
BOLD_PATH = "../tests/assets/fonts/DejaVuSansMono-Bold.ttf"
ITAL_PATH = "../tests/assets/fonts/DejaVuSansMono-Oblique.ttf"
WIDE_PATH = "../tests/assets/fonts/DroidSansFallback-subset.ttf"
for fp in (BOLD_PATH, ITAL_PATH, WIDE_PATH):
    test(f"vendored test font exists: {fp}", os.path.exists(fp))
BOLD, ITAL, WIDE = mcrfpy.Font(BOLD_PATH), mcrfpy.Font(ITAL_PATH), mcrfpy.Font(WIDE_PATH)
tb = mcrfpy.Texture.from_font(FONT, SIZE, codepoints="AB", bold=BOLD)
test("variants lists bold", tb.variants == ("regular", "bold"), f"{tb.variants}")
test("bold tile differs from regular", tb.index("A", bold=True) not in (0, tb.index("A")), f"{tb.index('A', bold=True)}")
test("bold=False is the regular tile", tb.index("A", bold=False) == tb.index("A"))
test("regular tiles come first, bold glyphs follow",
     tb.index("A") == 2 and tb.index("B") == 3 and tb.index("A", bold=True) == 4 and tb.index("B", bold=True) == 5)
test("italic with no italic face gives the regular tile (layer fakes it)",
     tb.index("A", italic=True) == tb.index("A"))
tn = mcrfpy.Texture.from_font(FONT, SIZE, codepoints="AB")
test("bold with no bold face gives the regular tile (layer double-draws)",
     tn.index("A", bold=True) == tn.index("A") != 0 and "bold" not in tn.variants)
ti = mcrfpy.Texture.from_font(FONT, SIZE, codepoints="AB", bold=BOLD, italic=ITAL)
test("both faces", ti.variants == ("regular", "bold", "italic"))
test("italic tile is its own", len({ti.index("A"), ti.index("A", bold=True), ti.index("A", italic=True)}) == 3)
test("bold+italic is the bold tile (no bold-italic face)", ti.index("A", bold=True, italic=True) == ti.index("A", bold=True))
test("only-italic: bold falls back to regular, italic found",
     mcrfpy.Texture.from_font(FONT, SIZE, codepoints="A", italic=ITAL).index("A", bold=True, italic=True) ==
     mcrfpy.Texture.from_font(FONT, SIZE, codepoints="A", italic=ITAL).index("A", italic=True))
rb = render(tb, {(0, 0): tb.index("A"), (1, 0): tb.index("A", bold=True)})
test("bold glyph pixels exist", any(v > 200 for v in flat(rb[(1, 0)])))
test("bold glyph is not the regular glyph", flat(rb[(0, 0)]) != flat(rb[(1, 0)]))
# A face that has a codepoint the other lacks, both ways round: JetBrains Mono has Latin and no CJK,
# the Droid subset has CJK and no Latin.
tvm = mcrfpy.Texture.from_font(FONT, SIZE, codepoints=[0x41, 0x4E2D], bold=WIDE)
test("regular lacks the CJK codepoint", tvm.missing == [0x4E2D], f"{tvm.missing}")
test("bold lacks the Latin codepoint", tvm.variant_missing == [(0x41, True, False)], f"{tvm.variant_missing}")
test("bold requested, bold face lacks it, regular has it: the regular tile",
     tvm.index("A", bold=True) == tvm.index("A") != 0, f"{tvm.index('A', bold=True)} vs {tvm.index('A')}")
test("...and glyph() says that tile is the regular face", tvm.glyph(tvm.index("A", bold=True)) == (0x41, False, False))
test("bold requested, only the bold face has it: the bold tile",
     tvm.index(0x4E2D, bold=True) != 0 and tvm.glyph(tvm.index(0x4E2D, bold=True)) == (0x4E2D, True, False))
test("regular lookup of a codepoint only the bold face has is the box", tvm.index(0x4E2D) == 0)
test("a codepoint no face has is the box, bold or not", tvm.index(0x10FFFE, bold=True) == 0 and tvm.index(0x10FFFE) == 0)
tim = mcrfpy.Texture.from_font(FONT, SIZE, codepoints=[0x41, 0x4E2D], italic=WIDE)
test("italic face lacking a codepoint falls back to the regular tile too",
     tim.index("A", italic=True) == tim.index("A") != 0 and tim.variant_missing == [(0x41, False, True)])
test("bold+italic walks bold, italic, regular", tim.index("A", bold=True, italic=True) == tim.index("A") and
     tim.index(0x4E2D, bold=True, italic=True) == tim.index(0x4E2D, italic=True) != 0)

# A cell too small for the glyphs: clipped is regular face only, variant_clipped the others.
tvc = mcrfpy.Texture.from_font(FONT, SIZE, codepoints="AW", cell=(9, 16), bold=BOLD)
test("regular clipping is reported for the wide letter only", tvc.clipped == [0x57], f"{tvc.clipped}")
test("the bold face overflows on both, and its entries are not in clipped",
     tvc.variant_clipped == [(0x41, True, False), (0x57, True, False)], f"{tvc.variant_clipped}")
test("variant_missing is empty when the bold face has everything", tvc.variant_missing == [])

print("=== reverse lookup ===")
test("glyph(tile) round-trips", tex.glyph(tex.index("A")) == (65, False, False), f"{tex.glyph(tex.index('A'))}")
test("glyph() names the face", ti.glyph(ti.index("A", bold=True)) == (65, True, False) and
     ti.glyph(ti.index("A", italic=True)) == (65, False, True))
test("box tile has no codepoint", tex.glyph(0) is None)
test("white tile has no codepoint", tex.glyph(tex.white_tile) is None)
bad = tex.sprite_count + 5
raises("glyph() out of range raises IndexError", IndexError, lambda: tex.glyph(bad))
raises("glyph() negative raises IndexError", IndexError, lambda: tex.glyph(-1))
ok = all(tex.glyph(tex.index(c))[0] == ord(c) for c in map(chr, range(0x20, 0x7F)))
test("every ASCII tile round-trips", ok)

print("=== wide glyphs ===")
tw = mcrfpy.Texture.from_font(WIDE, 16, codepoints=[0x20, 0x4E2D, 0x6587], cell=(10, 20))
test("nothing missing from the wide subset", tw.missing == [], f"{tw.missing}")
test("space is one tile", tw.index(" ") == 2)
left = tw.index(0x4E2D)
test("the wide glyph's left half follows the space", left == 3, f"{left}")
test("a wide glyph takes two adjacent tiles", tw.index(0x6587) == left + 2, f"{left} {tw.index(0x6587)}")
test("right half has no codepoint of its own", tw.glyph(left + 1) is None)
test("left half maps back", tw.glyph(left) == (0x4E2D, False, False))
rw = render(tw, {(0, 0): left, (1, 0): left + 1})
test("both halves have pixels", any(v > 0 for v in flat(rw[(0, 0)])) and any(v > 0 for v in flat(rw[(1, 0)])))
test("the halves differ", flat(rw[(0, 0)]) != flat(rw[(1, 0)]))
test("a wide glyph is not clipped by two cells", 0x4E2D not in tw.clipped, f"{tw.clipped}")
tw1 = mcrfpy.Texture.from_font(WIDE, 16, codepoints=[0x4E2D, 0x6587, 0x672C, 0x65E5])
test("default cell width of an all-wide set is half the advance", tw1.sprite_width * 2 >= 16 and tw1.sprite_width <= 10,
     f"{tw1.sprite_width}")

print("=== is_wide (Unicode East Asian Width, codepoint only) ===")
for cp in (0x1F680, 0x231A, 0x4E2D, 0xFF21, 0x3000):
    test(f"U+{cp:04X} is wide", tex.is_wide(cp) is True and tw.is_wide(cp) is True)
for cp in ("A", 0x2500, 0x20, 0xFF61):
    test(f"U+{ord(cp) if isinstance(cp, str) else cp:04X} is narrow", tex.is_wide(cp) is False)
test("the answer does not depend on the texture having the glyph",
     tex.is_wide(0x4E2D) is True and tex.index(0x4E2D) == 0 and tw.is_wide("A") is False)

print("=== errors ===")
raises("bare (a, b) tuple is ambiguous", TypeError, lambda: mcrfpy.Texture.from_font(FONT, 16, codepoints=(0x20, 0x7E)), "[(a, b)]")
raises("...and says how to write two codepoints", TypeError, lambda: mcrfpy.Texture.from_font(FONT, 16, codepoints=(0x20, 0x7E)), "[a, b]")
test("[(a, b)] is a range, [a, b] is two codepoints",
     mcrfpy.Texture.from_font(FONT, 16, codepoints=[(0x41, 0x43)]).index("B") != 0 and
     mcrfpy.Texture.from_font(FONT, 16, codepoints=[0x41, 0x43]).index("B") == 0)
raises("bool codepoint", TypeError, lambda: mcrfpy.Texture.from_font(FONT, 16, codepoints=[True]), "bool")
raises("bool in a range", TypeError, lambda: mcrfpy.Texture.from_font(FONT, 16, codepoints=[(False, 0x41)]), "bool")
raises("index of a bool", TypeError, lambda: tex.index(True), "bool")
raises("bool cell", TypeError, lambda: mcrfpy.Texture.from_font(FONT, 16, cell=(True, 5)), "cell")
raises("cell integer overflow", ValueError, lambda: mcrfpy.Texture.from_font(FONT, 16, cell=(2 ** 70, 5)), "1024")
raises("cell negative overflow", ValueError, lambda: mcrfpy.Texture.from_font(FONT, 16, cell=(5, -2 ** 70)), "1024")
raises("nothing in any face (bold given)", ValueError,
       lambda: mcrfpy.Texture.from_font(FONT, 16, codepoints=[0x4E2D], bold=FONT), "any of the fonts")
raises("nothing in any face (bold and italic given)", ValueError,
       lambda: mcrfpy.Texture.from_font(FONT, 16, codepoints=[0x4E2D, 0x10FFFE], bold=FONT, italic=BOLD), "any of the fonts")
test("a codepoint only a variant face has is accepted",
     mcrfpy.Texture.from_font(FONT, 16, codepoints=[0x4E2D], bold=WIDE, cell=(10, 20)).index(0x4E2D, bold=True) != 0)
raises("size 0", ValueError, lambda: mcrfpy.Texture.from_font(FONT, 0), "size")
raises("size negative", ValueError, lambda: mcrfpy.Texture.from_font(FONT, -4), "size")
raises("size absurd", ValueError, lambda: mcrfpy.Texture.from_font(FONT, 100000), "size")
raises("font not a Font", TypeError, lambda: mcrfpy.Texture.from_font("assets/JetbrainsMono.ttf", 16), "Font")
raises("bold not a Font", TypeError, lambda: mcrfpy.Texture.from_font(FONT, 16, bold="x"), "bold")
raises("codepoints not iterable", TypeError, lambda: mcrfpy.Texture.from_font(FONT, 16, codepoints=5), "codepoints")
raises("range backwards", ValueError, lambda: mcrfpy.Texture.from_font(FONT, 16, codepoints=[(0x7E, 0x20)]), "backwards")
raises("range of three", ValueError, lambda: mcrfpy.Texture.from_font(FONT, 16, codepoints=[(1, 2, 3)]), "pair")
raises("multi-char str item", ValueError, lambda: mcrfpy.Texture.from_font(FONT, 16, codepoints=["ab"]), "single character")
raises("codepoint out of Unicode", ValueError, lambda: mcrfpy.Texture.from_font(FONT, 16, codepoints=[0x110000]), "outside")
raises("negative codepoint", ValueError, lambda: mcrfpy.Texture.from_font(FONT, 16, codepoints=[-1]), "outside")
raises("surrogate", ValueError, lambda: mcrfpy.Texture.from_font(FONT, 16, codepoints=[0xD800]), "surrogate")
raises("float codepoint", TypeError, lambda: mcrfpy.Texture.from_font(FONT, 16, codepoints=[1.5]), "codepoint")
raises("empty codepoints", ValueError, lambda: mcrfpy.Texture.from_font(FONT, 16, codepoints=[]), "empty")
raises("nothing in the font", ValueError, lambda: mcrfpy.Texture.from_font(FONT, 16, codepoints=[0x10FFFE]), "none of the requested")
raises("cell not a pair", TypeError, lambda: mcrfpy.Texture.from_font(FONT, 16, cell=12), "cell")
raises("cell zero", ValueError, lambda: mcrfpy.Texture.from_font(FONT, 16, cell=(0, 10)), "cell")
raises("index of a multi-char str", ValueError, lambda: tex.index("ab"), "single character")
raises("index of a float", TypeError, lambda: tex.index(1.5), "codepoint")
raises("atlas too big", ValueError, lambda: mcrfpy.Texture.from_font(FONT, 2048, codepoints=[(0x20, 0xFFFF)]), "fit")
plain = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
raises("index on a non-font texture", ValueError, lambda: plain.index("A"), "from_font")
raises("glyph on a non-font texture", ValueError, lambda: plain.glyph(0), "from_font")
test("font properties are None on a non-font texture",
     plain.missing is None and plain.clipped is None and plain.white_tile is None and plain.ascent is None)

test("every drawn pixel was white-over-blue (glyphs are white on transparent)", not BAD_PIXELS, f"{BAD_PIXELS[:3]}")

print("=== a TileLayer draws it ===")
word = "Hello"
tiles = {(i, 0): tex.index(c) for i, c in enumerate(word)}
tiles[(6, 0)] = tex.index("☃")  # a codepoint not in the atlas -> the box
tiles[(7, 0)] = tex.white_tile
rr = render(tex, tiles)
for i, c in enumerate(word):
    test(f"'{c}' tile drew pixels", any(v > 0 for v in flat(rr[(i, 0)])))
test("the 'H' and 'e' tiles differ", flat(rr[(0, 0)]) != flat(rr[(1, 0)]))
test("'l' repeated draws identically", flat(rr[(2, 0)]) == flat(rr[(3, 0)]))
test("unknown codepoint drew the box", flat(rr[(6, 0)]) == box)
test("white tile drew solid white", all(v == 255 for v in flat(rr[(7, 0)])))
print(f"  screenshot: test_547_{_shot[0] - 1}.png")

print()
if errors:
    print(f"FAIL: {len(errors)} failure(s)")
    for e in errors:
        print("  -", e)
    sys.exit(1)
print("PASS")
sys.exit(0)
