# mcrf: objects=[Caption,Color,Frame,Scene,Timer] verified=0.2.8-dev status=ok
# Hovered State - Check if element is hovered
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

# Create several frames
frames = []
for i in range(4):
    frame = mcrfpy.Frame(
        pos=(150 + i * 200, 300), size=(150, 150),
        fill_color=mcrfpy.Color(80, 80, 120),
        name=f"frame_{i}"
    )
    frame.children.append(mcrfpy.Caption(text=f"Frame {i}", pos=(40, 60)))
    scene.children.append(frame)
    frames.append(frame)

status = mcrfpy.Caption(text="Hover over frames", pos=(400, 550))
scene.children.append(status)

def check_hover(timer, runtime):
    hovered_names = []
    for frame in frames:
        if frame.hovered:
            hovered_names.append(frame.name)
            frame.fill_color = mcrfpy.Color(120, 120, 180)
        else:
            frame.fill_color = mcrfpy.Color(80, 80, 120)

    if hovered_names:
        status.text = f"Currently hovered: {', '.join(hovered_names)}"
    else:
        status.text = "No frames hovered"

timer = mcrfpy.Timer("hover_check", check_hover, 50)
