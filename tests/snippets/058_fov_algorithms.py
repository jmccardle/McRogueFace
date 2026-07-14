# mcrf: objects=[Caption,Color,ColorLayer,FOV,Frame,Grid,Scene] verified=0.2.8-dev@a7ba486 status=ok
# FOV Algorithms - Compare different algorithms
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

algorithms = [
    (mcrfpy.FOV.BASIC, "BASIC"),
    (mcrfpy.FOV.SHADOW, "SHADOW"),
    (mcrfpy.FOV.DIAMOND, "DIAMOND"),
    (mcrfpy.FOV.PERMISSIVE_4, "PERMISSIVE4"),
]

for i, (algo, name) in enumerate(algorithms):
    x = 62 + (i % 2) * 480
    y = 60 + (i // 2) * 360

    grid = mcrfpy.Grid(
        grid_size=(12, 9),
        texture=mcrfpy.default_texture,
        pos=(x, y),
        size=(420, 300)
    )
    scene.children.append(grid)

    # Add fog layer
    fog = mcrfpy.ColorLayer(z_index=1, name="fog")
    grid.add_layer(fog)
    fog.fill(mcrfpy.Color(0, 0, 0, 180))

    # Setup dungeon
    for gy in range(9):
        for gx in range(12):
            cell = grid.at(gx, gy)
            if gx == 0 or gx == 11 or gy == 0 or gy == 8:
                cell.tilesprite = 1
                cell.transparent = False
            elif gx == 6 and gy > 1 and gy < 7:
                cell.tilesprite = 1
                cell.transparent = False
            else:
                cell.tilesprite = 48
                cell.transparent = True

    # Compute FOV with this algorithm
    grid.compute_fov((3, 4), radius=6, algorithm=algo)

    # Clear fog for visible cells
    for gy in range(9):
        for gx in range(12):
            if grid.is_in_fov((gx, gy)):
                fog.set((gx, gy), mcrfpy.Color(0, 0, 0, 0))

    label = mcrfpy.Caption(text=name, pos=(x + 170, y + 310))
    label.outline = 2
    label.outline_color = mcrfpy.Color(0, 0, 0)
    scene.children.append(label)
