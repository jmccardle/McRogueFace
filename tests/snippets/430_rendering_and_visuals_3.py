# mcrf: objects=[Grid,Scene,Sprite,Texture,TileLayer] verified=0.3.6 status=ok
import mcrfpy

scene = mcrfpy.Scene("textures")
ui = scene.children

# region: load-texture
# Load a sprite sheet with tile dimensions
texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)

# Use with sprite
sprite = mcrfpy.Sprite(x=100, y=100)
sprite.texture = texture
sprite.sprite_index = 5  # Use 6th sprite (0-indexed)
# endregion

# region: sheet-grid
# Load tileset for grid layers
texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
terrain = mcrfpy.TileLayer(name="terrain", z_index=-1, texture=texture)

grid = mcrfpy.Grid(grid_size=(50, 50), pos=(100, 100), size=(400, 400),
                    layers=[terrain])

# Set tiles using the TileLayer
for x in range(50):
    for y in range(50):
        terrain.set((x, y), 0)  # Floor tile index
# endregion

ui.append(grid)
sprite.z_index = 10
ui.append(sprite)

mcrfpy.current_scene = scene
