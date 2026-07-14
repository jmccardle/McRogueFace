# mcrf: objects=[Grid,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Grid Tiles - Different tile types
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

# Different terrain types
tile_types = [
    (48, "Floor"),     # Floor
    (1, "Wall"),       # Wall
    (65, "Door"),      # Door
    (17, "Chest"),     # Chest
    (80, "Water"),     # Water
]

# Fill grid with pattern showing different tiles
for y in range(12):
    for x in range(16):
        cell = grid.at(x, y)
        # Border walls
        if x == 0 or x == 15 or y == 0 or y == 11:
            cell.tilesprite = 1
        else:
            # Show different tiles in sections
            section = (x - 1) // 3
            if section < len(tile_types):
                cell.tilesprite = tile_types[section][0]
            else:
                cell.tilesprite = 48
