# mcrf: objects=[ColorLayer,Entity,Grid,Scene,TileLayer] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

texture = mcrfpy.default_texture

# Create a grid
grid = mcrfpy.Grid(grid_size=(80, 45), texture=texture, pos=(0, 0), size=(800, 600))
scene.children.append(grid)

# Position and zoom
grid.pos = (100, 50)
grid.zoom = 2.0
grid.center_camera((40, 22))  # Center on tile coordinates

# Work with layers - construct a layer object, then attach it
tile_layer = mcrfpy.TileLayer(name="floor", z_index=0, texture=texture)
color_layer = mcrfpy.ColorLayer(z_index=1, name="tint")
grid.add_layer(tile_layer)
grid.add_layer(color_layer)
tile_layer.set((5, 5), 42)  # Set tile sprite index

# Add entities
player = mcrfpy.Entity(grid_pos=(10, 10), texture=texture, sprite_index=84)
grid.entities.append(player)

# Field of view
grid.fov_radius = 8
grid.compute_fov(player.grid_pos, radius=8)
if grid.is_in_fov((15, 10)):
    print("Visible!")

# Pathfinding
path = grid.find_path(player.grid_pos, (20, 15))
if path:
    next_step = path.walk()

# Dijkstra maps
dijkstra = grid.get_dijkstra_map((20, 15))
distance = dijkstra.distance((10, 10))
