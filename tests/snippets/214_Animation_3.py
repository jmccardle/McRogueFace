# mcrf: objects=[Frame,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

frame = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
scene.children.append(frame)

frame.animate("x", 100.0, 1.0)

# replace (default): the running animation jumps to its final value,
# then the new animation starts
frame.animate("x", 200.0, 1.0)

# queue: run after the current animation on "x" finishes
frame.animate("x", 300.0, 1.0, conflict_mode="queue")

# error: raise RuntimeError if "x" is already animating
try:
    frame.animate("x", 400.0, 1.0, conflict_mode="error")
except RuntimeError as e:
    print(e)
