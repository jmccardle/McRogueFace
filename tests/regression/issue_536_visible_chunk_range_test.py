"""#536: layers repainted (and cached a texture for) one chunk row and column beyond the view.

`x_limit` / `y_limit` are exclusive cell limits, so the last visible chunk is the one
holding cell `limit - 1`. The old expression was a ceiling used as an inclusive index.

Observed through get_metrics()["grid_chunks_repainted"]: chunk textures repainted in the
last render, summed over layers. Chunks are 64x64 cells; the view adds a 2-cell margin on
the right and bottom. A Grid made with a texture has a built-in "tilesprite" layer, so
counts are per layer times len(grid.layers).
"""
import os
import sys
import tempfile

import mcrfpy
from mcrfpy import automation

failures = []
SHOT = os.path.join(tempfile.gettempdir(), "issue536.png")


def check(label, got, want):
    if got == want:
        print(f"  PASS: {label}: {got}")
    else:
        print(f"  FAIL: {label}: got {got}, want {want}")
        failures.append(label)


def repainted():
    automation.screenshot(SHOT)
    return mcrfpy.get_metrics()["grid_chunks_repainted"]


def make(size, layers=("tile", "color")):
    scene = mcrfpy.Scene("issue536")
    grid = mcrfpy.Grid(grid_size=(256, 256), pos=(0, 0), size=size,
                       texture=mcrfpy.default_texture)
    made = []
    if "tile" in layers:
        made.append(mcrfpy.TileLayer(name="t", z_index=-1, grid_size=(256, 256)))
        made[-1].fill(1)
    if "color" in layers:
        made.append(mcrfpy.ColorLayer(name="c", z_index=-2, grid_size=(256, 256)))
        made[-1].fill(mcrfpy.Color(10, 20, 30, 255))
    for layer in made:
        grid.add_layer(layer)
    scene.children.append(grid)
    mcrfpy.current_scene = scene
    return grid, made, len(grid.layers)


assert mcrfpy.default_texture.sprite_width == 16

print("1. view inside one chunk: 40x22 cells at the top-left")
grid, layers, n = make((640, 352))
check("one chunk per layer", repainted(), 1 * n)
check("nothing dirty, nothing repainted", repainted(), 0)
layers[0].set((3, 3), 2)
check("one cell changed, one chunk", repainted(), 1)
with layers[1].edit():
    pass
check("edit() exit dirties the layer; one chunk is in view", repainted(), 1)

print("2. exclusive limit on a chunk boundary: cells 0..61 visible, +2 margin = limit 64")
grid, layers, n = make((992, 352))
check("still one chunk per layer", repainted(), 1 * n)

print("3. one cell further: limit 65 reaches the second chunk column")
grid, layers, n = make((1008, 352))
check("two chunks per layer", repainted(), 2 * n)

print("4. view centred on a chunk corner: 2x2 chunks, not 3x3")
grid, layers, n = make((640, 352))
grid.center = (64 * 16, 64 * 16)
check("four chunks per layer", repainted(), 4 * n)

print("5. view at the far corner of the layer")
grid, layers, n = make((640, 352), layers=("tile",))
grid.center = (256 * 16 - 320, 256 * 16 - 176)
check("one chunk per layer", repainted(), 1 * n)

print("6. zoomed out to the whole layer: every chunk, once")
grid, layers, n = make((1024, 1024), layers=("color",))
grid.zoom = 0.25
grid.center = (128 * 16, 128 * 16)
check("16 chunks per layer", repainted(), 16 * n)

if failures:
    print("FAIL:", failures)
    sys.exit(1)
print("PASS")
sys.exit(0)
