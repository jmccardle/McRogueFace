# mcrf: objects=[Caption,Color,Entity,Frame,Grid,Scene] verified=0.2.8-dev status=ok
# Grid Zoom - Scale the grid view
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

zooms = [0.5, 1.0, 1.5, 2.0]
for i, zoom in enumerate(zooms):
    x = 62 + (i % 2) * 480
    y = 84 + (i // 2) * 340

    grid = mcrfpy.Grid(
        grid_size=(10, 8),
        texture=mcrfpy.default_texture,
        pos=(x, y),
        size=(420, 280)
    )
    scene.children.append(grid)

    # Fill with pattern
    for gy in range(8):
        for gx in range(10):
            cell = grid.at(gx, gy)
            cell.tilesprite = 48 if (gx + gy) % 2 == 0 else 49

    # Add entity
    ent = mcrfpy.Entity(grid_pos=(5, 4), texture=mcrfpy.default_texture, sprite_index=84)
    grid.entities.append(ent)

    # Apply zoom
    grid.zoom = zoom
    grid.center_camera((5, 4))

    label = mcrfpy.Caption(text=f"zoom={zoom}", pos=(x + 170, y + 290))
    label.outline = 2
    label.outline_color = mcrfpy.Color(0, 0, 0)
    scene.children.append(label)

# Add background and title
scene.children.insert(0, mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))
