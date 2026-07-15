# mcrf: objects=[Frame,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

frame = mcrfpy.Frame(pos=(0, 0), size=(50, 50))
scene.children.append(frame)

def step2(target, prop, value):
    target.animate("y", 100.0, 0.3, callback=step3)

def step3(target, prop, value):
    target.animate("x", 0.0, 0.3, callback=step4)

def step4(target, prop, value):
    target.animate("y", 0.0, 0.3)

# Trace a rectangle: each callback starts the next leg
frame.animate("x", 100.0, 0.3, callback=step2)
