# mcrf: objects=[Caption,Color,Frame,Scene] verified=0.2.8-dev status=ok
# Frame Name - Named elements for lookup
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

# Create named frames
header = mcrfpy.Frame(
    pos=(112, 50), size=(800, 100),
    fill_color=mcrfpy.Color(80, 80, 120),
    name="header"
)
scene.children.append(header)

sidebar = mcrfpy.Frame(
    pos=(112, 170), size=(200, 500),
    fill_color=mcrfpy.Color(60, 100, 80),
    name="sidebar"
)
scene.children.append(sidebar)

content = mcrfpy.Frame(
    pos=(332, 170), size=(580, 500),
    fill_color=mcrfpy.Color(100, 80, 60),
    name="main_content"
)
scene.children.append(content)

# Find elements by name
found = mcrfpy.find("header")
if found:
    label = mcrfpy.Caption(
        text=f"Found: '{found.name}'",
        pos=(20, 30)
    )
    found.children.append(label)

# Display all names
scene.children.append(mcrfpy.Caption(text="sidebar", pos=(170, 400)))
scene.children.append(mcrfpy.Caption(text="main_content", pos=(550, 400)))
