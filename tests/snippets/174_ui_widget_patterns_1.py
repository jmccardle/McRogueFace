# mcrf: objects=[Color,Frame,Scene] verified=0.2.8-dev status=ok
# Setup Template - the basic scaffold shared by all widget patterns on this page.
import mcrfpy

# Create scene and get UI collection
scene = mcrfpy.Scene("menu")
ui = scene.children

# Create root container for the menu/HUD
root = mcrfpy.Frame(pos=(50, 50), size=(300, 400),
                     fill_color=mcrfpy.Color(30, 30, 40))
root.outline_color = mcrfpy.Color(80, 80, 100)
root.outline = 2
ui.append(root)

# Add widgets to root.children...

mcrfpy.current_scene = scene
