# mcrf: objects=[Caption,Color,Easing,Frame,Scene,Timer] verified=0.2.8-dev status=ok
# Easing: ELASTIC - Springy overshoot
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(
    pos=(0, 0), size=(1024, 768),
    fill_color=mcrfpy.Color(30, 30, 40)
))

frame = mcrfpy.Frame(
    pos=(100, 334), size=(100, 100),
    fill_color=mcrfpy.Color(100, 200, 255)
)
scene.children.append(frame)

# Target marker
scene.children.append(mcrfpy.Frame(
    pos=(824, 300), size=(5, 170),
    fill_color=mcrfpy.Color(255, 100, 100)
))

_caption = mcrfpy.Caption(
    text="EASE_OUT_ELASTIC - Spring overshoot",
    pos=(340, 200))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)

def restart_animation(timer, runtime):
    frame.x = 100
    frame.animate("x", 824, 2.5, mcrfpy.Easing.EASE_OUT_ELASTIC)

frame.animate("x", 824, 2.5, mcrfpy.Easing.EASE_OUT_ELASTIC)
loop_timer = mcrfpy.Timer("loop", restart_animation, 7500)  # 2.5s animation + 5s pause
