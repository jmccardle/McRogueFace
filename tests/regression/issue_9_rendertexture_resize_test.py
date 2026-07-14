#!/usr/bin/env python3
"""
Regression test for Issue #9: Recreate RenderTexture when a grid view is resized

The bug: UIGrid::render() created its RenderTexture once, at a hardcoded size, and
never recreated it. Resizing the grid widget beyond that texture left the new area
unrendered (clipped), and shrinking it left stale content blitted outside the box.

The fix (UIGridView::ensureRenderTextureSize()) sizes the RenderTexture from the game
resolution and recreates it whenever that changes; the blit is clipped to the widget
box. So today a grid must render *correctly across its whole box at every size*:

  * enlarging the widget renders content in the newly exposed area (was clipped),
  * shrinking it leaves no stale pixels outside the new box,
  * content never spills past the widget bounds,
  * a widget larger than the window still renders its visible portion.

This test asserts those four properties on real screenshot pixels. The old version of
this file only printed "check the screenshots by eye" and, worse, died in setup on
grid.at(x, y).color (removed -- per-cell color lives on a ColorLayer now), so none of
it ever ran.

API notes for the update: GridPoint has no .color -> mcrfpy.ColorLayer; Grid takes
grid_size=/pos=/size= kwargs; mcrfpy.setScene/sceneUI -> mcrfpy.Scene + scene.children;
step() is the clock and never renders, automation.screenshot() forces the render.
Window.resolution cannot change in headless, so the resolution-driven recreation path
is exercised via widget resizes only.
"""

import mcrfpy
from mcrfpy import automation
import struct
import sys
import zlib

FAILURES = []

# Grid data is large enough (160 x 160 cells) that its content covers every widget
# size used below, so "no content here" always means a rendering failure.
GRID_CELLS = 160

WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
RED = (255, 0, 0)
BACKGROUND = (0, 0, 0)     # scene clear color, outside any grid
CONTENT_COLORS = (WHITE, GRAY, RED)


def check(label, condition, detail=""):
    if condition:
        print("  PASS: %s" % label)
    else:
        print("  FAIL: %s %s" % (label, detail))
        FAILURES.append(label)


# --------------------------------------------------------------------------- #
# Minimal PNG reader (stdlib only), same as tests/unit/validate_screenshot_test.py
# --------------------------------------------------------------------------- #
def read_png(path):
    with open(path, "rb") as f:
        data = f.read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    pos = 8
    idat = b""
    width = height = depth = color = None
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        ctype = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if ctype == b"IHDR":
            width, height, depth, color, _, _, interlace = struct.unpack(">IIBBBBB", chunk)
            assert depth == 8, "unexpected bit depth %d" % depth
            assert color in (2, 6), "unexpected color type %d" % color
            assert interlace == 0, "interlaced PNG not supported"
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
        if filt == 1:      # Sub
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 0xFF
        elif filt == 2:    # Up
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif filt == 3:    # Average
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif filt == 4:    # Paeth
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


class Image:
    def __init__(self, path):
        self.w, self.h, self.ch, self.px = read_png(path)

    def at(self, x, y):
        i = (y * self.w + x) * self.ch
        return tuple(self.px[i:i + 3])


def create_checkerboard_pattern(layer, grid_width, grid_height, cell_size=2):
    """Create a checkerboard pattern on the color layer for visibility"""
    for x in range(grid_width):
        for y in range(grid_height):
            if (x // cell_size + y // cell_size) % 2 == 0:
                layer.set((x, y), mcrfpy.Color(*WHITE))
            else:
                layer.set((x, y), mcrfpy.Color(*GRAY))


def add_border_markers(layer, grid_width, grid_height):
    """Add colored markers at the borders to test rendering limits"""
    for x in range(grid_width):
        layer.set((x, 0), mcrfpy.Color(*RED))
        layer.set((x, grid_height - 1), mcrfpy.Color(*RED))
    for y in range(grid_height):
        layer.set((0, y), mcrfpy.Color(*RED))
        layer.set((grid_width - 1, y), mcrfpy.Color(*RED))


def render(path):
    """step() advances the sim; the screenshot is what forces a render."""
    mcrfpy.step(0.01)
    automation.screenshot(path)
    return Image(path)


def anchor_camera(grid):
    """Keep tile (0,0) at the widget's top-left after a resize (#169 default)."""
    grid.center = (grid.w / 2.0, grid.h / 2.0)


def is_content(px):
    return px in CONTENT_COLORS


print("=== Testing grid RenderTexture resize (Issue #9) ===\n")

test = mcrfpy.Scene("test")
mcrfpy.current_scene = test
scene_ui = test.children

GRID_X, GRID_Y = 10, 10
grid = mcrfpy.Grid(grid_size=(GRID_CELLS, GRID_CELLS), pos=(GRID_X, GRID_Y), size=(200, 150))
colors = mcrfpy.ColorLayer(name="cells")
grid.add_layer(colors)
create_checkerboard_pattern(colors, GRID_CELLS, GRID_CELLS)
add_border_markers(colors, GRID_CELLS, GRID_CELLS)
scene_ui.append(grid)

# --- Test 1: small grid renders its whole box, and nothing outside it ---------
print("--- Test 1: Small Grid (200x150) ---")
anchor_camera(grid)
img = render("/tmp/issue_9_small_grid.png")

check("top-left tile of small grid is the red border marker",
      img.at(GRID_X + 2, GRID_Y + 2) == RED,
      "got %s" % (img.at(GRID_X + 2, GRID_Y + 2),))
check("interior of small grid is rendered content",
      is_content(img.at(100, 100)), "got %s" % (img.at(100, 100),))
check("far corner of small grid box is rendered content",
      is_content(img.at(GRID_X + 195, GRID_Y + 145)),
      "got %s" % (img.at(GRID_X + 195, GRID_Y + 145),))
check("nothing rendered outside the small grid box",
      img.at(500, 400) == BACKGROUND, "got %s" % (img.at(500, 400),))

# --- Test 2: enlarging the widget must render the newly exposed area ----------
# This is the heart of #9: (500,400) and (880,690) were outside the previous render
# area. With a stale RenderTexture they stay blank/clipped.
print("\n--- Test 2: Resize 200x150 -> 900x700 ---")
grid.w = 900
grid.h = 700
anchor_camera(grid)
img = render("/tmp/issue_9_resized.png")

check("area exposed by the resize is rendered (500,400)",
      is_content(img.at(500, 400)), "got %s" % (img.at(500, 400),))
check("far corner of the enlarged box is rendered (880,690)",
      is_content(img.at(880, 690)), "got %s" % (img.at(880, 690),))
check("enlarged grid does not spill past its right edge",
      img.at(GRID_X + 900 + 5, 100) == BACKGROUND,
      "got %s" % (img.at(GRID_X + 900 + 5, 100),))
check("enlarged grid does not spill past its bottom edge",
      img.at(100, GRID_Y + 700 + 5) == BACKGROUND,
      "got %s" % (img.at(100, GRID_Y + 700 + 5),))

# --- Test 3: widget larger than the window still renders its visible portion --
print("\n--- Test 3: Grid larger than the window (2400x1400) ---")
grid.w = 2400
grid.h = 1400
anchor_camera(grid)
img = render("/tmp/issue_9_beyond_window.png")

check("oversized grid renders at the far edge of the window (1000,700)",
      is_content(img.at(1000, 700)), "got %s" % (img.at(1000, 700),))
check("oversized grid renders near the window origin (20,20)",
      is_content(img.at(20, 20)), "got %s" % (img.at(20, 20),))

# --- Test 4: shrinking must not leave stale pixels outside the new box --------
print("\n--- Test 4: Shrink back to 200x150 ---")
grid.w = 200
grid.h = 150
anchor_camera(grid)
img = render("/tmp/issue_9_shrunk.png")

check("shrunken grid still renders inside its box",
      is_content(img.at(100, 100)), "got %s" % (img.at(100, 100),))
check("no stale content left outside the shrunken box (500,400)",
      img.at(500, 400) == BACKGROUND, "got %s" % (img.at(500, 400),))
check("no stale content left outside the shrunken box (880,690)",
      img.at(880, 690) == BACKGROUND, "got %s" % (img.at(880, 690),))

print("\n=== SUMMARY ===")
if FAILURES:
    print("FAIL: %d check(s) failed: %s" % (len(FAILURES), ", ".join(FAILURES)))
    sys.exit(1)

print("Screenshots saved to /tmp/issue_9_*.png")
print("PASS")
sys.exit(0)
