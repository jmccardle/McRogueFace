# mcrf: objects=[Frame,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

frame = mcrfpy.Frame(pos=(0, 0), size=(100, 100))
scene.children.append(frame)

anim = frame.animate("x", 500.0, 2.0)

print(anim.property)      # "x"
print(anim.duration)      # 2.0
print(anim.elapsed)       # seconds since start
print(anim.is_complete)   # False until finished (or complete() called)
print(anim.get_current_value())  # current interpolated value

anim.complete()   # jump to x=500 immediately; fires the callback if set
print(frame.x)    # 500.0
