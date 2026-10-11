"""Regression test for #453 / #454 (0.3.0 part) - a grid's texture and cell size.

#453: a GridData's cell size was copied from its texture when it was made, and a
GridData with no texture loaded mcrfpy.default_texture anyway (so it needed a display),
or fell back to a hardcoded 16x16. Now:
  - GridData.cell_size is a field: unset reads the texture's sprite size, or 1x1 with no
    texture. Setting a texture fills an unset size; a set one is kept, including when the
    texture is removed.
  - GridData.texture is writable. A grid made with no texture has none, and needs no display.
  - The first time a view draws a grid with no texture, it assigns mcrfpy.default_texture
    and warns (mcrfpy.TextureWarning). A Grid's default size and default camera follow the
    cell size, so a textureless Grid looks the same as one given the default texture.

#454 (the GridData level): TileLayers and entities with no texture of their own hold none
(`.texture` is None) and draw with the grid's texture, looked up each time they're drawn,
so assigning grid.texture restyles them ("day" -> "night").

Also a first look at non-16 and non-square cells (#455): 8x8, 8x16, 16x8, 12x12, 48x48 --
cell boundaries land on exact pixels and hit testing finds the right cell at its edges.

Ground truth for drawing is the screenshot, decoded here.
"""
import os
import struct
import subprocess
import sys
import tempfile
import warnings
import zlib

import mcrfpy
from mcrfpy import automation

TMPDIR = tempfile.mkdtemp(prefix="mcrf453_")
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


def solid_sheet(cw, ch, colors, name):
    """A texture whose sprites (cw x ch each, in one row) are solid `colors`."""
    w = cw * len(colors)
    rows = []
    for _ in range(ch):
        row = b""
        for r, g, b in colors:
            row += bytes([r, g, b, 255]) * cw
        rows.append(row)
    return mcrfpy.Texture.from_bytes(b"".join(rows), w, ch, cw, ch, name=name)


def fresh_scene(name):
    scene = mcrfpy.Scene(name)
    scene.activate()
    return scene


GREEN, YELLOW, BLUE, WHITE, RED = (0, 200, 0), (230, 230, 0), (0, 0, 220), (250, 250, 250), (255, 0, 0)


# ---------------------------------------------------------------------------
print("1. no display: a GridData and its entities need no texture")
probe = r'''
import mcrfpy
for layers in ("default", None):
    d = mcrfpy.GridData(grid_size=(4, 3)) if layers == "default" else mcrfpy.GridData(grid_size=(4, 3), layers=None)
    print("DATA", d.texture, tuple(d.cell_size), d.cell_width, d.cell_height)
e = mcrfpy.Entity((1, 2), grid=d)
print("ENTITY", e.texture, tuple(e.pos))
d.cell_size = (16, 8)
print("SIZED", tuple(d.cell_size), tuple(e.pos), e.x, e.y)
lay = mcrfpy.TileLayer(name="t", z_index=0)
d.add_layer(lay)
print("LAYER", lay.texture)
print("TILESPRITE", mcrfpy.GridData(grid_size=(2, 2)).layer("tilesprite").texture)
'''
env = {k: v for k, v in os.environ.items() if k not in ("DISPLAY", "WAYLAND_DISPLAY")}
env["ALSOFT_DRIVERS"] = "null"
try:
    out = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True,
                         timeout=30, env=env, cwd=os.path.dirname(sys.executable))
    text = out.stdout + out.stderr
    rc = out.returncode
except subprocess.TimeoutExpired:
    text, rc = "", None
check(rc == 0, "the probe runs with no display (rc=%s)%s" % (rc, "" if rc == 0 else "\n" + text[-500:]))
check(text.count("DATA None (1.0, 1.0) 1 1") == 2,
      "GridData() and GridData(layers=None): no texture, cell size 1x1")
check("ENTITY None (1.0, 2.0)" in text, "Entity() has no texture; with 1x1 cells its pixels are its tiles")
check("SIZED (16.0, 8.0) (16.0, 16.0) 16.0 16.0" in text, "a custom 16x8 cell size scales entity pixels")
check("LAYER None" in text, "an attached TileLayer with no texture keeps none")
check("TILESPRITE None" in text, "the default 'tilesprite' layer has no texture of its own")

# ---------------------------------------------------------------------------
print("2. cell size rules")
tex16 = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
tex8 = solid_sheet(8, 8, [GREEN], "<8x8>")
d = mcrfpy.GridData(grid_size=(3, 3))
check(tuple(d.cell_size) == (1, 1), "no texture: 1x1")
d.texture = tex16
check(d.texture is tex16 and tuple(d.cell_size) == (16, 16), "setting a texture fills an unset size")
d.texture = tex8
check(tuple(d.cell_size) == (16, 16), "a filled size is kept when the texture changes")
d.texture = None
check(d.texture is None and tuple(d.cell_size) == (16, 16), "removing the texture keeps the size")
d.cell_size = None
check(tuple(d.cell_size) == (1, 1), "cell_size = None unsets it (no texture: 1x1)")
d.texture = tex8
check(tuple(d.cell_size) == (8, 8), "a texture fills it again")
d.cell_size = (12, 12)
d.texture = tex16
check(tuple(d.cell_size) == (12, 12), "a custom size is kept when a texture is set")
d.cell_size = None
check(tuple(d.cell_size) == (16, 16), "unset with a texture: reads the texture's sprite size")
d.cell_width = 8
check(tuple(d.cell_size) == (8, 16) and d.cell_height == 16, "cell_width sets one dimension")
d.cell_size = mcrfpy.Vector(4, 6)
check(tuple(d.cell_size) == (4, 6), "cell_size takes a Vector")
for bad, exc in (((0, 4), ValueError), ((1.5, 2), ValueError), ((-8, 8), ValueError),
                 ("ab", TypeError), ((1, 2, 3), TypeError)):
    try:
        d.cell_size = bad
        check(False, "cell_size = %r raises %s" % (bad, exc.__name__))
    except exc:
        check(True, "cell_size = %r raises %s" % (bad, exc.__name__))
for attr, bad, exc in (("cell_width", 0, ValueError), ("cell_height", "x", TypeError),
                       ("texture", 5, TypeError)):
    try:
        setattr(d, attr, bad)
        check(False, "%s = %r raises %s" % (attr, bad, exc.__name__))
    except exc:
        check(True, "%s = %r raises %s" % (attr, bad, exc.__name__))
try:
    del d.cell_size
    check(False, "del cell_size raises TypeError")
except TypeError:
    check(True, "del cell_size raises TypeError")

# ---------------------------------------------------------------------------
print("3. first draw: the default texture, once, with a TextureWarning")
scene = fresh_scene("s453_first")
g = mcrfpy.Grid(grid_size=(10, 8), pos=(0, 0), parent=scene)
e = mcrfpy.Entity((3, 2), grid=g)
check(g.texture is None and tuple(g.size) == (10, 8) and tuple(g.center) == (5, 4),
      "before drawing: no texture, 1x1 cells, the view is the map at 1:1 (10x8)")
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    Shot("first")
    first = [w for w in caught if issubclass(w.category, mcrfpy.TextureWarning)]
    Shot("second")
    second = [w for w in caught if issubclass(w.category, mcrfpy.TextureWarning)]
check(len(first) == 1, "the first draw warns once (%d)" % len(first))
check(len(second) == 1, "a later draw doesn't warn again (%d)" % len(second))
check(issubclass(mcrfpy.TextureWarning, UserWarning), "TextureWarning is a UserWarning")
dt = mcrfpy.default_texture
check(g.texture is dt and g.grid_data.texture is dt, "the default texture is assigned to the GridData")
check(tuple(g.cell_size) == (dt.sprite_width, dt.sprite_height), "the cell size follows it")
check(tuple(g.size) == (10 * dt.sprite_width, 8 * dt.sprite_height),
      "a view with no size given still shows the whole map")
check(tuple(g.center) == (5 * dt.sprite_width, 4 * dt.sprite_height),
      "a view with no center given still has cell (0, 0) at the top left")
check(tuple(e.pos) == (3 * dt.sprite_width, 2 * dt.sprite_height), "entity pixels use the new size")
check(e.texture is None and g.layer("tilesprite").texture is None,
      "the entity and the default layer still have none of their own")

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("ignore", mcrfpy.TextureWarning)
    scene = fresh_scene("s453_quiet")
    mcrfpy.Grid(grid_size=(2, 2), parent=scene)
    Shot("quiet")
    check(not [w for w in caught if issubclass(w.category, mcrfpy.TextureWarning)],
          "the warnings filter silences it")

warnings.simplefilter("ignore", mcrfpy.TextureWarning)   # the rest of the test draws on purpose

scene = fresh_scene("s453_camera")
data = mcrfpy.GridData(grid_size=(6, 6), layers=None)
view = mcrfpy.GridView(grid=data, pos=(0, 0), size=(96, 96), parent=scene)
view.center_camera((2.5, 2.5))
fixed = mcrfpy.Grid(grid_size=(5, 5), pos=(200, 0), size=(100, 100), parent=scene)
color_only = mcrfpy.Grid(grid_size=(4, 4), pos=(400, 0), layers=[], parent=scene)
color_only.grid_data.cell_size = (8, 8)
check(tuple(color_only.size) == (32, 32), "a view showing the whole map follows a custom cell size")
Shot("camera")
check(data.texture is dt, "a logic-only GridData shown in a view gets the default too")
check(tuple(view.size) == (96, 96), "an explicit size stays")
check(tuple(view.center) == (2.5 * dt.sprite_width, 2.5 * dt.sprite_height),
      "center_camera() before the first draw keeps the same cells centered")
check(tuple(fixed.size) == (100, 100) and tuple(fixed.center) == (50, 50),
      "explicit size, default camera: cell (0, 0) stays at the top left")
check(tuple(color_only.cell_size) == (8, 8) and tuple(color_only.size) == (32, 32),
      "a custom cell size is kept when the default texture is assigned")

# ---------------------------------------------------------------------------
print("4. inheritance: one texture swap restyles layers and entities (#454)")
day = solid_sheet(16, 16, [GREEN, YELLOW], "<day>")
night = solid_sheet(16, 16, [BLUE, WHITE], "<night>")
own = solid_sheet(16, 16, [RED], "<own>")
scene = fresh_scene("s454")
GX, GY = 100, 100
g = mcrfpy.Grid(grid_size=(5, 4), texture=day, pos=(GX, GY), parent=scene)
ground = g.layer("tilesprite")
ground.fill(0)
marker = mcrfpy.TileLayer(name="marker", z_index=1, texture=own)
g.add_layer(marker)
marker.set((0, 0), 0)
walker = mcrfpy.Entity((4, 3), grid=g, sprite_index=1)
mover = mcrfpy.Entity((2, 0), grid=g, sprite_index=0, texture=own)


def cell_rgb(shot, cx, cy):
    return shot.rgb(GX + cx * 16 + 8, GY + cy * 16 + 8)


s = Shot("day")
check(cell_rgb(s, 1, 1) == GREEN, "day: the ground draws with the grid's texture")
check(cell_rgb(s, 4, 3) == YELLOW, "day: an entity with no texture draws with the grid's")
check(cell_rgb(s, 0, 0) == RED and cell_rgb(s, 2, 0) == RED, "own textures draw their own")
g.texture = night
s = Shot("night")
check(cell_rgb(s, 1, 1) == BLUE, "night: assigning grid.texture restyles the ground")
check(cell_rgb(s, 4, 3) == WHITE, "night: and the entity")
check(cell_rgb(s, 0, 0) == RED and cell_rgb(s, 2, 0) == RED, "own textures are unaffected")
mover.texture = None
check(mover.texture is None, "entity.texture = None: none of its own")
s = Shot("inherit")
check(cell_rgb(s, 2, 0) == BLUE, "an entity set back to None inherits again")
marker.texture = None
s = Shot("layer_inherit")
check(cell_rgb(s, 0, 0) == BLUE, "a layer set back to None inherits again")

# ---------------------------------------------------------------------------
print("5. cell sizes: 8x8, 8x16, 16x8, 12x12, 48x48 (#455 preview)")
for cw, ch in ((8, 8), (8, 16), (16, 8), (12, 12), (48, 48)):
    tag = "%dx%d" % (cw, ch)
    scene = fresh_scene("s455_" + tag)
    tex = solid_sheet(cw, ch, [GREEN], "<%s>" % tag)
    GX, GY = 40, 40
    g = mcrfpy.Grid(grid_size=(5, 4), texture=tex, pos=(GX, GY), parent=scene)
    check(tuple(g.cell_size) == (cw, ch) and tuple(g.size) == (5 * cw, 4 * ch),
          "%s: cell size and default view size" % tag)
    e = mcrfpy.Entity((3, 2), grid=g)
    check(tuple(e.pos) == (3 * cw, 2 * ch), "%s: entity pixels" % tag)
    e.x = 4 * cw
    check(e.draw_pos.x == 4, "%s: setting entity x in pixels moves draw_pos by cells" % tag)
    hot = mcrfpy.ColorLayer(name="hot", z_index=2)
    g.add_layer(hot)
    hot.set((2, 1), mcrfpy.Color(*RED))
    s = Shot("cells_" + tag)
    box, n = s.bbox(RED, (GX, GY, GX + 5 * cw, GY + 4 * ch))
    want = (GX + 2 * cw, GY + ch, GX + 3 * cw, GY + 2 * ch)
    check(box == want and n == cw * ch,
          "%s: cell (2, 1) is exactly its %d pixels, no blur (got %s, %d)" % (tag, cw * ch, box, n))
    clicked = []
    g.on_cell_click = lambda pos, button, action: clicked.append((int(pos.x), int(pos.y)))
    for x, y in ((want[0], want[1]), (want[2] - 1, want[3] - 1), (want[0] + cw // 2, want[1] + ch // 2)):
        clicked.clear()
        automation.click((x, y))
        check(clicked and clicked[0] == (2, 1), "%s: a click at (%d, %d) hits cell (2, 1) (got %s)"
              % (tag, x, y, clicked[:1]))
    clicked.clear()
    automation.click((want[2], want[1]))
    check(clicked and clicked[0] == (3, 1), "%s: one pixel right is cell (3, 1) (got %s)" % (tag, clicked[:1]))

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
