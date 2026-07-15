# mcrf: objects=[Grid,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("quickstart")
mcrfpy.current_scene = scene

# Create a grid with walkable cells
grid = mcrfpy.Grid(grid_size=(20, 20))
for y in range(20):
    for x in range(20):
        grid.at((x, y)).walkable = True
scene.children.append(grid)

# Get dijkstra map from player position
dijkstra = grid.get_dijkstra_map((10, 10))

# Convert to heightmap
hmap = dijkstra.to_heightmap()

# Use the heights
player_distance = hmap[(5, 5)]  # Distance from (5,5) to (10,10)
