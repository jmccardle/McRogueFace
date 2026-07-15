# mcrf: objects=[Color,ColorLayer,Entity,FOV,Grid,InputState,Key,Scene] verified=0.2.8-dev status=ok
import mcrfpy

# Setup
scene = mcrfpy.Scene("game")
mcrfpy.current_scene = scene

# Create grid
grid = mcrfpy.Grid(
    grid_size=(40, 30),
    texture=mcrfpy.default_texture,
    pos=(0, 0),
    size=(800, 600)
)
scene.children.append(grid)

# Initialize map with walls and floors
for y in range(30):
    for x in range(40):
        point = grid.at(x, y)
        # Border walls
        if x == 0 or x == 39 or y == 0 or y == 29:
            point.tilesprite = 1
            point.walkable = False
            point.transparent = False
        # Some interior walls
        elif x == 15 and 5 <= y <= 20:
            point.tilesprite = 1
            point.walkable = False
            point.transparent = False
        elif y == 15 and 20 <= x <= 30:
            point.tilesprite = 1
            point.walkable = False
            point.transparent = False
        else:
            point.tilesprite = 0
            point.walkable = True
            point.transparent = True

# Add FOV color layer
fov_layer = mcrfpy.ColorLayer(z_index=-1, name="fog")
grid.add_layer(fov_layer)

# Track explored tiles
explored = [[False for _ in range(40)] for _ in range(30)]

# Create player
player = mcrfpy.Entity(
    grid_pos=(5, 5),
    texture=mcrfpy.default_texture,
    sprite_index=64
)
grid.entities.append(player)

# FOV update function
def update_fov():
    px, py = player.grid_x, player.grid_y
    radius = 8

    # Compute FOV
    grid.compute_fov((px, py), radius=radius, algorithm=mcrfpy.FOV.SHADOW)

    # Update visibility display
    for y in range(30):
        for x in range(40):
            if grid.is_in_fov(x, y):
                explored[y][x] = True
                fov_layer.set((x, y), mcrfpy.Color(0, 0, 0, 0))
            elif explored[y][x]:
                fov_layer.set((x, y), mcrfpy.Color(30, 30, 50, 180))
            else:
                fov_layer.set((x, y), mcrfpy.Color(0, 0, 0, 255))

# Initial FOV calculation
update_fov()
grid.center = player.pos

# Movement with FOV update
def on_key(key, action):
    if action != mcrfpy.InputState.PRESSED:
        return

    dx, dy = 0, 0

    if key in (mcrfpy.Key.UP, mcrfpy.Key.W): dy = -1
    elif key in (mcrfpy.Key.DOWN, mcrfpy.Key.S): dy = 1
    elif key in (mcrfpy.Key.LEFT, mcrfpy.Key.A): dx = -1
    elif key in (mcrfpy.Key.RIGHT, mcrfpy.Key.D): dx = 1
    else:
        return

    new_x = player.grid_x + dx
    new_y = player.grid_y + dy

    if 0 <= new_x < 40 and 0 <= new_y < 30:
        if grid.at(new_x, new_y).walkable:
            player.grid_pos = (new_x, new_y)
            grid.center = player.pos
            update_fov()

scene.on_key = on_key
