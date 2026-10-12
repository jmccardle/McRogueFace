"""Regression test for #480 - tile and entity sprites stretch to the cell size.

A grid's cell_size can differ from its texture's sprite size (an IBM MDA 9x14 font on
18x42 cells emulates the 2:3 pixel aspect). Before #480 every sprite drew at its
texture's own size in the cell's top-left corner. Now:
  - TileLayer: per-texture fit. scale = cell_size / that layer's texture sprite size, so
    every tile fills exactly its cell -- in the chunk raster and in the per-cell fallback
    used when a chunk's RenderTexture can't be created.
  - Entities: grid stretch. scale = cell_size / the GRID texture's sprite size, for every
    entity, so an own-texture entity keeps its size relative to the grid's sprites.
  - sprite_offset is in texture pixels and stretches with the sprite.
  - Display bounds (#235): the factor is measured against the sprite size, so a crop
    keeps its proportion of the cell and stays at the cell's top-left (not tested here).
  - Grid children (Caption/Frame) are not stretched.

Ground truth is the screenshot, decoded here. Mutation-checked by hand: reverting the
chunk raster's scale (GridLayers.cpp, renderChunkToTexture) to (1, 1) fails sections
1 and 2; reverting the fallback's to (zoom, zoom) fails section 3; reverting the
entity scale to (zoom, zoom) fails section 4, and
dropping the stretch from sprite_offset fails its check in section 4.
"""
import os
import struct
import sys
import tempfile
import warnings
import zlib

import mcrfpy
from mcrfpy import automation

TMPDIR = tempfile.mkdtemp(prefix="mcrf480_")
failures = []
warnings.simplefilter("ignore", mcrfpy.TextureWarning)


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


def read_png(path):
    with open(path, "rb") as f:
        data = f.read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    pos = 8
    idat = b""
    width = height = color = None
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        ctype = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if ctype == b"IHDR":
            width, height, depth, color, _, _, interlace = struct.unpack(">IIBBBBB", chunk)
            assert depth == 8 and color in (2, 6) and interlace == 0
        elif ctype == b"IDAT":
            idat += chunk
        elif ctype == b"IEND":
            break
    raw = zlib.decompress(idat)
    channels = 3 if color == 2 else 4
    stride = width * channels
    out = bytearray(height * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(height):
        filt = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if filt == 1:
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 0xFF
        elif filt == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif filt == 3:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif filt == 4:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                b = prev[i]
                c = prev[i - channels] if i >= channels else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        elif filt != 0:
            raise AssertionError("bad PNG filter %d" % filt)
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return width, height, channels, bytes(out)


class Shot:
    def __init__(self, name):
        path = os.path.join(TMPDIR, name + ".png")
        automation.screenshot(path)
        self.w, self.h, self.ch, self.px = read_png(path)

    def rgb(self, x, y):
        i = (y * self.w + x) * self.ch
        return tuple(self.px[i:i + 3])

    def bbox(self, rgb, region):
        """Bounding box and count of pixels exactly `rgb` inside region (x0, y0, x1, y1)."""
        x0, y0, x1, y1 = region
        xs, ys, n = [], [], 0
        for y in range(y0, y1):
            for x in range(x0, x1):
                if self.rgb(x, y) == rgb:
                    xs.append(x)
                    ys.append(y)
                    n += 1
        if not n:
            return None, 0
        return (min(xs), min(ys), max(xs) + 1, max(ys) + 1), n


def pixels_to_texture(w, h, cw, ch, pixel, name):
    data = bytearray()
    for y in range(h):
        for x in range(w):
            data += bytes(list(pixel(x, y)) + [255])
    return mcrfpy.Texture.from_bytes(bytes(data), w, h, cw, ch, name=name)


def marked_sheet(cw, ch, colors, name):
    """One row of cw x ch sprites, each solid colors[i] except a RED top-left texel."""
    return pixels_to_texture(cw * len(colors), ch, cw, ch,
                             lambda x, y: RED if (x % cw, y) == (0, 0) else colors[x // cw], name)


def fresh_scene(name):
    scene = mcrfpy.Scene(name)
    scene.activate()
    return scene


GREEN, YELLOW, BLUE, RED, MAG = (0, 200, 0), (230, 230, 0), (0, 0, 220), (255, 0, 0), (200, 0, 200)


def expect_cell(s, rgb, cell_box, tag, mark=None):
    """The sprite covers exactly cell_box; its RED top-left texel is a mark[0] x mark[1] block."""
    x0, y0, x1, y1 = cell_box
    region = (max(0, x0 - 4), max(0, y0 - 4), min(s.w, x1 + 4), min(s.h, y1 + 4))
    box, n = s.bbox(rgb, region)
    area = (x1 - x0) * (y1 - y0)
    mark_n = 0 if mark is None else mark[0] * mark[1]
    check(box == cell_box and n == area - mark_n,
          "%s: fills %s exactly (got %s, %d px of %d)" % (tag, cell_box, box, n, area - mark_n))
    if mark is not None:
        want = (x0, y0, x0 + mark[0], y0 + mark[1])
        mbox, mn = s.bbox(RED, cell_box)   # not the margin: a neighbour's mark may be there
        check(mbox == want and mn == mark_n,
              "%s: its top-left texel is the %dx%d block %s (got %s, %d)"
              % (tag, mark[0], mark[1], want, mbox, mn))


# ---------------------------------------------------------------------------
print("1. TileLayer chunk raster: a glyph fills its cell (MDA x2/x3, CGA x5/x6, x1)")
for (tw, th), (sx, sy) in (((9, 14), (2, 3)), ((8, 8), (5, 6)), ((16, 16), (1, 1))):
    tag = "%dx%d x%d/x%d" % (tw, th, sx, sy)
    cw, ch = tw * sx, th * sy
    tex = marked_sheet(tw, th, [GREEN, YELLOW], "<glyph %s>" % tag)
    scene = fresh_scene("s480_chunk_%d_%d" % (tw, sx))
    GX, GY = 20, 20
    g = mcrfpy.Grid(grid_size=(4, 3), texture=tex, pos=(GX, GY), size=(4 * cw, 3 * ch), parent=scene)
    g.cell_size = (cw, ch)
    g.center = (2 * cw, 1.5 * ch)
    ground = g.layer("tilesprite")
    ground.fill(-1)
    ground.set((1, 1), 0)
    ground.set((2, 1), 1)
    s = Shot("chunk_%d_%d" % (tw, sx))
    expect_cell(s, GREEN, (GX + cw, GY + ch, GX + 2 * cw, GY + 2 * ch), tag, mark=(sx, sy))
    expect_cell(s, YELLOW, (GX + 2 * cw, GY + ch, GX + 3 * cw, GY + 2 * ch), tag + " (next tile)",
                mark=(sx, sy))

print("1b. the stretch compounds with zoom")
tex = marked_sheet(9, 14, [GREEN], "<glyph zoom>")
scene = fresh_scene("s480_zoom")
g = mcrfpy.Grid(grid_size=(3, 2), texture=tex, pos=(0, 0), size=(108, 168), parent=scene)
g.cell_size = (18, 42)
g.zoom = 2.0
g.center = (27, 42)          # cell (0, 0) at the top left
g.layer("tilesprite").fill(-1)
g.layer("tilesprite").set((1, 0), 0)
s = Shot("zoom")
expect_cell(s, GREEN, (36, 0, 72, 84), "x2/x3 at zoom 2", mark=(4, 6))

# ---------------------------------------------------------------------------
print("2. TileLayer per-texture fit: a layer's own texture fills the cell too")
grid_tex = marked_sheet(16, 16, [BLUE], "<grid16>")
small = marked_sheet(8, 8, [GREEN], "<own8>")
big = pixels_to_texture(32, 24, 32, 24, lambda x, y: YELLOW, "<own32x24>")
scene = fresh_scene("s480_fit")
GX, GY = 10, 10
g = mcrfpy.Grid(grid_size=(5, 2), texture=grid_tex, pos=(GX, GY), parent=scene)
g.layer("tilesprite").fill(-1)
lay_small = mcrfpy.TileLayer(name="small", z_index=1, texture=small)
lay_big = mcrfpy.TileLayer(name="big", z_index=2, texture=big)
g.add_layer(lay_small)
g.add_layer(lay_big)
lay_small.set((0, 0), 0)
lay_big.set((2, 0), 0)
g.layer("tilesprite").set((4, 0), 0)
s = Shot("fit")
expect_cell(s, GREEN, (GX, GY, GX + 16, GY + 16), "8x8 own texture on 16x16 cells (x2)", mark=(2, 2))
expect_cell(s, YELLOW, (GX + 32, GY, GX + 48, GY + 16), "32x24 own texture on 16x16 cells (x1/2, x2/3)")
check(s.bbox(YELLOW, (GX + 48, GY, GX + 80, GY + 32))[1] == 0 and
      s.bbox(YELLOW, (GX + 32, GY + 16, GX + 48, GY + 32))[1] == 0,
      "an oversized tile no longer overhangs into its neighbours")
expect_cell(s, BLUE, (GX + 64, GY, GX + 80, GY + 16), "the grid's own 16x16 texture (x1)", mark=(1, 1))

# ---------------------------------------------------------------------------
print("3. TileLayer per-cell fallback (a chunk RenderTexture that can't be created)")
# 64 cells x 1200 px = a 76800 px wide chunk: beyond any GL max texture size, so
# create() fails and the layer draws cell by cell (#470).
tex = marked_sheet(400, 14, [GREEN], "<wide400x14>")
scene = fresh_scene("s480_fallback")
GX, GY = 0, 30
g = mcrfpy.Grid(grid_size=(64, 2), texture=tex, pos=(GX, GY), size=(1000, 84), layers=[],
                parent=scene)
g.cell_size = (1200, 42)
g.center = (500, 42)
lay = mcrfpy.TileLayer(name="wide", z_index=0)
g.add_layer(lay)
lay.set((0, 1), 0)
errpath = os.path.join(TMPDIR, "stderr.txt")
sys.stderr.flush()
saved = os.dup(2)
with open(errpath, "wb") as ef:
    os.dup2(ef.fileno(), 2)
    try:
        s = Shot("fallback")
    finally:
        os.dup2(saved, 2)
        os.close(saved)
with open(errpath, "rb") as ef:
    err = ef.read().decode("utf-8", "replace")
check("render texture" in err.lower(),
      "precondition: the chunk RenderTexture really failed, so the fallback drew")
box, n = s.bbox(GREEN, (GX, GY, GX + 1000, GY + 84))
check(box == (GX, GY + 42, GX + 1000, GY + 84) and n == 1000 * 42 - 9,
      "fallback x3/x3: cell (0, 1) fills its row to the view edge (got %s, %d)" % (box, n))
mbox, mn = s.bbox(RED, (GX, GY, GX + 1000, GY + 84))
check(mbox == (GX, GY + 42, GX + 3, GY + 45) and mn == 9,
      "fallback: the top-left texel is a 3x3 block (got %s, %d)" % (mbox, mn))

# ---------------------------------------------------------------------------
print("4. Entities: grid stretch, sprite_offset in texture pixels")
grid_tex = marked_sheet(16, 16, [BLUE, GREEN], "<grid16e>")
hero = marked_sheet(16, 24, [YELLOW], "<hero16x24>")
scene = fresh_scene("s480_entity")
GX, GY = 10, 100
g = mcrfpy.Grid(grid_size=(6, 4), texture=grid_tex, pos=(GX, GY), size=(6 * 32, 4 * 48), parent=scene)
g.layer("tilesprite").fill(-1)
g.cell_size = (32, 48)               # x2 / x3 against the grid texture
g.center = (3 * 32, 2 * 48)
inherit = mcrfpy.Entity((0, 0), grid=g, sprite_index=1)
own = mcrfpy.Entity((2, 1), grid=g, sprite_index=0, texture=hero)
lifted = mcrfpy.Entity((4, 2), grid=g, sprite_index=0, texture=hero, sprite_offset=(0, -8))
s = Shot("entity")
expect_cell(s, GREEN, (GX, GY, GX + 32, GY + 48), "an inherited-texture entity fills its cell", mark=(2, 3))
ox, oy = GX + 2 * 32, GY + 48
expect_cell(s, YELLOW, (ox, oy, ox + 32, oy + 72),
            "a 16x24 own-texture entity keeps its proportions (32x72, 1.5 cells tall)", mark=(2, 3))
lx, ly = GX + 4 * 32, GY + 2 * 48 - 8 * 3
expect_cell(s, YELLOW, (lx, ly, lx + 32, ly + 72),
            "sprite_offset (0, -8) is texture pixels: lifted 24 screen px at x3", mark=(2, 3))
check(tuple(lifted.sprite_offset) == (0, -8), "sprite_offset reads back unscaled")

# ---------------------------------------------------------------------------
print("5. Grid children are not stretched")
scene = fresh_scene("s480_children")
tex = marked_sheet(8, 8, [BLUE], "<child8>")
g = mcrfpy.Grid(grid_size=(4, 4), texture=tex, pos=(0, 0), size=(160, 192), parent=scene)
g.layer("tilesprite").fill(-1)
g.cell_size = (40, 48)
g.center = (80, 96)
g.children.append(mcrfpy.Frame(pos=(40, 48), size=(10, 10), fill_color=mcrfpy.Color(*MAG)))
s = Shot("children")
box, n = s.bbox(MAG, (0, 0, 160, 192))
check(box == (40, 48, 50, 58) and n == 100, "a 10x10 Frame child stays 10x10 (got %s, %d)" % (box, n))

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
