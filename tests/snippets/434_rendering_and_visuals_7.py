# mcrf: objects=[Easing,Grid,Scene,Texture,TileLayer] verified=0.3.6-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("grid_rendering")
ui = scene.children

# region: basic-grid
# Load tileset
texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)
terrain = mcrfpy.TileLayer(name="terrain", z_index=-1, texture=texture)

# Create grid with layer
grid = mcrfpy.Grid(grid_size=(50, 50), pos=(100, 100), size=(400, 400),
                    layers=[terrain])

# Set tiles via the TileLayer
for x in range(50):
    for y in range(50):
        if x == 0 or x == 49 or y == 0 or y == 49:
            terrain.set((x, y), 1)  # Wall
        else:
            terrain.set((x, y), 0)  # Floor
# endregion

ui.append(grid)

# region: viewport
# Zoom
grid.zoom = 2.0

# Center camera on tile coordinates
grid.center_camera((25, 25))

# Animate viewport
grid.animate("zoom", 1.5, 1.0, mcrfpy.Easing.EASE_IN_OUT)
grid.animate("center_x", 100.0, 1.0, mcrfpy.Easing.EASE_IN_OUT)
# endregion

mcrfpy.current_scene = scene
