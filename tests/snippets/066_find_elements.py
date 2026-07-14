# mcrf: objects=[Caption,Color,Frame,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Find Elements - Locate UI by name
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

# Create named elements
elements = [
    ("btn_play", 200, 200, mcrfpy.Color(100, 150, 100)),
    ("btn_options", 200, 320, mcrfpy.Color(100, 100, 150)),
    ("btn_quit", 200, 440, mcrfpy.Color(150, 100, 100)),
    ("header", 500, 100, mcrfpy.Color(150, 150, 100)),
]

for name, x, y, color in elements:
    frame = mcrfpy.Frame(pos=(x, y), size=(200, 80), fill_color=color, name=name)
    scene.children.append(frame)
    label = mcrfpy.Caption(text=name, pos=(20, 30))
    frame.children.append(label)

# Find specific element
found = mcrfpy.find("btn_options")
if found:
    found.outline = 4.0
    found.outline_color = mcrfpy.Color(255, 255, 255)

# Find all buttons
buttons = mcrfpy.find_all("btn_*")
status = mcrfpy.Caption(
    text=f"Found {len(buttons)} elements matching 'btn_*'",
    pos=(350, 600))
status.fill_color = mcrfpy.Color(200, 200, 200)
scene.children.append(status)
