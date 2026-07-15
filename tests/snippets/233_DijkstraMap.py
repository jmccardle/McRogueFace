# mcrf: objects=[Caption,Color,ColorLayer,Entity,Grid,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("dijkstra_demo")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(
    grid_size=(16, 12),
    texture=mcrfpy.default_texture,
    pos=(0, 0),
    size=(1024, 768),
    zoom=4.0,
)
scene.children.append(grid)

for y in range(12):
    for x in range(16):
        cell = grid.at(x, y)
        cell.tilesprite = 48
        cell.walkable = True

player = mcrfpy.Entity(grid_pos=(8, 6), texture=mcrfpy.default_texture, grid=grid)
enemy = mcrfpy.Entity(grid_pos=(2, 2), texture=mcrfpy.default_texture, grid=grid)

# AI Movement Toward Goal
player_dijkstra = grid.get_dijkstra_map(player.grid_pos)

for e in grid.entities:
    if e != player:
        next_step = player_dijkstra.step_from(e)
        if next_step:
            e.grid_pos = next_step

# Distance-Based Decisions
goal_map = grid.get_dijkstra_map(player.grid_pos)
for e in grid.entities:
    dist = goal_map.distance(e)
    if dist is None:
        print(f"{e} cannot reach goal")
    elif dist < 5:
        print(f"{e} is very close!")
    else:
        print(f"{e} is {dist} steps away")

# Visualization with HeightMap
heightmap = goal_map.to_heightmap()
color_layer = mcrfpy.ColorLayer(z_index=1, name="distance_gradient")
grid.add_layer(color_layer)
color_layer.apply_gradient(
    heightmap,
    (0, 20),
    mcrfpy.Color(0, 255, 0),
    mcrfpy.Color(255, 0, 0),
)

# Cache Management
grid.at(5, 5).walkable = False
grid.clear_dijkstra_maps()

status = mcrfpy.Caption(text="Dijkstra distance map demo", pos=(320, 720))
scene.children.append(status)
