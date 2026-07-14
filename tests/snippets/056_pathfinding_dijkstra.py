# mcrf: objects=[Caption,Color,ColorLayer,Grid,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Dijkstra Map - Distance-based pathfinding
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(
    grid_size=(16, 12),
    texture=mcrfpy.default_texture,
    pos=(0, 0),
    size=(1024, 768),
    zoom=4.0
)
scene.children.append(grid)

# Add color layer for visualization
dist_layer = mcrfpy.ColorLayer(z_index=1, name="distances")
grid.add_layer(dist_layer)

# Floor tiles
for y in range(12):
    for x in range(16):
        cell = grid.at(x, y)
        cell.tilesprite = 48
        cell.walkable = True

# Some walls
for i in range(5):
    grid.at(8, 2 + i).tilesprite = 1
    grid.at(8, 2 + i).walkable = False

# Compute dijkstra from center
center = (8, 6)
dijkstra = grid.get_dijkstra_map(center)

# Visualize distances with color gradient
for y in range(12):
    for x in range(16):
        if grid.at(x, y).walkable:
            dist = dijkstra.distance((x, y))
            if dist is not None and dist < 1000:  # Valid distance
                intensity = max(0, 255 - int(dist * 20))
                dist_layer.set((x, y), mcrfpy.Color(intensity, intensity, 255, 180))

# Mark center
dist_layer.set((center[0], center[1]), mcrfpy.Color(255, 100, 100, 255))

status = mcrfpy.Caption(text="Dijkstra distance map (darker = farther)", pos=(320, 720))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)
