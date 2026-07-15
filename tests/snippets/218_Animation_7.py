# mcrf: objects=[Easing,Grid,Scene,Texture] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
grid = mcrfpy.Grid(grid_size=(30, 20), pos=(0, 0), size=(480, 320), texture=texture)
scene.children.append(grid)

# grid.center is in PIXELS. To pan to tile (14, 8) with 16x16 tiles,
# target the middle of that tile:
tile_x, tile_y = 14, 8
target = (tile_x * 16 + 8, tile_y * 16 + 8)

grid.animate("center", target, 0.4, mcrfpy.Easing.EASE_OUT_CUBIC)
grid.animate("zoom", 2.0, 0.4, mcrfpy.Easing.EASE_IN_OUT)
