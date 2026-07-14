# mcrf: objects=[Caption,Color,ColorLayer,Entity,Grid,Scene] verified=0.2.8-dev status=ok
# FOV Basic - Field of view computation
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

# Add fog layer for FOV visualization
fog_layer = mcrfpy.ColorLayer(z_index=1, name="fog")
grid.add_layer(fog_layer)
fog_layer.fill(mcrfpy.Color(0, 0, 0, 200))  # Start dark

# Create dungeon with walls
for y in range(12):
    for x in range(16):
        cell = grid.at(x, y)
        # Border walls
        if x == 0 or x == 15 or y == 0 or y == 11:
            cell.tilesprite = 1
            cell.walkable = False
            cell.transparent = False
        # Internal pillars
        elif (x in [4, 8, 12]) and (y in [4, 8]):
            cell.tilesprite = 1
            cell.walkable = False
            cell.transparent = False
        else:
            cell.tilesprite = 48
            cell.walkable = True
            cell.transparent = True

# Player position
player_pos = (8, 6)
player = mcrfpy.Entity(grid_pos=player_pos, texture=mcrfpy.default_texture, sprite_index=84)
grid.entities.append(player)

# Compute FOV from player position
grid.compute_fov(player_pos, radius=8)

# Clear fog for visible cells
for y in range(12):
    for x in range(16):
        if grid.is_in_fov((x, y)):
            fog_layer.set((x, y), mcrfpy.Color(0, 0, 0, 0))  # Clear

status = mcrfpy.Caption(text="FOV radius=8, dark areas not visible", pos=(340, 700))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)
