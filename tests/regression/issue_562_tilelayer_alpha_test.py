"""Regression test for #562 - layer chunks applied alpha twice.

A TileLayer/ColorLayer paints each chunk into a RenderTexture, then composites the chunk
sprite onto the target. With plain alpha blending at both steps, a translucent texel was
multiplied by its alpha twice: white@128 over blue (0,0,255) read (64,64,191) instead of
(128,128,255), red@128 read (64,0,127) instead of (128,0,127). The chunk now holds correct
premultiplied RGBA (colour SrcAlpha/OneMinusSrcAlpha, alpha One/OneMinusSrcAlpha) and is
composited with One/OneMinusSrcAlpha.

The same double alpha hit Frame's clip_children / cache_subtree texture (section 4).

Ground truth is a Sprite / Frame (drawn straight to the target, never through a chunk)
over the same background, within +-2, and the closed-form value.
"""
import os
import struct
import sys
import tempfile
import warnings
import zlib

import mcrfpy
from mcrfpy import automation

TMPDIR = tempfile.mkdtemp(prefix="mcrf562_")
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



def shot(name):
    path = os.path.join(TMPDIR, name + ".png")
    mcrfpy.step(0)  # the screenshot shows the last complete frame; draw this one (#529)
    automation.screenshot(path)
    return read_png(path)


def px(img, x, y):
    w, h, ch, data = img
    i = (y * w + x) * ch
    return tuple(data[i:i + 3])


def near(a, b, tol=2):
    return all(abs(p - q) <= tol for p, q in zip(a, b))


BLUE = (0, 0, 255)
# 4 sprites of 16x16: 0 white@128, 1 red@128, 2 opaque green, 3 white@255
SPRITES = [(255, 255, 255, 128), (255, 0, 0, 128), (0, 200, 0, 255), (255, 255, 255, 255)]
data = bytearray()
for y in range(16):
    for s in SPRITES:
        data += bytes(s) * 16
tex = mcrfpy.Texture.from_bytes(bytes(data), 64, 16, 16, 16, name="<issue562>")
tex_b = mcrfpy.Texture.from_bytes(bytes(data), 64, 16, 16, 16, name="<issue562b>")

scene = mcrfpy.Scene("s562")
scene.activate()
bg = mcrfpy.Frame(pos=(0, 0), size=(400, 300), fill_color=mcrfpy.Color(*BLUE))
scene.children.append(bg)


def grid_at(y):
    g = mcrfpy.Grid(grid_size=(4, 1), texture=tex, pos=(10, y), size=(64, 16))
    g.cell_size = (16, 16)
    g.center = (32, 8)
    g.fill_color = mcrfpy.Color(*BLUE)
    scene.children.append(g)
    return g


# --- TileLayer: one layer, tiles 0..3 -------------------------------------------------
g1 = grid_at(10)
t = g1.layer("tilesprite")
for i in range(4):
    t.set((i, 0), i)

# --- reference: the same sprites drawn directly --------------------------------------
for i in range(4):
    bg.children.append(mcrfpy.Sprite(pos=(10 + 16 * i, 60), texture=tex, sprite_index=i))

# --- two stacked TileLayers (white@128 twice) vs two stacked Sprites -------------------
g2 = grid_at(110)
t_lo = g2.layer("tilesprite")
t_lo.fill(-1)
t_lo.set((0, 0), 0)
t_lo.set((1, 0), 1)
t_hi = mcrfpy.TileLayer(name="hi", z_index=1, texture=tex_b)
g2.add_layer(t_hi)
t_hi.fill(-1)
t_hi.set((0, 0), 0)
t_hi.set((1, 0), 1)
for i in range(2):
    for _ in range(2):
        bg.children.append(mcrfpy.Sprite(pos=(10 + 16 * i, 160), texture=tex, sprite_index=i))

# --- ColorLayers: translucent white, alone and stacked, vs Frames ----------------------
g3 = grid_at(210)
c1 = mcrfpy.ColorLayer(name="c1", z_index=1)
g3.add_layer(c1)
c1.fill(mcrfpy.Color(255, 255, 255, 128))
g4 = grid_at(250)
ca = mcrfpy.ColorLayer(name="ca", z_index=1)
cb = mcrfpy.ColorLayer(name="cb", z_index=2)
g4.add_layer(ca)
g4.add_layer(cb)
ca.fill(mcrfpy.Color(255, 255, 255, 128))
cb.fill(mcrfpy.Color(255, 255, 255, 128))
for _ in range(2):
    bg.children.append(mcrfpy.Frame(pos=(200, 250), size=(64, 16), fill_color=mcrfpy.Color(255, 255, 255, 128)))
bg.children.append(mcrfpy.Frame(pos=(200, 210), size=(64, 16), fill_color=mcrfpy.Color(255, 255, 255, 128)))

# --- Frame render-texture paths (cache_subtree / clip_children) vs the direct path -----
WHITE128 = mcrfpy.Color(255, 255, 255, 128)
SOLID = mcrfpy.Color(255, 255, 255, 255)
FRAME_X = 300
frame_rows = []   # (label, y, expected)


def frame_row(label, y, fill, expected, **kw):
    f = mcrfpy.Frame(pos=(FRAME_X, y), size=(40, 16), fill_color=fill)
    for k, v in kw.items():
        setattr(f, k, v)
    if kw.get("clip_children"):
        f.children.append(mcrfpy.Frame(pos=(0, 0), size=(4, 4)))
    bg.children.append(f)
    frame_rows.append((label, y, expected))


frame_row("plain translucent frame", 10, WHITE128, (128, 128, 255))
frame_row("cache_subtree translucent frame", 40, WHITE128, (128, 128, 255), cache_subtree=True)
frame_row("clip_children translucent frame", 70, WHITE128, (128, 128, 255), clip_children=True)
frame_row("plain translucent frame, opacity 0.5", 100, WHITE128, (64, 64, 255), opacity=0.5)
frame_row("cached translucent frame, opacity 0.5", 130, WHITE128, (64, 64, 255),
          cache_subtree=True, opacity=0.5)
frame_row("plain solid frame, opacity 0.5", 160, SOLID, (127, 127, 255), opacity=0.5)
frame_row("cached solid frame, opacity 0.5", 190, SOLID, (127, 127, 255),
          cache_subtree=True, opacity=0.5)

img = shot("all")


def cell(x0, y0, i):
    return px(img, x0 + 16 * i + 8, y0 + 8)


print("1. single TileLayer vs Sprite vs closed form")
# 255 * 128/255 = 128 ; 255 * (1 - 128/255) = 127
want = [(128, 128, 255), (128, 0, 127), (0, 200, 0), (255, 255, 255)]
for i in range(4):
    got, ref = cell(10, 10, i), cell(10, 60, i)
    check(near(ref, want[i]), "Sprite tile %d = %s (want %s)" % (i, ref, want[i]))
    check(near(got, ref), "TileLayer tile %d = %s matches Sprite %s" % (i, got, ref))
    check(near(got, want[i]), "TileLayer tile %d = %s (want %s)" % (i, got, want[i]))

print("2. two stacked TileLayers")
# white@128 over (128,128,255) -> 255*a + 128*(1-a) = 191.75 ; red@128 over red-on-blue (128,0,127)
# -> R 255*a + 128*(1-a) = 191.75, B 127*(1-a) = 63.25
for i in range(2):
    got, ref = cell(10, 110, i), cell(10, 160, i)
    check(near(got, ref), "stacked TileLayers tile %d = %s matches stacked Sprites %s" % (i, got, ref))
check(near(cell(10, 110, 0), (192, 192, 255)), "stacked white@128 = (192,192,255), got %s" % (cell(10, 110, 0),))

print("3. ColorLayer")
got = px(img, 10 + 8, 210 + 8)
check(near(got, (128, 128, 255)), "one translucent ColorLayer = %s (want 128,128,255)" % (got,))
got, ref = px(img, 10 + 8, 250 + 8), px(img, 200 + 8, 250 + 8)
check(near(got, ref), "two stacked ColorLayers = %s matches two Frames %s" % (got, ref))

print("4. Frame cache_subtree / clip_children / opacity")
for label, y, want in frame_rows:
    got = px(img, FRAME_X + 30, y + 12)   # clear of clip_children's 4x4 child
    check(near(got, want), "%s = %s (want %s)" % (label, got, want))

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
