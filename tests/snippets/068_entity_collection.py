# mcrf: objects=[Caption,Color,Entity,Grid,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Entity Collection - Manage grid entities
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
        grid.at(x, y).tilesprite = 48

# Add multiple entities
sprites = [84, 86, 88, 112, 116, 120]
for i, sprite_idx in enumerate(sprites):
    entity = mcrfpy.Entity(
        grid_pos=(2 + i * 2, 6),
        texture=mcrfpy.default_texture,
        sprite_index=sprite_idx,
        name=f"entity_{i}"
    )
    grid.entities.append(entity)

# Count and iterate
status = mcrfpy.Caption(text=f"Grid has {len(grid.entities)} entities", pos=(400, 720))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)

# Highlight alternating entities
for i, entity in enumerate(grid.entities):
    if i % 2 == 0:
        entity.opacity = 0.5
