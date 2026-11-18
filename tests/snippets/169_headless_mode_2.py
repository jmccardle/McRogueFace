# mcrf: objects=[Color,Frame,Scene] verified=0.3.6 status=ok
import mcrfpy
from mcrfpy import automation

scene = mcrfpy.Scene("test")
ui = scene.children

frame = mcrfpy.Frame(pos=(100, 100), size=(200, 200),
                      fill_color=mcrfpy.Color(255, 0, 0))
ui.append(frame)
mcrfpy.current_scene = scene

# No frame has been rendered yet, so the first screenshot renders one (no timer needed)
automation.screenshot("/tmp/red_frame.png")

# Change to green
frame.fill_color = mcrfpy.Color(0, 255, 0)

# A screenshot shows the last complete frame, so shooting now would save the red image
# again. Headless, step() runs a frame; the next screenshot draws it.
mcrfpy.step(0.016)

# Now the screenshot shows green
automation.screenshot("/tmp/green_frame.png")
