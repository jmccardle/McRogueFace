"""Regression test for #476 - grid children were drawn at twice their position.

A grid child's `pos` is in grid-world pixels (docs/grid-coordinate-spaces.md), so it
must draw at grid.pos + (pos - camera_top_left) * zoom. UIGridView::render passed the
child its final pixel position as the render offset, and every drawable adds its own
position to the offset, so the child drew at (pos - top_left) * zoom + pos.

Ground truth is the screenshot, decoded here.
"""
import os
import struct
import sys
import tempfile
import zlib

import mcrfpy
from mcrfpy import automation

TMPDIR = tempfile.mkdtemp(prefix="mcrf476_")
failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


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
    automation.screenshot(path)
    return read_png(path)


def bbox(img, rgb, region):
    """Bounding box (x0, y0, x1, y1) of pixels exactly `rgb` inside region, or None."""
    w, h, ch, px = img
    x0, y0, x1, y1 = region
    xs, ys = [], []
    for y in range(y0, y1):
        for x in range(x0, x1):
            i = (y * w + x) * ch
            if tuple(px[i:i + 3]) == rgb:
                xs.append(x)
                ys.append(y)
    if not xs:
        return None
    return (min(xs), min(ys), max(xs) + 1, max(ys) + 1)


MAGENTA = (255, 0, 255)
GX, GY, GW, GH = 100, 100, 320, 240
GRID_REGION = (GX, GY, GX + GW, GY + GH)
CHILD = (96, 64)          # grid-world pixels
CHILD_SIZE = (10, 10)


def expected(center, zoom):
    # UIGridView truncates the camera's top-left to whole sprite pixels.
    tl_x = int(center[0] - GW / 2.0 / zoom)
    tl_y = int(center[1] - GH / 2.0 / zoom)
    return (round(GX + (CHILD[0] - tl_x) * zoom), round(GY + (CHILD[1] - tl_y) * zoom))


def build(center, zoom):
    scene = mcrfpy.Scene("s476")
    scene.activate()
    grid = mcrfpy.Grid(grid_size=(40, 30), pos=(GX, GY), size=(GW, GH),
                       texture=mcrfpy.default_texture)
    grid.fill_color = mcrfpy.Color(0, 0, 0)
    for layer in list(grid.layers):
        grid.remove_layer(layer)
    grid.zoom = zoom
    grid.center = center
    scene.children.append(grid)
    return scene, grid


CASES = [
    ("default camera, zoom 1", (160, 120), 1.0),
    ("panned camera, zoom 1", (200, 150), 1.0),
    ("zoom 2", (160, 120), 2.0),
    ("zoom 0.5", (320, 240), 0.5),
]

print("1. a Frame child draws at grid.pos + (pos - camera_top_left) * zoom")
for label, center, zoom in CASES:
    scene, grid = build(center, zoom)
    f = mcrfpy.Frame(pos=CHILD, size=CHILD_SIZE, fill_color=mcrfpy.Color(*MAGENTA))
    f.outline = 0
    grid.children.append(f)
    box = bbox(shot("frame_%s" % zoom), MAGENTA, GRID_REGION)
    ex = expected(center, zoom)
    check(box is not None and box[:2] == ex,
          "%s: frame top-left %s, expected %s" % (label, box and box[:2], ex))

print("2. a Caption child lands at its position too (all drawables share the fix)")
for label, center, zoom in CASES[:3]:
    scene, grid = build(center, zoom)
    c = mcrfpy.Caption(text="#", pos=CHILD, font_size=16,
                       fill_color=mcrfpy.Color(*MAGENTA))
    c.outline = 0
    grid.children.append(c)
    box = bbox(shot("caption_%s" % zoom), MAGENTA, GRID_REGION)
    ex = expected(center, zoom)
    # Glyph ink starts a few pixels inside the caption's box (bearing, line gap).
    ok = box is not None and 0 <= box[0] - ex[0] <= 8 and 0 <= box[1] - ex[1] <= 16
    check(ok, "%s: caption ink at %s, box origin expected %s" % (label, box and box[:2], ex))

print("=" * 50)
if failures:
    print("FAIL (%d)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
