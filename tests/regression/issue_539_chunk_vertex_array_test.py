"""#539: a dirty layer chunk is repainted as one vertex array, not one draw per cell.

The change must not move a pixel. This test does not compare against the old renderer
(that was done once, byte for byte, when the change was made); it checks every pixel of
a screenshot against an oracle computed here from the texture bytes and the layer
contents:

  - a generated texture of 8x6 sprites, each a solid colour with a distinct top-left and
    bottom-right texel, so a flipped, shifted or wrongly indexed quad is visible;
  - a 70x66 grid, so the view crosses a chunk boundary (64 cells) on both axes;
  - a TileLayer over a ColorLayer: valid tiles, -1, and out-of-range indices (#524);
    opaque and fully transparent colour cells;
  - cells at the texture's size, then stretched 2x (#480) so each texel covers 2x2 pixels;
  - a second screenshot after a one-cell change in each layer (one dirty chunk);
  - a texture with display_size / display_origin (#235): the quad is the display rectangle
    at the cell's top-left, sampling sprite texels offset by the origin, the rest of the
    cell showing what is under it;
  - an integer zoom of 2 (the chunk textures are blitted scaled, nearest-neighbour, at an
    integer destination: each texel becomes a 2x2 block).

Mutation-checked by hand: swapping u and u + dw in TileLayer::renderChunkToTexture, or
dropping the texture from the draw call, fails it.
"""
import os
import struct
import sys
import tempfile
import warnings
import zlib

import mcrfpy
from mcrfpy import automation

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _png import read_png

warnings.simplefilter("ignore", mcrfpy.TextureWarning)
TMP = tempfile.mkdtemp(prefix="mcrf539_")
failures = []

SW, SH = 8, 6            # sprite size, non-square
COLS, ROWS = 4, 2        # sheet
GW, GH = 70, 66          # grid, wider and taller than one 64-cell chunk
FILL = (17, 34, 51)


def sprite_texel(index, i, j):
    """RGB of texel (i, j) of sprite `index` in the generated sheet."""
    if (i, j) == (0, 0):
        return (255, 255, 10 + index)
    if (i, j) == (SW - 1, SH - 1):
        return (10 + index, 255, 255)
    if (i, j) == (1, 1):             # first texel of the display_origin variant's window
        return (200, 10 + index, 255 - index)
    if (i, j) == (6, 4):             # last texel of the display_size variant's window
        return (10 + index, 200, 120)
    return (40 + 25 * index, 200 - 20 * index, 90 + 15 * index)


def make_sheet():
    data = bytearray(COLS * SW * ROWS * SH * 4)
    for index in range(COLS * ROWS):
        ox, oy = (index % COLS) * SW, (index // COLS) * SH
        for j in range(SH):
            for i in range(SW):
                p = ((oy + j) * COLS * SW + ox + i) * 4
                data[p:p + 4] = bytes(sprite_texel(index, i, j) + (255,))
    return bytes(data)


def make_texture():
    return mcrfpy.Texture.from_bytes(make_sheet(), COLS * SW, ROWS * SH, SW, SH)


def write_png(path, w, h, rgba):
    """Minimal RGBA PNG writer (Texture.from_bytes has no display_size/display_origin)."""
    raw = b"".join(b"\x00" + rgba[y * w * 4:(y + 1) * w * 4] for y in range(h))

    def chunk(tag, body):
        c = struct.pack(">I", len(body)) + tag + body
        return c + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def tile_at(x, y):
    k = (x * 7 + y * 13) % 11
    if k == 0:
        return -1
    if k == 1:
        return COLS * ROWS + (x % 3)     # just past the last sprite
    if k == 2:
        return 2 ** 31 - 1
    if k == 3:
        return -5
    return (x * 3 + y * 5) % (COLS * ROWS)


def color_at(x, y):
    if (x + 2 * y) % 5 == 0:
        return (0, 0, 0, 0)              # transparent: the grid's fill shows
    return ((x * 9) % 256, (y * 11) % 256, (x + y) * 5 % 256, 255)


# Display window of the texture under test: (width, height, origin x, origin y) within the
# sprite. The full sprite for the plain texture.
WINDOW = (SW, SH, 0, 0)


def expected(tiles, colors, px, py, cell_w, cell_h):
    """Colour of world pixel (px, py). The tile quad is the display window scaled by
    cell/sprite size, at the cell's top-left; outside it the colour layer (or the fill)
    shows."""
    x, y = px // cell_w, py // cell_h
    t = tiles[(x, y)]
    dw, dh, ox, oy = WINDOW
    lx, ly = px % cell_w, py % cell_h
    if 0 <= t < COLS * ROWS and lx < dw * cell_w // SW and ly < dh * cell_h // SH:
        return sprite_texel(t, ox + lx * SW // cell_w, oy + ly * SH // cell_h)
    c = colors[(x, y)]
    return c[:3] if c[3] == 255 else FILL


def compare(label, shot, tiles, colors, cell_w, cell_h, view_w, view_h, zoom=1, left=0, top=0):
    """Screen pixel (px, py) shows world pixel (left + px // zoom, top + py // zoom); `left` /
    `top` are the integer "spritepixels" origin of the view."""
    automation.screenshot(shot)
    w, h, ch, px = read_png(shot)
    bad = 0
    first = None
    for py in range(min(view_h, h)):
        row = py * w * ch
        for pxx in range(min(view_w, w)):
            got = (px[row + pxx * ch], px[row + pxx * ch + 1], px[row + pxx * ch + 2])
            want = expected(tiles, colors, left + pxx // zoom, top + py // zoom, cell_w, cell_h)
            if got != want:
                bad += 1
                if first is None:
                    first = (pxx, py, got, want)
    if bad:
        print(f"  FAIL: {label}: {bad} wrong pixels; first at {first[:2]}: got {first[2]}, want {first[3]}")
        failures.append(label)
    else:
        print(f"  PASS: {label}: {min(view_w, w)}x{min(view_h, h)} pixels exact")


texture = make_texture()
scene = mcrfpy.Scene("issue539")
grid = mcrfpy.Grid(grid_size=(GW, GH), pos=(0, 0), size=(GW * SW, GH * SH), texture=texture)
grid.fill_color = mcrfpy.Color(*FILL)
colors_layer = mcrfpy.ColorLayer(name="colors", z_index=-2, grid_size=(GW, GH))
tiles_layer = mcrfpy.TileLayer(name="tiles", z_index=-1, texture=texture, grid_size=(GW, GH))
grid.add_layer(colors_layer)
grid.add_layer(tiles_layer)

tiles, colors = {}, {}
for y in range(GH):
    for x in range(GW):
        tiles[(x, y)] = tile_at(x, y)
        colors[(x, y)] = color_at(x, y)
        tiles_layer.set((x, y), tiles[(x, y)])
        colors_layer.set((x, y), mcrfpy.Color(*colors[(x, y)]))
scene.children.append(grid)
mcrfpy.current_scene = scene
assert tuple(grid.cell_size) == (SW, SH), grid.cell_size

print("1. cells at the texture's sprite size, view across four chunks")
shot = os.path.join(TMP, "a.png")
compare("full repaint", shot, tiles, colors, SW, SH, GW * SW, GH * SH)

print("2. one cell changed in each layer, in different chunks")
tiles[(3, 4)] = 5
tiles_layer.set((3, 4), 5)
tiles[(66, 65)] = -1
tiles_layer.set((66, 65), -1)
colors[(66, 65)] = (250, 1, 2, 255)
colors_layer.set((66, 65), mcrfpy.Color(250, 1, 2, 255))
compare("partial repaint", shot, tiles, colors, SW, SH, GW * SW, GH * SH)
check_repaints = mcrfpy.get_metrics()["grid_chunks_repainted"]
if check_repaints != 3:
    print(f"  FAIL: expected 3 chunk repaints (2 tile, 1 colour), got {check_repaints}")
    failures.append("partial repaint count")

print("3. cells stretched 2x: every texel covers 2x2 pixels")
grid.cell_size = (SW * 2, SH * 2)
grid.size = (GW * SW * 2, GH * SH * 2)
compare("stretched", shot, tiles, colors, SW * 2, SH * 2, GW * SW * 2, GH * SH * 2)

print("4. edit() exit repaints the layer; same pixels")
with tiles_layer.edit():
    pass
with colors_layer.edit():
    pass
compare("after edit()", shot, tiles, colors, SW * 2, SH * 2, GW * SW * 2, GH * SH * 2)



def build_grid(tex, name, size):
    """A fresh grid over the same tile/colour contents (current `tiles` / `colors`)."""
    sc = mcrfpy.Scene(name)
    g = mcrfpy.Grid(grid_size=(GW, GH), pos=(0, 0), size=size, texture=tex)
    g.fill_color = mcrfpy.Color(*FILL)
    cl = mcrfpy.ColorLayer(name="colors", z_index=-2, grid_size=(GW, GH))
    tl = mcrfpy.TileLayer(name="tiles", z_index=-1, texture=tex, grid_size=(GW, GH))
    g.add_layer(cl)
    g.add_layer(tl)
    for yy in range(GH):
        for xx in range(GW):
            tl.set((xx, yy), tiles[(xx, yy)])
            cl.set((xx, yy), mcrfpy.Color(*colors[(xx, yy)]))
    sc.children.append(g)
    mcrfpy.current_scene = sc
    return g


print("5. texture with display_size=(6, 4), display_origin=(1, 1)")
sheet_png = os.path.join(TMP, "sheet.png")
write_png(sheet_png, COLS * SW, ROWS * SH, make_sheet())
dtex = mcrfpy.Texture(sheet_png, SW, SH, display_size=(6, 4), display_origin=(1, 1))
assert (dtex.display_width, dtex.display_height) == (6, 4), (dtex.display_width, dtex.display_height)
assert (dtex.display_offset_x, dtex.display_offset_y) == (1, 1)
WINDOW = (6, 4, 1, 1)
dgrid = build_grid(dtex, "issue539_display", (GW * SW, GH * SH))
assert tuple(dgrid.cell_size) == (SW, SH), dgrid.cell_size
compare("display window at cell size", shot, tiles, colors, SW, SH, GW * SW, GH * SH)
dgrid.cell_size = (SW * 2, SH * 2)
dgrid.size = (GW * SW * 2, GH * SH * 2)
compare("display window stretched 2x", shot, tiles, colors, SW * 2, SH * 2, GW * SW * 2, GH * SH * 2)
WINDOW = (SW, SH, 0, 0)

print("6. zoom 2: each texel of the chunk texture covers 2x2 screen pixels")
zgrid = build_grid(texture, "issue539_zoom", (640, 400))
zgrid.zoom = 2
zgrid.center = (400, 290)
# the view's integer origin, as the engine computes it: int(center - view / 2 / zoom)
compare("zoom 2", shot, tiles, colors, SW, SH, 640, 400, zoom=2,
        left=int(400 - 640 / 2 / 2), top=int(290 - 400 / 2 / 2))

if failures:
    print("FAIL:", failures)
    sys.exit(1)
print("PASS")
sys.exit(0)
