# mcrf: objects=[Easing,Frame,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

frame = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
scene.children.append(frame)

def on_arrival(target, prop, value):
    # target: the Frame that was animated
    # prop:   "x"
    # value:  500.0
    print(f"{type(target).__name__}.{prop} reached {value}")

frame.animate("x", 500.0, 2.0, mcrfpy.Easing.EASE_OUT_CUBIC, callback=on_arrival)
