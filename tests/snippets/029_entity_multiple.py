# mcrf: objects=[Caption,Color,Entity,Grid,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Multiple Entities - Several entities on one grid
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

# Floor tiles
for y in range(12):
    for x in range(16):
        grid.at(x, y).tilesprite = 48

# Different entity types
entities = [
    (4, 3, 84, "Knight"),   # Knight
    (8, 3, 86, "Mage"),     # Mage
    (12, 3, 88, "Archer"),  # Archer
    (4, 8, 112, "Goblin"),  # Goblin
    (8, 8, 116, "Skeleton"),# Skeleton
    (12, 8, 120, "Slime"),  # Slime
]

for x, y, sprite_idx, name in entities:
    entity = mcrfpy.Entity(
        grid_pos=(x, y),
        texture=mcrfpy.default_texture,
        sprite_index=sprite_idx,
        name=name
    )
    grid.entities.append(entity)

status = mcrfpy.Caption(text=f"Entity count: {len(grid.entities)}", pos=(420, 720))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)
