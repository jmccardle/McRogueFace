# mcrf: objects=[Easing,Entity,Grid,Scene] verified=0.3.1 status=ok
import mcrfpy

scene = mcrfpy.Scene("entity-demo")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(
    grid_size=(16, 12),
    texture=mcrfpy.default_texture,
    pos=(0, 0),
    size=(1024, 768),
    zoom=4.0
)
scene.children.append(grid)

for y in range(12):
    for x in range(16):
        grid.at(x, y).tilesprite = 48

# Create an entity
player = mcrfpy.Entity(grid_pos=(10, 10), texture=mcrfpy.default_texture, sprite_index=84)

# Add to a grid
grid.entities.append(player)

# Move to a new grid (tile) position -- instant, integer coordinates
player.grid_pos = (11, 10)

# Animated movement: draw_pos is the fractional tile position used for smooth
# motion between cells. (player.x/.y/.pos are pixels, like every drawable.)
player.animate("draw_pos", (12, 10), 0.2, mcrfpy.Easing.EASE_OUT_QUAD)

# Pathfinding: find_path() returns an AStarPath (or None if unreachable);
# it does not move the entity itself.
path = player.find_path((15, 10))
if path is not None:
    print("Path found!")

# Field of view
visible = player.visible_entities(radius=8)
for enemy in visible:
    print(f"Can see: {enemy.name}")
