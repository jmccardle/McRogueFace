# mcrf: objects=[Caption,Color,Entity,Frame,Grid,Scene] verified=0.2.8-dev status=ok
# Grid Display Size - Viewport dimensions
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

# Different sized grids with same grid_size
configs = [
    ((50, 50), (300, 300), "300x300"),
    ((400, 50), (500, 300), "500x300"),
    ((50, 400), (300, 200), "300x200"),
    ((400, 400), (500, 200), "500x200"),
]

for pos, size, label in configs:
    grid = mcrfpy.Grid(
        grid_size=(10, 8),
        texture=mcrfpy.default_texture,
        pos=pos,
        size=size
    )
    scene.children.append(grid)

    for y in range(8):
        for x in range(10):
            grid.at(x, y).tilesprite = 48 if (x + y) % 2 == 0 else 49

    # Add entity
    grid.entities.append(mcrfpy.Entity(grid_pos=(5, 4), texture=mcrfpy.default_texture, sprite_index=84))

    # Label
    label_cap = mcrfpy.Caption(text=label, pos=(pos[0] + 10, pos[1] + size[1] + 10))
    label_cap.outline = 2
    label_cap.outline_color = mcrfpy.Color(0, 0, 0)
    scene.children.append(label_cap)

status = mcrfpy.Caption(
    text="Same grid_size (10x8), different display sizes",
    pos=(320, 720)
)
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)
