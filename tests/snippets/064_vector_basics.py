# mcrf: objects=[Caption,Color,Frame,Scene,Vector] verified=0.2.8-dev status=ok
# Vector Basics - 2D vector operations
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

# Create vectors
v1 = mcrfpy.Vector(100, 50)
v2 = mcrfpy.Vector(30, 80)

# Display vector info
info = [
    f"v1 = Vector({v1.x}, {v1.y})",
    f"v2 = Vector({v2.x}, {v2.y})",
    f"",
    f"v1.magnitude() = {v1.magnitude():.2f}",
    f"v1.angle() = {v1.angle():.2f} radians",
    f"",
    f"Distance v1 to v2 = {v1.distance_to(v2):.2f}",
]

y = 150
for line in info:
    cap = mcrfpy.Caption(text=line, pos=(300, y))
    cap.fill_color = mcrfpy.Color(200, 200, 200)
    scene.children.append(cap)
    y += 60

# Visual representation
origin = mcrfpy.Frame(pos=(500, 500), size=(10, 10), fill_color=mcrfpy.Color(255, 255, 255))
scene.children.append(origin)

# v1 endpoint
p1 = mcrfpy.Frame(pos=(500 + v1.x * 2, 500 - v1.y * 2), size=(15, 15), fill_color=mcrfpy.Color(255, 100, 100))
scene.children.append(p1)
v1_label = mcrfpy.Caption(text="v1", pos=(500 + v1.x * 2 + 20, 500 - v1.y * 2))
v1_label.outline = 2
v1_label.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(v1_label)

# v2 endpoint
p2 = mcrfpy.Frame(pos=(500 + v2.x * 2, 500 - v2.y * 2), size=(15, 15), fill_color=mcrfpy.Color(100, 100, 255))
scene.children.append(p2)
v2_label = mcrfpy.Caption(text="v2", pos=(500 + v2.x * 2 + 20, 500 - v2.y * 2))
v2_label.outline = 2
v2_label.outline_color = mcrfpy.Color(0, 0, 0)
scene.children.append(v2_label)
