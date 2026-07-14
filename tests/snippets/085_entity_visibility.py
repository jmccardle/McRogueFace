# mcrf: objects=[Caption,Color,Entity,Grid,Scene,Timer] verified=0.2.8-dev status=ok
# Entity Visibility - Check what entities can see
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

# Create dungeon
for y in range(12):
    for x in range(16):
        cell = grid.at(x, y)
        if x == 8 and y > 1 and y < 10:
            cell.tilesprite = 1
            cell.transparent = False
        else:
            cell.tilesprite = 48
            cell.transparent = True

# Player
player = mcrfpy.Entity(grid_pos=(4, 6), texture=mcrfpy.default_texture, sprite_index=84, name="player")
grid.entities.append(player)

# Enemies
for i, pos in enumerate([(12, 3), (12, 6), (12, 9)]):
    enemy = mcrfpy.Entity(grid_pos=pos, texture=mcrfpy.default_texture, sprite_index=112, name=f"enemy_{i}")
    grid.entities.append(enemy)

grid.perspective = player
grid.fov_radius = 10

status = mcrfpy.Caption(text="Wall blocks view of some enemies", pos=(320, 700))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)

def update_status(timer, runtime):
    visible = player.visible_entities()
    names = [e.name for e in visible if e.name != "player"]
    status.text = f"Visible entities: {names if names else 'none'}"

timer = mcrfpy.Timer("check", update_status, 100)
