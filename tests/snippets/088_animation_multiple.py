# mcrf: objects=[Caption,Color,Easing,Frame,Scene,Timer] verified=0.2.8-dev@a7ba486 status=ok
# Animation Multiple - Several animations at once
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

# Create a frame
frame = mcrfpy.Frame(
    pos=(100, 300), size=(100, 100),
    fill_color=mcrfpy.Color(255, 100, 100),
    outline=2.0,
    outline_color=mcrfpy.Color(255, 255, 255),
    opacity=1.0
)
scene.children.append(frame)

scene.children.append(mcrfpy.Caption(
    text="Multiple animations running simultaneously",
    pos=(300, 600)
))

def restart_animation(timer, runtime):
    frame.x = 100
    frame.y = 300
    frame.w = 100
    frame.h = 100
    frame.fill_color = mcrfpy.Color(255, 100, 100)
    frame.opacity = 1.0
    frame.outline = 2.0
    frame.animate("x", 800, 3.0, mcrfpy.Easing.EASE_IN_OUT)
    frame.animate("y", 500, 3.0, mcrfpy.Easing.EASE_IN_OUT_BACK)
    frame.animate("w", 200, 3.0, mcrfpy.Easing.EASE_OUT_ELASTIC)
    frame.animate("h", 150, 3.0, mcrfpy.Easing.EASE_OUT_ELASTIC)
    frame.animate("fill_color", (100, 100, 255, 255), 3.0, mcrfpy.Easing.LINEAR)
    frame.animate("opacity", 0.5, 3.0, mcrfpy.Easing.EASE_IN)
    frame.animate("outline", 10.0, 3.0, mcrfpy.Easing.LINEAR)

# Start multiple animations at the same time
frame.animate("x", 800, 3.0, mcrfpy.Easing.EASE_IN_OUT)
frame.animate("y", 500, 3.0, mcrfpy.Easing.EASE_IN_OUT_BACK)
frame.animate("w", 200, 3.0, mcrfpy.Easing.EASE_OUT_ELASTIC)
frame.animate("h", 150, 3.0, mcrfpy.Easing.EASE_OUT_ELASTIC)
frame.animate("fill_color", (100, 100, 255, 255), 3.0, mcrfpy.Easing.LINEAR)
frame.animate("opacity", 0.5, 3.0, mcrfpy.Easing.EASE_IN)
frame.animate("outline", 10.0, 3.0, mcrfpy.Easing.LINEAR)
loop_timer = mcrfpy.Timer("loop", restart_animation, 8000)
