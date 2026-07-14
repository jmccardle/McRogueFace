# mcrf: objects=[Caption,Color,Frame,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Input Mouse Hover - Enter/exit/move events
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(
    pos=(0, 0), size=(1024, 768),
    fill_color=mcrfpy.Color(30, 30, 40)
))

# Hoverable frame
frame = mcrfpy.Frame(
    pos=(312, 234), size=(400, 300),
    fill_color=mcrfpy.Color(80, 80, 120),
    outline=3.0,
    outline_color=mcrfpy.Color(120, 120, 180)
)
scene.children.append(frame)

status = mcrfpy.Caption(
    text="Mouse outside",
    pos=(140, 130)
)
frame.children.append(status)

coords = mcrfpy.Caption(text="", pos=(140, 180))
frame.children.append(coords)

def on_enter(pos):
    frame.fill_color = mcrfpy.Color(100, 150, 100)
    status.text = "Mouse ENTERED"

def on_exit(pos):
    frame.fill_color = mcrfpy.Color(80, 80, 120)
    status.text = "Mouse EXITED"
    coords.text = ""

def on_move(pos):
    coords.text = f"Position: ({pos.x:.0f}, {pos.y:.0f})"

frame.on_enter = on_enter
frame.on_exit = on_exit
frame.on_move = on_move
