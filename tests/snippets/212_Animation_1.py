# mcrf: objects=[Easing,Frame,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

frame = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
scene.children.append(frame)

# Animate a property: creates, starts, and registers the animation
frame.animate("x", 500.0, 2.0, mcrfpy.Easing.EASE_OUT_QUAD)

# With a completion callback
def on_done(target, prop, value):
    print(f"{prop} finished at {value}")

frame.animate("opacity", 0.0, 1.0, callback=on_done)

# The returned Animation handle can be inspected and controlled
anim = frame.animate("w", 300.0, 1.5)
print(anim.property, anim.duration, anim.is_complete)
anim.stop()  # cancel without applying the final value
