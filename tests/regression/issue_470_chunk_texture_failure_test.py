"""#470: a chunk whose RenderTexture cannot be created warns once, then stops retrying."""
import sys, warnings, mcrfpy
from mcrfpy import automation

# 64 cells * 4096 px = 262144 px: beyond any GL max texture size, so create() fails for real.
grid = mcrfpy.Grid(grid_size=(64, 64), pos=(0, 0), size=(200, 200), texture=mcrfpy.default_texture)
layer = mcrfpy.ColorLayer(z_index=-1, name="big")
grid.add_layer(layer)
layer.fill((255, 0, 0, 255))
grid.cell_size = (4096, 4096)
scene = mcrfpy.Scene("t470")
scene.children.append(grid)
mcrfpy.current_scene = scene

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    for i in range(5):
        automation.screenshot("/tmp/t470_%d.png" % i)
    got = [x for x in w if issubclass(x.category, mcrfpy.TextureWarning)
           and "RenderTexture" in str(x.message)]
# one per failing layer (the grid's default TileLayer fails too), not one per frame
mine = [x for x in got if "'big'" in str(x.message)]
assert len(mine) == 1, "expected one warning for 'big' over 5 frames, got %d" % len(mine)
assert len(got) == 2, "expected one warning per layer, got %d" % len(got)
print("PASS")
sys.exit(0)
