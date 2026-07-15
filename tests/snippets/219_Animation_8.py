# mcrf: objects=[Easing,Entity,Grid,Scene,Texture] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
grid = mcrfpy.Grid(grid_size=(10, 10), pos=(0, 0), size=(160, 160), texture=texture)
scene.children.append(grid)

player = mcrfpy.Entity(grid_pos=(1, 1), texture=texture, sprite_index=84)
grid.entities.append(player)

# Slide the drawn position across the grid in tile coordinates.
# cell_pos (the logical cell) is NOT changed by this animation.
player.animate("draw_x", 5.0, 0.5, mcrfpy.Easing.EASE_OUT_QUAD)
