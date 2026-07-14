# mcrf: objects=[Caption,Color,Entity,Frame,Grid,InputState,Key,Scene] verified=0.2.8-dev status=ok
# Complete Mini-Game - Putting it all together
import mcrfpy
import random

scene = mcrfpy.Scene("game")
mcrfpy.current_scene = scene

# Game state
score = 0
game_over = False

# UI
scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(20, 20, 30)))

grid = mcrfpy.Grid(grid_size=(16, 12), texture=mcrfpy.default_texture, pos=(0, 0), size=(1024, 768), zoom=4.0)
scene.children.append(grid)

for y in range(12):
    for x in range(16):
        cell = grid.at(x, y)
        cell.tilesprite = 48 if (x > 0 and x < 15 and y > 0 and y < 11) else 1
        cell.walkable = cell.tilesprite == 48

# Player
player = mcrfpy.Entity(grid_pos=(8, 6), texture=mcrfpy.default_texture, sprite_index=84)
grid.entities.append(player)

# Coins
def spawn_coin():
    while True:
        x, y = random.randint(1, 14), random.randint(1, 10)
        if grid.at(x, y).walkable:
            occupied = False
            for e in grid.entities:
                if e.grid_x == x and e.grid_y == y:
                    occupied = True
                    break
            if not occupied:
                coin = mcrfpy.Entity(grid_pos=(x, y), texture=mcrfpy.default_texture, sprite_index=17, name="coin")
                grid.entities.append(coin)
                return

for _ in range(5):
    spawn_coin()

score_label = mcrfpy.Caption(text="Score: 0", pos=(20, 20))
score_label.fill_color = mcrfpy.Color(255, 220, 100)
score_label.outline = 2
score_label.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(score_label)

status = mcrfpy.Caption(text="WASD to collect coins!", pos=(400, 720))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)

def check_collision():
    global score
    for entity in list(grid.entities):
        if entity.name == "coin" and entity.grid_x == player.grid_x and entity.grid_y == player.grid_y:
            entity.die()
            score += 10
            score_label.text = f"Score: {score}"
            spawn_coin()

def on_key(key, action):
    if action != mcrfpy.InputState.PRESSED: return
    x, y = player.grid_x, player.grid_y
    if key == mcrfpy.Key.W and grid.at(x, y-1).walkable: player.grid_pos = (x, y-1)
    elif key == mcrfpy.Key.S and grid.at(x, y+1).walkable: player.grid_pos = (x, y+1)
    elif key == mcrfpy.Key.A and grid.at(x-1, y).walkable: player.grid_pos = (x-1, y)
    elif key == mcrfpy.Key.D and grid.at(x+1, y).walkable: player.grid_pos = (x+1, y)
    check_collision()

scene.on_key = on_key
