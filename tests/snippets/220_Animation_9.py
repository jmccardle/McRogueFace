# mcrf: objects=[Frame,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

frame = mcrfpy.Frame(pos=(100, 100), size=(200, 80))
scene.children.append(frame)

# Animate a whole color (interpolates R, G, B, and A together)
frame.animate("fill_color", (255, 0, 0, 255), 1.0)

# Animate a single channel
frame.animate("fill_color.a", 0.0, 0.5)

# Delta mode: move 50 pixels down from wherever the frame is now
frame.animate("y", 50.0, 0.5, delta=True)
