# mcrf: objects=[Caption,Color,Entity,Grid,InputState,Scene] verified=0.2.8-dev status=ok
# Entity Index - Get entity position in collection
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

# Create entities
sprites = [84, 86, 88, 112, 116]
for i, sprite_idx in enumerate(sprites):
    entity = mcrfpy.Entity(
        grid_pos=(3 + i * 2, 6),
        texture=mcrfpy.default_texture,
        sprite_index=sprite_idx,
        name=f"entity_{i}"
    )
    grid.entities.append(entity)

status = mcrfpy.Caption(text="Click on entities to see their index", pos=(340, 720))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)

def on_cell_click(pos, button, action):
    if action == mcrfpy.InputState.PRESSED:
        x, y = int(pos.x), int(pos.y)
        # Check if entity at position
        for entity in grid.entities:
            if entity.grid_x == x and entity.grid_y == y:
                idx = entity.index()
                status.text = f"'{entity.name}' is at index {idx} in grid.entities"
                return
        status.text = f"No entity at ({x}, {y})"

grid.on_cell_click = on_cell_click
