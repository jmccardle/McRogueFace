# mcrf: objects=[Color,Frame,Grid,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("game")
ui = scene.children

# Background layer (z=0)
background = mcrfpy.Frame(pos=(0, 0), size=(800, 600),
                           fill_color=mcrfpy.Color(20, 20, 20))
background.z_index = 0
ui.append(background)

# Game layer (z=10)
grid = mcrfpy.Grid(grid_size=(50, 50), pos=(50, 50), size=(700, 500))
grid.z_index = 10
ui.append(grid)

# UI layer (z=100)
hud = mcrfpy.Frame(pos=(0, 0), size=(800, 50),
                    fill_color=mcrfpy.Color(30, 30, 30, 200))
hud.z_index = 100
ui.append(hud)

# Renders: background -> grid -> hud
mcrfpy.current_scene = scene
