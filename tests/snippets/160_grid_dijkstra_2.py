# mcrf: objects=[Caption,Color,Entity,Grid,Scene] verified=0.2.8-dev status=ok
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

for y in range(12):
    for x in range(16):
        cell = grid.at(x, y)
        cell.tilesprite = 48
        cell.walkable = True

threat = mcrfpy.Entity(grid_pos=(8, 6), texture=mcrfpy.default_texture, sprite_index=84)
grid.entities.append(threat)

prey = mcrfpy.Entity(grid_pos=(9, 6), texture=mcrfpy.default_texture, sprite_index=112)
grid.entities.append(prey)


def ai_flee(grid, entity, threat_x, threat_y):
    """Move entity away from threat using an inverted Dijkstra map."""
    toward_threat = grid.get_dijkstra_map((threat_x, threat_y))
    away_from_threat = toward_threat.invert()
    step = away_from_threat.descent_step(entity.grid_pos)
    if step is not None:
        entity.grid_pos = step


ai_flee(grid, prey, threat.grid_pos[0], threat.grid_pos[1])

status = mcrfpy.Caption(text="Flee behavior via DijkstraMap.invert()", pos=(320, 720))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)
