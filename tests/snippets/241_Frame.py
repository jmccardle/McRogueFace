# mcrf: objects=[Caption,Color,Frame,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

# Create a styled panel
panel = mcrfpy.Frame(pos=(100, 100), size=(200, 150))
panel.fill_color = mcrfpy.Color(40, 40, 40, 200)
panel.outline_color = mcrfpy.Color(100, 100, 100)
panel.outline = 2

# Add to scene
scene.children.append(panel)

# Frames can contain children
label = mcrfpy.Caption(text="Panel Title", pos=(10, 10))
panel.children.append(label)

# Enable clipping for scrollable content
panel.clip_children = True

# Animate properties
panel.animate("opacity", 0.5, 1.0, "easeInOut")
