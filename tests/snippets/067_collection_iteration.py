# mcrf: objects=[Caption,Color,Frame,Scene] verified=0.2.8-dev status=ok
# Collection Iteration - Loop through UI children
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

# Container with multiple children
container = mcrfpy.Frame(pos=(162, 134), size=(700, 500), fill_color=mcrfpy.Color(50, 50, 70))
scene.children.append(container)

# Add various elements
for i in range(5):
    frame = mcrfpy.Frame(
        pos=(20 + i * 130, 50),
        size=(110, 80),
        fill_color=mcrfpy.Color(100 + i * 30, 100, 200 - i * 30)
    )
    container.children.append(frame)

for i in range(3):
    cap = mcrfpy.Caption(text=f"Label {i}", pos=(50 + i * 200, 200))
    container.children.append(cap)

# Iterate and count by type
frames = 0
captions = 0
for child in container.children:
    if hasattr(child, 'fill_color'):
        frames += 1
    if hasattr(child, 'text'):
        captions += 1

status = mcrfpy.Caption(
    text=f"Container has {len(container.children)} children: {frames} frames, {captions} captions",
    pos=(100, 400)
)
container.children.append(status)
