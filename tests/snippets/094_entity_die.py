# mcrf: objects=[Caption,Color,Entity,Grid,InputState,Key,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Entity Die - Remove entity from grid
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

# Create several enemies
enemies = []
for i in range(5):
    enemy = mcrfpy.Entity(
        grid_pos=(3 + i * 2, 6),
        texture=mcrfpy.default_texture,
        sprite_index=112,
        name=f"enemy_{i}"
    )
    grid.entities.append(enemy)
    enemies.append(enemy)

status = mcrfpy.Caption(text=f"Enemies: {len(grid.entities)} - Press SPACE to kill one", pos=(300, 720))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)

def on_key(key, action):
    if key == mcrfpy.Key.SPACE and action == mcrfpy.InputState.PRESSED:
        if len(grid.entities) > 0:
            # Remove first entity
            entity = grid.entities[0]
            entity.die()  # Removes from grid
            status.text = f"Enemies remaining: {len(grid.entities)}"
        else:
            status.text = "No enemies left!"

scene.on_key = on_key
