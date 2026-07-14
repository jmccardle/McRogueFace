# mcrf: objects=[Caption,Color,Easing,Frame,InputState,Key,Scene,Timer] verified=0.2.8-dev status=ok
# Animation Basic - Animate position
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

# Dark background
scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

# Create a frame to animate
frame = mcrfpy.Frame(
    pos=(100, 334),
    size=(150, 100),
    fill_color=mcrfpy.Color(100, 150, 255)
)
scene.children.append(frame)

label = mcrfpy.Caption(text="SPACE to restart animation", pos=(380, 700))
label.outline = 2
label.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(label)

# Animate position when space pressed
def on_key(key, action):
    if key == mcrfpy.Key.SPACE and action == mcrfpy.InputState.PRESSED:
        frame.x = 100
        frame.animate("x", 774, 2.0, mcrfpy.Easing.LINEAR)

scene.on_key = on_key

def restart_animation(timer, runtime):
    frame.x = 100
    frame.animate("x", 774, 2.0, mcrfpy.Easing.LINEAR)

# Auto-start animation with looping
frame.animate("x", 774, 2.0, mcrfpy.Easing.LINEAR)
loop_timer = mcrfpy.Timer("loop", restart_animation, 7000)
