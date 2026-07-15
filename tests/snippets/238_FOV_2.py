# mcrf: objects=[Color,ColorLayer,Entity,Grid,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("fov-colorlayer-demo")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(grid_size=(20, 15), texture=mcrfpy.default_texture, pos=(0, 0), size=(640, 480))
scene.children.append(grid)

player = mcrfpy.Entity(grid_pos=(10, 7), texture=mcrfpy.default_texture, sprite_index=84)
grid.entities.append(player)

fog = mcrfpy.ColorLayer(z_index=10, name="fog")
grid.add_layer(fog)
fog.fill(mcrfpy.Color(0, 0, 0, 255))  # Start dark

def update_visibility():
    fog.draw_fov((player.grid_x, player.grid_y), radius=8)  # Reveal visible cells, re-fog the rest

update_visibility()
