# mcrf: objects=[Easing,Frame,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("test")
frame = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
scene.children.append(frame)
mcrfpy.current_scene = scene

# Start animation: move x from 0 to 500 over 2 seconds
frame.animate("x", 500.0, 2.0, mcrfpy.Easing.EASE_IN_OUT)

# Advance halfway through animation
mcrfpy.step(1.0)
print(f"Frame x: {frame.x}")  # ~250 (halfway)

# Complete the animation
mcrfpy.step(1.0)
print(f"Frame x: {frame.x}")  # 500 (complete)
