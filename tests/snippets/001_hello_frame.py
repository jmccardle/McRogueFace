# mcrf: objects=[Color,Frame,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Hello Frame - The simplest UI element
import mcrfpy

# Create a scene and make it active
scene = mcrfpy.Scene("hello")
mcrfpy.current_scene = scene

# Create a big, colorful frame in the center
frame = mcrfpy.Frame(
    pos=(312, 234),
    size=(400, 300),
    fill_color=mcrfpy.Color(100, 150, 200),
    outline_color=mcrfpy.Color(255, 255, 255),
    outline=4.0
)
scene.children.append(frame)
