# mcrf: objects=[Entity,Grid,Scene,Texture,TileLayer] verified=0.2.8-dev status=ok
import mcrfpy

# Load texture
texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)

# Create grid using texture
grid = mcrfpy.Grid(
    grid_size=(40, 30),
    texture=texture,
    pos=(0, 0),
    size=(640, 480)
)

# Set tile sprites via a TileLayer
layer = mcrfpy.TileLayer(name="floor", z_index=0, texture=texture)
grid.add_layer(layer)
layer.fill(0)  # Floor tile

# Add entity with same texture
player = mcrfpy.Entity(
    grid_pos=(5, 5),
    texture=texture,
    sprite_index=84  # Player sprite
)
grid.entities.append(player)

scene = mcrfpy.Scene("texture_grid_demo")
scene.children.append(grid)
mcrfpy.current_scene = scene
