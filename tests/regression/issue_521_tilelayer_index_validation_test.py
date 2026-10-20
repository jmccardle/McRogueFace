"""#524 (reverses part of #521): a TileLayer stores ANY int; out-of-range indices are not drawn.

Layers do not know what their values mean (a TileLayer can stage a DiscreteMap; "take the
texture off, set values, put it back" must work), so:
  * set / fill / fill_rect / apply_threshold / apply_ranges / layer[x, y] = v accept every int
    that fits a C int: no ValueError for range. Non-ints are TypeErrors; ints beyond a C int
    are OverflowErrors.
  * a value outside 0..sprite_count-1 (including every negative) is not rendered, whatever
    texture is bound when the layer is drawn (screenshot pixel check below).
  * a value ABOVE the highest sprite index of a known texture warns (TextureWarning), once per
    call, on the write only. Negative values never warn.
"""
import os
import struct
import sys
import tempfile
import warnings
import zlib

import mcrfpy
from mcrfpy import automation

TMPDIR = tempfile.mkdtemp(prefix="mcrf524_")
failures = []


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
    automation.screenshot(path)
    w, h, ch, px = read_png(path)
    return lambda x, y: tuple(px[(y * w + x) * ch:(y * w + x) * ch + 3])


def sheet(colors, name):
    """Texture of 8x8 solid sprites in one row."""
    row = b"".join(bytes(c + (255,)) * 8 for c in colors)
    return mcrfpy.Texture.from_bytes(row * 8, 8 * len(colors), 8, 8, 8, name=name)


C = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
BG = (0, 0, 0)
tex4 = sheet(C[:4], "<4 sprites>")
tex6 = sheet(C, "<6 sprites>")


def raises(exc, fn, label):
    try:
        fn()
    except exc:
        return True
    except Exception as e:
        check(False, "%s: wrong exception %s: %s" % (label, type(e).__name__, e))
        return False
    check(False, "%s: did not raise" % label)
    return False


def warned(fn):
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        fn()
    return [x for x in w if issubclass(x.category, mcrfpy.TextureWarning)]


print("1. every int is stored; no ValueError")
scene = mcrfpy.Scene("t524")
scene.activate()
grid = mcrfpy.Grid(grid_size=(8, 1), texture=tex4, pos=(0, 0), size=(64, 8))
grid.fill_color = BG
scene.children.append(grid)
layer = mcrfpy.TileLayer(name="t", z_index=0, texture=tex4)
grid.add_layer(layer)
vals = [0, 4, 99, -5, 2 ** 31 - 1, -2 ** 31, 3, -1]
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    for x, v in enumerate(vals):
        layer.set((x, 0), v)
check([layer.at(x, 0) for x in range(8)] == vals, "set() stores 0, 4, 99, -5, INT_MAX, INT_MIN, 3, -1 unchanged")
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    layer.fill(1000); check(layer.at(2, 0) == 1000, "fill(1000)")
    layer.fill(-77); check(layer.at(2, 0) == -77, "fill(-77)")
    layer.fill_rect((0, 0), (2, 1), 12345); check(layer.at(1, 0) == 12345, "fill_rect(12345)")
    layer.fill_rect((0, 0), (2, 1), -9); check(layer.at(1, 0) == -9, "fill_rect(-9)")
    layer[3, 0] = 50; check(layer.at(3, 0) == 50, "layer[x, y] = 50")
    layer[3, 0] = -50; check(layer.at(3, 0) == -50, "layer[x, y] = -50")
    hm = mcrfpy.HeightMap((8, 1), fill=0.5)
    layer.apply_threshold(hm, (0.0, 1.0), 8); check(layer.at(5, 0) == 8, "apply_threshold(8)")
    layer.apply_threshold(hm, (0.0, 1.0), -3); check(layer.at(5, 0) == -3, "apply_threshold(-3)")
    layer.apply_ranges(hm, [((0.0, 1.0), 2 ** 20)]); check(layer.at(5, 0) == 2 ** 20, "apply_ranges(2**20)")
    layer.apply_ranges(hm, [((0.0, 1.0), -2)]); check(layer.at(5, 0) == -2, "apply_ranges(-2)")

print("2. type and C-int overflow errors remain")
raises(TypeError, lambda: layer.set((0, 0), 1.5), "set float")
raises(TypeError, lambda: layer.fill("a"), "fill str")
raises(TypeError, lambda: layer.__setitem__((0, 0), 1.5), "subscript float")
raises(TypeError, lambda: layer.apply_ranges(hm, [((0.0, 1.0), 1.5)]), "apply_ranges float")
raises(OverflowError, lambda: layer.set((0, 0), 2 ** 31), "set 2**31")
raises(OverflowError, lambda: layer.fill(-2 ** 31 - 1), "fill < INT_MIN")
raises(OverflowError, lambda: layer.__setitem__((0, 0), 2 ** 40), "subscript 2**40")
raises(OverflowError, lambda: layer.__setitem__((0, 0), 2 ** 80), "subscript 2**80")
raises(OverflowError, lambda: layer.apply_ranges(hm, [((0.0, 1.0), 2 ** 40)]), "apply_ranges 2**40")
raises(OverflowError, lambda: layer.apply_ranges(hm, [((0.0, 1.0), 2 ** 80)]), "apply_ranges 2**80")

print("3. warning: only above the highest sprite index, once per call")
layer.fill(-1)
check(not warned(lambda: layer.set((0, 0), 3)), "3 of 4: silent")
check(not warned(lambda: layer.set((0, 0), -40)), "negative: silent")
check(len(warned(lambda: layer.set((0, 0), 4))) == 1, "set(4): TextureWarning")
check(len(warned(lambda: layer.fill(99))) == 1, "fill(99): one warning")
check(len(warned(lambda: layer.fill_rect((0, 0), (4, 1), 4))) == 1, "fill_rect(4): one warning for the call")
check(len(warned(lambda: layer.__setitem__((1, 0), 7))) == 1, "subscript 7: warning")
check(len(warned(lambda: layer.apply_threshold(hm, (0.0, 1.0), 4))) == 1, "apply_threshold(4): one warning")
check(len(warned(lambda: layer.apply_ranges(hm, [((0.0, 0.2), 9), ((0.3, 1.0), 10)]))) == 1,
      "apply_ranges with two high indices: one warning for the call")
check(not warned(lambda: layer.apply_ranges(hm, [((0.0, 1.0), -4)])), "apply_ranges(-4): silent")
layer.texture = tex6
check(not warned(lambda: layer.set((0, 0), 5)), "after rebinding a 6-sprite texture, 5 is valid")
check(len(warned(lambda: layer.set((0, 0), 6))) == 1, "...and 6 warns")
bare = mcrfpy.TileLayer(name="bare", z_index=0)
check(not warned(lambda: bare.fill(10 ** 6)), "a layer with no known texture never warns")
layer.texture = tex4
# -W error turns the warning into an exception, and nothing is stored
with warnings.catch_warnings():
    warnings.simplefilter("error", mcrfpy.TextureWarning)
    layer.fill(-1)
    raises(mcrfpy.TextureWarning, lambda: layer.set((0, 0), 4), "warning as error")
    check(layer.at(0, 0) == -1, "a warning raised as an error stores nothing")

print("4. out-of-range indices are not drawn")
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    for x, v in enumerate(vals):
        layer.set((x, 0), v)
mcrfpy.step(0.01)
px = shot("oor")
want = [C[0], BG, BG, BG, BG, BG, C[3], BG]
for x, w_ in enumerate(want):
    got = px(x * 8 + 4, 4)
    check(got == w_, "cell %d (index %d) draws %s (got %s)" % (x, vals[x], w_, got))

print("5. 'remove the texture, set values, put it back'")
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    layer.fill(-1)
    layer.texture = tex6
    layer.set((0, 0), 5)
    layer.set((1, 0), 4)
    layer.set((2, 0), 99)
mcrfpy.step(0.01)
px = shot("six")
check(px(4, 4) == C[5] and px(12, 4) == C[4] and px(20, 4) == BG, "6-sprite texture: 5 and 4 draw, 99 does not")
layer.texture = tex4
mcrfpy.step(0.01)
px = shot("four")
check(px(4, 4) == BG and px(12, 4) == BG and px(20, 4) == BG,
      "rebound to the 4-sprite texture: the same values are now unrendered (no read past the sheet)")
check(layer.at(0, 0) == 5 and layer.at(1, 0) == 4, "the values themselves were kept")
layer.texture = tex6
mcrfpy.step(0.01)
px = shot("six_again")
check(px(4, 4) == C[5] and px(12, 4) == C[4], "rebound to 6 sprites: they draw again")

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
