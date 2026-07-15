# mcrf: objects=[Caption,Color,ColorLayer,Entity,Grid,Scene] verified=0.2.8-dev status=ok
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

# Color layer to visualize the distance field
dist_layer = mcrfpy.ColorLayer(z_index=1, name="distances")
grid.add_layer(dist_layer)

# Floor tiles with a wall down the middle
for y in range(12):
    for x in range(16):
        cell = grid.at(x, y)
        cell.tilesprite = 48
        cell.walkable = True

for i in range(5):
    grid.at(8, 2 + i).tilesprite = 1
    grid.at(8, 2 + i).walkable = False

player = mcrfpy.Entity(grid_pos=(3, 6), texture=mcrfpy.default_texture, sprite_index=84)
grid.entities.append(player)

enemy = mcrfpy.Entity(grid_pos=(13, 6), texture=mcrfpy.default_texture, sprite_index=112)
grid.entities.append(enemy)


def move_enemy_toward_player(grid, enemy, player):
    """Move enemy one step toward the player."""
    dijkstra = grid.get_dijkstra_map(player.grid_pos)
    step = dijkstra.step_from(enemy.grid_pos)
    if step is not None:
        enemy.grid_pos = step


# Visualize the distance field rooted at the player
dijkstra = grid.get_dijkstra_map(player.grid_pos)
for y in range(12):
    for x in range(16):
        if grid.at(x, y).walkable:
            dist = dijkstra.distance((x, y))
            if dist is not None:
                intensity = max(0, 255 - int(dist * 20))
                dist_layer.set((x, y), mcrfpy.Color(intensity, intensity, 255, 180))

move_enemy_toward_player(grid, enemy, player)

status = mcrfpy.Caption(text="Dijkstra distance map (darker = farther)", pos=(320, 720))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)
