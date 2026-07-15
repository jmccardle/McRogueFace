# mcrf: objects=[Caption,Color,Entity,Grid,InputState,Key,Scene,Texture] verified=0.2.8-dev status=ok
"""McRogueFace Tutorial - Part 2: Walls, Floors, and Collision"""
import mcrfpy

# Constants
SPRITE_WALL = 35
SPRITE_FLOOR = 46
SPRITE_PLAYER = 64
GRID_WIDTH = 30
GRID_HEIGHT = 20

def create_map(grid: mcrfpy.Grid) -> None:
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            cell = grid.at(x, y)
            if x == 0 or x == GRID_WIDTH - 1 or y == 0 or y == GRID_HEIGHT - 1:
                cell.tilesprite = SPRITE_WALL
                cell.walkable = False
            else:
                cell.tilesprite = SPRITE_FLOOR
                cell.walkable = True

    for y in range(5, 15):
        cell = grid.at(10, y)
        cell.tilesprite = SPRITE_WALL
        cell.walkable = False

    for x in range(15, 25):
        cell = grid.at(x, 10)
        cell.tilesprite = SPRITE_WALL
        cell.walkable = False

    grid.at(10, 10).tilesprite = SPRITE_FLOOR
    grid.at(10, 10).walkable = True
    grid.at(20, 10).tilesprite = SPRITE_FLOOR
    grid.at(20, 10).walkable = True

def can_move_to(grid: mcrfpy.Grid, x: int, y: int) -> bool:
    if x < 0 or x >= GRID_WIDTH or y < 0 or y >= GRID_HEIGHT:
        return False
    return grid.at(x, y).walkable

scene = mcrfpy.Scene("game")
texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16)

grid = mcrfpy.Grid(
    pos=(80, 100), size=(720, 480),
    grid_size=(GRID_WIDTH, GRID_HEIGHT), texture=texture,
    zoom=1.5
)
create_map(grid)

player = mcrfpy.Entity(grid_pos=(5, 10), texture=texture, sprite_index=SPRITE_PLAYER)
grid.entities.append(player)
scene.children.append(grid)

title = mcrfpy.Caption(pos=(80, 20), text="Part 2: Walls and Collision")
title.fill_color = mcrfpy.Color(255, 255, 255)
title.font_size = 24
scene.children.append(title)

instructions = mcrfpy.Caption(pos=(80, 55), text="WASD or Arrow Keys | Walls block movement")
instructions.fill_color = mcrfpy.Color(180, 180, 180)
instructions.font_size = 16
scene.children.append(instructions)

pos_display = mcrfpy.Caption(pos=(80, 600), text=f"Position: ({player.grid_x}, {player.grid_y})")
pos_display.fill_color = mcrfpy.Color(200, 200, 100)
pos_display.font_size = 16
scene.children.append(pos_display)

status_display = mcrfpy.Caption(pos=(400, 600), text="Status: Ready")
status_display.fill_color = mcrfpy.Color(100, 200, 100)
status_display.font_size = 16
scene.children.append(status_display)

def handle_keys(key: mcrfpy.Key, action: mcrfpy.InputState) -> None:
    if action != mcrfpy.InputState.PRESSED:
        return
    px, py = player.grid_x, player.grid_y
    new_x, new_y = px, py
    if key == mcrfpy.Key.W or key == mcrfpy.Key.UP:
        new_y -= 1
    elif key == mcrfpy.Key.S or key == mcrfpy.Key.DOWN:
        new_y += 1
    elif key == mcrfpy.Key.A or key == mcrfpy.Key.LEFT:
        new_x -= 1
    elif key == mcrfpy.Key.D or key == mcrfpy.Key.RIGHT:
        new_x += 1
    elif key == mcrfpy.Key.ESCAPE:
        mcrfpy.exit()
        return
    else:
        return
    if can_move_to(grid, new_x, new_y):
        player.grid_x = new_x
        player.grid_y = new_y
        pos_display.text = f"Position: ({new_x}, {new_y})"
        status_display.text = "Status: Moved"
        status_display.fill_color = mcrfpy.Color(100, 200, 100)
    else:
        status_display.text = "Status: Blocked!"
        status_display.fill_color = mcrfpy.Color(200, 100, 100)

scene.on_key = handle_keys
scene.activate()
