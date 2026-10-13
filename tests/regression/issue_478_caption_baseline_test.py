"""Regression test for #478 - where a Caption's text sits relative to its pos.

Before #478 the first baseline sat at pos.y + font_size (SFML's rule), so a Caption
placed at a grid cell's top-left drew (em - ascent) px too low, by a different amount
for every font. Caption.baseline (mcrfpy.TextBaseline) now says which line sits at pos.y:

  TOP       baseline at pos.y + the font's ascent (the default)
  BASELINE  baseline at pos.y
  EM_TOP    baseline at pos.y + font_size (the old placement; pixel-exact against a
            pre-change capture in issue_478_em_top_reference_test.py)

Ground truth is the screenshot. The fonts are generated (_synthetic_font.py): one glyph,
a solid rectangle, with ascents of 0.8 and 0.6 em, so every expected pixel row is a
whole number taken straight from the font's design units, independent of hinting and
antialiasing. Each case is checked at zoom 1 and 2.
"""
import os
import sys
import tempfile

import mcrfpy
from mcrfpy import automation

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # --exec does not put the script's directory on sys.path
import _png  # noqa: E402
import _synthetic_font  # noqa: E402

TMPDIR = tempfile.mkdtemp(prefix="mcrf478_")
failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


UPEM = 1000
EM = 20          # px at zoom 1: 50 font units per pixel, so every metric below is whole
ADVANCE = 600    # 12 px: the cell is 12 x 20 (ascent + descent = 1000 units for both fonts)
CELL = (12, 20)
FONTS = {
    # name: ascender, descender, box (x0, y0, x1, y1) in font units; the box sits on the baseline
    "tall":  (800, -200, (100, 0, 500, 700)),   # ascent 16 px, ink 14 px tall
    "short": (600, -400, (100, 0, 500, 500)),   # ascent 12 px, ink 10 px tall
}
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)


def px(units, zoom):
    return units * EM * zoom // UPEM


fonts = {}
for name, (asc, desc, box) in FONTS.items():
    path = _synthetic_font.write(os.path.join(TMPDIR, name + ".ttf"), units_per_em=UPEM,
                                 ascender=asc, descender=desc, box=box, advance=ADVANCE)
    fonts[name] = mcrfpy.Font(path)


def tile_texture(name):
    """One 12x20 tile: the glyph drawn the way a terminal cell holds it, its top
    (ascent - ink top) px below the cell top: what TOP must reproduce."""
    asc, _desc, (x0, y0, x1, y1) = FONTS[name]
    w, h = CELL
    data = bytearray(w * h * 4)
    top = px(asc - y1, 1)
    bottom = px(asc - y0, 1)
    for y in range(top, bottom):
        for x in range(px(x0, 1), px(x1, 1)):
            data[(y * w + x) * 4:(y * w + x) * 4 + 4] = bytes((255, 255, 255, 255))
    return mcrfpy.Texture.from_bytes(bytes(data), w, h, w, h)


def shot(name):
    path = os.path.join(TMPDIR, name + ".png")
    automation.screenshot(path)
    return _png.read_png(path)


GX, GY = 40, 40

print("1. TOP: a Caption at a grid cell's top-left draws exactly over the cell's tile glyph")
for zoom in (1, 2):
    for name in FONTS:
        scene = mcrfpy.Scene("t478_%s_%d" % (name, zoom))
        mcrfpy.current_scene = scene
        tex = tile_texture(name)
        gw, gh = 4 * CELL[0] * zoom, 3 * CELL[1] * zoom
        grid = mcrfpy.Grid(grid_size=(4, 3), pos=(GX, GY), size=(gw, gh), texture=tex)
        grid.fill_color = mcrfpy.Color(0, 0, 0)
        for layer in list(grid.layers):
            grid.remove_layer(layer)
        tiles = mcrfpy.TileLayer(name="glyphs", z_index=-1, texture=tex)
        grid.add_layer(tiles)
        for x in range(4):
            for y in range(3):
                tiles.set((x, y), -1)
        tiles.set((1, 1), 0)
        grid.zoom = zoom
        grid.center = (gw / 2.0 / zoom, gh / 2.0 / zoom)  # camera top-left at world (0, 0)
        scene.children.append(grid)
        # The caption goes on cell (2, 1), in screen space, over the grid.
        cx, cy = GX + 2 * CELL[0] * zoom, GY + 1 * CELL[1] * zoom
        cap = mcrfpy.Caption(text="X", pos=(cx, cy), font=fonts[name], font_size=EM * zoom,
                             fill_color=YELLOW)
        scene.children.append(cap)
        img = shot("top_%s_%d" % (name, zoom))
        tile_ink = _png.mask(img, WHITE, (GX, GY, GX + gw, GY + gh))
        cap_ink = {(x - CELL[0] * zoom, y) for x, y in _png.mask(img, YELLOW)}
        check(len(tile_ink) > 0, "%s zoom %d: tile glyph drawn (%d px)" % (name, zoom, len(tile_ink)))
        check(cap_ink == tile_ink,
              "%s zoom %d: caption ink == tile ink one cell left (caption bbox %s, tile bbox %s)"
              % (name, zoom, _png.bbox({(x + CELL[0] * zoom, y) for x, y in cap_ink}),
                 _png.bbox(tile_ink)))
        asc, _d, (x0, y0, x1, y1) = FONTS[name]
        b = cap.bounds
        check((b[0].y, b[1].y) == (cy + px(asc - y1, zoom), px(y1 - y0, zoom)),
              "%s zoom %d: bounds top/height follow the ink: %s" % (name, zoom, b))

print("2. Ink rows per mode, for two fonts of different ascent")
Y = 60
for zoom in (1, 2):
    for mode in ("TOP", "BASELINE", "EM_TOP"):
        scene = mcrfpy.Scene("m478_%s_%d" % (mode, zoom))
        mcrfpy.current_scene = scene
        colors = {"tall": (255, 0, 0), "short": (0, 255, 0)}
        caps = {}
        for i, name in enumerate(FONTS):
            caps[name] = mcrfpy.Caption(text="X", pos=(20 + 60 * i * zoom, Y), font=fonts[name],
                                        font_size=EM * zoom, fill_color=colors[name],
                                        baseline=getattr(mcrfpy.TextBaseline, mode))
            scene.children.append(caps[name])
        img = shot("mode_%s_%d" % (mode, zoom))
        baselines = []
        for name in FONTS:
            asc, _d, (x0, y0, x1, y1) = FONTS[name]
            base = {"TOP": Y + px(asc, zoom), "BASELINE": Y, "EM_TOP": Y + EM * zoom}[mode]
            box = _png.bbox(_png.mask(img, colors[name]))
            want = (20 + 60 * list(FONTS).index(name) * zoom + px(x0, zoom), base - px(y1, zoom),
                    20 + 60 * list(FONTS).index(name) * zoom + px(x1, zoom), base - px(y0, zoom))
            check(box == want, "%s zoom %d %s: ink %s == %s" % (mode, zoom, name, box, want))
            baselines.append(box[3] if box else None)
            check(caps[name].baseline == getattr(mcrfpy.TextBaseline, mode), "%s: .baseline reads back" % mode)
        if mode == "BASELINE":
            check(baselines[0] == baselines[1] == Y,
                  "zoom %d: both fonts share the baseline row (ink ends at y=%d): %s" % (zoom, Y, baselines))
        if mode == "TOP":
            tops = [caps[n].bounds[0].y for n in FONTS]
            check(tops[0] == Y + 2 * zoom and tops[1] == Y + 2 * zoom,
                  "zoom %d: each font's ink top is pos.y + (ascent - ink top): %s" % (zoom, tops))

print("3. Real font (default JetBrains Mono): the modes differ by exactly the metrics")
scene = mcrfpy.Scene("real478")
mcrfpy.current_scene = scene
size = 32
colors = {"TOP": (255, 0, 0), "BASELINE": (0, 255, 0), "EM_TOP": (0, 0, 255)}
caps = {}
for i, mode in enumerate(colors):
    caps[mode] = mcrfpy.Caption(text="H", pos=(20 + 50 * i, 100), font_size=size, outline=0,
                                fill_color=colors[mode], baseline=getattr(mcrfpy.TextBaseline, mode))
    scene.children.append(caps[mode])
img = shot("real")
ink = {m: _png.bbox(_png.mask(img, c)) for m, c in colors.items()}
print("  ink:", ink)
# "H" sits on the baseline: its bottom ink row is the baseline row - 1 in every mode.
check(ink["BASELINE"][3] == 100, "BASELINE: 'H' ends on the row above pos.y (%s)" % (ink["BASELINE"],))
check(ink["EM_TOP"][3] - ink["BASELINE"][3] == size, "EM_TOP is exactly font_size below BASELINE")
asc = ink["TOP"][3] - ink["BASELINE"][3]
# The ascent from the font file itself: hhea.ascender * size / unitsPerEm, which FreeType
# grid-fits to a whole pixel.
with open(mcrfpy.default_font.source, "rb") as f:
    ttf = f.read()
import struct  # noqa: E402
tables = {}
for i in range(struct.unpack(">H", ttf[4:6])[0]):
    tag, _cs, off, _ln = struct.unpack(">4sIII", ttf[12 + 16 * i:28 + 16 * i])
    tables[tag] = off
upem = struct.unpack(">H", ttf[tables[b"head"] + 18:tables[b"head"] + 20])[0]
hhea_asc = struct.unpack(">h", ttf[tables[b"hhea"] + 4:tables[b"hhea"] + 6])[0]
exact = hhea_asc * size / upem
check(int(exact) <= asc <= int(exact) + 1,
      "TOP is the font's ascent below BASELINE: %d px (hhea %d/%d em -> %.2f px)"
      % (asc, hhea_asc, upem, exact))
for m in colors:
    check(caps[m].bounds[0].y == ink[m][1], "%s: bounds top is the ink top (%s vs %s)"
          % (m, caps[m].bounds[0].y, ink[m][1]))
    check(caps[m].advance == caps["EM_TOP"].advance and caps[m].h == caps["EM_TOP"].h,
          "%s: advance and h do not depend on the baseline" % m)

print("4. Changing baseline or font_size later re-places the text")
c = caps["TOP"]
c.baseline = mcrfpy.TextBaseline.BASELINE
check(c.bounds[0].y == caps["BASELINE"].bounds[0].y, "TOP -> BASELINE moves bounds to match")
c.font_size = 16
c.baseline = mcrfpy.TextBaseline.EM_TOP
fresh = mcrfpy.Caption(text="H", pos=(20, 100), font_size=16, baseline=mcrfpy.TextBaseline.EM_TOP)
check(c.bounds[0].y == fresh.bounds[0].y, "font_size + baseline change == a fresh caption")

print("=" * 50)
if failures:
    print("FAIL (%d)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
