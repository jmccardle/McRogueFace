# mcrf: objects=[Caption,Color,Frame,Scene,Timer] verified=0.2.8-dev@a7ba486 status=ok
# Effect Pulse - Pulsing highlight
import mcrfpy
import math

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

# Pulsing frame
frame = mcrfpy.Frame(
    pos=(362, 284), size=(300, 200),
    fill_color=mcrfpy.Color(100, 100, 200),
    outline=4.0,
    outline_color=mcrfpy.Color(150, 150, 255)
)
scene.children.append(frame)

label = mcrfpy.Caption(text="Pulsing Effect", pos=(80, 80))
frame.children.append(label)

time = 0

def pulse(timer, runtime):
    global time
    time += 0.1

    # Oscillate opacity
    opacity = 0.5 + 0.5 * math.sin(time)
    frame.opacity = opacity

    # Oscillate outline
    outline = 2 + 4 * abs(math.sin(time))
    frame.outline = outline

timer = mcrfpy.Timer("pulse", pulse, 50)

scene.children.append(mcrfpy.Caption(text="Continuous pulse animation", pos=(380, 550)))
