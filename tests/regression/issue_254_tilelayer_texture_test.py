"""Regression test for #254: a TileLayer with no texture draws with its grid's.

#454 changed how: the grid's texture used to be COPIED into the layer when it was
attached, so changing the grid's texture later didn't restyle it. Now the layer keeps
none of its own (`layer.texture is None`) and looks the grid's up each time it's drawn.
The drawing itself is checked against screenshots in
issue_453_454_grid_texture_cell_size_test.py; this checks every way of attaching.
"""
import mcrfpy
import sys

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


scene = mcrfpy.Scene("test254")
mcrfpy.current_scene = scene
tex = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
tex2 = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)

# add_layer()
grid = mcrfpy.Grid(grid_size=(10, 10), texture=tex, pos=(0, 0), size=(160, 160))
scene.children.append(grid)
layer = mcrfpy.TileLayer(name="terrain", z_index=0)
grid.add_layer(layer)
check(layer.texture is None, "add_layer: no texture of its own (inherits)")
own = mcrfpy.TileLayer(name="overlay", z_index=1, texture=tex2)
grid.add_layer(own)
check(own.texture is tex2, "add_layer: a layer with a texture keeps its own")

# Grid(layers=[...])
layer = mcrfpy.TileLayer(name="base", z_index=0)
grid2 = mcrfpy.Grid(grid_size=(10, 10), texture=tex, pos=(0, 0), size=(160, 160), layers=[layer])
check(layer.texture is None, "Grid(layers=[...]): no texture of its own (inherits)")

# layer.grid = grid
layer = mcrfpy.TileLayer(name="via_prop", z_index=0)
layer.grid = grid
check(layer.texture is None, "layer.grid = grid: no texture of its own (inherits)")

# Assigning None goes back to inheriting.
own.texture = None
check(own.texture is None, "layer.texture = None: inherits again")

if failures:
    print("FAIL: %d check(s)" % len(failures))
    sys.exit(1)
print("PASS")
sys.exit(0)
