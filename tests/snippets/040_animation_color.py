# mcrf: objects=[Caption,Color,Easing,Frame,Scene,Timer] verified=0.2.8-dev status=ok
# Animation Color - Animate fill_color
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(
    pos=(0, 0), size=(1024, 768),
    fill_color=mcrfpy.Color(30, 30, 40)
))

# Large frame to show color change
frame = mcrfpy.Frame(
    pos=(262, 184), size=(500, 400),
    fill_color=mcrfpy.Color(255, 100, 100),
    outline=3.0,
    outline_color=mcrfpy.Color(255, 255, 255)
)
scene.children.append(frame)

_caption = mcrfpy.Caption(
    text="Animating fill_color from red to blue",
    pos=(340, 620))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)

def restart_animation(timer, runtime):
    frame.fill_color = mcrfpy.Color(255, 100, 100)
    frame.animate("fill_color", (100, 100, 255, 255), 3.0, mcrfpy.Easing.EASE_IN_OUT)

# Animate to blue (pass color as RGBA tuple)
frame.animate("fill_color", (100, 100, 255, 255), 3.0, mcrfpy.Easing.EASE_IN_OUT)
loop_timer = mcrfpy.Timer("loop", restart_animation, 8000)
