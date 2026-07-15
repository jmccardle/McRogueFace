# mcrf: objects=[Color,Frame,Scene] verified=0.2.8-dev status=ok
import mcrfpy
from mcrfpy import automation

scene = mcrfpy.Scene("test")
ui = scene.children

frame = mcrfpy.Frame(pos=(100, 100), size=(200, 200),
                      fill_color=mcrfpy.Color(255, 0, 0))
ui.append(frame)
mcrfpy.current_scene = scene

# Screenshot captures current state immediately (no timer needed)
automation.screenshot("/tmp/red_frame.png")

# Change to green
frame.fill_color = mcrfpy.Color(0, 255, 0)

# Next screenshot shows green
automation.screenshot("/tmp/green_frame.png")
