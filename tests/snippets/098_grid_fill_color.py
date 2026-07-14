# mcrf: objects=[Caption,Color,Entity,Frame,Grid,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Grid Fill Color - Background color
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

# Grid with colored background
grid = mcrfpy.Grid(
    grid_size=(16, 12),
    texture=mcrfpy.default_texture,
    pos=(0, 0),
    size=(1024, 768),
    zoom=4.0,
    fill_color=mcrfpy.Color(40, 60, 80)  # Blue-ish background
)
scene.children.append(grid)

# Sparse tiles to show background (only set some cells)
positions = [(3, 3), (7, 5), (12, 3), (5, 8), (10, 8)]
for x, y in positions:
    grid.at(x, y).tilesprite = 48

# Add some entities
grid.entities.append(mcrfpy.Entity(grid_pos=(5, 4), texture=mcrfpy.default_texture, sprite_index=84))
grid.entities.append(mcrfpy.Entity(grid_pos=(10, 6), texture=mcrfpy.default_texture, sprite_index=112))

status = mcrfpy.Caption(text="Grid fill_color creates background behind tiles", pos=(300, 720))
status.outline = 2
status.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(status)

# Show different fill colors
info = mcrfpy.Caption(text="fill_color = (40, 60, 80) - only some cells have tiles", pos=(280, 50))
info.outline = 2
info.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(info)
