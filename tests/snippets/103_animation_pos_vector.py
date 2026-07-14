# mcrf: objects=[Caption,Color,Easing,Frame,Scene,Timer] verified=0.2.8-dev@a7ba486 status=ok
# Animation Position - Animate x and y along a path
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

frame = mcrfpy.Frame(
    pos=(100, 100), size=(100, 100),
    fill_color=mcrfpy.Color(255, 150, 100)
)
scene.children.append(frame)

# Path markers
path = [(100, 100), (800, 100), (800, 600), (100, 600)]
for x, y in path:
    marker = mcrfpy.Frame(
        pos=(x - 5, y - 5), size=(10, 10),
        fill_color=mcrfpy.Color(100, 100, 100)
    )
    scene.children.append(marker)

scene.children.append(mcrfpy.Caption(text="Animating x and y position along path", pos=(340, 350)))

current_idx = 0

def move_to_next(timer, runtime):
    global current_idx
    current_idx = (current_idx + 1) % len(path)
    next_pos = path[current_idx]
    # Animate both x and y
    frame.animate("x", next_pos[0], 1.0, mcrfpy.Easing.EASE_IN_OUT)
    frame.animate("y", next_pos[1], 1.0, mcrfpy.Easing.EASE_IN_OUT)

# Use timer to control path movement (avoids recursive callback segfault)
path_timer = mcrfpy.Timer("path", move_to_next, 1500)

# Start first animation
frame.animate("x", path[1][0], 1.0, mcrfpy.Easing.EASE_IN_OUT)
frame.animate("y", path[1][1], 1.0, mcrfpy.Easing.EASE_IN_OUT)
current_idx = 1
