# mcrf: objects=[Caption,Color,Easing,Frame,Scene,Timer] verified=0.2.8-dev status=ok
# Easing: EASE_IN - Slow start, fast end
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(
    pos=(0, 0), size=(1024, 768),
    fill_color=mcrfpy.Color(30, 30, 40)
))

frame = mcrfpy.Frame(
    pos=(100, 334), size=(100, 100),
    fill_color=mcrfpy.Color(100, 255, 150)
)
scene.children.append(frame)

# Markers
scene.children.append(mcrfpy.Frame(pos=(100, 300), size=(5, 170), fill_color=mcrfpy.Color(100, 100, 100)))
scene.children.append(mcrfpy.Frame(pos=(824, 300), size=(5, 170), fill_color=mcrfpy.Color(100, 100, 100)))

_caption = mcrfpy.Caption(
    text="EASE_IN - Accelerates from rest",
    pos=(350, 200))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)

def restart_animation(timer, runtime):
    frame.x = 100
    frame.animate("x", 824, 3.0, mcrfpy.Easing.EASE_IN)

frame.animate("x", 824, 3.0, mcrfpy.Easing.EASE_IN)
loop_timer = mcrfpy.Timer("loop", restart_animation, 8000)
